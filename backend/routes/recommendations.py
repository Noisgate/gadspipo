"""
Google Ads recommendation and command center routes.
"""

from datetime import datetime, timedelta
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from config import settings
from database.connection import get_db
from integrations.google_ads_client import google_ads_wrapper
from models.database import (
    AuditLog,
    Automation,
    Campaign,
    GoogleAdsAccount,
    Recommendation,
    User,
)
from models.schemas import RecommendationActionRequest
from models.schemas import RecommendationProposalRequest, RecommendationProposalResponse
from services.campaign_service import campaign_service
from services.google_ads_command_center import google_ads_command_center_service
from services.recommendation_workshop_service import recommendation_workshop_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _load_user_campaign(
    db: Session,
    user_id,
    campaign_id,
) -> Campaign | None:
    return (
        db.query(Campaign)
        .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
        .filter(
            GoogleAdsAccount.user_id == user_id,
            Campaign.id == campaign_id,
        )
        .first()
    )


def _mark_recommendation_executed(
    recommendation: Recommendation,
) -> None:
    recommendation.status = "EXECUTED"
    recommendation.executed_at = datetime.utcnow()


def _build_recommendation_audit_log(
    *,
    action_type: str,
    user_id,
    account_id,
    resource_id: str | None,
    changes: dict,
) -> AuditLog:
    mapped_action_type = "RECOMMENDATION_ACCEPT"
    mapped_resource_type = "CAMPAIGN"

    if action_type == "PAUSE_UNDERPERFORMING":
        mapped_action_type = "CAMPAIGN_PAUSE"
        mapped_resource_type = "CAMPAIGN"
    elif action_type == "BUDGET_REALLOC":
        mapped_action_type = "BID_UPDATE"
        mapped_resource_type = "CAMPAIGN"
    elif action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
        mapped_action_type = "KEYWORD_ADD"
        mapped_resource_type = "KEYWORD"

    return AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        account_id=account_id,
        action_type=mapped_action_type,
        resource_type=mapped_resource_type,
        resource_id=resource_id,
        changes=changes,
        source="RECOMMENDATION",
    )


@router.get("/google-ads")
async def get_google_ads_command_center(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the Google Ads command center inspired by the Traffic Masters squad.
    """
    try:
        return google_ads_command_center_service.build(user.id, db)
    except Exception as exc:
        logger.error("Error loading Google Ads command center for %s: %s", user.email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load Google Ads command center",
        ) from exc


@router.post("/google-ads/refresh")
async def refresh_google_ads_command_center(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sync all active Google Ads accounts and rebuild the command center payload.
    """
    accounts = (
        db.query(GoogleAdsAccount)
        .filter(
            GoogleAdsAccount.user_id == user.id,
            GoogleAdsAccount.is_active == True,  # noqa: E712
        )
        .all()
    )

    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No connected Google Ads account found",
        )

    try:
        sync_results = []
        for account in accounts:
            stats = campaign_service.sync_campaigns(account, db)
            sync_results.append(
                {
                    "account_id": str(account.id),
                    "customer_id": account.customer_id,
                    "account_name": account.account_name,
                    "stats": stats,
                }
            )

        return {
            "sync_results": sync_results,
            "data": google_ads_command_center_service.build(user.id, db),
        }
    except Exception as exc:
        logger.error("Error refreshing Google Ads command center for %s: %s", user.email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh Google Ads command center",
        ) from exc


