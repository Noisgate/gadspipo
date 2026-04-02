export interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Campaign {
  id: string
  name: string
  status: 'ENABLED' | 'PAUSED' | 'REMOVED'
  type: 'SEARCH' | 'DISPLAY' | 'SHOPPING' | 'VIDEO' | 'PERFORMANCE_MAX'
  budget_daily?: number
  account_id: string
  created_at: string
  updated_at: string
  latest_metrics?: CampaignMetrics
}

export interface CampaignMetrics {
  date: string
  impressions: number
  clicks: number
  conversions: number
  cost: number
  ctr?: number
  avg_cpc?: number
  roas?: number
}

export interface CampaignPerformancePoint {
  date: string
  impressions: number
  clicks: number
  conversions: number
  cost: number
  ctr?: number | null
  avg_cpc?: number | null
  roas?: number | null
}

export interface CampaignPerformanceMetrics {
  total_impressions: number
  total_clicks: number
  total_conversions: number
  total_cost: number
  avg_ctr?: number | null
  avg_cpc?: number | null
  avg_cpa?: number | null
  roas?: number | null
}

export interface CampaignAnalysis {
  score: number
  tier: 'WINNERS' | 'PERFORMERS' | 'UNDERPERFORMERS' | 'ZOMBIES'
  tier_label: string
  analysis_mode: 'DIAGNOSTIC' | 'OPTIMIZATION'
  confidence: 'LOW' | 'MEDIUM' | 'HIGH'
  trend?: 'up' | 'down' | 'stable' | null
  summary: string
  delivery_diagnosis: {
    stage: 'NOT_SERVING' | 'LIMITED' | 'SERVING'
    status_label: string
    summary: string
    blockers: string[]
    evidence: string[]
    next_checks: string[]
    xquads_playbooks: string[]
    google_primary_status?: string | null
    google_primary_status_reasons: string[]
  }
  benchmark: {
    campaign_ctr?: number | null
    account_avg_ctr?: number | null
    campaign_cpa?: number | null
    account_avg_cpa?: number | null
  }
  strengths: string[]
  weaknesses: string[]
  opportunities: string[]
  next_steps: string[]
  guardrails: string[]
}

export interface CampaignDetail {
  id: string
  name: string
  status: 'ENABLED' | 'PAUSED' | 'REMOVED'
  primary_status?: string | null
  primary_status_reasons: string[]
  type: 'SEARCH' | 'DISPLAY' | 'SHOPPING' | 'VIDEO' | 'PERFORMANCE_MAX'
  budget_daily?: number | null
  account_id: string
  account_name: string
  customer_id?: string | null
  created_at: string
  updated_at: string
  performance: {
    campaign_id: string
    period_days: number
    metrics: CampaignPerformanceMetrics
    daily_data: CampaignPerformancePoint[]
  }
  analysis: CampaignAnalysis
  query_intelligence: {
    keyword_count: number
    search_term_count: number
    low_quality_keyword_count: number
    top_keywords: GoogleAdsQueryKeyword[]
    top_search_terms: GoogleAdsQuerySearchTerm[]
  }
  recommended_actions: GoogleAdsActionRecommendation[]
}

export interface CampaignInvestigation {
  id: string
  campaign_id: string
  prompt: string
  status: 'OPEN' | 'PLAN_READY' | 'APPROVED' | 'EXECUTED'
  analysis_mode: 'DIAGNOSTIC' | 'OPTIMIZATION'
  summary: string
  root_cause: string
  diagnosis: {
    requested_analysis: string
    campaign_status: string
    google_primary_status?: string | null
    sync_status: {
      attempted: boolean
      success: boolean
      detail: string
    }
    delivery_stage: 'NOT_SERVING' | 'LIMITED' | 'SERVING'
    delivery_summary: string
    blockers: string[]
    evidence: string[]
    xquads_playbooks: string[]
    metrics_snapshot: {
      impressions: number
      clicks: number
      conversions: number
      cost: number
      keyword_count: number
      search_term_count: number
    }
  }
  repair_plan: {
    goal: string
    sequence: CampaignInvestigationStep[]
    success_signals: string[]
    history: CampaignInvestigationHistoryEntry[]
  }
  approval_payload: {
    mode: string
    message: string
    candidate_actions: GoogleAdsActionRecommendation[]
    blocked_until_approval: boolean
    approval_note?: string | null
    approved_at?: string | null
    execution_note?: string | null
    last_executed_at?: string | null
    execution_results: CampaignInvestigationExecutionResult[]
  }
  created_at: string
  updated_at: string
}

export interface CampaignInvestigationStep {
  id: string
  title: string
  owner: string
  playbook: string
  reason: string
  actions: string[]
  status: 'pending' | 'in_progress' | 'completed'
  completed_at?: string | null
  completion_note?: string | null
  last_updated_at?: string | null
}

