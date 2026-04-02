"""Add campaign delivery diagnosis columns.

Revision ID: 003
Revises: 002
Create Date: 2026-03-31 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('campaigns', sa.Column('primary_status', sa.String(length=64), nullable=True))
    op.add_column('campaigns', sa.Column('primary_status_reasons', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('campaigns', 'primary_status_reasons')
    op.drop_column('campaigns', 'primary_status')
