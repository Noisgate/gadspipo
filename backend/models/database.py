"""
SQLAlchemy ORM models for the application.
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Enum, ForeignKey,
    JSON, Text, DECIMAL, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class User(Base):
    """User model for application authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # OAuth users won't have password
    oauth_google_id = Column(String(255), unique=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = relationship("GoogleAdsAccount", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_oauth_google_id', 'oauth_google_id'),
    )


class GoogleAdsAccount(Base):
    """Google Ads account connection for a user."""

    __tablename__ = "google_ads_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    customer_id = Column(String(16), nullable=False)  # Google Ads Customer ID (10 digits)
    account_name = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=False)  # Encrypted
    token_expires_at = Column(DateTime, nullable=False)
    connected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="accounts")
    campaigns = relationship("Campaign", back_populates="account", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="account", cascade="all, delete-orphan")
    automations = relationship("Automation", back_populates="account", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('user_id', 'customer_id', name='uq_user_customer'),
        Index('idx_account_user_id', 'user_id'),
        Index('idx_account_customer_id', 'customer_id'),
    )


class Campaign(Base):
    """Google Ads campaign snapshot."""

    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('google_ads_accounts.id'), nullable=False)
    google_campaign_id = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum('ENABLED', 'PAUSED', 'REMOVED', name='campaign_status'), default='ENABLED')
    campaign_type = Column(
        Enum('SEARCH', 'DISPLAY', 'SHOPPING', 'VIDEO', 'PERFORMANCE_MAX', name='campaign_type'),
        default='SEARCH'
    )
    budget_daily = Column(DECIMAL(12, 2), nullable=True)
    primary_status = Column(String(64), nullable=True)
    primary_status_reasons = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("GoogleAdsAccount", back_populates="campaigns")
    metrics = relationship("CampaignMetric", back_populates="campaign", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="campaign", cascade="all, delete-orphan")
    search_terms = relationship("SearchTerm", back_populates="campaign", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="campaign")
    investigations = relationship("CampaignInvestigation", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('account_id', 'google_campaign_id', name='uq_account_google_campaign'),
        Index('idx_campaign_account_id', 'account_id'),
        Index('idx_campaign_status', 'status'),
    )


class CampaignMetric(Base):
    """Campaign metrics (time-series data for TimescaleDB hypertable)."""

    __tablename__ = "campaign_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=False)
    time = Column(DateTime, default=datetime.utcnow)  # For TimescaleDB time bucketing
    date = Column(DateTime, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)
    cost = Column(DECIMAL(12, 2), default=0.0)
    revenue = Column(DECIMAL(12, 2), nullable=True)
    avg_cpc = Column(DECIMAL(8, 4), nullable=True)
    ctr = Column(Float, nullable=True)
    roas = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="metrics")

    __table_args__ = (
        Index('idx_metric_campaign_id', 'campaign_id'),
        Index('idx_metric_date', 'date'),
        Index('idx_metric_time', 'time'),
    )


class Keyword(Base):
    """Ad group keyword."""

    __tablename__ = "keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=False)
    google_keyword_id = Column(String(20), nullable=False)
    text = Column(String(255), nullable=False)
    match_type = Column(
        Enum('EXACT', 'PHRASE', 'BROAD', 'BROAD_MODIFIER', name='match_type'),
        default='BROAD'
    )
    bid = Column(DECIMAL(8, 4), nullable=True)
    quality_score = Column(Integer, nullable=True)  # 1-10
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="keywords")

    __table_args__ = (
        Index('idx_keyword_campaign_id', 'campaign_id'),
        Index('idx_keyword_quality_score', 'quality_score'),
    )


class SearchTerm(Base):
    """Aggregated search term metrics for a campaign."""

    __tablename__ = "search_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=False)
    term = Column(String(255), nullable=False)
    match_type = Column(String(50), nullable=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Float, default=0.0)
    cost = Column(DECIMAL(12, 2), default=0.0)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="search_terms")

    __table_args__ = (
        UniqueConstraint('campaign_id', 'term', name='uq_campaign_search_term'),
        Index('idx_search_term_campaign_id', 'campaign_id'),
        Index('idx_search_term_clicks', 'clicks'),
    )