export interface CampaignInvestigationHistoryEntry {
  step_id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed'
  note?: string | null
  created_at: string
}

export interface CampaignInvestigationExecutionResult {
  title: string
  action_type: string
  status: 'executed' | 'skipped' | 'failed'
  message: string
  recommendation_id?: string
}

export interface DashboardStats {
  total_campaigns: number
  active_campaigns: number
  paused_campaigns: number
  metrics: {
    total_impressions: number
    total_clicks: number
    total_conversions: number
    total_cost: number
    avg_ctr?: number
    avg_cpc?: number
    roas?: number
  }
}

export interface Recommendation {
  id: string
  type: string
  title: string
  description: string
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'OPEN' | 'ACCEPTED' | 'REJECTED' | 'EXECUTED'
  estimated_impact?: Record<string, any>
  created_at: string
}

export interface CommandCenterCapability {
  id: string
  label: string
  source: string
  command: string
  description: string
}

export interface GoogleAdsConnectedAccount {
  id: string
  customer_id: string
  account_name: string
  connected_at: string
}

export interface GoogleAdsSummary {
  account_count: number
  campaign_count: number
  active_campaign_count: number
  period_days: number
  impressions: number
  clicks: number
  conversions: number
  cost: number
  avg_ctr?: number | null
  avg_cpc?: number | null
  avg_cpa?: number | null
  measurement_readiness: 'LOW' | 'MEDIUM' | 'HIGH'
}

export interface GoogleAdsCampaignInsight {
  id: string
  campaign_id: string
  google_campaign_id: string
  name: string
  status: string
  type: string
  account_id: string
  account_name: string
  customer_id?: string | null
  budget_daily?: number | null
  impressions: number
  clicks: number
  conversions: number
  cost: number
  avg_ctr?: number | null
  avg_cpc?: number | null
  avg_cpa?: number | null
  trend?: 'up' | 'down' | 'stable' | null
  latest_date?: string | null
  days_with_data: number
}

export interface GoogleAdsAuditDimension {
  name: string
  score: number
  status: 'OK' | 'WATCH' | 'FIX'
  note: string
}

export interface GoogleAdsActionRecommendation {
  type: string
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
  title: string
  description: string
  campaign_id?: string | null
  campaign_name?: string | null
  estimated_impact?: {
    metric: string
    current?: number | null
    projected?: number | null
  } | null
  execution_modes: Array<'approve_and_execute' | 'create_automation' | 'plan_only'>
  action_payload: Record<string, any>
  source: string
}

export interface RecommendationProposal {
  action_type: string
  proposal_title: string
  campaign_id?: string | null
  campaign_name?: string | null
  analysis_mode: 'DIAGNOSTIC' | 'OPTIMIZATION'
  confidence: 'LOW' | 'MEDIUM' | 'HIGH'
  summary: string
  data_notes: string[]
  why_this_proposal: string[]
  suggested_changes: string[]
  risks: string[]
  preflight_checklist: string[]
  discussion_points: string[]
  success_signals: string[]
  approval_checklist: string[]
  change_highlights: string[]
  feedback_notes: string[]
  applied_feedback: string[]
  pending_feedback: string[]
  refinement_summary?: string | null
  refined_action: {
    title: string
    description: string
    action_payload: Record<string, any>
    recommended_execution_mode: 'approve_and_execute' | 'plan_only'
  }
  ai_metadata: {
    provider: string
    model: string
    used_ai: boolean
  }
}

export interface GoogleAdsQueryKeyword {
  id: string
  campaign_id: string
  campaign_name: string
  google_keyword_id?: string
  text: string
  match_type: string
  quality_score?: number | null
  bid?: number | null
}

export interface GoogleAdsQuerySearchTerm {
  id: string
  campaign_id: string
  campaign_name: string
  term: string
  match_type?: string | null
  impressions: number
  clicks: number
  conversions: number
  cost: number
  last_seen_at?: string | null
}

export interface GoogleAdsAutomation {
  id: string
  name: string
  rule_type: string
  enabled: boolean
  created_at: string
  last_run_at?: string | null
  next_run_at?: string | null
}

