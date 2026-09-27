from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import PerfilUsuario, check_in


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (CheckConstraint(check_in("perfil", PerfilUsuario), name="ck_usuario_perfil"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(80), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    nome: Mapped[str] = mapped_column(String(160))
    perfil: Mapped[PerfilUsuario] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
