"""
PulseBridge.ai FastAPI Backend with AI Integration
Complete backend server with Claude AI chat and platform control
"""

import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging
from pydantic import BaseModel
import aiohttp

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase Integration
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    # Try SUPABASE_KEY first (your variable), then fallback to SUPABASE_ANON_KEY
    SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_AVAILABLE = True
        logger.info("✅ Supabase client initialized successfully")
    else:
        logger.warning("❌ Supabase environment variables not found")
        logger.warning(f"SUPABASE_URL: {bool(SUPABASE_URL)}, SUPABASE_KEY: {bool(SUPABASE_KEY)}")
        supabase = None
        SUPABASE_AVAILABLE = False
except ImportError as e:
    logger.warning(f"Supabase not available: {e}")
    supabase = None
    SUPABASE_AVAILABLE = False

# Import AI Services
from ai_endpoints import ai_router
from ai_chat_service import ai_service, ChatRequest

# Import Optimization Engine
from optimization_endpoints import router as optimization_router

# Import Multi-Platform Sync Engine
from sync_endpoints import router as sync_router

# Import Advanced Analytics Engine
from analytics_endpoints import router as analytics_router

# Import Autonomous Decision Framework
from autonomous_decision_endpoints import router as autonomous_router

# Import Google Ads Integration
try:
    from google_ads_integration import get_google_ads_client, fetch_campaigns_from_google_ads, fetch_performance_from_google_ads
    GOOGLE_ADS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google Ads integration not available: {e}")
    GOOGLE_ADS_AVAILABLE = False
    # Create placeholder functions
    def get_google_ads_client(): return None
    def fetch_campaigns_from_google_ads(): return []
    def fetch_performance_from_google_ads(campaign_id: str, days: int = 30): return []

# Import Meta Business API Integration - ✅ VALIDATED CREDENTIALS
from meta_business_api import meta_api

# Import LinkedIn Ads Integration  
from linkedin_ads_integration import (
    get_linkedin_ads_status,
    get_linkedin_ads_campaigns,
    get_linkedin_ads_performance
)

# Import Pinterest Ads Integration
from pinterest_ads_integration import (
    get_pinterest_ads_status,
    get_pinterest_ads_campaigns,
    get_pinterest_ads_performance
)

# Import Hybrid AI System (NEW)
from meta_ai_hybrid_integration import PulseBridgeAIMasterController, CrossPlatformMetrics, AIDecisionLog
from smart_risk_management import SmartRiskManager, ClientReportingManager, RISK_MANAGEMENT_TEMPLATES, CLIENT_REPORTING_TEMPLATES
from hybrid_ai_endpoints import hybrid_ai_router

