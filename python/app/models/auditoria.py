from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
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
