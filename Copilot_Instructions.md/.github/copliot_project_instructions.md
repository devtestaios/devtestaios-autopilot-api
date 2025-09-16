# Autopilot Marketing Platform - Project Context

## Project Overview
Building an AI-powered marketing optimization platform called "Autopilot" that autonomously manages ad campaigns across multiple platforms (Google Ads, Meta, etc.), analyzes performance, optimizes spend, and provides strategic recommendations with minimal human intervention.

## Client Background
- Full-service marketing and advertising agency
- Has team currently managing online ads, split testing, analytics optimization
- Wants to automate this entire process with AI
- First-time developer, needs detailed step-by-step instructions
- Learning as we go, assumes no prior knowledge

## Current Tech Stack
- **Frontend**: Next.js 15 (App Router) on Vercel
- **Backend**: FastAPI (Python) on Render
- **Database**: Supabase (PostgreSQL)
- **Version Control**: GitHub
- **Development**: VS Code

## Architecture Flow
```
Vercel (Next.js UI) → Render (FastAPI) → Supabase (Postgres)
```

## Current Status - What's Built
### Backend (main.py)
- ✅ FastAPI with CORS configured for Vercel
- ✅ Supabase integration working
- ✅ Lead management system (GET/POST /leads)
- ✅ KPI endpoints (/kpi/summary, /kpi/daily)
- ✅ Basic health checks and env validation
- ✅ Proper error handling

### Frontend
- ✅ Next.js deployed on Vercel
- ✅ Basic lead management interface
- ✅ API integration working
- ✅ Status/health pages

### Database
- ✅ Supabase project set up
- ✅ `leads` table with RLS policies
- ✅ Basic CRUD operations working

## What We Just Planned (Next Phase)
### 1. Database Schema Update
Need to add these tables to Supabase:
- `campaigns` table (name, platform, client_name, budget, spend, metrics)
- `performance_snapshots` table (daily campaign performance data)

### 2. Backend Expansion
Adding to main.py:
- Campaign CRUD endpoints (/campaigns)
- Performance tracking (/campaigns/{id}/performance)
- Dashboard overview (/dashboard/overview)
- New Pydantic models for campaigns

### 3. Frontend Transformation
- Replace lead management with campaign dashboard
- Real-time campaign monitoring interface
- Performance analytics visualization
- Client management interface

## Immediate Next Steps
1. **Execute SQL schema** - Add campaigns and performance_snapshots tables
2. **Update main.py** - Add campaign endpoints (code ready)
3. **Test backend changes** - Verify new endpoints work
4. **Build campaign dashboard UI** - Replace current leads interface
5. **Google Ads API integration** - Connect real campaign data

## Future Phases
- **Phase 1**: Google Ads integration + basic dashboard
- **Phase 2**: AI optimization engine + automated recommendations
- **Phase 3**: Multi-platform support (Meta, LinkedIn)
- **Phase 4**: Full autopilot mode with safeguards

## Development Approach
- Build UI first with mock data, then connect real APIs
- Always test locally before deploying
- Use feature branches for major changes
- Keep costs low during prototyping phase
- Focus on working prototype first, optimize later

## Key Requirements
- Web-based tool, accessible anywhere
- Simple interface focused on technical analysis and ease of use
- Compatible with multiple ad platforms
- KPIs change based on client specifications
- Minimal user interface once running
- Cost-effective to build and test

## Files to Upload to Project
1. Current `main.py` (backend)
2. Frontend structure/key files
3. Database schema (current state)
4. Environment configuration examples
5. This context document

## Communication Style Needed
- Assume no prior coding knowledge
- Explain every step clearly
- Provide exact commands to run
- Suggest efficiency improvements
- Focus on working solutions over perfect code initially

## Current Challenges
- First-time developer needs detailed guidance
- Transforming from lead management to campaign management
- Need to maintain existing functionality while adding new features
- Cost optimization during development phase

## Success Metrics
- Campaign dashboard showing real Google Ads data
- Automated performance analysis
- Budget optimization recommendations
- Multi-client campaign management
- Eventual full automation with minimal human oversight