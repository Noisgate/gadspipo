"""Add search_terms table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-30 17:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'search_terms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('term', sa.String(length=255), nullable=False),
        sa.Column('match_type', sa.String(length=50), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Float(), nullable=False, server_default='0'),
        sa.Column('cost', sa.DECIMAL(12, 2), nullable=False, server_default='0'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'term', name='uq_campaign_search_term'),
    )
    op.create_index('idx_search_term_campaign_id', 'search_terms', ['campaign_id'])
    op.create_index('idx_search_term_clicks', 'search_terms', ['clicks'])


def downgrade() -> None:
    op.drop_index('idx_search_term_clicks', table_name='search_terms')
    op.drop_index('idx_search_term_campaign_id', table_name='search_terms')
    op.drop_table('search_terms')
