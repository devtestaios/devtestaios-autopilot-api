"""
FastAPI endpoints for Advanced Analytics Engine
Provides sophisticated analytics with predictive modeling, trend analysis, and AI insights
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
import logging
from pydantic import BaseModel, Field

from advanced_analytics_engine import (
    AdvancedAnalyticsEngine,
    PredictiveMetrics,
    CrossPlatformCorrelation,
    PerformanceTrend,
    AIInsight
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/analytics", tags=["Advanced Analytics"])

# Global analytics engine instance
analytics_engine = AdvancedAnalyticsEngine()

# Pydantic models for API responses
class PredictiveMetricsResponse(BaseModel):
    forecast_period: int
    predicted_impressions: float
    predicted_clicks: float
    predicted_conversions: float
    predicted_spend: float
    predicted_revenue: float
    confidence_score: float
    trend_direction: str
    seasonal_factors: Dict[str, Union[float, Dict[str, float]]]
    risk_factors: List[str]

class CrossPlatformCorrelationResponse(BaseModel):
    platform_a: str
    platform_b: str
    correlation_score: float
    correlation_type: str
    shared_audience_overlap: float
    budget_cannibalization_risk: float
    optimization_opportunity: str

class PerformanceTrendResponse(BaseModel):
    metric_name: str
    current_value: float
    trend_direction: str
    trend_strength: float
    weekly_change: float
    monthly_change: float
    seasonal_pattern: Dict[str, float]
    anomaly_detected: bool
    anomaly_severity: str

class AIInsightResponse(BaseModel):
    insight_type: str
    confidence: float
    impact_score: float
    title: str
    description: str
    recommendation: str
    priority: str
    estimated_impact: Dict[str, float]
    implementation_effort: str

class AnalyticsOverviewResponse(BaseModel):
    summary: Dict[str, Union[str, float, int]]
    key_insights: List[AIInsightResponse]
    performance_trends: List[PerformanceTrendResponse]
    predictive_forecast: PredictiveMetricsResponse
    cross_platform_analysis: List[CrossPlatformCorrelationResponse]
    generated_at: datetime

class TrainingStatusResponse(BaseModel):
    status: str
    model_scores: Dict[str, Dict[str, float]]
    feature_importance: Dict[str, Dict[str, float]]
    last_trained: datetime
    data_points_used: int

# Request models
class HistoricalDataRequest(BaseModel):
    campaign_data: List[Dict]
    date_range: Dict[str, str]
    platforms: List[str] = Field(default_factory=list)

class ForecastRequest(BaseModel):
    historical_data: List[Dict]
    forecast_days: int = Field(default=30, ge=1, le=365)
    include_seasonal_adjustment: bool = True

class TrendAnalysisRequest(BaseModel):
    performance_data: List[Dict]
    lookback_days: int = Field(default=30, ge=7, le=365)
    metrics: List[str] = Field(default_factory=list)

# Initialize analytics engine on startup
@router.on_event("startup")
async def initialize_analytics():
    """Initialize the analytics engine on startup"""
    try:
        success = await analytics_engine.initialize_models()
        if success:
            logger.info("Advanced Analytics Engine initialized successfully")
        else:
            logger.error("Failed to initialize Advanced Analytics Engine")
    except Exception as e:
        logger.error(f"Error initializing analytics engine: {e}")

@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    days: int = Query(default=30, ge=7, le=365, description="Number of days for analysis"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
) -> AnalyticsOverviewResponse:
    """
    Get comprehensive analytics overview with trends, predictions, and insights
    """
    try:
        # Parse platforms
        platform_list = platforms.split(',') if platforms else ['google_ads', 'meta', 'linkedin']
        
        # Mock data for demonstration (replace with actual data fetching)
        historical_data = await _fetch_historical_data(days, platform_list)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail="No historical data found")
        
        # Train models on historical data
        model_scores = await analytics_engine.train_predictive_models(historical_data)
        
        # Generate predictive forecast
        forecast = await analytics_engine.generate_predictive_forecast(historical_data, 30)
        
        # Analyze performance trends
        trends = await analytics_engine.analyze_performance_trends(historical_data, days)
        
        # Analyze cross-platform correlations
        platform_data = await _organize_data_by_platform(historical_data)
        correlations = await analytics_engine.analyze_cross_platform_correlations(platform_data)
        
        # Generate AI insights
        insights = await analytics_engine.generate_ai_insights(
            historical_data, trends, correlations, forecast
        )
        
        # Calculate summary statistics
        summary = _calculate_summary_stats(historical_data, trends, forecast)
        
        return AnalyticsOverviewResponse(
            summary=summary,
            key_insights=[AIInsightResponse(**insight.__dict__) for insight in insights],
            performance_trends=[PerformanceTrendResponse(**trend.__dict__) for trend in trends],
            predictive_forecast=PredictiveMetricsResponse(**forecast.__dict__),
            cross_platform_analysis=[CrossPlatformCorrelationResponse(**corr.__dict__) for corr in correlations],
            generated_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics processing failed: {str(e)}")

@router.post("/forecast", response_model=PredictiveMetricsResponse)
async def generate_forecast(request: ForecastRequest) -> PredictiveMetricsResponse:
    """
    Generate predictive forecast for campaign performance
    """
    try:
        if not request.historical_data:
            raise HTTPException(status_code=400, detail="Historical data is required")
        
        # Train models if needed
        await analytics_engine.train_predictive_models(request.historical_data)
        
        # Generate forecast
        forecast = await analytics_engine.generate_predictive_forecast(
            request.historical_data, 
            request.forecast_days
        )
        
        return PredictiveMetricsResponse(**forecast.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

@router.post("/trends", response_model=List[PerformanceTrendResponse])
async def analyze_trends(request: TrendAnalysisRequest) -> List[PerformanceTrendResponse]:
    """
    Analyze performance trends and detect anomalies
    """
    try:
        if not request.performance_data:
            raise HTTPException(status_code=400, detail="Performance data is required")
        
        trends = await analytics_engine.analyze_performance_trends(
            request.performance_data,
            request.lookback_days
        )
        
        # Filter by requested metrics if specified
        if request.metrics:
            trends = [trend for trend in trends if trend.metric_name in request.metrics]
        
        return [PerformanceTrendResponse(**trend.__dict__) for trend in trends]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@router.get("/correlations", response_model=List[CrossPlatformCorrelationResponse])
async def get_cross_platform_correlations(
    days: int = Query(default=30, ge=7, le=365),
    platforms: Optional[str] = Query(default=None, description="Comma-separated platform names")
) -> List[CrossPlatformCorrelationResponse]:
    """
    Analyze correlations between different advertising platforms
    """
    try:
        platform_list = platforms.split(',') if platforms else ['google_ads', 'meta', 'linkedin']
        
        if len(platform_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 platforms required for correlation analysis")
        
        # Fetch data for each platform
        platform_data = {}
        for platform in platform_list:
            data = await _fetch_platform_data(platform, days)
            if data:
                platform_data[platform] = data
        
        if len(platform_data) < 2:
            raise HTTPException(status_code=404, detail="Insufficient data for correlation analysis")
        
        correlations = await analytics_engine.analyze_cross_platform_correlations(platform_data)
        
        return [CrossPlatformCorrelationResponse(**corr.__dict__) for corr in correlations]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing correlations: {e}")
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")

@router.get("/insights", response_model=List[AIInsightResponse])
async def get_ai_insights(
    days: int = Query(default=30, ge=7, le=365),
    priority: Optional[str] = Query(default=None, regex="^(low|medium|high|critical)$"),
    insight_type: Optional[str] = Query(default=None, regex="^(performance|trend|correlation|prediction|anomaly)$")
) -> List[AIInsightResponse]:
    """
    Get AI-generated insights and recommendations
    """
    try:
        # Fetch comprehensive data
        historical_data = await _fetch_historical_data(days, ['google_ads', 'meta', 'linkedin'])
        
        if not historical_data:
            raise HTTPException(status_code=404, detail="No data available for insights")
        
        # Generate all analysis components
        trends = await analytics_engine.analyze_performance_trends(historical_data, days)
        
        platform_data = await _organize_data_by_platform(historical_data)
        correlations = await analytics_engine.analyze_cross_platform_correlations(platform_data)
        
        forecast = await analytics_engine.generate_predictive_forecast(historical_data, 30)
        
        # Generate insights
        insights = await analytics_engine.generate_ai_insights(
            historical_data, trends, correlations, forecast
        )
        
        # Filter by priority if specified
        if priority:
            insights = [insight for insight in insights if insight.priority == priority]
        
        # Filter by type if specified
        if insight_type:
            insights = [insight for insight in insights if insight.insight_type == insight_type]
        
        return [AIInsightResponse(**insight.__dict__) for insight in insights]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")

@router.post("/train-models", response_model=TrainingStatusResponse)
async def train_predictive_models(request: HistoricalDataRequest) -> TrainingStatusResponse:
    """
    Train predictive models on provided historical data
    """
    try:
        if not request.campaign_data:
            raise HTTPException(status_code=400, detail="Campaign data is required for training")
        
        # Train models
        model_scores = await analytics_engine.train_predictive_models(request.campaign_data)
        
        if not model_scores:
            raise HTTPException(status_code=400, detail="Failed to train models - insufficient or invalid data")
        
        return TrainingStatusResponse(
            status="success",
            model_scores=model_scores,
            feature_importance=analytics_engine.feature_importance,
            last_trained=datetime.now(),
            data_points_used=len(request.campaign_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training models: {e}")
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@router.get("/model-status", response_model=Dict[str, Union[str, Dict]])
async def get_model_status() -> Dict[str, Union[str, Dict]]:
    """
    Get current status of predictive models
    """
    try:
        return {
            "status": "ready" if analytics_engine.models else "not_initialized",
            "available_models": list(analytics_engine.models.keys()),
            "historical_accuracy": analytics_engine.historical_accuracy,
            "feature_importance": analytics_engine.feature_importance
        }
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")

# Helper functions
async def _fetch_historical_data(days: int, platforms: List[str]) -> List[Dict]:
    """Fetch historical performance data (mock implementation)"""
    try:
        # Mock data generation for demonstration
        import random
        from datetime import datetime, timedelta
        
        data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            
            for platform in platforms:
                # Generate realistic mock data with trends
                base_impressions = random.randint(1000, 5000) + i * 10  # Slight upward trend
                base_clicks = int(base_impressions * random.uniform(0.02, 0.05))
                base_conversions = int(base_clicks * random.uniform(0.05, 0.15))
                base_spend = base_clicks * random.uniform(1.0, 3.0)
                base_revenue = base_conversions * random.uniform(50, 200)
                
                data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'platform': platform,
                    'campaign_id': f'{platform}_campaign_{random.randint(1, 5)}',
                    'impressions': base_impressions,
                    'clicks': base_clicks,
                    'conversions': base_conversions,
                    'spend': round(base_spend, 2),
                    'revenue': round(base_revenue, 2)
                })
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return []

async def _fetch_platform_data(platform: str, days: int) -> List[Dict]:
    """Fetch data for a specific platform"""
    all_data = await _fetch_historical_data(days, [platform])
    return [item for item in all_data if item['platform'] == platform]

async def _organize_data_by_platform(historical_data: List[Dict]) -> Dict[str, List[Dict]]:
    """Organize data by platform for correlation analysis"""
    platform_data = {}
    
    for item in historical_data:
        platform = item.get('platform', 'unknown')
        if platform not in platform_data:
            platform_data[platform] = []
        platform_data[platform].append(item)
    
    return platform_data

def _calculate_summary_stats(historical_data: List[Dict], trends: List[PerformanceTrend], forecast: PredictiveMetrics) -> Dict[str, Union[str, float, int]]:
    """Calculate summary statistics for analytics overview"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(historical_data)
        
        total_impressions = df['impressions'].sum() if 'impressions' in df.columns else 0
        total_clicks = df['clicks'].sum() if 'clicks' in df.columns else 0
        total_spend = df['spend'].sum() if 'spend' in df.columns else 0
        total_revenue = df['revenue'].sum() if 'revenue' in df.columns else 0
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0
        
        # Count trends
        positive_trends = len([t for t in trends if t.trend_direction == 'up'])
        negative_trends = len([t for t in trends if t.trend_direction == 'down'])
        
        return {
            'total_impressions': int(total_impressions),
            'total_clicks': int(total_clicks),
            'total_spend': round(total_spend, 2),
            'total_revenue': round(total_revenue, 2),
            'average_ctr': round(avg_ctr, 2),
            'average_roas': round(avg_roas, 2),
            'positive_trends': positive_trends,
            'negative_trends': negative_trends,
            'forecast_confidence': round(forecast.confidence_score * 100, 1),
            'prediction_period': forecast.forecast_period
        }
        
    except Exception as e:
        logger.error(f"Error calculating summary stats: {e}")
        return {}

# Export router
__all__ = ['router']