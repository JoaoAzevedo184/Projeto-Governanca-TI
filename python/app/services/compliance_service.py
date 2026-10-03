"""Painel de compliance (FR-007, AC-022, AC-023, AC-039 a AC-043).

Os alertas são derivados do estado atual no momento da consulta; nada é persistido, então um
alerta some sozinho quando a não conformidade é corrigida (AC-043). Contagem de uso respeita a
Sprint 3: só vínculo ativo conta (BR-021) e vínculo encerrado pela baixa já saiu da conta.
"""

from datetime import date

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ativo import Ativo
from app.models.enums import StatusAtivo
from app.models.historico import HistoricoTransferencia
from app.models.licenca import Licenca
from app.schemas.compliance import AlertaResponse, AlertasResponse, GrupoAlertas
from app.services.licenca_service import contar_em_uso
from app.utils.conformidade import REGRAS, SEVERIDADES, alertas_licenca
from app.utils.datas import hoje


def _alerta(codigo: str, entidade: str, entidade_id: int, recurso: str) -> AlertaResponse:
    regra = REGRAS[codigo]
    return AlertaResponse(
        codigo=codigo,
        severidade=regra.severidade,
        regra=regra.descricao,
        mensagem=regra.mensagem,
        entidade=entidade,
        entidade_id=entidade_id,
        recurso=recurso,
        link=f"/api/v1/{entidade}s/{entidade_id}",
    )


def apurar_alertas(
    db: Session, data_referencia: date | None = None, janela_dias: int | None = None
) -> list[AlertaResponse]:
    referencia = data_referencia or hoje()
    janela = janela_dias if janela_dias is not None else get_settings().janela_alerta_licenca_dias
    alertas: list[AlertaResponse] = []

    licencas = list(db.scalars(select(Licenca).order_by(Licenca.id)))
    em_uso = contar_em_uso(db, [lic.id for lic in licencas])
    for lic in licencas:
        recurso = lic.software or f"Licença perpétua do ativo {lic.ativo_id}"
        for codigo in alertas_licenca(
            lic.quantidade_contratada,
            em_uso.get(lic.id, 0),
            lic.data_expiracao,
            referencia,
            janela,
        ):
            alertas.append(_alerta(codigo, "licenca", lic.id, recurso))

    sem_responsavel = select(Ativo).where(
        Ativo.status == StatusAtivo.ATIVO,
        ~exists().where(
            HistoricoTransferencia.ativo_id == Ativo.id, HistoricoTransferencia.data_fim.is_(None)
        ),
    )
    for ativo in db.scalars(sem_responsavel.order_by(Ativo.id)):
        alertas.append(_alerta("CP-04", "ativo", ativo.id, ativo.nome))
    return alertas


def listar_alertas(db: Session, data_referencia: date | None = None) -> AlertasResponse:
    referencia = data_referencia or hoje()
    alertas = apurar_alertas(db, referencia)
    grupos = []
    for severidade in SEVERIDADES:
        do_grupo = [a for a in alertas if a.severidade == severidade]
        if do_grupo:
            grupos.append(
                GrupoAlertas(severidade=severidade, total=len(do_grupo), alertas=do_grupo)
            )
    return AlertasResponse(
        data_referencia=referencia,
        total=len(alertas),
        por_severidade={s: sum(1 for a in alertas if a.severidade == s) for s in SEVERIDADES},
        grupos=grupos,
    )


def licencas_nao_conformes_por_motivo(db: Session) -> dict[str, int]:
    """Gauge `itam_licencas_nao_conformes{motivo}`: CP-01 (vencida) e CP-02 (acima do uso)."""
    alertas = apurar_alertas(db)
    return {
        "vencida": sum(1 for a in alertas if a.codigo == "CP-01"),
        "acima_do_contratado": sum(1 for a in alertas if a.codigo == "CP-02"),
    }
