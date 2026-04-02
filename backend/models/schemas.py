"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


# ========================================
# User Schemas
# ========================================

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = None  # For OAuth, password is optional


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Google Ads Account Schemas
# ========================================

class GoogleAdsAccountCreate(BaseModel):
    customer_id: str = Field(..., min_length=10, max_length=16)
    account_name: str
    access_token: str
    refresh_token: str
    token_expires_at: datetime


class GoogleAdsAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    is_active: Optional[bool] = None


class GoogleAdsAccountResponse(BaseModel):
    id: UUID
    customer_id: str
    account_name: str
    is_active: bool
    connected_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Campaign Schemas
# ========================================

class CampaignMetricBase(BaseModel):
    impressions: int = 0
    clicks: int = 0
    conversions: float = 0.0
    cost: float = 0.0
    revenue: Optional[float] = None


class CampaignMetricResponse(CampaignMetricBase):
    id: UUID
    campaign_id: UUID
    date: datetime
    avg_cpc: Optional[float] = None
    ctr: Optional[float] = None
    roas: Optional[float] = None

    class Config:
        from_attributes = True


class KeywordBase(BaseModel):
    text: str
    match_type: str = "BROAD"
    bid: Optional[float] = None
    quality_score: Optional[int] = None


class KeywordResponse(KeywordBase):
    id: UUID
    campaign_id: UUID
    google_keyword_id: str

    class Config:
        from_attributes = True


class SearchTermResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    term: str
    match_type: Optional[str] = None
    impressions: int
    clicks: int
    conversions: float
    cost: float
    last_seen_at: datetime

    class Config:
        from_attributes = True


class CampaignBase(BaseModel):
    name: str
    status: str = "ENABLED"
    campaign_type: str = "SEARCH"
    budget_daily: Optional[float] = None


class CampaignCreate(CampaignBase):
    google_campaign_id: str


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    budget_daily: Optional[float] = None


class CampaignResponse(CampaignBase):
    id: UUID
    account_id: UUID
    google_campaign_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignDetailResponse(CampaignResponse):
    """Campaign with related data (metrics, keywords)."""
    metrics: List[CampaignMetricResponse] = []
    keywords: List[KeywordResponse] = []


class CampaignStudioUploadedMaterial(BaseModel):
    id: str
    original_name: str
    stored_name: str
    content_type: str
    size_bytes: int
    kind: Literal["asset", "document", "other"]
    category: str
    mapped_asset: Optional[str] = None
    mapped_document: Optional[str] = None
    notes: Optional[str] = None


class CampaignStudioBriefDraft(BaseModel):
    business_name: Optional[str] = None
    product_or_service: Optional[str] = None
    offer: Optional[str] = None
    objective: Literal["LEADS", "SALES", "AWARENESS", "TRAFFIC"] = "LEADS"
    intention: Optional[str] = None
    target_audience: Optional[str] = None
    location: Optional[str] = None
    budget_amount: Optional[float] = None
    budget_period: Literal["daily", "monthly"] = "daily"
    website_url: Optional[str] = None
    conversion_goal: Optional[str] = None
    differentiators: Optional[str] = None
    current_assets: List[str] = Field(default_factory=list)
    available_documents: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CampaignStudioIdeaRequest(BaseModel):
    request: str = Field(..., min_length=10)
    objective: Optional[Literal["LEADS", "SALES", "AWARENESS", "TRAFFIC"]] = None
    budget_amount: Optional[float] = Field(None, gt=0)
    budget_period: Literal["daily", "monthly"] = "daily"
    location: Optional[str] = None
    uploaded_materials: List[CampaignStudioUploadedMaterial] = Field(default_factory=list)


class CampaignStudioBriefRequest(BaseModel):
    business_name: Optional[str] = None
    product_or_service: str = Field(..., min_length=3)
    offer: str = Field(..., min_length=3)
    objective: Literal["LEADS", "SALES", "AWARENESS", "TRAFFIC"] = "LEADS"
    intention: str = Field(..., min_length=10)
    target_audience: str = Field(..., min_length=3)
    location: str = Field(..., min_length=2)
    budget_amount: float = Field(..., gt=0)
    budget_period: Literal["daily", "monthly"] = "daily"
    website_url: Optional[str] = None
    conversion_goal: Optional[str] = None
    differentiators: Optional[str] = None
    current_assets: List[str] = Field(default_factory=list)
    available_documents: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CampaignStudioRequirement(BaseModel):
    item: str
    category: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    status: Literal["ready", "missing", "recommended"]
    reason: str
    example: Optional[str] = None


class CampaignStudioChecklistItem(BaseModel):
    label: str
    status: Literal["ready", "missing", "warning"]
    detail: str


class CampaignStudioAdGroupPlan(BaseModel):
    name: str
    intent: str
    keyword_themes: List[str]
    audiences: List[str]
    landing_page_focus: str


class CampaignStudioStrategicRecommendation(BaseModel):
    recommended_campaign_type: str
    recommended_bidding_strategy: str
    budget_daily_suggestion: float
    budget_explanation: str
    rationale: List[str]
    launch_sequence: List[str]


class CampaignStudioMessaging(BaseModel):
    angles: List[str]
    headline_ideas: List[str]
    description_ideas: List[str]