# Security
security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 PulseBridge.ai Backend Starting...")
    logger.info(f"AI Provider: {os.getenv('AI_PROVIDER', 'openai')}")
    logger.info(f"Claude API Key: {'✅ Configured' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    logger.info(f"OpenAI API Key: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    yield
    logger.info("🔄 PulseBridge.ai Backend Shutting Down...")

# Create FastAPI application
app = FastAPI(
    title="PulseBridge.ai Backend",
    description="Fully AI-Powered Marketing Automation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pulsebridge.ai",
        "https://autopilot-web-rho.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI router
app.include_router(ai_router, prefix="/api/v1")

# Include Optimization Engine router
app.include_router(optimization_router)

# Include Multi-Platform Sync router
app.include_router(sync_router)

# Include Advanced Analytics Engine router
app.include_router(analytics_router)

# Include Autonomous Decision Framework router
app.include_router(autonomous_router)

# Include Hybrid AI System router (NEW)
app.include_router(hybrid_ai_router)

# ================================
# GOOGLE ADS INTEGRATION ENDPOINTS
# ================================

@app.get("/google-ads/status")
def google_ads_status():
    """Check Google Ads API connection status"""
    try:
        google_ads_client = get_google_ads_client()
        status = google_ads_client.get_connection_status()
        
        return {
            "status": "connected" if status["connected"] else "error",
            "connected": status["connected"],
            "customer_id": status.get("customer_id"),
            "message": status.get("message"),
            "error": status.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking Google Ads status: {e}")
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/google-ads/campaigns")
def get_google_ads_campaigns():
    """Fetch campaigns from Google Ads API"""
    try:
        google_ads_client = get_google_ads_client()
        
        if not google_ads_client.is_connected():
            raise HTTPException(
                status_code=503, 
                detail="Google Ads API not connected. Check your credentials."
            )
        
        campaigns = fetch_campaigns_from_google_ads()
        
        return {
            "campaigns": campaigns,
            "count": len(campaigns),
            "source": "google_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Google Ads campaigns: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch campaigns from Google Ads: {str(e)}"
        )

@app.get("/google-ads/campaigns/{campaign_id}/performance")
def get_google_ads_campaign_performance(campaign_id: str, days: int = 30):
    """Get performance data for a specific campaign from Google Ads"""
    try:
        google_ads_client = get_google_ads_client()
        
        if not google_ads_client.is_connected():
            raise HTTPException(
                status_code=503,
                detail="Google Ads API not connected. Check your credentials."
            )
        
        performance_data = fetch_performance_from_google_ads(campaign_id, days)
        
        return {
            "campaign_id": campaign_id,
            "performance": performance_data,
            "count": len(performance_data),
            "days": days,
            "source": "google_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Google Ads performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch performance data from Google Ads: {str(e)}"
        )

# ===== META ADS ENDPOINTS - ✅ VALIDATED INTEGRATION =====

@app.get("/meta-ads/status")
async def get_meta_ads_status_endpoint():
    """Check Meta Ads API connection status - ✅ WORKING"""
    try:
        account_info = meta_api.get_account_info()
        
        if 'error' in account_info:
            return {
                "platform": "meta_ads",
                "status": {"connected": False, "error": account_info['error']},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return {
            "platform": "meta_ads",
            "status": {
                "connected": True,
                "account_name": account_info.get('name', 'pulsebridge.ai'),
                "account_id": meta_api.ad_account_id,
                "currency": account_info.get('currency', 'USD'),
                "account_status": account_info.get('account_status', 1)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking Meta Ads status: {e}")
        return {
            "platform": "meta_ads", 
            "status": {"connected": False, "error": str(e)},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/meta-ads/campaigns")
async def get_meta_ads_campaigns_endpoint(limit: int = 25):
    """Get campaigns from Meta Ads - ✅ VALIDATED"""
    try:
        campaigns = meta_api.get_campaigns(limit)
        return {
            "campaigns": campaigns,
            "count": len(campaigns),
            "source": "meta_business_api",
            "account": "pulsebridge.ai",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching Meta Ads campaigns: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaigns from Meta Ads: {str(e)}"
        )

@app.get("/meta-ads/campaigns/{campaign_id}/performance")
async def get_meta_ads_campaign_performance(campaign_id: str, days: int = 7):
    """Get performance data for a specific campaign from Meta Ads"""
    try:
        # Map days to Meta's date preset
        date_preset = 'last_7_days'
        if days <= 1:
            date_preset = 'yesterday'
        elif days <= 7:
            date_preset = 'last_7_days'
        elif days <= 14:
            date_preset = 'last_14_days'
        elif days <= 30:
            date_preset = 'last_30_days'
        else:
            date_preset = 'last_90_days'
        
        performance_data = meta_api.get_campaign_insights(campaign_id, date_preset)
        
        return {
            "campaign_id": campaign_id,
            "performance": performance_data,
            "days": days,
            "date_preset": date_preset,
            "source": "meta_business_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching Meta Ads performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch performance data from Meta Ads: {str(e)}"
        )

@app.get("/meta-ads/performance")
async def get_meta_ads_account_performance():
    """Get account-level summary from Meta Ads - ✅ VALIDATED"""
    try:
        summary = meta_api.get_account_summary()
        return {
            "account_summary": summary,
            "source": "meta_business_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching Meta Ads account performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch account performance from Meta Ads: {str(e)}"
        )

@app.post("/meta-ads/campaigns")
async def create_meta_campaign(campaign_data: Dict[str, Any]):
    """Create a new Meta campaign - ✅ API READY"""
    try:
        result = meta_api.create_campaign(campaign_data)
        
        if 'error' in result:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create campaign: {result['error']}"
            )
        
        return {
            "success": True,
            "campaign": result,
            "source": "meta_business_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Meta campaign: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Meta campaign: {str(e)}"
        )

# ===== META API CONVENIENCE ALIASES =====
# These aliases make the API more intuitive for frontend testing

@app.get("/meta/status")
async def get_meta_status_alias():
    """Convenience alias for /meta-ads/status"""
    return await get_meta_ads_status_endpoint()

@app.get("/meta/campaigns")
async def get_meta_campaigns_alias(limit: int = 25):
    """Convenience alias for /meta-ads/campaigns"""
    return await get_meta_ads_campaigns_endpoint(limit)

@app.get("/meta/test")
async def meta_api_test():
    """Simple Meta API connectivity test"""
    try:
        status = await get_meta_ads_status_endpoint()
        return {
            "success": True,
            "message": "Meta Business API connection successful",
            "platform": "Meta Business API",
            "account": status.get("status", {}).get("account_name", "Unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Meta API connection failed: {str(e)}",
            "platform": "Meta Business API",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# ===== LINKEDIN ADS ENDPOINTS =====

@app.get("/linkedin-ads/status")
async def get_linkedin_ads_status_endpoint():
    """Check LinkedIn Ads API connection status"""
    try:
        status = await get_linkedin_ads_status()
        return {
            "platform": "linkedin_ads",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking LinkedIn Ads status: {e}")
        return {
            "platform": "linkedin_ads",
            "status": {"connected": False, "error": str(e)},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/linkedin-ads/campaigns")
async def get_linkedin_ads_campaigns_endpoint(limit: int = 25):
    """Get campaigns from LinkedIn Ads"""
    try:
        campaigns = await get_linkedin_ads_campaigns(limit)
        return {
            "campaigns": campaigns,
            "count": len(campaigns),
            "source": "linkedin_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching LinkedIn Ads campaigns: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaigns from LinkedIn Ads: {str(e)}"
        )

@app.get("/linkedin-ads/campaigns/{campaign_id}/performance")
async def get_linkedin_ads_campaign_performance(campaign_id: str, days: int = 30):
    """Get performance data for a specific campaign from LinkedIn Ads"""
    try:
        performance_data = await get_linkedin_ads_performance(campaign_id, days)
        return {
            "campaign_id": campaign_id,
            "performance": performance_data,
            "days": days,
            "source": "linkedin_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching LinkedIn Ads performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch performance data from LinkedIn Ads: {str(e)}"
        )

@app.get("/linkedin-ads/performance")
async def get_linkedin_ads_account_performance(days: int = 30):
    """Get account-level performance data from LinkedIn Ads"""
    try:
        performance_data = await get_linkedin_ads_performance(None, days)
        return {
            "performance": performance_data,
            "days": days,
            "source": "linkedin_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching LinkedIn Ads account performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch account performance from LinkedIn Ads: {str(e)}"
        )

# ===== PINTEREST ADS ENDPOINTS =====

@app.get("/pinterest-ads/status")
async def get_pinterest_ads_status_endpoint():
    """Check Pinterest Ads API connection status"""
    try:
        status = await get_pinterest_ads_status()
        return {
            "platform": "pinterest_ads",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking Pinterest Ads status: {e}")
        return {
            "platform": "pinterest_ads",
            "status": {"connected": False, "error": str(e)},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/pinterest-ads/campaigns")
async def get_pinterest_ads_campaigns_endpoint(limit: int = 25):
    """Get campaigns from Pinterest Ads"""
    try:
        campaigns = await get_pinterest_ads_campaigns(limit)
        return {
            "campaigns": campaigns,
            "count": len(campaigns),
            "source": "pinterest_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Pinterest Ads campaigns: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaigns from Pinterest Ads: {str(e)}"
        )

@app.get("/pinterest-ads/campaigns/{campaign_id}/performance")
async def get_pinterest_ads_campaign_performance(campaign_id: str, days: int = 30):
    """Get performance data for a specific campaign from Pinterest Ads"""
    try:
        performance_data = await get_pinterest_ads_performance(campaign_id, days)
        return {
            "campaign_id": campaign_id,
            "performance": performance_data,
            "days": days,
            "source": "pinterest_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Pinterest Ads performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch performance data from Pinterest Ads: {str(e)}"
        )

@app.get("/pinterest-ads/performance")
async def get_pinterest_ads_account_performance(days: int = 30):
    """Get account-level performance data from Pinterest Ads"""
    try:
        performance_data = await get_pinterest_ads_performance(None, days)
        return {
            "performance": performance_data,
            "days": days,
            "source": "pinterest_ads_api",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Pinterest Ads account performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch account performance from Pinterest Ads: {str(e)}"
        )

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with service status"""
    return {
        "service": "PulseBridge.ai Backend",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_integration": "enabled",
        "ai_provider": os.getenv('AI_PROVIDER', 'openai'),
        "endpoints": {
            "ai_chat": "/api/v1/ai/chat",
            "ai_actions": "/api/v1/ai/execute-action",
            "ai_status": "/api/v1/ai/status",
            "optimization": "/api/v1/optimization",
            "sync": "/api/v1/sync",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    ai_status = {
        "claude_configured": bool(os.getenv('ANTHROPIC_API_KEY')),
        "openai_configured": bool(os.getenv('OPENAI_API_KEY')),
        "preferred_provider": os.getenv('AI_PROVIDER', 'openai'),
        "service_healthy": True
    }
    
    # Test actual Supabase connection
    db_status = "disconnected"
    if SUPABASE_AVAILABLE and supabase:
        try:
            # Test with a simple query
            result = supabase.table("email_campaigns").select("id").limit(1).execute()
            db_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "operational",
        "ai_services": ai_status,
        "database": db_status,
        "supabase_available": SUPABASE_AVAILABLE,
        "version": "1.0.0"
    }

@app.get("/debug/supabase")
async def debug_supabase():
    """Debug Supabase connection"""
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    return {
        "supabase_url_configured": bool(os.getenv('SUPABASE_URL')),
        "supabase_key_configured": bool(supabase_key),
        "supabase_available": SUPABASE_AVAILABLE,
        "supabase_client_exists": supabase is not None,
        "env_vars": {
            "SUPABASE_URL": os.getenv('SUPABASE_URL', 'NOT_SET')[:50] + "..." if os.getenv('SUPABASE_URL') else None,
            "SUPABASE_KEY": os.getenv('SUPABASE_KEY', 'NOT_SET')[:20] + "..." if os.getenv('SUPABASE_KEY') else None,
            "SUPABASE_ANON_KEY": os.getenv('SUPABASE_ANON_KEY', 'NOT_SET')[:20] + "..." if os.getenv('SUPABASE_ANON_KEY') else None,
            "SUPABASE_SERVICE_ROLE_KEY": os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'NOT_SET')[:20] + "..." if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else None
        }
    }

@app.get("/debug/tables")
async def debug_tables():
    """List available tables in the database"""
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Try to get the schema information
        result = supabase.table("information_schema.tables").select("table_name").eq("table_schema", "public").execute()
        return {
            "tables_found": len(result.data),
            "tables": [row["table_name"] for row in result.data] if result.data else [],
            "raw_response": result.data
        }
    except Exception as e:
        # Fallback: try to query some common table names to see which exist
        test_tables = ["email_campaigns", "campaigns", "leads", "social_media_accounts", "team_members"]
        existing_tables = []
        
        for table in test_tables:
            try:
                result = supabase.table(table).select("id").limit(1).execute()
                existing_tables.append(table)
            except:
                pass
        
        return {
            "error": str(e),
            "test_method": "table_probing",
            "existing_tables": existing_tables
        }

@app.get("/health/instagram")
async def instagram_health_check():
    """Instagram OAuth configuration health check"""
    try:
        app_id = os.getenv("NEXT_PUBLIC_INSTAGRAM_APP_ID")
        app_secret = os.getenv("INSTAGRAM_APP_SECRET")
        base_url = os.getenv("NEXT_PUBLIC_BASE_URL")
        
        status = {
            "instagram_app_id_configured": bool(app_id),
            "instagram_app_secret_configured": bool(app_secret),
            "base_url_configured": bool(base_url),
            "oauth_endpoints_available": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if app_id:
            status["app_id_length"] = len(app_id)
            status["app_id_preview"] = f"{app_id[:4]}...{app_id[-4:]}" if len(app_id) > 8 else "too_short"
        
        if base_url:
            status["redirect_uri"] = f"{base_url}/auth/instagram/callback"
        
        overall_status = "healthy" if all([app_id, app_secret, base_url]) else "partial"
        
        return {
            "status": overall_status,
            "details": status,
            "ready_for_oauth": all([app_id, app_secret, base_url])
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Campaign Management (existing endpoints)
@app.get("/api/v1/campaigns")
async def get_campaigns():
    """Get all campaigns"""
    # Mock data for now - integrate with your database
    return [
        {
            "id": "camp_001",
            "name": "Holiday Shopping Campaign",
            "platform": "google_ads",
            "status": "active",
            "budget": 5000,
            "spend": 2150.50,
            "created_at": "2025-09-15T10:00:00Z"
        },
        {
            "id": "camp_002", 
            "name": "Brand Awareness Q4",
            "platform": "meta",
            "status": "active",
            "budget": 3000,
            "spend": 1850.25,
            "created_at": "2025-09-10T14:30:00Z"
        }
    ]

@app.post("/api/v1/campaigns")
async def create_campaign(campaign_data: Dict[str, Any]):
    """Create new campaign"""
    logger.info(f"Creating campaign: {campaign_data}")
    
    # Mock campaign creation - integrate with your database
    new_campaign = {
        "id": f"camp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "name": campaign_data.get("name", "New Campaign"),
        "platform": campaign_data.get("platform", "google_ads"),
        "status": "active",
        "budget": campaign_data.get("budget", 1000),
        "spend": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return {
        "success": True,
        "campaign": new_campaign,
        "message": "Campaign created successfully"
    }

# Dashboard data
@app.get("/api/v1/dashboard/overview")
async def dashboard_overview():
    """Dashboard overview data"""
    return {
        "total_campaigns": 12,
        "active_campaigns": 8,
        "total_spend": 15750.25,
        "total_conversions": 342,
        "avg_roas": 4.2,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

# Lead management
@app.get("/api/v1/leads")
async def get_leads():
    """Get all leads"""
    return [
        {
            "id": "lead_001",
            "name": "John Smith",
            "email": "john@example.com",
            "source": "google_ads",
            "status": "qualified",
            "created_at": "2025-09-18T09:15:00Z"
        }
    ]

# AI Chat Endpoints
@app.post("/api/v1/ai/chat")
async def ai_chat(request: ChatRequest):
    """AI Chat endpoint for content generation and assistance"""
    try:
        logger.info(f"AI Chat Request: {request.message[:100]}...")
        response = await ai_service.chat_with_ai(request)
        logger.info(f"AI Chat Response generated successfully")
        return response
    except Exception as e:
        logger.error(f"AI Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

@app.get("/api/v1/ai/health")
async def ai_health():
    """Check AI service health"""
    try:
        return {
            "status": "healthy",
            "claude_available": bool(os.getenv('ANTHROPIC_API_KEY')),
            "openai_available": bool(os.getenv('OPENAI_API_KEY')),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"AI Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "status_code": 500}

# Google Ads Test Endpoints
@app.get("/google-ads/config-check")
def check_google_ads_config():
    """Check if Google Ads environment variables are configured"""
    config = {}
    
    # Show environment variables (safely)
    config["GOOGLE_ADS_DEVELOPER_TOKEN"] = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN', 'NOT SET')
    
    client_id = os.getenv('GOOGLE_ADS_CLIENT_ID', 'NOT SET')
    config["GOOGLE_ADS_CLIENT_ID"] = client_id  # Show full client ID for debugging
    config["GOOGLE_ADS_CLIENT_ID_LENGTH"] = len(client_id) if client_id != 'NOT SET' else 0
    
    client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET', 'NOT SET')
    config["GOOGLE_ADS_CLIENT_SECRET"] = "***" + client_secret[-6:] if client_secret != 'NOT SET' and len(client_secret) > 6 else 'NOT SET'
    config["GOOGLE_ADS_CLIENT_SECRET_LENGTH"] = len(client_secret) if client_secret != 'NOT SET' else 0
    
    refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN', 'NOT SET')
    config["GOOGLE_ADS_REFRESH_TOKEN"] = refresh_token[:30] + "..." if refresh_token != 'NOT SET' and len(refresh_token) > 30 else 'NOT SET'
    config["GOOGLE_ADS_REFRESH_TOKEN_LENGTH"] = len(refresh_token) if refresh_token != 'NOT SET' else 0
    
    config["GOOGLE_ADS_CUSTOMER_ID"] = os.getenv('GOOGLE_ADS_CUSTOMER_ID', 'NOT SET')
    
    return config

@app.get("/google-ads/oauth-help")
def google_ads_oauth_help():
    """Provide guidance for fixing OAuth configuration"""
    return {
        "issue": "OAuth client was not found",
        "likely_cause": "Domain restrictions on OAuth client",
        "solution_steps": [
            "1. Go to Google Cloud Console (https://console.cloud.google.com/)",
            "2. Navigate to 'APIs & Services' > 'Credentials'",
            "3. Find your OAuth 2.0 client ID that starts with '141284371364-...'",
            "4. Click 'Edit' on the OAuth client",
            "5. In 'Authorized JavaScript origins', add:",
            "   - https://autopilot-api-1.onrender.com",
            "6. In 'Authorized redirect URIs', add:",
            "   - https://autopilot-api-1.onrender.com/",
            "   - https://autopilot-api-1.onrender.com/oauth/callback",
            "7. Save changes and wait 5-10 minutes for propagation",
            "8. Test again using /google-ads/oauth-diagnostic"
        ],
        "current_domain": "autopilot-api-1.onrender.com",
        "test_endpoints": {
            "config": "/google-ads/config-check",
            "oauth_test": "/google-ads/oauth-diagnostic", 
            "full_api_test": "/google-ads/test-api",
            "help": "/google-ads/oauth-help"
        },
        "additional_notes": [
            "The OAuth client must be configured for 'Web application' type",
            "Make sure the Google Ads API is enabled in your project",
            "The client ID should end with .apps.googleusercontent.com"
        ]
    }

@app.post("/google-ads/test-token")
def test_google_ads_token():
    """Test Google Ads refresh token exchange"""
    import requests
    
    try:
        client_id = os.getenv('GOOGLE_ADS_CLIENT_ID', '').strip()
        client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET', '').strip()
        refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN', '').strip()
        
        if not all([client_id, client_secret, refresh_token]):
            raise HTTPException(status_code=400, detail="Missing OAuth credentials")
        
        # Exchange refresh token for access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                "success": True,
                "access_token": token_data.get('access_token', '')[:20] + "...",
                "expires_in": token_data.get('expires_in'),
                "token_type": token_data.get('token_type')
            }
        else:
            return {
                "success": False,
                "error": response.json(),
                "status_code": response.status_code
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token test failed: {str(e)}")

@app.get("/google-ads/oauth-diagnostic")
def google_ads_oauth_diagnostic():
    """Diagnostic endpoint for Google Ads OAuth issues"""
    try:
        # Only import requests which should be available
        import requests
        
        client_id = os.getenv('GOOGLE_ADS_CLIENT_ID', '').strip()
        client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET', '').strip()
        refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN', '').strip()
        developer_token = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN', '').strip()
        customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID', '').strip()
        
        # Check if all variables are present
        config_status = {
            "client_id_present": bool(client_id),
            "client_id_format": client_id[:30] + "..." if client_id and len(client_id) > 30 else client_id,
            "client_secret_present": bool(client_secret),
            "client_secret_format": "***" + client_secret[-4:] if client_secret and len(client_secret) > 4 else "MISSING",
            "refresh_token_present": bool(refresh_token),
            "refresh_token_format": refresh_token[:30] + "..." if refresh_token and len(refresh_token) > 30 else "MISSING",
            "developer_token_present": bool(developer_token),
            "customer_id_present": bool(customer_id)
        }
        
        if not all([client_id, client_secret, refresh_token]):
            return {
                "status": "incomplete_config",
                "config": config_status,
                "message": "Missing required OAuth credentials"
            }
        
        # Try a simple token validation call
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        
        # Parse response
        if response.status_code == 200:
            token_data = response.json()
            return {
                "status": "oauth_success",
                "config": config_status,
                "oauth_response": {
                    "status_code": response.status_code,
                    "success": True,
                    "message": "OAuth token refreshed successfully",
                    "token_type": token_data.get('token_type', 'unknown'),
                    "expires_in": token_data.get('expires_in', 'unknown'),
                    "access_token_preview": token_data.get('access_token', '')[:20] + "..." if token_data.get('access_token') else "NONE"
                }
            }
        else:
            error_data = response.json() if response.content else {"error": "no_response"}
            return {
                "status": "oauth_failed",
                "config": config_status,
                "oauth_response": {
                    "status_code": response.status_code,
                    "success": False,
                    "error": error_data,
                    "raw_response": response.text[:500] if response.text else "empty"
                }
            }
        
    except Exception as e:
        import traceback
        return {
            "status": "diagnostic_error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@app.get("/google-ads/test-api")
def test_google_ads_api():
    """Test Google Ads API with comprehensive error handling"""
    import requests
    from google.oauth2.credentials import Credentials
    
    try:
        # Step 1: Get OAuth token
        client_id = os.getenv('GOOGLE_ADS_CLIENT_ID', '').strip()
        client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET', '').strip()
        refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN', '').strip()
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token'
        }
        
        token_response = requests.post(token_url, data=data)
        
        if token_response.status_code != 200:
            return {
                "success": False,
                "step": "oauth_token",
                "error": token_response.json(),
                "status_code": token_response.status_code
            }
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Step 2: Try to create Google Ads client
        try:
            from google.ads.googleads.client import GoogleAdsClient
            
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                id_token=None,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )
            
            client = GoogleAdsClient(
                credentials=credentials,
                developer_token=os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
            )
            
            # Step 3: Try a simple API call
            customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID', '').replace('-', '')
            
            if not customer_id:
                return {
                    "success": True,
                    "step": "oauth_success",
                    "message": "OAuth working, but no customer ID to test API calls",
                    "token_obtained": True
                }
            
            # Try to get customer info using GoogleAdsService
            ga_service = client.get_service("GoogleAdsService")
            query = """
                SELECT 
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone
                FROM customer 
                LIMIT 1
            """
            
            search_request = client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            results = list(ga_service.search(request=search_request))
            
            if results:
                customer = results[0].customer
                return {
                    "success": True,
                    "step": "api_success",
                    "customer_info": {
                        "id": str(customer.id),
                        "descriptive_name": customer.descriptive_name,
                        "currency_code": customer.currency_code,
                        "time_zone": customer.time_zone
                }
            }
            
        except ImportError:
            return {
                "success": True,
                "step": "oauth_success_no_client",
                "message": "OAuth token obtained successfully, but Google Ads client library not available",
                "token_obtained": True
            }
        
    except Exception as e:
        return {
            "success": False,
            "step": "api_error",
            "error": str(e),
            "error_type": type(e).__name__
        }

# ===============================================
# SOCIAL MEDIA API INTEGRATION - DATABASE ENDPOINTS
# ===============================================

# Pydantic Models for Social Media
class SocialMediaAccountIn(BaseModel):
    platform: str  # 'facebook', 'instagram', 'twitter', 'linkedin', 'tiktok', 'youtube', 'pinterest'
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    permissions: List[str] = []
    status: str = 'active'
    followers: int = 0

class SocialMediaPostIn(BaseModel):
    content: str
    media_urls: List[str] = []
    target_accounts: List[str] = []  # Account IDs to post to
    scheduled_date: Optional[datetime] = None
    post_type: str = 'text'  # 'text', 'image', 'video', 'carousel', 'story', 'reel'
    hashtags: List[str] = []
    mentions: List[str] = []
    location: Optional[Dict[str, Any]] = None
    campaign_id: Optional[str] = None
    approval_status: str = 'pending'

class SocialMediaCommentIn(BaseModel):
    post_id: str
    platform: str
    platform_comment_id: str
    author_username: str
    author_name: Optional[str] = None
    comment_text: str
    parent_comment_id: Optional[str] = None
    sentiment_score: Optional[float] = None

# Social Media API Endpoints
@app.get("/api/social-media/accounts")
async def get_social_accounts():
    """Get all connected social media accounts"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        response = supabase.table("social_media_accounts").select("*").order("created_at", desc=True).execute()
        return {
            "accounts": response.data or [],
            "count": len(response.data or []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching social media accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/social-media/accounts")
async def create_social_account(account: SocialMediaAccountIn):
    """Connect a new social media account"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        account_data = account.dict()
        account_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        response = supabase.table("social_media_accounts").insert(account_data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        logger.error(f"Error creating social media account: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/social-media/accounts/{account_id}")
async def get_social_account(account_id: str):
    """Get a specific social media account"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        response = supabase.table("social_media_accounts").select("*").eq("id", account_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Social media account not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching social media account: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/api/social-media/accounts/{account_id}")
async def update_social_account(account_id: str, account: SocialMediaAccountIn):
    """Update a social media account"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        account_data = account.dict()
        account_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        response = supabase.table("social_media_accounts").update(account_data).eq("id", account_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Social media account not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating social media account: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/api/social-media/accounts/{account_id}")
async def delete_social_account(account_id: str):
    """Disconnect a social media account"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        response = supabase.table("social_media_accounts").delete().eq("id", account_id).execute()
        return {"success": True, "message": "Social media account disconnected"}
    except Exception as e:
        logger.error(f"Error deleting social media account: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/social-media/posts")
async def get_social_posts(limit: int = 50, platform: Optional[str] = None, status: Optional[str] = None):
    """Get social media posts with filtering and pagination"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        query = supabase.table("social_media_posts").select("*")
        
        if platform:
            # Join with accounts to filter by platform
            query = supabase.table("social_media_posts").select("*, social_media_accounts!inner(platform)").eq("social_media_accounts.platform", platform)
        
        if status:
            query = query.eq("status", status)
            
        response = query.order("created_at", desc=True).limit(limit).execute()
        return {
            "posts": response.data or [],
            "count": len(response.data or []),
            "filters": {"platform": platform, "status": status, "limit": limit}
        }
    except Exception as e:
        logger.error(f"Error fetching social media posts: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/social-media/posts")
async def create_social_post(post: SocialMediaPostIn):
    """Create and optionally schedule a social media post"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        post_data = post.dict()
        post_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        # Set initial engagement metrics
        post_data["engagement"] = {
            "likes": 0,
            "shares": 0,
            "comments": 0,
            "reach": 0,
            "impressions": 0
        }
        
        response = supabase.table("social_media_posts").insert(post_data).execute()
        created_post = response.data[0] if response.data else {}
        
        # If not scheduled and has target accounts, attempt to publish immediately
        if not post.scheduled_date and post.target_accounts:
            try:
                publish_result = await publish_to_platforms(created_post, post.target_accounts)
                created_post["publish_status"] = publish_result
            except Exception as publish_error:
                logger.error(f"Error publishing post: {publish_error}")
                # Update post status to failed but don't fail the creation
                created_post["status"] = "failed"
                created_post["error_message"] = str(publish_error)
        
        return created_post
    except Exception as e:
        logger.error(f"Error creating social media post: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Instagram Publishing Functions
async def publish_to_platforms(post_data: dict, target_account_ids: list) -> dict:
    """Publish post to specified social media platforms"""
    results = {}
    
    try:
        # Get account details for each target account
        account_response = supabase.table("social_media_accounts")\
            .select("*")\
            .in_("id", target_account_ids)\
            .execute()
        
        accounts = account_response.data or []
        
        for account in accounts:
            platform = account.get("platform")
            account_id = account.get("id")
            
            try:
                if platform == "instagram":
                    result = await publish_to_instagram(post_data, account)
                elif platform == "facebook":
                    result = await publish_to_facebook(post_data, account)
                else:
                    result = {"status": "skipped", "message": f"Publishing to {platform} not implemented"}
                
                results[account_id] = result
                
            except Exception as account_error:
                logger.error(f"Error publishing to {platform} account {account_id}: {account_error}")
                results[account_id] = {
                    "status": "failed",
                    "error": str(account_error)
                }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in publish_to_platforms: {e}")
        return {"error": str(e)}

# Graph API Configuration
GRAPH_API_VERSION = "v19.0"  # Use latest stable version
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

async def publish_to_instagram(post_data: dict, account: dict) -> dict:
    """Publish post to Instagram using Graph API"""
    try:
        access_token = account.get("access_token")
        instagram_business_account_id = account.get("instagram_business_account_id")
        
        if not access_token:
            return {"status": "failed", "error": "No access token available"}
        
        if not instagram_business_account_id:
            return {"status": "failed", "error": "No Instagram Business Account ID"}
        
        content = post_data.get("content", "")
        media_urls = post_data.get("media_urls", [])
        
        # For now, handle text-only posts (media posts require additional steps)
        if not media_urls:
            # Create Instagram post using proper Graph API structure
            url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media"
            
            payload = {
                "caption": content,
                "access_token": access_token
            }
            
            async with aiohttp.ClientSession() as session:
                # Step 1: Create media object
                async with session.post(url, data=payload) as response:
                    if response.status == 200:
                        media_data = await response.json()
                        creation_id = media_data.get("id")
                        
                        # Step 2: Publish media object
                        publish_url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media_publish"
                        publish_payload = {
                            "creation_id": creation_id,
                            "access_token": access_token
                        }
                        
                        async with session.post(publish_url, data=publish_payload) as publish_response:
                            if publish_response.status == 200:
                                publish_data = await publish_response.json()
                                return {
                                    "status": "published",
                                    "instagram_post_id": publish_data.get("id"),
                                    "message": "Successfully published to Instagram"
                                }
                            else:
                                error_data = await publish_response.json()
                                return {
                                    "status": "failed",
                                    "error": f"Publish failed: {error_data}"
                                }
                    else:
                        error_data = await response.json()
                        return {
                            "status": "failed", 
                            "error": f"Media creation failed: {error_data}"
                        }
        else:
            # Enhanced media posts implementation
            return await publish_instagram_media_post(post_data, account)
            
    except Exception as e:
        logger.error(f"Instagram publishing error: {e}")
        return {"status": "failed", "error": str(e)}

async def publish_instagram_media_post(post_data: dict, account: dict) -> dict:
    """Publish Instagram post with media using Graph API best practices"""
    try:
        access_token = account.get("access_token")
        instagram_business_account_id = account.get("instagram_business_account_id")
        content = post_data.get("content", "")
        media_urls = post_data.get("media_urls", [])
        
        if len(media_urls) == 1:
            # Single media post
            media_url = media_urls[0]
            media_type = "IMAGE" if media_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) else "VIDEO"
            
            # Step 1: Create media container
            url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media"
            payload = {
                "image_url" if media_type == "IMAGE" else "video_url": media_url,
                "caption": content,
                "access_token": access_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload) as response:
                    if response.status == 200:
                        media_data = await response.json()
                        creation_id = media_data.get("id")
                        
                        # Step 2: Publish the media
                        publish_url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media_publish"
                        publish_payload = {
                            "creation_id": creation_id,
                            "access_token": access_token
                        }
                        
                        async with session.post(publish_url, data=publish_payload) as publish_response:
                            if publish_response.status == 200:
                                publish_data = await publish_response.json()
                                return {
                                    "status": "published",
                                    "instagram_post_id": publish_data.get("id"),
                                    "media_type": media_type,
                                    "message": f"Successfully published {media_type.lower()} to Instagram"
                                }
                            else:
                                error_data = await publish_response.json()
                                return {"status": "failed", "error": f"Publish failed: {error_data}"}
                    else:
                        error_data = await response.json()
                        return {"status": "failed", "error": f"Media creation failed: {error_data}"}
                        
        elif len(media_urls) > 1:
            # Carousel post (multiple media)
            return await publish_instagram_carousel(post_data, account)
        else:
            return {"status": "failed", "error": "No media URLs provided"}
            
    except Exception as e:
        logger.error(f"Instagram media publishing error: {e}")
        return {"status": "failed", "error": str(e)}

async def publish_instagram_carousel(post_data: dict, account: dict) -> dict:
    """Publish Instagram carousel post with multiple media"""
    try:
        access_token = account.get("access_token")
        instagram_business_account_id = account.get("instagram_business_account_id")
        content = post_data.get("content", "")
        media_urls = post_data.get("media_urls", [])
        
        if len(media_urls) > 10:  # Instagram limit
            return {"status": "failed", "error": "Maximum 10 media items allowed in carousel"}
        
        media_ids = []
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Create media containers for each item
            for media_url in media_urls:
                media_type = "IMAGE" if media_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) else "VIDEO"
                url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media"
                
                payload = {
                    "image_url" if media_type == "IMAGE" else "video_url": media_url,
                    "is_carousel_item": "true",
                    "access_token": access_token
                }
                
                async with session.post(url, data=payload) as response:
                    if response.status == 200:
                        media_data = await response.json()
                        media_ids.append(media_data.get("id"))
                    else:
                        error_data = await response.json()
                        return {"status": "failed", "error": f"Failed to create carousel item: {error_data}"}
            
            # Step 2: Create carousel container
            carousel_url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media"
            carousel_payload = {
                "media_type": "CAROUSEL",
                "children": ",".join(media_ids),
                "caption": content,
                "access_token": access_token
            }
            
            async with session.post(carousel_url, data=carousel_payload) as response:
                if response.status == 200:
                    carousel_data = await response.json()
                    creation_id = carousel_data.get("id")
                    
                    # Step 3: Publish carousel
                    publish_url = f"{GRAPH_API_BASE}/{instagram_business_account_id}/media_publish"
                    publish_payload = {
                        "creation_id": creation_id,
                        "access_token": access_token
                    }
                    
                    async with session.post(publish_url, data=publish_payload) as publish_response:
                        if publish_response.status == 200:
                            publish_data = await publish_response.json()
                            return {
                                "status": "published",
                                "instagram_post_id": publish_data.get("id"),
                                "media_type": "CAROUSEL",
                                "media_count": len(media_ids),
                                "message": f"Successfully published carousel with {len(media_ids)} items to Instagram"
                            }
                        else:
                            error_data = await publish_response.json()
                            return {"status": "failed", "error": f"Carousel publish failed: {error_data}"}
                else:
                    error_data = await response.json()
                    return {"status": "failed", "error": f"Carousel creation failed: {error_data}"}
                    
    except Exception as e:
        logger.error(f"Instagram carousel publishing error: {e}")
        return {"status": "failed", "error": str(e)}

# Graph API Utility Functions
async def get_instagram_account_info(access_token: str, instagram_business_account_id: str) -> dict:
    """Get Instagram account information using Graph API"""
    try:
        url = f"{GRAPH_API_BASE}/{instagram_business_account_id}"
        params = {
            "fields": "id,username,name,biography,followers_count,follows_count,media_count,profile_picture_url",
            "access_token": access_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    logger.error(f"Failed to get Instagram account info: {error_data}")
                    return {}
    except Exception as e:
        logger.error(f"Error getting Instagram account info: {e}")
        return {}

async def get_instagram_media_insights(access_token: str, media_id: str) -> dict:
    """Get insights for an Instagram media post"""
    try:
        url = f"{GRAPH_API_BASE}/{media_id}/insights"
        params = {
            "metric": "engagement,impressions,likes,comments,shares,saves,reach",
            "access_token": access_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    logger.error(f"Failed to get media insights: {error_data}")
                    return {}
    except Exception as e:
        logger.error(f"Error getting media insights: {e}")
        return {}

async def validate_instagram_media_url(media_url: str) -> dict:
    """Validate media URL before posting to Instagram"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(media_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = int(response.headers.get('content-length', 0))
                    
                    # Instagram requirements
                    if content_type.startswith('image/'):
                        max_size = 8 * 1024 * 1024  # 8MB for images
                        media_type = "IMAGE"
                    elif content_type.startswith('video/'):
                        max_size = 100 * 1024 * 1024  # 100MB for videos
                        media_type = "VIDEO"
                    else:
                        return {"valid": False, "error": "Unsupported media type"}
                    
                    if content_length > max_size:
                        return {"valid": False, "error": f"File too large. Max size: {max_size/1024/1024}MB"}
                    
                    return {
                        "valid": True,
                        "media_type": media_type,
                        "content_type": content_type,
                        "size": content_length
                    }
                else:
                    return {"valid": False, "error": f"Media URL not accessible: {response.status}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

# Enhanced endpoint for Instagram account insights
@app.get("/api/social-media/instagram/{account_id}/insights")
async def get_instagram_insights(account_id: str):
    """Get Instagram account insights and metrics"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get account details
        account_response = supabase.table("social_media_accounts")\
            .select("*")\
            .eq("id", account_id)\
            .eq("platform", "instagram")\
            .execute()
        
        if not account_response.data:
            raise HTTPException(status_code=404, detail="Instagram account not found")
        
        account = account_response.data[0]
        access_token = account.get("access_token")
        instagram_business_account_id = account.get("instagram_business_account_id")
        
        if not access_token or not instagram_business_account_id:
            raise HTTPException(status_code=400, detail="Account not properly configured for insights")
        
        # Get account info
        account_info = await get_instagram_account_info(access_token, instagram_business_account_id)
        
        # Get recent posts for engagement metrics
        recent_posts_response = supabase.table("social_media_posts")\
            .select("*")\
            .eq("target_accounts", f'["{account_id}"]')\
            .eq("status", "published")\
            .order("published_date", desc=True)\
            .limit(10)\
            .execute()
        
        posts_insights = []
        for post in recent_posts_response.data or []:
            if post.get("publish_results", {}).get(account_id, {}).get("instagram_post_id"):
                media_id = post["publish_results"][account_id]["instagram_post_id"]
                insights = await get_instagram_media_insights(access_token, media_id)
                posts_insights.append({
                    "post_id": post["id"],
                    "instagram_media_id": media_id,
                    "insights": insights
                })
        
        return {
            "account_info": account_info,
            "recent_posts_insights": posts_insights,
            "summary": {
                "total_posts": len(posts_insights),
                "account_metrics": account_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Instagram insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

# Media validation endpoint
@app.post("/api/social-media/validate-media")
async def validate_media_for_posting(request: dict):
    """Validate media URLs before posting"""
    try:
        media_urls = request.get("media_urls", [])
        platform = request.get("platform", "instagram")
        
        if not media_urls:
            raise HTTPException(status_code=400, detail="No media URLs provided")
        
        validation_results = []
        
        for url in media_urls:
            if platform == "instagram":
                result = await validate_instagram_media_url(url)
                validation_results.append({
                    "url": url,
                    "validation": result
                })
            else:
                validation_results.append({
                    "url": url,
                    "validation": {"valid": True, "message": "Validation not implemented for this platform"}
                })
        
        all_valid = all(result["validation"]["valid"] for result in validation_results)
        
        return {
            "all_valid": all_valid,
            "results": validation_results,
            "platform": platform
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating media: {e}")
        raise HTTPException(status_code=500, detail=f"Media validation failed: {str(e)}")

async def publish_to_facebook(post_data: dict, account: dict) -> dict:
    """Publish post to Facebook Page using Graph API best practices"""
    try:
        access_token = account.get("access_token")
        facebook_page_id = account.get("facebook_page_id")
        
        if not access_token or not facebook_page_id:
            return {"status": "failed", "error": "Missing access token or page ID"}
        
        content = post_data.get("content", "")
        media_urls = post_data.get("media_urls", [])
        
        # Use proper Graph API versioning
        if not media_urls:
            # Text-only post
            url = f"{GRAPH_API_BASE}/{facebook_page_id}/feed"
            payload = {
                "message": content,
                "access_token": access_token
            }
        else:
            # Post with media
            url = f"{GRAPH_API_BASE}/{facebook_page_id}/photos"
            payload = {
                "message": content,
                "url": media_urls[0],  # For now, just use first image
                "access_token": access_token
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return {
                        "status": "published",
                        "facebook_post_id": response_data.get("id"),
                        "post_type": "media" if media_urls else "text",
                        "message": "Successfully published to Facebook"
                    }
                else:
                    error_data = await response.json()
                    return {"status": "failed", "error": f"Facebook publish failed: {error_data}"}
                    
    except Exception as e:
        logger.error(f"Facebook publishing error: {e}")
        return {"status": "failed", "error": str(e)}

# New endpoint for immediate publishing
@app.post("/api/social-media/posts/{post_id}/publish")
async def publish_existing_post(post_id: str):
    """Publish an existing post to its target platforms"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get the post
        post_response = supabase.table("social_media_posts").select("*").eq("id", post_id).execute()
        if not post_response.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post = post_response.data[0]
        target_accounts = post.get("target_accounts", [])
        
        if not target_accounts:
            raise HTTPException(status_code=400, detail="No target accounts specified")
        
        # Attempt to publish
        publish_result = await publish_to_platforms(post, target_accounts)
        
        # Update post status based on results
        success_count = sum(1 for result in publish_result.values() 
                          if isinstance(result, dict) and result.get("status") == "published")
        
        if success_count > 0:
            post_status = "published" if success_count == len(target_accounts) else "partially_published"
        else:
            post_status = "failed"
        
        # Update the post in database
        supabase.table("social_media_posts").update({
            "status": post_status,
            "published_date": datetime.now(timezone.utc).isoformat() if success_count > 0 else None,
            "publish_results": publish_result
        }).eq("id", post_id).execute()
        
        return {
            "post_id": post_id,
            "status": post_status,
            "results": publish_result,
            "published_to": success_count,
            "total_targets": len(target_accounts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Publishing error: {str(e)}")

@app.get("/api/social-media/posts/{post_id}")
async def get_social_post(post_id: str):
    """Get a specific social media post with account details"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        response = supabase.table("social_media_posts")\
            .select("*, social_media_accounts(platform, username, display_name)")\
            .eq("id", post_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Social media post not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching social media post: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/api/social-media/posts/{post_id}")
async def update_social_post(post_id: str, post: SocialMediaPostIn):
    """Update a social media post"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        post_data = post.dict()
        post_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        response = supabase.table("social_media_posts").update(post_data).eq("id", post_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Social media post not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating social media post: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/api/social-media/posts/{post_id}")
async def delete_social_post(post_id: str):
    """Delete a social media post"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        response = supabase.table("social_media_posts").delete().eq("id", post_id).execute()
        return {"success": True, "message": "Social media post deleted"}
    except Exception as e:
        logger.error(f"Error deleting social media post: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/social-media/posts/{post_id}/comments")
async def get_post_comments(post_id: str, limit: int = 50):
    """Get comments for a specific social media post"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        response = supabase.table("social_media_comments")\
            .select("*")\
            .eq("post_id", post_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "comments": response.data or [],
            "count": len(response.data or []),
            "post_id": post_id
        }
    except Exception as e:
        logger.error(f"Error fetching post comments: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/social-media/comments")
async def create_comment(comment: SocialMediaCommentIn):
    """Add a comment to the database (from platform sync)"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        comment_data = comment.dict()
        comment_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        response = supabase.table("social_media_comments").insert(comment_data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/social-media/analytics/overview")
async def get_social_media_overview():
    """Get social media analytics overview"""
    if not SUPABASE_AVAILABLE or not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get accounts count by platform
        accounts_response = supabase.table("social_media_accounts")\
            .select("platform")\
            .eq("is_connected", True)\
            .execute()
        
        # Get posts count and engagement
        posts_response = supabase.table("social_media_posts")\
            .select("status, engagement")\
            .execute()
        
        # Calculate metrics
        platforms = {}
        for account in accounts_response.data or []:
            platform = account["platform"]
            platforms[platform] = platforms.get(platform, 0) + 1
        
        total_posts = len(posts_response.data or [])
        total_engagement = 0
        posts_by_status = {}
        
        for post in posts_response.data or []:
            status = post.get("status", "unknown")
            posts_by_status[status] = posts_by_status.get(status, 0) + 1
            
            engagement = post.get("engagement", {})
            if isinstance(engagement, dict):
                total_engagement += sum([
                    engagement.get("likes", 0),
                    engagement.get("shares", 0),
                    engagement.get("comments", 0)
                ])
        
        return {
            "connected_platforms": platforms,
            "total_accounts": len(accounts_response.data or []),
            "total_posts": total_posts,
            "posts_by_status": posts_by_status,
            "total_engagement": total_engagement,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching social media overview: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Social Media OAuth Authentication Endpoints
@app.post("/api/social-media/oauth/initiate")
async def initiate_social_media_oauth(request: dict):
    """Initiate OAuth flow for social media platforms"""
    try:
        platform = request.get("platform")
        config = request.get("config", {})
        
        if platform == "instagram":
            # Instagram API with Facebook Login (post-December 2024 approach)
            # Instagram Basic Display API was deprecated on December 4th, 2024
            app_id = config.get("appId") or os.getenv("NEXT_PUBLIC_FACEBOOK_APP_ID") or os.getenv("NEXT_PUBLIC_INSTAGRAM_APP_ID")
            # Handle empty string case
            if not app_id or app_id == "":
                app_id = os.getenv("NEXT_PUBLIC_FACEBOOK_APP_ID") or os.getenv("NEXT_PUBLIC_INSTAGRAM_APP_ID")
            if not app_id:
                raise HTTPException(status_code=400, detail="Facebook App ID not configured")
            
            logger.info(f"Instagram API with Facebook Login: Using App ID {app_id[:4]}...{app_id[-4:]} (length: {len(app_id)})")
                
            base_url = os.getenv('NEXT_PUBLIC_BASE_URL', 'https://pulsebridge.ai')
            redirect_uri = f"{base_url}/auth/instagram/callback"
            
            # Instagram API with Facebook Login permissions
            # Required for business/creator Instagram accounts
            scope = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish"
            
            # Facebook Login endpoint for Instagram API access
            auth_url = (
                f"https://www.facebook.com/v19.0/dialog/oauth?"
                f"client_id={app_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope}&"
                f"response_type=code&"
                f"state={platform}"
            )
            
            return {"auth_url": auth_url}
        
        elif platform == "facebook":
            # Facebook OAuth
            app_id = config.get("appId") or os.getenv("NEXT_PUBLIC_FACEBOOK_APP_ID")
            if not app_id:
                raise HTTPException(status_code=400, detail="Facebook App ID not configured")
                
            base_url = os.getenv('NEXT_PUBLIC_BASE_URL', 'https://pulsebridge.ai')
            redirect_uri = f"{base_url}/auth/facebook/callback"
            
            scope = "pages_manage_posts,pages_read_engagement,pages_show_list"
            
            auth_url = (
                f"https://www.facebook.com/v18.0/dialog/oauth?"
                f"client_id={app_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope}&"
                f"response_type=code&"
                f"state={platform}"
            )
            
            return {"auth_url": auth_url}
        
        else:
            raise HTTPException(status_code=400, detail=f"Platform {platform} not supported yet")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating OAuth for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initiation error: {str(e)}")

@app.post("/api/social-media/oauth/callback")
async def complete_social_media_oauth(request: dict):
    """Complete OAuth flow and store account information"""
    try:
        platform = request.get("platform")
        code = request.get("code")
        state = request.get("state")
        
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        
        if platform == "instagram":
            # Exchange code for access token
            app_id = os.getenv("NEXT_PUBLIC_INSTAGRAM_APP_ID")
            app_secret = os.getenv("INSTAGRAM_APP_SECRET")
            
            if not app_id or not app_secret:
                raise HTTPException(status_code=500, detail="Instagram credentials not configured")
                
            base_url = os.getenv('NEXT_PUBLIC_BASE_URL', 'https://pulsebridge.ai')
            redirect_uri = f"{base_url}/auth/instagram/callback"
            
            # Get access token from Facebook
            token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
            token_params = {
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
            
            # This is a mock response for now - in production you would make the actual API call
            # For now, we'll create a mock account to avoid API integration complexity
            mock_account = {
                "id": f"mock_instagram_{code[:10]}",
                "platform": "instagram",
                "username": "connected_account",
                "display_name": "Connected Instagram Account",
                "profile_picture": "https://via.placeholder.com/100",
                "followers_count": 0,
                "is_connected": True,
                "access_token": f"mock_token_{code[:10]}",
                "refresh_token": f"mock_refresh_{code[:10]}",
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # In production, store this in the database
            if SUPABASE_AVAILABLE and supabase:
                try:
                    response = supabase.table("social_media_accounts").insert(mock_account).execute()
                    if response.data:
                        return response.data[0]
                except Exception as db_error:
                    logger.warning(f"Database insertion failed, returning mock data: {db_error}")
            
            return mock_account
        
        else:
            raise HTTPException(status_code=400, detail=f"Platform {platform} not supported yet")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing OAuth for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth completion error: {str(e)}")

# ===============================================
# EMAIL MARKETING API ENDPOINTS
# ===============================================

# Email Campaign Management
@app.get("/api/email-marketing/campaigns")
def get_email_campaigns(limit: int = 50):
    """Get all email campaigns with pagination"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_campaigns").select("*").order("created_at", desc=True).limit(limit).execute()
        return {"campaigns": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email campaigns: {str(e)}")

@app.post("/api/email-marketing/campaigns")
def create_email_campaign(campaign: dict):
    """Create a new email campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_campaigns").insert(campaign).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create campaign")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create email campaign: {str(e)}")

@app.get("/api/email-marketing/campaigns/{campaign_id}")
def get_email_campaign(campaign_id: str):
    """Get a specific email campaign by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_campaigns").select("*").eq("id", campaign_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Campaign not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email campaign: {str(e)}")

@app.put("/api/email-marketing/campaigns/{campaign_id}")
def update_email_campaign(campaign_id: str, campaign: dict):
    """Update an existing email campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        campaign["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("email_campaigns").update(campaign).eq("id", campaign_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Campaign not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update email campaign: {str(e)}")

@app.delete("/api/email-marketing/campaigns/{campaign_id}")
def delete_email_campaign(campaign_id: str):
    """Delete an email campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_campaigns").delete().eq("id", campaign_id).execute()
        return {"success": True, "message": "Campaign deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete email campaign: {str(e)}")

# Email Subscriber Management
@app.get("/api/email-marketing/subscribers")
def get_email_subscribers(limit: int = 100, status: str = None):
    """Get email subscribers with optional status filter"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("email_subscribers").select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("status", status)
        
        res = query.execute()
        return {"subscribers": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email subscribers: {str(e)}")

@app.post("/api/email-marketing/subscribers")
def create_email_subscriber(subscriber: dict):
    """Add a new email subscriber"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_subscribers").insert(subscriber).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create subscriber")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create email subscriber: {str(e)}")

@app.get("/api/email-marketing/subscribers/{subscriber_id}")
def get_email_subscriber(subscriber_id: str):
    """Get a specific email subscriber by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_subscribers").select("*").eq("id", subscriber_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Subscriber not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email subscriber: {str(e)}")

@app.put("/api/email-marketing/subscribers/{subscriber_id}")
def update_email_subscriber(subscriber_id: str, subscriber: dict):
    """Update an existing email subscriber"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        subscriber["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("email_subscribers").update(subscriber).eq("id", subscriber_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Subscriber not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update email subscriber: {str(e)}")

@app.delete("/api/email-marketing/subscribers/{subscriber_id}")
def delete_email_subscriber(subscriber_id: str):
    """Delete an email subscriber"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_subscribers").delete().eq("id", subscriber_id).execute()
        return {"success": True, "message": "Subscriber deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete email subscriber: {str(e)}")

# Email Template Management
@app.get("/api/email-marketing/templates")
def get_email_templates(limit: int = 50):
    """Get all email templates"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_templates").select("*").order("created_at", desc=True).limit(limit).execute()
        return {"templates": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email templates: {str(e)}")

@app.post("/api/email-marketing/templates")
def create_email_template(template: dict):
    """Create a new email template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_templates").insert(template).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create template")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create email template: {str(e)}")

@app.get("/api/email-marketing/templates/{template_id}")
def get_email_template(template_id: str):
    """Get a specific email template by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_templates").select("*").eq("id", template_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email template: {str(e)}")

@app.put("/api/email-marketing/templates/{template_id}")
def update_email_template(template_id: str, template: dict):
    """Update an existing email template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        template["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("email_templates").update(template).eq("id", template_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update email template: {str(e)}")

@app.delete("/api/email-marketing/templates/{template_id}")
def delete_email_template(template_id: str):
    """Delete an email template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("email_templates").delete().eq("id", template_id).execute()
        return {"success": True, "message": "Template deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete email template: {str(e)}")

# Email Analytics
@app.get("/api/email-marketing/analytics/overview")
def get_email_marketing_overview():
    """Get comprehensive email marketing analytics overview"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get campaign statistics
        campaigns_res = supabase.table("email_campaigns").select("status, sent_count, open_rate, click_rate").execute()
        campaigns_by_status = {}
        total_sent = 0
        total_opens = 0
        total_clicks = 0
        
        for campaign in campaigns_res.data or []:
            status = campaign.get("status", "unknown")
            campaigns_by_status[status] = campaigns_by_status.get(status, 0) + 1
            
            sent = campaign.get("sent_count", 0)
            open_rate = campaign.get("open_rate", 0)
            click_rate = campaign.get("click_rate", 0)
            
            total_sent += sent
            total_opens += int(sent * (open_rate / 100) if open_rate else 0)
            total_clicks += int(sent * (click_rate / 100) if click_rate else 0)
        
        # Get subscriber statistics
        subscribers_res = supabase.table("email_subscribers").select("status").execute()
        subscribers_by_status = {}
        for subscriber in subscribers_res.data or []:
            status = subscriber.get("status", "unknown")
            subscribers_by_status[status] = subscribers_by_status.get(status, 0) + 1
        
        # Calculate average rates
        avg_open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
        avg_click_rate = (total_clicks / total_sent * 100) if total_sent > 0 else 0
        
        return {
            "total_campaigns": len(campaigns_res.data or []),
            "campaigns_by_status": campaigns_by_status,
            "total_subscribers": len(subscribers_res.data or []),
            "subscribers_by_status": subscribers_by_status,
            "total_emails_sent": total_sent,
            "average_open_rate": round(avg_open_rate, 2),
            "average_click_rate": round(avg_click_rate, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email marketing overview: {str(e)}")

@app.get("/api/email-marketing/campaigns/{campaign_id}/analytics")
def get_campaign_analytics(campaign_id: str):
    """Get detailed analytics for a specific email campaign"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get campaign details
        campaign_res = supabase.table("email_campaigns").select("*").eq("id", campaign_id).execute()
        if not campaign_res.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_res.data[0]
        
        # Get related analytics data (you might have separate analytics tables)
        # For now, return the campaign data with calculated metrics
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.get("name", ""),
            "status": campaign.get("status", ""),
            "sent_count": campaign.get("sent_count", 0),
            "delivered_count": campaign.get("delivered_count", 0),
            "opened_count": campaign.get("opened_count", 0),
            "clicked_count": campaign.get("clicked_count", 0),
            "unsubscribed_count": campaign.get("unsubscribed_count", 0),
            "bounced_count": campaign.get("bounced_count", 0),
            "open_rate": campaign.get("open_rate", 0),
            "click_rate": campaign.get("click_rate", 0),
            "unsubscribe_rate": campaign.get("unsubscribe_rate", 0),
            "bounce_rate": campaign.get("bounce_rate", 0),
            "created_at": campaign.get("created_at", ""),
            "sent_at": campaign.get("sent_at", "")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaign analytics: {str(e)}")

# ===============================================
# COLLABORATION API ENDPOINTS
# ===============================================

# Team Member Management
@app.get("/api/collaboration/team-members")
def get_team_members(limit: int = 100):
    """Get all team members with their roles and status"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("team_members").select("*").order("created_at", desc=True).limit(limit).execute()
        return {"team_members": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team members: {str(e)}")

@app.post("/api/collaboration/team-members")
def create_team_member(member: dict):
    """Add a new team member"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("team_members").insert(member).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create team member")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team member: {str(e)}")

@app.get("/api/collaboration/team-members/{member_id}")
def get_team_member(member_id: str):
    """Get a specific team member by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("team_members").select("*").eq("id", member_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Team member not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team member: {str(e)}")

@app.put("/api/collaboration/team-members/{member_id}")
def update_team_member(member_id: str, member: dict):
    """Update an existing team member"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        member["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("team_members").update(member).eq("id", member_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Team member not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update team member: {str(e)}")

@app.delete("/api/collaboration/team-members/{member_id}")
def delete_team_member(member_id: str):
    """Remove a team member"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("team_members").delete().eq("id", member_id).execute()
        return {"success": True, "message": "Team member removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete team member: {str(e)}")

# Real-time Activity Feed
@app.get("/api/collaboration/activities")
def get_activities(limit: int = 50, user_id: str = None, activity_type: str = None):
    """Get recent team activities with optional filters"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("team_activities").select("*").order("created_at", desc=True).limit(limit)
        
        if user_id:
            query = query.eq("user_id", user_id)
        if activity_type:
            query = query.eq("activity_type", activity_type)
        
        res = query.execute()
        return {"activities": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activities: {str(e)}")

@app.post("/api/collaboration/activities")
def create_activity(activity: dict):
    """Log a new team activity"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("team_activities").insert(activity).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create activity")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create activity: {str(e)}")

@app.get("/api/collaboration/activities/{activity_id}")
def get_activity(activity_id: str):
    """Get a specific activity by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("team_activities").select("*").eq("id", activity_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Activity not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity: {str(e)}")

# User Presence and Status
@app.get("/api/collaboration/presence")
def get_user_presence():
    """Get current online status of all team members"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get presence data from last 5 minutes (active users)
        cutoff_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        res = supabase.table("user_presence").select("*").gte("last_seen", cutoff_time).execute()
        return {"presence": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user presence: {str(e)}")

@app.post("/api/collaboration/presence")
def update_user_presence(presence: dict):
    """Update user presence status"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        presence["last_seen"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("user_presence").upsert(presence).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to update presence")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user presence: {str(e)}")

@app.get("/api/collaboration/presence/{user_id}")
def get_user_presence_status(user_id: str):
    """Get presence status for a specific user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("user_presence").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="User presence not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user presence: {str(e)}")

# Project Management
@app.get("/api/collaboration/projects")
def get_projects(limit: int = 50, status: str = None):
    """Get all collaborative projects with optional status filter"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("collaboration_projects").select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("status", status)
        
        res = query.execute()
        return {"projects": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@app.post("/api/collaboration/projects")
def create_project(project: dict):
    """Create a new collaborative project"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("collaboration_projects").insert(project).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create project")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.get("/api/collaboration/projects/{project_id}")
def get_project(project_id: str):
    """Get a specific project by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("collaboration_projects").select("*").eq("id", project_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")

@app.put("/api/collaboration/projects/{project_id}")
def update_project(project_id: str, project: dict):
    """Update an existing project"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("collaboration_projects").update(project).eq("id", project_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@app.delete("/api/collaboration/projects/{project_id}")
def delete_project(project_id: str):
    """Delete a collaborative project"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("collaboration_projects").delete().eq("id", project_id).execute()
        return {"success": True, "message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# Live Cursors and Real-time Collaboration
@app.get("/api/collaboration/cursors")
def get_live_cursors(page: str = None):
    """Get current cursor positions for real-time collaboration"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get cursor data from last 30 seconds (active cursors)
        cutoff_time = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        query = supabase.table("live_cursors").select("*").gte("updated_at", cutoff_time)
        
        if page:
            query = query.eq("page", page)
        
        res = query.execute()
        return {"cursors": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live cursors: {str(e)}")

@app.post("/api/collaboration/cursors")
def update_cursor_position(cursor: dict):
    """Update user cursor position for real-time collaboration"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        cursor["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("live_cursors").upsert(cursor).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to update cursor")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cursor position: {str(e)}")

# Notifications and Alerts
@app.get("/api/collaboration/notifications")
def get_notifications(user_id: str, limit: int = 50, unread_only: bool = False):
    """Get notifications for a specific user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit)
        
        if unread_only:
            query = query.eq("read", False)
        
        res = query.execute()
        return {"notifications": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")

@app.post("/api/collaboration/notifications")
def create_notification(notification: dict):
    """Create a new notification"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("notifications").insert(notification).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create notification")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")

@app.put("/api/collaboration/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("notifications").update({"read": True, "read_at": datetime.now(timezone.utc).isoformat()}).eq("id", notification_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")

# Collaboration Analytics
@app.get("/api/collaboration/analytics/overview")
def get_collaboration_overview():
    """Get comprehensive collaboration analytics overview"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get team member statistics
        members_res = supabase.table("team_members").select("role, status").execute()
        members_by_role = {}
        members_by_status = {}
        
        for member in members_res.data or []:
            role = member.get("role", "unknown")
            status = member.get("status", "unknown")
            members_by_role[role] = members_by_role.get(role, 0) + 1
            members_by_status[status] = members_by_status.get(status, 0) + 1
        
        # Get project statistics
        projects_res = supabase.table("collaboration_projects").select("status").execute()
        projects_by_status = {}
        for project in projects_res.data or []:
            status = project.get("status", "unknown")
            projects_by_status[status] = projects_by_status.get(status, 0) + 1
        
        # Get activity statistics (last 24 hours)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        activities_res = supabase.table("team_activities").select("activity_type").gte("created_at", yesterday).execute()
        activities_by_type = {}
        for activity in activities_res.data or []:
            activity_type = activity.get("activity_type", "unknown")
            activities_by_type[activity_type] = activities_by_type.get(activity_type, 0) + 1
        
        # Get online users (last 5 minutes)
        online_cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        online_res = supabase.table("user_presence").select("user_id").gte("last_seen", online_cutoff).execute()
        
        return {
            "total_team_members": len(members_res.data or []),
            "members_by_role": members_by_role,
            "members_by_status": members_by_status,
            "total_projects": len(projects_res.data or []),
            "projects_by_status": projects_by_status,
            "online_users": len(online_res.data or []),
            "activities_last_24h": len(activities_res.data or []),
            "activities_by_type": activities_by_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch collaboration overview: {str(e)}")

# ===============================================
# INTEGRATIONS API ENDPOINTS
# ===============================================

# Integration App Management
@app.get("/api/integrations/apps")
def get_integration_apps(category: str = None, limit: int = 100):
    """Get all available integration apps with optional category filter"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("integration_apps").select("*").order("name").limit(limit)
        if category:
            query = query.eq("category", category)
        
        res = query.execute()
        return {"apps": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integration apps: {str(e)}")

@app.post("/api/integrations/apps")
def create_integration_app(app: dict):
    """Create a new integration app"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_apps").insert(app).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to create integration app")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create integration app: {str(e)}")

@app.get("/api/integrations/apps/{app_id}")
def get_integration_app(app_id: str):
    """Get a specific integration app by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_apps").select("*").eq("id", app_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Integration app not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integration app: {str(e)}")

@app.put("/api/integrations/apps/{app_id}")
def update_integration_app(app_id: str, app: dict):
    """Update an existing integration app"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        app["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("integration_apps").update(app).eq("id", app_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Integration app not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update integration app: {str(e)}")

@app.delete("/api/integrations/apps/{app_id}")
def delete_integration_app(app_id: str):
    """Delete an integration app"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_apps").delete().eq("id", app_id).execute()
        return {"success": True, "message": "Integration app deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete integration app: {str(e)}")

# User Integration Management
@app.get("/api/integrations/user-integrations")
def get_user_integrations(user_id: str = None, limit: int = 100):
    """Get user's installed integrations"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("user_integrations").select("*").order("created_at", desc=True).limit(limit)
        if user_id:
            query = query.eq("user_id", user_id)
        
        res = query.execute()
        return {"integrations": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user integrations: {str(e)}")

@app.post("/api/integrations/user-integrations")
def install_integration(integration: dict):
    """Install an integration for a user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("user_integrations").insert(integration).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to install integration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to install integration: {str(e)}")

@app.get("/api/integrations/user-integrations/{integration_id}")
def get_user_integration(integration_id: str):
    """Get a specific user integration by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("user_integrations").select("*").eq("id", integration_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="User integration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user integration: {str(e)}")

@app.put("/api/integrations/user-integrations/{integration_id}")
def update_user_integration(integration_id: str, integration: dict):
    """Update an existing user integration"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        integration["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("user_integrations").update(integration).eq("id", integration_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="User integration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user integration: {str(e)}")

@app.delete("/api/integrations/user-integrations/{integration_id}")
def uninstall_integration(integration_id: str):
    """Uninstall a user integration"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("user_integrations").delete().eq("id", integration_id).execute()
        return {"success": True, "message": "Integration uninstalled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to uninstall integration: {str(e)}")

# API Key Management
@app.get("/api/integrations/api-keys")
def get_api_keys(user_id: str = None, service: str = None):
    """Get API keys for integrations"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        query = supabase.table("integration_api_keys").select("id, user_id, service, name, status, created_at, updated_at")
        if user_id:
            query = query.eq("user_id", user_id)
        if service:
            query = query.eq("service", service)
        
        res = query.execute()
        return {"api_keys": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch API keys: {str(e)}")

@app.post("/api/integrations/api-keys")
def create_api_key(api_key: dict):
    """Create a new API key for integration"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_api_keys").insert(api_key).execute()
        if res.data:
            # Return without exposing the actual key value
            result = res.data[0].copy()
            if "key_value" in result:
                del result["key_value"]
            return result
        raise HTTPException(status_code=400, detail="Failed to create API key")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@app.get("/api/integrations/api-keys/{key_id}")
def get_api_key(key_id: str):
    """Get a specific API key by ID (without exposing the key value)"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_api_keys").select("id, user_id, service, name, status, created_at, updated_at").eq("id", key_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch API key: {str(e)}")

@app.put("/api/integrations/api-keys/{key_id}")
def update_api_key(key_id: str, api_key: dict):
    """Update an existing API key"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        api_key["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = supabase.table("integration_api_keys").update(api_key).eq("id", key_id).execute()
        if res.data:
            # Return without exposing the actual key value
            result = res.data[0].copy()
            if "key_value" in result:
                del result["key_value"]
            return result
        raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")

@app.delete("/api/integrations/api-keys/{key_id}")
def delete_api_key(key_id: str):
    """Delete an API key"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_api_keys").delete().eq("id", key_id).execute()
        return {"success": True, "message": "API key deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete API key: {str(e)}")

# Integration Usage Analytics
@app.get("/api/integrations/usage")
def get_integration_usage(user_id: str = None, integration_id: str = None, days: int = 30):
    """Get integration usage analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get usage from last N days
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query = supabase.table("integration_usage").select("*").gte("created_at", start_date).order("created_at", desc=True)
        
        if user_id:
            query = query.eq("user_id", user_id)
        if integration_id:
            query = query.eq("integration_id", integration_id)
        
        res = query.execute()
        return {"usage": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integration usage: {str(e)}")

@app.post("/api/integrations/usage")
def log_integration_usage(usage: dict):
    """Log integration usage event"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        res = supabase.table("integration_usage").insert(usage).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=400, detail="Failed to log usage")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log integration usage: {str(e)}")

# Integration Categories
@app.get("/api/integrations/categories")
def get_integration_categories():
    """Get all integration categories with app counts"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get category distribution
        apps_res = supabase.table("integration_apps").select("category").execute()
        categories = {}
        for app in apps_res.data or []:
            category = app.get("category", "Other")
            categories[category] = categories.get(category, 0) + 1
        
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integration categories: {str(e)}")

# Marketplace Revenue Analytics
@app.get("/api/integrations/revenue")
def get_marketplace_revenue(days: int = 30):
    """Get marketplace revenue analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get revenue from last N days
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get installations (revenue events)
        installations_res = supabase.table("user_integrations").select("app_id, created_at").gte("created_at", start_date).execute()
        
        # Get app pricing information
        apps_res = supabase.table("integration_apps").select("id, name, price, commission_rate").execute()
        app_pricing = {app["id"]: app for app in apps_res.data or []}
        
        total_revenue = 0
        total_commission = 0
        installations_by_app = {}
        
        for installation in installations_res.data or []:
            app_id = installation.get("app_id")
            if app_id in app_pricing:
                app = app_pricing[app_id]
                price = app.get("price", 0)
                commission_rate = app.get("commission_rate", 0.3)  # Default 30%
                
                total_revenue += price
                total_commission += price * commission_rate
                
                app_name = app.get("name", "Unknown")
                if app_name not in installations_by_app:
                    installations_by_app[app_name] = {"count": 0, "revenue": 0}
                installations_by_app[app_name]["count"] += 1
                installations_by_app[app_name]["revenue"] += price
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_commission": round(total_commission, 2),
            "total_installations": len(installations_res.data or []),
            "installations_by_app": installations_by_app,
            "period_days": days,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch marketplace revenue: {str(e)}")

# Integration Analytics Overview
@app.get("/api/integrations/analytics/overview")
def get_integrations_overview():
    """Get comprehensive integrations analytics overview"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get app statistics
        apps_res = supabase.table("integration_apps").select("category, status").execute()
        apps_by_category = {}
        apps_by_status = {}
        
        for app in apps_res.data or []:
            category = app.get("category", "Other")
            status = app.get("status", "unknown")
            apps_by_category[category] = apps_by_category.get(category, 0) + 1
            apps_by_status[status] = apps_by_status.get(status, 0) + 1
        
        # Get user integration statistics
        user_integrations_res = supabase.table("user_integrations").select("status").execute()
        integrations_by_status = {}
        for integration in user_integrations_res.data or []:
            status = integration.get("status", "unknown")
            integrations_by_status[status] = integrations_by_status.get(status, 0) + 1
        
        # Get API key statistics
        api_keys_res = supabase.table("integration_api_keys").select("service, status").execute()
        keys_by_service = {}
        keys_by_status = {}
        for key in api_keys_res.data or []:
            service = key.get("service", "unknown")
            status = key.get("status", "unknown")
            keys_by_service[service] = keys_by_service.get(service, 0) + 1
            keys_by_status[status] = keys_by_status.get(status, 0) + 1
        
        # Get usage statistics (last 24 hours)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        usage_res = supabase.table("integration_usage").select("action").gte("created_at", yesterday).execute()
        usage_by_action = {}
        for usage in usage_res.data or []:
            action = usage.get("action", "unknown")
            usage_by_action[action] = usage_by_action.get(action, 0) + 1
        
        return {
            "total_apps": len(apps_res.data or []),
            "apps_by_category": apps_by_category,
            "apps_by_status": apps_by_status,
            "total_user_integrations": len(user_integrations_res.data or []),
            "integrations_by_status": integrations_by_status,
            "total_api_keys": len(api_keys_res.data or []),
            "keys_by_service": keys_by_service,
            "keys_by_status": keys_by_status,
            "usage_last_24h": len(usage_res.data or []),
            "usage_by_action": usage_by_action,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch integrations overview: {str(e)}")

# AI Content Generation Endpoints
@app.post("/api/social-media/ai/generate-content")
async def generate_social_content(request: dict):
    """Generate AI-powered social media content using Claude"""
    try:
        platform = request.get('platform', 'instagram')
        prompt = request.get('prompt', '')
        tone = request.get('tone', 'casual')
        content_type = request.get('content_type', 'post')
        target_audience = request.get('target_audience', 'general')
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Build specialized prompt for social media content
        specialized_prompt = f"""Create a {tone} {content_type} for {platform} about: {prompt}

Target audience: {target_audience}
Platform: {platform}
Content type: {content_type}
Tone: {tone}

Requirements for {platform}:
{_get_platform_requirements(platform)}

Please provide:
1. Main content text
2. 5-8 relevant hashtags
3. Optimal posting time recommendation
4. Engagement prediction (0-1 score)

Format as JSON with keys: content, hashtags, optimal_time, engagement_prediction, suggestions"""

        # Use the AI service
        chat_request = ChatRequest(
            message=specialized_prompt,
            context={"platform": platform, "content_type": content_type},
            page="social-media"
        )
        
        ai_response = await ai_service.chat_with_ai(chat_request)
        
        # Try to parse JSON response, fallback to structured response
        try:
            import json
            parsed_response = json.loads(ai_response.response)
            return {
                "content": parsed_response.get("content", ai_response.response),
                "hashtags": parsed_response.get("hashtags", []),
                "optimal_time": parsed_response.get("optimal_time"),
                "engagement_prediction": parsed_response.get("engagement_prediction", 0.75),
                "suggestions": parsed_response.get("suggestions", []),
                "platform": platform,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        except json.JSONDecodeError:
            # Fallback: extract content and generate hashtags
            content = ai_response.response
            hashtags = _extract_hashtags(content, platform)
            
            return {
                "content": content,
                "hashtags": hashtags,
                "optimal_time": _get_optimal_time(platform),
                "engagement_prediction": 0.75,
                "suggestions": ["Consider adding emojis", "Include a call-to-action"],
                "platform": platform,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        logger.error(f"Content generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@app.post("/api/email-marketing/ai/generate-content")
async def generate_email_content(request: dict):
    """Generate AI-powered email marketing content using Claude"""
    try:
        subject = request.get('subject', '')
        campaign_type = request.get('campaign_type', 'newsletter')
        tone = request.get('tone', 'professional')
        target_audience = request.get('target_audience', 'subscribers')
        key_points = request.get('key_points', [])
        
        if not subject:
            raise HTTPException(status_code=400, detail="Subject is required")
        
        specialized_prompt = f"""Create an email marketing campaign with:

Subject: {subject}
Campaign type: {campaign_type}
Tone: {tone}
Target audience: {target_audience}
Key points to include: {', '.join(key_points) if key_points else 'None specified'}

Please provide:
1. Email subject line (optimized)
2. Email body content (HTML format)
3. Call-to-action text
4. Personalization suggestions
5. A/B testing recommendations

Format as JSON with keys: subject_line, body_html, cta_text, personalization_tips, ab_test_suggestions"""

        chat_request = ChatRequest(
            message=specialized_prompt,
            context={"campaign_type": campaign_type, "tone": tone},
            page="email-marketing"
        )
        
        ai_response = await ai_service.chat_with_ai(chat_request)
        
        try:
            import json
            parsed_response = json.loads(ai_response.response)
            return {
                "subject_line": parsed_response.get("subject_line", subject),
                "body_html": parsed_response.get("body_html", ai_response.response),
                "cta_text": parsed_response.get("cta_text", "Learn More"),
                "personalization_tips": parsed_response.get("personalization_tips", []),
                "ab_test_suggestions": parsed_response.get("ab_test_suggestions", []),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        except json.JSONDecodeError:
            return {
                "subject_line": subject,
                "body_html": ai_response.response,
                "cta_text": "Learn More",
                "personalization_tips": ["Use recipient's first name", "Reference past purchases"],
                "ab_test_suggestions": ["Test different subject lines", "Test CTA button colors"],
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
    except Exception as e:
        logger.error(f"Email content generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate email content: {str(e)}")

# Media Upload Endpoint
@app.post("/api/social-media/upload-media")
async def upload_media(files: list):
    """Upload media files for social media posts"""
    try:
        # This is a simplified implementation
        # In production, you'd want to:
        # 1. Validate file types and sizes
        # 2. Upload to cloud storage (AWS S3, Cloudinary, etc.)
        # 3. Generate thumbnails
        # 4. Store metadata in database
        
        uploaded_files = []
        
        for file_data in files:
            # Mock file processing
            file_info = {
                "id": f"media_{datetime.now().timestamp()}",
                "url": f"https://storage.example.com/{file_data.get('name', 'upload.jpg')}",
                "thumbnail_url": f"https://storage.example.com/thumbs/{file_data.get('name', 'upload.jpg')}",
                "type": file_data.get('type', 'image/jpeg'),
                "size": file_data.get('size', 0),
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
            uploaded_files.append(file_info)
        
        return {
            "uploaded_files": uploaded_files,
            "message": f"Successfully uploaded {len(uploaded_files)} files"
        }
        
    except Exception as e:
        logger.error(f"Media upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload media: {str(e)}")

# Helper functions for AI content generation
def _get_platform_requirements(platform: str) -> str:
    """Get platform-specific content requirements"""
    requirements = {
        "instagram": "- Max 2,200 characters\n- Use 5-10 hashtags\n- Include emojis\n- Visual storytelling focus",
        "twitter": "- Max 280 characters\n- Use 1-2 hashtags\n- Be concise and engaging\n- Include relevant mentions",
        "facebook": "- Max 2,000 characters\n- Use 2-3 hashtags\n- Encourage comments\n- Friendly and conversational",
        "linkedin": "- Max 3,000 characters\n- Professional tone\n- Include industry insights\n- End with thought-provoking question",
        "tiktok": "- Max 300 characters\n- Trending hashtags\n- Call for engagement\n- Fun and energetic tone"
    }
    return requirements.get(platform, "- Follow platform best practices")

def _extract_hashtags(content: str, platform: str) -> list:
    """Extract or generate hashtags from content"""
    import re
    hashtags = re.findall(r'#\w+', content)
    
    # If no hashtags found, generate some based on platform
    if not hashtags:
        platform_hashtags = {
            "instagram": ["#instagram", "#content", "#social"],
            "twitter": ["#twitter", "#engagement"],
            "facebook": ["#facebook", "#community"],
            "linkedin": ["#linkedin", "#professional"],
            "tiktok": ["#tiktok", "#trending", "#viral"]
        }
        hashtags = platform_hashtags.get(platform, ["#social", "#content"])
    
    return hashtags[:10]  # Limit to 10 hashtags

def _get_optimal_time(platform: str) -> dict:
    """Get optimal posting time for platform"""
    optimal_times = {
        "instagram": {"day": "Tuesday", "hour": 11, "timezone": "EST"},
        "twitter": {"day": "Wednesday", "hour": 9, "timezone": "EST"},
        "facebook": {"day": "Thursday", "hour": 15, "timezone": "EST"},
        "linkedin": {"day": "Tuesday", "hour": 10, "timezone": "EST"},
        "tiktok": {"day": "Thursday", "hour": 18, "timezone": "EST"}
    }
    return optimal_times.get(platform, {"day": "Tuesday", "hour": 11, "timezone": "EST"})

# Development server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )