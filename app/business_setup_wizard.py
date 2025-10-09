"""
Business Setup Wizard API Endpoints
Industry-standard onboarding with modular pricing and conversion optimization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timezone
import uuid

from app.modular_pricing_engine import (
    ModularPricingEngine, 
    CompanySize, 
    OnboardingProfile,
    PricingCalculation
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

# Initialize pricing engine
pricing_engine = ModularPricingEngine()

# Pydantic Models
class CompanyProfileRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=100)
    industry: str = Field(..., min_length=2, max_length=50)
    company_size: str = Field(..., description="startup, small, medium, or enterprise")
    employees_count: Optional[int] = Field(None, ge=1, le=10000)
    primary_challenges: List[str] = Field(default_factory=list, max_items=5)
    current_tools: List[str] = Field(default_factory=list, max_items=10)
    goals: List[str] = Field(default_factory=list, max_items=5)
    estimated_monthly_spend: Optional[float] = Field(None, ge=0, le=50000)

class SuiteSelectionRequest(BaseModel):
    selected_suites: List[str] = Field(..., min_items=0, max_items=4)
    company_size: str = Field(..., description="startup, small, medium, or enterprise")
    annual_billing: bool = Field(default=False)

class OnboardingStepTracking(BaseModel):
    step_name: str
    user_id: Optional[str] = None
    session_id: str
    time_spent_seconds: Optional[int] = None
    selections: Dict[str, Any] = Field(default_factory=dict)
    completion_rate: Optional[float] = None

class DemoRequest(BaseModel):
    company_profile: CompanyProfileRequest
    requested_suite: str
    demo_type: str = Field(default="interactive", description="interactive, video, or quick")

# In-memory storage for onboarding sessions (use Redis/database in production)
onboarding_sessions = {}
conversion_analytics = {}

@router.post("/company-profile")
async def create_company_profile(
    profile_request: CompanyProfileRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Step 2: Company Discovery - Collect company information and generate recommendations
    """
    try:
        # Validate company size
        try:
            company_size = CompanySize(profile_request.company_size.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid company size: {profile_request.company_size}"
            )
        
        # Create onboarding profile
        profile = OnboardingProfile(
            company_name=profile_request.company_name,
            industry=profile_request.industry,
            company_size=company_size,
            employees_count=profile_request.employees_count,
            primary_challenges=profile_request.primary_challenges,
            current_tools=profile_request.current_tools,
            goals=profile_request.goals,
            estimated_monthly_spend=profile_request.estimated_monthly_spend
        )
        
        # Generate smart recommendations
        recommended_suites = pricing_engine.get_smart_recommendations(profile)
        
        # Calculate pricing for recommendations
        pricing = pricing_engine.calculate_pricing(recommended_suites, company_size)
        
        # Generate ROI analysis
        roi_analysis = pricing_engine.get_roi_analysis(recommended_suites, company_size)
        
        # Create session ID for tracking
        session_id = str(uuid.uuid4())
        onboarding_sessions[session_id] = {
            "profile": profile,
            "recommended_suites": recommended_suites,
            "created_at": datetime.now(timezone.utc),
            "current_step": "company_profile_complete"
        }
        
        # Background task for analytics
        background_tasks.add_task(
            track_onboarding_step,
            "company_profile_complete",
            session_id,
            {"company_size": company_size.value, "industry": profile.industry}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "company_profile": {
                "company_name": profile.company_name,
                "industry": profile.industry,
                "company_size": company_size.value,
                "size_description": pricing_engine.size_multipliers[company_size].description
            },
            "recommended_suites": recommended_suites,
            "pricing_preview": {
                "monthly_price": float(pricing.final_monthly_price),
                "annual_price": float(pricing.final_annual_price),
                "total_savings": float(pricing.total_savings),
                "bundle_discount": float(pricing.bundle_discount_percent)
            },
            "roi_analysis": roi_analysis,
            "next_step": "suite_demo"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Company profile creation failed: {e}")
        raise HTTPException(status_code=500, detail="Profile creation failed")

@router.get("/suite-catalog")
async def get_suite_catalog() -> Dict[str, Any]:
    """
    Get complete suite catalog with features and pricing
    """
    try:
        catalog = pricing_engine.get_suite_catalog()
        
        return {
            "success": True,
            "suites": catalog,
            "base_platform": {
                "name": "PulseBridge.ai Platform",
                "description": "Core dashboard, integrations, and data management",
                "base_price": 29.0,
                "features": [
                    "Unified dashboard",
                    "Google Ads integration",
                    "Meta/Instagram integration", 
                    "LinkedIn integration",
                    "Real-time analytics",
                    "Standard support"
                ]
            },
            "bundle_discounts": {
                "2_suites": 10,
                "3_suites": 20,
                "4_suites": 30
            }
        }
        
    except Exception as e:
        logger.error(f"Suite catalog retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Catalog retrieval failed")

@router.post("/calculate-pricing")
async def calculate_modular_pricing(pricing_request: SuiteSelectionRequest) -> Dict[str, Any]:
    """
    Calculate real-time pricing based on suite selection
    """
    try:
        # Validate company size
        try:
            company_size = CompanySize(pricing_request.company_size.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid company size: {pricing_request.company_size}"
            )
        
        # Calculate pricing
        pricing = pricing_engine.calculate_pricing(
            pricing_request.selected_suites,
            company_size,
            pricing_request.annual_billing
        )
        
        # Get ROI analysis
        roi_analysis = pricing_engine.get_roi_analysis(
            pricing_request.selected_suites,
            company_size
        )
        
        # Get competitor comparison
        competitor_comparison = pricing_engine.get_competitor_comparison(
            pricing_request.selected_suites
        )
        
        return {
            "success": True,
            "pricing": {
                "base_platform_price": float(pricing.base_platform_price),
                "suite_costs": {k: float(v) for k, v in pricing.suite_costs.items()},
                "subtotal": float(pricing.subtotal),
                "bundle_discount_percent": float(pricing.bundle_discount_percent),
                "bundle_discount_amount": float(pricing.bundle_discount_amount),
                "company_size_multiplier": float(pricing.company_size_multiplier),
                "size_adjusted_total": float(pricing.size_adjusted_total),
                "annual_discount_percent": float(pricing.annual_discount_percent),
                "annual_discount_amount": float(pricing.annual_discount_amount),
                "final_monthly_price": float(pricing.final_monthly_price),
                "final_annual_price": float(pricing.final_annual_price),
                "total_savings": float(pricing.total_savings),
                "recommended_plan": pricing.recommended_plan
            },
            "roi_analysis": roi_analysis,
            "competitor_comparison": competitor_comparison,
            "billing_options": {
                "monthly": {
                    "price": float(pricing.final_monthly_price),
                    "total_annual": float(pricing.final_monthly_price * 12),
                    "savings": 0
                },
                "annual": {
                    "monthly_equivalent": float(pricing.final_monthly_price * 0.8333),  # 2 months free
                    "total_annual": float(pricing.final_annual_price),
                    "savings": float(pricing.final_monthly_price * 2)  # 2 months free
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pricing calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Pricing calculation failed")

@router.post("/demo-request")
async def request_suite_demo(
    demo_request: DemoRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Step 3: Personalized Demo Experience - Generate customized demo content
    """
    try:
        # Validate suite
        valid_suites = ["predictive_analytics", "financial_management", "conversational_ai", "hr_management"]
        if demo_request.requested_suite not in valid_suites:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid suite: {demo_request.requested_suite}"
            )
        
        # Generate personalized demo content
        demo_content = generate_personalized_demo(
            demo_request.company_profile,
            demo_request.requested_suite,
            demo_request.demo_type
        )
        
        # Track demo request
        background_tasks.add_task(
            track_onboarding_step,
            "demo_requested",
            f"demo_{uuid.uuid4().hex[:8]}",
            {
                "suite": demo_request.requested_suite,
                "demo_type": demo_request.demo_type,
                "company_size": demo_request.company_profile.company_size
            }
        )
        
        return {
            "success": True,
            "demo_content": demo_content,
            "next_steps": [
                "Try interactive features",
                "See ROI calculator", 
                "View implementation timeline",
                "Start free trial"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo request failed: {e}")
        raise HTTPException(status_code=500, detail="Demo generation failed")

@router.post("/track-onboarding")
async def track_onboarding_step(
    tracking: OnboardingStepTracking,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Track onboarding funnel metrics for optimization
    """
    try:
        # Store tracking data
        if tracking.session_id not in conversion_analytics:
            conversion_analytics[tracking.session_id] = {
                "steps": [],
                "started_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc)
            }
        
        conversion_analytics[tracking.session_id]["steps"].append({
            "step_name": tracking.step_name,
            "timestamp": datetime.now(timezone.utc),
            "time_spent": tracking.time_spent_seconds,
            "selections": tracking.selections,
            "completion_rate": tracking.completion_rate
        })
        
        conversion_analytics[tracking.session_id]["last_activity"] = datetime.now(timezone.utc)
        
        # Background task for real-time analytics processing
        background_tasks.add_task(
            process_conversion_analytics,
            tracking.session_id,
            tracking.step_name
        )
        
        return {
            "success": True,
            "message": "Tracking recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Onboarding tracking failed: {e}")
        raise HTTPException(status_code=500, detail="Tracking failed")

@router.get("/conversion-analytics")
async def get_conversion_analytics() -> Dict[str, Any]:
    """
    Get onboarding funnel analytics for optimization
    """
    try:
        # Calculate funnel metrics
        total_sessions = len(conversion_analytics)
        if total_sessions == 0:
            return {
                "success": True,
                "metrics": {
                    "total_sessions": 0,
                    "conversion_funnel": {},
                    "average_time_per_step": {},
                    "drop_off_points": []
                }
            }
        
        # Analyze step completion rates
        step_counts = {}
        step_times = {}
        
        for session_data in conversion_analytics.values():
            for step in session_data["steps"]:
                step_name = step["step_name"]
                step_counts[step_name] = step_counts.get(step_name, 0) + 1
                
                if step["time_spent"]:
                    if step_name not in step_times:
                        step_times[step_name] = []
                    step_times[step_name].append(step["time_spent"])
        
        # Calculate conversion rates
        funnel_steps = [
            "company_profile_complete",
            "demo_requested", 
            "pricing_calculated",
            "trial_started",
            "subscription_created"
        ]
        
        conversion_funnel = {}
        for i, step in enumerate(funnel_steps):
            completion_count = step_counts.get(step, 0)
            completion_rate = (completion_count / total_sessions * 100) if total_sessions > 0 else 0
            conversion_funnel[step] = {
                "completions": completion_count,
                "rate": round(completion_rate, 2)
            }
        
        # Calculate average time per step
        average_times = {}
        for step, times in step_times.items():
            average_times[step] = round(sum(times) / len(times), 1) if times else 0
        
        return {
            "success": True,
            "metrics": {
                "total_sessions": total_sessions,
                "conversion_funnel": conversion_funnel,
                "average_time_per_step": average_times,
                "overall_conversion_rate": conversion_funnel.get("subscription_created", {}).get("rate", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Analytics retrieval failed")

# Helper Functions
def generate_personalized_demo(
    profile: CompanyProfileRequest,
    suite: str, 
    demo_type: str
) -> Dict[str, Any]:
    """Generate personalized demo content based on company profile"""
    
    # Suite-specific demo templates
    demo_templates = {
        "predictive_analytics": {
            "title": f"See How {profile.company_name} Can Increase ROI by 40%",
            "description": "AI-powered predictions for your marketing campaigns",
            "features_demo": [
                f"Campaign performance forecasting for {profile.industry} companies",
                f"Revenue predictions based on your current ${profile.estimated_monthly_spend or 5000}/month spend",
                "Budget optimization recommendations",
                "Market trend analysis for your industry"
            ],
            "interactive_elements": [
                "Try the ROI calculator with your data",
                "See live prediction models",
                "Explore budget optimization scenarios"
            ]
        },
        "financial_management": {
            "title": f"Streamline {profile.company_name}'s Financial Operations",
            "description": "Complete budget and billing automation",
            "features_demo": [
                f"Budget tracking for {profile.company_size} companies",
                "Professional invoice generation",
                "Automated recurring billing",
                "Financial reporting and analytics"
            ],
            "interactive_elements": [
                "Generate a sample invoice",
                "Try the budget calculator",
                "Explore expense tracking"
            ]
        },
        "conversational_ai": {
            "title": f"Handle 90% of {profile.company_name}'s Customer Inquiries Automatically",
            "description": "Multi-language AI with voice integration",
            "features_demo": [
                "24/7 automated customer support",
                "Multi-language conversation handling",
                "Real-time sentiment analysis",
                "Voice-to-text integration"
            ],
            "interactive_elements": [
                "Chat with our AI assistant",
                "Try voice commands",
                "See sentiment analysis in action"
            ]
        },
        "hr_management": {
            "title": f"Streamline {profile.company_name}'s HR Processes by 70%",
            "description": "Complete employee lifecycle management",
            "features_demo": [
                f"Employee management for {profile.employees_count or 25} employees",
                "Performance review automation",
                "Leave request workflows",
                "Recruitment pipeline management"
            ],
            "interactive_elements": [
                "Create a sample employee record",
                "Try the performance review system",
                "Explore recruitment tracking"
            ]
        }
    }
    
    return demo_templates.get(suite, {
        "title": f"Discover How {profile.company_name} Can Benefit",
        "description": "Comprehensive business automation",
        "features_demo": ["Feature demonstration"],
        "interactive_elements": ["Try our platform"]
    })

async def track_onboarding_step(step_name: str, session_id: str, data: Dict[str, Any]):
    """Background task for tracking onboarding steps"""
    try:
        # In production, save to database/analytics service
        logger.info(f"Onboarding step tracked: {step_name} for session {session_id}")
        
        # Here you would typically:
        # - Send to analytics service (Mixpanel, Amplitude, etc.)
        # - Update user progress in database
        # - Trigger automated follow-up campaigns
        # - Update A/B testing metrics
        
    except Exception as e:
        logger.error(f"Tracking background task failed: {e}")

async def process_conversion_analytics(session_id: str, step_name: str):
    """Background task for processing conversion analytics"""
    try:
        # In production, this would:
        # - Update real-time dashboard metrics
        # - Trigger alerts for conversion drops
        # - Update A/B testing results
        # - Send data to BI systems
        
        logger.info(f"Processing analytics for step {step_name} in session {session_id}")
        
    except Exception as e:
        logger.error(f"Analytics processing failed: {e}")