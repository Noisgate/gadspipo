"""add campaign investigations table

Revision ID: 004_add_campaign_investigations_table
Revises: 003_add_campaign_delivery_columns
Create Date: 2026-03-31 21:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_add_campaign_investigations_table'
down_revision = '003_add_campaign_delivery_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'campaign_investigations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'PLAN_READY', 'APPROVED', 'EXECUTED', name='investigation_status'), nullable=False),
        sa.Column('analysis_mode', sa.String(length=32), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=False),
        sa.Column('diagnosis', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('repair_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('approval_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_campaign_investigation_campaign_id', 'campaign_investigations', ['campaign_id'], unique=False)
    op.create_index('idx_campaign_investigation_user_id', 'campaign_investigations', ['user_id'], unique=False)
    op.create_index('idx_campaign_investigation_created_at', 'campaign_investigations', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_campaign_investigation_created_at', table_name='campaign_investigations')
    op.drop_index('idx_campaign_investigation_user_id', table_name='campaign_investigations')
    op.drop_index('idx_campaign_investigation_campaign_id', table_name='campaign_investigations')
    op.drop_table('campaign_investigations')
    sa.Enum(name='investigation_status').drop(op.get_bind(), checkfirst=False)
