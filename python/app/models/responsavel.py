from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Responsavel(Base):
    __tablename__ = "responsavel"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160))
    matricula: Mapped[str | None] = mapped_column(String(30), unique=True)
    email: Mapped[str | None] = mapped_column(String(160))
    cargo: Mapped[str | None] = mapped_column(String(120))
    localizacao: Mapped[str | None] = mapped_column(String(120))
    setor_id: Mapped[int | None] = mapped_column(ForeignKey("setor.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    data_source: Mapped[str] = mapped_column(String(20), default="sintetico")
