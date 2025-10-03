
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime, timedelta, timezone

# Google Ads Integration
try:
    from google_ads_integration import get_google_ads_client
    google_ads_available = True
except ImportError:
    google_ads_available = False
    get_google_ads_client = None


# ---------- Env & Supabase ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client, Client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    # Keep supabase = None so routes can return a helpful error
    supabase = None


# ---------- App + CORS ----------
app = FastAPI(title="Autopilot API", version="0.1.0")

# Allow *.vercel.app and your pretty domain
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_origins=["https://ai-marketing-autopilot.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Models ----------
class LeadIn(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = None


# ---------- Campaign Models ----------
class CampaignIn(BaseModel):
    name: str
    platform: str
    client_name: str
    budget: Optional[float] = None
    spend: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None

class CampaignOut(CampaignIn):
    id: str
    created_at: Optional[str] = None


# ---------- Performance Snapshot Models ----------
class PerformanceSnapshotIn(BaseModel):
    snapshot_date: str  # ISO date string, e.g. "2025-09-15"
    metrics: Dict[str, Any]

class PerformanceSnapshotOut(PerformanceSnapshotIn):
    id: str
    campaign_id: str
    created_at: Optional[str] = None


# ---------- Utility ----------
def _iso(dt: datetime) -> str:
    # Return UTC ISO string
    return dt.astimezone(timezone.utc).isoformat()

def _today_utc() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


# ---------- Basic routes ----------
@app.get("/")
def root():
    return {"message": "Welcome to Autopilot API"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": "0.1.0"}

@app.get("/_routes")
def routes():
    return {"routes": [r.path for r in app.routes]}

@app.get("/env-check")
def env_check():
    return {
        "SUPABASE_URL_present": bool(SUPABASE_URL),
        "SUPABASE_ANON_KEY_present": bool(SUPABASE_KEY),
    }

@app.get("/test-db")
async def test_db():
    """
    Checks Supabase reachability via auth settings endpoint.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"ok": False, "error": "Missing Supabase envs on server"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{SUPABASE_URL}/auth/v1/settings",
            headers={"apikey": SUPABASE_KEY},
        )
        return {"ok": r.status_code == 200, "status": r.status_code, "url": str(r.url)}


# ---------- Leads API ----------
@app.get("/leads")
def get_leads(limit: int = 100) -> List[Dict]:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    res = supabase.table("leads").select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data or []


# ---------- Campaigns API ----------
@app.get("/campaigns", response_model=List[CampaignOut])
def get_campaigns(limit: int = 100):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    res = supabase.table("campaigns").select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data or []

@app.post("/campaigns", response_model=CampaignOut)
def create_campaign(campaign: CampaignIn):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    payload = campaign.dict()
    res = supabase.table("campaigns").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create campaign")
    return res.data[0]

@app.get("/campaigns/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    res = supabase.table("campaigns").select("*").eq("id", campaign_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return res.data

@app.put("/campaigns/{campaign_id}", response_model=CampaignOut)
def update_campaign(campaign_id: str, campaign: CampaignIn):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    payload = campaign.dict()
    res = supabase.table("campaigns").update(payload).eq("id", campaign_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Campaign not found or not updated")
    return res.data[0]

@app.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    res = supabase.table("campaigns").delete().eq("id", campaign_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Campaign not found or not deleted")
    return {"ok": True, "deleted": res.data}


# ---------- Performance Snapshots API ----------
@app.post("/campaigns/{campaign_id}/performance", response_model=PerformanceSnapshotOut)
def create_performance_snapshot(campaign_id: str, snapshot: PerformanceSnapshotIn):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    payload = snapshot.dict()
    payload["campaign_id"] = campaign_id
    res = supabase.table("performance_snapshots").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create performance snapshot")
    return res.data[0]

@app.get("/campaigns/{campaign_id}/performance", response_model=List[PerformanceSnapshotOut])
def get_performance_snapshots(campaign_id: str, limit: int = 100):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    res = supabase.table("performance_snapshots").select("*").eq("campaign_id", campaign_id).order("snapshot_date", desc=True).limit(limit).execute()
    return res.data or []

@app.post("/leads")
def create_lead(lead: LeadIn):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    payload = {
        "email": lead.email,
        "name": lead.name,
        "source": lead.source,
    }
    res = supabase.table("leads").insert(payload).execute()
    return res.data or []

# ---------- KPI routes ----------
@app.get("/kpi/summary")
def kpi_summary():
    """
    Returns simple counts:
      - total leads
      - leads in last 7 days
      - leads in last 30 days
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")

    now = datetime.now(timezone.utc)
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    # Total (use head=1 with count='exact' to avoid fetching all rows)
    total = supabase.table("leads").select("id", count="exact").limit(1).execute()
    total_count = total.count or 0

    last7 = supabase.table("leads").select("id", count="exact").gte("created_at", _iso(d7)).limit(1).execute()
    last7_count = last7.count or 0

    last30 = supabase.table("leads").select("id", count="exact").gte("created_at", _iso(d30)).limit(1).execute()
    last30_count = last30.count or 0

    return {
        "total": total_count,
        "last_7_days": last7_count,
        "last_30_days": last30_count,
    }

@app.get("/kpi/daily")
def kpi_daily(days: int = 30):
    """
    Returns daily counts for the last N days (default 30).
    We fetch leads since N days and group by day on the app side (simple & portable).
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")

    days = max(1, min(days, 90))  # clamp 1..90
    start = _today_utc() - timedelta(days=days - 1)

    res = supabase.table("leads").select("created_at").gte("created_at", _iso(start)).execute()
    rows = res.data or []

    # Initialize all days with 0
    buckets = {}
    for i in range(days):
        d = (start + timedelta(days=i)).date().isoformat()
        buckets[d] = 0

    # Count
    for r in rows:
        try:
            d = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).date().isoformat()
            if d in buckets:
                buckets[d] += 1
        except Exception:
            continue

    # Return in chronological order
    out = [{"day": day, "count": buckets[day]} for day in sorted(buckets.keys())]
    return out


# ---------- Google Ads Integration Endpoints ----------

@app.get("/google-ads/status")
def google_ads_status():
    """Check Google Ads API connection status"""
    if not google_ads_available:
        return {
            "available": False,
            "error": "Google Ads client not installed or configured",
            "required_env_vars": [
                "GOOGLE_ADS_DEVELOPER_TOKEN",
                "GOOGLE_ADS_CLIENT_ID",
                "GOOGLE_ADS_CLIENT_SECRET", 
                "GOOGLE_ADS_REFRESH_TOKEN",
                "GOOGLE_ADS_CUSTOMER_ID"
            ]
        }
    
    client = get_google_ads_client()
    if not client.is_available():
        return {
            "available": False,
            "error": "Google Ads client not properly configured",
            "missing_env_vars": True
        }
    
    # Test the connection
    connection_test = client.test_connection()
    return {
        "available": True,
        "connection_test": connection_test
    }

@app.get("/google-ads/campaigns")
def get_google_ads_campaigns():
    """Fetch campaigns directly from Google Ads"""
    if not google_ads_available:
        raise HTTPException(status_code=503, detail="Google Ads integration not available")
    
    client = get_google_ads_client()
    if not client.is_available():
        raise HTTPException(status_code=503, detail="Google Ads client not configured")
    
    campaigns = client.get_campaigns()
    return {
        "campaigns": campaigns,
        "count": len(campaigns),
        "source": "google_ads_api"
    }

@app.post("/google-ads/sync-campaigns")
def sync_google_ads_campaigns():
    """Sync campaigns from Google Ads to our database"""
    if not google_ads_available:
        raise HTTPException(status_code=503, detail="Google Ads integration not available")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    client = get_google_ads_client()
    if not client.is_available():
        raise HTTPException(status_code=503, detail="Google Ads client not configured")
    
    # Fetch campaigns from Google Ads
    google_campaigns = client.get_campaigns()
    
    synced_campaigns = []
    for google_campaign in google_campaigns:
        try:
            # Check if campaign already exists in our database
            existing = supabase.table("campaigns").select("*").eq("name", google_campaign["name"]).eq("platform", "google_ads").execute()
            
            campaign_data = {
                "name": google_campaign["name"],
                "platform": "google_ads", 
                "client_name": "Google Ads Import",  # Could be enhanced to extract actual client
                "budget": google_campaign["budget"],
                "spend": google_campaign["spend"],
                "metrics": {
                    "google_ads_id": google_campaign["google_ads_id"],
                    "status": google_campaign["status"],
                    "advertising_channel": google_campaign["advertising_channel"],
                    "impressions": google_campaign["impressions"],
                    "clicks": google_campaign["clicks"],
                    "conversions": google_campaign["conversions"],
                    "ctr": google_campaign["ctr"],
                    "average_cpc": google_campaign["average_cpc"],
                    "cost_per_conversion": google_campaign["cost_per_conversion"]
                }
            }
            
            if existing.data:
                # Update existing campaign
                result = supabase.table("campaigns").update(campaign_data).eq("id", existing.data[0]["id"]).execute()
                synced_campaigns.append({"action": "updated", "campaign": result.data[0]})
            else:
                # Create new campaign
                result = supabase.table("campaigns").insert(campaign_data).execute()
                synced_campaigns.append({"action": "created", "campaign": result.data[0]})
                
        except Exception as e:
            synced_campaigns.append({"action": "error", "campaign_name": google_campaign["name"], "error": str(e)})
    
    return {
        "synced_campaigns": synced_campaigns,
        "total_processed": len(google_campaigns),
        "successful_syncs": len([c for c in synced_campaigns if c["action"] in ["created", "updated"]])
    }

@app.get("/google-ads/campaigns/{google_ads_id}/performance")  
def get_google_ads_campaign_performance(google_ads_id: str, days: int = 30):
    """Get performance data for a specific Google Ads campaign"""
    if not google_ads_available:
        raise HTTPException(status_code=503, detail="Google Ads integration not available")
    
    client = get_google_ads_client()
    if not client.is_available():
        raise HTTPException(status_code=503, detail="Google Ads client not configured")
    
    performance_data = client.get_campaign_performance(google_ads_id, days)
    return {
        "campaign_id": google_ads_id,
        "days": days,
        "performance_data": performance_data,
        "data_points": len(performance_data)
    }

@app.post("/google-ads/sync-performance/{campaign_id}")
def sync_campaign_performance(campaign_id: str, days: int = 30):
    """Sync performance data from Google Ads for a specific campaign"""
    if not google_ads_available:
        raise HTTPException(status_code=503, detail="Google Ads integration not available")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    client = get_google_ads_client()
    if not client.is_available():
        raise HTTPException(status_code=503, detail="Google Ads client not configured")
    
    # Get campaign from our database to find Google Ads ID
    campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
    if not campaign.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign_data = campaign.data[0]
    google_ads_id = campaign_data.get("metrics", {}).get("google_ads_id")
    
    if not google_ads_id:
        raise HTTPException(status_code=400, detail="Campaign does not have Google Ads ID")
    
    # Fetch performance data from Google Ads
    performance_data = client.get_campaign_performance(google_ads_id, days)
    
    synced_snapshots = []
    for daily_data in performance_data:
        try:
            snapshot_data = {
                "snapshot_date": daily_data["date"],
                "metrics": {
                    "spend": daily_data["spend"],
                    "impressions": daily_data["impressions"],
                    "clicks": daily_data["clicks"], 
                    "conversions": daily_data["conversions"],
                    "ctr": daily_data["ctr"],
                    "average_cpc": daily_data["average_cpc"],
                    "cost_per_conversion": daily_data["cost_per_conversion"]
                }
            }
            
            # Upsert performance snapshot
            result = supabase.table("performance_snapshots").upsert({
                "campaign_id": campaign_id,
                **snapshot_data
            }).execute()
            
            synced_snapshots.append({"date": daily_data["date"], "status": "synced"})
            
        except Exception as e:
            synced_snapshots.append({"date": daily_data["date"], "status": "error", "error": str(e)})
    
    return {
        "campaign_id": campaign_id,
        "google_ads_id": google_ads_id,
        "synced_snapshots": synced_snapshots,
        "total_days": len(performance_data),
        "successful_syncs": len([s for s in synced_snapshots if s["status"] == "synced"])
    }


# ========== EMAIL MARKETING ENDPOINTS ==========

# Email Campaign Models
class EmailCampaignIn(BaseModel):
    name: str
    subject: Optional[str] = None
    content: Optional[str] = None
    status: str = "draft"  # draft, scheduled, sent, paused
    scheduled_at: Optional[str] = None
    template_id: Optional[str] = None
    segment_filters: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

class EmailCampaignOut(EmailCampaignIn):
    id: str
    created_at: str
    updated_at: str
    sent_count: Optional[int] = 0
    opened_count: Optional[int] = 0
    clicked_count: Optional[int] = 0
    bounce_count: Optional[int] = 0

# Email Subscriber Models  
class EmailSubscriberIn(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    status: str = "active"  # active, unsubscribed, bounced
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

class EmailSubscriberOut(EmailSubscriberIn):
    id: str
    created_at: str
    updated_at: str
    last_activity: Optional[str] = None

# Email Template Models
class EmailTemplateIn(BaseModel):
    name: str
    subject: str
    content: str
    template_type: str = "custom"  # custom, newsletter, welcome, promotional
    variables: Optional[List[str]] = None
    thumbnail: Optional[str] = None

class EmailTemplateOut(EmailTemplateIn):
    id: str
    created_at: str
    updated_at: str
    usage_count: Optional[int] = 0

# Email Campaign CRUD Operations
@app.get("/api/email-marketing/campaigns", response_model=List[EmailCampaignOut])
async def get_email_campaigns(
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """Get email marketing campaigns with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("email_campaigns").select("*")
        
        if status:
            query = query.eq("status", status)
        if search:
            query = query.ilike("name", f"%{search}%")
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")

@app.post("/api/email-marketing/campaigns", response_model=EmailCampaignOut)
async def create_email_campaign(campaign: EmailCampaignIn):
    """Create a new email marketing campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        campaign_data = campaign.dict()
        campaign_data.update({
            "created_at": now,
            "updated_at": now,
            "sent_count": 0,
            "opened_count": 0,
            "clicked_count": 0,
            "bounce_count": 0
        })
        
        result = supabase.table("email_campaigns").insert(campaign_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")

@app.get("/api/email-marketing/campaigns/{campaign_id}", response_model=EmailCampaignOut)
async def get_email_campaign(campaign_id: str):
    """Get a specific email campaign by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("email_campaigns").select("*").eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaign: {str(e)}")

@app.put("/api/email-marketing/campaigns/{campaign_id}", response_model=EmailCampaignOut)
async def update_email_campaign(campaign_id: str, campaign: EmailCampaignIn):
    """Update an existing email campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        campaign_data = campaign.dict()
        campaign_data["updated_at"] = _iso(datetime.now(timezone.utc))
        
        result = supabase.table("email_campaigns").update(campaign_data).eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update campaign: {str(e)}")

@app.delete("/api/email-marketing/campaigns/{campaign_id}")
async def delete_email_campaign(campaign_id: str):
    """Delete an email campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("email_campaigns").delete().eq("id", campaign_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        return {"message": "Campaign deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete campaign: {str(e)}")

# Email Subscriber CRUD Operations
@app.get("/api/email-marketing/subscribers", response_model=List[EmailSubscriberOut])
async def get_email_subscribers(
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None
):
    """Get email subscribers with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("email_subscribers").select("*")
        
        if status:
            query = query.eq("status", status)
        if search:
            query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
        if tags:
            tag_list = tags.split(",")
            query = query.contains("tags", tag_list)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subscribers: {str(e)}")

@app.post("/api/email-marketing/subscribers", response_model=EmailSubscriberOut)
async def create_email_subscriber(subscriber: EmailSubscriberIn):
    """Create a new email subscriber"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        subscriber_data = subscriber.dict()
        subscriber_data.update({
            "created_at": now,
            "updated_at": now,
            "last_activity": now
        })
        
        result = supabase.table("email_subscribers").insert(subscriber_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscriber: {str(e)}")

# Email Template CRUD Operations
@app.get("/api/email-marketing/templates", response_model=List[EmailTemplateOut])
async def get_email_templates(
    limit: int = 50,
    template_type: Optional[str] = None,
    search: Optional[str] = None
):
    """Get email templates with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("email_templates").select("*")
        
        if template_type:
            query = query.eq("template_type", template_type)
        if search:
            query = query.ilike("name", f"%{search}%")
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")

@app.post("/api/email-marketing/templates", response_model=EmailTemplateOut)
async def create_email_template(template: EmailTemplateIn):
    """Create a new email template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        template_data = template.dict()
        template_data.update({
            "created_at": now,
            "updated_at": now,
            "usage_count": 0
        })
        
        result = supabase.table("email_templates").insert(template_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

# Email Marketing Analytics
@app.get("/api/email-marketing/analytics/overview")
async def get_email_marketing_overview():
    """Get email marketing overview analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get campaign counts by status
        campaigns_result = supabase.table("email_campaigns").select("status").execute()
        campaigns_by_status = {}
        for campaign in campaigns_result.data:
            status = campaign.get("status", "draft")
            campaigns_by_status[status] = campaigns_by_status.get(status, 0) + 1
        
        # Get subscriber counts by status
        subscribers_result = supabase.table("email_subscribers").select("status").execute()
        subscribers_by_status = {}
        for subscriber in subscribers_result.data:
            status = subscriber.get("status", "active")
            subscribers_by_status[status] = subscribers_by_status.get(status, 0) + 1
        
        # Get total templates
        templates_result = supabase.table("email_templates").select("id").execute()
        total_templates = len(templates_result.data)
        
        # Calculate overall metrics
        total_campaigns = len(campaigns_result.data)
        total_subscribers = len(subscribers_result.data)
        
        return {
            "total_campaigns": total_campaigns,
            "total_subscribers": total_subscribers,
            "total_templates": total_templates,
            "campaigns_by_status": campaigns_by_status,
            "subscribers_by_status": subscribers_by_status,
            "active_subscribers": subscribers_by_status.get("active", 0),
            "sent_campaigns": campaigns_by_status.get("sent", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch overview: {str(e)}")


# ========== SOCIAL MEDIA ENDPOINTS ==========

# Social Media Models
class SocialMediaAccountIn(BaseModel):
    platform: str  # instagram, facebook, twitter, linkedin, tiktok, youtube
    username: str
    account_id: str
    access_token: Optional[str] = None
    account_type: str = "personal"  # personal, business, creator
    is_active: bool = True
    profile_data: Optional[Dict[str, Any]] = None

class SocialMediaAccountOut(SocialMediaAccountIn):
    id: str
    created_at: str
    updated_at: str
    last_sync: Optional[str] = None
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0
    post_count: Optional[int] = 0

class SocialMediaPostIn(BaseModel):
    account_id: str
    platform: str
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[str] = None
    status: str = "draft"  # draft, scheduled, published, failed
    post_type: str = "post"  # post, story, reel, video
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    location: Optional[str] = None

class SocialMediaPostOut(SocialMediaPostIn):
    id: str
    created_at: str
    updated_at: str
    published_at: Optional[str] = None
    platform_post_id: Optional[str] = None
    likes_count: Optional[int] = 0
    comments_count: Optional[int] = 0
    shares_count: Optional[int] = 0
    reach: Optional[int] = 0
    impressions: Optional[int] = 0

class SocialMediaCommentIn(BaseModel):
    post_id: str
    author_name: str
    author_username: str
    content: str
    platform_comment_id: str
    parent_comment_id: Optional[str] = None
    sentiment: Optional[str] = None  # positive, negative, neutral

class SocialMediaCommentOut(SocialMediaCommentIn):
    id: str
    created_at: str
    updated_at: str
    likes_count: Optional[int] = 0
    replies_count: Optional[int] = 0

# Social Media Account CRUD Operations
@app.get("/api/social-media/accounts", response_model=List[SocialMediaAccountOut])
async def get_social_media_accounts(
    platform: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50
):
    """Get social media accounts with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("social_media_accounts").select("*")
        
        if platform:
            query = query.eq("platform", platform)
        if is_active is not None:
            query = query.eq("is_active", is_active)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")

@app.post("/api/social-media/accounts", response_model=SocialMediaAccountOut)
async def create_social_media_account(account: SocialMediaAccountIn):
    """Create a new social media account"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        account_data = account.dict()
        account_data.update({
            "created_at": now,
            "updated_at": now,
            "last_sync": now,
            "follower_count": 0,
            "following_count": 0,
            "post_count": 0
        })
        
        result = supabase.table("social_media_accounts").insert(account_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")

@app.get("/api/social-media/accounts/{account_id}", response_model=SocialMediaAccountOut)
async def get_social_media_account(account_id: str):
    """Get a specific social media account by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("social_media_accounts").select("*").eq("id", account_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Account not found")
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch account: {str(e)}")

# Social Media Post CRUD Operations
@app.get("/api/social-media/posts", response_model=List[SocialMediaPostOut])
async def get_social_media_posts(
    account_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get social media posts with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("social_media_posts").select("*")
        
        if account_id:
            query = query.eq("account_id", account_id)
        if platform:
            query = query.eq("platform", platform)
        if status:
            query = query.eq("status", status)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")

@app.post("/api/social-media/posts", response_model=SocialMediaPostOut)
async def create_social_media_post(post: SocialMediaPostIn):
    """Create a new social media post"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        post_data = post.dict()
        post_data.update({
            "created_at": now,
            "updated_at": now,
            "likes_count": 0,
            "comments_count": 0,
            "shares_count": 0,
            "reach": 0,
            "impressions": 0
        })
        
        result = supabase.table("social_media_posts").insert(post_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")

@app.put("/api/social-media/posts/{post_id}", response_model=SocialMediaPostOut)
async def update_social_media_post(post_id: str, post: SocialMediaPostIn):
    """Update an existing social media post"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        post_data = post.dict()
        post_data["updated_at"] = _iso(datetime.now(timezone.utc))
        
        result = supabase.table("social_media_posts").update(post_data).eq("id", post_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update post: {str(e)}")

# Social Media Analytics
@app.get("/api/social-media/analytics/overview")
async def get_social_media_overview():
    """Get social media overview analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get account counts by platform
        accounts_result = supabase.table("social_media_accounts").select("platform,is_active").execute()
        accounts_by_platform = {}
        active_accounts = 0
        
        for account in accounts_result.data:
            platform = account.get("platform", "unknown")
            is_active = account.get("is_active", False)
            accounts_by_platform[platform] = accounts_by_platform.get(platform, 0) + 1
            if is_active:
                active_accounts += 1
        
        # Get post counts by status
        posts_result = supabase.table("social_media_posts").select("status,platform").execute()
        posts_by_status = {}
        posts_by_platform = {}
        
        for post in posts_result.data:
            status = post.get("status", "draft")
            platform = post.get("platform", "unknown")
            posts_by_status[status] = posts_by_status.get(status, 0) + 1
            posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1
        
        # Calculate totals
        total_accounts = len(accounts_result.data)
        total_posts = len(posts_result.data)
        published_posts = posts_by_status.get("published", 0)
        scheduled_posts = posts_by_status.get("scheduled", 0)
        
        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "total_posts": total_posts,
            "published_posts": published_posts,
            "scheduled_posts": scheduled_posts,
            "accounts_by_platform": accounts_by_platform,
            "posts_by_status": posts_by_status,
            "posts_by_platform": posts_by_platform
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch overview: {str(e)}")


# ========== COLLABORATION ENDPOINTS ==========

# Collaboration Models
class TeamMemberIn(BaseModel):
    name: str
    email: EmailStr
    role: str = "member"  # admin, manager, member, viewer
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    permissions: Optional[List[str]] = None

class TeamMemberOut(TeamMemberIn):
    id: str
    created_at: str
    updated_at: str
    last_active: Optional[str] = None
    projects_count: Optional[int] = 0

class TeamActivityIn(BaseModel):
    user_id: str
    action: str
    resource_type: str  # project, task, campaign, post
    resource_id: str
    description: str
    metadata: Optional[Dict[str, Any]] = None

class TeamActivityOut(TeamActivityIn):
    id: str
    created_at: str
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

class CollaborationProjectIn(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"  # active, completed, paused, archived
    team_members: Optional[List[str]] = None  # List of user IDs
    due_date: Optional[str] = None
    project_type: str = "marketing"  # marketing, content, campaign
    settings: Optional[Dict[str, Any]] = None

class CollaborationProjectOut(CollaborationProjectIn):
    id: str
    created_at: str
    updated_at: str
    completion_percentage: Optional[float] = 0.0
    task_count: Optional[int] = 0
    member_count: Optional[int] = 0

# Team Member CRUD Operations
@app.get("/api/collaboration/team-members", response_model=List[TeamMemberOut])
async def get_team_members(
    role: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50
):
    """Get team members with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("team_members").select("*")
        
        if role:
            query = query.eq("role", role)
        if department:
            query = query.eq("department", department)
        if is_active is not None:
            query = query.eq("is_active", is_active)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team members: {str(e)}")

@app.post("/api/collaboration/team-members", response_model=TeamMemberOut)
async def create_team_member(member: TeamMemberIn):
    """Create a new team member"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        member_data = member.dict()
        member_data.update({
            "created_at": now,
            "updated_at": now,
            "last_active": now,
            "projects_count": 0
        })
        
        result = supabase.table("team_members").insert(member_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team member: {str(e)}")

# Team Activity CRUD Operations
@app.get("/api/collaboration/activities", response_model=List[TeamActivityOut])
async def get_team_activities(
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100
):
    """Get team activities with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("team_activities").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        if resource_type:
            query = query.eq("resource_type", resource_type)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activities: {str(e)}")

@app.post("/api/collaboration/activities", response_model=TeamActivityOut)
async def create_team_activity(activity: TeamActivityIn):
    """Create a new team activity log"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        activity_data = activity.dict()
        activity_data["created_at"] = now
        
        result = supabase.table("team_activities").insert(activity_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create activity: {str(e)}")

# Collaboration Project CRUD Operations
@app.get("/api/collaboration/projects", response_model=List[CollaborationProjectOut])
async def get_collaboration_projects(
    status: Optional[str] = None,
    project_type: Optional[str] = None,
    limit: int = 50
):
    """Get collaboration projects with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("collaboration_projects").select("*")
        
        if status:
            query = query.eq("status", status)
        if project_type:
            query = query.eq("project_type", project_type)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@app.post("/api/collaboration/projects", response_model=CollaborationProjectOut)
async def create_collaboration_project(project: CollaborationProjectIn):
    """Create a new collaboration project"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        project_data = project.dict()
        project_data.update({
            "created_at": now,
            "updated_at": now,
            "completion_percentage": 0.0,
            "task_count": 0,
            "member_count": len(project_data.get("team_members", []))
        })
        
        result = supabase.table("collaboration_projects").insert(project_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

# Collaboration Analytics
@app.get("/api/collaboration/analytics/overview")
async def get_collaboration_overview():
    """Get collaboration overview analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get team member counts by role
        members_result = supabase.table("team_members").select("role,is_active").execute()
        members_by_role = {}
        active_members = 0
        
        for member in members_result.data:
            role = member.get("role", "member")
            is_active = member.get("is_active", False)
            members_by_role[role] = members_by_role.get(role, 0) + 1
            if is_active:
                active_members += 1
        
        # Get project counts by status
        projects_result = supabase.table("collaboration_projects").select("status,project_type").execute()
        projects_by_status = {}
        projects_by_type = {}
        
        for project in projects_result.data:
            status = project.get("status", "active")
            project_type = project.get("project_type", "marketing")
            projects_by_status[status] = projects_by_status.get(status, 0) + 1
            projects_by_type[project_type] = projects_by_type.get(project_type, 0) + 1
        
        # Get recent activity count
        today = _today_utc()
        week_ago = today - timedelta(days=7)
        activities_result = supabase.table("team_activities").select("id").gte("created_at", _iso(week_ago)).execute()
        
        return {
            "total_members": len(members_result.data),
            "active_members": active_members,
            "total_projects": len(projects_result.data),
            "active_projects": projects_by_status.get("active", 0),
            "completed_projects": projects_by_status.get("completed", 0),
            "recent_activities": len(activities_result.data),
            "members_by_role": members_by_role,
            "projects_by_status": projects_by_status,
            "projects_by_type": projects_by_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch overview: {str(e)}")


# ========== INTEGRATIONS ENDPOINTS ==========

# Integration Models
class IntegrationAppIn(BaseModel):
    name: str
    description: str
    category: str  # productivity, analytics, design, marketing, automation
    icon_url: Optional[str] = None
    developer: str
    website_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    pricing_model: str = "free"  # free, paid, freemium
    capabilities: Optional[List[str]] = None

class IntegrationAppOut(IntegrationAppIn):
    id: str
    created_at: str
    updated_at: str
    install_count: Optional[int] = 0
    rating: Optional[float] = 0.0
    review_count: Optional[int] = 0

class UserIntegrationIn(BaseModel):
    app_id: str
    user_id: str
    configuration: Optional[Dict[str, Any]] = None
    is_active: bool = True
    auto_sync: bool = False

class UserIntegrationOut(UserIntegrationIn):
    id: str
    created_at: str
    updated_at: str
    last_sync: Optional[str] = None
    sync_status: Optional[str] = "connected"  # connected, error, syncing
    app_name: Optional[str] = None
    app_icon: Optional[str] = None

# Integration App CRUD Operations
@app.get("/api/integrations/apps", response_model=List[IntegrationAppOut])
async def get_integration_apps(
    category: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_active: Optional[bool] = None,
    limit: int = 50
):
    """Get integration apps with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("integration_apps").select("*")
        
        if category:
            query = query.eq("category", category)
        if is_featured is not None:
            query = query.eq("is_featured", is_featured)
        if is_active is not None:
            query = query.eq("is_active", is_active)
            
        query = query.order("install_count", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integration apps: {str(e)}")

@app.post("/api/integrations/apps", response_model=IntegrationAppOut)
async def create_integration_app(app: IntegrationAppIn):
    """Create a new integration app"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        app_data = app.dict()
        app_data.update({
            "created_at": now,
            "updated_at": now,
            "install_count": 0,
            "rating": 0.0,
            "review_count": 0
        })
        
        result = supabase.table("integration_apps").insert(app_data).execute()
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create integration app: {str(e)}")

# User Integration CRUD Operations
@app.get("/api/integrations/user-integrations", response_model=List[UserIntegrationOut])
async def get_user_integrations(
    user_id: Optional[str] = None,
    app_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50
):
    """Get user integrations with optional filtering"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("user_integrations").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        if app_id:
            query = query.eq("app_id", app_id)
        if is_active is not None:
            query = query.eq("is_active", is_active)
            
        query = query.order("created_at", desc=True).limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user integrations: {str(e)}")

@app.post("/api/integrations/user-integrations", response_model=UserIntegrationOut)
async def create_user_integration(integration: UserIntegrationIn):
    """Create a new user integration"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        now = _iso(datetime.now(timezone.utc))
        integration_data = integration.dict()
        integration_data.update({
            "created_at": now,
            "updated_at": now,
            "last_sync": now,
            "sync_status": "connected"
        })
        
        result = supabase.table("user_integrations").insert(integration_data).execute()
        
        # Update install count for the app
        supabase.rpc("increment_install_count", {"app_id": integration.app_id}).execute()
        
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user integration: {str(e)}")

# Integrations Analytics
@app.get("/api/integrations/analytics/overview")
async def get_integrations_overview():
    """Get integrations overview analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get app counts by category
        apps_result = supabase.table("integration_apps").select("category,is_active,install_count").execute()
        apps_by_category = {}
        total_installs = 0
        active_apps = 0
        
        for app in apps_result.data:
            category = app.get("category", "other")
            is_active = app.get("is_active", False)
            install_count = app.get("install_count", 0)
            
            apps_by_category[category] = apps_by_category.get(category, 0) + 1
            total_installs += install_count
            if is_active:
                active_apps += 1
        
        # Get user integration counts
        integrations_result = supabase.table("user_integrations").select("is_active,sync_status").execute()
        active_integrations = 0
        connected_integrations = 0
        
        for integration in integrations_result.data:
            is_active = integration.get("is_active", False)
            sync_status = integration.get("sync_status", "")
            
            if is_active:
                active_integrations += 1
            if sync_status == "connected":
                connected_integrations += 1
        
        return {
            "total_apps": len(apps_result.data),
            "active_apps": active_apps,
            "total_installs": total_installs,
            "total_integrations": len(integrations_result.data),
            "active_integrations": active_integrations,
            "connected_integrations": connected_integrations,
            "apps_by_category": apps_by_category,
            "connection_rate": (connected_integrations / len(integrations_result.data)) * 100 if integrations_result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch overview: {str(e)}")

