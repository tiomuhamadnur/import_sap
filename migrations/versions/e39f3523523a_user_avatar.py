"""user avatar

Revision ID: e39f3523523a
Revises: e2f5a7c3b901
Create Date: 2026-10-11 17:07:59.166628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e39f3523523a'
down_revision: Union[str, None] = 'e2f5a7c3b901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar')
