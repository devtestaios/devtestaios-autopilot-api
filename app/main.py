from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx

app = FastAPI(title="Autopilot API", version="0.1.0")

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

@app.get("/_routes")
def list_routes():
    return {"routes": sorted([r.path for r in app.routes])}

@app.get("/version")
def version():
    return {"version": app.version}

@app.get("/env-check")
def env_check():
    return {
        "SUPABASE_URL_present": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY_present": bool(os.getenv("SUPABASE_ANON_KEY")),
    }

@app.get("/test-db")
def test_db():
    """
    Minimal Supabase reachability check.
    Requires SUPABASE_URL and SUPABASE_ANON_KEY set in Render.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return {
            "ok": False,
            "SUPABASE_URL_present": bool(url),
            "SUPABASE_ANON_KEY_present": bool(key),
            "error": "Missing SUPABASE_URL or SUPABASE_ANON_KEY",
        }

    info_url = url.rstrip("/") + "/auth/v1/info"
    try:
        r = httpx.get(info_url, headers={"apikey": key}, timeout=5.0)
        return {"ok": r.status_code == 200, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}
