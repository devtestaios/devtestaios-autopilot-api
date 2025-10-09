"""
Attribution API Endpoints
Multi-platform attribution analysis powered by AI

This is the CORE value prop - what sets PulseBridge apart
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import uuid

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
from app.attribution.db_service import AttributionDatabaseService
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/attribution", tags=["Attribution Engine"])

# Global model instances
_shapley_model = None
_markov_model = None


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
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now())

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
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now())

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
async def track_touchpoint(
    request: TrackEventRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
        db_service = AttributionDatabaseService(db)

        # Convert request to TouchpointEvent
        event = TouchpointEvent(
            event_id=f"{request.user_id}_{int(request.timestamp.timestamp())}_{uuid.uuid4().hex[:8]}",
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

        # Get or create journey for this user
        journey = db_service.get_journey_for_user(request.user_id, active_only=True)
        if not journey:
            # Create new journey
            journey_id = f"journey_{request.user_id}_{uuid.uuid4().hex[:12]}"
            temp_journey = CustomerJourney(
                journey_id=journey_id,
                user_id=request.user_id,
                touchpoints=[event],
                conversion=None
            )
            db_service.create_or_update_journey(temp_journey)
        else:
            journey_id = journey.id

        # Save touchpoint to database
        db_service.save_touchpoint(event, journey_id)

        logger.info(f"Tracked touchpoint {event.event_id} for user {request.user_id}")

        return {
            "status": "success",
            "event_id": event.event_id,
            "journey_id": journey_id,
            "message": "Touchpoint tracked",
            "timestamp": event.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track/conversion")
async def track_conversion(
    request: TrackConversionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Track a conversion and trigger attribution analysis

    This is the key event - when someone converts, we analyze their
    entire journey to determine which touchpoints deserve credit.

    Automatically runs attribution in the background and stores results.
    """
    try:
        db_service = AttributionDatabaseService(db)

        # Create conversion event
        conversion = ConversionEvent(
            conversion_id=f"{request.user_id}_{int(request.timestamp.timestamp())}_{uuid.uuid4().hex[:8]}",
            user_id=request.user_id,
            conversion_type=request.conversion_type,
            timestamp=request.timestamp,
            revenue=request.revenue,
            attribution_window_days=request.attribution_window_days,
            order_id=request.order_id,
            product_ids=request.product_ids
        )

        # Get existing journey for this user
        journey = db_service.get_journey_for_user(request.user_id, active_only=True)
        if not journey:
            # No journey exists - create one with just the conversion
            logger.warning(f"No journey found for user {request.user_id}, creating conversion-only journey")
            journey_id = f"journey_{request.user_id}_{uuid.uuid4().hex[:12]}"
            temp_journey = CustomerJourney(
                journey_id=journey_id,
                user_id=request.user_id,
                touchpoints=[],
                conversion=conversion
            )
            db_service.create_or_update_journey(temp_journey)
        else:
            journey_id = journey.id
            # Update journey to mark as converted
            journey.converted = True
            journey.conversion_id = conversion.conversion_id

        # Save conversion to database
        db_service.save_conversion(conversion, journey_id)

        # Queue attribution analysis in background
        background_tasks.add_task(
            _analyze_and_save_attribution,
            journey_id,
            db
        )

        logger.info(f"Tracked conversion {conversion.conversion_id} for user {request.user_id}")

        return {
            "status": "success",
            "conversion_id": conversion.conversion_id,
            "journey_id": journey_id,
            "message": "Conversion tracked, attribution analysis queued",
            "revenue": conversion.revenue,
            "timestamp": conversion.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/journey", response_model=AttributionResult)
async def analyze_journey(
    request: AnalyzeJourneyRequest,
    db: Session = Depends(get_db)
) -> AttributionResult:
    """
    Analyze attribution for a single customer journey

    Returns detailed breakdown of which touchpoints/platforms/campaigns
    contributed to the conversion (if any).

    This is the core value proposition - showing marketers exactly where
    their customers came from.
    """
    try:
        db_service = AttributionDatabaseService(db)

        # Get journey from database
        db_journey = db_service.get_journey_for_user(request.user_id, active_only=False)
        if not db_journey:
            raise HTTPException(
                status_code=404,
                detail=f"No journey found for user {request.user_id}"
            )

        # Build CustomerJourney from database
        journey = db_service.build_journey_from_db(db_journey.id)
        if not journey:
            raise HTTPException(
                status_code=404,
                detail=f"Could not build journey for user {request.user_id}"
            )

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

        # Calculate attribution
        result = model.calculate_attribution(journey)

        # Save result to database
        db_service.save_attribution_result(result, db_journey.id)

        logger.info(f"Analyzed journey {db_journey.id} using {request.model_type.value}")

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Train Markov attribution model on historical data

    The Markov model learns conversion probabilities from actual journeys.
    More data = better attribution accuracy.

    Should be run weekly or after collecting significant new data.
    """
    try:
        # Queue training job (can take minutes for large datasets)
        background_tasks.add_task(_train_markov_background, request, db)

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

async def _analyze_and_save_attribution(journey_id: str, db: Session):
    """Background task to analyze journey and save attribution result"""
    try:
        db_service = AttributionDatabaseService(db)

        # Build journey from database
        journey = db_service.build_journey_from_db(journey_id)
        if not journey:
            logger.error(f"Could not build journey {journey_id} for attribution")
            return

        # Analyze with Shapley model
        shapley = get_shapley_model()
        result = shapley.calculate_attribution(journey)

        # Save result to database
        db_service.save_attribution_result(result, journey_id)

        logger.info(f"Attribution complete for journey {journey_id}: {result.insights}")

    except Exception as e:
        logger.error(f"Error in background attribution for journey {journey_id}: {e}")


async def _train_markov_background(request: TrainMarkovRequest, db: Session):
    """Background task to train Markov model"""
    try:
        db_service = AttributionDatabaseService(db)
        model = get_markov_model()

        # Fetch converted journeys from database for training
        db_journeys = db_service.get_recent_journeys(
            limit=1000,
            converted_only=True,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Build CustomerJourney objects
        journeys = []
        for db_journey in db_journeys:
            journey = db_service.build_journey_from_db(db_journey.id)
            if journey and len(journey.touchpoints) >= request.min_touchpoints:
                journeys.append(journey)

        if len(journeys) < 10:
            logger.warning(f"Only {len(journeys)} journeys available for training, need at least 10")
            return

        # Train model
        model.train(journeys)

        # Save model state to database
        model_state = {
            "transitions": dict(model.transitions),
            "state_counts": dict(model.state_counts),
            "conversion_probs": dict(model.conversion_probs)
        }
        db_service.save_model_state(
            model_type="markov",
            model_state=model_state,
            training_journeys_count=len(journeys)
        )

        logger.info(f"Markov model training complete with {len(journeys)} journeys")

    except Exception as e:
        logger.error(f"Error training Markov model: {e}")


# Helper functions


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
