"""trigram indexes for data page search and relation filters

Revision ID: 9f2c4a17bd03
Revises: 6417bd42bf48
Create Date: 2026-10-11 14:32:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = '9f2c4a17bd03'
down_revision: Union[str, None] = '6417bd42bf48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ('equipment', 'functional_location', 'measuring_document', 'notification', 'work_order')

RELATION_COLUMNS = {
    'equipment': ('functional_location',),
    'functional_location': ('sup_funcloc', 'equip_installed'),
    'measuring_document': ('equipment', 'functional_location', 'notification', 'order'),
    'notification': ('equipment', 'functional_location', 'order'),
    'work_order': ('equipment', 'functional_location', 'notification'),
}


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for table in TABLES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS ix_{table}_description_trgm "
            f"ON {table} USING gin (description gin_trgm_ops)"
        )
    for table, columns in RELATION_COLUMNS.items():
        for column in columns:
            op.execute(
                f'CREATE INDEX IF NOT EXISTS ix_{table}_{column}_trgm '
                f'ON {table} USING gin ("{column}" gin_trgm_ops)'
            )


def downgrade() -> None:
    for table, columns in RELATION_COLUMNS.items():
        for column in columns:
            op.execute(f"DROP INDEX IF EXISTS ix_{table}_{column}_trgm")
    for table in TABLES:
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_description_trgm")
