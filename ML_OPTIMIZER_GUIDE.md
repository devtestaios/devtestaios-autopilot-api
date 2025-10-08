# PulseBridge.ai ML Budget Optimizer - User Guide

## Overview

The ML Budget Optimizer is PulseBridge.ai's **first real machine learning feature** - a production-ready AI system that predicts optimal daily budgets for Meta advertising campaigns.

Unlike our other endpoints that return mock data, **this is a fully functional ML system** that:
- Fetches real historical data from Meta Ads API
- Trains a Gradient Boosting model on your campaigns
- Makes actual predictions with confidence scores
- Improves over time with feedback loops

---

## Quick Start (5 minutes)

### Step 1: Train the Model

First, you need to train the ML model on your campaign data:

```bash
POST https://autopilot-api-1.onrender.com/api/v1/ml/train

Headers:
  Content-Type: application/json

Body:
{
  "campaign_ids": ["123456789", "987654321"],
  "access_token": "YOUR_META_ACCESS_TOKEN",
  "days_back": 90,
  "test_size": 0.2
}
```

**Response** (after 30-90 seconds):
```json
{
  "status": "success",
  "message": "Model trained on 2 campaigns",
  "metrics": {
    "test_mae": 45.23,
    "test_r2": 0.87,
    "cv_mae": 48.15,
    "n_samples": 156,
    "n_features": 20
  },
  "top_features": [
    ["roas", 0.245],
    ["spend_trend_7d", 0.189],
    ["conversion_rate", 0.156]
  ],
  "model_version": "1.0.0",
  "trained_at": "2025-10-08T10:30:00"
}
```

### Step 2: Get Budget Predictions

Once trained, get optimal budget recommendations:

```bash
POST https://autopilot-api-1.onrender.com/api/v1/ml/predict

Headers:
  Content-Type: application/json

Body:
{
  "campaign_id": "123456789",
  "access_token": "YOUR_META_ACCESS_TOKEN"
}
```

**Response**:
```json
{
  "predicted_budget": 750.50,
  "current_budget": 500.00,
  "budget_change": 250.50,
  "budget_change_percentage": 50.1,
  "confidence_score": 0.85,
  "prediction_date": "2025-10-09",
  "current_roas": 3.2,
  "recent_7d_avg_roas": 3.1,
  "reasoning": "Increase budget by 50.1%. Strong ROAS of 3.20x indicates room for profitable scaling.",
  "model_version": "1.0.0"
}
```

---

## API Endpoints

### 1. Train Model
**POST** `/api/v1/ml/train`

Train the ML model on historical campaign data.

**Request Body:**
```typescript
{
  campaign_ids: string[];      // Meta campaign IDs to train on
  access_token?: string;       // Meta API token (uses env var if not provided)
  days_back?: number;          // Historical data days (default: 90, min: 30, max: 365)
  test_size?: number;          // Test split proportion (default: 0.2, range: 0.1-0.4)
}
```

**Response:**
```typescript
{
  status: "success";
  message: string;
  metrics: {
    train_mae: number;         // Mean Absolute Error on training set
    test_mae: number;          // MAE on test set (lower is better)
    train_r2: number;          // R² score on training (1.0 = perfect)
    test_r2: number;           // R² on test set
    cv_mae: number;            // Cross-validation MAE
    n_samples: number;         // Total training samples
    n_features: number;        // Feature count
  };
  top_features: [string, number][]; // Most important features
  model_version: string;
  trained_at: string;
  feature_count: number;
}
```

**Training Time:** 30-90 seconds depending on data volume

**Data Requirements:**
- Minimum 30 days of historical data per campaign
- At least 1 campaign (recommend 3+ for better generalization)
- More campaigns = better model performance across different scenarios

---

### 2. Predict Optimal Budget
**POST** `/api/v1/ml/predict`

Get ML-powered budget recommendation for a campaign.

**Request Body:**
```typescript
{
  campaign_id: string;         // Meta campaign ID
  access_token?: string;       // Meta API token
  prediction_date?: string;    // ISO date (default: tomorrow)
}
```

**Response:**
```typescript
{
  predicted_budget: number;           // Recommended daily budget
  current_budget: number;             // Current daily spend
  budget_change: number;              // Dollar change
  budget_change_percentage: number;   // Percent change
  confidence_score: number;           // 0.0 - 1.0 (higher = more confident)
  prediction_date: string;            // ISO date
  current_roas: number;               // Current ROAS
  recent_7d_avg_roas: number;         // 7-day average ROAS
  reasoning: string;                  // Human-readable explanation
  model_version: string;
}
```