class CampaignStudioLaunchReadiness(BaseModel):
    score: int
    status: Literal["BLOCKED", "NEEDS_INPUT", "READY_FOR_SETUP"]
    blockers: List[str]
    next_steps: List[str]


class CampaignStudioIdeaAnalysisResponse(BaseModel):
    summary: str
    suggested_campaign_type: str
    suggested_bidding_strategy: str
    suggested_brief: CampaignStudioBriefDraft
    questions_to_clarify: List[str]
    material_requirements: List[CampaignStudioRequirement]
    uploaded_materials: List[CampaignStudioUploadedMaterial]
    next_steps: List[str]
    ai_metadata: Dict[str, Any]


class CampaignStudioAnalysisResponse(BaseModel):
    briefing_digest: Dict[str, Any]
    strategic_recommendation: CampaignStudioStrategicRecommendation
    campaign_blueprint: Dict[str, Any]
    messaging: CampaignStudioMessaging
    asset_requirements: List[CampaignStudioRequirement]
    information_requirements: List[CampaignStudioRequirement]
    launch_checklist: List[CampaignStudioChecklistItem]
    tracking_requirements: List[str]
    compliance_checks: List[str]
    launch_readiness: CampaignStudioLaunchReadiness
    ai_metadata: Dict[str, Any]


class CampaignInvestigationRequest(BaseModel):
    prompt: str = Field(..., min_length=10)


class CampaignInvestigationApprovalRequest(BaseModel):
    approval_note: Optional[str] = None


class CampaignInvestigationStepUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|completed)$")
    note: Optional[str] = None


class CampaignInvestigationExecuteRequest(BaseModel):
    execution_note: Optional[str] = None


class CampaignInvestigationResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    prompt: str
    status: str
    analysis_mode: str
    summary: str
    root_cause: str
    diagnosis: Dict[str, Any]
    repair_plan: Dict[str, Any]
    approval_payload: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ========================================
# Recommendation Schemas
# ========================================

class RecommendationBase(BaseModel):
    type: str
    title: str
    description: str
    priority: str = "MEDIUM"
    estimated_impact: Optional[Dict[str, Any]] = None


class RecommendationCreate(RecommendationBase):
    account_id: UUID
    campaign_id: Optional[UUID] = None
    action_payload: Dict[str, Any]
    ai_model: str = "gpt-4o"


class RecommendationUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None


class RecommendationResponse(RecommendationBase):
    id: UUID
    account_id: UUID
    campaign_id: Optional[UUID] = None
    status: str
    ai_model: str
    created_at: datetime
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecommendationActionRequest(BaseModel):
    action_type: str
    title: str
    description: str
    priority: str = "MEDIUM"
    campaign_id: Optional[UUID] = None
    campaign_name: Optional[str] = None
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    execution_mode: str = "create_automation"
    approval_note: Optional[str] = None


class RecommendationActionResponse(BaseModel):
    status: str
    message: str
    recommendation_id: Optional[UUID] = None
    automation_id: Optional[UUID] = None


class RecommendationProposalRequest(BaseModel):
    action_type: str
    title: str
    description: str
    priority: str = "MEDIUM"
    campaign_id: Optional[UUID] = None
    campaign_name: Optional[str] = None
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class RecommendationProposalResponse(BaseModel):
    action_type: str
    proposal_title: str
    campaign_id: Optional[UUID] = None
    campaign_name: Optional[str] = None
    analysis_mode: str
    confidence: str
    summary: str
    data_notes: List[str]
    why_this_proposal: List[str]
    suggested_changes: List[str]
    risks: List[str]
    preflight_checklist: List[str]
    discussion_points: List[str]
    success_signals: List[str]
    approval_checklist: List[str]
    change_highlights: List[str]
    feedback_notes: List[str]
    applied_feedback: List[str]
    pending_feedback: List[str]
    refinement_summary: Optional[str] = None
    refined_action: Dict[str, Any]
    ai_metadata: Dict[str, Any]


# ========================================
# Automation Schemas
# ========================================

class AutomationBase(BaseModel):
    name: str
    rule_type: str
    rule_config: Dict[str, Any]
    enabled: bool = True


class AutomationCreate(AutomationBase):
    account_id: UUID


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class AutomationResponse(AutomationBase):
    id: UUID
    account_id: UUID
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Audit Log Schemas
# ========================================

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_id: Optional[UUID] = None
    action_type: str
    resource_type: str
    resource_id: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Notification Schemas
# ========================================

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Dashboard/Analytics Schemas
# ========================================

class CampaignPerformanceMetrics(BaseModel):
    """Overall performance metrics for campaigns."""
    total_impressions: int
    total_clicks: int
    total_conversions: float
    total_cost: float
    total_revenue: Optional[float] = None
    average_ctr: float
    average_cpc: float
    average_roas: Optional[float] = None


class DashboardStats(BaseModel):
    """Dashboard overview statistics."""
    active_campaigns: int
    paused_campaigns: int
    total_campaigns: int
    metrics: CampaignPerformanceMetrics
    last_sync_at: Optional[datetime] = None


# ========================================
# Auth Schemas
# ========================================

class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class OAuthCallbackRequest(BaseModel):
    """OAuth callback parameters."""
    code: str
    state: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# ========================================
# Error Schemas
# ========================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: List[Dict[str, Any]]
    code: str = "VALIDATION_ERROR"