export interface GoogleAdsCommandCenter {
  connected_accounts: GoogleAdsConnectedAccount[]
  capabilities: CommandCenterCapability[]
  methodology: {
    squad: string
    google_ads_lead: string
    principles: string[]
  }
  summary: GoogleAdsSummary
  account_audit?: {
    health_score: number
    health_label: string
    wasted_spend: number
    wasted_spend_share: number
    campaign_tiers: {
      winners: number
      performers: number
      underperformers: number
      zombies: number
    }
    dimensions: GoogleAdsAuditDimension[]
    top_findings: string[]
  } | null
  performance_analysis?: {
    period_days: number
    metrics: GoogleAdsSummary
    top_spend_campaigns: GoogleAdsCampaignInsight[]
    top_ctr_campaigns: GoogleAdsCampaignInsight[]
    insights: { title: string; detail: string }[]
    action_plan: string[]
  } | null
  budget_optimization?: {
    current_monthly_spend: number
    wasted_spend: number
    winner_cpa?: number | null
    scenarios: {
      name: string
      budget: number
      projected_cpa?: number | null
      projected_conversions: number
    }[]
    recommended_reallocation: {
      from_campaign: string
      to_campaign: string
      shift_amount: number
      rationale: string
    }[]
    guardrails: string[]
  } | null
  tracking_setup?: {
    status: string
    summary: string
    checklist: {
      label: string
      status: 'done' | 'manual-review'
    }[]
    recommended_events: string[]
    utm_strategy: {
      parameter: string
      convention: string
      example: string
    }[]
  } | null
  scaling_plan?: {
    eligible_campaigns: GoogleAdsCampaignInsight[]
    recommended_method: string
    summary: string
    guardrails: string[]
    schedule: {
      week: string
      action: string
    }[]
  } | null
  query_intelligence: {
    keyword_count: number
    search_term_count: number
    low_quality_keyword_count: number
    top_keywords: GoogleAdsQueryKeyword[]
    top_search_terms: GoogleAdsQuerySearchTerm[]
  }
  automations: GoogleAdsAutomation[]
  strategy_blueprint: {
    framework: string
    principles: string[]
    current_mix: Record<string, boolean>
    gaps: string[]
    next_steps: string[]
  }
  recommended_actions: GoogleAdsActionRecommendation[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface CampaignStudioBrief {
  business_name?: string
  product_or_service: string
  offer: string
  objective: 'LEADS' | 'SALES' | 'AWARENESS' | 'TRAFFIC'
  intention: string
  target_audience: string
  location: string
  budget_amount: number
  budget_period: 'daily' | 'monthly'
  website_url?: string
  conversion_goal?: string
  differentiators?: string
  current_assets: string[]
  available_documents: string[]
  notes?: string
}

export interface CampaignStudioUploadedMaterial {
  id: string
  original_name: string
  stored_name: string
  content_type: string
  size_bytes: number
  kind: 'asset' | 'document' | 'other'
  category: string
  mapped_asset?: string | null
  mapped_document?: string | null
  notes?: string | null
}

export interface CampaignStudioIdeaAnalysis {
  summary: string
  suggested_campaign_type: string
  suggested_bidding_strategy: string
  suggested_brief: Partial<CampaignStudioBrief>
  questions_to_clarify: string[]
  material_requirements: CampaignStudioRequirement[]
  uploaded_materials: CampaignStudioUploadedMaterial[]
  next_steps: string[]
  ai_metadata: {
    provider: string
    model: string
    used_ai: boolean
  }
}

export interface CampaignStudioRequirement {
  item: string
  category: string
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'ready' | 'missing' | 'recommended'
  reason: string
  example?: string | null
}

export interface CampaignStudioChecklistItem {
  label: string
  status: 'ready' | 'missing' | 'warning'
  detail: string
}

export interface CampaignStudioAdGroupPlan {
  name: string
  intent: string
  keyword_themes: string[]
  audiences: string[]
  landing_page_focus: string
}

export interface CampaignStudioAnalysis {
  briefing_digest: {
    business_name: string
    objective: string
    funnel_stage: string
    normalized_daily_budget: number
    campaign_type: string
    summary: string
  }
  strategic_recommendation: {
    recommended_campaign_type: string
    recommended_bidding_strategy: string
    budget_daily_suggestion: number
    budget_explanation: string
    rationale: string[]
    launch_sequence: string[]
  }
  campaign_blueprint: {
    suggested_campaign_name: string
    recommended_campaign_type: string
    daily_budget: number
    ad_groups: CampaignStudioAdGroupPlan[]
    negative_keyword_themes: string[]
    ad_extensions: string[]
  }
  messaging: {
    angles: string[]
    headline_ideas: string[]
    description_ideas: string[]
  }
  asset_requirements: CampaignStudioRequirement[]
  information_requirements: CampaignStudioRequirement[]
  launch_checklist: CampaignStudioChecklistItem[]
  tracking_requirements: string[]
  compliance_checks: string[]
  launch_readiness: {
    score: number
    status: 'BLOCKED' | 'NEEDS_INPUT' | 'READY_FOR_SETUP'
    blockers: string[]
    next_steps: string[]
  }
  ai_metadata: {
    provider: string
    model: string
    used_ai: boolean
  }
}
