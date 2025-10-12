# 🔧 Quick Fix for 404 Errors

## **Most Likely Causes**

### **1. Missing Root Endpoint**
If visiting your site's root URL gives 404, add this:

```python
# Add to app/main.py (near the top, after app = FastAPI())

@app.get("/")
async def root():
    """API Root - Welcome message"""
    return {
        "message": "PulseBridge.ai Marketing Autopilot API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

### **2. CORS Issues (Frontend Can't Reach API)**

Add CORS middleware if frontend getting blocked:

```python
# Add after app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **3. Import Errors Breaking Startup**

Check Render logs for:
```
ModuleNotFoundError: No module named 'jwt'
ImportError: cannot import name 'verify_admin_token'
```

**Fix:** Ensure PyJWT is installed:
```bash
# Check requirements.txt has:
pyjwt==2.10.1
```

### **4. Database Connection Failing**

If all endpoints return 500 errors:
- Check SUPABASE_URL is set in Render
- Check SUPABASE_KEY is set in Render

---

## **EMERGENCY DIAGNOSTIC COMMANDS**

Run these (replace URL with your actual Render URL):

```bash
# 1. Test if server is running
curl https://your-app.onrender.com/

# 2. Test health endpoint
curl https://your-app.onrender.com/health

# 3. Test API docs
curl https://your-app.onrender.com/docs

# 4. Test onboarding endpoint
curl https://your-app.onrender.com/api/v1/onboarding/suite-catalog

# 5. Check what endpoints exist
curl https://your-app.onrender.com/openapi.json | jq '.paths | keys'
```

---

## **IF EVERYTHING IS 404**

Server might not be starting. Check Render logs for:

```
FAILED TO START
Application startup failed
ImportError
ModuleNotFoundError
```

**Common fixes:**
1. Missing `from datetime import datetime, timezone` in main.py
2. Missing PyJWT in requirements.txt
3. Circular import between auth.py and other files

---

## **NEXT STEPS**

1. **Check Render logs NOW** - Look for error messages
2. **Test your URL** - Share what happens when you visit it
3. **Share specific 404 URLs** - Tell me which pages aren't working

Then I can provide exact fix!
