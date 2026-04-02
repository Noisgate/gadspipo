"""
Google Ads command center inspired by the Traffic Masters squad.

This service converts the squad playbooks into structured application data
that the frontend can render as actionable Google Ads guidance.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.database import (
    Automation,
    Campaign,
    CampaignMetric,
    GoogleAdsAccount,
    Keyword,
    SearchTerm,
)


_CAPABILITIES = [
    {
        "id": "diagnose",
        "label": "Diagnóstico",
        "source": "traffic-chief",
        "command": "*diagnose",
        "description": "Classifica gargalos da conta e aponta o especialista certo.",
    },
    {
        "id": "account-audit",
        "label": "Auditoria de conta",
        "source": "ads-analyst",
        "command": "*account-audit",
        "description": "Scorecard de 8 dimensões, tiers de campanhas e listas de kill/scale/fix.",
    },
    {
        "id": "performance-analysis",
        "label": "Análise de performance",
        "source": "performance-analyst",
        "command": "*analyze-performance",
        "description": "Leitura 80/20, tendências e plano de ação de 7 dias.",
    },
    {
        "id": "budget-optimization",
        "label": "Otimização de orçamento",
        "source": "fiscal",
        "command": "*manage-budget",
        "description": "Modelagem de cenários, reallocation e guardrails de spend.",
    },
    {
        "id": "tracking-setup",
        "label": "Tracking e medição",
        "source": "pixel-specialist",
        "command": "*setup-tracking",
        "description": "Checklist de tag, enhanced conversions, GA4 e QA de eventos.",
    },
    {
        "id": "scaling-plan",
        "label": "Escala",
        "source": "scale-optimizer",
        "command": "*scale-campaign",
        "description": "Plano vertical/horizontal para escalar vencedores com segurança.",
    },
]

_KASIM_PRINCIPLES = [
    "Traffic first, product second.",
    "Nao confiar cegamente nas recomendacoes do Google.",
    "Separar branded, competitor, general intent e remarketing.",
    "Performance Max precisa de sinais e conversoes bem desenhados.",
    "Mudancas de budget devem ser graduais e monitoradas.",
]

_TRACKING_CHECKLIST = [
    "Google tag instalada em todas as paginas relevantes",
    "Enhanced Conversions configurado para o evento principal",
    "Conversion Linker ativo",
    "GA4 vinculado ao Google Ads para audiences e validacao",
    "Conversoes primarias e secundarias definidas",
    "UTMs padronizadas por fonte, campanha e ad group",
    "Teste real concluido na thank-you page ou evento de lead",
]

_UTM_STRATEGY = [
    {"parameter": "utm_source", "convention": "google", "example": "google"},
    {"parameter": "utm_medium", "convention": "cpc", "example": "cpc"},
    {
        "parameter": "utm_campaign",
        "convention": "objetivo_publico_oferta",
        "example": "search_leads_rede-pesquisa_oferta-principal",
    },
    {
        "parameter": "utm_content",
        "convention": "criativo_variacao",
        "example": "rsa_headline-a_v1",
    },
]


class GoogleAdsCommandCenterService:
    """Builds structured Google Ads insights for the current user."""

    def build(self, user_id: UUID, db: Session) -> dict[str, Any]:
        accounts = (
            db.query(GoogleAdsAccount)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                GoogleAdsAccount.is_active == True,  # noqa: E712
            )
            .order_by(GoogleAdsAccount.connected_at.asc())
            .all()
        )

        account_payload = [
            {
                "id": str(account.id),
                "customer_id": account.customer_id,
                "account_name": account.account_name,
                "connected_at": account.connected_at.isoformat(),
            }
            for account in accounts
        ]

        if not accounts:
            return {
                "connected_accounts": [],
                "capabilities": _CAPABILITIES,
                "methodology": {
                    "squad": "traffic-masters",
                    "google_ads_lead": "kasim-aslam",
                    "principles": _KASIM_PRINCIPLES,
                },
                "summary": self._empty_summary(),
                "account_audit": None,
                "performance_analysis": None,
                "budget_optimization": None,
                "tracking_setup": {
                    "status": "NO_ACCOUNT",
                    "summary": "Conecte ao menos uma conta do Google Ads para habilitar a auditoria automatizada.",
                    "checklist": self._build_tracking_checklist(False),
                    "utm_strategy": _UTM_STRATEGY,
                },
                "scaling_plan": None,
                "strategy_blueprint": self._build_strategy_blueprint([]),
                "query_intelligence": self._empty_query_intelligence(),
                "automations": [],
                "recommended_actions": [],
            }

        campaigns = (
            db.query(Campaign)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                GoogleAdsAccount.is_active == True,  # noqa: E712
            )
            .all()
        )

        campaign_ids = [campaign.id for campaign in campaigns]
        metrics_by_campaign: dict[Any, list[CampaignMetric]] = defaultdict(list)
        keywords = []
        search_terms = []

        if campaign_ids:
            keywords = (
                db.query(Keyword)
                .filter(Keyword.campaign_id.in_(campaign_ids))
                .all()
            )
            search_terms = (
                db.query(SearchTerm)
                .filter(SearchTerm.campaign_id.in_(campaign_ids))
                .all()
            )

        if campaign_ids:
            start_date = datetime.utcnow().date() - timedelta(days=30)
            metrics = (
                db.query(CampaignMetric)
                .filter(
                    CampaignMetric.campaign_id.in_(campaign_ids),
                    func.date(CampaignMetric.date) >= start_date,
                )
                .order_by(CampaignMetric.date.asc())
                .all()
            )
            for metric in metrics:
                metrics_by_campaign[metric.campaign_id].append(metric)

        account_by_id = {account.id: account for account in accounts}
        campaign_snapshots = [
            self._build_campaign_snapshot(campaign, account_by_id.get(campaign.account_id), metrics_by_campaign[campaign.id])
            for campaign in campaigns
        ]

        tiers = self._split_campaign_tiers(campaign_snapshots)
        summary = self._build_summary(account_payload, campaign_snapshots)
        audit = self._build_account_audit(campaign_snapshots, tiers, summary)
        performance = self._build_performance_analysis(campaign_snapshots, tiers, summary)
        budget = self._build_budget_optimization(campaign_snapshots, tiers, summary)
        tracking = self._build_tracking_setup(summary)
        scaling = self._build_scaling_plan(campaign_snapshots, tiers, summary)
        strategy = self._build_strategy_blueprint(campaign_snapshots)
        query_intelligence = self._build_query_intelligence(campaign_snapshots, keywords, search_terms)
        automations = self._build_automation_overview(user_id, db)
        actions = self._build_recommended_actions(campaign_snapshots, tiers, summary, query_intelligence)

        return {
            "connected_accounts": account_payload,
            "capabilities": _CAPABILITIES,
            "methodology": {
                "squad": "traffic-masters",
                "google_ads_lead": "kasim-aslam",
                "principles": _KASIM_PRINCIPLES,
            },
            "summary": summary,
            "account_audit": audit,
            "performance_analysis": performance,
            "budget_optimization": budget,
            "tracking_setup": tracking,
            "scaling_plan": scaling,
            "strategy_blueprint": strategy,
            "query_intelligence": query_intelligence,
            "automations": automations,
            "recommended_actions": actions,
        }

    def build_campaign_detail(
        self,
        user_id: UUID,
        campaign_id: UUID,
        db: Session,
    ) -> dict[str, Any] | None:
        accounts = (
            db.query(GoogleAdsAccount)
            .filter(GoogleAdsAccount.user_id == user_id)
            .all()
        )
        account_by_id = {account.id: account for account in accounts}

        campaigns = (
            db.query(Campaign)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(GoogleAdsAccount.user_id == user_id)
            .all()
        )
        campaign_by_id = {campaign.id: campaign for campaign in campaigns}
        selected_campaign = campaign_by_id.get(campaign_id)
        if not selected_campaign:
            return None

        campaign_ids = list(campaign_by_id.keys())
        metrics_by_campaign: dict[Any, list[CampaignMetric]] = defaultdict(list)
        if campaign_ids:
            start_date = datetime.utcnow().date() - timedelta(days=30)
            metrics = (
                db.query(CampaignMetric)
                .filter(
                    CampaignMetric.campaign_id.in_(campaign_ids),
                    func.date(CampaignMetric.date) >= start_date,
                )
                .order_by(CampaignMetric.date.asc())
                .all()
            )
            for metric in metrics:
                metrics_by_campaign[metric.campaign_id].append(metric)

        snapshots = [
            self._build_campaign_snapshot(campaign, account_by_id.get(campaign.account_id), metrics_by_campaign[campaign.id])
            for campaign in campaigns
        ]
        snapshot_by_campaign_id = {snapshot["campaign_id"]: snapshot for snapshot in snapshots}
        selected_snapshot = snapshot_by_campaign_id.get(str(campaign_id))
        if not selected_snapshot:
            return None

        summary = self._build_summary(
            [
                {
                    "id": str(account.id),
                    "customer_id": account.customer_id,
                    "account_name": account.account_name,
                    "connected_at": account.connected_at.isoformat(),
                }
                for account in accounts
            ],
            snapshots,
        )
        tiers = self._split_campaign_tiers(snapshots)

        keywords = db.query(Keyword).filter(Keyword.campaign_id == campaign_id).all()
        search_terms = db.query(SearchTerm).filter(SearchTerm.campaign_id == campaign_id).all()
        query_intelligence = self._build_query_intelligence([selected_snapshot], keywords, search_terms)
        actions = [
            action
            for action in self._build_recommended_actions(
                snapshots,
                tiers,
                summary,
                query_intelligence,
            )
            if action.get("campaign_id") == selected_snapshot["campaign_id"]
            or (
                action.get("campaign_id") is None
                and action.get("source") == "setup-tracking"
            )
        ]

        analysis = self._build_campaign_analysis(
            selected_snapshot,
            summary,
            tiers,
            query_intelligence,
        )

        return {
            "id": selected_snapshot["campaign_id"],
            "name": selected_snapshot["name"],
            "status": selected_snapshot["status"],
            "primary_status": selected_snapshot.get("primary_status"),
            "primary_status_reasons": selected_snapshot.get("primary_status_reasons", []),
            "type": selected_snapshot["type"],
            "budget_daily": selected_snapshot["budget_daily"],
            "account_id": selected_snapshot["account_id"],
            "account_name": selected_snapshot["account_name"],
            "customer_id": selected_snapshot["customer_id"],
            "created_at": selected_campaign.created_at.isoformat(),
            "updated_at": selected_campaign.updated_at.isoformat(),
            "performance": self._build_campaign_performance_payload(
                campaign_id=campaign_id,
                metrics=metrics_by_campaign[campaign_id],
                days=30,
            ),
            "analysis": analysis,
            "query_intelligence": query_intelligence,
            "recommended_actions": actions,
        }

    def _empty_summary(self) -> dict[str, Any]:
        return {
            "account_count": 0,
            "campaign_count": 0,
            "active_campaign_count": 0,
            "period_days": 30,
            "impressions": 0,
            "clicks": 0,
            "conversions": 0.0,
            "cost": 0.0,
            "avg_ctr": None,
            "avg_cpc": None,
            "avg_cpa": None,
            "measurement_readiness": "LOW",
        }

    def _empty_query_intelligence(self) -> dict[str, Any]:
        return {
            "keyword_count": 0,
            "search_term_count": 0,
            "low_quality_keyword_count": 0,
            "top_keywords": [],
            "top_search_terms": [],
        }

    def _build_campaign_snapshot(
        self,
        campaign: Campaign,
        account: GoogleAdsAccount | None,
        metrics: list[CampaignMetric],
    ) -> dict[str, Any]:
        impressions = sum(metric.impressions for metric in metrics)
        clicks = sum(metric.clicks for metric in metrics)
        conversions = float(sum(metric.conversions for metric in metrics))
        cost = float(sum(metric.cost for metric in metrics))
        avg_ctr = (clicks / impressions) if impressions > 0 else None
        avg_cpc = (cost / clicks) if clicks > 0 else None
        avg_cpa = (cost / conversions) if conversions > 0 else None

        latest_metric = metrics[-1] if metrics else None
        trend = None
        if len(metrics) >= 14:
            recent = metrics[-7:]
            previous = metrics[-14:-7]
            recent_ctr = self._safe_ratio(sum(m.clicks for m in recent), sum(m.impressions for m in recent))
            previous_ctr = self._safe_ratio(sum(m.clicks for m in previous), sum(m.impressions for m in previous))
            if recent_ctr is not None and previous_ctr is not None:
                if recent_ctr > previous_ctr * 1.05:
                    trend = "up"
                elif recent_ctr < previous_ctr * 0.95:
                    trend = "down"
                else:
                    trend = "stable"

        return {
            "id": str(campaign.id),
            "campaign_id": str(campaign.id),
            "google_campaign_id": campaign.google_campaign_id,
            "name": campaign.name,
            "status": campaign.status,
            "primary_status": campaign.primary_status,
            "primary_status_reasons": campaign.primary_status_reasons or [],
            "type": campaign.campaign_type,
            "account_id": str(campaign.account_id),
            "account_name": account.account_name if account else "Conta Google Ads",
            "customer_id": account.customer_id if account else None,
            "budget_daily": float(campaign.budget_daily) if campaign.budget_daily else None,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "cost": cost,
            "avg_ctr": avg_ctr,
            "avg_cpc": avg_cpc,
            "avg_cpa": avg_cpa,
            "trend": trend,
            "latest_date": latest_metric.date.date().isoformat() if latest_metric else None,
            "days_with_data": len(metrics),
        }

    def _split_campaign_tiers(self, campaigns: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        if not campaigns:
            return {"winners": [], "performers": [], "underperformers": [], "zombies": []}

        cpa_candidates = [campaign["avg_cpa"] for campaign in campaigns if campaign["avg_cpa"]]
        ctr_candidates = [campaign["avg_ctr"] for campaign in campaigns if campaign["avg_ctr"]]
        cpa_median = median(cpa_candidates) if cpa_candidates else None
        ctr_median = median(ctr_candidates) if ctr_candidates else None

        tiers = {"winners": [], "performers": [], "underperformers": [], "zombies": []}
        for campaign in campaigns:
            clicks = campaign["clicks"]
            conversions = campaign["conversions"]
            cost = campaign["cost"]
            ctr = campaign["avg_ctr"]
            cpa = campaign["avg_cpa"]

            if cost > 0 and conversions == 0 and clicks <= 5:
                tiers["zombies"].append(campaign)
                continue

            if cost > 0 and (
                conversions == 0
                or (cpa_median and cpa and cpa > cpa_median * 1.35)
                or (ctr_median and ctr and ctr < ctr_median * 0.75 and cost > 0)
            ):
                tiers["underperformers"].append(campaign)
                continue

            if conversions > 0 and (
                (cpa_median and cpa and cpa <= cpa_median)
                or (ctr_median and ctr and ctr >= ctr_median * 1.1)
            ):
                tiers["winners"].append(campaign)
                continue

            tiers["performers"].append(campaign)

        return tiers

    def _build_summary(
        self,
        accounts: list[dict[str, Any]],
        campaigns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        impressions = sum(campaign["impressions"] for campaign in campaigns)
        clicks = sum(campaign["clicks"] for campaign in campaigns)
        conversions = sum(campaign["conversions"] for campaign in campaigns)
        cost = sum(campaign["cost"] for campaign in campaigns)

        measurement_readiness = "LOW"
        if conversions > 0 and len(campaigns) >= 1:
            measurement_readiness = "HIGH"
        elif clicks > 0 or impressions > 0:
            measurement_readiness = "MEDIUM"

        return {
            "account_count": len(accounts),
            "campaign_count": len(campaigns),
            "active_campaign_count": sum(1 for campaign in campaigns if campaign["status"] == "ENABLED"),
            "period_days": 30,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": round(conversions, 2),
            "cost": round(cost, 2),
            "avg_ctr": self._safe_ratio(clicks, impressions),
            "avg_cpc": round(cost / clicks, 2) if clicks > 0 else None,
            "avg_cpa": round(cost / conversions, 2) if conversions > 0 else None,
            "measurement_readiness": measurement_readiness,
        }

    def _build_account_audit(
        self,
        campaigns: list[dict[str, Any]],
        tiers: dict[str, list[dict[str, Any]]],
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        winners = tiers["winners"]
        underperformers = tiers["underperformers"]
        zombies = tiers["zombies"]
        wasted_spend = sum(campaign["cost"] for campaign in underperformers + zombies)
        wasted_share = self._safe_ratio(wasted_spend, summary["cost"]) or 0
        current_mix = self._categorize_campaign_mix(campaigns)

        scorecard = [
            self._build_dimension("Structure", self._score_structure(campaigns, current_mix), "Cobertura de tipos e organizacao das campanhas."),
            self._build_dimension("Targeting", self._score_targeting(summary), "Usa CTR medio como proxy de aderencia entre busca e anuncio."),
            self._build_dimension("Creative", self._score_creative(campaigns, winners), "Le os sinais de CTR e estabilidade dos vencedores."),
            self._build_dimension("Budget", self._score_budget(wasted_share), "Mede quanto do spend esta preso em campanhas fracas."),
            self._build_dimension("Bidding", self._score_bidding(summary), "Usa estabilidade de CPA medio e volume de conversao como proxy."),
            self._build_dimension("Tracking", self._score_tracking(summary), "Confere se existe sinal de conversao suficiente para otimizar."),
            self._build_dimension("Funnel Alignment", self._score_funnel_alignment(current_mix), "Busca a cobertura do framework branded / competitor / intent / remarketing."),
            self._build_dimension("Performance", self._score_performance(summary, winners), "Combina volume, eficiencia e proporcao de campanhas vencedoras."),
        ]
        health_score = sum(item["score"] for item in scorecard)

        top_findings = [
            f"{len(winners)} campanha(s) aparecem como vencedoras e estao prontas para receber mais foco.",
            f"{len(underperformers) + len(zombies)} campanha(s) concentram R${wasted_spend:.2f} de spend com baixa eficiencia.",
            "O framework Kasim/Traffic Masters pede revisar branded, competitor, general intent e remarketing antes de escalar.",
        ]
        if summary["impressions"] == 0 and summary["clicks"] == 0 and summary["cost"] == 0:
            top_findings = [
                "Ainda nao existe entrega suficiente para uma auditoria de performance confiavel.",
                "Antes de otimizar, vale confirmar aprovacao, elegibilidade, segmentacao e tracking da conta.",
                "Use o framework Kasim para separar branded, competitor, general intent e remarketing antes de escalar.",
            ]

        return {
            "health_score": health_score,
            "health_label": self._label_health(health_score),
            "wasted_spend": round(wasted_spend, 2),
            "wasted_spend_share": round(wasted_share, 4),
            "campaign_tiers": {
                "winners": len(winners),
                "performers": len(tiers["performers"]),
                "underperformers": len(underperformers),
                "zombies": len(zombies),
            },
            "dimensions": scorecard,
            "top_findings": top_findings,
        }

    def _build_performance_analysis(
        self,
        campaigns: list[dict[str, Any]],
        tiers: dict[str, list[dict[str, Any]]],
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        if summary["impressions"] == 0 and summary["clicks"] == 0 and summary["cost"] == 0:
            return {
                "period_days": 30,
                "metrics": summary,
                "top_spend_campaigns": campaigns[: max(1, min(3, len(campaigns)))],
                "top_ctr_campaigns": [],
                "insights": [
                    {
                        "title": "Sem volume suficiente",
                        "detail": "Nao ha impressoes, cliques nem custo no recorte sincronizado. Ainda nao existe base para 80/20 ou leitura de tendencia.",
                    },
                    {
                        "title": "Modo correto agora",
                        "detail": "A conta esta em diagnostico de entrega, nao em otimizacao de performance. Primeiro vem aprovacao, elegibilidade, tracking e estrutura.",
                    },
                    {
                        "title": "O que falta para opinar melhor",
                        "detail": "Precisamos de search terms, cliques reais, conversoes confiaveis e pelo menos 7 dias uteis de entrega.",
                    },
                ],
                "action_plan": [
                    "Dia 1: confirmar aprovacao, elegibilidade e status de entrega das campanhas.",
                    "Dia 2: validar tracking principal, Enhanced Conversions e URL final.",
                    "Dia 3: revisar estrutura de keywords por intencao e separar branded, general e competitor.",
                    "Dia 4-7: esperar o primeiro volume real antes de otimizar bid, copy ou budget.",
                ],
            }

        ordered_by_cost = sorted(campaigns, key=lambda item: item["cost"], reverse=True)
        ordered_by_ctr = sorted(
            [campaign for campaign in campaigns if campaign["avg_ctr"] is not None],
            key=lambda item: item["avg_ctr"],
            reverse=True,
        )
        top_spend = ordered_by_cost[: max(1, min(3, len(ordered_by_cost)))]
        top_ctr = ordered_by_ctr[: max(1, min(3, len(ordered_by_ctr)))] if ordered_by_ctr else []
        top_spend_share = self._safe_ratio(sum(item["cost"] for item in top_spend), summary["cost"]) or 0

        insights = [
            {
                "title": "80/20 do spend",
                "detail": f"As top campanhas por gasto concentram {top_spend_share:.0%} do investimento dos ultimos 30 dias.",
            },
            {
                "title": "Melhores sinais de clique",
                "detail": (
                    f"{', '.join(item['name'] for item in top_ctr[:2])}"
                    if top_ctr
                    else "Ainda nao ha CTR suficiente para ranquear criativos."
                ),
            },
            {
                "title": "Campanhas sob pressao",
                "detail": (
                    f"{len(tiers['underperformers']) + len(tiers['zombies'])} campanha(s) pedem corte, fix ou troca de copy."
                ),
            },
        ]

        action_plan = [
            "Dia 1: validar tracking de lead/purchase e Enhanced Conversions.",
            "Dia 2: pausar zombies e revisar campanhas sem conversao.",
            "Dia 3-4: redistribuir 10-20% do budget para vencedoras.",
            "Dia 5: revisar anuncios com CTR abaixo da media da conta.",
            "Dia 6-7: medir impacto e decidir nova rodada de escala.",
        ]

        return {
            "period_days": 30,
            "metrics": summary,
            "top_spend_campaigns": top_spend,
            "top_ctr_campaigns": top_ctr,
            "insights": insights,
            "action_plan": action_plan,
        }

    def _build_budget_optimization(
        self,
        campaigns: list[dict[str, Any]],
        tiers: dict[str, list[dict[str, Any]]],
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        winners = tiers["winners"]
        underperformers = tiers["underperformers"] + tiers["zombies"]
        spend = summary["cost"]
        current_cpa = summary["avg_cpa"]

        winner_spend = sum(item["cost"] for item in winners)
        winner_conversions = sum(item["conversions"] for item in winners)
        winner_cpa = round(winner_spend / winner_conversions, 2) if winner_conversions > 0 else current_cpa
        projected_base_cpa = winner_cpa or current_cpa or 0

        def scenario(name: str, multiplier: float, cpa_penalty: float) -> dict[str, Any]:
            budget = round(spend * multiplier, 2)
            projected_cpa = round(projected_base_cpa * cpa_penalty, 2) if projected_base_cpa else None
            projected_conversions = round(budget / projected_cpa, 2) if projected_cpa else 0
            return {
                "name": name,
                "budget": budget,
                "projected_cpa": projected_cpa,
                "projected_conversions": projected_conversions,
            }

        reallocations = []
        for source, target in zip(underperformers[:3], winners[:3] or winners[:1]):
            shift_value = round(source["cost"] * 0.2, 2)
            reallocations.append(
                {
                    "from_campaign": source["name"],
                    "to_campaign": target["name"],
                    "shift_amount": shift_value,
                    "rationale": "Mover 20% do budget de campanhas fracas para vencedoras com melhor CPA/CTR.",
                }
            )

        return {
            "current_monthly_spend": round(spend, 2),
            "wasted_spend": round(sum(item["cost"] for item in underperformers), 2),
            "winner_cpa": winner_cpa,
            "scenarios": [
                scenario("Conservador", 1.0, 1.0),
                scenario("Growth", 1.15, 1.1),
                scenario("Agressivo", 1.35, 1.25),
            ],
            "recommended_reallocation": reallocations,
            "guardrails": [
                "Nao aumentar mais de 20% do budget por ajuste.",
                "Reverter a mudanca se o CPA subir mais de 30% por 48h.",
                "Evitar cortar campanhas lucrativas para zero no mesmo dia.",
            ],
        }

    def _build_tracking_setup(self, summary: dict[str, Any]) -> dict[str, Any]:
        ready = summary["measurement_readiness"] == "HIGH"
        return {
            "status": "READY_TO_SCALE" if ready else "VALIDATE_BEFORE_SCALING",
            "summary": (
                "A conta ja envia sinais suficientes para comecar a otimizar com mais confianca."
                if ready
                else "Ainda faltam sinais confiaveis o suficiente; valide tracking antes de escalar."
            ),
            "checklist": self._build_tracking_checklist(ready),
            "recommended_events": [
                "Lead ou Purchase como conversao primaria",
                "Page View, View Content, Add to Cart e Begin Checkout como secundarias",
                "Importacao de conversoes via GA4 ou enhanced conversions quando possivel",
            ],
            "utm_strategy": _UTM_STRATEGY,
        }

    def _build_scaling_plan(
        self,
        campaigns: list[dict[str, Any]],
        tiers: dict[str, list[dict[str, Any]]],
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        eligible = [
            campaign
            for campaign in tiers["winners"]
            if campaign["conversions"] > 0 and campaign["avg_ctr"] is not None
        ]

        if not eligible:
            return {
                "eligible_campaigns": [],
                "recommended_method": "wait",
                "summary": "Nenhuma campanha atingiu sinal suficiente para um plano de escala seguro.",
                "guardrails": [
                    "Concluir tracking antes de qualquer aumento de budget.",
                    "Buscar 7+ dias de estabilidade antes de escalar.",
                ],
                "schedule": [],
            }

        method = "vertical" if len(eligible) <= 2 else "horizontal"
        schedule = [
            {"week": "Semana 1", "action": "Aumentar 10-15% das vencedoras e medir CPA/CTR por 48h."},
            {"week": "Semana 2", "action": "Completar o restante do shift se a performance estiver estavel."},
        ]
        return {
            "eligible_campaigns": eligible[:3],
            "recommended_method": method,
            "summary": f"{len(eligible)} campanha(s) mostram sinal para escala {method}.",
            "guardrails": [
                "Maximo de 20% de incremento por ajuste.",
                "Refresh de criativo se o CTR cair abaixo da media da conta.",
                "Pausar a escala se o CPA subir mais de 30% por dois dias.",
            ],
            "schedule": schedule,
        }

    def _build_strategy_blueprint(self, campaigns: list[dict[str, Any]]) -> dict[str, Any]:
        current_mix = self._categorize_campaign_mix(campaigns)
        gaps = [name for name, present in current_mix.items() if not present and name != "performance_max"]
        next_steps = [
            "Revisar se existe campanha branded protegendo seu termo de marca.",
            "Criar ou reforcar remarketing antes de escalar cold traffic.",
            "Separar general intent de competitor para ler eficiencia com mais clareza.",
        ]
        return {
            "framework": "Traffic Masters + Kasim Aslam",
            "principles": _KASIM_PRINCIPLES,
            "current_mix": current_mix,
            "gaps": gaps,
            "next_steps": next_steps,
        }

    def _build_query_intelligence(
        self,
        campaigns: list[dict[str, Any]],
        keywords: list[Keyword],
        search_terms: list[SearchTerm],
    ) -> dict[str, Any]:
        campaign_name_by_id = {campaign["campaign_id"]: campaign["name"] for campaign in campaigns}

        top_keywords = sorted(
            keywords,
            key=lambda item: ((item.quality_score or 0), item.text.lower()),
            reverse=True,
        )[:5]
        top_search_terms = sorted(
            search_terms,
            key=lambda item: (item.clicks, float(item.cost)),
            reverse=True,
        )[:5]

        return {
            "keyword_count": len(keywords),
            "search_term_count": len(search_terms),
            "low_quality_keyword_count": sum(
                1
                for keyword in keywords
                if keyword.quality_score is not None and keyword.quality_score > 0 and keyword.quality_score < 5
            ),
            "top_keywords": [
                {
                    "id": str(keyword.id),
                    "campaign_id": str(keyword.campaign_id),
                    "campaign_name": campaign_name_by_id.get(str(keyword.campaign_id), "Campanha"),
                    "text": keyword.text,
                    "match_type": keyword.match_type,
                    "quality_score": keyword.quality_score,
                    "bid": float(keyword.bid) if keyword.bid is not None else None,
                }
                for keyword in top_keywords
            ],
            "top_search_terms": [
                {
                    "id": str(term.id),
                    "campaign_id": str(term.campaign_id),
                    "campaign_name": campaign_name_by_id.get(str(term.campaign_id), "Campanha"),
                    "term": term.term,
                    "match_type": term.match_type,
                    "impressions": term.impressions,
                    "clicks": term.clicks,
                    "conversions": float(term.conversions),
                    "cost": float(term.cost),
                }
                for term in top_search_terms
            ],
        }

    def _build_automation_overview(self, user_id: UUID, db: Session) -> list[dict[str, Any]]:
        automations = (
            db.query(Automation)
            .join(GoogleAdsAccount, Automation.account_id == GoogleAdsAccount.id)
            .filter(GoogleAdsAccount.user_id == user_id)
            .order_by(Automation.created_at.desc())
            .limit(10)
            .all()
        )

        return [
            {
                "id": str(automation.id),
                "name": automation.name,
                "rule_type": automation.rule_type,
                "enabled": automation.enabled,
                "created_at": automation.created_at.isoformat(),
                "last_run_at": automation.last_run_at.isoformat() if automation.last_run_at else None,
                "next_run_at": automation.next_run_at.isoformat() if automation.next_run_at else None,
            }
            for automation in automations
        ]

    def _build_recommended_actions(
        self,
        campaigns: list[dict[str, Any]],
        tiers: dict[str, list[dict[str, Any]]],
        summary: dict[str, Any],
        query_intelligence: dict[str, Any],
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []

        for campaign in tiers["underperformers"][:2]:
            actions.append(
                {
                    "type": "PAUSE_UNDERPERFORMING",
                    "priority": "HIGH",
                    "title": f"Revisar ou pausar {campaign['name']}",
                    "description": "A campanha esta consumindo budget com baixa eficiencia relativa da conta.",
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": campaign["name"],
                    "estimated_impact": {
                        "metric": "cost_savings",
                        "current": round(campaign["cost"], 2),
                        "projected": round(campaign["cost"] * 0.7, 2),
                    },
                    "execution_modes": ["approve_and_execute", "create_automation"],
                    "action_payload": {
                        "campaign_id": campaign["campaign_id"],
                        "google_campaign_id": campaign["google_campaign_id"],
                        "reason": "underperforming_campaign",
                    },
                    "source": "audit-ad-account",
                }
            )

        for campaign in tiers["winners"][:2]:
            target_budget = round((campaign["budget_daily"] or 0) * 1.15, 2) if campaign["budget_daily"] else None
            actions.append(
                {
                    "type": "BUDGET_REALLOC",
                    "priority": "MEDIUM",
                    "title": f"Aumentar budget de {campaign['name']}",
                    "description": "Campanha com sinal de vencedora para receber mais volume com incremento gradual.",
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": campaign["name"],
                    "estimated_impact": {
                        "metric": "projected_extra_conversions",
                        "current": round(campaign["conversions"], 2),
                        "projected": round(campaign["conversions"] * 1.15, 2),
                    },
                    "execution_modes": ["approve_and_execute", "create_automation"],
                    "action_payload": {
                        "campaign_id": campaign["campaign_id"],
                        "target_budget_change_percent": 15,
                        "current_budget_daily": campaign["budget_daily"],
                        "target_daily_budget": target_budget,
                        "guardrail": "rollback_if_cpa_spikes_30_percent",
                    },
                    "source": "manage-budget",
                }
            )

        idle_learning_campaigns = [
            campaign
            for campaign in campaigns
            if campaign["status"] == "ENABLED"
            and (campaign["budget_daily"] or 0) >= 20
            and campaign["clicks"] == 0
            and campaign["cost"] == 0
            and campaign["days_with_data"] <= 3
        ]
        for campaign in idle_learning_campaigns[:2]:
            current_budget = float(campaign["budget_daily"] or 0)
            target_budget = round(max(20.0, current_budget * 0.75), 2)
            if target_budget >= current_budget:
                continue

            actions.append(
                {
                    "type": "BUDGET_REALLOC",
                    "priority": "LOW",
                    "title": f"Colocar {campaign['name']} em modo observacao",
                    "description": (
                        "Campanha ainda sem entrega no recorte salvo. Reduzir temporariamente o budget "
                        "ajuda a validar distribuicao, aprovacao e tracking sem queimar verba cedo demais."
                    ),
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": campaign["name"],
                    "estimated_impact": {
                        "metric": "daily_budget",
                        "current": round(current_budget, 2),
                        "projected": target_budget,
                    },
                    "execution_modes": ["approve_and_execute", "create_automation"],
                    "action_payload": {
                        "campaign_id": campaign["campaign_id"],
                        "target_budget_change_percent": -25,
                        "current_budget_daily": current_budget,
                        "target_daily_budget": target_budget,
                        "guardrail": "restore_after_first_delivery_signal",
                        "reason": "idle_learning_campaign",
                    },
                    "source": "manage-budget",
                }
            )

        low_ctr_campaigns = sorted(
            [campaign for campaign in campaigns if campaign["avg_ctr"] is not None],
            key=lambda item: item["avg_ctr"],
        )[:1]
        for campaign in low_ctr_campaigns:
            actions.append(
                {
                    "type": "AD_COPY",
                    "priority": "MEDIUM",
                    "title": f"Atualizar criativos/copy de {campaign['name']}",
                    "description": "CTR abaixo da media sugere fadiga criativa ou desalinhamento entre busca e anuncio.",
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": campaign["name"],
                    "estimated_impact": {
                        "metric": "ctr",
                        "current": round(campaign["avg_ctr"], 4) if campaign["avg_ctr"] is not None else None,
                        "projected": round((campaign["avg_ctr"] or 0) * 1.2, 4),
                    },
                    "execution_modes": ["plan_only"],
                    "action_payload": {
                        "campaign_id": campaign["campaign_id"],
                        "playbook": "refresh_ad_copy",
                    },
                    "source": "analyze-performance",
                }
            )

        for term in query_intelligence.get("top_search_terms", []):
            if term["clicks"] >= 5 and term["conversions"] == 0:
                actions.append(
                    {
                        "type": "KEYWORD_REMOVE",
                        "priority": "MEDIUM",
                        "title": f"Negativar ou revisar '{term['term']}'",
                        "description": "Search term com gasto e clique, mas sem conversao no recorte sincronizado.",
                        "campaign_id": term["campaign_id"],
                        "campaign_name": term["campaign_name"],
                        "estimated_impact": {
                            "metric": "cost_savings",
                            "current": round(term["cost"], 2),
                            "projected": round(term["cost"] * 0.8, 2),
                        },
                        "execution_modes": ["approve_and_execute", "create_automation"],
                        "action_payload": {
                            "campaign_id": term["campaign_id"],
                            "search_term": term["term"],
                            "match_type": term["match_type"],
                            "suggestion": "review_or_negative_keyword",
                        },
                        "source": "search-term-analysis",
                    }
                )
                break

        for term in query_intelligence.get("top_search_terms", []):
            if term["conversions"] > 0:
                actions.append(
                    {
                        "type": "KEYWORD_ADD",
                        "priority": "LOW",
                        "title": f"Promover '{term['term']}' a keyword controlada",
                        "description": "Search term com conversao que merece virar keyword propria para ganhar controle.",
                        "campaign_id": term["campaign_id"],
                        "campaign_name": term["campaign_name"],
                        "estimated_impact": {
                            "metric": "conversions",
                            "current": round(term["conversions"], 2),
                            "projected": round(term["conversions"] * 1.1, 2),
                        },
                        "execution_modes": ["approve_and_execute", "create_automation"],
                        "action_payload": {
                            "campaign_id": term["campaign_id"],
                            "keyword_text": term["term"],
                            "match_type": "EXACT",
                            "suggestion": "promote_search_term",
                        },
                        "source": "search-term-analysis",
                    }
                )
                break

        if summary["measurement_readiness"] != "HIGH":
            actions.append(
                {
                    "type": "BID_ADJUSTMENT",
                    "priority": "HIGH",
                    "title": "Validar tracking antes de otimizar lances",
                    "description": "Sem uma base de conversoes confiavel, o algoritmo do Google aprende errado.",
                    "campaign_id": None,
                    "campaign_name": None,
                    "estimated_impact": None,
                    "execution_modes": ["plan_only"],
                    "action_payload": {
                        "playbook": "validate_tracking",
                    },
                    "source": "setup-tracking",
                }
            )

        return actions[:5]

    def _build_campaign_performance_payload(
        self,
        campaign_id: UUID,
        metrics: list[CampaignMetric],
        days: int,
    ) -> dict[str, Any]:
        total_impressions = sum(metric.impressions for metric in metrics)
        total_clicks = sum(metric.clicks for metric in metrics)
        total_conversions = float(sum(metric.conversions for metric in metrics))
        total_cost = float(sum(metric.cost for metric in metrics))

        avg_ctr = self._safe_ratio(total_clicks, total_impressions)
        avg_cpc = round(total_cost / total_clicks, 2) if total_clicks > 0 else None
        avg_cpa = round(total_cost / total_conversions, 2) if total_conversions > 0 else None
        roas = round(total_conversions / total_cost, 2) if total_cost > 0 and total_conversions > 0 else None

        return {
            "campaign_id": str(campaign_id),
            "period_days": days,
            "metrics": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "total_cost": total_cost,
                "avg_ctr": avg_ctr,
                "avg_cpc": avg_cpc,
                "avg_cpa": avg_cpa,
                "roas": roas,
            },
            "daily_data": [
                {
                    "date": metric.date.isoformat(),
                    "impressions": metric.impressions,
                    "clicks": metric.clicks,
                    "conversions": float(metric.conversions),
                    "cost": float(metric.cost),
                    "ctr": metric.ctr,
                    "avg_cpc": metric.avg_cpc,
                    "roas": metric.roas,
                }
                for metric in metrics
            ],
        }

    def _build_campaign_analysis(
        self,
        campaign: dict[str, Any],
        summary: dict[str, Any],
        tiers: dict[str, list[dict[str, Any]]],
        query_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        tier = self._get_campaign_tier(campaign["campaign_id"], tiers)
        tier_labels = {
            "winners": "Vencedora",
            "performers": "Em observacao",
            "underperformers": "Sob correcao",
            "zombies": "Zumbi",
        }
        tier_label = tier_labels.get(tier, "Em observacao")

        campaign_ctr = campaign["avg_ctr"]
        account_ctr = summary["avg_ctr"]
        campaign_cpa = campaign["avg_cpa"]
        account_cpa = summary["avg_cpa"]
        delivery_diagnosis = self._build_delivery_diagnosis(campaign, summary, query_intelligence)

        wasted_terms = [
            term
            for term in query_intelligence["top_search_terms"]
            if term["clicks"] >= 5 and term["conversions"] == 0
        ]
        promoted_terms = [
            term
            for term in query_intelligence["top_search_terms"]
            if term["conversions"] > 0
        ]

        score = 55
        if tier == "winners":
            score += 22
        elif tier == "performers":
            score += 8
        elif tier == "underperformers":
            score -= 14
        else:
            score -= 24

        if campaign["trend"] == "up":
            score += 8
        elif campaign["trend"] == "down":
            score -= 8

        if campaign_ctr is not None and account_ctr is not None:
            if campaign_ctr >= account_ctr:
                score += 8
            else:
                score -= 6

        if campaign_cpa is not None and account_cpa is not None:
            if campaign_cpa <= account_cpa:
                score += 8
            elif campaign_cpa > account_cpa * 1.2:
                score -= 8

        if query_intelligence["low_quality_keyword_count"] > 0:
            score -= min(12, query_intelligence["low_quality_keyword_count"] * 3)
        if wasted_terms:
            score -= 8
        if summary["measurement_readiness"] != "HIGH":
            score -= 10

        score = max(0, min(100, score))
        if campaign["impressions"] == 0 and campaign["clicks"] == 0 and campaign["cost"] == 0:
            score = min(score, 35)

        analysis_mode = "OPTIMIZATION"
        confidence = "HIGH"
        if delivery_diagnosis["stage"] == "NOT_SERVING":
            analysis_mode = "DIAGNOSTIC"
            confidence = "HIGH" if delivery_diagnosis["google_primary_status"] else "LOW"
        elif delivery_diagnosis["stage"] == "LIMITED":
            analysis_mode = "DIAGNOSTIC"
            confidence = "MEDIUM"
        elif campaign["conversions"] == 0 or summary["measurement_readiness"] != "HIGH":
            analysis_mode = "DIAGNOSTIC"
            confidence = "MEDIUM"

        strengths = []
        if campaign["conversions"] > 0:
            strengths.append(
                f"Gerou {campaign['conversions']:.2f} conversoes nos ultimos 30 dias."
            )
        if campaign_ctr is not None and account_ctr is not None and campaign_ctr >= account_ctr:
            strengths.append("CTR acima ou em linha com a media da conta.")
        if tier == "winners":
            strengths.append("Ja opera como campanha vencedora para o recorte atual.")
        if promoted_terms:
            strengths.append("Ha search terms com conversao que merecem mais controle.")
        if delivery_diagnosis["stage"] == "SERVING":
            strengths.append("A campanha aparece como elegivel para entregar no recorte atual.")

        weaknesses = []
        if campaign["conversions"] == 0 and campaign["cost"] > 0:
            weaknesses.append("Consumiu budget sem gerar conversoes no periodo.")
        if campaign["clicks"] == 0 and campaign["cost"] == 0 and campaign["days_with_data"] <= 3:
            weaknesses.append("Ainda nao gerou entrega no recorte salvo; esta em fase inicial ou com pouca distribuicao.")
        if campaign_ctr is not None and account_ctr is not None and campaign_ctr < account_ctr:
            weaknesses.append("CTR abaixo da media da conta, sugerindo fadiga criativa ou busca desalinhada.")
        if query_intelligence["low_quality_keyword_count"] > 0:
            weaknesses.append("Existem keywords com quality score baixo puxando eficiencia para baixo.")
        if wasted_terms:
            weaknesses.append("Existem search terms com clique e gasto, mas sem conversao.")
        weaknesses.extend(delivery_diagnosis["blockers"][:3])

        opportunities = []
        if tier == "winners":
            opportunities.append("Escalar 10-15% com guardrail de CPA por 48h.")
        if campaign["clicks"] == 0 and campaign["cost"] == 0 and (campaign["budget_daily"] or 0) >= 20:
            opportunities.append("Aplicar budget de observacao enquanto a campanha ainda nao mostra entrega real.")
        if wasted_terms:
            opportunities.append("Negativar ou revisar termos desperdicando spend.")
        if promoted_terms:
            opportunities.append("Promover termos que convertem para keywords exatas controladas.")
        if summary["measurement_readiness"] != "HIGH":
            opportunities.append("Validar tracking antes de mexer agressivamente em bid e budget.")
        if campaign["days_with_data"] < 7:
            opportunities.append("Deixar mais dias de aprendizagem antes de decidir cortes maiores.")
        opportunities.extend(delivery_diagnosis["next_checks"][:2])

        next_steps = [
            "Validar o objetivo principal da campanha antes de mexer em budget ou bid.",
            "Executar apenas 1-2 mudancas por ciclo para conseguir ler causa e efeito.",
            "Revisar novamente a campanha apos um novo sync da conta.",
        ]
        if campaign["clicks"] == 0 and campaign["cost"] == 0 and campaign["days_with_data"] <= 3:
            next_steps[0] = "Confirmar se a campanha esta aprovada, elegivel e realmente entregando antes de escalar."
        next_steps = self._dedupe_items(delivery_diagnosis["next_checks"] + next_steps)

        guardrails = [
            "Nao aumentar budget mais de 20% por ajuste.",
            "Reverter a mudanca se o CPA piorar mais de 30% por 48h.",
            "Nao pausar campanha em aprendizado sem volume minimo suficiente.",
        ]

        return {
            "score": score,
            "tier": tier.upper(),
            "tier_label": tier_label,
            "analysis_mode": analysis_mode,
            "confidence": confidence,
            "trend": campaign["trend"],
            "summary": self._build_campaign_analysis_summary(
                campaign,
                tier_label,
                summary,
                wasted_terms,
                delivery_diagnosis,
            ),
            "benchmark": {
                "campaign_ctr": campaign_ctr,
                "account_avg_ctr": account_ctr,
                "campaign_cpa": campaign_cpa,
                "account_avg_cpa": account_cpa,
            },
            "strengths": self._dedupe_items(strengths),
            "weaknesses": self._dedupe_items(weaknesses),
            "opportunities": self._dedupe_items(opportunities),
            "next_steps": next_steps,
            "guardrails": guardrails,
            "delivery_diagnosis": delivery_diagnosis,
        }

    def _build_delivery_diagnosis(
        self,
        campaign: dict[str, Any],
        summary: dict[str, Any],
        query_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        google_primary_status = campaign.get("primary_status")
        google_primary_reasons = [
            str(reason)
            for reason in (campaign.get("primary_status_reasons") or [])
            if str(reason).strip()
        ]
        keyword_count = int(query_intelligence.get("keyword_count", 0))
        search_term_count = int(query_intelligence.get("search_term_count", 0))

        stage = "SERVING"
        if google_primary_status in {"PAUSED", "REMOVED", "PENDING", "ENDED", "MISCONFIGURED", "NOT_ELIGIBLE"}:
            stage = "NOT_SERVING"
        elif google_primary_status in {"LIMITED", "LEARNING"}:
            stage = "LIMITED"
        elif campaign["impressions"] == 0 and campaign["clicks"] == 0 and campaign["cost"] == 0:
            stage = "NOT_SERVING"

        blockers = [self._humanize_primary_reason(reason) for reason in google_primary_reasons]
        if stage == "NOT_SERVING" and not blockers:
            if campaign["status"] != "ENABLED":
                blockers.append("A campanha nao esta habilitada para veicular agora.")
            elif keyword_count == 0:
                blockers.append("Nao ha keywords sincronizadas para confirmar cobertura de busca e elegibilidade.")
            else:
                blockers.append("A campanha esta habilitada, mas ainda sem impressoes ou custo no recorte salvo.")
            if search_term_count == 0:
                blockers.append("Ainda nao existem search terms, o que reforca que a campanha nao entrou em distribuicao real.")
        if summary["measurement_readiness"] == "LOW":
            blockers.append("Tracking e medicao ainda estao fracos; o xquads veta otimizacao antes de validar esse ponto.")

        evidence = []
        if google_primary_status:
            evidence.append(
                f"Primary status do Google: {self._humanize_primary_status(google_primary_status)} ({google_primary_status})."
            )
        if google_primary_reasons:
            evidence.append(
                "Razoes sinalizadas pelo Google: " + ", ".join(google_primary_reasons) + "."
            )
        evidence.append(
            f"Recorte salvo: {campaign['impressions']} impressoes, {campaign['clicks']} cliques, "
            f"{campaign['conversions']:.2f} conversoes e R${campaign['cost']:.2f} de custo em 30 dias."
        )
        evidence.append(
            f"Cobertura sincronizada: {keyword_count} keyword(s) e {search_term_count} search term(s)."
        )

        next_checks = [
            "Rodar *diagnose para classificar se o gargalo esta em aprovacao, setup, budget, bidding ou estrutura.",
            "Executar o checklist de *setup-tracking antes de mexer em budget, lance ou keyword.",
        ]
        if stage == "NOT_SERVING":
            next_checks.insert(
                0,
                "Confirmar no Google Ads se a campanha esta aprovada, elegivel, com data correta e apta a servir.",
            )
            next_checks.append(
                "Revisar segmentacao geografica, idioma, agenda, cobertura de keywords e status dos anuncios/ad groups."
            )
        if any(reason.startswith("BIDDING_STRATEGY") for reason in google_primary_reasons):
            next_checks.append(
                "Abrir a estrategia de lance e validar se a campanha tem volume minimo e sinais suficientes para esse bidding."
            )
        if any(reason.startswith("BUDGET") for reason in google_primary_reasons):
            next_checks.append(
                "Comparar budget diario, share de impressao e distribuicao real antes de aprovar qualquer realocacao."
            )
        if any(
            token in reason
            for reason in google_primary_reasons
            for token in ("POLICY", "DISAPPROVED", "REVIEW")
        ):
            next_checks.append(
                "Revisar politicas, anuncios e assets reprovados antes de discutir performance."
            )
        if campaign["days_with_data"] < 7:
            next_checks.append(
                "Evitar conclusoes de performance antes de fechar ao menos 7 dias uteis de entrega."
            )

        xquads_playbooks = [
            "*diagnose (traffic-chief): triagem rapida do gargalo de entrega e roteamento do especialista certo.",
            "*setup-tracking (pixel-specialist): validar tag, enhanced conversions, URL final e QA de eventos.",
            "*audit-ad-account (ads-analyst): revisar estrutura, targeting, budget e lacunas da conta.",
        ]
        if stage != "NOT_SERVING":
            xquads_playbooks.append(
                "*analyze-performance (performance-analyst): usar so depois de 7+ dias uteis e tracking confiavel."
            )
        if google_primary_status in {"LIMITED", "LEARNING"}:
            xquads_playbooks.append(
                "*manage-budget (fiscal): modelar cenarios de budget depois que a campanha estiver entregando."
            )

        if stage == "NOT_SERVING":
            summary_text = (
                f"{campaign['name']} nao esta veiculando com consistencia. "
                f"{blockers[0] if blockers else 'O Google ainda nao entregou sinal suficiente para esta campanha.'}"
            )
        elif stage == "LIMITED":
            summary_text = (
                f"{campaign['name']} tem veiculacao limitada. "
                f"{blockers[0] if blockers else 'Ainda existem restricoes que pedem validacao antes de escalar.'}"
            )
        else:
            summary_text = (
                f"{campaign['name']} aparece como elegivel para veicular. "
                "Agora a conversa pode migrar de entrega para eficiencia e assertividade."
            )

        return {
            "stage": stage,
            "status_label": {
                "NOT_SERVING": "Nao esta veiculando",
                "LIMITED": "Veiculacao limitada",
                "SERVING": "Apta a veicular",
            }.get(stage, "Em avaliacao"),
            "summary": summary_text,
            "blockers": self._dedupe_items(blockers),
            "evidence": self._dedupe_items(evidence),
            "next_checks": self._dedupe_items(next_checks),
            "xquads_playbooks": self._dedupe_items(xquads_playbooks),
            "google_primary_status": google_primary_status,
            "google_primary_status_reasons": google_primary_reasons,
        }

    def _build_campaign_analysis_summary(
        self,
        campaign: dict[str, Any],
        tier_label: str,
        summary: dict[str, Any],
        wasted_terms: list[dict[str, Any]],
        delivery_diagnosis: dict[str, Any],
    ) -> str:
        if delivery_diagnosis["stage"] in {"NOT_SERVING", "LIMITED"}:
            return delivery_diagnosis["summary"]

        if campaign["clicks"] == 0 and campaign["cost"] == 0 and campaign["days_with_data"] <= 3:
            return (
                f"{campaign['name']} esta classificada como {tier_label.lower()}, mas ainda sem entrega real no recorte salvo. "
                f"Nesse momento o melhor movimento e validar elegibilidade, aprovacao e tracking antes de escalar o budget."
            )

        readiness = "tracking ja esta forte" if summary["measurement_readiness"] == "HIGH" else "tracking ainda pede validacao"
        wasted_term_note = (
            f" Foram detectados {len(wasted_terms)} termo(s) com desperdicio claro."
            if wasted_terms
            else ""
        )
        return (
            f"{campaign['name']} esta classificada como {tier_label.lower()}."
            f" Nos ultimos 30 dias acumulou {campaign['clicks']} cliques, "
            f"{campaign['conversions']:.2f} conversoes e custo de R${campaign['cost']:.2f}; "
            f"{readiness}.{wasted_term_note}"
        )

    def _humanize_primary_status(self, primary_status: str | None) -> str:
        if not primary_status:
            return "Sem status detalhado"
        mapping = {
            "ELIGIBLE": "Elegivel para servir",
            "LIMITED": "Limitada",
            "LEARNING": "Em aprendizagem",
            "PAUSED": "Pausada",
            "REMOVED": "Removida",
            "PENDING": "Pendente de inicio",
            "ENDED": "Encerrada",
            "MISCONFIGURED": "Mal configurada",
            "NOT_ELIGIBLE": "Nao elegivel",
        }
        return mapping.get(primary_status, primary_status.replace("_", " ").title())

    def _humanize_primary_reason(self, reason: str) -> str:
        exact_matches = {
            "CAMPAIGN_PAUSED": "A campanha esta pausada no Google Ads.",
            "CAMPAIGN_REMOVED": "A campanha foi removida e nao pode mais servir.",
            "CAMPAIGN_PENDING": "A campanha ainda nao entrou na janela de inicio.",
            "CAMPAIGN_ENDED": "A campanha ja passou da data final.",
            "CAMPAIGN_DRAFT": "A campanha ainda esta em rascunho.",
        }
        if reason in exact_matches:
            return exact_matches[reason]
        if reason.startswith("BIDDING_STRATEGY"):
            return "A estrategia de lance pede revisao; ela pode estar incompativel com o volume ou a configuracao atual."
        if reason.startswith("BUDGET"):
            return "O budget da campanha esta limitando distribuicao ou precisa de revisao."
        if reason.startswith("AD_GROUP"):
            return "Existe um bloqueio em ad group, anuncio ou estrutura interna da campanha."
        if "KEYWORD" in reason:
            return "Keywords ou correspondencias estao restringindo a campanha e precisam de revisao."
        if any(token in reason for token in ("POLICY", "DISAPPROVED", "REVIEW")):
            return "O Google sinalizou revisao, politica ou reprovacao em itens usados pela campanha."
        if "ASSET" in reason:
            return "Assets ou criativos da campanha pedem revisao para liberar ou ampliar entrega."
        if "TARGET" in reason or "LOCATION" in reason:
            return "Segmentacao ou alvo da campanha pode estar restrito demais."
        return f"Motivo tecnico sinalizado pelo Google: {reason}."

    def _dedupe_items(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in items:
            normalized = str(item).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered

    def _get_campaign_tier(
        self,
        campaign_id: str,
        tiers: dict[str, list[dict[str, Any]]],
    ) -> str:
        for tier_name, items in tiers.items():
            if any(item["campaign_id"] == campaign_id for item in items):
                return tier_name
        return "performers"

    def _build_tracking_checklist(self, ready: bool) -> list[dict[str, Any]]:
        checklist = []
        for index, item in enumerate(_TRACKING_CHECKLIST):
            checklist.append(
                {
                    "label": item,
                    "status": "done" if ready and index == len(_TRACKING_CHECKLIST) - 1 else "manual-review",
                }
            )
        return checklist

    def _categorize_campaign_mix(self, campaigns: list[dict[str, Any]]) -> dict[str, bool]:
        categories = {
            "branded": False,
            "competitor": False,
            "general_intent": False,
            "remarketing": False,
            "performance_max": False,
        }

        for campaign in campaigns:
            name = campaign["name"].lower()
            campaign_type = str(campaign["type"]).upper()
            if "brand" in name:
                categories["branded"] = True
            if "competitor" in name or "concorr" in name:
                categories["competitor"] = True
            if "remark" in name or "retarget" in name:
                categories["remarketing"] = True
            if campaign_type == "PERFORMANCE_MAX":
                categories["performance_max"] = True
            if campaign_type in {"SEARCH", "SHOPPING"} or "search" in name:
                categories["general_intent"] = True

        return categories

    def _build_dimension(self, name: str, score: int, note: str) -> dict[str, Any]:
        return {
            "name": name,
            "score": score,
            "status": "OK" if score >= 7 else ("WATCH" if score >= 5 else "FIX"),
            "note": note,
        }

    def _score_structure(self, campaigns: list[dict[str, Any]], current_mix: dict[str, bool]) -> int:
        distinct_types = len({str(campaign["type"]) for campaign in campaigns})
        mix_bonus = sum(1 for enabled in current_mix.values() if enabled)
        return max(3, min(10, 3 + distinct_types + mix_bonus // 2))

    def _score_targeting(self, summary: dict[str, Any]) -> int:
        ctr = summary["avg_ctr"] or 0
        if ctr >= 0.06:
            return 9
        if ctr >= 0.04:
            return 8
        if ctr >= 0.025:
            return 6
        if ctr > 0:
            return 4
        return 3

    def _score_creative(self, campaigns: list[dict[str, Any]], winners: list[dict[str, Any]]) -> int:
        if not campaigns:
            return 3
        with_ctr = [campaign for campaign in campaigns if campaign["avg_ctr"] is not None]
        if len(winners) >= 2 and len(with_ctr) >= 2:
            return 8
        if len(winners) >= 1:
            return 6
        return 4

    def _score_budget(self, wasted_share: float) -> int:
        if wasted_share <= 0.1:
            return 9
        if wasted_share <= 0.2:
            return 7
        if wasted_share <= 0.35:
            return 5
        return 3

    def _score_bidding(self, summary: dict[str, Any]) -> int:
        cpa = summary["avg_cpa"]
        if cpa is None and summary["conversions"] == 0:
            return 3
        if cpa is not None and cpa <= 20:
            return 8
        if cpa is not None and cpa <= 50:
            return 6
        return 5

    def _score_tracking(self, summary: dict[str, Any]) -> int:
        readiness = summary["measurement_readiness"]
        if readiness == "HIGH":
            return 9
        if readiness == "MEDIUM":
            return 6
        return 3

    def _score_funnel_alignment(self, current_mix: dict[str, bool]) -> int:
        coverage = sum(1 for key, enabled in current_mix.items() if enabled and key != "performance_max")
        if coverage >= 4:
            return 9
        if coverage == 3:
            return 7
        if coverage == 2:
            return 5
        return 3

    def _score_performance(self, summary: dict[str, Any], winners: list[dict[str, Any]]) -> int:
        if summary["conversions"] <= 0:
            return 3
        if len(winners) >= 2 and (summary["avg_cpa"] or 999) <= 30:
            return 8
        if len(winners) >= 1:
            return 6
        return 5

    def _label_health(self, score: int) -> str:
        if score >= 64:
            return "FORTE"
        if score >= 48:
            return "BOA_COM_AJUSTES"
        return "PRECISA_ATENCAO"

    def _safe_ratio(self, numerator: float, denominator: float) -> float | None:
        if denominator and denominator > 0:
            return round(numerator / denominator, 4)
        return None


google_ads_command_center_service = GoogleAdsCommandCenterService()
