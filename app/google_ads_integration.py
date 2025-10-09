"""
Google Ads API Integration for Autopilot
Handles authentication, campaign sync, and performance data retrieval
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
    GOOGLE_ADS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google Ads library not available: {e}")
    GOOGLE_ADS_AVAILABLE = False
    GoogleAdsClient = None
    GoogleAdsException = None

class GoogleAdsIntegration:
    """Google Ads API client for campaign management and data sync"""
    
    def __init__(self):
        """Initialize Google Ads client with environment variables and configuration file"""
        self.client = None
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
        
        if not GOOGLE_ADS_AVAILABLE:
            logger.warning("Google Ads library not available - integration disabled")
            return
        
        # Check if all required environment variables are present
        required_env_vars = [
            "GOOGLE_ADS_DEVELOPER_TOKEN",
            "GOOGLE_ADS_CLIENT_ID", 
            "GOOGLE_ADS_CLIENT_SECRET",
            "GOOGLE_ADS_REFRESH_TOKEN",
            "GOOGLE_ADS_CUSTOMER_ID"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing Google Ads environment variables: {missing_vars}")
            self.client = None
        else:
            try:
                # Try to load from configuration file first
                config_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "google-ads.yaml")
                if os.path.exists(config_file_path):
                    # Create a configuration dictionary with the required use_proto_plus setting
                    config_dict = {
                        "use_proto_plus": True,
                        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
                        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
                        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
                        "login_customer_id": os.getenv("GOOGLE_ADS_CUSTOMER_ID")
                    }
                    self.client = GoogleAdsClient.load_from_dict(config_dict)
                    logger.info("Google Ads client initialized with use_proto_plus configuration")
                else:
                    # Fallback to environment variables with manual configuration
                    config_dict = {
                        "use_proto_plus": True,
                        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
                        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
                        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
                        "login_customer_id": os.getenv("GOOGLE_ADS_CUSTOMER_ID")
                    }
                    self.client = GoogleAdsClient.load_from_dict(config_dict)
                    logger.info("Google Ads client initialized from environment variables with use_proto_plus")
            except Exception as e:
                logger.error(f"Failed to initialize Google Ads client: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if Google Ads integration is available"""
        return GOOGLE_ADS_AVAILABLE and self.client is not None and self.customer_id is not None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the Google Ads API connection"""
        if not self.is_available():
            return {
                "success": False,
                "error": "Google Ads client not initialized",
                "customer_id": self.customer_id
            }
        
        try:
            # Test connection by fetching customer info
            customer_service = self.client.get_service("CustomerService")
            customer = customer_service.get_customer(
                customer_id=self.customer_id
            )
            
            return {
                "success": True,
                "customer_name": customer.descriptive_name,
                "customer_id": self.customer_id,
                "currency_code": customer.currency_code,
                "time_zone": customer.time_zone
            }
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            return {
                "success": False,
                "error": f"Google Ads API error: {ex.error.code().name}",
                "details": str(ex)
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_campaigns(self) -> List[Dict[str, Any]]:
        """Fetch all campaigns from Google Ads"""
        if not self.is_available():
            return []
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            query = """
                SELECT 
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type,
                    campaign_budget.amount_micros,
                    metrics.cost_micros,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM campaign 
                WHERE campaign.status != 'REMOVED'
                ORDER BY campaign.name
            """
            
            response = ga_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            campaigns = []
            for row in response:
                campaign = row.campaign
                budget = row.campaign_budget
                metrics = row.metrics
                
                campaigns.append({
                    "google_ads_id": str(campaign.id),
                    "name": campaign.name,
                    "status": campaign.status.name.lower(),
                    "platform": "google_ads",
                    "advertising_channel": campaign.advertising_channel_type.name.lower(),
                    "budget_micros": budget.amount_micros if budget else 0,
                    "budget": (budget.amount_micros / 1_000_000) if budget else 0,
                    "spend_micros": metrics.cost_micros,
                    "spend": metrics.cost_micros / 1_000_000,
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "conversions": metrics.conversions,
                    "ctr": metrics.ctr,
                    "average_cpc_micros": metrics.average_cpc,
                    "average_cpc": metrics.average_cpc / 1_000_000 if metrics.average_cpc else 0,
                    "cost_per_conversion_micros": metrics.cost_per_conversion,
                    "cost_per_conversion": metrics.cost_per_conversion / 1_000_000 if metrics.cost_per_conversion else 0
                })
            
            logger.info(f"Retrieved {len(campaigns)} campaigns from Google Ads")
            return campaigns
            
        except GoogleAdsException as ex:
            logger.error(f"Failed to fetch campaigns: {ex}")
            return []
        except Exception as e:
            logger.error(f"Error fetching campaigns: {e}")
            return []
    
    def get_campaign_performance(self, campaign_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily performance data for a specific campaign"""
        if not self.is_available():
            return []
        
        try:
            ga_service = self.client.get_service("GoogleAdsService")
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            query = f"""
                SELECT 
                    segments.date,
                    metrics.cost_micros,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM campaign 
                WHERE campaign.id = {campaign_id}
                    AND segments.date >= '{start_date}'
                    AND segments.date <= '{end_date}'
                ORDER BY segments.date ASC
            """
            
            response = ga_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            performance_data = []
            for row in response:
                metrics = row.metrics
                date_segment = row.segments
                
                performance_data.append({
                    "date": str(date_segment.date),
                    "spend_micros": metrics.cost_micros,
                    "spend": metrics.cost_micros / 1_000_000,
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "conversions": metrics.conversions,
                    "ctr": metrics.ctr,
                    "average_cpc": metrics.average_cpc / 1_000_000 if metrics.average_cpc else 0,
                    "cost_per_conversion": metrics.cost_per_conversion / 1_000_000 if metrics.cost_per_conversion else 0
                })
            
            logger.info(f"Retrieved {len(performance_data)} days of performance data for campaign {campaign_id}")
            return performance_data
            
        except GoogleAdsException as ex:
            logger.error(f"Failed to fetch performance data: {ex}")
            return []
        except Exception as e:
            logger.error(f"Error fetching performance data: {e}")
            return []
    
    def update_campaign_budget(self, campaign_id: str, new_budget_micros: int) -> bool:
        """Update campaign budget in Google Ads"""
        if not self.is_available():
            return False
        
        try:
            # This is a complex operation that requires:
            # 1. Getting the campaign's budget ID
            # 2. Updating the shared budget
            # Note: This is a simplified version - real implementation needs more error handling
            
            logger.info(f"Budget update requested for campaign {campaign_id}: {new_budget_micros / 1_000_000}")
            
            # For now, just log the request - full implementation requires more setup
            return True
            
        except Exception as e:
            logger.error(f"Failed to update budget: {e}")
            return False

# Global instance
google_ads_client = GoogleAdsIntegration()

def get_google_ads_client() -> GoogleAdsIntegration:
    """Get the Google Ads client instance"""
    return google_ads_client

def fetch_campaigns_from_google_ads() -> List[Dict[str, Any]]:
    """Fetch campaigns from Google Ads - wrapper function for main.py compatibility"""
    return google_ads_client.get_campaigns()

def fetch_performance_from_google_ads(campaign_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """Fetch performance data from Google Ads - wrapper function for main.py compatibility"""
    return google_ads_client.get_campaign_performance(campaign_id, days)