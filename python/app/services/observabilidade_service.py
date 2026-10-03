"""Saúde e gauges de negócio para `/health` e `/metrics` (FR-014, AC-053, AC-054).

Os gauges (`itam_ativos_total`, `itam_licencas_nao_conformes`) são recalculados do banco a cada
leitura de `/metrics`, como todo número derivado do sistema: nada fica armazenado.
"""

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import ATIVOS_TOTAL, DATABASE_UP, LICENCAS_NAO_CONFORMES
from app.models.ativo import Ativo
from app.models.enums import StatusAtivo
from app.schemas.saude import BancoSaude, SaudeResponse
from app.services.compliance_service import licencas_nao_conformes_por_motivo


def _banco_responde(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


def estado_saude(db: Session) -> SaudeResponse:
    configuracao = get_settings()
    banco_ok = _banco_responde(db)
    return SaudeResponse(
        status="UP" if banco_ok else "DOWN",
        environment=configuracao.environment,
        database=BancoSaude(
            status="UP" if banco_ok else "DOWN", dialect=db.get_bind().dialect.name
        ),
        version=configuracao.app_version,
    )


def atualizar_gauges(db: Session) -> None:
    """Recalcula os gauges de negócio; com o banco fora do ar, só marca `itam_database_up = 0`."""
    if not _banco_responde(db):
        DATABASE_UP.set(0)
        return
    DATABASE_UP.set(1)
    por_status = {
        status: quantidade
        for status, quantidade in db.execute(
            select(Ativo.status, func.count()).group_by(Ativo.status)
        )
    }
    for status in StatusAtivo:
        ATIVOS_TOTAL.labels(status=status.value).set(por_status.get(status.value, 0))
    for motivo, quantidade in licencas_nao_conformes_por_motivo(db).items():
        LICENCAS_NAO_CONFORMES.labels(motivo=motivo).set(quantidade)
