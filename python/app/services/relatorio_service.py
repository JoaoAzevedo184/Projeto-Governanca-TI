"""Relatórios (FR-006, FR-007): inventário filtrado e conformidade, em tela, CSV ou XLSX.

O inventário padrão não lista ativo baixado (AC-031); o filtro `status=BAIXADO` o traz de volta.
Depreciação sai da mesma função do restante da API (`calcular_para_ativo`): para o ativo baixado
usa a data da baixa e o residual congelado (AC-019).
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from math import ceil

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.ativo import Ativo
from app.models.enums import StatusAtivo, TipoAtivo
from app.models.historico import HistoricoTransferencia
from app.models.responsavel import Responsavel
from app.models.setor import Setor
from app.models.usuario import Usuario
from app.schemas.relatorio import InventarioResponse, LinhaInventario, TotaisInventario
from app.services.compliance_service import apurar_alertas
from app.services.depreciacao_service import calcular_para_ativo
from app.utils.datas import agora, hoje
from app.utils.exportacao import (
    CSV_MEDIA_TYPE,
    XLSX_MEDIA_TYPE,
    gerar_csv,
    gerar_xlsx,
)
from app.utils.mascaramento import chave_para_perfil

COLUNAS_INVENTARIO = [
    "id",
    "nome",
    "tipo",
    "categoria",
    "identificador",
    "responsavel",
    "setor",
    "status",
    "data_aquisicao",
    "valor_compra",
    "depreciacao_acumulada",
    "percentual_depreciado",
    "valor_residual",
    "fornecedor",
]
COLUNAS_CONFORMIDADE = [
    "codigo",
    "severidade",
    "regra",
    "mensagem",
    "entidade",
    "entidade_id",
    "recurso",
]


@dataclass
class FiltrosInventario:
    """Filtros do FR-006, combinados por conjunção (AND). Lista vazia ou nula = sem filtro."""

    status: list[StatusAtivo] | None = None
    tipo: list[TipoAtivo] | None = None
    categoria_id: list[int] | None = None
    fornecedor_id: list[int] | None = None
    responsavel_id: int | None = None
    valor_depreciado_min: Decimal | None = None
    valor_depreciado_max: Decimal | None = None
    percentual_depreciado_min: Decimal | None = None
    percentual_depreciado_max: Decimal | None = None
    aquisicao_de: date | None = None
    aquisicao_ate: date | None = None
    fim_vida_util: bool | None = None


def _linhas_inventario(
    db: Session, usuario: Usuario, f: FiltrosInventario, data_referencia: date
) -> list[LinhaInventario]:
    consulta = select(Ativo).options(
        selectinload(Ativo.baixa), selectinload(Ativo.categoria), selectinload(Ativo.fornecedor)
    )
    if f.status:
        consulta = consulta.where(Ativo.status.in_(f.status))
    else:
        consulta = consulta.where(Ativo.status != StatusAtivo.BAIXADO)  # AC-031
    if f.tipo:
        consulta = consulta.where(Ativo.tipo.in_(f.tipo))
    if f.categoria_id:
        consulta = consulta.where(Ativo.categoria_id.in_(f.categoria_id))
    if f.fornecedor_id:
        consulta = consulta.where(Ativo.fornecedor_id.in_(f.fornecedor_id))
    if f.aquisicao_de is not None:
        consulta = consulta.where(Ativo.data_aquisicao >= f.aquisicao_de)
    if f.aquisicao_ate is not None:
        consulta = consulta.where(Ativo.data_aquisicao <= f.aquisicao_ate)
    if f.responsavel_id is not None:
        consulta = consulta.where(
            exists().where(
                HistoricoTransferencia.ativo_id == Ativo.id,
                HistoricoTransferencia.data_fim.is_(None),
                HistoricoTransferencia.responsavel_id == f.responsavel_id,
            )
        )
    ativos = list(db.scalars(consulta.order_by(Ativo.id)))

    atuais = {
        ativo_id: (responsavel, setor)
        for ativo_id, responsavel, setor in db.execute(
            select(HistoricoTransferencia.ativo_id, Responsavel.nome, Setor.nome)
            .join(Responsavel, Responsavel.id == HistoricoTransferencia.responsavel_id)
            .join(Setor, Setor.id == HistoricoTransferencia.setor_id)
            .where(
                HistoricoTransferencia.ativo_id.in_([a.id for a in ativos]),
                HistoricoTransferencia.data_fim.is_(None),
            )
        )
    }
    limiar = Decimal(get_settings().limiar_fim_vida_util_percentual)

    # ponytail: filtros de depreciação em Python sobre o resultado do SQL (a depreciação é função
    # pura por ativo, não coluna); migrar para SQL se o inventário passar de dezenas de milhares.
    linhas = []
    for ativo in ativos:
        dep = calcular_para_ativo(ativo, data_referencia)
        if (
            f.valor_depreciado_min is not None
            and dep.depreciacao_acumulada < f.valor_depreciado_min
        ):
            continue
        if (
            f.valor_depreciado_max is not None
            and dep.depreciacao_acumulada > f.valor_depreciado_max
        ):
            continue
        if (
            f.percentual_depreciado_min is not None
            and dep.percentual_depreciado < f.percentual_depreciado_min
        ):
            continue
        if (
            f.percentual_depreciado_max is not None
            and dep.percentual_depreciado > f.percentual_depreciado_max
        ):
            continue
        if f.fim_vida_util and dep.percentual_depreciado < limiar:  # AC-038
            continue
        responsavel, setor = atuais.get(ativo.id, (None, None))
        linhas.append(
            LinhaInventario(
                id=ativo.id,
                nome=ativo.nome,
                tipo=ativo.tipo,
                categoria=ativo.categoria.nome,
                identificador=ativo.numero_serie
                or chave_para_perfil(ativo.chave_licenca, usuario.perfil, detalhe=False),
                responsavel=responsavel,
                setor=setor,
                status=ativo.status,
                data_aquisicao=ativo.data_aquisicao,
                valor_compra=ativo.valor_compra,
                depreciacao_acumulada=dep.depreciacao_acumulada,
                percentual_depreciado=dep.percentual_depreciado,
                valor_residual=dep.valor_residual,
                fornecedor=ativo.fornecedor.razao_social,
            )
        )
    return linhas


def _totais(linhas: list[LinhaInventario]) -> TotaisInventario:
    return TotaisInventario(
        quantidade=len(linhas),
        valor_compra=sum((linha.valor_compra for linha in linhas), Decimal(0)),
        valor_residual=sum((linha.valor_residual for linha in linhas), Decimal(0)),
    )


def inventario(
    db: Session,
    usuario: Usuario,
    filtros: FiltrosInventario,
    *,
    pagina: int = 1,
    tamanho: int = 20,
    data_referencia: date | None = None,
) -> InventarioResponse:
    linhas = _linhas_inventario(db, usuario, filtros, data_referencia or hoje())
    inicio = (pagina - 1) * tamanho
    return InventarioResponse(
        itens=linhas[inicio : inicio + tamanho],
        pagina=pagina,
        tamanho=tamanho,
        total=len(linhas),
        total_paginas=ceil(len(linhas) / tamanho) if linhas else 0,
        totais=_totais(linhas),
    )


def _arquivo(
    formato: str,
    titulo: str,
    gerado_em: datetime,
    solicitante: str,
    colunas: list[str],
    linhas: list[list],
    rodape: list[list] | None = None,
) -> tuple[bytes, str]:
    gerar, media_type = (
        (gerar_csv, CSV_MEDIA_TYPE) if formato == "csv" else (gerar_xlsx, XLSX_MEDIA_TYPE)
    )
    return gerar(titulo, gerado_em, solicitante, colunas, linhas, rodape or []), media_type


def exportar_inventario(
    db: Session,
    usuario: Usuario,
    formato: str,
    filtros: FiltrosInventario,
    *,
    data_referencia: date | None = None,
    gerado_em: datetime | None = None,
) -> tuple[bytes, str]:
    """CSV ou XLSX com todo o resultado, sem paginação (AC-037), e totalizadores no rodapé."""
    linhas = _linhas_inventario(db, usuario, filtros, data_referencia or hoje())
    totais = _totais(linhas)
    return _arquivo(
        formato,
        "Inventário de ativos",
        gerado_em or agora(),
        usuario.login,
        COLUNAS_INVENTARIO,
        [[getattr(linha, coluna) for coluna in COLUNAS_INVENTARIO] for linha in linhas],
        [
            [],
            ["TOTAL", totais.quantidade, "", "", "", "", "", "", "", totais.valor_compra]
            + ["", "", totais.valor_residual],
        ],
    )


def exportar_conformidade(
    db: Session,
    usuario: Usuario,
    formato: str,
    *,
    data_referencia: date | None = None,
    gerado_em: datetime | None = None,
) -> tuple[bytes, str]:
    """Relatório de conformidade datado (FR-007): os alertas abertos na data de referência."""
    alertas = apurar_alertas(db, data_referencia)
    return _arquivo(
        formato,
        f"Conformidade em {(data_referencia or hoje()).isoformat()}",
        gerado_em or agora(),
        usuario.login,
        COLUNAS_CONFORMIDADE,
        [[getattr(a, coluna) for coluna in COLUNAS_CONFORMIDADE] for a in alertas],
    )
