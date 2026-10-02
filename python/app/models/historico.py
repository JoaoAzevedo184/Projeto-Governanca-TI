from datetime import date, datetime

from sqlalchemy import (
    DDL,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    event,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Trigger de imutabilidade (BR-011, BR-025, NFR-AUD-01, ADR-005):
# docs/modelo-de-dados/invariantes.md.
# Permite uma única transição: data_fim de NULL para preenchida, sem alterar nenhuma outra coluna.
# Só PostgreSQL; a mesma DDL é aplicada pela migração do Sprint 2.
FUNCAO_PERMITIR_APENAS_ENCERRAMENTO = """
CREATE OR REPLACE FUNCTION permitir_apenas_encerramento() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Vínculo histórico não pode ser excluído (BR-025)';
  END IF;
  IF OLD.data_fim IS NOT NULL THEN
    RAISE EXCEPTION 'Vínculo já encerrado é imutável (BR-011)';
  END IF;
  IF NEW.id                IS DISTINCT FROM OLD.id
  OR NEW.ativo_id          IS DISTINCT FROM OLD.ativo_id
  OR NEW.responsavel_id    IS DISTINCT FROM OLD.responsavel_id
  OR NEW.setor_id          IS DISTINCT FROM OLD.setor_id
  OR NEW.data_inicio       IS DISTINCT FROM OLD.data_inicio
  OR NEW.motivo            IS DISTINCT FROM OLD.motivo
  OR NEW.registrado_por_id IS DISTINCT FROM OLD.registrado_por_id
  OR NEW.data_source       IS DISTINCT FROM OLD.data_source
  OR NEW.criado_em         IS DISTINCT FROM OLD.criado_em THEN
    RAISE EXCEPTION 'Somente data_fim pode ser preenchida (BR-011)';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_HISTORICO_IMUTAVEL = """
CREATE TRIGGER tg_historico_imutavel
  BEFORE UPDATE OR DELETE ON historico_transferencia
  FOR EACH ROW EXECUTE FUNCTION permitir_apenas_encerramento();
"""


class HistoricoTransferencia(Base):
    """Vínculo temporal ativo × responsável (FR-002). Append-only: só `data_fim` é preenchível."""

    __tablename__ = "historico_transferencia"
    __table_args__ = (
        CheckConstraint(
            "data_fim IS NULL OR data_fim >= data_inicio", name="ck_historico_periodo_valido"
        ),
        # BR-007 / ADR-006: um único vínculo aberto por ativo, garantido pelo banco.
        Index(
            "ux_vinculo_aberto",
            "ativo_id",
            unique=True,
            postgresql_where=text("data_fim IS NULL"),
            sqlite_where=text("data_fim IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ativo_id: Mapped[int] = mapped_column(ForeignKey("ativo.id"))
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("responsavel.id"))
    setor_id: Mapped[int] = mapped_column(ForeignKey("setor.id"))
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    motivo: Mapped[str | None] = mapped_column(String(200))
    registrado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    data_source: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


event.listen(
    HistoricoTransferencia.__table__,
    "after_create",
    DDL(FUNCAO_PERMITIR_APENAS_ENCERRAMENTO).execute_if(dialect="postgresql"),
)
event.listen(
    HistoricoTransferencia.__table__,
    "after_create",
    DDL(TRIGGER_HISTORICO_IMUTAVEL).execute_if(dialect="postgresql"),
)