**Requirements:**
- Model must be trained first (via `/train` endpoint)
- Need at least 7 days of recent performance data
- Campaign must be active in Meta Ads

---

### 3. Get Model Info
**GET** `/api/v1/ml/model/info`

Get current ML model status and metrics.

**Response:**
```typescript
{
  is_trained: boolean;
  model_version: string;
  trained_at: string | null;
  training_metrics: {
    test_mae: number;
    test_r2: number;
    cv_mae: number;
    n_samples: number;
    n_features: number;
  };
  feature_count: number;
  model_type: "GradientBoostingRegressor";
}
```

---

### 4. Save Model
**POST** `/api/v1/ml/model/save`

Manually save trained model to disk (auto-saves after training).

**Response:**
```typescript
{
  status: "success";
  message: "Model saved successfully";
  filepath: string;
}
```

---

### 5. Load Model
**POST** `/api/v1/ml/model/load`

Load a previously saved model.

**Query Parameters:**
- `filepath` - Path to saved model file

**Response:**
```typescript
{
  status: "success";
  message: "Model loaded successfully";
  model_info: {
    // Same structure as /model/info
  };
}
```

---

### 6. Health Check
**GET** `/api/v1/ml/health`

Check ML system status.

**Response:**
```typescript
{
  status: "healthy";
  timestamp: string;
  model_trained: boolean;
  model_version: string;
  capabilities: string[];
}
```

---

## How It Works

### Data Collection
1. Connects to Meta Ads API
2. Fetches daily performance data (impressions, clicks, conversions, revenue, ROAS)
3. Collects 90 days of historical data by default
4. Supports multiple campaigns for better model generalization

### Feature Engineering
The system engineers **20+ features** from raw data:

**Raw Metrics:**
- Daily spend, impressions, clicks, conversions, revenue

**Rate Metrics:**
- CTR, CPC, CPA, ROAS, conversion rate

**Trend Features (7-day moving averages):**
- Spend trend, ROAS trend, conversion trend

**Time Features:**
- Day of week, weekend indicator, week of month, day of month

**Performance Indicators:**
- Spend efficiency (revenue per dollar)
- Engagement rate (clicks per impression)
- Value per conversion

### Machine Learning Model
- **Algorithm:** Gradient Boosting Regressor (scikit-learn)
- **Training:** 80/20 train/test split with 5-fold cross-validation
- **Scaling:** StandardScaler for feature normalization
- **Validation:** MAE, R², and cross-validation scoring

### Prediction Logic
The model predicts optimal budget based on:
1. **Recent performance trends** (7-day moving averages)
2. **Current ROAS** (higher ROAS → recommend scaling up)
3. **Conversion trends** (improving → more aggressive, declining → conservative)
4. **Time patterns** (weekday/weekend, seasonal factors)

**Safety Bounds:**
- Maximum increase: 100% (2x current spend)
- Maximum decrease: 50% (0.5x current spend)

### Target Variable Calculation
The model learns what "optimal" budget means by analyzing historical performance:
- ROAS ≥ 3.5 → Could have spent 20% more
- ROAS 2.5-3.5 → Could have spent 10% more
- ROAS 2.0-2.5 → Maintain spend
- ROAS 1.5-2.0 → Reduce spend 10%
- ROAS < 1.5 → Reduce spend 25%

---

## Performance Metrics Explained

### MAE (Mean Absolute Error)
Average dollar difference between predictions and actual optimal budgets.
- **Good:** < $50
- **Acceptable:** $50-$100
- **Needs improvement:** > $100

### R² Score
How well the model explains budget variations (0-1 scale).
- **Excellent:** > 0.85
- **Good:** 0.70-0.85
- **Acceptable:** 0.50-0.70
- **Poor:** < 0.50

### Cross-Validation MAE
Average MAE across 5 different train/test splits (tests generalization).

### Confidence Score
Prediction confidence based on recent performance stability (0-1 scale).
- **High:** > 0.8 (stable performance, reliable prediction)
- **Medium:** 0.6-0.8 (some variance)
- **Low:** < 0.6 (high variance, use with caution)

---

## Best Practices

### Training
✅ **DO:**
- Train on 3+ campaigns for better generalization
- Use 90+ days of historical data when available
- Retrain weekly as new data becomes available
- Include campaigns with varying budgets and performance levels

❌ **DON'T:**
- Train on campaigns with < 30 days of data
- Train on only high-performing campaigns (creates bias)
- Train on paused/inactive campaigns

### Predictions
✅ **DO:**
- Check confidence score before acting (aim for > 0.7)
- Review reasoning to understand recommendations
- Start with small budget changes to validate predictions
- Monitor actual results vs. predictions for feedback

