"""
Meta Ads Data Collector - Real Implementation
Collects historical campaign performance data from Meta Ads API
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CampaignPerformanceData:
    """Structure for campaign performance metrics"""
    campaign_id: str
    date: datetime
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    ctr: float
    cpc: float
    cpa: float
    roas: float

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate"""
        return self.conversions / self.clicks if self.clicks > 0 else 0.0


class MetaDataCollector:
    """Collects historical performance data from Meta Ads API"""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def fetch_campaign_history(
        self,
        campaign_id: str,
        days_back: int = 90,
        ad_account_id: Optional[str] = None
    ) -> List[CampaignPerformanceData]:
        """
        Fetch historical performance data for a campaign

        Args:
            campaign_id: Meta campaign ID
            days_back: Number of days of historical data to fetch
            ad_account_id: Meta ad account ID (optional)

        Returns:
            List of daily performance data points
        """
        if not self.access_token:
            logger.error("Meta access token not configured")
            return []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Meta Ads API insights endpoint
        url = f"{self.base_url}/{campaign_id}/insights"

        params = {
            "access_token": self.access_token,
            "time_range": {
                "since": start_date.strftime("%Y-%m-%d"),
                "until": end_date.strftime("%Y-%m-%d")
            },
            "time_increment": 1,  # Daily breakdown
            "fields": ",".join([
                "campaign_id",
                "campaign_name",
                "date_start",
                "spend",
                "impressions",
                "clicks",
                "actions",  # Contains conversions
                "action_values",  # Contains revenue
                "ctr",
                "cpc",
                "cpa",
                "purchase_roas"
            ]),
            "level": "campaign",
            "limit": 1000
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                return self._parse_insights_response(data, campaign_id)

        except httpx.HTTPError as e:
            logger.error(f"Error fetching Meta campaign data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in data collection: {e}")
            return []

    def _parse_insights_response(
        self,
        response_data: Dict[str, Any],
        campaign_id: str
    ) -> List[CampaignPerformanceData]:
        """Parse Meta Ads API insights response into structured data"""
        performance_data = []

        if "data" not in response_data:
            logger.warning(f"No data in Meta API response for campaign {campaign_id}")
            return []

        for daily_data in response_data["data"]:
            try:
                # Extract conversion data from actions array
                conversions = 0
                revenue = 0.0

                if "actions" in daily_data:
                    for action in daily_data["actions"]:
                        if action.get("action_type") in ["purchase", "offsite_conversion.fb_pixel_purchase"]:
                            conversions = int(action.get("value", 0))

                if "action_values" in daily_data:
                    for action_value in daily_data["action_values"]:
                        if action_value.get("action_type") in ["purchase", "offsite_conversion.fb_pixel_purchase"]:
                            revenue = float(action_value.get("value", 0))

                spend = float(daily_data.get("spend", 0))
                impressions = int(daily_data.get("impressions", 0))
                clicks = int(daily_data.get("clicks", 0))
                ctr = float(daily_data.get("ctr", 0))
                cpc = float(daily_data.get("cpc", 0))
                cpa = float(daily_data.get("cpa", 0))
                roas = float(daily_data.get("purchase_roas", 0))

                performance_point = CampaignPerformanceData(
                    campaign_id=campaign_id,
                    date=datetime.strptime(daily_data["date_start"], "%Y-%m-%d"),
                    spend=spend,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                    revenue=revenue,
                    ctr=ctr,
                    cpc=cpc,
                    cpa=cpa,
                    roas=roas
                )

                performance_data.append(performance_point)

            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing daily data point: {e}")
                continue

        logger.info(f"Collected {len(performance_data)} days of performance data for campaign {campaign_id}")
        return performance_data

    async def fetch_multiple_campaigns(
        self,
        campaign_ids: List[str],
        days_back: int = 90
    ) -> Dict[str, List[CampaignPerformanceData]]:
        """
        Fetch historical data for multiple campaigns concurrently

        Args:
            campaign_ids: List of Meta campaign IDs
            days_back: Number of days of historical data

        Returns:
            Dictionary mapping campaign_id to performance data list
        """
        tasks = [
            self.fetch_campaign_history(campaign_id, days_back)
            for campaign_id in campaign_ids
        ]

        results = await asyncio.gather(*tasks)

        return {
            campaign_id: data
            for campaign_id, data in zip(campaign_ids, results)
            if data  # Only include campaigns with data
        }

    async def get_active_campaigns(
        self,
        ad_account_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of active campaigns from Meta ad account

        Args:
            ad_account_id: Meta ad account ID (format: act_XXXXXXXXXX)

        Returns:
            List of campaign dictionaries with id, name, status
        """
        if not self.access_token:
            logger.error("Meta access token not configured")
            return []

        url = f"{self.base_url}/{ad_account_id}/campaigns"

        params = {
            "access_token": self.access_token,
            "fields": "id,name,status,objective,daily_budget,lifetime_budget",
            "limit": 100
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                campaigns = data.get("data", [])
                logger.info(f"Found {len(campaigns)} campaigns in account {ad_account_id}")
                return campaigns

        except httpx.HTTPError as e:
            logger.error(f"Error fetching campaigns: {e}")
            return []
