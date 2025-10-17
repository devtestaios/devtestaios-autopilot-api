# Environment Variables - Render vs Vercel Configuration

## 🎯 **THE PROBLEM IDENTIFIED**

Your backend (`oauth_meta.py` and `meta_campaign_sync.py`) is looking for **frontend-style** variable names, but Render doesn't have them!

---

## 📊 **Variable Name Differences**

### **Backend (Render) - What Code Expects:**
```python
# These files look for NEXT_PUBLIC_ prefixed vars:
oauth_meta.py:        SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
oauth_meta.py:        SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

meta_campaign_sync.py: SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
meta_campaign_sync.py: SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
```

### **Backend (Render) - What Main.py Uses:**
```python
# main.py looks for either naming convention:
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
```

### **Frontend (Vercel) - Correct Naming:**
```typescript
// Frontend expects NEXT_PUBLIC_ prefix (correct for Next.js):
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY  // Backend only, no NEXT_PUBLIC
```

---

## ✅ **THE SOLUTION**

You have **TWO OPTIONS**:

### **Option 1: Add NEXT_PUBLIC_ Variables to Render (Quick Fix)**

Add these to Render (in addition to what you have):
```bash
NEXT_PUBLIC_SUPABASE_URL=https://aggorhmzuhdirterhyej.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[your_anon_key]
```

**Why**: `oauth_meta.py` and `meta_campaign_sync.py` specifically look for these prefixed names

### **Option 2: Fix the Backend Code (Better Long-term)**

Update `oauth_meta.py` and `meta_campaign_sync.py` to use the same pattern as `main.py`

---

## 🔧 **COMPLETE ENVIRONMENT VARIABLE SETUP**

### **Render (Backend) - Required Variables:**

```bash
# Database Connection
DATABASE_URL=postgresql://postgres:9bKqs5dnhSRtUWfh@db.aggorhmzuhdirterhyej.supabase.co:5432/postgres

# Supabase - Backend Style (for main.py)
SUPABASE_URL=https://aggorhmzuhdirterhyej.supabase.co
SUPABASE_KEY=[your_anon_key]
SUPABASE_SERVICE_KEY=[your_service_role_key]

# Supabase - Frontend Style (for oauth_meta.py & meta_campaign_sync.py)
NEXT_PUBLIC_SUPABASE_URL=https://aggorhmzuhdirterhyej.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[your_anon_key]

# AI Services
ANTHROPIC_API_KEY=[your_key]
OPENAI_API_KEY=[your_key]
AI_PROVIDER=anthropic

# Meta/Facebook
META_APP_ID=[your_id]
META_APP_SECRET=[your_secret]
META_REDIRECT_URI=https://pulsebridge.ai/auth/meta/callback

# Stripe
STRIPE_SECRET_KEY=[your_key]
STRIPE_PUBLISHABLE_KEY=[your_key]
STRIPE_WEBHOOK_SECRET=[your_secret]

# Application
ENVIRONMENT=production
HOST=0.0.0.0
PORT=10000
CORS_ORIGINS=https://pulsebridge.ai,https://www.pulsebridge.ai
```

### **Vercel (Frontend) - Required Variables:**

```bash
# Supabase - Frontend (NEXT_PUBLIC_ prefix required)
NEXT_PUBLIC_SUPABASE_URL=https://aggorhmzuhdirterhyej.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[your_anon_key]
SUPABASE_SERVICE_ROLE_KEY=[your_service_role_key]  # No NEXT_PUBLIC (backend only)

# Backend API
NEXT_PUBLIC_API_URL=https://autopilot-api-1.onrender.com

# AI Services (if used in frontend)
NEXT_PUBLIC_ANTHROPIC_API_KEY=[your_key]  # Only if needed client-side
OPENAI_API_KEY=[your_key]  # Server-side only

# Stripe (frontend)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=[your_key]

# Meta OAuth
NEXT_PUBLIC_META_APP_ID=[your_id]

# Google Ads
NEXT_PUBLIC_GOOGLE_ADS_CLIENT_ID=[your_id]
```

