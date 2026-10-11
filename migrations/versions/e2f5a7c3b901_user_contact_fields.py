"""add user name, email, phone; make username optional

Revision ID: e2f5a7c3b901
Revises: d7e4b1c90a24
Create Date: 2026-10-11 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'e2f5a7c3b901'
down_revision: Union[str, None] = 'd7e4b1c90a24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name varchar(128)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email varchar(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone varchar(32)")
    op.execute("ALTER TABLE users ALTER COLUMN username DROP NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("UPDATE users SET name = username WHERE name IS NULL")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_email")
    op.execute("UPDATE users SET username = COALESCE(email, 'user_' || id) WHERE username IS NULL")
    op.execute("ALTER TABLE users ALTER COLUMN username SET NOT NULL")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS name")
