"""
Keyword and search-term sync services for Google Ads.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from integrations.google_ads_client import google_ads_wrapper
from models.database import Campaign, GoogleAdsAccount, Keyword, SearchTerm

logger = logging.getLogger(__name__)


class KeywordService:
    """Synchronize keywords and search terms from Google Ads."""

    def sync_account_assets(
        self,
        account: GoogleAdsAccount,
        db: Session,
    ) -> dict[str, int]:
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.account_id == account.id)
            .all()
        )
        campaign_by_google_id = {
            campaign.google_campaign_id: campaign for campaign in campaigns
        }

        stats = {
            "keywords_synced": 0,
            "search_terms_synced": 0,
            "asset_errors": 0,
        }

        try:
            keywords = google_ads_wrapper.get_keywords(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
            )
            for item in keywords:
                campaign = campaign_by_google_id.get(str(item["campaign_id"]))
                if not campaign:
                    continue

                record = (
                    db.query(Keyword)
                    .filter(
                        Keyword.campaign_id == campaign.id,
                        Keyword.google_keyword_id == str(item["keyword_id"]),
                    )
                    .first()
                )

                if record:
                    record.text = item["text"]
                    record.match_type = item["match_type"]
                    record.bid = self._decimal_or_none(item.get("bid_micros"))
                    record.quality_score = item.get("quality_score")
                    record.updated_at = datetime.utcnow()
                else:
                    db.add(
                        Keyword(
                            campaign_id=campaign.id,
                            google_keyword_id=str(item["keyword_id"]),
                            text=item["text"],
                            match_type=item["match_type"],
                            bid=self._decimal_or_none(item.get("bid_micros")),
                            quality_score=item.get("quality_score"),
                        )
                    )

                stats["keywords_synced"] += 1
        except Exception as exc:
            logger.warning(
                "Keyword sync failed for account %s: %s",
                account.customer_id,
                exc,
            )
            stats["asset_errors"] += 1

        try:
            search_terms = google_ads_wrapper.get_search_terms(
                refresh_token=account.refresh_token,
                customer_id=account.customer_id,
            )
            for item in search_terms:
                campaign = campaign_by_google_id.get(str(item["campaign_id"]))
                if not campaign:
                    continue

                record = (
                    db.query(SearchTerm)
                    .filter(
                        SearchTerm.campaign_id == campaign.id,
                        SearchTerm.term == item["term"],
                    )
                    .first()
                )

                if record:
                    record.match_type = item.get("match_type")
                    record.impressions = item.get("impressions", 0)
                    record.clicks = item.get("clicks", 0)
                    record.conversions = item.get("conversions", 0.0)
                    record.cost = Decimal(str(item.get("cost_micros", 0) / 1_000_000))
                    record.last_seen_at = datetime.utcnow()
                    record.updated_at = datetime.utcnow()
                else:
                    db.add(
                        SearchTerm(
                            campaign_id=campaign.id,
                            term=item["term"],
                            match_type=item.get("match_type"),
                            impressions=item.get("impressions", 0),
                            clicks=item.get("clicks", 0),
                            conversions=item.get("conversions", 0.0),
                            cost=Decimal(str(item.get("cost_micros", 0) / 1_000_000)),
                            last_seen_at=datetime.utcnow(),
                        )
                    )

                stats["search_terms_synced"] += 1
        except Exception as exc:
            logger.warning(
                "Search term sync failed for account %s: %s",
                account.customer_id,
                exc,
            )
            stats["asset_errors"] += 1

        db.flush()
        return stats

    def get_campaign_keywords(self, campaign_id: UUID, db: Session) -> list[dict[str, Any]]:
        keywords = (
            db.query(Keyword)
            .filter(Keyword.campaign_id == campaign_id)
            .order_by(Keyword.quality_score.desc().nullslast(), Keyword.text.asc())
            .all()
        )

        return [
            {
                "id": str(keyword.id),
                "campaign_id": str(keyword.campaign_id),
                "google_keyword_id": keyword.google_keyword_id,
                "text": keyword.text,
                "match_type": keyword.match_type,
                "bid": float(keyword.bid) if keyword.bid is not None else None,
                "quality_score": keyword.quality_score,
            }
            for keyword in keywords
        ]

    def get_campaign_search_terms(self, campaign_id: UUID, db: Session) -> list[dict[str, Any]]:
        terms = (
            db.query(SearchTerm)
            .filter(SearchTerm.campaign_id == campaign_id)
            .order_by(SearchTerm.clicks.desc(), SearchTerm.cost.desc())
            .all()
        )

        return [
            {
                "id": str(term.id),
                "campaign_id": str(term.campaign_id),
                "term": term.term,
                "match_type": term.match_type,
                "impressions": term.impressions,
                "clicks": term.clicks,
                "conversions": float(term.conversions),
                "cost": float(term.cost),
                "last_seen_at": term.last_seen_at.isoformat(),
            }
            for term in terms
        ]

    def _decimal_or_none(self, bid_micros: int | None) -> Decimal | None:
        if bid_micros is None:
            return None
        return Decimal(str(bid_micros / 1_000_000))


keyword_service = KeywordService()