class Recommendation(Base):
    """AI-generated recommendations for campaign optimization."""

    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('google_ads_accounts.id'), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=True)
    type = Column(
        Enum(
            'BID_ADJUSTMENT', 'KEYWORD_ADD', 'KEYWORD_REMOVE', 'AD_COPY',
            'BUDGET_REALLOC', 'PAUSE_UNDERPERFORMING',
            name='recommendation_type'
        ),
        nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum('HIGH', 'MEDIUM', 'LOW', name='priority'), default='MEDIUM')
    estimated_impact = Column(JSONB, nullable=True)  # {metric: string, current: float, projected: float, confidence: float}
    action_payload = Column(JSONB, nullable=False)  # Data needed to execute recommendation
    status = Column(Enum('OPEN', 'ACCEPTED', 'REJECTED', 'EXECUTED', name='rec_status'), default='OPEN')
    ai_model = Column(String(50), default='gpt-4o')
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    account = relationship("GoogleAdsAccount", back_populates="recommendations")
    campaign = relationship("Campaign", back_populates="recommendations")

    __table_args__ = (
        Index('idx_rec_account_id', 'account_id'),
        Index('idx_rec_status', 'status'),
    )


class CampaignInvestigation(Base):
    """Persisted investigation workflow for campaign diagnosis and repair planning."""

    __tablename__ = "campaign_investigations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('campaigns.id'), nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(
        Enum('OPEN', 'PLAN_READY', 'APPROVED', 'EXECUTED', name='investigation_status'),
        default='PLAN_READY',
        nullable=False,
    )
    analysis_mode = Column(String(32), nullable=False, default='DIAGNOSTIC')
    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    diagnosis = Column(JSONB, nullable=False)
    repair_plan = Column(JSONB, nullable=False)
    approval_payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="investigations")

    __table_args__ = (
        Index('idx_campaign_investigation_campaign_id', 'campaign_id'),
        Index('idx_campaign_investigation_user_id', 'user_id'),
        Index('idx_campaign_investigation_created_at', 'created_at'),
    )


class Automation(Base):
    """Automation rules for campaigns."""

    __tablename__ = "automations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('google_ads_accounts.id'), nullable=False)
    name = Column(String(255), nullable=False)
    rule_type = Column(
        Enum(
            'BID_ADJUSTMENT', 'PAUSE_LOW_PERFORMERS', 'ENABLE_KEYWORDS',
            'DAILY_BUDGET_CONTROL',
            name='rule_type'
        ),
        nullable=False
    )
    rule_config = Column(JSONB, nullable=False)  # Conditions + actions
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("GoogleAdsAccount", back_populates="automations")

    __table_args__ = (
        Index('idx_automation_account_id', 'account_id'),
        Index('idx_automation_enabled', 'enabled'),
    )


class AuditLog(Base):
    """Audit trail for compliance and debugging."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey('google_ads_accounts.id'), nullable=True)
    action_type = Column(
        Enum(
            'CAMPAIGN_PAUSE', 'BID_UPDATE', 'KEYWORD_ADD', 'AUTOMATION_RUN',
            'RECOMMENDATION_ACCEPT', 'ACCOUNT_CONNECT', 'ACCOUNT_DISCONNECT',
            name='action_type'
        ),
        nullable=False
    )
    resource_type = Column(
        Enum('CAMPAIGN', 'KEYWORD', 'AUTOMATION', 'ACCOUNT_CONNECTION', name='resource_type'),
        nullable=False
    )
    resource_id = Column(String(255), nullable=True)
    changes = Column(JSONB, nullable=True)  # before/after
    source = Column(Enum('MANUAL', 'AUTOMATION', 'RECOMMENDATION', name='action_source'), default='MANUAL')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_created_at', 'created_at'),
    )


class Notification(Base):
    """User notifications."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    type = Column(
        Enum(
            'ALERT_UNDERPERFORMING', 'RECOMMENDATION', 'AUTOMATION_EXECUTED',
            'SYNC_COMPLETE', 'ERROR',
            name='notification_type'
        ),
        nullable=False
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_resource = Column(JSONB, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index('idx_notification_user_id', 'user_id'),
        Index('idx_notification_created_at', 'created_at'),
    )
