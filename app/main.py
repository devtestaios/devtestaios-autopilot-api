from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os, httpx

app = FastAPI(title="Autopilot API", version="0.1.0")

# Allow your Vercel sites to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # just show the important ones (nice for debugging what deployed)
    return {"routes": ["/", "/health", "/_routes", "/version", "/env-check", "/test-db", "/leads"]}

@app.get("/env-check")
def env_check():
    return {
        "SUPABASE_URL_present": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY_present": bool(os.getenv("SUPABASE_ANON_KEY")),
        "SUPABASE_SERVICE_ROLE_KEY_present": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
    }

@app.get("/test-db")
async def test_db():
    """
    Pings a public Supabase auth endpoint to prove URL/key shape.
    This uses the *anon* key; it doesn't read/write DB.
    """
    url = os.getenv("SUPABASE_URL")
    anon = os.getenv("SUPABASE_ANON_KEY")
    if not url or not anon:
        return {"ok": False, "error": "Missing Supabase envs on server"}
    try_urls = [
        (url.rstrip("/") + "/auth/v1/info", "info"),
        (url.rstrip("/") + "/auth/v1/settings", "settings"),
    ]
    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        for u, label in try_urls:
            r = await client.get(u, headers={"apikey": anon})
            results.append({"url": u, "label": label, "status": r.status_code})
            if r.status_code == 200:
                return {"ok": True, "status": 200, "url": u}
    return {"ok": False, "status": results[-1]["status"] if results else None, "tried": results}

# ------------------------
# Leads endpoints (WRITE + READ via service role)
# ------------------------

class LeadIn(BaseModel):
    email: EmailStr
    name: str | None = None

@app.post("/leads")
async def create_lead(payload: LeadIn):
    """
    Inserts a row into public.leads using Supabase REST.
    Uses SERVICE ROLE key (server-only).
    """
    base = os.getenv("SUPABASE_URL")
    srv = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not srv:
        return {"ok": False, "error": "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY"}

    rest_url = base.rstrip("/") + "/rest/v1/leads"
    headers = {
        "apikey": srv,
        "Authorization": f"Bearer {srv}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(rest_url, headers=headers, json=payload.model_dump())
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
    return {"ok": r.status_code in (200, 201), "status": r.status_code, "data": data}

@app.get("/leads")
async def list_leads():
    """
    Returns the latest 20 leads.
    """
    base = os.getenv("SUPABASE_URL")
    srv = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not srv:
        return {"ok": False, "error": "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY"}

    rest_url = base.rstrip("/") + "/rest/v1/leads?select=*&order=created_at.desc&limit=20"
    headers = {
        "apikey": srv,
        "Authorization": f"Bearer {srv}",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(rest_url, headers=headers)
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
    return {"ok": r.status_code == 200, "status": r.status_code, "data": data}
