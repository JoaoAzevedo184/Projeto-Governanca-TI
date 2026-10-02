from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    DDL,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DestinacaoBaixa, MotivoBaixa, check_in

# Trigger de imutabilidade (BR-025, NFR-AUD-01, ADR-005): docs/modelo-de-dados/invariantes.md.
# Reusa a função bloquear_mutacao() criada para audit_log (CREATE OR REPLACE: idempotente). Só
# PostgreSQL; a mesma DDL é aplicada pela migração da Sprint 3 (cópia congelada).
FUNCAO_BLOQUEAR_MUTACAO = """
CREATE OR REPLACE FUNCTION bloquear_mutacao() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Registro histórico é imutável (NFR-AUD-01)';
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_BAIXA_IMUTAVEL = """
CREATE TRIGGER tg_baixa_imutavel
  BEFORE UPDATE OR DELETE ON baixa_ativo
  FOR EACH ROW EXECUTE FUNCTION bloquear_mutacao();
"""


class BaixaAtivo(Base):
    """Baixa de ativo (FR-005): append-only; o valor residual fica congelado (BR-015)."""

    __tablename__ = "baixa_ativo"
    __table_args__ = (
        CheckConstraint(check_in("motivo", MotivoBaixa), name="ck_baixa_motivo"),
        CheckConstraint(check_in("destinacao", DestinacaoBaixa), name="ck_baixa_destinacao"),
        CheckConstraint("valor_residual_baixa >= 0", name="ck_baixa_residual_nao_negativo"),
        CheckConstraint(
            "motivo <> 'OUTRO' OR (justificativa IS NOT NULL AND length(justificativa) >= 10)",
            name="ck_baixa_justificativa",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # UNIQUE torna BR-024 uma garantia do banco, não uma verificação que falha sob concorrência.
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativo.id"), unique=True)
    motivo: Mapped[str] = mapped_column(String(20))
    justificativa: Mapped[str | None] = mapped_column(String(500))
    data_baixa: Mapped[date] = mapped_column(Date)
    destinacao: Mapped[str] = mapped_column(String(30))
    valor_residual_baixa: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    registrado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    data_source: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ativo = relationship("Ativo", back_populates="baixa")


event.listen(
    BaixaAtivo.__table__,
    "after_create",
    DDL(FUNCAO_BLOQUEAR_MUTACAO).execute_if(dialect="postgresql"),
)
event.listen(
    BaixaAtivo.__table__,
    "after_create",
    DDL(TRIGGER_BAIXA_IMUTAVEL).execute_if(dialect="postgresql"),
)
