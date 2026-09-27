from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Setor(Base):
    __tablename__ = "setor"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    sigla: Mapped[str | None] = mapped_column(String(12))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
