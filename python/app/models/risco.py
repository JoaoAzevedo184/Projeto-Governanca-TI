from datetime import date

from sqlalchemy import CheckConstraint, Computed, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import CategoriaRisco, RespostaRisco, StatusRisco, check_in


class Risco(Base, TimestampMixin):
    """Registro formal de risco do parque de TI (FR-012). O `score` é coluna gerada pelo banco
    (probabilidade × impacto), nunca informado; a classificação sai de `utils/risco.py`."""

    __tablename__ = "risco"
    __table_args__ = (
        CheckConstraint("length(titulo) >= 3", name="ck_risco_titulo_minimo"),
        CheckConstraint(check_in("categoria", CategoriaRisco), name="ck_risco_categoria"),
        CheckConstraint(check_in("resposta", RespostaRisco), name="ck_risco_resposta"),
        CheckConstraint(check_in("status", StatusRisco), name="ck_risco_status"),
        CheckConstraint("probabilidade BETWEEN 1 AND 5", name="ck_risco_probabilidade"),
        CheckConstraint("impacto BETWEEN 1 AND 5", name="ck_risco_impacto"),
        Index("ix_risco_score", "score"),
        Index("ix_risco_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(160))
    descricao: Mapped[str | None] = mapped_column(String(1000))
    categoria: Mapped[str] = mapped_column(String(20))
    probabilidade: Mapped[int] = mapped_column(Integer)
    impacto: Mapped[int] = mapped_column(Integer)
    score: Mapped[int] = mapped_column(Integer, Computed("probabilidade * impacto", persisted=True))
    resposta: Mapped[str] = mapped_column(String(20))
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("responsavel.id"))
    status: Mapped[str] = mapped_column(String(20), default=StatusRisco.ABERTO.value)
    gatilho: Mapped[str | None] = mapped_column(String(255))
    data_revisao: Mapped[date | None] = mapped_column(Date)
    data_source: Mapped[str] = mapped_column(String(20), default="manual")
