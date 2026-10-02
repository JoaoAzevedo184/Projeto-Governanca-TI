from datetime import datetime

from sqlalchemy import DDL, JSON, DateTime, ForeignKey, Integer, String, event, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    operacao: Mapped[str] = mapped_column(String(20))
    entidade: Mapped[str] = mapped_column(String(80))
    entidade_id: Mapped[int | None] = mapped_column(Integer)
    resultado: Mapped[str] = mapped_column(String(20))
    regra_violada: Mapped[str | None] = mapped_column(String(20))
    detalhe: Mapped[dict | None] = mapped_column(JSON)
    carimbo: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Trigger de imutabilidade (NFR-AUD-01, ADR-005): a trilha é append-only no banco. A migração
# 25b1f6d20128 aplica a mesma DDL (cópia congelada). Só PostgreSQL; no SQLite não há trigger.
FUNCAO_BLOQUEAR_MUTACAO = """
CREATE OR REPLACE FUNCTION bloquear_mutacao() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Registro histórico é imutável (NFR-AUD-01)';
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_AUDIT_IMUTAVEL = """
CREATE TRIGGER tg_audit_imutavel
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION bloquear_mutacao();
"""

event.listen(
    AuditLog.__table__,
    "after_create",
    DDL(FUNCAO_BLOQUEAR_MUTACAO).execute_if(dialect="postgresql"),
)
event.listen(
    AuditLog.__table__, "after_create", DDL(TRIGGER_AUDIT_IMUTAVEL).execute_if(dialect="postgresql")
)
