"""
APScheduler job scheduler for background sync and automation execution.
"""

from __future__ import annotations

import logging

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from tasks.automation_worker import run_due_automations
from tasks.sync_worker import sync_all_campaigns

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)


def start_scheduler():
    """Start the background scheduler with sync and automation jobs."""
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled")
        return

    if scheduler.running:
        logger.info("Scheduler already running")
        return

    if settings.SYNC_INTERVAL_HOURS > 0:
        scheduler.add_job(
            func=sync_google_ads,
            trigger=IntervalTrigger(hours=settings.SYNC_INTERVAL_HOURS),
            id="google_ads_sync_interval",
            name="Google Ads Interval Sync",
            replace_existing=True,
        )
    else:
        scheduler.add_job(
            func=sync_google_ads,
            trigger=CronTrigger(
                hour=settings.SYNC_SCHEDULE_HOUR,
                minute=0,
                timezone=pytz.timezone(settings.SCHEDULER_TIMEZONE),
            ),
            id="google_ads_sync_daily",
            name="Daily Google Ads Sync",
            replace_existing=True,
        )

    scheduler.add_job(
        func=run_google_ads_automations,
        trigger=IntervalTrigger(minutes=settings.AUTOMATION_RUN_INTERVAL_MINUTES),
        id="google_ads_automation_runner",
        name="Google Ads Automation Runner",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started with timezone %s | sync interval %sh | automation interval %smin",
        settings.SCHEDULER_TIMEZONE,
        settings.SYNC_INTERVAL_HOURS,
        settings.AUTOMATION_RUN_INTERVAL_MINUTES,
    )


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def sync_google_ads():
    """Sync Google Ads campaigns and metrics into the local database."""
    logger.info("Starting scheduled Google Ads sync...")
    try:
        stats = sync_all_campaigns()
        logger.info("Scheduled Google Ads sync finished: %s", stats)
        return stats
    except Exception as exc:
        logger.error("Error in scheduled sync: %s", exc)
        return {"status": "failed", "error": str(exc)}


def run_google_ads_automations():
    """Execute due Google Ads automations."""
    logger.info("Starting scheduled Google Ads automations...")
    try:
        stats = run_due_automations()
        logger.info("Scheduled automation runner finished: %s", stats)
        return stats
    except Exception as exc:
        logger.error("Error running automations: %s", exc)
        return {"status": "failed", "error": str(exc)}


def get_scheduler_status() -> dict:
    """Return current scheduler status and registered jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
        )

    return {
        "running": scheduler.running,
        "jobs_count": len(jobs),
        "jobs": jobs,
    }
