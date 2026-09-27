from sqlalchemy.orm import Session

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
