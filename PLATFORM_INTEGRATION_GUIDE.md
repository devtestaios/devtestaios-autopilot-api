# Platform Integration Guide - Meta & Google Ads

**Date:** 2025-10-09
**Status:** ✅ Ready for Test Users
**Meta API Status:** Test Mode (can onboard test users)
**Google Ads API Status:** Production Ready

---

## Overview

The optimization engine now has **complete platform integration** with Meta and Google Ads APIs. You can execute budget and bid optimizations directly via the existing API clients.

---

## Meta Ads Integration ✅

### Status: Test Mode
- **App ID:** 1978667392867839
- **Ad Account:** 800452322951630 (pulsebridge.ai)
- **Access:** Test API (can onboard test users)
- **Next Step:** Submit for dev API approval once test users validate

### Capabilities:
1. **Budget Updates** - Update campaign daily budgets
2. **Status Changes** - Pause/activate campaigns
3. **Bid Adjustments** - Update ad set bids
4. **Performance Tracking** - Fetch campaign metrics

### Example Usage:

```python
from app.meta_business_api import MetaBusinessAPI
from app.optimization import MetaAdsExecutor

# Initialize Meta client
meta_client = MetaBusinessAPI()

# Create executor
executor = MetaAdsExecutor(meta_client)

# Update campaign budget
result = await executor.update_campaign_budget(
    campaign_id="120210000000000000",  # Your campaign ID
    new_daily_budget=150.00,  # $150/day
    dry_run=False  # Set True to simulate
)

if result["success"]:
    print(f"✅ Budget updated to ${result['new_daily_budget']:.2f}/day")
else:
    print(f"❌ Error: {result['error']}")
```

### Update Ad Set Bid:

```python
# Update bid for an ad set
result = await executor.update_adset_bid(
    adset_id="120210000000000001",  # Your ad set ID
    new_bid=2.50,  # $2.50 per result
    dry_run=False
)
```

### Get Campaign Performance:

```python
# Fetch performance metrics
performance = await executor.get_campaign_performance(
    campaign_id="120210000000000000",
    date_range="last_7d"  # or last_30d, today, etc.
)

print(f"Impressions: {performance['impressions']}")
print(f"Clicks: {performance['clicks']}")
print(f"Spend: ${performance['spend']:.2f}")
print(f"Conversions: {performance['conversions']}")
print(f"Revenue: ${performance['revenue']:.2f}")
```

---

## Google Ads Integration ✅

### Status: Production Ready
- **Customer ID:** From environment variable
- **Access:** Full API access
- **OAuth:** Configured with refresh token

### Capabilities:
1. **Budget Updates** - Update campaign budgets (micro-dollars)
2. **Status Changes** - Enable/pause/remove campaigns
3. **Performance Tracking** - Fetch campaign metrics

### Example Usage:

```python
from app.google_ads_integration import GoogleAdsIntegration
from app.optimization import GoogleAdsExecutor

# Initialize Google Ads client
google_client = GoogleAdsIntegration()

# Check if available
if google_client.is_available():
    # Create executor
    executor = GoogleAdsExecutor(google_client)

    # Update campaign budget
    result = await executor.update_campaign_budget(
        campaign_id="1234567890",  # Your campaign ID
        new_daily_budget=200.00,  # $200/day
        dry_run=False
    )

    if result["success"]:
        print(f"✅ Budget updated to ${result['new_daily_budget']:.2f}/day")
else:
    print("Google Ads client not available")
```

### Get Campaign Performance:

```python
# Fetch performance metrics
performance = await executor.get_campaign_performance(
    campaign_id="1234567890",
    days=7  # Last 7 days
)

print(f"Impressions: {performance['impressions']}")
print(f"Clicks: {performance['clicks']}")
print(f"Spend: ${performance['spend']:.2f}")
print(f"Conversions: {performance['conversions']}")
print(f"Revenue: ${performance['revenue']:.2f}")
```

---

## Complete Optimization Workflow

