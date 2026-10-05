from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(160))
    cnpj: Mapped[str | None] = mapped_column(String(18), unique=True)
    contato: Mapped[str | None] = mapped_column(String(120))
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    data_source: Mapped[str] = mapped_column(String(20), default="sintetico")


class FornecedorAvaliacao(Base):
    """Uma nota de um critério do scorecard de fornecedores (FR-011). O scorecard é a soma
    ponderada das linhas do mesmo fornecedor e período; a pontuação não é guardada, é derivada."""

    __tablename__ = "fornecedor_avaliacao"
    __table_args__ = (
        CheckConstraint("peso > 0 AND peso <= 100", name="ck_avaliacao_peso"),
        CheckConstraint("nota BETWEEN 0 AND 10", name="ck_avaliacao_nota"),
        Index("ix_avaliacao_fornecedor", "fornecedor_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"))
    criterio: Mapped[str] = mapped_column(String(80))
    peso: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    nota: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    periodo: Mapped[str] = mapped_column(String(20))
    data_source: Mapped[str] = mapped_column(String(20), default="manual")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
