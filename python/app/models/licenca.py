from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import TipoLicenciamento, check_in


class Licenca(Base):
    """Contrato de direito de uso de software (FR-004, ADR-012).

    Só o contrato: o valor patrimonial da licença perpétua fica no ativo `SOFTWARE`. A quantidade
    em uso não é coluna: é o COUNT dos vínculos ativos (BR-021, ADR-008).
    """

    __tablename__ = "licenca"
    __table_args__ = (
        CheckConstraint(
            check_in("tipo_licenciamento", TipoLicenciamento), name="ck_licenca_tipo_licenciamento"
        ),
        CheckConstraint("quantidade_contratada >= 1", name="ck_licenca_quantidade_minima"),
        CheckConstraint("data_expiracao > data_inicio_vigencia", name="ck_licenca_vigencia"),
        CheckConstraint("valor_total IS NULL OR valor_total > 0", name="ck_licenca_valor_positivo"),
        # Um único dono para nome e valor (ADR-012, item 4 da resolução do Sprint 2): perpétua
        # aponta para o ativo; subscrição e OEM não são ativo e guardam o nome aqui.
        CheckConstraint(
            "(tipo_licenciamento = 'PERPETUA' AND ativo_id IS NOT NULL"
            " AND software IS NULL AND valor_total IS NULL) OR "
            "(tipo_licenciamento = 'SUBSCRICAO' AND ativo_id IS NULL"
            " AND software IS NOT NULL AND valor_total IS NOT NULL) OR "
            "(tipo_licenciamento = 'OEM' AND ativo_id IS NULL"
            " AND software IS NOT NULL AND valor_total IS NULL)",
            name="ck_licenca_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Deve apontar para ativo SOFTWARE; o CHECK não enxerga outra tabela, então o serviço valida.
    ativo_id: Mapped[int | None] = mapped_column(ForeignKey("ativo.id"))
    software: Mapped[str | None] = mapped_column(String(120))
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"))
    chave_licenca: Mapped[str] = mapped_column(String(200))
    quantidade_contratada: Mapped[int] = mapped_column(Integer)
    data_inicio_vigencia: Mapped[date] = mapped_column(Date)
    data_expiracao: Mapped[date] = mapped_column(Date)
    valor_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    tipo_licenciamento: Mapped[str] = mapped_column(String(20))
    data_source: Mapped[str] = mapped_column(String(20))


class LicencaVinculo(Base):
    """Instalação da licença numa máquina: `ativo_id` é a máquina hospedeira (item 5 da resolução
    do Sprint 2). O desvínculo é lógico (`ativo_vinculo = false`); nada é apagado."""

    __tablename__ = "licenca_vinculo"
    __table_args__ = (
        # Uma máquina conta uma vez por licença: só o banco garante sob concorrência.
        Index(
            "ux_licenca_ativo",
            "licenca_id",
            "ativo_id",
            unique=True,
            postgresql_where=text("ativo_vinculo = true"),
            sqlite_where=text("ativo_vinculo = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    licenca_id: Mapped[int] = mapped_column(ForeignKey("licenca.id"))
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativo.id"))
    data_vinculo: Mapped[date] = mapped_column(Date)
    ativo_vinculo: Mapped[bool] = mapped_column(Boolean, default=True)
    data_source: Mapped[str] = mapped_column(String(20))