### 1. Analyze Campaign Performance

```python
from app.optimization_engine import CampaignOptimizationEngine, PerformanceMetrics

# Initialize optimization engine
engine = CampaignOptimizationEngine(target_roas=2.0)

# Get campaign metrics (from Meta or Google)
meta_client = MetaBusinessAPI()
meta_executor = MetaAdsExecutor(meta_client)

performance = await meta_executor.get_campaign_performance(
    campaign_id="120210000000000000",
    date_range="last_7d"
)

# Create metrics object
metrics = PerformanceMetrics(
    campaign_id="120210000000000000",
    platform="meta",
    impressions=performance['impressions'],
    clicks=performance['clicks'],
    conversions=performance['conversions'],
    spend=performance['spend'],
    revenue=performance['revenue'],
    ctr=performance['clicks'] / performance['impressions'] if performance['impressions'] > 0 else 0,
    cpc=performance['spend'] / performance['clicks'] if performance['clicks'] > 0 else 0,
    cpa=performance['spend'] / performance['conversions'] if performance['conversions'] > 0 else 0,
    roas=performance['revenue'] / performance['spend'] if performance['spend'] > 0 else 0
)

# Generate recommendations
recommendations = await engine.analyze_campaign_performance(
    metrics=metrics,
    total_budget=500.0,
    avg_order_value=60.0,
    bid_context={
        "ad_set_id": "120210000000000001",
        "device_type": "desktop"
    }
)

print(f"Generated {len(recommendations)} recommendations")
for rec in recommendations:
    print(f"\n{rec.optimization_type.value}:")
    print(f"  Current: ${rec.current_value:.2f}")
    print(f"  Recommended: ${rec.recommended_value:.2f}")
    print(f"  Confidence: {rec.confidence_score:.0%}")
    print(f"  Auto-execute: {rec.auto_execute}")
    print(f"  Reasoning: {rec.reasoning}")
```

### 2. Execute Recommendations

```python
from app.optimization_engine import OptimizationExecutor, OptimizationType

# Create executor (production mode)
executor = OptimizationExecutor(
    dry_run=False,  # Set True to simulate
    require_approval=True  # Only execute high-confidence recommendations
)

# Execute each recommendation
for recommendation in recommendations:
    # Determine platform
    if metrics.platform == "meta":
        platform_client = meta_executor
    elif metrics.platform == "google":
        platform_client = google_executor
    else:
        continue

    # Execute via platform executor
    if recommendation.optimization_type == OptimizationType.BUDGET_ADJUSTMENT:
        result = await platform_client.update_campaign_budget(
            campaign_id=recommendation.campaign_id,
            new_daily_budget=recommendation.recommended_value,
            dry_run=executor.dry_run
        )
    elif recommendation.optimization_type == OptimizationType.BID_OPTIMIZATION:
        # Extract ad set ID from recommendation
        result = await platform_client.update_adset_bid(
            adset_id=recommendation.campaign_id,  # Or extract from context
            new_bid=recommendation.recommended_value,
            dry_run=executor.dry_run
        )

    # Log result
    if result["success"]:
        print(f"✅ {recommendation.optimization_type.value} executed successfully")
        executor.execution_history.append({
            "timestamp": datetime.utcnow(),
            "recommendation": recommendation.dict(),
            "result": result
        })
    else:
        print(f"❌ {recommendation.optimization_type.value} failed: {result.get('error')}")
```

---

## Automated Optimization Loop

### Complete End-to-End Example:

```python
from app.meta_business_api import MetaBusinessAPI
from app.optimization import MetaAdsExecutor
from app.optimization_engine import CampaignOptimizationEngine, PerformanceMetrics
from datetime import datetime
import asyncio

async def optimize_campaign(campaign_id: str):
    """
    Complete optimization workflow for a campaign
    """
    # 1. Initialize clients
    meta_client = MetaBusinessAPI()
    meta_executor = MetaAdsExecutor(meta_client)
    engine = CampaignOptimizationEngine(target_roas=2.0)

    # 2. Fetch current performance
    print(f"📊 Fetching performance for campaign {campaign_id}...")
    performance = await meta_executor.get_campaign_performance(
        campaign_id=campaign_id,
        date_range="last_7d"
    )

    if not performance['success']:
        print(f"❌ Failed to fetch performance: {performance.get('error')}")
        return

    # 3. Calculate derived metrics
    impressions = performance['impressions']
    clicks = performance['clicks']
    conversions = performance['conversions']
    spend = performance['spend']
    revenue = performance['revenue']

    ctr = clicks / impressions if impressions > 0 else 0
    cpc = spend / clicks if clicks > 0 else 0
    cpa = spend / conversions if conversions > 0 else 0
    roas = revenue / spend if spend > 0 else 0

    print(f"  Impressions: {impressions:,}")
    print(f"  Clicks: {clicks:,} (CTR: {ctr:.2%})")
    print(f"  Conversions: {conversions} (CVR: {conversions/clicks:.2%})")
    print(f"  Spend: ${spend:.2f}")
    print(f"  Revenue: ${revenue:.2f}")
    print(f"  ROAS: {roas:.2f}x")

    # 4. Create metrics object
    metrics = PerformanceMetrics(
        campaign_id=campaign_id,
        platform="meta",
        impressions=impressions,
        clicks=clicks,
        conversions=conversions,
        spend=spend,
        revenue=revenue,
        ctr=ctr,
        cpc=cpc,
        cpa=cpa,
        roas=roas
    )

    # 5. Generate recommendations
    print(f"\n🧠 Analyzing performance...")
    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=spend * 1.5,  # Allow 50% increase
        avg_order_value=revenue / conversions if conversions > 0 else 50.0
    )

    print(f"✅ Generated {len(recommendations)} recommendations\n")

    # 6. Execute high-confidence recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.optimization_type.value.upper()}")
        print(f"   Priority: {rec.priority.value}")
        print(f"   Current: ${rec.current_value:.2f}")
        print(f"   Recommended: ${rec.recommended_value:.2f}")
        print(f"   Change: {rec.recommended_value - rec.current_value:+.2f} ({(rec.recommended_value - rec.current_value) / rec.current_value:+.1%})")
        print(f"   Confidence: {rec.confidence_score:.0%}")
        print(f"   Reasoning: {rec.reasoning}")

        # Execute if high confidence and auto-execute enabled
        if rec.auto_execute and rec.confidence_score >= 0.75:
            print(f"   🚀 Executing...")

            if rec.optimization_type.value == "budget_adjustment":
                result = await meta_executor.update_campaign_budget(
                    campaign_id=campaign_id,
                    new_daily_budget=rec.recommended_value,
                    dry_run=False  # Set True for testing
                )

                if result["success"]:
                    print(f"   ✅ Budget updated successfully!")
                else:
                    print(f"   ❌ Failed: {result.get('error')}")
            else:
                print(f"   ⏸️  Skipped (requires manual review)")
        else:
            print(f"   ⏸️  Skipped (low confidence or manual approval required)")

        print()

# Run optimization
asyncio.run(optimize_campaign("120210000000000000"))
```

---

## Test Mode Considerations (Meta)

### What You Can Do:
- ✅ Test all API functionality with test users
- ✅ Update budgets, bids, status
- ✅ Fetch performance data
- ✅ Validate optimization algorithms
- ✅ Onboard up to 5 test users

### Test User Setup:
1. Go to Meta App Dashboard → Roles → Test Users
2. Add test users (email required)
3. Test users can create test ad accounts
4. All API functionality works in test mode
5. No real money spent, no real ads shown

### What You Can't Do (Yet):
- ❌ Manage production ad accounts (need dev API approval)
- ❌ Onboard unlimited users (5 test user limit)

### Next Steps for Production:
1. **Test with test users** - Validate all functionality
2. **Submit for App Review** - Request ads_management permission
3. **Meta Review Process** - Usually 1-2 weeks
4. **Production Access** - Full API access after approval

