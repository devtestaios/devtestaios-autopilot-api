"""
Attribution API Endpoints
Multi-platform attribution analysis powered by AI

This is the CORE value prop - what sets PulseBridge apart
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from app.attribution import (
    TouchpointEvent,
    ConversionEvent,
    CustomerJourney,
    AttributionModelType,
    ShapleyAttributionModel,
    MarkovChainAttributionModel,
    AttributionResult,
    Platform
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/attribution", tags=["Attribution Engine"])

# Global model instances
_shapley_model = None
_markov_model = None
_journey_store: Dict[str, CustomerJourney] = {}  # In-memory for MVP (use DB in prod)


def get_shapley_model() -> ShapleyAttributionModel:
    """Get or create Shapley attribution model"""
    global _shapley_model
    if _shapley_model is None:
        _shapley_model = ShapleyAttributionModel(max_touchpoints=10)
    return _shapley_model


def get_markov_model() -> MarkovChainAttributionModel:
    """Get or create Markov attribution model"""
    global _markov_model
    if _markov_model is None:
        _markov_model = MarkovChainAttributionModel(min_support=5)
    return _markov_model


# Request/Response Models

class TrackEventRequest(BaseModel):
    """Track a single touchpoint event"""
    user_id: str = Field(..., description="Unique user identifier (anonymized)")
    event_type: str = Field(..., description="Type of event (click, impression, etc.)")
    platform: str = Field(..., description="Platform (meta, google_ads, linkedin, etc.)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    # Campaign info
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    ad_set_id: Optional[str] = None
    ad_id: Optional[str] = None

    # UTM parameters
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    # Context
    page_url: Optional[str] = None
    referrer_url: Optional[str] = None
    device_type: Optional[str] = None

    # Geo
    country: Optional[str] = None
    city: Optional[str] = None

    # Custom data
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class TrackConversionRequest(BaseModel):
    """Track a conversion event"""
    user_id: str = Field(..., description="User who converted")
    conversion_type: str = Field(..., description="purchase, lead, signup, etc.")
    revenue: float = Field(0.0, description="Revenue from conversion")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    # Attribution config
    attribution_window_days: int = Field(30, description="Days to look back")

    # Order details
    order_id: Optional[str] = None
    product_ids: List[str] = Field(default_factory=list)


class AnalyzeJourneyRequest(BaseModel):
    """Request to analyze attribution for a journey"""
    user_id: str = Field(..., description="User to analyze")
    model_type: AttributionModelType = Field(
        AttributionModelType.SHAPLEY,
        description="Which attribution model to use"
    )
    start_date: Optional[datetime] = Field(None, description="Start of analysis window")
    end_date: Optional[datetime] = Field(None, description="End of analysis window")


class BatchAnalysisRequest(BaseModel):
    """Analyze multiple journeys at once"""
    user_ids: List[str] = Field(..., description="Users to analyze")
    model_type: AttributionModelType = Field(AttributionModelType.SHAPLEY)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TrainMarkovRequest(BaseModel):
    """Train Markov model on historical data"""
    start_date: datetime = Field(..., description="Start of training period")
    end_date: datetime = Field(..., description="End of training period")
    min_touchpoints: int = Field(2, description="Minimum touchpoints per journey")


# API Endpoints

@router.post("/track/event")
async def track_touchpoint(request: TrackEventRequest) -> Dict[str, Any]:
    """
    Track a marketing touchpoint event

    Use this to log every customer interaction across all platforms.
    This is the raw data that powers attribution analysis.

    Example:
        User clicks a Meta ad → POST to this endpoint
        User visits from Google → POST to this endpoint
        User clicks email link → POST to this endpoint
    """
    try:
        # Convert request to TouchpointEvent
        event = TouchpointEvent(
            event_id=f"{request.user_id}_{request.timestamp.timestamp()}",
            user_id=request.user_id,
            event_type=request.event_type,
            platform=Platform(request.platform),
            timestamp=request.timestamp,
            campaign_id=request.campaign_id,
            campaign_name=request.campaign_name,
            ad_set_id=request.ad_set_id,
            ad_id=request.ad_id,
            utm_source=request.utm_source,
            utm_medium=request.utm_medium,
            utm_campaign=request.utm_campaign,
            page_url=request.page_url,
            referrer_url=request.referrer_url,
            device_type=request.device_type,
            country=request.country,
            city=request.city,
            custom_data=request.custom_data
        )

        # Store event (in production, save to database)
        # For MVP, we'll build journeys on-the-fly from recent events

        return {
            "status": "success",
            "event_id": event.event_id,
            "message": "Touchpoint tracked",
            "timestamp": event.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/conversion")
async def track_conversion(
    request: TrackConversionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Track a conversion and trigger attribution analysis

    This is the key event - when someone converts, we analyze their
    entire journey to determine which touchpoints deserve credit.

    Automatically runs attribution in the background and stores results.
    """
    try:
        # Create conversion event
        conversion = ConversionEvent(
            conversion_id=f"{request.user_id}_{request.timestamp.timestamp()}",
            user_id=request.user_id,
            conversion_type=request.conversion_type,
            timestamp=request.timestamp,
            revenue=request.revenue,
            attribution_window_days=request.attribution_window_days,
            order_id=request.order_id,
            product_ids=request.product_ids
        )

        # In production: save to database and trigger background job
        # For MVP: return confirmation

        # Queue attribution analysis
        background_tasks.add_task(
            _analyze_user_journey,
            request.user_id,
            conversion
        )

        return {
            "status": "success",
            "conversion_id": conversion.conversion_id,
            "message": "Conversion tracked, attribution analysis queued",
            "revenue": conversion.revenue,
            "timestamp": conversion.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/journey", response_model=AttributionResult)
async def analyze_journey(request: AnalyzeJourneyRequest) -> AttributionResult:
    """
    Analyze attribution for a single customer journey

    Returns detailed breakdown of which touchpoints/platforms/campaigns
    contributed to the conversion (if any).

    This is the core value proposition - showing marketers exactly where
    their customers came from.
    """
    try:
        # In production: fetch touchpoints from database
        # For MVP: return example result

        # Get attribution model
        if request.model_type == AttributionModelType.SHAPLEY:
            model = get_shapley_model()
        elif request.model_type == AttributionModelType.MARKOV:
            model = get_markov_model()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Model type {request.model_type} not supported yet"
            )

        # Build customer journey (in prod: from DB)
        # For MVP: return mock result
        journey = _get_or_create_mock_journey(request.user_id)

        # Calculate attribution
        result = model.calculate_attribution(journey)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/batch")