---

## 🎯 **QUICK FIX FOR YOUR CURRENT ISSUE**

### **What You Need to Add to Render RIGHT NOW:**

Go to Render Dashboard → Environment and add:

```bash
NEXT_PUBLIC_SUPABASE_URL = https://aggorhmzuhdirterhyej.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = [your_anon_key_from_supabase]
```

**That's it!** These two variables will fix the warnings:
- ✅ `WARNING:app.oauth_meta:Supabase not configured`
- ✅ `WARNING:app.meta_campaign_sync:Supabase not configured`

---

## 📝 **Why This Happened**

### **Root Cause:**
Some backend files (`oauth_meta.py`, `meta_campaign_sync.py`) were coded to look for `NEXT_PUBLIC_` prefixed variables (frontend convention), but:
- Render backend doesn't need `NEXT_PUBLIC_` prefix
- Your existing Render vars probably use backend naming: `SUPABASE_URL`, `SUPABASE_KEY`
- The code is looking for the wrong variable names

### **Why NEXT_PUBLIC_ Prefix Exists:**
- In Next.js, `NEXT_PUBLIC_` prefix exposes variables to browser
- Backend doesn't need this prefix (it's server-side only)
- Some backend files incorrectly expect frontend variable names

---

## 🔍 **Verification Guide**

### **Check What You Currently Have:**

**In Render:**
```bash
# Check if you have these (you probably do):
SUPABASE_URL ✅
SUPABASE_KEY or SUPABASE_ANON_KEY ✅

# Check if you have these (you probably DON'T):
NEXT_PUBLIC_SUPABASE_URL ❌ (MISSING - ADD THIS)
NEXT_PUBLIC_SUPABASE_ANON_KEY ❌ (MISSING - ADD THIS)
```

**In Vercel:**
```bash
# Check if you have these (you probably do):
NEXT_PUBLIC_SUPABASE_URL ✅
NEXT_PUBLIC_SUPABASE_ANON_KEY ✅
```

---

## 🚀 **ACTION PLAN**

### **Immediate Fix (2 minutes):**

1. **Go to Render Dashboard**
   - https://dashboard.render.com
   - Select: autopilot-api
   - Click: Environment

2. **Add These 2 Variables**
   ```
   NEXT_PUBLIC_SUPABASE_URL = https://aggorhmzuhdirterhyej.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY = [paste your anon key]
   ```

3. **Click Save**
   - Triggers redeploy (~3 min)

4. **Check Logs**
   - Warnings should disappear
   - Should see: "✅ Supabase client initialized successfully"

### **Long-term Fix (Optional):**
Update `oauth_meta.py` and `meta_campaign_sync.py` to use backend variable names like `main.py` does (I can help with this if you want)

---

## 📊 **Summary Table**

| File | Current Variable | Should Also Accept | Status |
|------|-----------------|-------------------|--------|
| `main.py` | `SUPABASE_URL` | `SUPABASE_KEY` or `SUPABASE_ANON_KEY` | ✅ Flexible |
| `oauth_meta.py` | `NEXT_PUBLIC_SUPABASE_URL` | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ❌ Frontend naming |
| `meta_campaign_sync.py` | `NEXT_PUBLIC_SUPABASE_URL` | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ❌ Frontend naming |
| Frontend files | `NEXT_PUBLIC_SUPABASE_URL` | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ Correct |

---

## ✅ **Final Answer to Your Question**

### **Render (Backend) Needs BOTH:**
```bash
# Standard backend naming (for main.py):
SUPABASE_URL
SUPABASE_KEY or SUPABASE_ANON_KEY

# Frontend naming (for oauth_meta.py & meta_campaign_sync.py):
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### **Vercel (Frontend) Needs:**
```bash
# Frontend naming (standard Next.js):
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY  # Server-side only
```

---

**The Fix**: Add the `NEXT_PUBLIC_` prefixed variables to Render, even though it's a backend. Two backend files expect them! 🎯
