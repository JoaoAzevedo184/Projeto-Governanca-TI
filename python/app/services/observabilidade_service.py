"""Saúde e gauges de negócio para `/health` e `/metrics` (FR-014, AC-053, AC-054).

Os gauges de negócio são recalculados do banco a cada leitura de `/metrics`, como todo número
derivado do sistema: nada fica armazenado. Reaproveitam os services de indicadores (FR-009) e de
compliance (FR-007), sem refazer cálculo. Uma falha nesse cálculo é registrada no log e marcada em
`itam_metricas_negocio_up = 0`; o `/metrics` e as métricas técnicas seguem respondendo.
"""

import logging
import time
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import (
    ATIVOS_POR_TIPO,
    ATIVOS_SEM_RESPONSAVEL,
    ATIVOS_TOTAL,
    COMPLIANCE_ALERTAS,
    DATABASE_UP,
    LICENCAS_NAO_CONFORMES,
    LICENCAS_POR_CONFORMIDADE,
    METRICAS_NEGOCIO_DURACAO,
    METRICAS_NEGOCIO_UP,
    PATRIMONIO_REAIS,
)
from app.models.enums import StatusAtivo, TipoAtivo
from app.models.licenca import Licenca
from app.schemas.saude import BancoSaude, SaudeResponse
from app.services.compliance_service import apurar_alertas, licencas_nao_conformes_por_motivo
from app.services.indicador_service import calcular_indicadores
from app.utils.conformidade import CONFORME, SEVERIDADES, status_conformidade

_logger = logging.getLogger("itam.metricas")
_STATUS_LICENCA = (CONFORME, "ALERTA", "NAO_CONFORME")


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
    inicio = time.perf_counter()
    try:
        _atualizar_negocio(db)
    except Exception:  # o cálculo de negócio nunca derruba o /metrics: loga e sinaliza
        db.rollback()
        _logger.exception("falha ao calcular as métricas de negócio")
        METRICAS_NEGOCIO_UP.set(0)
    else:
        METRICAS_NEGOCIO_UP.set(1)
    METRICAS_NEGOCIO_DURACAO.set(time.perf_counter() - inicio)


def _atualizar_negocio(db: Session) -> None:
    indicadores = {i.codigo: i for i in calcular_indicadores(db).indicadores}
    alertas = apurar_alertas(db)
    por_licenca: dict[int, list[str]] = {}
    for alerta in alertas:
        if alerta.entidade == "licenca":
            por_licenca.setdefault(alerta.entidade_id, []).append(alerta.codigo)
    total_licencas = db.scalar(select(func.count()).select_from(Licenca)) or 0
    por_conformidade = dict.fromkeys(_STATUS_LICENCA, 0)
    for codigos in por_licenca.values():
        por_conformidade[status_conformidade(codigos)] += 1
    por_conformidade[CONFORME] += total_licencas - len(por_licenca)

    for status in StatusAtivo:
        ATIVOS_TOTAL.labels(status=status.value).set(
            (indicadores["IND-01"].detalhe or {})[status.value]
        )
    for tipo in TipoAtivo:
        ATIVOS_POR_TIPO.labels(tipo=tipo.value).set(
            (indicadores["IND-02"].detalhe or {})[tipo.value]
        )
    PATRIMONIO_REAIS.labels(base="compra").set(float(Decimal(str(indicadores["IND-03"].valor))))
    PATRIMONIO_REAIS.labels(base="residual").set(float(Decimal(str(indicadores["IND-04"].valor))))
    for situacao, quantidade in por_conformidade.items():
        LICENCAS_POR_CONFORMIDADE.labels(status=situacao).set(quantidade)
    for severidade in SEVERIDADES:
        COMPLIANCE_ALERTAS.labels(severidade=severidade).set(
            sum(1 for a in alertas if a.severidade == severidade)
        )
    ATIVOS_SEM_RESPONSAVEL.set(sum(1 for a in alertas if a.codigo == "CP-04"))
    for motivo, quantidade in licencas_nao_conformes_por_motivo(db, alertas).items():
        LICENCAS_NAO_CONFORMES.labels(motivo=motivo).set(quantidade)
