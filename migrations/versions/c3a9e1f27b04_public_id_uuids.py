"""add public uuid identifiers to entity tables

Revision ID: c3a9e1f27b04
Revises: 9f2c4a17bd03
Create Date: 2026-10-11 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c3a9e1f27b04'
down_revision: Union[str, None] = '9f2c4a17bd03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ('equipment', 'functional_location', 'measuring_document', 'notification', 'work_order')


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            f"ALTER TABLE {table} "
            f"ADD COLUMN IF NOT EXISTS public_id uuid NOT NULL DEFAULT gen_random_uuid()"
        )
        op.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS ix_{table}_public_id ON {table} (public_id)"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_public_id")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS public_id")
