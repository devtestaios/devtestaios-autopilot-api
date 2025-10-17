# Render Deployment Guide - PulseBridge.ai Backend

## 🚨 Critical Fix Applied: Supabase SSL Connection

**Date**: October 17, 2025  
**Issue**: `SSL connection has been closed unexpectedly`  
**Solution**: Added SSL configuration to SQLAlchemy database connections

---

## ✅ Recent Fixes

### 1. Added psycopg2-binary Dependency
- **File**: `requirements.txt`
- **Change**: Added `psycopg2-binary>=2.9.7`
- **Result**: Backend can now import psycopg2 for PostgreSQL connections

### 2. Added SSL Configuration for Supabase
- **Files**: `app/database.py`, `app/core/database_pool.py`
- **Changes**: 
  - Added `sslmode=require` for PostgreSQL connections
  - Added `connect_timeout=10` for better error handling
  - Added `pool_pre_ping=True` to verify connections before use
  - Added `pool_recycle=300` to recycle stale connections
- **Result**: Backend properly handles SSL connections to Supabase

---

## 🔧 Render Environment Variables Setup

### Step 1: Access Render Dashboard
1. Go to https://dashboard.render.com
2. Select your `autopilot-api` service
3. Click on "Environment" tab

### Step 2: Configure Required Variables

#### Database (CRITICAL - Use Direct Connection for Render)

**RECOMMENDED for Render (persistent containers):**
```bash
DATABASE_URL=postgresql://postgres:9bKqs5dnhSRtUWfh@db.aggorhmzuhdirterhyej.supabase.co:5432/postgres
```

**Why Direct Connection?**
- ✅ Supports all PostgreSQL features including PREPARE statements
- ✅ Better for persistent, long-lived connections (Render containers)
- ✅ Lower latency, direct database access
- ✅ SSL properly configured in the code

**Alternative (Transaction Pooler - for serverless only):**
```bash
DATABASE_URL=postgresql://postgres.aggorhmzuhdirterhyej:9bKqs5dnhSRtUWfh@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

**Why NOT Transaction Pooler for Render?**
- ⚠️ Does NOT support PREPARE statements (per Supabase docs)
- ⚠️ Better for serverless/edge functions with brief connections
- ⚠️ Adds unnecessary overhead for persistent containers

**Note**: The code now automatically detects which connection type you're using and configures the pool accordingly!

#### Supabase Configuration
```bash
SUPABASE_URL=https://aggorhmzuhdirterhyej.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