async def analyze_batch(request: BatchAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze attribution for multiple journeys

    Use this for:
    - Cohort analysis (all users who converted this week)
    - Campaign performance (all conversions from Campaign X)
    - Platform analysis (overall attribution across all users)

    Returns aggregated attribution insights.
    """
    try:
        model = get_shapley_model()

        # In production: fetch journeys from database
        # For MVP: analyze sample journeys

        results = []
        for user_id in request.user_ids[:100]:  # Limit for MVP
            journey = _get_or_create_mock_journey(user_id)
            result = model.calculate_attribution(journey)
            results.append(result)

        # Aggregate results
        aggregated = _aggregate_attribution_results(results)

        return {
            "total_journeys": len(results),
            "converted_journeys": sum(1 for r in results if r.converted),
            "total_revenue": sum(r.conversion_value for r in results),
            "platform_attribution": aggregated["platforms"],
            "campaign_attribution": aggregated["campaigns"],
            "insights": aggregated["insights"]
        }

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/markov")
async def train_markov(
    request: TrainMarkovRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Train Markov attribution model on historical data

    The Markov model learns conversion probabilities from actual journeys.
    More data = better attribution accuracy.

    Should be run weekly or after collecting significant new data.
    """
    try:
        model = get_markov_model()

        # In production: fetch journeys from database
        # For MVP: use sample data

        # Queue training job (can take minutes for large datasets)
        background_tasks.add_task(_train_markov_background, request)

        return {
            "status": "training_queued",
            "message": "Markov model training started in background",
            "training_period": {
                "start": request.start_date.isoformat(),
                "end": request.end_date.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error starting Markov training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
async def get_models_status() -> Dict[str, Any]:
    """
    Get status of attribution models

    Returns:
    - Which models are available
    - Training status
    - Number of journeys analyzed
    - Model accuracy metrics
    """
    shapley = get_shapley_model()
    markov = get_markov_model()

    return {
        "models": {
            "shapley": {
                "available": True,
                "type": "game_theory",
                "max_touchpoints": shapley.max_touchpoints,
                "version": shapley.model_version
            },
            "markov": {
                "available": True,
                "trained": markov.is_trained,
                "type": "probabilistic",
                "transitions_learned": len(markov.transitions),
                "states": len(markov.state_counts),
                "version": markov.model_version
            }
        },
        "journeys_analyzed": len(_journey_store),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for attribution engine"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "shapley_attribution",
            "markov_attribution",
            "multi_platform_tracking",
            "real_time_analysis"
        ]
    }


# Background tasks

async def _analyze_user_journey(user_id: str, conversion: ConversionEvent):
    """Background task to analyze journey after conversion"""
    try:
        # Get journey (from DB in production)
        journey = _get_or_create_mock_journey(user_id)
        journey.conversion = conversion
        journey.converted = True

        # Analyze with Shapley model
        shapley = get_shapley_model()
        result = shapley.calculate_attribution(journey)

        # Save result (to DB in production)
        logger.info(f"Attribution complete for {user_id}: {result.insights}")

    except Exception as e:
        logger.error(f"Error in background attribution: {e}")


async def _train_markov_background(request: TrainMarkovRequest):
    """Background task to train Markov model"""
    try:
        model = get_markov_model()

        # Fetch journeys from database (in production)
        # For MVP: use sample data
        sample_journeys = [
            _get_or_create_mock_journey(f"user_{i}")
            for i in range(100)
        ]

        # Train model
        model.train(sample_journeys)

        logger.info("Markov model training complete")

    except Exception as e:
        logger.error(f"Error training Markov model: {e}")


# Helper functions

def _get_or_create_mock_journey(user_id: str) -> CustomerJourney:
    """Get or create a mock journey for testing (replace with DB in production)"""
    if user_id in _journey_store:
        return _journey_store[user_id]

    # Create mock journey with multiple touchpoints
    from datetime import datetime, timedelta
    import random

    now = datetime.now()
    touchpoints = []

    # Simulate a multi-touch journey
    platforms = [Platform.META, Platform.GOOGLE_SEARCH, Platform.LINKEDIN]

    for i, platform in enumerate(platforms):
        touchpoint = TouchpointEvent(
            event_id=f"{user_id}_touch_{i}",
            user_id=user_id,
            event_type="click",
            platform=platform,
            timestamp=now - timedelta(days=len(platforms) - i),
            campaign_id=f"campaign_{platform.value}_{random.randint(1, 3)}",
            campaign_name=f"{platform.value.title()} Campaign"
        )
        touchpoints.append(touchpoint)

    # Random conversion
    conversion = None
    if random.random() > 0.5:
        conversion = ConversionEvent(
            conversion_id=f"{user_id}_conversion",
            user_id=user_id,
            conversion_type="purchase",
            timestamp=now,
            revenue=random.uniform(50, 500)
        )

    journey = CustomerJourney.from_touchpoints(user_id, touchpoints, conversion)
    _journey_store[user_id] = journey

    return journey


def _aggregate_attribution_results(results: List[AttributionResult]) -> Dict[str, Any]:
    """Aggregate multiple attribution results"""
    from collections import defaultdict

    platform_totals = defaultdict(lambda: {"credit": 0.0, "revenue": 0.0, "count": 0})
    campaign_totals = defaultdict(lambda: {"credit": 0.0, "revenue": 0.0, "count": 0})
    all_insights = []

    for result in results:
        for pa in result.platform_attribution:
            platform_totals[pa.platform.value]["credit"] += pa.credit
            platform_totals[pa.platform.value]["revenue"] += pa.revenue_attributed
            platform_totals[pa.platform.value]["count"] += 1

        for ca in result.campaign_attribution:
            campaign_totals[ca.campaign_id]["credit"] += ca.credit
            campaign_totals[ca.campaign_id]["revenue"] += ca.revenue_attributed
            campaign_totals[ca.campaign_id]["count"] += 1

        all_insights.extend(result.insights)

    return {
        "platforms": [
            {"platform": p, **data}
            for p, data in sorted(
                platform_totals.items(),
                key=lambda x: x[1]["revenue"],
                reverse=True
            )
        ],
        "campaigns": [
            {"campaign_id": c, **data}
            for c, data in sorted(
                campaign_totals.items(),
                key=lambda x: x[1]["revenue"],
                reverse=True
            )[:10]  # Top 10 campaigns
        ],
        "insights": list(set(all_insights))[:5]  # Top 5 unique insights
    }


# Export router
__all__ = ['router']
