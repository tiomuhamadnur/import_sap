"""import engine columns: job progress/options/preview, record rollback data

Revision ID: 6417bd42bf48
Revises: ba896b3612a0
Create Date: 2026-10-11 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '6417bd42bf48'
down_revision: Union[str, None] = 'ba896b3612a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('import_job', sa.Column('storage_path', sa.String(length=512), nullable=True))
    op.add_column('import_job', sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('import_job', sa.Column('preview', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('import_job', sa.Column('processed', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('import_job', sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('import_job', sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True))

    op.add_column('import_record_result', sa.Column('entity_id', sa.Integer(), nullable=True))
    op.add_column('import_record_result', sa.Column('before_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index(op.f('ix_import_record_result_entity_id'), 'import_record_result', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_import_record_result_entity_id'), table_name='import_record_result')
    op.drop_column('import_record_result', 'before_data')
    op.drop_column('import_record_result', 'entity_id')

    op.drop_column('import_job', 'rolled_back_at')
    op.drop_column('import_job', 'queued_at')
    op.drop_column('import_job', 'processed')
    op.drop_column('import_job', 'preview')
    op.drop_column('import_job', 'options')
    op.drop_column('import_job', 'storage_path')
