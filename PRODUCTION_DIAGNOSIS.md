# 🔴 Production Issues - Diagnosis & Fixes

## **What You're Experiencing**
- 404 errors on the deployed site
- Some features not functional
- Site not fully operational

---

## **Likely Issues**

### **1. Router Registration Order (COMMON ISSUE)**

**Problem:** FastAPI routers must be registered in correct order

**Check:** `/app/main.py` router order

**Common Fix:**
```python
# WRONG ORDER (causes 404s)
app.include_router(specific_router)  # More specific route
app.include_router(general_router)   # General/catch-all route

# CORRECT ORDER
app.include_router(general_router)   # Register general first
app.include_router(specific_router)  # Then specific
```

---

### **2. Missing Environment Variables**

**Problem:** Endpoints fail if required env vars missing

**Critical Variables:**
```bash
# Check these are set in Render
SUPABASE_URL=<your-url>
SUPABASE_KEY=<your-key>
STRIPE_SECRET_KEY=<your-key>
ADMIN_SECRET_KEY=<must-be-set>
ADMIN_PASSWORD=<must-be-set>
```

---

### **3. Import Errors on Deployment**

**Problem:** Code works locally but fails in production

**Common Causes:**
- Missing dependencies in requirements.txt
- Circular imports
- Python version mismatch

---

### **4. Database Connection Issues**

**Problem:** Supabase not connected

**Symptoms:**
- 500 errors on database queries
- User creation fails
- Company data not loading

---

## **🔍 IMMEDIATE DIAGNOSIS STEPS**

### **Step 1: Check Render Deployment Logs**

1. Go to Render Dashboard
2. Click your service
3. Go to "Logs" tab
4. Look for errors like:
   ```
   ImportError: ...
   ModuleNotFoundError: ...
   AttributeError: ...
   500 Internal Server Error
   ```

### **Step 2: Test Critical Endpoints**

Run these curl commands (replace `your-api.onrender.com` with your actual URL):

```bash
# 1. Health check
curl https://your-api.onrender.com/health

# 2. Root endpoint
curl https://your-api.onrender.com/

# 3. Docs (should show Swagger UI)
curl https://your-api.onrender.com/docs

# 4. Business setup wizard catalog
curl https://your-api.onrender.com/api/v1/onboarding/suite-catalog

# 5. Admin login (should fail with 401 for wrong password)
curl -X POST https://your-api.onrender.com/api/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@pulsebridge.ai", "password": "test"}'
```

---

## **🔧 COMMON FIXES**

### **Fix 1: Add Missing Health Endpoint**

If `/health` returns 404, add this to `main.py`:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
```

### **Fix 2: Enable CORS for Frontend**

If frontend can't reach API:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Fix 3: Check Router Prefixes**

Make sure routers have correct prefixes:

```python
# app/business_setup_wizard.py
router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

# app/admin_user_management.py
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# app/billing_endpoints.py
router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
```

---

## **🚨 EMERGENCY ROLLBACK**

If site is completely broken, rollback to last working commit:

```bash
# Find last working commit
git log --oneline -10

# Rollback (example)
git revert HEAD --no-edit
git push origin main
```

---

## **📋 DEBUGGING CHECKLIST**

### **In Render Dashboard:**
- [ ] Check deployment succeeded (green checkmark)
- [ ] Review build logs for errors
- [ ] Check runtime logs for crashes
- [ ] Verify environment variables are set
- [ ] Check Python version matches requirements

### **Test Endpoints:**
- [ ] `/health` returns 200 OK
- [ ] `/docs` shows Swagger UI
- [ ] `/api/v1/onboarding/suite-catalog` returns data
- [ ] POST `/api/v1/auth/admin/login` returns 401 (not 404)

### **Environment Variables:**
- [ ] SUPABASE_URL set
- [ ] SUPABASE_KEY set
- [ ] ADMIN_SECRET_KEY set (for auth)
- [ ] ADMIN_PASSWORD set (for auth)
- [ ] STRIPE_SECRET_KEY set (if using billing)

---

## **NEXT STEPS**

1. **Share Render deployment logs** - Copy recent errors
2. **Share your Render URL** - So I can test endpoints
3. **List which pages/features are 404ing** - Specific URLs

Then I can diagnose exactly what's wrong and fix it!
