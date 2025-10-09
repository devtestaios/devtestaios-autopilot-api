"""
Integration tests for Attribution API Endpoints
Tests the complete HTTP API for attribution engine
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.attribution.event_schema import Platform


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh in-memory SQLite database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Override the get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client with test database"""
    return TestClient(app)


# ==================== HEALTH CHECK TESTS ====================

def test_health_check(client):
    """Test attribution engine health endpoint"""
    response = client.get("/api/v1/attribution/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "shapley_attribution" in data["capabilities"]
    assert "markov_attribution" in data["capabilities"]


def test_models_status(client):
    """Test attribution models status endpoint"""
    response = client.get("/api/v1/attribution/models/status")

    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "shapley" in data["models"]
    assert "markov" in data["models"]
    assert data["models"]["shapley"]["available"] == True


# ==================== TOUCHPOINT TRACKING TESTS ====================

def test_track_touchpoint(client):
    """Test tracking a touchpoint event"""
    touchpoint_data = {
        "user_id": "test_user_001",
        "event_type": "click",
        "platform": "meta",
        "timestamp": datetime.now().isoformat(),
        "campaign_id": "campaign_001",
        "campaign_name": "Test Campaign",
        "utm_source": "meta",
        "utm_medium": "cpc",
        "country": "US",
        "device_type": "mobile"
    }

    response = client.post("/api/v1/attribution/track/event", json=touchpoint_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "event_id" in data
    assert "journey_id" in data
    assert data["message"] == "Touchpoint tracked"


def test_track_multiple_touchpoints_same_user(client):
    """Test tracking multiple touchpoints for same user creates one journey"""
    user_id = "test_user_multi"

    # Track first touchpoint
    touchpoint1 = {
        "user_id": user_id,
        "event_type": "impression",
        "platform": "meta",
        "campaign_id": "campaign_001"
    }
    response1 = client.post("/api/v1/attribution/track/event", json=touchpoint1)
    journey_id_1 = response1.json()["journey_id"]

    # Track second touchpoint
    touchpoint2 = {
        "user_id": user_id,
        "event_type": "click",
        "platform": "google_ads",
        "campaign_id": "campaign_002"
    }
    response2 = client.post("/api/v1/attribution/track/event", json=touchpoint2)
    journey_id_2 = response2.json()["journey_id"]

    # Both should be in same journey
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert journey_id_1 == journey_id_2


def test_track_touchpoint_invalid_platform(client):
    """Test tracking touchpoint with invalid platform"""
    touchpoint_data = {
        "user_id": "test_user_invalid",
        "event_type": "click",
        "platform": "invalid_platform",
        "timestamp": datetime.now().isoformat()
    }

    response = client.post("/api/v1/attribution/track/event", json=touchpoint_data)

    # Should fail validation
    assert response.status_code in [422, 500]  # Validation error or internal error


# ==================== CONVERSION TRACKING TESTS ====================

def test_track_conversion(client):
    """Test tracking a conversion event"""
    user_id = "test_user_conversion"

    # First track a touchpoint
    touchpoint = {
        "user_id": user_id,
        "event_type": "click",
        "platform": "meta",
        "campaign_id": "campaign_001"
    }
    client.post("/api/v1/attribution/track/event", json=touchpoint)

    # Then track conversion
    conversion_data = {
        "user_id": user_id,
        "conversion_type": "purchase",
        "revenue": 99.99,
        "timestamp": datetime.now().isoformat(),
        "attribution_window_days": 30,
        "order_id": "order_123",
        "product_ids": ["prod_1", "prod_2"]
    }

    response = client.post("/api/v1/attribution/track/conversion", json=conversion_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "conversion_id" in data
    assert "journey_id" in data
    assert data["revenue"] == 99.99
    assert "attribution analysis queued" in data["message"]


def test_track_conversion_without_touchpoints(client):
    """Test tracking conversion for user with no touchpoints"""
    conversion_data = {
        "user_id": "user_no_touchpoints",
        "conversion_type": "purchase",
        "revenue": 50.00,
        "timestamp": datetime.now().isoformat()
    }

    response = client.post("/api/v1/attribution/track/conversion", json=conversion_data)

    # Should still succeed (create conversion-only journey)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_track_conversion_missing_required_fields(client):
    """Test tracking conversion with missing required fields"""
    conversion_data = {
        "conversion_type": "purchase",
        "revenue": 100.00
        # Missing user_id
    }

    response = client.post("/api/v1/attribution/track/conversion", json=conversion_data)

    assert response.status_code == 422  # Validation error


# ==================== JOURNEY ANALYSIS TESTS ====================

def test_analyze_journey_shapley(client):
    """Test analyzing a journey with Shapley model"""
    user_id = "test_user_analyze"

    # Create a journey with touchpoints
    client.post("/api/v1/attribution/track/event", json={
        "user_id": user_id,
        "event_type": "click",
        "platform": "meta",
        "campaign_id": "campaign_001"
    })

    client.post("/api/v1/attribution/track/event", json={
        "user_id": user_id,
        "event_type": "click",
        "platform": "google_search",
        "campaign_id": "campaign_002"
    })

    # Add conversion
    client.post("/api/v1/attribution/track/conversion", json={
        "user_id": user_id,
        "conversion_type": "purchase",
        "revenue": 150.00
    })

    # Analyze journey
    analysis_request = {
        "user_id": user_id,
        "model_type": "shapley"
    }

    response = client.post("/api/v1/attribution/analyze/journey", json=analysis_request)

    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "shapley"
    assert data["converted"] == True
    assert data["conversion_value"] == 150.00
    assert len(data["platform_attribution"]) > 0
    assert "insights" in data


def test_analyze_journey_markov(client):
    """Test analyzing a journey with Markov model"""
    user_id = "test_user_markov"

    # Create journey
    client.post("/api/v1/attribution/track/event", json={
        "user_id": user_id,
        "event_type": "click",
        "platform": "linkedin",
        "campaign_id": "campaign_001"
    })

    client.post("/api/v1/attribution/track/conversion", json={
        "user_id": user_id,
        "conversion_type": "lead",
        "revenue": 0.00
    })

    # Analyze with Markov (note: may fall back to linear if not trained)
    analysis_request = {
        "user_id": user_id,
        "model_type": "markov"
    }

    response = client.post("/api/v1/attribution/analyze/journey", json=analysis_request)

    assert response.status_code == 200
    data = response.json()
    # Model type may be "markov" or "linear" (fallback)
    assert data["model_type"] in ["markov", "linear"]


def test_analyze_journey_not_found(client):
    """Test analyzing non-existent journey"""
    analysis_request = {
        "user_id": "user_does_not_exist",
        "model_type": "shapley"
    }

    response = client.post("/api/v1/attribution/analyze/journey", json=analysis_request)

    assert response.status_code == 404
    assert "No journey found" in response.json()["detail"]


# ==================== BATCH ANALYSIS TESTS ====================

def test_analyze_batch(client):
    """Test batch analysis of multiple journeys"""
    # Create multiple journeys
    for i in range(3):
        user_id = f"batch_user_{i}"

        client.post("/api/v1/attribution/track/event", json={
            "user_id": user_id,
            "event_type": "click",
            "platform": "meta",
            "campaign_id": "campaign_001"
        })

        client.post("/api/v1/attribution/track/conversion", json={
            "user_id": user_id,
            "conversion_type": "purchase",
            "revenue": 100.00 * (i + 1)
        })

    # Batch analyze
    batch_request = {
        "user_ids": ["batch_user_0", "batch_user_1", "batch_user_2"],
        "model_type": "shapley"
    }

    response = client.post("/api/v1/attribution/analyze/batch", json=batch_request)

    assert response.status_code == 200
    data = response.json()
    assert data["total_journeys"] == 3
    assert data["converted_journeys"] == 3
    assert data["total_revenue"] == 600.00  # 100 + 200 + 300
    assert "platform_attribution" in data
    assert "insights" in data


# ==================== MARKOV TRAINING TESTS ====================

def test_train_markov(client):
    """Test training Markov model"""
    # Create some training data first
    for i in range(5):
        user_id = f"train_user_{i}"

        client.post("/api/v1/attribution/track/event", json={
            "user_id": user_id,
            "event_type": "click",
            "platform": "meta"
        })

        client.post("/api/v1/attribution/track/conversion", json={
            "user_id": user_id,
            "conversion_type": "purchase",
            "revenue": 50.00
        })

    # Train model
    train_request = {
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "min_touchpoints": 1
    }

    response = client.post("/api/v1/attribution/train/markov", json=train_request)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "training_queued"
    assert "training_period" in data


# ==================== COMPLETE WORKFLOW TEST ====================

def test_complete_attribution_workflow(client):
    """Test complete attribution workflow from tracking to analysis"""
    user_id = "workflow_test_user"

    # Step 1: Track first touchpoint (Meta ad)
    response1 = client.post("/api/v1/attribution/track/event", json={
        "user_id": user_id,
        "event_type": "impression",
        "platform": "meta",
        "campaign_id": "meta_campaign_001",
        "campaign_name": "Meta Brand Awareness"
    })
    assert response1.status_code == 200
    journey_id = response1.json()["journey_id"]

    # Step 2: Track second touchpoint (Google Search)
    response2 = client.post("/api/v1/attribution/track/event", json={
        "user_id": user_id,
        "event_type": "click",
        "platform": "google_search",
        "campaign_id": "google_campaign_001",
        "campaign_name": "Google Search Brand"
    })
    assert response2.status_code == 200
    assert response2.json()["journey_id"] == journey_id  # Same journey

    # Step 3: Track third touchpoint (LinkedIn)
    response3 = client.post("/api/v1/attribution/track/event", json={
        "user_id": user_id,
        "event_type": "click",
        "platform": "linkedin",
        "campaign_id": "linkedin_campaign_001",
        "campaign_name": "LinkedIn Retargeting"
    })
    assert response3.status_code == 200

    # Step 4: Track conversion
    response4 = client.post("/api/v1/attribution/track/conversion", json={
        "user_id": user_id,
        "conversion_type": "purchase",
        "revenue": 299.99,
        "order_id": "order_workflow_test",
        "product_ids": ["prod_premium"]
    })
    assert response4.status_code == 200
    assert "attribution analysis queued" in response4.json()["message"]

    # Step 5: Analyze journey
    response5 = client.post("/api/v1/attribution/analyze/journey", json={
        "user_id": user_id,
        "model_type": "shapley"
    })
    assert response5.status_code == 200

    result = response5.json()

    # Verify attribution result
    assert result["converted"] == True
    assert result["conversion_value"] == 299.99
    assert result["total_touchpoints"] == 3
    assert result["unique_platforms"] == 3
    assert len(result["platform_attribution"]) == 3
    assert result["model_type"] == "shapley"
    assert result["confidence_score"] > 0
    assert len(result["insights"]) > 0

    # Verify platforms are correctly attributed
    platforms = [pa["platform"] for pa in result["platform_attribution"]]
    assert "meta" in platforms
    assert "google_search" in platforms
    assert "linkedin" in platforms

    # Verify credits sum to 1.0 (or close to it)
    total_credit = sum(pa["credit"] for pa in result["platform_attribution"])
    assert abs(total_credit - 1.0) < 0.01  # Allow small floating point error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
