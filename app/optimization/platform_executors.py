"""
Platform Executors for Optimization Engine
Connects optimization recommendations to Meta and Google Ads APIs
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetaAdsExecutor:
    """
    Execute optimization recommendations via Meta Ads API
    Uses existing MetaBusinessAPI client
    """

    def __init__(self, meta_client):
        """
        Initialize Meta executor

        Args:
            meta_client: Instance of MetaBusinessAPI
        """
        self.client = meta_client
        self.ad_account_id = meta_client.ad_account_id

    async def update_campaign_budget(
        self,
        campaign_id: str,
        new_daily_budget: float,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Update campaign daily budget

        Args:
            campaign_id: Meta campaign ID
            new_daily_budget: New daily budget in cents (Meta requires cents)
            dry_run: If True, simulate without making changes

        Returns:
            Result with success status
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would update campaign {campaign_id} budget to ${new_daily_budget/100:.2f}/day")
            return {
                "success": True,
                "status": "simulated",
                "campaign_id": campaign_id,
                "new_daily_budget": new_daily_budget / 100,
                "message": "[DRY RUN] Budget update simulated"
            }

        try:
            # Convert dollars to cents for Meta API
            budget_cents = int(new_daily_budget * 100)

            # Update campaign via Meta API
            endpoint = f"{campaign_id}"
            data = {
                "daily_budget": budget_cents
            }

            result = self.client._make_request('POST', endpoint, data=data)

            logger.info(f"✅ Updated Meta campaign {campaign_id} budget to ${new_daily_budget:.2f}/day")

            return {
                "success": True,
                "status": "executed",
                "campaign_id": campaign_id,
                "new_daily_budget": new_daily_budget,
                "meta_response": result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to update Meta campaign budget: {e}")
            return {
                "success": False,
                "status": "error",
                "campaign_id": campaign_id,
                "error": str(e)
            }

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Update campaign status (ACTIVE, PAUSED, ARCHIVED)

        Args:
            campaign_id: Meta campaign ID
            status: New status (ACTIVE, PAUSED, ARCHIVED)
            dry_run: If True, simulate

        Returns:
            Result with success status
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would update campaign {campaign_id} status to {status}")
            return {
                "success": True,
                "status": "simulated",
                "campaign_id": campaign_id,
                "new_status": status,
                "message": "[DRY RUN] Status update simulated"
            }

        try:
            endpoint = f"{campaign_id}"
            data = {"status": status}

            result = self.client._make_request('POST', endpoint, data=data)

            logger.info(f"✅ Updated Meta campaign {campaign_id} status to {status}")

            return {
                "success": True,
                "status": "executed",
                "campaign_id": campaign_id,
                "new_status": status,
                "meta_response": result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to update Meta campaign status: {e}")
            return {
                "success": False,
                "status": "error",
                "campaign_id": campaign_id,
                "error": str(e)
            }

    async def update_adset_bid(
        self,
        adset_id: str,
        new_bid: float,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Update ad set bid amount

        Args:
            adset_id: Meta ad set ID
            new_bid: New bid amount in dollars
            dry_run: If True, simulate

        Returns:
            Result with success status
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would update ad set {adset_id} bid to ${new_bid:.2f}")
            return {
                "success": True,
                "status": "simulated",
                "adset_id": adset_id,
                "new_bid": new_bid,
                "message": "[DRY RUN] Bid update simulated"
            }

        try:
            # Convert dollars to cents
            bid_cents = int(new_bid * 100)

            endpoint = f"{adset_id}"
            data = {
                "bid_amount": bid_cents
            }

            result = self.client._make_request('POST', endpoint, data=data)

            logger.info(f"✅ Updated Meta ad set {adset_id} bid to ${new_bid:.2f}")

            return {
                "success": True,
                "status": "executed",
                "adset_id": adset_id,
                "new_bid": new_bid,
                "meta_response": result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to update Meta ad set bid: {e}")
            return {
                "success": False,
                "status": "error",
                "adset_id": adset_id,
                "error": str(e)
            }

    async def get_campaign_performance(
        self,
        campaign_id: str,
        date_range: str = "last_7d"
    ) -> Dict[str, Any]:
        """
        Get campaign performance metrics

        Args:
            campaign_id: Meta campaign ID
            date_range: Date range (last_7d, last_30d, etc.)

        Returns:
            Performance metrics
        """
        try:
            params = {
                "fields": "impressions,clicks,spend,actions,action_values",
                "date_preset": date_range
            }

            endpoint = f"{campaign_id}/insights"
            result = self.client._make_request('GET', endpoint, params=params)

            insights = result.get('data', [])

            if insights:
                data = insights[0]

                # Extract conversions and revenue
                conversions = 0
                revenue = 0.0

                actions = data.get('actions', [])
                for action in actions:
                    if action['action_type'] == 'purchase':
                        conversions = int(action['value'])

                action_values = data.get('action_values', [])
                for value in action_values:
                    if value['action_type'] == 'purchase':
                        revenue = float(value['value'])

                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "impressions": int(data.get('impressions', 0)),
                    "clicks": int(data.get('clicks', 0)),
                    "spend": float(data.get('spend', 0)),
                    "conversions": conversions,
                    "revenue": revenue,
                    "date_range": date_range
                }
            else:
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": "No insights data available"
                }

        except Exception as e:
            logger.error(f"❌ Failed to get Meta campaign performance: {e}")
            return {
                "success": False,
                "campaign_id": campaign_id,
                "error": str(e)
            }


class GoogleAdsExecutor:
    """
    Execute optimization recommendations via Google Ads API
    Uses existing GoogleAdsIntegration client
    """

    def __init__(self, google_client):
        """
        Initialize Google Ads executor

        Args:
            google_client: Instance of GoogleAdsIntegration
        """
        self.client = google_client
        self.customer_id = google_client.customer_id

    async def update_campaign_budget(
        self,
        campaign_id: str,
        new_daily_budget: float,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Update campaign daily budget

        Args:
            campaign_id: Google Ads campaign ID
            new_daily_budget: New daily budget in dollars (micro-dollars for API)
            dry_run: If True, simulate

        Returns:
            Result with success status
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would update Google campaign {campaign_id} budget to ${new_daily_budget:.2f}/day")
            return {
                "success": True,
                "status": "simulated",
                "campaign_id": campaign_id,
                "new_daily_budget": new_daily_budget,
                "message": "[DRY RUN] Budget update simulated"
            }

        if not self.client.is_available():
            return {
                "success": False,
                "status": "unavailable",
                "message": "Google Ads client not available"
            }

        try:
            # Google Ads uses micro-dollars (1 dollar = 1,000,000 micro-dollars)
            budget_micros = int(new_daily_budget * 1_000_000)

            # Get campaign budget ID first
            campaign_service = self.client.client.get_service("CampaignService")
            ga_service = self.client.client.get_service("GoogleAdsService")

            query = f"""
                SELECT campaign.id, campaign.campaign_budget
                FROM campaign
                WHERE campaign.id = {campaign_id}
            """

            response = ga_service.search(customer_id=self.customer_id, query=query)

            campaign_budget_resource = None
            for row in response:
                campaign_budget_resource = row.campaign.campaign_budget
                break

            if not campaign_budget_resource:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Campaign budget not found"
                }

            # Update the campaign budget
            campaign_budget_service = self.client.client.get_service("CampaignBudgetService")

            campaign_budget_operation = self.client.client.get_type("CampaignBudgetOperation")
            campaign_budget = campaign_budget_operation.update
            campaign_budget.resource_name = campaign_budget_resource
            campaign_budget.amount_micros = budget_micros

            campaign_budget_operation.update_mask.paths.append("amount_micros")

            response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id,
                operations=[campaign_budget_operation]
            )

            logger.info(f"✅ Updated Google campaign {campaign_id} budget to ${new_daily_budget:.2f}/day")

            return {
                "success": True,
                "status": "executed",
                "campaign_id": campaign_id,
                "new_daily_budget": new_daily_budget,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to update Google campaign budget: {e}")
            return {
                "success": False,
                "status": "error",
                "campaign_id": campaign_id,
                "error": str(e)
            }

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Update campaign status (ENABLED, PAUSED, REMOVED)

        Args:
            campaign_id: Google Ads campaign ID
            status: New status (ENABLED, PAUSED, REMOVED)
            dry_run: If True, simulate

        Returns:
            Result with success status
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would update Google campaign {campaign_id} status to {status}")
            return {
                "success": True,
                "status": "simulated",
                "campaign_id": campaign_id,
                "new_status": status,
                "message": "[DRY RUN] Status update simulated"
            }

        if not self.client.is_available():
            return {
                "success": False,
                "status": "unavailable",
                "message": "Google Ads client not available"
            }

        try:
            campaign_service = self.client.client.get_service("CampaignService")

            campaign_operation = self.client.client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            campaign.resource_name = campaign_service.campaign_path(self.customer_id, campaign_id)
            campaign.status = getattr(
                self.client.client.enums.CampaignStatusEnum.CampaignStatus,
                status
            )

            campaign_operation.update_mask.paths.append("status")

            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )

            logger.info(f"✅ Updated Google campaign {campaign_id} status to {status}")

            return {
                "success": True,
                "status": "executed",
                "campaign_id": campaign_id,
                "new_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to update Google campaign status: {e}")
            return {
                "success": False,
                "status": "error",
                "campaign_id": campaign_id,
                "error": str(e)
            }

    async def get_campaign_performance(
        self,
        campaign_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get campaign performance metrics

        Args:
            campaign_id: Google Ads campaign ID
            days: Number of days to look back

        Returns:
            Performance metrics
        """
        if not self.client.is_available():
            return {
                "success": False,
                "message": "Google Ads client not available"
            }

        try:
            ga_service = self.client.client.get_service("GoogleAdsService")

            query = f"""
                SELECT
                    campaign.id,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value
                FROM campaign
                WHERE campaign.id = {campaign_id}
                AND segments.date DURING LAST_{days}_DAYS
            """

            response = ga_service.search(customer_id=self.customer_id, query=query)

            impressions = 0
            clicks = 0
            cost_micros = 0
            conversions = 0
            conversions_value = 0

            for row in response:
                impressions += row.metrics.impressions
                clicks += row.metrics.clicks
                cost_micros += row.metrics.cost_micros
                conversions += row.metrics.conversions
                conversions_value += row.metrics.conversions_value

            return {
                "success": True,
                "campaign_id": campaign_id,
                "impressions": impressions,
                "clicks": clicks,
                "spend": cost_micros / 1_000_000,  # Convert from micro-dollars
                "conversions": int(conversions),
                "revenue": conversions_value,
                "days": days
            }

        except Exception as e:
            logger.error(f"❌ Failed to get Google campaign performance: {e}")
            return {
                "success": False,
                "campaign_id": campaign_id,
                "error": str(e)
            }


class PlatformExecutorFactory:
    """
    Factory to create appropriate platform executor
    """

    @staticmethod
    def create_executor(platform: str, client: Any) -> Optional[Any]:
        """
        Create platform executor

        Args:
            platform: Platform name (meta, google, linkedin, etc.)
            client: Platform API client instance

        Returns:
            Platform executor instance or None
        """
        platform_lower = platform.lower()

        if platform_lower in ["meta", "facebook", "instagram"]:
            return MetaAdsExecutor(client)
        elif platform_lower in ["google", "google_ads", "google_search"]:
            return GoogleAdsExecutor(client)
        else:
            logger.warning(f"No executor available for platform: {platform}")
            return None
