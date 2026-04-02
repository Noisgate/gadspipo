"""
Campaign service for fetching and syncing Google Ads data.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
import logging
from typing import List, Dict

from models.database import (
    GoogleAdsAccount,
    Campaign,
    CampaignMetric,
)
from integrations.google_ads_client import google_ads_wrapper
from services.keyword_service import keyword_service

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing campaigns and metrics."""

    def sync_campaigns(
        self,
        account: GoogleAdsAccount,
        db: Session,
    ) -> Dict[str, int]:
        """
        Sync campaigns from Google Ads to database.

        Args:
            account: GoogleAdsAccount to sync
            db: Database session

        Returns:
            Dict with sync stats (created, updated, errors)
        """
        try:
            google_campaigns = google_ads_wrapper.get_campaigns(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
            )
            historical_metrics = google_ads_wrapper.get_campaign_metrics_last_30_days(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
            )

            metrics_by_campaign: dict[str, list[dict]] = {}
            for metric_row in historical_metrics:
                campaign_key = str(metric_row["campaign_id"])
                metrics_by_campaign.setdefault(campaign_key, []).append(metric_row)

            stats = {
                "fetched": len(google_campaigns),
                "created": 0,
                "updated": 0,
                "errors": 0,
            }

            for google_campaign in google_campaigns:
                try:
                    campaign = db.query(Campaign).filter(
                        Campaign.account_id == account.id,
                        Campaign.google_campaign_id == str(google_campaign["id"]),
                    ).first()

                    if campaign:
                        # Update existing campaign
                        campaign.name = google_campaign["name"]
                        campaign.status = google_campaign["status"]
                        campaign.campaign_type = google_campaign["type"]
                        campaign.primary_status = google_campaign.get("primary_status")
                        campaign.primary_status_reasons = google_campaign.get("primary_status_reasons")
                        if google_campaign.get("daily_budget_micros"):
                            campaign.budget_daily = Decimal(
                                google_campaign["daily_budget_micros"] / 1_000_000
                            )
                        campaign.updated_at = datetime.utcnow()
                        stats["updated"] += 1
                    else:
                        # Create new campaign
                        campaign = Campaign(
                            account_id=account.id,
                            google_campaign_id=str(google_campaign["id"]),
                            name=google_campaign["name"],
                            status=google_campaign["status"],
                            campaign_type=google_campaign["type"],
                            primary_status=google_campaign.get("primary_status"),
                            primary_status_reasons=google_campaign.get("primary_status_reasons"),
                            budget_daily=(
                                Decimal(google_campaign["daily_budget_micros"] / 1_000_000)
                                if google_campaign.get("daily_budget_micros")
                                else None
                            ),
                        )
                        db.add(campaign)
                        # Ensure the campaign has a primary key before creating
                        # related metric rows in the same transaction.
                        db.flush()
                        stats["created"] += 1

                    # Persist the trailing 30-day history first so audits and
                    # trend analysis can work with more than a single-day view.
                    for metric_row in metrics_by_campaign.get(str(google_campaign["id"]), []):
                        self._upsert_campaign_metrics(
                            campaign=campaign,
                            metric_date=self._normalize_metric_date(metric_row["date"]),
                            impressions=metric_row.get("impressions", 0),
                            clicks=metric_row.get("clicks", 0),
                            conversions=metric_row.get("conversions", 0),
                            cost_micros=metric_row.get("cost_micros", 0),
                            db=db,
                        )

                    # Ensure today's snapshot is present with the freshest
                    # numbers from the current sync response.
                    self._upsert_campaign_metrics(
                        campaign=campaign,
                        metric_date=datetime.utcnow().date(),
                        impressions=google_campaign.get("impressions", 0),
                        clicks=google_campaign.get("clicks", 0),
                        conversions=google_campaign.get("conversions", 0),
                        cost_micros=google_campaign.get("cost_micros", 0),
                        db=db,
                    )

                    db.flush()

                except Exception as e:
                    logger.error(f"Error syncing campaign {google_campaign.get('id')}: {str(e)}")
                    stats["errors"] += 1
                    db.rollback()

            try:
                asset_stats = keyword_service.sync_account_assets(account, db)
                stats.update(asset_stats)
            except Exception as asset_error:
                logger.warning(
                    "Keyword/search term sync failed for account %s: %s",
                    account.customer_id,
                    asset_error,
                )
                stats["asset_errors"] = stats.get("asset_errors", 0) + 1

            db.commit()
            logger.info(f"Sync completed for account {account.customer_id}: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error syncing campaigns for account {account.id}: {str(e)}")
            db.rollback()
            raise

    def _normalize_metric_date(self, value: date | datetime | str) -> date:
        """Normalize Google Ads date values to a Python date."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.fromisoformat(str(value)).date()

    def _upsert_campaign_metrics(
        self,
        campaign: Campaign,
        metric_date: date,
        impressions: int,
        clicks: int,
        conversions: float,
        cost_micros: int,
        db: Session,
    ) -> None:
        """
        Insert or update campaign metrics for a given date.

        Args:
            campaign: Campaign object
            metric_date: Metric date
            impressions: Number of impressions
            clicks: Number of clicks
            conversions: Number of conversions
            cost_micros: Cost in micros
            db: Database session
        """
        try:
            metric_date_dt = datetime.combine(metric_date, datetime.min.time())
            existing_metric = db.query(CampaignMetric).filter(
                CampaignMetric.campaign_id == campaign.id,
                func.date(CampaignMetric.date) == metric_date,
            ).first()

            conversions_decimal = Decimal(str(conversions or 0))
            cost_decimal = Decimal((cost_micros or 0) / 1_000_000)

            if existing_metric:
                # Update existing metric
                existing_metric.date = metric_date_dt
                existing_metric.impressions = impressions
                existing_metric.clicks = clicks
                existing_metric.conversions = conversions_decimal
                existing_metric.cost = cost_decimal

                # Calculate derived metrics
                if existing_metric.impressions > 0:
                    existing_metric.ctr = (
                        existing_metric.clicks / existing_metric.impressions
                    )
                if existing_metric.clicks > 0:
                    existing_metric.avg_cpc = (
                        existing_metric.cost / existing_metric.clicks
                    )
                if existing_metric.conversions > 0 and existing_metric.cost > 0:
                    existing_metric.roas = (
                        existing_metric.conversions / existing_metric.cost
                    )
            else:
                # Create new metric
                # Calculate metrics
                ctr = None
                if impressions > 0:
                    ctr = clicks / impressions

                avg_cpc = None
                if clicks > 0:
                    avg_cpc = cost_decimal / clicks

                roas = None
                if conversions_decimal > 0 and cost_decimal > 0:
                    roas = conversions_decimal / cost_decimal

                metric = CampaignMetric(
                    campaign_id=campaign.id,
                    date=metric_date_dt,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions_decimal,
                    cost=cost_decimal,
                    ctr=ctr,
                    avg_cpc=avg_cpc,
                    roas=roas,
                )
                db.add(metric)

        except Exception as e:
            logger.error(f"Error adding metrics for campaign {campaign.id}: {str(e)}")
            raise

    def get_user_campaigns(
        self,
        user_id: UUID,
        db: Session,
    ) -> List[Dict]:
        """
        Get all campaigns for a user across all accounts.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of campaign data with latest metrics
        """
        try:
            campaigns = db.query(Campaign).join(
                GoogleAdsAccount,
                Campaign.account_id == GoogleAdsAccount.id,
            ).filter(
                GoogleAdsAccount.user_id == user_id,
            ).all()

            result = []
            for campaign in campaigns:
                latest_metric = db.query(CampaignMetric).filter(
                    CampaignMetric.campaign_id == campaign.id,
                ).order_by(
                    CampaignMetric.date.desc(),
                ).first()

                campaign_data = {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "status": campaign.status,
                    "type": campaign.campaign_type,
                    "budget_daily": float(campaign.budget_daily) if campaign.budget_daily else None,
                    "primary_status": campaign.primary_status,
                    "primary_status_reasons": campaign.primary_status_reasons or [],
                    "account_id": str(campaign.account_id),
                    "created_at": campaign.created_at.isoformat(),
                    "updated_at": campaign.updated_at.isoformat(),
                }

                if latest_metric:
                    campaign_data["latest_metrics"] = {
                        "date": latest_metric.date.isoformat(),
                        "impressions": latest_metric.impressions,
                        "clicks": latest_metric.clicks,
                        "conversions": float(latest_metric.conversions),
                        "cost": float(latest_metric.cost),
                        "ctr": latest_metric.ctr,
                        "avg_cpc": latest_metric.avg_cpc,
                        "roas": latest_metric.roas,
                    }

                result.append(campaign_data)

            return result

        except Exception as e:
            logger.error(f"Error fetching campaigns for user {user_id}: {str(e)}")
            raise

    def get_campaign_performance(
        self,
        campaign_id: UUID,
        days: int = 30,
        db: Session = None,
    ) -> Dict:
        """
        Get campaign performance metrics for last N days.

        Args:
            campaign_id: Campaign ID
            days: Number of days to fetch
            db: Database session

        Returns:
            Campaign performance data
        """
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()

            metrics = db.query(CampaignMetric).filter(
                CampaignMetric.campaign_id == campaign_id,
                CampaignMetric.date >= start_date,
            ).order_by(
                CampaignMetric.date.asc(),
            ).all()

            # Aggregate metrics
            total_impressions = sum(m.impressions for m in metrics)
            total_clicks = sum(m.clicks for m in metrics)
            total_conversions = sum(m.conversions for m in metrics)
            total_cost = sum(m.cost for m in metrics)

            # Calculate averages
            avg_ctr = None
            if total_impressions > 0:
                avg_ctr = total_clicks / total_impressions

            avg_cpc = None
            if total_clicks > 0:
                avg_cpc = total_cost / total_clicks

            roas = None
            if total_conversions > 0 and total_cost > 0:
                roas = total_conversions / total_cost

            return {
                "campaign_id": str(campaign_id),
                "period_days": days,
                "metrics": {
                    "total_impressions": total_impressions,
                    "total_clicks": total_clicks,
                    "total_conversions": float(total_conversions),
                    "total_cost": float(total_cost),
                    "avg_ctr": avg_ctr,
                    "avg_cpc": avg_cpc,
                    "roas": roas,
                },
                "daily_data": [
                    {
                        "date": m.date.isoformat(),
                        "impressions": m.impressions,
                        "clicks": m.clicks,
                        "conversions": float(m.conversions),
                        "cost": float(m.cost),
                        "ctr": m.ctr,
                        "avg_cpc": m.avg_cpc,
                        "roas": m.roas,
                    }
                    for m in metrics
                ],
            }

        except Exception as e:
            logger.error(f"Error fetching campaign performance for {campaign_id}: {str(e)}")
            raise


# Global service instance
campaign_service = CampaignService()
