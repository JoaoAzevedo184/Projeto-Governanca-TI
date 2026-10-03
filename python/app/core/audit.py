from typing import NoReturn

from sqlalchemy.orm import Session

from app.core.exceptions import RegraNegocioError
from app.core.metrics import REGRAS_VIOLADAS
from app.models.auditoria import AuditLog


def registrar_auditoria(
    db: Session,
    *,
    usuario_id: int | None,
    operacao: str,
    entidade: str,
    entidade_id: int | None,
    resultado: str = "SUCESSO",
    regra_violada: str | None = None,
    detalhe: dict | None = None,
) -> None:
    """Registra uma linha na trilha de auditoria (BR-030, AC-057). Append-only, nunca editar."""
    if resultado == "RECUSADO" and regra_violada:
        # Único ponto do contador: toda recusa por regra passa por aqui para ser auditada.
        REGRAS_VIOLADAS.labels(regra=regra_violada).inc()
    db.add(
        AuditLog(
            usuario_id=usuario_id,
            operacao=operacao,
            entidade=entidade,
            entidade_id=entidade_id,
            resultado=resultado,
            regra_violada=regra_violada,
            detalhe=detalhe,
        )
    )


def recusar_operacao(
    db: Session,
    *,
    usuario_id: int,
    operacao: str,
    entidade: str,
    regra: str,
    mensagem: str,
    detalhe: dict | None = None,
) -> NoReturn:
    """Registra a recusa por regra de negócio na auditoria (NFR-AUD-05) e devolve o 409.

    Faz commit: a linha RECUSADO precisa sobreviver ao erro. Quem chama não pode ter escritas
    pendentes que devam ser desfeitas (use rollback ou savepoint antes).
    """
    registrar_auditoria(
        db,
        usuario_id=usuario_id,
        operacao=operacao,
        entidade=entidade,
        entidade_id=None,
        resultado="RECUSADO",
        regra_violada=regra,
        detalhe=detalhe,
    )
    db.commit()
    raise RegraNegocioError(mensagem, regra=regra)
