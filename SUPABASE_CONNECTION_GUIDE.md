# Supabase Connection Strings - Quick Reference

## 🎯 For Render Deployment: Use Direct Connection

### ✅ Direct Connection (RECOMMENDED)
```bash
postgresql://postgres:9bKqs5dnhSRtUWfh@db.aggorhmzuhdirterhyej.supabase.co:5432/postgres
```

**When to use:**
- ✅ Render deployments (persistent containers)
- ✅ Long-running applications
- ✅ Virtual machines
- ✅ Docker containers
- ✅ When you need all PostgreSQL features

**Advantages:**
- Supports PREPARE statements
- Lower latency
- Full PostgreSQL feature set
- Each client has dedicated connection

---

### ⚠️ Transaction Pooler (NOT recommended for Render)
```bash
postgresql://postgres.aggorhmzuhdirterhyej:9bKqs5dnhSRtUWfh@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

**When to use:**
- Serverless functions (Vercel, Netlify Edge, Cloudflare Workers)
- Edge functions
- Brief, isolated database interactions
- High number of concurrent clients

**Limitations:**
- ❌ Does NOT support PREPARE statements
- ❌ Not IPv4 compatible (use Session Pooler for IPv4)
- Shared connection pool (all clients share)
- Best for stateless applications

---

## 🔧 Configuration Applied

The backend code now **automatically detects** which connection type you're using:

### For Direct Connection:
- Uses QueuePool with larger pool size (20 base, 30 overflow)
- Enables connection recycling (1 hour)
- Full PostgreSQL feature support

### For Transaction Pooler:
- Uses smaller pool size (5 base, 10 overflow)
- Optimized for brief connections
- Works around PREPARE statement limitation

---

## 🚀 Render Environment Setup

1. Go to Render Dashboard → Your Service → Environment
2. Add/Update `DATABASE_URL` variable:
   ```
   postgresql://postgres:9bKqs5dnhSRtUWfh@db.aggorhmzuhdirterhyej.supabase.co:5432/postgres
   ```
3. Save and redeploy

---

## 🧪 Testing Connection

### Local Testing
```bash
cd /Users/grayadkins/Desktop/PulseBridge_Repos/autopilot-api

# Set environment variable
export DATABASE_URL="postgresql://postgres:9bKqs5dnhSRtUWfh@db.aggorhmzuhdirterhyej.supabase.co:5432/postgres"

# Test with Python
python -c "
from sqlalchemy import create_engine, text
engine = create_engine('$DATABASE_URL', connect_args={'sslmode': 'require'})
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print('✅ Connection successful!')
    print(result.fetchone()[0])
"
```

### Test on Render
```bash
# After deployment, check logs for:
INFO: Using Supabase Direct Connection configuration
INFO: Application startup complete.
```

---

## 📊 Connection String Breakdown

### Direct Connection Format:
```
postgresql://[user]:[password]@[host]:[port]/[database]
           
           postgres : 9bKqs5dnhSRtUWfh @ db.aggorhmzuhdirterhyej.supabase.co : 5432 / postgres
           └─user   └─password           └─host                              └─port └─db
```

### Transaction Pooler Format:
```
postgresql://[user.project]:[password]@[pooler-host]:[port]/[database]

           postgres.aggorhmzuhdirterhyej : 9bKqs5dnhSRtUWfh @ aws-1-us-east-2.pooler.supabase.com : 6543 / postgres
           └─user.project-ref             └─password           └─pooler host                          └─port └─db
```

---

## 🔐 Security Notes

- ✅ SSL is **required** and automatically configured
- ✅ Password is included in connection string (keep secure!)
- ✅ Use environment variables (never commit to git)
- ✅ Supabase project: `aggorhmzuhdirterhyej`
- ✅ Region: `us-east-2` (AWS)

---

## 📝 Current Status

- [x] SSL configuration added to `app/database.py`
- [x] SSL configuration added to `app/core/database_pool.py`
- [x] Automatic connection type detection
- [x] Optimized pool settings for both connection types
- [x] Ready for Render deployment

**Last Updated**: October 17, 2025
