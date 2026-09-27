from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import TipoAtivo, check_in


class Categoria(Base):
    __tablename__ = "categoria"
    __table_args__ = (
        CheckConstraint("vida_util_meses > 0", name="ck_categoria_vida_util_positiva"),
        CheckConstraint(check_in("tipo_aplicavel", TipoAtivo), name="ck_categoria_tipo_aplicavel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    descricao: Mapped[str | None] = mapped_column(String(255))
    vida_util_meses: Mapped[int] = mapped_column(Integer)
    tipo_aplicavel: Mapped[TipoAtivo] = mapped_column(String(10))
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
