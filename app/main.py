from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import os
import httpx
from datetime import datetime, timedelta, timezone


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

