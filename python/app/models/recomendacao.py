from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import EVIDENCIAS_SEM_REFERENCIA, StatusRecomendacao, TipoEvidencia, check_in

_SEM_REFERENCIA_SQL = ", ".join(f"'{t.value}'" for t in sorted(EVIDENCIAS_SEM_REFERENCIA))


class Recomendacao(Base):
    """Recomendação de decisão (FR-013). É registrada por uma pessoa: o sistema não a gera.

    BR-027 (nenhuma recomendação sem evidência) não cabe numa constraint simples e é garantida
    pelo serviço, que cria a recomendação e as evidências na mesma transação (invariantes.md).
    """

    __tablename__ = "recomendacao"
    __table_args__ = (
        CheckConstraint("length(titulo) >= 3", name="ck_recomendacao_titulo_minimo"),
        CheckConstraint(check_in("status", StatusRecomendacao), name="ck_recomendacao_status"),
        Index("ix_recomendacao_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(160))
    contexto: Mapped[str] = mapped_column(String(2000))
    recomendacao: Mapped[str] = mapped_column(String(2000))
    alternativas: Mapped[str | None] = mapped_column(String(2000))
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("responsavel.id"))
    data: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default=StatusRecomendacao.PROPOSTA.value)
    data_source: Mapped[str] = mapped_column(String(20), default="manual")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidencias: Mapped[list["Evidencia"]] = relationship(
        back_populates="recomendacao", order_by="Evidencia.id", cascade="all, delete-orphan"
    )


class Evidencia(Base):
    __tablename__ = "evidencia"
    __table_args__ = (
        CheckConstraint(check_in("tipo", TipoEvidencia), name="ck_evidencia_tipo"),
        # Risco, ativo, licença e scorecard apontam para um registro; os demais não têm registro.
        CheckConstraint(
            f"tipo IN ({_SEM_REFERENCIA_SQL}) OR referencia_id IS NOT NULL",
            name="ck_evidencia_referencia",
        ),
        CheckConstraint(
            f"tipo NOT IN ({_SEM_REFERENCIA_SQL})"
            " OR (descricao IS NOT NULL AND length(descricao) >= 3)",
            name="ck_evidencia_descricao",
        ),
        Index("ix_evidencia_recomendacao", "recomendacao_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recomendacao_id: Mapped[int] = mapped_column(ForeignKey("recomendacao.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20))
    referencia_id: Mapped[int | None] = mapped_column(Integer)
    descricao: Mapped[str | None] = mapped_column(String(500))

    recomendacao: Mapped[Recomendacao] = relationship(back_populates="evidencias")