❌ **DON'T:**
- Blindly follow predictions with low confidence scores
- Make extreme budget changes without validation
- Ignore business constraints (max daily budget, cash flow)

### Model Maintenance
✅ **DO:**
- Retrain weekly with fresh data
- Track prediction accuracy over time
- Save model versions for rollback capability
- Monitor feature importance changes

---

## Example Workflow

### Initial Setup
```bash
# 1. Train model on your top campaigns
curl -X POST https://autopilot-api-1.onrender.com/api/v1/ml/train \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_ids": ["123", "456", "789"],
    "access_token": "YOUR_TOKEN",
    "days_back": 90
  }'

# 2. Check model info
curl https://autopilot-api-1.onrender.com/api/v1/ml/model/info
```

### Daily Optimization
```bash
# Get budget recommendation
curl -X POST https://autopilot-api-1.onrender.com/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "123",
    "access_token": "YOUR_TOKEN"
  }'

# Review recommendation
# If confidence > 0.7 and reasoning makes sense:
#   → Implement budget change in Meta Ads Manager
#   → Monitor results for 3-7 days
#   → Track actual ROAS vs. predicted impact
```

### Weekly Maintenance
```bash
# Retrain with latest data
curl -X POST https://autopilot-api-1.onrender.com/api/v1/ml/train \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_ids": ["123", "456", "789"],
    "access_token": "YOUR_TOKEN",
    "days_back": 90
  }'
```

---

## Troubleshooting

### Error: "Model not trained"
**Solution:** Train the model first using `/api/v1/ml/train`

### Error: "Insufficient data: need at least 7 days"
**Solution:** Campaign needs more historical data. Wait until campaign has run for 7+ days.

### Error: "No performance data available"
**Solution:**
- Verify Meta API access token is valid
- Check campaign ID is correct
- Ensure campaign is active in Meta Ads Manager

### Low confidence scores (< 0.6)
**Causes:**
- Recent performance is highly volatile
- Campaign recently changed significantly
- Insufficient historical data

**Solution:** Use predictions cautiously or wait for more stable data.

### Poor model performance (high MAE, low R²)
**Causes:**
- Too few training campaigns (< 3)
- Insufficient historical data (< 60 days)
- Campaigns have very different characteristics

**Solution:**
- Add more campaigns to training set
- Collect more historical data
- Retrain with longer lookback period

---

## Technical Architecture

```
┌─────────────────────────────────────────────────┐
│         Meta Ads API                            │
│  (Historical Performance Data)                  │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│      MetaDataCollector                          │
│  - Fetches daily insights                       │
│  - Parses conversions and revenue               │
│  - Handles pagination and rate limits           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│      FeatureEngineer                            │
│  - Calculates rate metrics (CTR, CPC, ROAS)     │
│  - Computes 7-day trends                        │
│  - Extracts time features                       │
│  - Generates 20+ ML-ready features              │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│      BudgetOptimizerML                          │
│  - Trains GradientBoostingRegressor             │
│  - StandardScaler normalization                 │
│  - Cross-validation                             │
│  - Feature importance tracking                  │
│  - Model persistence (pickle)                   │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│      REST API Endpoints                         │
│  /train, /predict, /model/info                  │
└─────────────────────────────────────────────────┘
```

---

## Feature Importance

After training, check which features drive predictions:

**Typical Top Features:**
1. **ROAS** (0.24) - Strong indicator of scaling opportunity
2. **7-day spend trend** (0.19) - Recent momentum matters
3. **Conversion rate** (0.16) - Efficiency indicator
4. **Revenue** (0.12) - Absolute performance level
5. **7-day ROAS trend** (0.10) - Performance trajectory

Lower importance but still used:
- Day of week patterns
- Engagement rates
- Value per conversion
- Weekend indicators

---

## Next Steps

### Phase 1: Validation (Current)
- Manual review of all predictions
- A/B test recommendations vs. current strategy
- Build confidence in model accuracy

### Phase 2: Semi-Automation (Next 30 days)
- Auto-implement predictions with confidence > 0.8
- Human review for confidence 0.6-0.8
- Reject predictions < 0.6

### Phase 3: Full Automation (60+ days)
- Autonomous budget adjustments
- Real-time optimization
- Multi-campaign portfolio optimization
- Feedback loops improve model continuously

---

## Support

**Questions or issues?**
- Check `/api/v1/ml/health` for system status
- Review training metrics for model quality
- Contact: admin@pulsebridge.ai

**Production URL:** https://autopilot-api-1.onrender.com

**API Docs:** https://autopilot-api-1.onrender.com/docs