---

## Environment Variables

### Meta Ads (Already Configured):
```bash
META_APP_ID=1978667392867839
META_APP_SECRET=365381fb087baf8cb38c53ced46b08a4
META_ACCESS_TOKEN=EAAcHlmcUnf8BPiAKrCTEy65c4sw...
META_AD_ACCOUNT_ID=800452322951630
```

### Google Ads (Required):
```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=your_customer_id
```

---

## Safety Features

### 1. Dry Run Mode:
```python
# Simulate without making changes
result = await executor.update_campaign_budget(
    campaign_id="...",
    new_daily_budget=150.0,
    dry_run=True  # Simulates execution
)
# Returns: {"status": "simulated", "message": "[DRY RUN] ..."}
```

### 2. Approval Requirements:
```python
# Only execute high-confidence recommendations
optimizer = OptimizationExecutor(
    dry_run=False,
    require_approval=True  # Only auto-execute if confidence > 0.75
)
```

### 3. Execution History:
```python
# Track all executed optimizations
history = executor.get_execution_history(campaign_id="...")
for entry in history:
    print(f"{entry['timestamp']}: {entry['result']['status']}")
```

### 4. Rollback Capability:
```python
# Revert last optimization
result = executor.rollback_last_execution(campaign_id="...")
```

---

## Performance Tips

### 1. Batch Operations:
```python
# Optimize multiple campaigns in parallel
campaigns = ["campaign_1", "campaign_2", "campaign_3"]
tasks = [optimize_campaign(cid) for cid in campaigns]
await asyncio.gather(*tasks)
```

### 2. Cache Performance Data:
```python
# Fetch once, analyze multiple times
performance = await executor.get_campaign_performance(campaign_id, "last_7d")
# Use performance data for multiple optimizations
```

### 3. Rate Limiting:
```python
# Add delay between API calls to respect rate limits
import asyncio

for campaign in campaigns:
    await optimize_campaign(campaign)
    await asyncio.sleep(1)  # 1 second delay
```

---

## Troubleshooting

### Meta API Issues:

**"Invalid OAuth access token"**
- Access token may have expired
- Generate new token via Meta App Dashboard
- Update `META_ACCESS_TOKEN` environment variable

**"Insufficient permissions"**
- Test API has limited permissions
- Submit for dev API approval to get full access
- Add test users for testing functionality

**"Campaign not found"**
- Verify campaign ID is correct
- Check if campaign belongs to your ad account
- Ensure ad account ID matches `META_AD_ACCOUNT_ID`

### Google Ads API Issues:

**"Google Ads client not available"**
- Check that all required env variables are set
- Verify Google Ads library is installed: `pip install google-ads`
- Run `google_client.test_connection()` to diagnose

**"Authentication failed"**
- Refresh token may have expired
- Re-authenticate via OAuth flow
- Update `GOOGLE_ADS_REFRESH_TOKEN`

**"Invalid customer ID"**
- Verify customer ID format (10 digits, no dashes)
- Check that you have access to the customer account

---

## What's Next

### Immediate (Test Users):
1. ✅ Set up 5 test users in Meta App Dashboard
2. ✅ Have test users create test ad accounts
3. ✅ Run optimization loop with test campaigns
4. ✅ Validate all functionality works correctly

### Short-term (Production):
1. 📝 Submit Meta app for review (ads_management permission)
2. ⏳ Wait 1-2 weeks for approval
3. ✅ Launch to production users after approval
4. 📊 Monitor optimization performance

### Medium-term (Enhancements):
1. 🤖 Automated optimization schedule (daily/weekly)
2. 📧 Email alerts for optimization recommendations
3. 📈 Dashboard for optimization history
4. 🔄 Auto-rollback if performance degrades

---

**Status:** ✅ Platform Integration Complete - Ready for Test Users

**Generated with Claude Code**
Co-Authored-By: Claude <noreply@anthropic.com>
