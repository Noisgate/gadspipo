"""
Google Ads API client using the official google-ads Python library.

Credentials are loaded from backend/google-ads.yaml (preferred) or from
environment variables defined in config.py.  The refresh_token is always
overridden per-user from the database, so the YAML file only needs:
  developer_token, client_id, client_secret (and optionally login_customer_id).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Map Google Ads channel types to our DB enum values
_CHANNEL_TYPE_MAP = {
    "SEARCH": "SEARCH",
    "DISPLAY_NETWORK": "DISPLAY",
    "SHOPPING": "SHOPPING",
    "VIDEO": "VIDEO",
    "PERFORMANCE_MAX": "PERFORMANCE_MAX",
    "MULTI_CHANNEL": "SEARCH",
    "UNKNOWN": "SEARCH",
    "UNSPECIFIED": "SEARCH",
}

_MATCH_TYPE_MAP = {
    "EXACT": "EXACT",
    "PHRASE": "PHRASE",
    "BROAD": "BROAD",
    "BROAD_MATCH_MODIFIER": "BROAD_MODIFIER",
    "UNKNOWN": "BROAD",
    "UNSPECIFIED": "BROAD",
}

_NEGATIVE_MATCH_TYPE_MAP = {
    "EXACT": "EXACT",
    "NEAR_EXACT": "EXACT",
    "PHRASE": "PHRASE",
    "NEAR_PHRASE": "PHRASE",
    "BROAD": "BROAD",
    "UNSPECIFIED": "PHRASE",
    "UNKNOWN": "PHRASE",
}


_YAML_PATH = Path(__file__).parent.parent / "google-ads.yaml"


def _load_yaml_config() -> dict:
    """Load optional Google Ads YAML settings."""
    if not _YAML_PATH.exists():
        return {}

    import yaml

    with open(_YAML_PATH) as f:
        data = yaml.safe_load(f) or {}

    return data if isinstance(data, dict) else {}


def _build_client(refresh_token: str, login_customer_id: str = None):
    """
    Build a GoogleAdsClient instance.

    Loads static credentials (developer_token, client_id, client_secret) from
    backend/google-ads.yaml when present, otherwise falls back to env vars.
    The refresh_token is always the per-user value from the database.
    """
    from google.ads.googleads.client import GoogleAdsClient
    from config import settings

    yaml_config = _load_yaml_config()
    config = {
        # Prefer the active app settings so refresh tokens issued by the current
        # OAuth flow remain compatible with the Google Ads client.
        "developer_token": settings.GOOGLE_ADS_DEVELOPER_TOKEN or yaml_config.get("developer_token", ""),
        "client_id": settings.GOOGLE_CLIENT_ID or yaml_config.get("client_id", ""),
        "client_secret": settings.GOOGLE_CLIENT_SECRET or yaml_config.get("client_secret", ""),
        "refresh_token": refresh_token,
        "use_proto_plus": True,
    }

    effective_login_customer_id = (
        login_customer_id
        or settings.GOOGLE_ADS_LOGIN_CUSTOMER_ID
        or yaml_config.get("login_customer_id")
    )

    if effective_login_customer_id:
        config["login_customer_id"] = str(effective_login_customer_id).replace("-", "")

    missing_fields = [key for key in ("developer_token", "client_id", "client_secret") if not config.get(key)]
    if missing_fields:
        missing_csv = ", ".join(missing_fields)
        raise ValueError(f"Missing Google Ads configuration: {missing_csv}")

    return GoogleAdsClient.load_from_dict(config)


class GoogleAdsClientWrapper:
    """High-level wrapper around the Google Ads API."""

    def _normalize_negative_match_type(self, match_type: str | None) -> str:
        cleaned = str(match_type or "").upper()
        return _NEGATIVE_MATCH_TYPE_MAP.get(cleaned, "PHRASE")

    def _normalize_keyword_match_type(self, match_type: str | None) -> str:
        cleaned = str(match_type or "").upper()
        return _MATCH_TYPE_MAP.get(cleaned, "BROAD")

    def list_accessible_customers(self, refresh_token: str) -> list[dict]:
        """
        List all Google Ads accounts the user has access to.

        Returns a list of dicts with customer_id, name, is_manager.
        """
        from google.ads.googleads.errors import GoogleAdsException

        client = _build_client(refresh_token)
        customer_service = client.get_service("CustomerService")
        ga_service = client.get_service("GoogleAdsService")

        try:
            accessible = customer_service.list_accessible_customers()
        except GoogleAdsException as ex:
            logger.error("Error listing accessible customers")
            for error in ex.failure.errors:
                logger.error(f"  {error.message}")
            raise

        accounts = []
        for resource_name in accessible.resource_names:
            customer_id = resource_name.split("/")[-1]
            try:
                query = """
                    SELECT
                        customer.id,
                        customer.descriptive_name,
                        customer.manager
                    FROM customer
                    LIMIT 1
                """
                response = ga_service.search(customer_id=customer_id, query=query)
                for row in response:
                    accounts.append({
                        "customer_id": str(row.customer.id),
                        "name": row.customer.descriptive_name or f"Account {customer_id}",
                        "is_manager": row.customer.manager,
                    })
                    break
            except GoogleAdsException as ex:
                logger.warning(f"Could not fetch info for customer {customer_id}: {ex.failure.errors[0].message}")

        return accounts

    def get_campaigns(self, refresh_token: str, customer_id: str) -> list[dict]:
        """
        Fetch all active campaigns with today's metrics for a customer.

        Returns list of dicts with id, name, status, type,
        daily_budget_micros, impressions, clicks, conversions, cost_micros.
        """
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.primary_status,
                campaign.primary_status_reasons,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros
            FROM campaign
            WHERE campaign.status != 'REMOVED'
              AND segments.date DURING TODAY
            ORDER BY campaign.id
        """

        campaigns = []
        try:
            response = ga_service.search(customer_id=customer_id_clean, query=query)
            for row in response:
                channel_name = row.campaign.advertising_channel_type.name
                campaigns.append({
                    "id": str(row.campaign.id),
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "primary_status": (
                        row.campaign.primary_status.name
                        if getattr(row.campaign, "primary_status", None) is not None
                        else None
                    ),
                    "primary_status_reasons": [
                        reason.name for reason in getattr(row.campaign, "primary_status_reasons", []) or []
                    ],
                    "type": _CHANNEL_TYPE_MAP.get(channel_name, "SEARCH"),
                    "daily_budget_micros": row.campaign_budget.amount_micros,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "conversions": float(row.metrics.conversions),
                    "cost_micros": row.metrics.cost_micros,
                })
        except GoogleAdsException as ex:
            logger.error(f"Error fetching campaigns for customer {customer_id}")
            for error in ex.failure.errors:
                logger.error(f"  {error.message}")
            raise

        return campaigns

    def get_campaign_metrics_last_30_days(
        self, refresh_token: str, customer_id: str
    ) -> list[dict]:
        """
        Fetch daily metrics for all campaigns over the last 30 days.

        Returns list of dicts with campaign_id, date (YYYY-MM-DD),
        impressions, clicks, conversions, cost_micros.
        """
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                campaign.id,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros
            FROM campaign
            WHERE campaign.status != 'REMOVED'
              AND segments.date DURING LAST_30_DAYS
            ORDER BY campaign.id, segments.date
        """

        rows = []
        try:
            response = ga_service.search(customer_id=customer_id_clean, query=query)
            for row in response:
                rows.append({
                    "campaign_id": str(row.campaign.id),
                    "date": row.segments.date,  # "YYYY-MM-DD" string
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "conversions": float(row.metrics.conversions),
                    "cost_micros": row.metrics.cost_micros,
                })
        except GoogleAdsException as ex:
            logger.error(f"Error fetching metrics for customer {customer_id}")
            for error in ex.failure.errors:
                logger.error(f"  {error.message}")
            raise

        return rows

    def get_keywords(self, refresh_token: str, customer_id: str) -> list[dict]:
        """Fetch enabled keywords for a customer."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                campaign.id,
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.effective_cpc_bid_micros,
                ad_group_criterion.quality_info.quality_score
            FROM keyword_view
            WHERE campaign.status != 'REMOVED'
              AND ad_group_criterion.status != 'REMOVED'
            ORDER BY campaign.id, ad_group_criterion.criterion_id
        """

        rows = []
        try:
            response = ga_service.search(customer_id=customer_id_clean, query=query)
            for row in response:
                match_type_name = row.ad_group_criterion.keyword.match_type.name
                rows.append({
                    "campaign_id": str(row.campaign.id),
                    "keyword_id": str(row.ad_group_criterion.criterion_id),
                    "text": row.ad_group_criterion.keyword.text,
                    "match_type": _MATCH_TYPE_MAP.get(match_type_name, "BROAD"),
                    "bid_micros": row.ad_group_criterion.effective_cpc_bid_micros,
                    "quality_score": row.ad_group_criterion.quality_info.quality_score,
                })
        except GoogleAdsException as ex:
            logger.error(f"Error fetching keywords for customer {customer_id}")
            for error in ex.failure.errors:
                logger.error(f"  {error.message}")
            raise

        return rows

    def get_search_terms(self, refresh_token: str, customer_id: str) -> list[dict]:
        """Fetch search-term performance over the last 30 days."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                campaign.id,
                search_term_view.search_term,
                segments.search_term_match_type,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros
            FROM search_term_view
            WHERE campaign.status != 'REMOVED'
              AND segments.date DURING LAST_30_DAYS
            ORDER BY metrics.clicks DESC
        """

        rows = []
        try:
            response = ga_service.search(customer_id=customer_id_clean, query=query)
            for row in response:
                rows.append({
                    "campaign_id": str(row.campaign.id),
                    "term": row.search_term_view.search_term,
                    "match_type": row.segments.search_term_match_type.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "conversions": float(row.metrics.conversions),
                    "cost_micros": row.metrics.cost_micros,
                })
        except GoogleAdsException as ex:
            logger.error(f"Error fetching search terms for customer {customer_id}")
            for error in ex.failure.errors:
                logger.error(f"  {error.message}")
            raise

        return rows

    def get_best_ad_group_for_campaign(
        self,
        refresh_token: str,
        customer_id: str,
        google_campaign_id: str,
    ) -> dict | None:
        """Return the most suitable active ad group for a campaign."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status
            FROM ad_group
            WHERE campaign.id = {google_campaign_id}
              AND ad_group.status != 'REMOVED'
            ORDER BY ad_group.id
            LIMIT 1
        """

        try:
            response = ga_service.search(customer_id=customer_id_clean, query=query)
            for row in response:
                return {
                    "ad_group_id": str(row.ad_group.id),
                    "ad_group_name": row.ad_group.name,
                    "status": row.ad_group.status.name,
                }
        except GoogleAdsException as ex:
            logger.error(
                "Error finding ad group for campaign %s in customer %s",
                google_campaign_id,
                customer_id,
            )
            for error in ex.failure.errors:
                logger.error("  %s", error.message)
            raise

        return None

    def pause_campaign(
        self, refresh_token: str, customer_id: str, google_campaign_id: str
    ) -> bool:
        """Pause a campaign. Returns True on success."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        campaign_service = client.get_service("CampaignService")

        operation = client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = campaign_service.campaign_path(
            customer_id_clean, google_campaign_id
        )
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        operation.update_mask.paths.append("status")

        try:
            campaign_service.mutate_campaigns(
                customer_id=customer_id_clean, operations=[operation]
            )
            logger.info(f"Campaign {google_campaign_id} paused in account {customer_id}")
            return True
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                logger.error(f"Error pausing campaign {google_campaign_id}: {error.message}")
            return False

    def resume_campaign(
        self, refresh_token: str, customer_id: str, google_campaign_id: str
    ) -> bool:
        """Enable a paused campaign. Returns True on success."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        campaign_service = client.get_service("CampaignService")

        operation = client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = campaign_service.campaign_path(
            customer_id_clean, google_campaign_id
        )
        campaign.status = client.enums.CampaignStatusEnum.ENABLED
        operation.update_mask.paths.append("status")

        try:
            campaign_service.mutate_campaigns(
                customer_id=customer_id_clean, operations=[operation]
            )
            logger.info(f"Campaign {google_campaign_id} enabled in account {customer_id}")
            return True
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                logger.error(f"Error enabling campaign {google_campaign_id}: {error.message}")
            return False

    def update_campaign_budget(
        self,
        refresh_token: str,
        customer_id: str,
        google_campaign_id: str,
        new_daily_budget: float,
    ) -> bool:
        """Update a campaign's daily budget. Returns True on success."""
        from google.ads.googleads.errors import GoogleAdsException

        if new_daily_budget <= 0:
            raise ValueError("New daily budget must be greater than zero")

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        ga_service = client.get_service("GoogleAdsService")
        budget_service = client.get_service("CampaignBudgetService")

        query = f"""
            SELECT
                campaign.campaign_budget,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.id = {google_campaign_id}
            LIMIT 1
        """

        try:
            response = ga_service.search(customer_id=customer_id_clean, query=query)
            budget_resource_name = None
            for row in response:
                budget_resource_name = row.campaign.campaign_budget
                break

            if not budget_resource_name:
                logger.error("No budget resource found for campaign %s", google_campaign_id)
                return False

            operation = client.get_type("CampaignBudgetOperation")
            budget = operation.update
            budget.resource_name = budget_resource_name
            budget.amount_micros = int(round(new_daily_budget * 1_000_000))
            operation.update_mask.paths.append("amount_micros")

            budget_service.mutate_campaign_budgets(
                customer_id=customer_id_clean,
                operations=[operation],
            )
            logger.info(
                "Campaign %s budget updated to %.2f in account %s",
                google_campaign_id,
                new_daily_budget,
                customer_id,
            )
            return True
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                logger.error(
                    "Error updating budget for campaign %s: %s",
                    google_campaign_id,
                    error.message,
                )
            return False

    def add_campaign_negative_keyword(
        self,
        refresh_token: str,
        customer_id: str,
        google_campaign_id: str,
        keyword_text: str,
        match_type: str | None = None,
    ) -> bool:
        """Add a campaign-level negative keyword. Returns True on success."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        client = _build_client(refresh_token, customer_id_clean)
        campaign_service = client.get_service("CampaignService")
        criterion_service = client.get_service("CampaignCriterionService")

        try:
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = campaign_service.campaign_path(
                customer_id_clean,
                google_campaign_id,
            )
            criterion.negative = True
            criterion.status = client.enums.CampaignCriterionStatusEnum.ENABLED
            criterion.keyword.text = keyword_text
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum,
                self._normalize_negative_match_type(match_type),
            )

            criterion_service.mutate_campaign_criteria(
                customer_id=customer_id_clean,
                operations=[operation],
            )
            logger.info(
                "Negative keyword '%s' added to campaign %s in account %s",
                keyword_text,
                google_campaign_id,
                customer_id,
            )
            return True
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                logger.error(
                    "Error adding negative keyword '%s' to campaign %s: %s",
                    keyword_text,
                    google_campaign_id,
                    error.message,
                )
            return False

    def add_keyword_to_best_ad_group(
        self,
        refresh_token: str,
        customer_id: str,
        google_campaign_id: str,
        keyword_text: str,
        match_type: str | None = None,
    ) -> dict | None:
        """Create a positive keyword in the first active ad group of a campaign."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id_clean = customer_id.replace("-", "")
        best_ad_group = self.get_best_ad_group_for_campaign(
            refresh_token=refresh_token,
            customer_id=customer_id_clean,
            google_campaign_id=google_campaign_id,
        )
        if not best_ad_group:
            logger.error(
                "No eligible ad group found for campaign %s in account %s",
                google_campaign_id,
                customer_id,
            )
            return None

        client = _build_client(refresh_token, customer_id_clean)
        criterion_service = client.get_service("AdGroupCriterionService")

        try:
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = (
                f"customers/{customer_id_clean}/adGroups/{best_ad_group['ad_group_id']}"
            )
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = keyword_text
            criterion.keyword.match_type = getattr(
                client.enums.KeywordMatchTypeEnum,
                self._normalize_keyword_match_type(match_type),
            )

            response = criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id_clean,
                operations=[operation],
            )
            resource_name = response.results[0].resource_name if response.results else None
            logger.info(
                "Keyword '%s' added to ad group %s in campaign %s",
                keyword_text,
                best_ad_group["ad_group_id"],
                google_campaign_id,
            )
            return {
                "resource_name": resource_name,
                "ad_group_id": best_ad_group["ad_group_id"],
                "ad_group_name": best_ad_group["ad_group_name"],
                "match_type": self._normalize_keyword_match_type(match_type),
            }
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                logger.error(
                    "Error adding keyword '%s' to campaign %s: %s",
                    keyword_text,
                    google_campaign_id,
                    error.message,
                )
            return None


# Singleton instance
google_ads_wrapper = GoogleAdsClientWrapper()
