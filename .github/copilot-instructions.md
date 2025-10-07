# PulseBridge.ai FastAPI Backend - AI Coding Instructions

## 🎯 Project Overview

**PulseBridge.ai Autopilot API** - AI-autonomous marketing platform backend built with FastAPI, managing campaigns across Google Ads, Meta, LinkedIn, and Pinterest with intelligent decision-making capabilities.

**Production URL**: https://autopilot-api-1.onrender.com  
**Architecture**: FastAPI + Supabase + Multi-platform Ad APIs + Claude AI Integration  
**Status**: Production-ready with 60+ endpoints and comprehensive multi-platform support

## 🏗️ Critical Architecture Patterns

### **Modular FastAPI Structure**
The backend is contained in `app/main.py` (3,724 lines) with proper modular router imports:
```python
# Core routers (✅ All modules now exist as separate files)
from ai_endpoints import ai_router
from optimization_endpoints import router as optimization_router
from sync_endpoints import router as sync_router
from analytics_endpoints import router as analytics_router
from autonomous_decision_endpoints import router as autonomous_router
```

**✅ Fixed Architecture**: All imported modules now exist as separate files, properly organized and functional. The repository now has a clean modular structure with working imports.

### **Multi-Platform Integration Architecture**
```python
# Platform-specific endpoints follow consistent patterns:
@app.get("/{platform}-ads/status")        # Health checks
@app.get("/{platform}-ads/campaigns")     # Campaign listing
@app.get("/{platform}-ads/campaigns/{id}/performance")  # Performance data
@app.post("/{platform}-ads/campaigns")    # Campaign creation
```

Supported platforms: `google-ads`, `meta-ads`, `linkedin-ads`, `pinterest-ads`

### **Supabase Integration Pattern**
```python
# Always check SUPABASE_AVAILABLE before database operations
if not SUPABASE_AVAILABLE:
    raise HTTPException(status_code=503, detail="Database unavailable")

# Use environment variable fallback pattern
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
```

## 🔧 Development Workflows

### **Local Development Setup**
```bash
# Environment setup (Python 3.8+)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Environment Variables**
Required in `.env` file:
```properties
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key  # Primary
SUPABASE_ANON_KEY=fallback_key  # Fallback
ANTHROPIC_API_KEY=claude_ai_key
# Platform-specific API keys as needed
```

### **Deployment Pattern**
- **Primary**: Render.com deployment (autopilot-api-1.onrender.com)
- **Backup**: Vercel deployment configured (.vercel/project.json)
- **CORS**: Configured for https://pulsebridge.ai frontend

## 📊 Key Architectural Decisions

### **Router Organization**
Despite modular imports, most functionality is in `main.py`. When adding features:
1. Add endpoints directly to `main.py` initially
2. Extract to separate modules only when files become unwieldy
3. Maintain consistent `/api/v1` prefix for new APIs

### **Error Handling Pattern**
```python
# Standard error response pattern
try:
    # Operation
    result = await operation()
    return {"success": True, "data": result}
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")
```

### **Database Schema Assumptions**
Based on endpoint patterns, expect these Supabase tables:
- `campaigns` - Campaign data across platforms
- `performance_snapshots` - Historical performance data
- `leads` - Lead management
- Social media tables: `social_media_accounts`, `social_media_posts`, `social_media_comments`

## 🚨 Critical Integration Points

### **AI Chat Service Integration**
```python
# Claude AI integration pattern
@app.post("/api/v1/ai/chat")
async def ai_chat_endpoint(request: ChatRequest):
    # Uses ai_chat_service module for Claude integration
```

### **Cross-Platform Sync Engine**
The platform abstracts multiple ad platforms behind unified endpoints. Each platform integration follows the same pattern but may have different authentication and data structures.

### **Available Modules**
All required modules are now present and functional:
- ✅ `ai_endpoints.py`, `optimization_endpoints.py`, `sync_endpoints.py`
- ✅ `analytics_endpoints.py`, `autonomous_decision_endpoints.py`
- ✅ All platform integration modules (meta, linkedin, pinterest, google-ads)
- ✅ AI hybrid integration and risk management modules

## 💡 Development Guidelines

1. **Modular Architecture**: All endpoints are properly organized into separate router modules
2. **Import Reliability**: All module imports are now functional and tested
3. **Error Logging**: Use the configured logger for all error tracking
4. **Database Checks**: Always verify `SUPABASE_AVAILABLE` before database operations
5. **Platform Parity**: When adding features to one platform, consider implementing across all supported platforms

## 🎯 Architecture Status: ✅ FULLY RESOLVED

**October 6, 2025 - Major Restructuring Complete:**
- ✅ **All Missing Modules**: Copied from autopilot-web/backend and properly integrated
- ✅ **Import Resolution**: No more missing import errors
- ✅ **Production Stability**: Live API remains functional and responsive
- ✅ **Modular Structure**: Clean separation of concerns across all components
- ✅ **Development Ready**: AI agents can now work confidently with full module access

## 🔍 Debugging Endpoints
- `/health` - Basic health check
- `/debug/supabase` - Supabase connection status
- `/debug/tables` - Database table verification
- `/{platform}-ads/status` - Platform-specific health checks

This backend serves as the intelligence layer for PulseBridge.ai's autonomous marketing platform, requiring careful attention to multi-platform consistency and robust error handling patterns.