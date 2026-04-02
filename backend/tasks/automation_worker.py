"""
Background worker for executing due Google Ads automations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
import uuid

from sqlalchemy.orm import Session

from config import settings
from database.connection import SessionLocal
from integrations.google_ads_client import google_ads_wrapper
from models.database import AuditLog, Automation, Campaign, GoogleAdsAccount

logger = logging.getLogger(__name__)


def run_due_automations() -> dict:
    """
    Execute enabled automations whose next_run_at is due.
    """
    logger.info("Starting Google Ads automation runner...")

    db: Session | None = None
    try:
        db = SessionLocal()
        now = datetime.utcnow()

        automations = (
            db.query(Automation)
            .join(GoogleAdsAccount, Automation.account_id == GoogleAdsAccount.id)
            .filter(
                Automation.enabled == True,  # noqa: E712
                GoogleAdsAccount.is_active == True,  # noqa: E712
            )
            .filter(
                (Automation.next_run_at.is_(None)) | (Automation.next_run_at <= now)
            )
            .order_by(Automation.created_at.asc())
            .all()
        )

        if not automations:
            logger.info("No due automations to execute")
            return {
                "status": "idle",
                "executed": 0,
                "failed": 0,
            }

        stats = {
            "status": "completed",
            "executed": 0,
            "failed": 0,
        }

        for automation in automations:
            try:
                if _execute_single_automation(db, automation):
                    stats["executed"] += 1
                else:
                    stats["failed"] += 1
            except Exception as exc:
                logger.error("Automation %s failed: %s", automation.id, exc)
                stats["failed"] += 1
                automation.last_run_at = now
                automation.next_run_at = now + timedelta(
                    minutes=settings.AUTOMATION_RUN_INTERVAL_MINUTES
                )
                db.add(automation)
                db.commit()

        logger.info("Automation runner finished: %s", stats)
        return stats
    except Exception as exc:
        logger.error("Fatal error in run_due_automations: %s", exc)
        return {
            "status": "failed",
            "error": str(exc),
        }
    finally:
        if db:
            db.close()


def _execute_single_automation(db: Session, automation: Automation) -> bool:
    now = datetime.utcnow()
    account = (
        db.query(GoogleAdsAccount)
        .filter(GoogleAdsAccount.id == automation.account_id)
        .first()
    )
    if not account:
        logger.warning("Automation %s skipped: account not found", automation.id)
        return False

    config = automation.rule_config or {}
    action_type = config.get("action_type")
    payload = config.get("payload") or {}
    campaign_id = config.get("campaign_id")
    campaign = None
    if campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    succeeded = False
    audit_action = "AUTOMATION_EXECUTION"
    audit_resource_type = "AUTOMATION"
    audit_resource_id = str(automation.id)
    audit_changes: dict = {
        "rule_type": automation.rule_type,
        "action_type": action_type,
    }

    if action_type == "PAUSE_UNDERPERFORMING" and campaign:
            succeeded = google_ads_wrapper.pause_campaign(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
                google_campaign_id=campaign.google_campaign_id,
            )
            if succeeded:
                campaign.status = "PAUSED"
                audit_action = "AUTOMATION_RUN"
                audit_resource_type = "AUTOMATION"
                audit_resource_id = str(automation.id)
                audit_changes["after"] = {"status": "PAUSED"}

    elif action_type == "BUDGET_REALLOC" and campaign:
        current_budget = float(campaign.budget_daily or 0)
        change_percent = float(payload.get("target_budget_change_percent", 0))
        target_budget = payload.get("target_daily_budget")
        new_budget = (
            float(target_budget)
            if target_budget is not None
            else round(current_budget * (1 + (change_percent / 100)), 2)
        )
        if current_budget > 0 and new_budget > 0:
            succeeded = google_ads_wrapper.update_campaign_budget(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
                google_campaign_id=campaign.google_campaign_id,
                new_daily_budget=new_budget,
            )
            if succeeded:
                campaign.budget_daily = new_budget
                audit_action = "AUTOMATION_RUN"
                audit_resource_type = "AUTOMATION"
                audit_resource_id = str(automation.id)
                audit_changes["before"] = {"budget_daily": current_budget}
                audit_changes["after"] = {"budget_daily": new_budget}

    elif action_type == "KEYWORD_REMOVE" and campaign:
        search_term = payload.get("search_term") or payload.get("keyword_text")
        if search_term:
            succeeded = google_ads_wrapper.add_campaign_negative_keyword(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
                google_campaign_id=campaign.google_campaign_id,
                keyword_text=search_term,
                match_type=payload.get("match_type"),
            )
            if succeeded:
                audit_action = "AUTOMATION_RUN"
                audit_resource_type = "AUTOMATION"
                audit_resource_id = str(automation.id)
                audit_changes["after"] = {
                    "search_term": search_term,
                    "match_type": payload.get("match_type"),
                    "negative": True,
                }

    elif action_type == "KEYWORD_ADD" and campaign:
        keyword_text = payload.get("keyword_text")
        if keyword_text:
            result = google_ads_wrapper.add_keyword_to_best_ad_group(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
                google_campaign_id=campaign.google_campaign_id,
                keyword_text=keyword_text,
                match_type=payload.get("match_type"),
            )
            succeeded = bool(result)
            if succeeded:
                audit_action = "AUTOMATION_RUN"
                audit_resource_type = "AUTOMATION"
                audit_resource_id = str(automation.id)
                audit_changes["after"] = {
                    "keyword_text": keyword_text,
                    "match_type": result.get("match_type"),
                    "ad_group_id": result.get("ad_group_id"),
                    "ad_group_name": result.get("ad_group_name"),
                }

    else:
        logger.info(
            "Automation %s skipped: unsupported action type %s",
            automation.id,
            action_type,
        )

    automation.last_run_at = now
    automation.next_run_at = now + timedelta(
        minutes=settings.AUTOMATION_RUN_INTERVAL_MINUTES
    )
    db.add(automation)

    db.add(
        AuditLog(
            id=uuid.uuid4(),
            user_id=account.user_id,
            account_id=account.id,
            action_type=audit_action,
            resource_type=audit_resource_type,
            resource_id=audit_resource_id,
            changes=audit_changes | {"success": succeeded},
            source="AUTOMATION",
        )
    )
    db.commit()

    if succeeded:
        logger.info("Automation %s executed successfully", automation.id)
    else:
        logger.warning("Automation %s did not apply any change", automation.id)

    return succeeded
