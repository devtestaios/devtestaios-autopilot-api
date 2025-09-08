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
def routes():
    return {"routes": ["/", "/health", "/_routes", "/test-db"]}

@app.get("/test-db")
async def test_db():
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not url or not key:
        return {"ok": False, "error": "Missing Supabase envs on server"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{url}/auth/v1/settings", headers={"apikey": key})
        return {"ok": r.status_code == 200, "status": r.status_code}
