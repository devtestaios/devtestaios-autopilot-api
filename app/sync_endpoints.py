"""
FastAPI endpoints for Multi-Platform Campaign Sync
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json

from multi_platform_sync import (
    MultiPlatformSyncEngine,
    GoogleAdsConnector,
    MetaConnector,
    LinkedInConnector,
    UniversalCampaign,
    Platform,
    CampaignStatus,
    SyncStatus,
    SyncResult
)

router = APIRouter(prefix="/api/v1/sync", tags=["multi-platform-sync"])

# Global sync engine instance
sync_engine = MultiPlatformSyncEngine()

# Initialize connectors with mock credentials
google_connector = GoogleAdsConnector({
    "developer_token": "mock_dev_token",
    "client_id": "mock_client_id",
    "client_secret": "mock_secret",
    "refresh_token": "mock_refresh_token"
})

meta_connector = MetaConnector({
    "app_id": "mock_app_id",
    "app_secret": "mock_app_secret",
    "access_token": "mock_access_token"
})

linkedin_connector = LinkedInConnector({
    "client_id": "mock_linkedin_client_id",
    "client_secret": "mock_linkedin_secret",
    "access_token": "mock_linkedin_token"
})

# Add connectors to sync engine
sync_engine.add_connector(google_connector)
sync_engine.add_connector(meta_connector)
sync_engine.add_connector(linkedin_connector)

# Pydantic models for API
class PlatformCredentials(BaseModel):
    platform: str
    credentials: Dict[str, str]

class CampaignCreateRequest(BaseModel):
    name: str
    budget_amount: float
    budget_type: str = "daily"
    bid_strategy: str = "target_cpa"
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    target_platforms: List[str]
    target_audience: Optional[Dict[str, Any]] = {}
    geographic_targeting: Optional[List[str]] = []

class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    platform: str
    budget_amount: float
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    last_sync: Optional[datetime]
    sync_status: str

class SyncResultResponse(BaseModel):
    platform: str
    campaign_id: str
    success: bool
    message: str
    timestamp: datetime

class CrossPlatformPerformanceResponse(BaseModel):
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_spend: float
    total_revenue: float
    platform_breakdown: Dict[str, Any]
    performance_by_platform: Dict[str, Any]

@router.post("/authenticate")
async def authenticate_platforms():
    """Authenticate with all configured platforms"""
    try:
        auth_results = await sync_engine.authenticate_all()
        
        response = {}
        for platform, success in auth_results.items():
            response[platform.value] = {
                "authenticated": success,
                "status": "connected" if success else "failed"
            }
        
        return {
            "success": all(auth_results.values()),
            "platforms": response,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/sync-all", response_model=List[SyncResultResponse])
async def sync_all_campaigns():
    """Synchronize campaigns from all platforms"""
    try:
        sync_results = await sync_engine.sync_all_campaigns()
        
        response = []
        for result in sync_results:
            response.append(SyncResultResponse(
                platform=result.platform.value,
                campaign_id=result.campaign_id,
                success=result.success,
                message=result.message,
                timestamp=result.timestamp
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/campaigns", response_model=List[CampaignResponse])
async def get_all_campaigns(platform: Optional[str] = None):
    """Get all synchronized campaigns, optionally filtered by platform"""
    try:
        campaigns = list(sync_engine.campaigns.values())
        
        if platform:
            try:
                platform_enum = Platform(platform.lower())
                campaigns = [c for c in campaigns if c.platform == platform_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
        
        response = []
        for campaign in campaigns:
            response.append(CampaignResponse(
                id=campaign.id,
                name=campaign.name,
                status=campaign.status.value,
                platform=campaign.platform.value,
                budget_amount=campaign.budget_amount,
                impressions=campaign.impressions,
                clicks=campaign.clicks,
                conversions=campaign.conversions,
                spend=campaign.spend,
                revenue=campaign.revenue,
                last_sync=campaign.last_sync,
                sync_status=campaign.sync_status.value
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get campaigns: {str(e)}")

@router.post("/campaigns/create-cross-platform", response_model=List[SyncResultResponse])
async def create_cross_platform_campaign(request: CampaignCreateRequest):
    """Create a campaign across multiple platforms"""
    try:
        # Convert platform strings to enums
        target_platforms = []
        for platform_str in request.target_platforms:
            try:
                platform_enum = Platform(platform_str.lower())
                target_platforms.append(platform_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform_str}")
        
        # Create universal campaign template
        campaign_template = UniversalCampaign(
            id=f"cross_platform_{int(datetime.utcnow().timestamp())}",
            name=request.name,
            status=CampaignStatus.ACTIVE,
            platform=target_platforms[0],  # Will be adapted for each platform
            budget_amount=request.budget_amount,
            budget_type=request.budget_type,
            bid_strategy=request.bid_strategy,
            target_cpa=request.target_cpa,
            target_roas=request.target_roas,
            target_audience=request.target_audience or {},
            geographic_targeting=request.geographic_targeting or []
        )
        
        # Create campaigns across platforms
        creation_results = await sync_engine.create_cross_platform_campaign(
            campaign_template, 
            target_platforms
        )
        
        response = []
        for result in creation_results:
            response.append(SyncResultResponse(
                platform=result.platform.value,
                campaign_id=result.campaign_id,
                success=result.success,
                message=result.message,
                timestamp=result.timestamp
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")

@router.get("/performance/cross-platform", response_model=CrossPlatformPerformanceResponse)
async def get_cross_platform_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get aggregated performance data across all platforms"""
    try:
        # Default to last 30 days if no date range provided
        if not start_date or not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        date_range = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        performance_data = await sync_engine.get_cross_platform_performance(date_range)
        
        return CrossPlatformPerformanceResponse(**performance_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance data: {str(e)}")

@router.get("/status")
async def get_sync_status():
    """Get current synchronization status across all platforms"""
    try:
        status = sync_engine.get_sync_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@router.post("/campaigns/{campaign_id}/sync")
async def sync_single_campaign(campaign_id: str):
    """Manually sync a specific campaign"""
    try:
        if campaign_id not in sync_engine.campaigns:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = sync_engine.campaigns[campaign_id]
        connector = sync_engine.connectors.get(campaign.platform)
        
        if not connector:
            raise HTTPException(status_code=400, detail=f"No connector for platform {campaign.platform.value}")
        
        # Fetch fresh performance data
        date_range = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": datetime.utcnow().strftime("%Y-%m-%d")
        }
        
        performance_data = await connector.fetch_performance_data(campaign_id, date_range)
        
        # Update campaign with fresh data
        campaign.impressions = performance_data.get("impressions", campaign.impressions)
        campaign.clicks = performance_data.get("clicks", campaign.clicks)
        campaign.conversions = performance_data.get("conversions", campaign.conversions)
        campaign.spend = performance_data.get("spend", campaign.spend)
        campaign.revenue = performance_data.get("revenue", campaign.revenue)
        campaign.last_sync = datetime.utcnow()
        campaign.sync_status = SyncStatus.SYNCED
        
        return {
            "success": True,
            "message": f"Campaign {campaign_id} synced successfully",
            "updated_data": performance_data,
            "last_sync": campaign.last_sync
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/campaigns/{campaign_id}/performance-history")
async def get_campaign_performance_history(
    campaign_id: str,
    days: int = 30
):
    """Get performance history for a specific campaign"""
    try:
        if campaign_id not in sync_engine.campaigns:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = sync_engine.campaigns[campaign_id]
        connector = sync_engine.connectors.get(campaign.platform)
        
        if not connector:
            raise HTTPException(status_code=400, detail=f"No connector for platform {campaign.platform.value}")
        
        # Generate mock historical data
        history = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            
            # Mock daily performance with some variation
            base_performance = {
                "date": date.strftime("%Y-%m-%d"),
                "impressions": int(campaign.impressions / days * (0.8 + 0.4 * (i % 10) / 10)),
                "clicks": int(campaign.clicks / days * (0.8 + 0.4 * (i % 10) / 10)),
                "conversions": int(campaign.conversions / days * (0.8 + 0.4 * (i % 10) / 10)),
                "spend": round(campaign.spend / days * (0.8 + 0.4 * (i % 10) / 10), 2),
                "revenue": round(campaign.revenue / days * (0.8 + 0.4 * (i % 10) / 10), 2)
            }
            
            # Calculate derived metrics
            if base_performance["impressions"] > 0:
                base_performance["ctr"] = round((base_performance["clicks"] / base_performance["impressions"]) * 100, 2)
            if base_performance["clicks"] > 0:
                base_performance["cpc"] = round(base_performance["spend"] / base_performance["clicks"], 2)
            if base_performance["conversions"] > 0:
                base_performance["cpa"] = round(base_performance["spend"] / base_performance["conversions"], 2)
            if base_performance["spend"] > 0:
                base_performance["roas"] = round(base_performance["revenue"] / base_performance["spend"], 2)
            
            history.append(base_performance)
        
        return {
            "campaign_id": campaign_id,
            "platform": campaign.platform.value,
            "performance_history": list(reversed(history))  # Chronological order
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance history: {str(e)}")

@router.post("/platforms/{platform}/test-connection")
async def test_platform_connection(platform: str):
    """Test connection to a specific platform"""
    try:
        platform_enum = Platform(platform.lower())
        connector = sync_engine.connectors.get(platform_enum)
        
        if not connector:
            raise HTTPException(status_code=400, detail=f"No connector configured for {platform}")
        
        # Test authentication
        auth_success = await connector.authenticate()
        
        if auth_success:
            # Try to fetch a small amount of data
            campaigns = await connector.fetch_campaigns()
            
            return {
                "platform": platform,
                "connected": True,
                "message": f"Successfully connected to {platform}",
                "campaigns_found": len(campaigns),
                "test_timestamp": datetime.utcnow()
            }
        else:
            return {
                "platform": platform,
                "connected": False,
                "message": f"Failed to authenticate with {platform}",
                "test_timestamp": datetime.utcnow()
            }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

# Health check endpoint
@router.get("/health")
async def sync_engine_health():
    """Check multi-platform sync engine health"""
    platform_health = {}
    
    for platform, connector in sync_engine.connectors.items():
        platform_health[platform.value] = {
            "connected": connector.connected,
            "campaigns_synced": len([c for c in sync_engine.campaigns.values() if c.platform == platform])
        }
    
    return {
        "status": "healthy",
        "sync_engine_version": "1.0.0",
        "platforms": platform_health,
        "total_campaigns": len(sync_engine.campaigns),
        "last_sync_check": datetime.utcnow(),
        "capabilities": [
            "cross_platform_sync",
            "unified_campaign_management",
            "performance_aggregation",
            "real_time_monitoring"
        ]
    }