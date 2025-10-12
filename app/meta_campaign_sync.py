"""
Meta Campaign Sync Service
Syncs campaigns and metrics from Meta Ads to local database
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import os
import logging
from datetime import datetime, timedelta
from supabase import create_client, Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meta", tags=["meta-sync"])

# Supabase Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    logger.warning("Supabase not configured")
    supabase = None

class SyncResponse(BaseModel):
    """Response from campaign sync"""
    success: bool
    campaigns_synced: int
    metrics_synced: int
    message: str

def get_user_meta_connection(user_id: str) -> Optional[Dict]:
    """Get user's Meta connection from database"""
    if not supabase:
        return None

    try:
        result = supabase.table("platform_connections")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("platform", "meta")\
            .eq("is_active", True)\
            .execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get Meta connection: {e}")
        return None

def fetch_campaigns_from_meta(access_token: str, ad_account_id: str) -> List[Dict]:
    """
    Fetch campaigns from Meta Ads API

    Docs: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
    """
    try:
        url = f"https://graph.facebook.com/v18.0/{ad_account_id}/campaigns"
        params = {
            "access_token": access_token,
            "fields": "id,name,objective,status,daily_budget,lifetime_budget,created_time,updated_time",
            "limit": 100
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        campaigns = data.get("data", [])

        logger.info(f"Fetched {len(campaigns)} campaigns from Meta")
        return campaigns

    except requests.RequestException as e:
        logger.error(f"Failed to fetch campaigns from Meta: {e}")
        raise HTTPException(status_code=500, detail=f"Meta API error: {str(e)}")

def fetch_campaign_insights(access_token: str, campaign_id: str, days: int = 30) -> List[Dict]:
    """
    Fetch campaign insights (metrics) from Meta

    Docs: https://developers.facebook.com/docs/marketing-api/insights
    """
    try:
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        url = f"https://graph.facebook.com/v18.0/{campaign_id}/insights"
        params = {
            "access_token": access_token,
            "fields": "impressions,clicks,spend,reach,actions,cost_per_action_type",
            "time_range": f"{{'since':'{start_date.isoformat()}','until':'{end_date.isoformat()}'}}",
            "time_increment": 1,  # Daily granularity
            "level": "campaign"
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        insights = data.get("data", [])

        logger.info(f"Fetched {len(insights)} days of insights for campaign {campaign_id}")
        return insights

    except requests.RequestException as e:
        logger.error(f"Failed to fetch insights from Meta: {e}")
        return []

def save_campaign_to_db(user_id: str, meta_campaign: Dict) -> Optional[str]:
    """
    Save or update campaign in local database

    Returns:
        Campaign ID if successful, None otherwise
    """
    if not supabase:
        return None

    try:
        # Check if campaign already exists
        existing = supabase.table("campaigns")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("platform_campaign_id", meta_campaign["id"])\
            .execute()

        # Map Meta status to our status
        status_map = {
            "ACTIVE": "active",
            "PAUSED": "paused",
            "ARCHIVED": "ended",
            "DELETED": "ended"
        }

        campaign_data = {
            "user_id": user_id,
            "name": meta_campaign.get("name"),
            "platform": "meta",
            "platform_campaign_id": meta_campaign["id"],
            "status": status_map.get(meta_campaign.get("status", "").upper(), "active"),
            "objective": meta_campaign.get("objective"),
            "daily_budget": float(meta_campaign.get("daily_budget", 0)) / 100 if meta_campaign.get("daily_budget") else None,  # Meta uses cents
            "budget": float(meta_campaign.get("lifetime_budget", 0)) / 100 if meta_campaign.get("lifetime_budget") else None,
            "updated_at": datetime.now().isoformat()
        }

        if existing.data and len(existing.data) > 0:
            # Update existing
            campaign_id = existing.data[0]["id"]
            supabase.table("campaigns")\
                .update(campaign_data)\
                .eq("id", campaign_id)\
                .execute()

            logger.info(f"Updated campaign {campaign_id}")
            return campaign_id
        else:
            # Insert new
            campaign_data["created_at"] = datetime.now().isoformat()
            result = supabase.table("campaigns")\
                .insert(campaign_data)\
                .execute()

            if result.data:
                campaign_id = result.data[0]["id"]
                logger.info(f"Created new campaign {campaign_id}")
                return campaign_id

        return None

    except Exception as e:
        logger.error(f"Failed to save campaign: {e}")
        return None

def save_metrics_to_db(campaign_id: str, insights: List[Dict]) -> int:
    """
    Save campaign metrics to database

    Returns:
        Number of metrics saved
    """
    if not supabase or not insights:
        return 0

    metrics_saved = 0

    for insight in insights:
        try:
            # Extract conversions from actions array
            conversions = 0
            actions = insight.get("actions", [])
            for action in actions:
                if action.get("action_type") in ["purchase", "lead", "complete_registration"]:
                    conversions += int(action.get("value", 0))

            # Calculate derived metrics
            impressions = int(insight.get("impressions", 0))
            clicks = int(insight.get("clicks", 0))
            spend = float(insight.get("spend", 0))

            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cpc = (spend / clicks) if clicks > 0 else 0
            cpa = (spend / conversions) if conversions > 0 else 0

            metric_data = {
                "campaign_id": campaign_id,
                "date": insight.get("date_start"),
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "spend": spend,
                "ctr": round(ctr, 4),
                "cpc": round(cpc, 2),
                "cpa": round(cpa, 2),
                "platform": "meta",
                "updated_at": datetime.now().isoformat()
            }

            # Upsert (update if exists, insert if not)
            result = supabase.table("campaign_metrics")\
                .upsert(metric_data, on_conflict="campaign_id,date")\
                .execute()

            if result.data:
                metrics_saved += 1

        except Exception as e:
            logger.error(f"Failed to save metric: {e}")
            continue

    logger.info(f"Saved {metrics_saved} metrics for campaign {campaign_id}")
    return metrics_saved

@router.post("/sync-campaigns")
async def sync_meta_campaigns(
    user_id: str = Query(..., description="User ID to sync campaigns for"),
    days: int = Query(30, description="Number of days of metrics to sync")
) -> SyncResponse:
    """
    Sync all Meta campaigns and their metrics for a user

    This endpoint:
    1. Fetches user's Meta connection from database
    2. Fetches all campaigns from Meta API
    3. Saves campaigns to local database
    4. Fetches metrics for each campaign
    5. Saves metrics to local database

    Args:
        user_id: User ID to sync for
        days: Number of days of historical metrics to sync

    Returns:
        Sync summary with counts
    """
    # Get user's Meta connection
    connection = get_user_meta_connection(user_id)

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="Meta not connected. Please authorize Meta first."
        )

    access_token = connection.get("access_token")
    ad_account_id = connection.get("account_id")

    if not access_token or not ad_account_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid Meta connection. Please reconnect."
        )

    # Fetch campaigns from Meta
    meta_campaigns = fetch_campaigns_from_meta(access_token, ad_account_id)

    if not meta_campaigns:
        return SyncResponse(
            success=True,
            campaigns_synced=0,
            metrics_synced=0,
            message="No campaigns found in Meta account"
        )

    # Sync each campaign
    campaigns_synced = 0
    total_metrics_synced = 0

    for meta_campaign in meta_campaigns:
        # Save campaign to database
        campaign_id = save_campaign_to_db(user_id, meta_campaign)

        if campaign_id:
            campaigns_synced += 1

            # Fetch and save metrics
            insights = fetch_campaign_insights(
                access_token,
                meta_campaign["id"],
                days=days
            )

            metrics_synced = save_metrics_to_db(campaign_id, insights)
            total_metrics_synced += metrics_synced

    # Update connection sync status
    if supabase:
        try:
            supabase.table("platform_connections")\
                .update({
                    "last_sync_at": datetime.now().isoformat(),
                    "sync_status": "success"
                })\
                .eq("user_id", user_id)\
                .eq("platform", "meta")\
                .execute()
        except:
            pass

    return SyncResponse(
        success=True,
        campaigns_synced=campaigns_synced,
        metrics_synced=total_metrics_synced,
        message=f"Synced {campaigns_synced} campaigns with {total_metrics_synced} days of metrics"
    )

@router.get("/campaigns/{user_id}")
async def get_synced_campaigns(user_id: str):
    """
    Get all synced Meta campaigns for a user from local database
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        campaigns = supabase.table("campaigns")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("platform", "meta")\
            .order("created_at", desc=True)\
            .execute()

        return {
            "campaigns": campaigns.data if campaigns.data else [],
            "count": len(campaigns.data) if campaigns.data else 0
        }

    except Exception as e:
        logger.error(f"Failed to get campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")
