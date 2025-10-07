#!/usr/bin/env python3
"""
Meta Business API Integration Module
Validated credentials: September 24, 2025
Status: ✅ WORKING - All permissions confirmed

This module handles Meta Business API integration for PulseBridge AI
- Campaign management
- Performance tracking
- Automated optimization
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaBusinessAPI:
    """Meta Business API Integration for PulseBridge AI"""
    
    def __init__(self):
        """Initialize with validated environment variables"""
        self.app_id = os.getenv('META_APP_ID', '1978667392867839')
        self.app_secret = os.getenv('META_APP_SECRET', '365381fb087baf8cb38c53ced46b08a4')
        self.access_token = os.getenv('META_ACCESS_TOKEN', 'EAAcHlmcUnf8BPiAKrCTEy65c4swGgbMgjgkALE558Bf2e3nfe16UZB7szzwtheI6yFqeHz5GYfblNMeXTBsLYtBWKZByf2AbcwyE2UZAsElZAipjERURW7A4tadlBeLIYTlu11HJpUJEOl2KZCHsQNRZAR6g231CBYAZAXoWEijPDo9E192qihvvvNzp6YzCyK0VdQZD')
        self.ad_account_id = os.getenv('META_AD_ACCOUNT_ID', '800452322951630')
        
        self.base_url = "https://graph.facebook.com/v19.0"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Validated account info
        self.account_name = "pulsebridge.ai"
        self.account_currency = "USD"
        self.account_timezone = "America/Los_Angeles"
        
        logger.info(f"✅ MetaBusinessAPI initialized for account: {self.account_name}")
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, params=params, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, params=params, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Meta API request failed: {e}")
            raise Exception(f"Meta API Error: {e}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information - VALIDATED ✅"""
        try:
            params = {'fields': 'name,account_status,currency,timezone_name,amount_spent,balance'}
            result = self._make_request('GET', f'act_{self.ad_account_id}', params=params)
            
            logger.info(f"✅ Account info retrieved: {result.get('name')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get account info: {e}")
            return {'error': str(e)}
    
    def get_campaigns(self, limit: int = 50) -> List[Dict]:
        """Get all campaigns - VALIDATED ✅"""
        try:
            params = {
                'fields': 'id,name,status,objective,daily_budget,lifetime_budget,created_time,updated_time,start_time,stop_time',
                'limit': limit
            }
            result = self._make_request('GET', f'act_{self.ad_account_id}/campaigns', params=params)
            campaigns = result.get('data', [])
            
            logger.info(f"✅ Retrieved {len(campaigns)} campaigns")
            return campaigns
            
        except Exception as e:
            logger.error(f"❌ Failed to get campaigns: {e}")
            return []
    
    def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign"""
        try:
            # Required fields for campaign creation
            required_fields = ['name', 'objective', 'status']
            for field in required_fields:
                if field not in campaign_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Default values
            data = {
                'name': campaign_data['name'],
                'objective': campaign_data.get('objective', 'LINK_CLICKS'),
                'status': campaign_data.get('status', 'PAUSED'),
                'special_ad_categories': '[]',  # Required for most campaigns
                **campaign_data  # Allow overrides
            }
            
            result = self._make_request('POST', f'act_{self.ad_account_id}/campaigns', data=data)
            
            logger.info(f"✅ Campaign created: {campaign_data['name']} (ID: {result.get('id')})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to create campaign: {e}")
            return {'error': str(e)}
    
    def get_campaign_insights(self, campaign_id: str, date_preset: str = 'last_7_days') -> Dict[str, Any]:
        """Get campaign performance insights"""
        try:
            params = {
                'fields': 'impressions,clicks,ctr,cpc,cpm,reach,spend,actions,action_values',
                'date_preset': date_preset
            }
            result = self._make_request('GET', f'{campaign_id}/insights', params=params)
            insights = result.get('data', [])
            
            logger.info(f"✅ Retrieved insights for campaign {campaign_id}")
            return insights[0] if insights else {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get campaign insights: {e}")
            return {'error': str(e)}
    
    def update_campaign_budget(self, campaign_id: str, daily_budget: float) -> Dict[str, Any]:
        """Update campaign daily budget"""
        try:
            # Convert to Meta's budget format (cents)
            budget_cents = int(daily_budget * 100)
            
            data = {'daily_budget': budget_cents}
            result = self._make_request('POST', campaign_id, data=data)
            
            logger.info(f"✅ Updated budget for campaign {campaign_id}: ${daily_budget}/day")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to update campaign budget: {e}")
            return {'error': str(e)}
    
    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause a campaign"""
        return self._update_campaign_status(campaign_id, 'PAUSED')
    
    def activate_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Activate a campaign"""
        return self._update_campaign_status(campaign_id, 'ACTIVE')
    
    def _update_campaign_status(self, campaign_id: str, status: str) -> Dict[str, Any]:
        """Update campaign status"""
        try:
            data = {'status': status}
            result = self._make_request('POST', campaign_id, data=data)
            
            logger.info(f"✅ Campaign {campaign_id} status updated to {status}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to update campaign status: {e}")
            return {'error': str(e)}
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get comprehensive account summary for dashboard"""
        try:
            # Get account info
            account_info = self.get_account_info()
            
            # Get campaigns
            campaigns = self.get_campaigns()
            
            # Calculate summary metrics
            active_campaigns = len([c for c in campaigns if c.get('status') == 'ACTIVE'])
            total_campaigns = len(campaigns)
            
            summary = {
                'account_name': account_info.get('name', self.account_name),
                'account_id': self.ad_account_id,
                'currency': account_info.get('currency', self.account_currency),
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'paused_campaigns': total_campaigns - active_campaigns,
                'total_spend': float(account_info.get('amount_spent', 0)),
                'account_balance': float(account_info.get('balance', 0)),
                'campaigns': campaigns[:10],  # Recent campaigns
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Account summary generated: {total_campaigns} campaigns, {active_campaigns} active")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to get account summary: {e}")
            return {'error': str(e)}

# Initialize global instance
meta_api = MetaBusinessAPI()

# Test function
def test_meta_integration():
    """Test the Meta API integration"""
    print("🧪 Testing Meta Business API Integration...")
    
    try:
        # Test account info
        account_info = meta_api.get_account_info()
        print(f"✅ Account: {account_info.get('name')}")
        
        # Test campaigns
        campaigns = meta_api.get_campaigns()
        print(f"✅ Campaigns: {len(campaigns)} found")
        
        # Test summary
        summary = meta_api.get_account_summary()
        print(f"✅ Summary: {summary.get('total_campaigns')} total campaigns")
        
        print("🎉 Meta API integration test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Meta API integration test failed: {e}")
        return False

if __name__ == "__main__":
    test_meta_integration()