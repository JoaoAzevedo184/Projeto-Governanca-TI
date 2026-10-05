"""ativo chave licenca unica

Revision ID: d4a6c8e0f1b2
Revises: c9e4a7d25f83
Create Date: 2026-10-05 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a6c8e0f1b2'
down_revision: str | None = 'c9e4a7d25f83'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # BR-039: índice único parcial, só para chave preenchida. Falha se a base já tiver chave
    # repetida em ativo: nada é apagado, a equipe resolve os duplicados e roda de novo.
    op.create_index('ux_ativo_chave_licenca', 'ativo', ['chave_licenca'], unique=True,
                    postgresql_where=sa.text('chave_licenca IS NOT NULL'),
                    sqlite_where=sa.text('chave_licenca IS NOT NULL'))


def downgrade() -> None:
    op.drop_index('ux_ativo_chave_licenca', table_name='ativo',
                  postgresql_where=sa.text('chave_licenca IS NOT NULL'),
                  sqlite_where=sa.text('chave_licenca IS NOT NULL'))
