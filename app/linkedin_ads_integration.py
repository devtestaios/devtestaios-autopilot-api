"""
LinkedIn Ads Integration Module
Provides backend endpoints for LinkedIn Ads integration
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from fastapi import HTTPException

# LinkedIn Ads API Configuration
LINKEDIN_API_BASE = "https://api.linkedin.com/rest"
LINKEDIN_API_VERSION = "202310"

class LinkedInAdsClient:
    def __init__(self, access_token: str, ad_account_id: str):
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.base_url = LINKEDIN_API_BASE
        
    def _make_request(self, endpoint: str, method: str = "GET", params: dict = None, data: dict = None) -> dict:
        """Make authenticated request to LinkedIn Ads API"""
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': LINKEDIN_API_VERSION
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
            raise HTTPException(status_code=500, detail=f"LinkedIn API request failed: {str(e)}")
    
    def test_connection(self) -> dict:
        """Test LinkedIn Ads API connection"""
        try:
            # Test with user info endpoint
            response = self._make_request("people/~:(id,firstName,lastName)")
            
            # Test ad account access
            ad_account_response = self._make_request(
                f"adAccounts/{self.ad_account_id}",
                params={'fields': 'id,name,status,type,currency'}
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
        """Retrieve LinkedIn Ad campaigns"""
        try:
            params = {
                'q': 'search',
                'search': f'(account:(values:List({self.ad_account_id})))',
                'fields': 'id,name,status,type,costType,dailyBudget,totalBudget,runSchedule,createdAt,lastModifiedAt',
                'count': limit
            }
            
            response = self._make_request("adCampaigns", params=params)
            return response.get('elements', [])
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get LinkedIn campaigns: {str(e)}")
    
    def get_campaign_analytics(self, campaign_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get campaign performance analytics"""
        try:
            params = {
                'q': 'analytics',
                'pivot': 'CAMPAIGN',
                'timeGranularity': 'ALL',
                'campaigns': f'List({campaign_id})',
                'fields': 'impressions,clicks,costInUsd,externalWebsiteConversions,externalWebsitePostClickConversions,externalWebsitePostViewConversions',
                'dateRange': f'(start:(year:{start_date[:4]},month:{start_date[5:7]},day:{start_date[8:10]}),end:(year:{end_date[:4]},month:{end_date[5:7]},day:{end_date[8:10]}))'
            }
            
            response = self._make_request("adAnalytics", params=params)
            
            if response.get('elements'):
                return response['elements'][0]
            else:
                return {}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get LinkedIn campaign analytics: {str(e)}")
    
    def get_account_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get account-level performance analytics"""
        try:
            params = {
                'q': 'analytics',
                'pivot': 'ACCOUNT',
                'timeGranularity': 'ALL',
                'accounts': f'List({self.ad_account_id})',
                'fields': 'impressions,clicks,costInUsd,externalWebsiteConversions,externalWebsitePostClickConversions,externalWebsitePostViewConversions',
                'dateRange': f'(start:(year:{start_date[:4]},month:{start_date[5:7]},day:{start_date[8:10]}),end:(year:{end_date[:4]},month:{end_date[5:7]},day:{end_date[8:10]}))'
            }
            
            response = self._make_request("adAnalytics", params=params)
            
            if response.get('elements'):
                return response['elements'][0]
            else:
                return {}
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get LinkedIn account analytics: {str(e)}")

# Initialize client with environment variables
def get_linkedin_client() -> Optional[LinkedInAdsClient]:
    """Get LinkedIn Ads client if credentials are available"""
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    ad_account_id = os.getenv('LINKEDIN_AD_ACCOUNT_ID')
    
    if not access_token or not ad_account_id:
        return None
        
    return LinkedInAdsClient(access_token, ad_account_id)

# FastAPI endpoint functions
async def get_linkedin_ads_status() -> Dict[str, Any]:
    """Check LinkedIn Ads API connection status"""
    client = get_linkedin_client()
    if not client:
        return {
            'connected': False,
            'error': 'LinkedIn Ads credentials not configured'
        }
    
    return client.test_connection()

async def get_linkedin_ads_campaigns(limit: int = 25) -> List[Dict[str, Any]]:
    """Get LinkedIn Ads campaigns"""
    client = get_linkedin_client()
    if not client:
        raise HTTPException(status_code=400, detail="LinkedIn Ads not configured")
    
    return client.get_campaigns(limit)

async def get_linkedin_ads_performance(
    campaign_id: Optional[str] = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """Get LinkedIn Ads performance data"""
    client = get_linkedin_client()
    if not client:
        raise HTTPException(status_code=400, detail="LinkedIn Ads not configured")
    
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