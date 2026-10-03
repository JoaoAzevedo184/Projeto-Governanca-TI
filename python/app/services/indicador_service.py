"""Indicadores de ITAM (FR-009, AC-047): derivados na hora, cada um com fórmula e amostra.

Respeita as regras da Sprint 3: ativo baixado não entra no patrimônio nem na cobertura, e só
vínculo de licença ativo conta como uso. As fórmulas puras estão em `app/utils/indicadores.py`.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.ativo import Ativo
from app.models.enums import StatusAtivo, TipoAtivo
from app.models.historico import HistoricoTransferencia
from app.models.licenca import Licenca
from app.schemas.indicador import IndicadoresResponse, IndicadorResponse
from app.services.depreciacao_service import calcular_para_ativo
from app.services.licenca_service import contar_em_uso
from app.utils.conformidade import NAO_CONFORME, alertas_licenca, status_conformidade
from app.utils.datas import hoje
from app.utils.depreciacao import CENTAVO
from app.utils.indicadores import (
    atende_meta,
    custo_medio,
    idade_media_meses,
    percentual,
    percentual_depreciado_parque,
    sem_movimentacao,
)

DIAS_PERIODO_PADRAO = 365


def _dinheiro(valor: Decimal) -> str:
    return str(valor.quantize(CENTAVO))


def _numero(valor: Decimal | None) -> float | None:
    return None if valor is None else float(valor)


def _indicador(
    codigo: str,
    nome: str,
    valor: int | float | str | None,
    unidade: str,
    formula: str,
    amostra: int,
    *,
    meta: int | None = None,
    sentido: str | None = None,
    detalhe: dict[str, int] | None = None,
) -> IndicadorResponse:
    numerico = valor if isinstance(valor, (int, float)) else None
    atende = (
        atende_meta(
            None if numerico is None else Decimal(str(numerico)),
            None if meta is None else Decimal(meta),
            sentido,
        )
        if meta is not None
        else None
    )
    return IndicadorResponse(
        codigo=codigo,
        nome=nome,
        valor=valor,
        unidade=unidade,
        formula=formula,
        amostra=amostra,
        meta=meta,
        sentido_meta=sentido if meta is not None else None,
        atende_meta=atende,
        detalhe=detalhe,
    )


def calcular_indicadores(
    db: Session,
    *,
    categoria_id: int | None = None,
    setor_id: int | None = None,
    fornecedor_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    data_referencia: date | None = None,
) -> IndicadoresResponse:
    referencia = data_referencia or hoje()
    configuracao = get_settings()
    fim = data_fim or referencia
    inicio = data_inicio or fim - timedelta(days=DIAS_PERIODO_PADRAO)

    # ponytail: carrega os ativos do filtro e agrega em Python (depreciação é função pura por
    # ativo); trocar por agregação em SQL se o parque passar de dezenas de milhares.
    consulta = select(Ativo).options(selectinload(Ativo.baixa)).order_by(Ativo.id)
    if categoria_id is not None:
        consulta = consulta.where(Ativo.categoria_id == categoria_id)
    if fornecedor_id is not None:
        consulta = consulta.where(Ativo.fornecedor_id == fornecedor_id)
    if setor_id is not None:
        consulta = consulta.where(
            exists().where(
                HistoricoTransferencia.ativo_id == Ativo.id,
                HistoricoTransferencia.data_fim.is_(None),
                HistoricoTransferencia.setor_id == setor_id,
            )
        )
    ativos = list(db.scalars(consulta))
    em_operacao = [a for a in ativos if a.status != StatusAtivo.BAIXADO]
    baixados = [a for a in ativos if a.status == StatusAtivo.BAIXADO]
    ids = [a.id for a in ativos]

    com_vinculo = set(
        db.scalars(
            select(HistoricoTransferencia.ativo_id).where(
                HistoricoTransferencia.ativo_id.in_(ids), HistoricoTransferencia.data_fim.is_(None)
            )
        )
    )
    ultimo_evento = {
        ativo_id: max(d for d in (inicio_h, fim_h) if d is not None)
        for ativo_id, inicio_h, fim_h in db.execute(
            select(
                HistoricoTransferencia.ativo_id,
                func.max(HistoricoTransferencia.data_inicio),
                func.max(HistoricoTransferencia.data_fim),
            )
            .where(HistoricoTransferencia.ativo_id.in_(ids))
            .group_by(HistoricoTransferencia.ativo_id)
        )
    }

    bruto = sum((a.valor_compra for a in em_operacao), Decimal(0))
    residual = sum(
        (calcular_para_ativo(a, referencia).valor_residual for a in em_operacao), Decimal(0)
    )
    ativos_status = [a for a in em_operacao if a.status == StatusAtivo.ATIVO]
    ociosos = [
        a
        for a in em_operacao
        if sem_movimentacao(
            ultimo_evento.get(a.id, a.data_aquisicao),
            referencia,
            configuracao.meses_sem_movimentacao_alerta,
        )
    ]
    no_inicio = [
        a
        for a in ativos
        if a.data_aquisicao <= inicio and (a.baixa is None or a.baixa.data_baixa >= inicio)
    ]
    baixas_no_periodo = [a for a in baixados if inicio <= a.baixa.data_baixa <= fim]

    licencas_consulta = select(Licenca)
    if fornecedor_id is not None:
        licencas_consulta = licencas_consulta.where(Licenca.fornecedor_id == fornecedor_id)
    licencas = list(db.scalars(licencas_consulta))
    em_uso = contar_em_uso(db, [lic.id for lic in licencas])
    nao_conformes = sum(
        1
        for lic in licencas
        if status_conformidade(
            alertas_licenca(
                lic.quantidade_contratada,
                em_uso.get(lic.id, 0),
                lic.data_expiracao,
                referencia,
                configuracao.janela_alerta_licenca_dias,
            )
        )
        == NAO_CONFORME
    )

    custo = custo_medio(bruto, len(em_operacao))
    por_status = {s.value: sum(1 for a in ativos if a.status == s) for s in StatusAtivo}
    por_tipo = {t.value: sum(1 for a in ativos if a.tipo == t) for t in TipoAtivo}

    indicadores = [
        _indicador(
            "IND-01",
            "Total de ativos por status",
            len(ativos),
            "ativos",
            "contagem de ativos agrupada por status",
            len(ativos),
            detalhe=por_status,
        ),
        _indicador(
            "IND-02",
            "Distribuição hardware x software",
            len(ativos),
            "ativos",
            "contagem de ativos agrupada por tipo",
            len(ativos),
            detalhe=por_tipo,
        ),
        _indicador(
            "IND-03",
            "Valor patrimonial bruto",
            _dinheiro(bruto),
            "BRL",
            "soma de valor_compra dos ativos não baixados",
            len(em_operacao),
        ),
        _indicador(
            "IND-04",
            "Valor residual total",
            _dinheiro(residual),
            "BRL",
            "soma do valor residual dos ativos não baixados",
            len(em_operacao),
        ),
        _indicador(
            "IND-05",
            "Percentual depreciado do parque",
            _numero(percentual_depreciado_parque(bruto, residual)),
            "%",
            "(1 - valor residual total / valor patrimonial bruto) * 100",
            len(em_operacao),
        ),
        _indicador(
            "KPI-02",
            "Cobertura de responsáveis",
            _numero(
                percentual(sum(1 for a in ativos_status if a.id in com_vinculo), len(ativos_status))
            ),
            "%",
            "ativos com vínculo aberto / ativos com status ATIVO * 100",
            len(ativos_status),
            meta=98,
            sentido=">=",
        ),
        _indicador(
            "KPI-03",
            "Conformidade de licenças",
            _numero(percentual(len(licencas) - nao_conformes, len(licencas))),
            "%",
            "licenças com uso <= contratado e não vencidas / total de licenças * 100",
            len(licencas),
            meta=100,
            sentido=">=",
        ),
        _indicador(
            "KPI-06",
            "Ativos sem movimentação registrada",
            _numero(percentual(len(ociosos), len(em_operacao))),
            "%",
            "ativos não baixados sem evento há mais de "
            f"{configuracao.meses_sem_movimentacao_alerta} meses / ativos não baixados * 100 "
            "(evento: aquisição ou início/fim de vínculo)",
            len(em_operacao),
            meta=10,
            sentido="<=",
        ),
        _indicador(
            "KPI-07",
            "Idade média do parque",
            _numero(idade_media_meses((a.data_aquisicao for a in em_operacao), referencia)),
            "meses",
            "média de (hoje - data_aquisicao) em meses completos, ativos não baixados",
            len(em_operacao),
        ),
        _indicador(
            "IND-06",
            "Custo médio por ativo",
            None if custo is None else _dinheiro(custo),
            "BRL",
            "valor patrimonial bruto / total de ativos não baixados",
            len(em_operacao),
        ),
        _indicador(
            "IND-07",
            "Taxa de baixas no período",
            _numero(percentual(len(baixas_no_periodo), len(no_inicio))),
            "%",
            f"baixas entre {inicio} e {fim} / ativos existentes em {inicio} * 100",
            len(no_inicio),
        ),
        _indicador(
            "KPI-08",
            "Taxa de baixas com destinação registrada",
            _numero(percentual(sum(1 for a in baixados if a.baixa.destinacao), len(baixados))),
            "%",
            "baixas com destinação / total de baixas * 100",
            len(baixados),
            meta=100,
            sentido=">=",
        ),
    ]
    return IndicadoresResponse(
        data_referencia=referencia,
        filtros_aplicados={
            "categoria_id": categoria_id,
            "setor_id": setor_id,
            "fornecedor_id": fornecedor_id,
            "data_inicio": inicio,
            "data_fim": fim,
        },
        indicadores=indicadores,
    )
