"""add measuring_point entity table

Revision ID: d7e4b1c90a24
Revises: c3a9e1f27b04
Create Date: 2026-10-11 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd7e4b1c90a24'
down_revision: Union[str, None] = 'c3a9e1f27b04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRGM_COLUMNS = ('description', 'equipment', 'functional_location', 'characteristic')


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        'measuring_point',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'public_id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('measuring_point', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('equipment', sa.String(length=64), nullable=True),
        sa.Column('functional_location', sa.String(length=64), nullable=True),
        sa.Column('measured_position', sa.String(length=128), nullable=True),
        sa.Column('characteristic', sa.String(length=128), nullable=True),
        sa.Column('charact_unit', sa.String(length=32), nullable=True),
        sa.Column('reading_transfer', sa.String(length=32), nullable=True),
        sa.Column('annual_estimate', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('upper_mr_limit', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('lower_mr_limit', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('counter', sa.String(length=32), nullable=True),
        sa.Column('decimal_places', sa.String(length=8), nullable=True),
        sa.Column('float_point_exp', sa.String(length=8), nullable=True),
        sa.Column('internal_meas_unit', sa.String(length=32), nullable=True),
        sa.Column('internal_char', sa.String(length=128), nullable=True),
        sa.Column('language', sa.String(length=8), nullable=True),
        sa.Column('meas_point_category', sa.String(length=8), nullable=True),
        sa.Column('meas_range_unit', sa.String(length=32), nullable=True),
        sa.Column('measurement_object_number', sa.String(length=64), nullable=True),
        sa.Column('client', sa.String(length=16), nullable=True),
        sa.Column('supported', sa.String(length=8), nullable=True),
        sa.Column('transfer_mode', sa.String(length=32), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=True),
        sa.Column('created_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('changed_by', sa.String(length=64), nullable=True),
        sa.Column('changed_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('import_job_id', sa.Integer(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False
        ),
        sa.ForeignKeyConstraint(['import_job_id'], ['import_job.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('measuring_point'),
    )
    op.create_index(
        op.f('ix_measuring_point_public_id'), 'measuring_point', ['public_id'], unique=True
    )
    op.create_index(
        op.f('ix_measuring_point_equipment'), 'measuring_point', ['equipment'], unique=False
    )
    op.create_index(
        op.f('ix_measuring_point_functional_location'),
        'measuring_point',
        ['functional_location'],
        unique=False,
    )
    for column in TRGM_COLUMNS:
        op.execute(
            f'CREATE INDEX IF NOT EXISTS ix_measuring_point_{column}_trgm '
            f'ON measuring_point USING gin ("{column}" gin_trgm_ops)'
        )


def downgrade() -> None:
    for column in TRGM_COLUMNS:
        op.execute(f'DROP INDEX IF EXISTS ix_measuring_point_{column}_trgm')
    op.drop_index(op.f('ix_measuring_point_functional_location'), table_name='measuring_point')
    op.drop_index(op.f('ix_measuring_point_equipment'), table_name='measuring_point')
    op.drop_index(op.f('ix_measuring_point_public_id'), table_name='measuring_point')
    op.drop_table('measuring_point')
