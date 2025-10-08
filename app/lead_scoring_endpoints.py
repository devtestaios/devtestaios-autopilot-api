"""
Lead Scoring API Endpoints
AI-powered lead qualification and routing system
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.ml.lead_scorer import LeadScorerML

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/lead-scorer", tags=["Lead Scoring"])

# Global lead scorer instance (lazy initialization)
_lead_scorer = None

def get_lead_scorer():
    """Get or create lead scorer instance"""
    global _lead_scorer
    if _lead_scorer is None:
        _lead_scorer = LeadScorerML()
    return _lead_scorer

# Request/Response Models
class LeadData(BaseModel):
    """Lead information from various platforms"""
    contact_info: Dict[str, Any] = Field(default_factory=dict, description="Name, email, phone, etc.")
    company_info: Dict[str, Any] = Field(default_factory=dict, description="Company size, industry, etc.")
    email_activity: Dict[str, Any] = Field(default_factory=dict, description="Email engagement metrics")
    website_activity: Dict[str, Any] = Field(default_factory=dict, description="Website behavior data")
    form_submission: Dict[str, Any] = Field(default_factory=dict, description="Form completion data")
    social_activity: Dict[str, Any] = Field(default_factory=dict, description="Social media presence")
    source_info: Dict[str, Any] = Field(default_factory=dict, description="Traffic source information")
    location: Dict[str, Any] = Field(default_factory=dict, description="Geographic data")
    timing: Dict[str, Any] = Field(default_factory=dict, description="Timing-related metrics")

class LeadScoringRequest(BaseModel):
    """Request for lead scoring"""
    lead_data: LeadData
    include_recommendations: bool = Field(default=True, description="Include follow-up recommendations")
    score_threshold: float = Field(default=0.5, description="Minimum confidence threshold")

class LeadScoringResponse(BaseModel):
    """Lead scoring prediction results"""
    lead_score: int = Field(description="Lead quality score (0-100)")
    quality_tier: str = Field(description="HOT, WARM, COOL, or COLD")
    confidence: float = Field(description="Model confidence (0-1)")
    recommendations: List[str] = Field(description="Recommended follow-up actions")
    prediction_date: str = Field(description="When prediction was made")
    model_version: str = Field(description="Version of model used")

class TrainingRequest(BaseModel):
    """Request for model training"""
    training_data: List[Dict[str, Any]] = Field(..., description="Historical lead data with outcomes")
    validation_split: float = Field(default=0.2, description="Fraction for validation")

class ModelInfoResponse(BaseModel):
    """Model information response"""
    is_trained: bool
    model_version: str
    training_date: Optional[str]
    performance_metrics: Dict[str, Any]
    feature_columns: List[str]
    model_type: str

# API Endpoints

@router.post("/score", response_model=LeadScoringResponse)
async def score_lead(request: LeadScoringRequest) -> LeadScoringResponse:
    """
    Score a lead using AI-powered analysis
    
    Returns lead quality score (0-100) and recommended follow-up actions.
    Works with rule-based fallback if ML model not trained yet.
    """
    try:
        scorer = get_lead_scorer()
        
        # Convert Pydantic model to dict for processing
        lead_data = request.lead_data.dict()
        
        # Get prediction
        prediction = scorer.predict_lead_score(lead_data)
        
        return LeadScoringResponse(**prediction)
        
    except Exception as e:
        logger.error(f"Lead scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Lead scoring failed: {str(e)}")

@router.post("/train")
async def train_lead_scorer(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Train the lead scoring ML model on historical data
    
    Requires historical lead data with conversion outcomes.
    Training happens in background, returns immediately.
    """
    try:
        scorer = get_lead_scorer()
        
        logger.info(f"Starting lead scorer training on {len(request.training_data)} samples")
        
        # Train the model
        training_results = scorer.train_model(request.training_data)
        
        # Save model in background
        if training_results.get("status") == "success":
            background_tasks.add_task(scorer.save_model)
        
        return {
            "status": "success",
            "message": f"Lead scoring model training started on {len(request.training_data)} samples",
            "training_results": training_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Lead scorer training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info() -> ModelInfoResponse:
    """
    Get information about the current lead scoring model
    
    Returns training status, performance metrics, and model details.
    """
    try:
        scorer = get_lead_scorer()
        model_info = scorer.get_model_info()
        return ModelInfoResponse(**model_info)
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@router.post("/model/save")
async def save_model() -> Dict[str, Any]:
    """
    Save the current trained model to disk
    
    Returns path to saved model file.
    """
    try:
        scorer = get_lead_scorer()
        
        if not scorer.is_trained:
            raise HTTPException(status_code=400, detail="No trained model to save")
        
        filepath = scorer.save_model()
        
        return {
            "status": "success",
            "message": "Lead scoring model saved successfully",
            "filepath": filepath,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save model: {str(e)}")

@router.post("/model/load")
async def load_model(filepath: str) -> Dict[str, Any]:
    """
    Load a trained model from disk
    
    Returns model information after loading.
    """
    try:
        scorer = get_lead_scorer()
        scorer.load_model(filepath)
        model_info = scorer.get_model_info()
        
        return {
            "status": "success",
            "message": "Lead scoring model loaded successfully",
            "model_info": model_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@router.get("/health")
async def lead_scorer_health() -> Dict[str, Any]:
    """Health check for lead scoring system"""
    try:
        scorer = get_lead_scorer()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "model_trained": scorer.is_trained,
            "model_version": scorer.model_version,
            "capabilities": [
                "lead_scoring",
                "quality_classification", 
                "follow_up_recommendations",
                "model_training",
                "performance_tracking"
            ]
        }
    except Exception as e:
        logger.error(f"Lead scorer health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Demo endpoint with sample data
@router.post("/demo")
async def demo_lead_scoring() -> Dict[str, Any]:
    """
    Demo endpoint with sample lead data
    
    Shows how the lead scoring system works with realistic data.
    """
    try:
        # Sample lead data
        sample_leads = [
            {
                "name": "High Quality Lead",
                "data": {
                    "contact_info": {"name": "John Smith", "email": "john@techcorp.com", "phone": "+1-555-0123"},
                    "company_info": {"employee_count": 500, "industry": "technology", "revenue": 50000000},
                    "email_activity": {"open_rate": 0.45, "click_rate": 0.12, "reply_rate": 0.03},
                    "website_activity": {"avg_session_duration": 180, "total_pages_viewed": 8},
                    "form_submission": {"fields_completed": 8, "total_fields": 10, "phone": True, "company": True},
                    "social_activity": {"linkedin_connections": 750, "engagement_rate": 0.08},
                    "source_info": {"source": "organic_search"},
                    "location": {"country": "united states", "state": "california"},
                    "timing": {"days_since_first_visit": 3}
                }
            },
            {
                "name": "Medium Quality Lead", 
                "data": {
                    "contact_info": {"name": "Jane Doe", "email": "jane@smallbiz.com"},
                    "company_info": {"employee_count": 25, "industry": "retail"},
                    "email_activity": {"open_rate": 0.25, "click_rate": 0.05},
                    "website_activity": {"avg_session_duration": 90, "total_pages_viewed": 3},
                    "form_submission": {"fields_completed": 5, "total_fields": 10},
                    "social_activity": {"linkedin_connections": 200},
                    "source_info": {"source": "facebook_ads"},
                    "location": {"country": "canada"},
                    "timing": {"days_since_first_visit": 7}
                }
            },
            {
                "name": "Low Quality Lead",
                "data": {
                    "contact_info": {"email": "test@example.com"},
                    "company_info": {"employee_count": 1},
                    "email_activity": {"open_rate": 0.10},
                    "website_activity": {"avg_session_duration": 30, "total_pages_viewed": 1},
                    "form_submission": {"fields_completed": 3, "total_fields": 10},
                    "source_info": {"source": "unknown"},
                    "timing": {"days_since_first_visit": 45}
                }
            }
        ]
        
        scorer = get_lead_scorer()
        results = []
        
        for lead in sample_leads:
            prediction = scorer.predict_lead_score(lead["data"])
            results.append({
                "lead_name": lead["name"],
                "prediction": prediction
            })
        
        return {
            "status": "success",
            "message": "Lead scoring demo completed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

# Export router
__all__ = ["router"]