from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LoteImportacao(Base):
    __tablename__ = "lote_importacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    data_importacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    total_processado: Mapped[int] = mapped_column(Integer, default=0)
    total_aceito: Mapped[int] = mapped_column(Integer, default=0)
    total_rejeitado: Mapped[int] = mapped_column(Integer, default=0)


class ErroImportacao(Base):
    __tablename__ = "erro_importacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote_importacao.id"))
    numero_linha: Mapped[int] = mapped_column(Integer)
    campo: Mapped[str] = mapped_column(String(80))
    valor_recebido: Mapped[str | None] = mapped_column(String(255))
    motivo: Mapped[str] = mapped_column(String(255))
