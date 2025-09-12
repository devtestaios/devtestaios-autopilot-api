from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx

app = FastAPI(title="Autopilot API", version="0.1.0")

# Allow your Vercel frontends
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
def _routes():
    # show available routes to prove what’s deployed
    return {
        "routes": sorted([r.path for r in app.routes])
    }

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
    Supabase reachability check.
    Tries /auth/v1/settings (preferred). Falls back to /auth/v1/info.
    Returns what it tried so 404s are diagnosable.
    """
    base = os.getenv("SUPABASE_URL")
    key  = os.getenv("SUPABASE_ANON_KEY")
    if not base or not key:
        return {
            "ok": False,
            "SUPABASE_URL_present": bool(base),
            "SUPABASE_ANON_KEY_present": bool(key),
            "error": "Missing SUPABASE_URL or SUPABASE_ANON_KEY",
        }

    base = base.rstrip("/")
    headers = {"apikey": key}
    tried = []

    for path in ("/auth/v1/settings", "/auth/v1/info"):
        url = base + path
        try:
            r = httpx.get(url, headers=headers, timeout=7.0)
            tried.append({"url": url, "status": r.status_code})
            if r.status_code == 200:
                return {"ok": True, "status": 200, "url": url}
        except Exception as e:
            tried.append({"url": url, "error": str(e)})

    return {"ok": False, "tried": tried}
