"""
Pinterest Ads Integration Module
Provides backend endpoints for Pinterest Ads integration
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from fastapi import HTTPException

# Pinterest Ads API Configuration
PINTEREST_API_BASE = "https://api.pinterest.com/v5"
PINTEREST_API_VERSION = "v5"

class PinterestAdsClient:
    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.base_url = PINTEREST_API_BASE
        
    def _make_request(self, endpoint: str, method: str = "GET", params: dict = None, data: dict = None) -> dict:
        """Make authenticated request to Pinterest Ads API"""
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, params=params, json=data, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, params=params, json=data, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, params=params, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Pinterest API request failed: {str(e)}")
    
    def test_connection(self) -> dict:
        """Test Pinterest Ads API connection"""
        try:
            # Test with user info endpoint
            response = self._make_request("user_account", params={'fields': 'id,username'})
            
            # Test ad account access
            ad_account_response = self._make_request(
                f"ad_accounts/{self.ad_account_id}",
                params={'fields': 'id,name,country,currency'}
            )
            
            return {
                'connected': True,
                'user': response,
                'ad_account': ad_account_response
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def get_campaigns(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieve Pinterest Ad campaigns"""
        try:
            params = {
                'entity_statuses': 'ACTIVE,PAUSED,ARCHIVED',
                'limit': limit
            }
            
            response = self._make_request(f"ad_accounts/{self.ad_account_id}/campaigns", params=params)
            return response.get('items', [])
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get Pinterest campaigns: {str(e)}")
    
    def get_campaign_analytics(self, campaign_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get campaign performance analytics"""
        try:
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'granularity': 'DAY',
                'columns': 'IMPRESSION,CLICKTHROUGH,SPEND,PIN_CLICK,OUTBOUND_CLICK,SAVE,TOTAL_CONVERSIONS,TOTAL_CONVERSION_VALUE',
                'campaign_ids': campaign_id
            }
            
            response = self._make_request("ad_accounts/{}/campaigns/analytics".format(self.ad_account_id), params=params)
            
            if response.get('items'):
                # Aggregate daily metrics
                aggregated = {
                    'impressions': 0,
                    'clicks': 0,
                    'spend': 0,
                    'pin_clicks': 0,
                    'outbound_clicks': 0,
                    'saves': 0,
                    'conversions': 0,
                    'conversion_value': 0
                }
                
                for item in response['items']:
                    aggregated['impressions'] += item.get('IMPRESSION', 0)
                    aggregated['clicks'] += item.get('CLICKTHROUGH', 0)
                    aggregated['spend'] += item.get('SPEND', 0)
                    aggregated['pin_clicks'] += item.get('PIN_CLICK', 0)
                    aggregated['outbound_clicks'] += item.get('OUTBOUND_CLICK', 0)
                    aggregated['saves'] += item.get('SAVE', 0)
                    aggregated['conversions'] += item.get('TOTAL_CONVERSIONS', 0)
                    aggregated['conversion_value'] += item.get('TOTAL_CONVERSION_VALUE', 0)
                
                return aggregated
            else:
                return {}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get Pinterest campaign analytics: {str(e)}")
    
    def get_account_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get account-level performance analytics"""
        try:
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'granularity': 'DAY',
                'columns': 'IMPRESSION,CLICKTHROUGH,SPEND,PIN_CLICK,OUTBOUND_CLICK,SAVE,TOTAL_CONVERSIONS,TOTAL_CONVERSION_VALUE'
            }
            
            response = self._make_request(f"ad_accounts/{self.ad_account_id}/analytics", params=params)
            
            if response.get('items'):
                # Aggregate daily metrics
                aggregated = {
                    'impressions': 0,
                    'clicks': 0,
                    'spend': 0,
                    'pin_clicks': 0,
                    'outbound_clicks': 0,
                    'saves': 0,
                    'conversions': 0,
                    'conversion_value': 0
                }
                
                for item in response['items']:
                    aggregated['impressions'] += item.get('IMPRESSION', 0)
                    aggregated['clicks'] += item.get('CLICKTHROUGH', 0)
                    aggregated['spend'] += item.get('SPEND', 0)
                    aggregated['pin_clicks'] += item.get('PIN_CLICK', 0)
                    aggregated['outbound_clicks'] += item.get('OUTBOUND_CLICK', 0)
                    aggregated['saves'] += item.get('SAVE', 0)
                    aggregated['conversions'] += item.get('TOTAL_CONVERSIONS', 0)
                    aggregated['conversion_value'] += item.get('TOTAL_CONVERSION_VALUE', 0)
                
                return aggregated
            else:
                return {}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get Pinterest account analytics: {str(e)}")

# Initialize client with environment variables
def get_pinterest_client() -> Optional[PinterestAdsClient]:
    """Get Pinterest Ads client if credentials are available"""
    access_token = os.getenv('PINTEREST_ACCESS_TOKEN')
    ad_account_id = os.getenv('PINTEREST_AD_ACCOUNT_ID')
    
    if not access_token or not ad_account_id:
        return None
        
    return PinterestAdsClient(access_token, ad_account_id)

# FastAPI endpoint functions
async def get_pinterest_ads_status() -> Dict[str, Any]:
    """Check Pinterest Ads API connection status"""
    client = get_pinterest_client()
    if not client:
        return {
            'connected': False,
            'error': 'Pinterest Ads credentials not configured'
        }
    
    return client.test_connection()

async def get_pinterest_ads_campaigns(limit: int = 25) -> List[Dict[str, Any]]:
    """Get Pinterest Ads campaigns"""
    client = get_pinterest_client()
    if not client:
        raise HTTPException(status_code=400, detail="Pinterest Ads not configured")
    
    return client.get_campaigns(limit)

async def get_pinterest_ads_performance(
    campaign_id: Optional[str] = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """Get Pinterest Ads performance data"""
    client = get_pinterest_client()
    if not client:
        raise HTTPException(status_code=400, detail="Pinterest Ads not configured")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    if campaign_id:
        # Get specific campaign performance
        return client.get_campaign_analytics(campaign_id, start_date_str, end_date_str)
    else:
        # Get account-level performance
        return client.get_account_analytics(start_date_str, end_date_str)