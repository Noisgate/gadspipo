"""Initial schema creation.

Revision ID: 001
Revises:
Create Date: 2024-03-23 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""

    # Create ENUM types
    op.execute("CREATE TYPE campaign_status AS ENUM ('ENABLED', 'PAUSED', 'REMOVED')")
    op.execute("CREATE TYPE campaign_type AS ENUM ('SEARCH', 'DISPLAY', 'SHOPPING', 'VIDEO', 'PERFORMANCE_MAX')")
    op.execute("CREATE TYPE match_type AS ENUM ('EXACT', 'PHRASE', 'BROAD', 'BROAD_MODIFIER')")
    op.execute("CREATE TYPE recommendation_type AS ENUM ('BID_ADJUSTMENT', 'KEYWORD_ADD', 'KEYWORD_REMOVE', 'AD_COPY', 'BUDGET_REALLOC', 'PAUSE_UNDERPERFORMING')")
    op.execute("CREATE TYPE priority AS ENUM ('HIGH', 'MEDIUM', 'LOW')")
    op.execute("CREATE TYPE rec_status AS ENUM ('OPEN', 'ACCEPTED', 'REJECTED', 'EXECUTED')")
    op.execute("CREATE TYPE rule_type AS ENUM ('BID_ADJUSTMENT', 'PAUSE_LOW_PERFORMERS', 'ENABLE_KEYWORDS', 'DAILY_BUDGET_CONTROL')")
    op.execute("CREATE TYPE action_type AS ENUM ('CAMPAIGN_PAUSE', 'BID_UPDATE', 'KEYWORD_ADD', 'AUTOMATION_RUN', 'RECOMMENDATION_ACCEPT', 'ACCOUNT_CONNECT', 'ACCOUNT_DISCONNECT')")
    op.execute("CREATE TYPE resource_type AS ENUM ('CAMPAIGN', 'KEYWORD', 'AUTOMATION', 'ACCOUNT_CONNECTION')")
    op.execute("CREATE TYPE action_source AS ENUM ('MANUAL', 'AUTOMATION', 'RECOMMENDATION')")
    op.execute("CREATE TYPE notification_type AS ENUM ('ALERT_UNDERPERFORMING', 'RECOMMENDATION', 'AUTOMATION_EXECUTED', 'SYNC_COMPLETE', 'ERROR')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('oauth_google_id', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_email'),
        sa.UniqueConstraint('oauth_google_id', name='uq_user_oauth_google_id'),
    )
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_oauth_google_id', 'users', ['oauth_google_id'])

    # Create google_ads_accounts table
    op.create_table(
        'google_ads_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', sa.String(16), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(), nullable=False),
        sa.Column('connected_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'customer_id', name='uq_user_customer'),
    )
    op.create_index('idx_account_user_id', 'google_ads_accounts', ['user_id'])
    op.create_index('idx_account_customer_id', 'google_ads_accounts', ['customer_id'])

    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('google_campaign_id', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('ENABLED', 'PAUSED', 'REMOVED', name='campaign_status'), nullable=False, server_default='ENABLED'),
        sa.Column('campaign_type', sa.Enum('SEARCH', 'DISPLAY', 'SHOPPING', 'VIDEO', 'PERFORMANCE_MAX', name='campaign_type'), nullable=False, server_default='SEARCH'),
        sa.Column('budget_daily', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['google_ads_accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'google_campaign_id', name='uq_account_google_campaign'),
    )
    op.create_index('idx_campaign_account_id', 'campaigns', ['account_id'])
    op.create_index('idx_campaign_status', 'campaigns', ['status'])

    # Create campaign_metrics table (for TimescaleDB hypertable)
    op.create_table(
        'campaign_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Float(), nullable=False, server_default='0'),
        sa.Column('cost', sa.DECIMAL(12, 2), nullable=False, server_default='0'),
        sa.Column('revenue', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('avg_cpc', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('ctr', sa.Float(), nullable=True),
        sa.Column('roas', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_metric_campaign_id', 'campaign_metrics', ['campaign_id'])
    op.create_index('idx_metric_date', 'campaign_metrics', ['date'])
    op.create_index('idx_metric_time', 'campaign_metrics', ['time'])

    # Create keywords table
    op.create_table(
        'keywords',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('google_keyword_id', sa.String(20), nullable=False),
        sa.Column('text', sa.String(255), nullable=False),
        sa.Column('match_type', sa.Enum('EXACT', 'PHRASE', 'BROAD', 'BROAD_MODIFIER', name='match_type'), nullable=False, server_default='BROAD'),
        sa.Column('bid', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_keyword_campaign_id', 'keywords', ['campaign_id'])
    op.create_index('idx_keyword_quality_score', 'keywords', ['quality_score'])

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.Enum('BID_ADJUSTMENT', 'KEYWORD_ADD', 'KEYWORD_REMOVE', 'AD_COPY', 'BUDGET_REALLOC', 'PAUSE_UNDERPERFORMING', name='recommendation_type'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.Enum('HIGH', 'MEDIUM', 'LOW', name='priority'), nullable=False, server_default='MEDIUM'),
        sa.Column('estimated_impact', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('action_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'ACCEPTED', 'REJECTED', 'EXECUTED', name='rec_status'), nullable=False, server_default='OPEN'),
        sa.Column('ai_model', sa.String(50), nullable=False, server_default='gpt-4o'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['google_ads_accounts.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_rec_account_id', 'recommendations', ['account_id'])
    op.create_index('idx_rec_status', 'recommendations', ['status'])

    # Create automations table
    op.create_table(
        'automations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.Enum('BID_ADJUSTMENT', 'PAUSE_LOW_PERFORMERS', 'ENABLE_KEYWORDS', 'DAILY_BUDGET_CONTROL', name='rule_type'), nullable=False),
        sa.Column('rule_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['google_ads_accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_automation_account_id', 'automations', ['account_id'])
    op.create_index('idx_automation_enabled', 'automations', ['enabled'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.Enum('CAMPAIGN_PAUSE', 'BID_UPDATE', 'KEYWORD_ADD', 'AUTOMATION_RUN', 'RECOMMENDATION_ACCEPT', 'ACCOUNT_CONNECT', 'ACCOUNT_DISCONNECT', name='action_type'), nullable=False),
        sa.Column('resource_type', sa.Enum('CAMPAIGN', 'KEYWORD', 'AUTOMATION', 'ACCOUNT_CONNECTION', name='resource_type'), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source', sa.Enum('MANUAL', 'AUTOMATION', 'RECOMMENDATION', name='action_source'), nullable=False, server_default='MANUAL'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['google_ads_accounts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('ALERT_UNDERPERFORMING', 'RECOMMENDATION', 'AUTOMATION_EXECUTED', 'SYNC_COMPLETE', 'ERROR', name='notification_type'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_resource', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_notification_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'])


def downgrade() -> None:
    """Drop all tables and types."""

    # Drop tables
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('automations')
    op.drop_table('recommendations')
    op.drop_table('keywords')
    op.drop_table('campaign_metrics')
    op.drop_table('campaigns')
    op.drop_table('google_ads_accounts')
    op.drop_table('users')

    # Drop ENUM types
    op.execute("DROP TYPE notification_type")
    op.execute("DROP TYPE action_source")
    op.execute("DROP TYPE resource_type")
    op.execute("DROP TYPE action_type")
    op.execute("DROP TYPE rule_type")
    op.execute("DROP TYPE rec_status")
    op.execute("DROP TYPE priority")
    op.execute("DROP TYPE recommendation_type")
    op.execute("DROP TYPE match_type")
    op.execute("DROP TYPE campaign_type")
    op.execute("DROP TYPE campaign_status")