@router.get("/google-ads/automations")
async def list_google_ads_automations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List saved automations for the current user's Google Ads accounts.
    """
    automations = (
        db.query(Automation)
        .join(GoogleAdsAccount, Automation.account_id == GoogleAdsAccount.id)
        .filter(GoogleAdsAccount.user_id == user.id)
        .order_by(Automation.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(automation.id),
            "name": automation.name,
            "rule_type": automation.rule_type,
            "enabled": automation.enabled,
            "rule_config": automation.rule_config,
            "created_at": automation.created_at.isoformat(),
            "last_run_at": automation.last_run_at.isoformat() if automation.last_run_at else None,
            "next_run_at": automation.next_run_at.isoformat() if automation.next_run_at else None,
        }
        for automation in automations
    ]


@router.post("/google-ads/actions")
async def run_google_ads_action(
    request: RecommendationActionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute an immediate Google Ads action or convert it into an automation.
    """
    campaign = None
    account = None

    if request.campaign_id:
        campaign = _load_user_campaign(db, user.id, request.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )
        account = db.query(GoogleAdsAccount).filter(GoogleAdsAccount.id == campaign.account_id).first()

    recommendation = Recommendation(
        id=uuid.uuid4(),
        account_id=account.id if account else (
            db.query(GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user.id,
                GoogleAdsAccount.is_active == True,  # noqa: E712
            )
            .limit(1)
            .scalar()
        ),
        campaign_id=campaign.id if campaign else None,
        type=request.action_type,
        title=request.title,
        description=request.description,
        priority=request.priority,
        estimated_impact=None,
        action_payload=request.action_payload,
        status="OPEN",
    )

    if not recommendation.account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Google Ads account available for this action",
        )

    try:
        if request.execution_mode in {"execute_now", "approve_and_execute"}:
            if not campaign or not account:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This action needs a campaign context to execute immediately",
                )
            if request.action_type == "PAUSE_UNDERPERFORMING":
                succeeded = google_ads_wrapper.pause_campaign(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                )
                if not succeeded:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Google Ads rejected the pause operation",
                    )

                campaign.status = "PAUSED"
                _mark_recommendation_executed(recommendation)
                db.add(recommendation)
                db.add(
                    _build_recommendation_audit_log(
                        action_type=request.action_type,
                        user_id=user.id,
                        account_id=account.id,
                        resource_id=campaign.google_campaign_id,
                        changes={
                            "after": {"status": "PAUSED"},
                            "approval_note": request.approval_note,
                        },
                    )
                )
                db.commit()

                return {
                    "status": "executed",
                    "message": (
                        f"Proposta aprovada: campanha {campaign.name} pausada com sucesso"
                        if request.execution_mode == "approve_and_execute"
                        else f"Campanha {campaign.name} pausada com sucesso"
                    ),
                    "recommendation_id": str(recommendation.id),
                    "automation_id": None,
                }

            if request.action_type == "BUDGET_REALLOC":
                current_budget = float(campaign.budget_daily or 0)
                change_percent = float(request.action_payload.get("target_budget_change_percent", 0))
                target_budget = request.action_payload.get("target_daily_budget")
                new_budget = (
                    float(target_budget)
                    if target_budget is not None
                    else round(current_budget * (1 + (change_percent / 100)), 2)
                )

                if current_budget <= 0 or new_budget <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Campaign has no valid daily budget to update",
                    )

                succeeded = google_ads_wrapper.update_campaign_budget(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                    new_daily_budget=new_budget,
                )
                if not succeeded:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Google Ads rejected the budget update",
                    )

                campaign.budget_daily = new_budget
                _mark_recommendation_executed(recommendation)
                db.add(recommendation)
                db.add(
                    _build_recommendation_audit_log(
                        action_type=request.action_type,
                        user_id=user.id,
                        account_id=account.id,
                        resource_id=campaign.google_campaign_id,
                        changes={
                            "before": {"budget_daily": current_budget},
                            "after": {"budget_daily": new_budget},
                            "approval_note": request.approval_note,
                        },
                    )
                )
                db.commit()

                return {
                    "status": "executed",
                    "message": (
                        f"Proposta aprovada: budget diario de {campaign.name} atualizado para R${new_budget:.2f}"
                        if request.execution_mode == "approve_and_execute"
                        else f"Budget diario de {campaign.name} atualizado para R${new_budget:.2f}"
                    ),
                    "recommendation_id": str(recommendation.id),
                    "automation_id": None,
                }

            if request.action_type == "KEYWORD_REMOVE":
                search_term = (
                    request.action_payload.get("search_term")
                    or request.action_payload.get("keyword_text")
                )
                match_type = request.action_payload.get("match_type")
                if not search_term:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This keyword removal action needs a search term or keyword text",
                    )

                succeeded = google_ads_wrapper.add_campaign_negative_keyword(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                    keyword_text=search_term,
                    match_type=match_type,
                )
                if not succeeded:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Google Ads rejected the negative keyword operation",
                    )

                _mark_recommendation_executed(recommendation)
                db.add(recommendation)
                db.add(
                    _build_recommendation_audit_log(
                        action_type=request.action_type,
                        user_id=user.id,
                        account_id=account.id,
                        resource_id=campaign.google_campaign_id,
                        changes={
                            "after": {
                                "search_term": search_term,
                                "match_type": match_type,
                                "negative": True,
                            },
                            "approval_note": request.approval_note,
                        },
                    )
                )
                db.commit()

                return {
                    "status": "executed",
                    "message": (
                        f"Proposta aprovada: termo '{search_term}' negativado na campanha {campaign.name}"
                        if request.execution_mode == "approve_and_execute"
                        else f"Termo '{search_term}' negativado na campanha {campaign.name}"
                    ),
                    "recommendation_id": str(recommendation.id),
                    "automation_id": None,
                }

            if request.action_type == "KEYWORD_ADD":
                keyword_text = request.action_payload.get("keyword_text")
                match_type = request.action_payload.get("match_type")
                if not keyword_text:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This keyword add action needs keyword_text",
                    )

                result = google_ads_wrapper.add_keyword_to_best_ad_group(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                    keyword_text=keyword_text,
                    match_type=match_type,
                )
                if not result:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Google Ads rejected the keyword creation",
                    )

                _mark_recommendation_executed(recommendation)
                db.add(recommendation)
                db.add(
                    _build_recommendation_audit_log(
                        action_type=request.action_type,
                        user_id=user.id,
                        account_id=account.id,
                        resource_id=result.get("resource_name") or campaign.google_campaign_id,
                        changes={
                            "after": {
                                "keyword_text": keyword_text,
                                "match_type": result.get("match_type"),
                                "ad_group_id": result.get("ad_group_id"),
                                "ad_group_name": result.get("ad_group_name"),
                            },
                            "approval_note": request.approval_note,
                        },
                    )
                )
                db.commit()

                return {
                    "status": "executed",
                    "message": (
                        f"Proposta aprovada: keyword '{keyword_text}' criada no ad group "
                        f"{result.get('ad_group_name') or result.get('ad_group_id')}"
                        if request.execution_mode == "approve_and_execute"
                        else (
                            f"Keyword '{keyword_text}' criada no ad group "
                            f"{result.get('ad_group_name') or result.get('ad_group_id')}"
                        )
                    ),
                    "recommendation_id": str(recommendation.id),
                    "automation_id": None,
                }

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This action cannot be executed immediately",
            )

        if request.execution_mode != "create_automation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported execution mode",
            )

        rule_type_map = {
            "PAUSE_UNDERPERFORMING": "PAUSE_LOW_PERFORMERS",
            "BUDGET_REALLOC": "DAILY_BUDGET_CONTROL",
            "KEYWORD_ADD": "ENABLE_KEYWORDS",
            "KEYWORD_REMOVE": "ENABLE_KEYWORDS",
            "BID_ADJUSTMENT": "BID_ADJUSTMENT",
        }
        rule_type = rule_type_map.get(request.action_type)
        if not rule_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This action can only be saved as a plan, not as automation",
            )

        automation = Automation(
            id=uuid.uuid4(),
            account_id=recommendation.account_id,
            name=request.title,
            rule_type=rule_type,
            rule_config={
                "source": "command_center",
                "action_type": request.action_type,
                "campaign_id": str(request.campaign_id) if request.campaign_id else None,
                "campaign_name": request.campaign_name,
                "payload": request.action_payload,
            },
            enabled=True,
            next_run_at=datetime.utcnow() + timedelta(minutes=settings.AUTOMATION_RUN_INTERVAL_MINUTES),
        )
        recommendation.status = "ACCEPTED"

        db.add(recommendation)
        db.add(automation)
        db.add(
            AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                account_id=recommendation.account_id,
                action_type="RECOMMENDATION_ACCEPT",
                resource_type="AUTOMATION",
                resource_id=str(automation.id),
                changes={"rule_type": rule_type, "title": request.title},
                source="RECOMMENDATION",
            )
        )
        db.commit()

        return {
            "status": "automation_created",
            "message": f"Automacao criada para {request.title}",
            "recommendation_id": str(recommendation.id),
            "automation_id": str(automation.id),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error processing Google Ads action for %s: %s", user.email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Google Ads action",
        ) from exc


@router.post("/google-ads/proposal", response_model=RecommendationProposalResponse)
async def build_google_ads_proposal(
    request: RecommendationProposalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Turn a raw Google Ads recommendation into a discussion-ready proposal.
    """
    try:
        return recommendation_workshop_service.build_proposal(
            user_id=user.id,
            request=request,
            db=db,
        )
    except Exception as exc:
        logger.error("Error building Google Ads proposal for %s: %s", user.email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build Google Ads proposal",
        ) from exc
