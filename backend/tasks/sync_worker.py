"""
Background sync worker for Google Ads data.
"""

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime
import logging

from config import settings
from database.connection import SessionLocal
from models.database import GoogleAdsAccount
from services.campaign_service import campaign_service

logger = logging.getLogger(__name__)


def sync_all_campaigns():
    """
    Sync campaigns for all active Google Ads accounts.

    This function is called by APScheduler at scheduled intervals.
    """
    logger.info("Starting daily campaign sync...")

    db: Session = None
    try:
        db = SessionLocal()

        # Get all active accounts
        accounts = db.query(GoogleAdsAccount).filter(
            GoogleAdsAccount.is_active == True,
        ).all()

        if not accounts:
            logger.info("No active Google Ads accounts to sync")
            return

        logger.info(f"Syncing {len(accounts)} Google Ads accounts...")

        total_stats = {
            "accounts_synced": 0,
            "accounts_failed": 0,
            "total_campaigns_fetched": 0,
            "total_campaigns_created": 0,
            "total_campaigns_updated": 0,
            "total_errors": 0,
        }

        for account in accounts:
            try:
                logger.info(f"Syncing account {account.customer_id}...")

                stats = campaign_service.sync_campaigns(account, db)

                total_stats["accounts_synced"] += 1
                total_stats["total_campaigns_fetched"] += stats.get("fetched", 0)
                total_stats["total_campaigns_created"] += stats.get("created", 0)
                total_stats["total_campaigns_updated"] += stats.get("updated", 0)
                total_stats["total_errors"] += stats.get("errors", 0)

                logger.info(f"✅ Account {account.customer_id} synced: {stats}")

            except Exception as e:
                logger.error(f"Failed to sync account {account.customer_id}: {str(e)}")
                total_stats["accounts_failed"] += 1

        logger.info(f"✅ Daily sync completed: {total_stats}")
        return total_stats

    except Exception as e:
        logger.error(f"Fatal error in sync_all_campaigns: {str(e)}")
        return {
            "error": str(e),
            "status": "failed",
        }
    finally:
        if db:
            db.close()


def sync_account(account_id: str) -> dict:
    """
    Sync campaigns for a specific account.

    Args:
        account_id: Google Ads Account ID (customer_id)

    Returns:
        Sync stats
    """
    logger.info(f"Starting manual sync for account {account_id}...")

    db: Session = None
    try:
        db = SessionLocal()

        account = db.query(GoogleAdsAccount).filter(
            GoogleAdsAccount.customer_id == account_id,
        ).first()

        if not account:
            logger.warning(f"Account {account_id} not found")
            return {"error": "Account not found"}

        if not account.is_active:
            logger.warning(f"Account {account_id} is not active")
            return {"error": "Account is not active"}

        stats = campaign_service.sync_campaigns(account, db)
        logger.info(f"✅ Account {account_id} synced: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to sync account {account_id}: {str(e)}")
        return {
            "error": str(e),
            "status": "failed",
        }
    finally:
        if db:
            db.close()
