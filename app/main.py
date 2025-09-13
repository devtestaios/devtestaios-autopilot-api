from typing import Optional, List
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import httpx

# ---- App + CORS ----
app = FastAPI(title="Autopilot API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Simple health/version/routes ----
@app.get("/")
def root():
    return {"status": "ok", "msg": "Autopilot API root"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": "0.1.0"}

@app.get("/_routes")
def routes():
    return {"routes": [r.path for r in app.routes]}

# ---- Env check + Supabase network check ----
@app.get("/env-check")
def env_check():
    return {
        "SUPABASE_URL_present": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY_present": bool(os.getenv("SUPABASE_ANON_KEY")),
    }

@app.get("/test-db")
def test_db():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        return {"ok": False, "error": "Missing Supabase envs on server"}

    targets = [f"{url}/auth/v1/settings", f"{url}/auth/v1/info"]
    tried = []
    for t in targets:
        try:
            r = httpx.get(t, headers={"apikey": key}, timeout=8.0)
            tried.append({"url": t, "status": r.status_code})
            if r.status_code == 200:
                return {"ok": True, "status": 200, "url": t}
        except Exception as e:
            tried.append({"url": t, "error": str(e)})
    return {"ok": False, "status": 404, "tried": tried}

# ---- Leads models ----
class LeadIn(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = None

class LeadOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None

# ---- Supabase client (lazy import so local dev works even if not installed) ----
def _sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase env vars missing")
    try:
        from supabase import create_client, Client  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase client import failed: {e}")
    return create_client(url, key)

# ---- Leads endpoints ----
@app.get("/leads", response_model=List[LeadOut])
def list_leads():
    sb = _sb()
    resp = sb.table("leads").select("*").order("created_at", desc=True).limit(50).execute()
    return resp.data or []

@app.post("/leads", response_model=LeadOut)
def create_lead(payload: LeadIn):
    sb = _sb()
    # Upsert by email (optional): change to .insert if you prefer duplicates
    resp = sb.table("leads").upsert(
        {"email": payload.email, "name": payload.name, "source": payload.source},
        on_conflict="email"
    ).select("*").single().execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Insert/upsert failed")
    return resp.data
