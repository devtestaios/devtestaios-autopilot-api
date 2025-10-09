"""
Unit tests for Attribution Database Service
Tests all database operations for attribution engine
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.database import Base
from app.attribution.db_service import AttributionDatabaseService
from app.attribution.db_models import (
    AttributionTouchpoint,
    AttributionConversion,
    AttributionJourney,
    AttributionResult,
    AttributionModelState
)
from app.attribution.event_schema import (
    TouchpointEvent,
    ConversionEvent,
    CustomerJourney,
    Platform,
    EventType
)
from app.attribution.models import (
    AttributionResult as AttributionResultModel,
    AttributionModelType,
    PlatformAttribution
)


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh in-memory SQLite database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def db_service(test_db):
    """Create database service instance"""
    return AttributionDatabaseService(test_db)


@pytest.fixture
def sample_touchpoint():
    """Create a sample touchpoint event"""
    return TouchpointEvent(
        event_id="test_event_1",
        user_id="user_123",
        event_type=EventType.CLICK,
        platform=Platform.META,
        timestamp=datetime.now(),
        campaign_id="campaign_001",
        campaign_name="Test Campaign",
        ad_set_id="adset_001",
        ad_id="ad_001",
        utm_source="meta",
        utm_medium="cpc",
        utm_campaign="test_campaign",
        page_url="https://example.com/landing",
        referrer_url="https://meta.com",
        device_type="mobile",
        country="US",
        city="New York"
    )


@pytest.fixture
def sample_conversion():
    """Create a sample conversion event"""
    return ConversionEvent(
        conversion_id="conv_001",
        user_id="user_123",
        conversion_type="purchase",
        timestamp=datetime.now(),
        revenue=99.99,
        currency="USD",
        attribution_window_days=30,
        order_id="order_123",
        product_ids=["prod_1", "prod_2"]
    )


@pytest.fixture
def sample_journey(sample_touchpoint, sample_conversion):
    """Create a sample customer journey"""
    touchpoints = [
        sample_touchpoint,
        TouchpointEvent(
            event_id="test_event_2",
            user_id="user_123",
            event_type=EventType.VIEW,
            platform=Platform.GOOGLE_SEARCH,
            timestamp=datetime.now() + timedelta(hours=1),
            campaign_id="campaign_002"
        )
    ]
    return CustomerJourney.from_touchpoints(
        user_id="user_123",
        touchpoints=touchpoints,
        conversion=sample_conversion
    )


# ==================== TOUCHPOINT TESTS ====================

def test_save_touchpoint(db_service, sample_touchpoint):
    """Test saving a touchpoint to database"""
    journey_id = "journey_001"

    db_touchpoint = db_service.save_touchpoint(sample_touchpoint, journey_id)

    assert db_touchpoint.id == sample_touchpoint.event_id
    assert db_touchpoint.user_id == sample_touchpoint.user_id
    assert db_touchpoint.platform == sample_touchpoint.platform.value
    assert db_touchpoint.journey_id == journey_id
    assert db_touchpoint.campaign_id == sample_touchpoint.campaign_id


def test_get_touchpoints_for_journey(db_service, sample_touchpoint):
    """Test retrieving touchpoints for a journey"""
    journey_id = "journey_001"

    # Save multiple touchpoints
    db_service.save_touchpoint(sample_touchpoint, journey_id)

    touchpoint2 = TouchpointEvent(
        event_id="test_event_2",
        user_id="user_123",
        event_type=EventType.VIEW,
        platform=Platform.GOOGLE_SEARCH,
        timestamp=datetime.now() + timedelta(hours=1)
    )
    db_service.save_touchpoint(touchpoint2, journey_id)

    # Retrieve touchpoints
    touchpoints = db_service.get_touchpoints_for_journey(journey_id)

    assert len(touchpoints) == 2
    assert touchpoints[0].id == sample_touchpoint.event_id
    assert touchpoints[1].id == touchpoint2.event_id


def test_get_touchpoints_for_user(db_service, sample_touchpoint):
    """Test retrieving all touchpoints for a user"""
    journey_id = "journey_001"

    db_service.save_touchpoint(sample_touchpoint, journey_id)

    touchpoints = db_service.get_touchpoints_for_user("user_123")

    assert len(touchpoints) == 1
    assert touchpoints[0].user_id == "user_123"


def test_get_touchpoints_for_user_with_date_range(db_service):
    """Test retrieving touchpoints within date range"""
    journey_id = "journey_001"
    now = datetime.now()

    # Touchpoint from yesterday
    old_touchpoint = TouchpointEvent(
        event_id="old_event",
        user_id="user_123",
        event_type=EventType.CLICK,
        platform=Platform.META,
        timestamp=now - timedelta(days=1)
    )
    db_service.save_touchpoint(old_touchpoint, journey_id)

    # Touchpoint from today
    new_touchpoint = TouchpointEvent(
        event_id="new_event",
        user_id="user_123",
        event_type=EventType.CLICK,
        platform=Platform.META,
        timestamp=now
    )
    db_service.save_touchpoint(new_touchpoint, journey_id)

    # Get only today's touchpoints
    touchpoints = db_service.get_touchpoints_for_user(
        "user_123",
        start_date=now - timedelta(hours=1)
    )

    assert len(touchpoints) == 1
    assert touchpoints[0].id == "new_event"


# ==================== CONVERSION TESTS ====================

def test_save_conversion(db_service, sample_conversion):
    """Test saving a conversion to database"""
    journey_id = "journey_001"

    db_conversion = db_service.save_conversion(sample_conversion, journey_id)

    assert db_conversion.id == sample_conversion.conversion_id
    assert db_conversion.user_id == sample_conversion.user_id
    assert db_conversion.revenue == sample_conversion.revenue
    assert db_conversion.journey_id == journey_id


def test_get_conversion_for_journey(db_service, sample_conversion):
    """Test retrieving conversion for a journey"""
    journey_id = "journey_001"

    db_service.save_conversion(sample_conversion, journey_id)

    conversion = db_service.get_conversion_for_journey(journey_id)

    assert conversion is not None
    assert conversion.id == sample_conversion.conversion_id
    assert conversion.revenue == sample_conversion.revenue


# ==================== JOURNEY TESTS ====================

def test_create_journey(db_service, sample_journey):
    """Test creating a new journey"""
    db_journey = db_service.create_or_update_journey(sample_journey)

    assert db_journey.id == sample_journey.journey_id
    assert db_journey.user_id == sample_journey.user_id
    assert db_journey.converted == sample_journey.converted
    assert db_journey.total_touchpoints == sample_journey.total_touchpoints
    assert db_journey.unique_platforms == sample_journey.unique_platforms


def test_update_journey(db_service, sample_journey):
    """Test updating an existing journey"""
    # Create journey
    db_journey = db_service.create_or_update_journey(sample_journey)
    assert db_journey.converted == True

    # Update journey (add another touchpoint)
    sample_journey.touchpoints.append(
        TouchpointEvent(
            event_id="test_event_3",
            user_id="user_123",
            event_type=EventType.CLICK,
            platform=Platform.LINKEDIN,
            timestamp=datetime.now() + timedelta(hours=2)
        )
    )
    sample_journey.total_touchpoints = len(sample_journey.touchpoints)

    updated_journey = db_service.create_or_update_journey(sample_journey)

    assert updated_journey.id == db_journey.id
    assert updated_journey.total_touchpoints == 3


def test_get_journey(db_service, sample_journey):
    """Test retrieving a journey by ID"""
    db_service.create_or_update_journey(sample_journey)

    journey = db_service.get_journey(sample_journey.journey_id)

    assert journey is not None
    assert journey.id == sample_journey.journey_id
    assert journey.user_id == sample_journey.user_id


def test_get_journey_for_user(db_service, sample_journey):
    """Test retrieving most recent journey for a user"""
    db_service.create_or_update_journey(sample_journey)

    journey = db_service.get_journey_for_user("user_123")

    assert journey is not None
    assert journey.user_id == "user_123"


def test_build_journey_from_db(db_service, sample_journey, sample_touchpoint):
    """Test building CustomerJourney object from database"""
    # Create journey
    db_journey = db_service.create_or_update_journey(sample_journey)

    # Save touchpoints
    for touchpoint in sample_journey.touchpoints:
        db_service.save_touchpoint(touchpoint, db_journey.id)

    # Save conversion
    if sample_journey.conversion:
        db_service.save_conversion(sample_journey.conversion, db_journey.id)

    # Build journey from DB
    rebuilt_journey = db_service.build_journey_from_db(db_journey.id)

    assert rebuilt_journey is not None
    assert rebuilt_journey.journey_id == sample_journey.journey_id
    assert rebuilt_journey.user_id == sample_journey.user_id
    assert len(rebuilt_journey.touchpoints) == len(sample_journey.touchpoints)
    assert rebuilt_journey.converted == sample_journey.converted


def test_get_recent_journeys(db_service, sample_journey):
    """Test retrieving recent journeys"""
    # Create multiple journeys
    db_service.create_or_update_journey(sample_journey)

    journey2 = CustomerJourney(
        journey_id="journey_002",
        user_id="user_456",
        touchpoints=[],
        conversion=None
    )
    db_service.create_or_update_journey(journey2)

    # Get all journeys
    journeys = db_service.get_recent_journeys(limit=10)
    assert len(journeys) == 2

    # Get only converted journeys
    converted_journeys = db_service.get_recent_journeys(converted_only=True)
    assert len(converted_journeys) == 1
    assert converted_journeys[0].converted == True


# ==================== ATTRIBUTION RESULT TESTS ====================

def test_save_attribution_result(db_service, sample_journey):
    """Test saving attribution result"""
    # Create journey first
    db_journey = db_service.create_or_update_journey(sample_journey)

    # Create attribution result
    result = AttributionResultModel(
        journey_id=sample_journey.journey_id,
        user_id=sample_journey.user_id,
        model_type=AttributionModelType.SHAPLEY,
        model_version="1.0.0",
        platform_attribution=[
            PlatformAttribution(
                platform=Platform.META,
                credit=0.6,
                touchpoint_count=1,
                revenue_attributed=59.99
            ),
            PlatformAttribution(
                platform=Platform.GOOGLE_SEARCH,
                credit=0.4,
                touchpoint_count=1,
                revenue_attributed=39.99
            )
        ],
        campaign_attribution=[],
        converted=True,
        conversion_value=99.99,
        total_touchpoints=2,
        unique_platforms=2,
        confidence_score=0.85,
        insights=["Meta drove 60% of conversion"]
    )

    db_result = db_service.save_attribution_result(result, db_journey.id)

    assert db_result.journey_id == db_journey.id
    assert db_result.model_type == "shapley"
    assert db_result.converted == True
    assert len(db_result.platform_attribution) == 2
    assert db_result.confidence_score == 0.85


def test_get_attribution_results_for_journey(db_service, sample_journey):
    """Test retrieving attribution results"""
    db_journey = db_service.create_or_update_journey(sample_journey)

    # Create and save result
    result = AttributionResultModel(
        journey_id=sample_journey.journey_id,
        user_id=sample_journey.user_id,
        model_type=AttributionModelType.SHAPLEY,
        platform_attribution=[],
        campaign_attribution=[],
        converted=True,
        conversion_value=99.99,
        total_touchpoints=2,
        unique_platforms=2,
        confidence_score=0.85
    )
    db_service.save_attribution_result(result, db_journey.id)

    # Retrieve results
    results = db_service.get_attribution_results_for_journey(db_journey.id)

    assert len(results) == 1
    assert results[0].journey_id == db_journey.id
    assert results[0].model_type == "shapley"


# ==================== MODEL STATE TESTS ====================

def test_save_model_state(db_service):
    """Test saving model state"""
    model_state = {
        "transitions": {"A": {"B": 0.7}},
        "state_counts": {"A": 100},
        "conversion_probs": {"B": 0.3}
    }

    db_state = db_service.save_model_state(
        model_type="markov",
        model_state=model_state,
        training_journeys_count=500
    )

    assert db_state.model_type == "markov"
    assert db_state.is_trained == True
    assert db_state.is_active == True
    assert db_state.training_journeys_count == 500
    assert "transitions" in db_state.model_state


def test_get_active_model_state(db_service):
    """Test retrieving active model state"""
    model_state = {
        "transitions": {"A": {"B": 0.7}}
    }

    db_service.save_model_state(
        model_type="markov",
        model_state=model_state,
        training_journeys_count=500
    )

    active_state = db_service.get_active_model_state("markov")

    assert active_state is not None
    assert active_state.model_type == "markov"
    assert active_state.is_active == True
    assert "transitions" in active_state.model_state


def test_model_state_deactivation(db_service):
    """Test that saving new model state deactivates old one"""
    # Save first model state
    model_state_1 = {"version": 1}
    db_service.save_model_state(
        model_type="markov",
        model_state=model_state_1,
        training_journeys_count=100
    )

    # Save second model state
    model_state_2 = {"version": 2}
    db_service.save_model_state(
        model_type="markov",
        model_state=model_state_2,
        training_journeys_count=200
    )

    # Only second state should be active
    active_state = db_service.get_active_model_state("markov")

    assert active_state.model_state["version"] == 2
    assert active_state.training_journeys_count == 200


# ==================== INTEGRATION TESTS ====================

def test_complete_attribution_flow(db_service, sample_touchpoint, sample_conversion):
    """Test complete attribution flow from touchpoint to result"""
    # 1. Create journey
    journey = CustomerJourney(
        journey_id="journey_test_flow",
        user_id="user_flow_test",
        touchpoints=[],
        conversion=None
    )
    db_journey = db_service.create_or_update_journey(journey)

    # 2. Add touchpoints
    db_service.save_touchpoint(sample_touchpoint, db_journey.id)

    # 3. Add conversion
    sample_conversion.user_id = "user_flow_test"
    db_service.save_conversion(sample_conversion, db_journey.id)

    # 4. Update journey as converted
    journey.converted = True
    journey.conversion = sample_conversion
    db_service.create_or_update_journey(journey)

    # 5. Save attribution result
    result = AttributionResultModel(
        journey_id=journey.journey_id,
        user_id=journey.user_id,
        model_type=AttributionModelType.SHAPLEY,
        platform_attribution=[],
        campaign_attribution=[],
        converted=True,
        conversion_value=sample_conversion.revenue,
        total_touchpoints=1,
        unique_platforms=1,
        confidence_score=0.9
    )
    db_service.save_attribution_result(result, db_journey.id)

    # 6. Verify complete flow
    rebuilt_journey = db_service.build_journey_from_db(db_journey.id)
    assert rebuilt_journey is not None
    assert rebuilt_journey.converted == True
    assert len(rebuilt_journey.touchpoints) == 1
    assert rebuilt_journey.conversion is not None

    results = db_service.get_attribution_results_for_journey(db_journey.id)
    assert len(results) == 1
    assert results[0].converted == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
