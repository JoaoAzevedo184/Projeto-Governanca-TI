"""audit_log imutavel

Revision ID: 25b1f6d20128
Revises: c8365ce7e5e4
Create Date: 2026-10-02

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '25b1f6d20128'
down_revision: str | None = 'c8365ce7e5e4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Trigger de imutabilidade da trilha de auditoria (NFR-AUD-01, ADR-005) — cópia congelada da DDL
# de app/models/auditoria.py (migração não importa modelo, que muda ao longo do tempo).
FUNCAO_BLOQUEAR_MUTACAO = """
CREATE OR REPLACE FUNCTION bloquear_mutacao() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Registro histórico é imutável (NFR-AUD-01)';
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER_AUDIT_IMUTAVEL = """
CREATE TRIGGER tg_audit_imutavel
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION bloquear_mutacao();
"""


def _postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _postgres():
        op.execute(FUNCAO_BLOQUEAR_MUTACAO)
        op.execute(TRIGGER_AUDIT_IMUTAVEL)


def downgrade() -> None:
    if _postgres():
        op.execute("DROP TRIGGER IF EXISTS tg_audit_imutavel ON audit_log")
        op.execute("DROP FUNCTION IF EXISTS bloquear_mutacao()")