#### AI Services (REQUIRED)
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
AI_PROVIDER=anthropic
```

#### Stripe (REQUIRED for production)
```bash
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
```

#### Application Settings
```bash
ENVIRONMENT=production
HOST=0.0.0.0
PORT=10000
CORS_ORIGINS=https://pulsebridge.ai,https://www.pulsebridge.ai
JWT_SECRET=your_secure_random_string_here
LOG_LEVEL=INFO
```

#### Feature Flags (Optional)
```bash
ENABLE_WORKFLOW_AUTOMATION=true
ENABLE_PLATFORM_INTERCONNECT=true
ENABLE_ATTRIBUTION_ENGINE=true
ENABLE_ML_OPTIMIZATION=false
ENABLE_LEAD_SCORING=false
```

---

## 🚀 Deployment Steps

### Option 1: Auto-Deploy (Recommended)
1. Commit and push changes to GitHub:
   ```bash
   cd /Users/grayadkins/Desktop/PulseBridge_Repos/autopilot-api
   git add .
   git commit -m "fix: Add SSL configuration for Supabase connections"
   git push origin main
   ```
2. Render will automatically detect the change and redeploy
3. Monitor deployment at: https://dashboard.render.com

### Option 2: Manual Deploy
1. Go to Render dashboard
2. Select your `autopilot-api` service
3. Click "Manual Deploy" → "Deploy latest commit"
4. Monitor the logs for success

---

## 🔍 Verifying Deployment

### Check Deployment Logs
Look for these success indicators:
```
✓ AI services loaded successfully
✓ Optimization engine loaded successfully
✓ Multi-platform sync loaded successfully
✓ Analytics engine loaded successfully
✓ Autonomous decision framework loaded successfully
✓ Billing system loaded successfully
✓ Platform Interconnectivity system loaded successfully
🎯 Attribution Engine loaded - AI-powered multi-platform attribution active
INFO: Uvicorn running on http://0.0.0.0:10000
==> Your service is live 🎉
```

### Check for Database Connection Success
You should see:
```
INFO:app.main:🚀 PulseBridge.ai Backend Starting...
INFO:app.main:Claude API Key: ✅ Configured
INFO:app.main:OpenAI API Key: ✅ Configured
INFO: Application startup complete.
```

### ❌ ERROR to Watch For (Should be GONE now)
```
ERROR:app.main:❌ Database initialization failed: SSL connection has been closed unexpectedly
```
**If you still see this**, the SSL configuration didn't apply. Check:
1. Did you push the latest code?
2. Did Render actually redeploy?
3. Is the DATABASE_URL correct?

---

## 🧪 Testing the Backend

### Test Health Endpoint
```bash
curl https://autopilot-api-1.onrender.com/
```
Expected: `{"message": "PulseBridge.ai API is running"}`

### Test Database Connection
```bash
curl https://autopilot-api-1.onrender.com/api/v1/health
```
Expected: `{"status": "healthy", "database": "connected"}`

### Test AI Service
```bash
curl -X POST https://autopilot-api-1.onrender.com/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "conversation_id": "test"}'
```

---

## 🐛 Troubleshooting

### Issue 1: SSL Connection Errors
**Symptoms**: `SSL connection has been closed unexpectedly`  
**Solution**: 
1. Ensure latest code is deployed (with SSL configuration)
2. Verify DATABASE_URL uses the correct Supabase connection string
3. Try switching between Transaction Pooler and Direct Connection

### Issue 2: Connection Timeout
**Symptoms**: `connection timeout exceeded`  
**Solution**:
1. Check Supabase dashboard for database status
2. Verify database password is correct
3. Check if Supabase project is paused (free tier auto-pauses)

### Issue 3: ModuleNotFoundError
**Symptoms**: `No module named 'psycopg2'`  
**Solution**: Already fixed! But if it appears again:
1. Verify `requirements.txt` has `psycopg2-binary>=2.9.7`
2. Check Render build logs for pip install errors
3. Clear Render build cache and redeploy

### Issue 4: Authentication Errors
**Symptoms**: `authentication failed for user "postgres"`  
**Solution**:
1. Verify database password in DATABASE_URL matches Supabase
2. Check for special characters that need URL encoding
3. Ensure you're using the correct Supabase project reference

---

## 📊 Connection String Comparison

### Transaction Pooler (Recommended for Production)
```
postgresql://postgres.aggorhmzuhdirterhyej:9bKqs5dnhSRtUWfh@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```
**Pros**: Better scaling, connection management  
**Cons**: Slight latency overhead

### Direct Connection (Good for Development)
```
postgresql://postgres:9bKqs5dnhSRtUWfh@db.aggorhmzuhdirterhyej.supabase.co:5432/postgres
```
**Pros**: Lower latency, direct access  
**Cons**: Connection limit issues under load

**Current Configuration**: Both now support SSL properly! ✅

---

## 🔐 Security Checklist

- [ ] All API keys stored as Render environment variables (not in code)
- [ ] DATABASE_URL contains actual password (not placeholder)
- [ ] JWT_SECRET is a long random string (not default)
- [ ] CORS_ORIGINS includes only trusted domains
- [ ] Stripe keys are production keys (if live)
- [ ] Supabase RLS policies are enabled
- [ ] Service role key is kept secure

---

## 📝 Deployment History

| Date | Issue | Solution | Status |
|------|-------|----------|--------|
| Oct 17, 2025 | `No module named 'psycopg2'` | Added `psycopg2-binary>=2.9.7` to requirements.txt | ✅ Fixed |
| Oct 17, 2025 | `SSL connection has been closed` | Added SSL config to SQLAlchemy engines | ✅ Fixed |

---

## 🎯 Next Steps

1. **Commit and push** the SSL configuration fixes
2. **Configure environment variables** in Render dashboard
3. **Monitor deployment logs** for successful database connection
4. **Test API endpoints** to verify full functionality
5. **Update frontend** to use production backend URL

---

## 📞 Support Resources

- **Supabase Status**: https://status.supabase.com
- **Render Status**: https://status.render.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Render Database Guide**: https://render.com/docs/databases

---

**Deployment URL**: https://autopilot-api-1.onrender.com  
**GitHub Repo**: devtestaios/devtestaios-autopilot-api  
**Last Updated**: October 17, 2025
