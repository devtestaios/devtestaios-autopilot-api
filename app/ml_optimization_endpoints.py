"""
ML-Powered Optimization Endpoints
Real machine learning budget optimization for Meta ads
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.ml.budget_optimizer import BudgetOptimizerML
from app.ml.meta_data_collector import MetaDataCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ML Optimization"])

# Global ML model instance (lazy initialization)
_budget_optimizer = None

def get_budget_optimizer():
    """Get or create budget optimizer instance"""
    global _budget_optimizer
    if _budget_optimizer is None:
        _budget_optimizer = BudgetOptimizerML()
    return _budget_optimizer


# Request/Response Models
class TrainModelRequest(BaseModel):
    campaign_ids: List[str] = Field(..., description="List of Meta campaign IDs to train on")
    access_token: Optional[str] = Field(None, description="Meta API access token (uses env var if not provided)")
    days_back: int = Field(90, description="Days of historical data to use", ge=30, le=365)
    test_size: float = Field(0.2, description="Proportion of data for testing", ge=0.1, le=0.4)


class BudgetPredictionRequest(BaseModel):
    campaign_id: str = Field(..., description="Meta campaign ID")
    access_token: Optional[str] = Field(None, description="Meta API access token")
    prediction_date: Optional[datetime] = Field(None, description="Date to predict budget for (default: tomorrow)")


class BudgetPredictionResponse(BaseModel):
    predicted_budget: float
    current_budget: float
    budget_change: float
    budget_change_percentage: float
    confidence_score: float
    prediction_date: str
    current_roas: float
    recent_7d_avg_roas: float
    reasoning: str
    model_version: str


class ModelInfoResponse(BaseModel):
    is_trained: bool
    model_version: str
    trained_at: Optional[str]
    training_metrics: Dict[str, float]
    feature_count: int
    model_type: str


@router.post("/train", response_model=Dict[str, Any])
async def train_budget_optimizer(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Train the ML budget optimizer on historical campaign data

    This endpoint:
    - Fetches historical performance data from Meta Ads API
    - Engineers features from the data
    - Trains a Gradient Boosting model
    - Returns training metrics and feature importance

    Training typically takes 30-90 seconds depending on data volume.
    """
    try:
        logger.info(f"Starting ML model training on {len(request.campaign_ids)} campaigns")

        optimizer = get_budget_optimizer()

        # Train the model
        training_results = await optimizer.train_on_multiple_campaigns(
            campaign_ids=request.campaign_ids,
            access_token=request.access_token,
            days_back=request.days_back,
            test_size=request.test_size
        )

        # Save model in background
        background_tasks.add_task(optimizer.save_model)

        return {
            "status": "success",
            "message": f"Model trained on {len(request.campaign_ids)} campaigns",
            **training_results
        }

    except ValueError as e:
        logger.error(f"Training validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/predict", response_model=BudgetPredictionResponse)
async def predict_optimal_budget(request: BudgetPredictionRequest) -> BudgetPredictionResponse:
    """
    Predict optimal budget for a campaign using the trained ML model

    This endpoint:
    - Fetches recent performance data (last 7 days minimum)
    - Generates features from recent performance
    - Uses trained ML model to predict optimal next-day budget
    - Returns prediction with reasoning and confidence score

    Requires model to be trained first via /train endpoint.
    """
    try:
        optimizer = get_budget_optimizer()

        if not optimizer.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Please train the model first using /ml/train endpoint."
            )

        # Fetch recent performance data
        collector = MetaDataCollector(request.access_token)
        recent_performance = await collector.fetch_campaign_history(
            campaign_id=request.campaign_id,
            days_back=14  # Get 14 days to ensure we have enough data
        )

        if len(recent_performance) < 7:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: need at least 7 days, got {len(recent_performance)}"
            )

        # Make prediction
        prediction = optimizer.predict_optimal_budget(
            recent_performance=recent_performance,
            prediction_date=request.prediction_date
        )

        return BudgetPredictionResponse(**prediction)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Prediction validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info() -> ModelInfoResponse:
    """
    Get information about the current ML model

    Returns:
    - Training status
    - Model version
    - Training metrics (MAE, R², etc.)
    - Feature count
    - Last training timestamp
    """
    try:
        optimizer = get_budget_optimizer()
        model_info = optimizer.get_model_info()
        return ModelInfoResponse(**model_info)

    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/save")
async def save_model() -> Dict[str, str]:
    """
    Manually save the current trained model to disk

    Returns path to saved model file.
    """
    try:
        optimizer = get_budget_optimizer()

        if not optimizer.is_trained:
            raise HTTPException(status_code=400, detail="No trained model to save")

        filepath = optimizer.save_model()

        return {
            "status": "success",
            "message": "Model saved successfully",
            "filepath": filepath
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")


@router.post("/model/load")
async def load_model(filepath: str) -> Dict[str, Any]:
    """
    Load a previously trained model from disk

    Args:
        filepath: Path to saved model file

    Returns model information after loading.
    """
    try:
        optimizer = get_budget_optimizer()
        optimizer.load_model(filepath)
        model_info = optimizer.get_model_info()

        return {
            "status": "success",
            "message": "Model loaded successfully",
            "model_info": model_info
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model file not found: {filepath}")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=f"Load failed: {str(e)}")


@router.get("/health")
async def ml_health_check() -> Dict[str, Any]:
    """Health check for ML optimization system"""
    try:
        optimizer = get_budget_optimizer()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "model_trained": optimizer.is_trained,
            "model_version": optimizer.model_version,
            "capabilities": [
                "budget_prediction",
                "model_training",
                "model_persistence",
                "feature_engineering"
            ]
        }
    except Exception as e:
        logger.error(f"ML health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Export router
__all__ = ['router']
