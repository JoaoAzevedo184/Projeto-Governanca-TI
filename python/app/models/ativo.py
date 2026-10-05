from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import baixa as _baixa  # noqa: F401 — registra BaixaAtivo para o relationship
from app.models.base import Base, TimestampMixin
from app.models.enums import StatusAtivo, TipoAtivo, check_in


class Ativo(Base, TimestampMixin):
    __tablename__ = "ativo"
    __table_args__ = (
        CheckConstraint("length(nome) >= 3", name="ck_ativo_nome_minimo"),
        CheckConstraint(check_in("tipo", TipoAtivo), name="ck_ativo_tipo"),
        CheckConstraint(check_in("status", StatusAtivo), name="ck_ativo_status"),
        CheckConstraint("valor_compra > 0", name="ck_ativo_valor_positivo"),
        CheckConstraint("vida_util_meses > 0", name="ck_ativo_vida_util_positiva"),
        CheckConstraint(
            "(tipo = 'HARDWARE' AND numero_serie IS NOT NULL) OR "
            "(tipo = 'SOFTWARE' AND chave_licenca IS NOT NULL)",
            name="ck_ativo_identificador",
        ),
        Index("ix_ativo_status", "status"),
        Index("ix_ativo_categoria_id", "categoria_id"),
        Index("ix_ativo_fornecedor_id", "fornecedor_id"),
        Index("ix_ativo_data_aquisicao", "data_aquisicao"),
        # BR-039: a chave de licença é única entre os ativos; só vale quando preenchida.
        Index(
            "ux_ativo_chave_licenca",
            "chave_licenca",
            unique=True,
            postgresql_where=text("chave_licenca IS NOT NULL"),
            sqlite_where=text("chave_licenca IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[TipoAtivo] = mapped_column(String(10))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"))
    numero_serie: Mapped[str | None] = mapped_column(String(80), unique=True)
    chave_licenca: Mapped[str | None] = mapped_column(String(200))
    data_aquisicao: Mapped[date] = mapped_column(Date)
    valor_compra: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    vida_util_meses: Mapped[int] = mapped_column(Integer)
    status: Mapped[StatusAtivo] = mapped_column(String(20), default=StatusAtivo.ATIVO)
    localizacao: Mapped[str | None] = mapped_column(String(120))
    observacoes: Mapped[str | None] = mapped_column(String(500))
    lote_importacao_id: Mapped[int | None] = mapped_column(ForeignKey("lote_importacao.id"))
    data_source: Mapped[str] = mapped_column(String(20))

    categoria = relationship("Categoria")
    fornecedor = relationship("Fornecedor")
    baixa = relationship("BaixaAtivo", back_populates="ativo", uselist=False)
