"""
Business Setup Wizard API Endpoints
Industry-standard onboarding with modular pricing and conversion optimization
Includes billing bypass for internal users and test accounts
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

# Import billing bypass system
from app.billing_bypass_system import (
    BillingBypassManager,
    check_billing_bypass_before_payment,
    get_user_billing_status
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

# Initialize pricing engine
pricing_engine = ModularPricingEngine()

# Pydantic Models
class CompanyProfileRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-zA-Z0-9\s\-\.&',]+$",  # Alphanumeric + common business chars
        description="Company name (alphanumeric, spaces, and common punctuation only)"
    )
    industry: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z\s\-_]+$",  # Letters, spaces, hyphens, underscores
        description="Industry (letters only)"
    )
    company_size: str = Field(..., description="startup, small, medium, or enterprise")
    employees_count: Optional[int] = Field(None, ge=1, le=10000)
    primary_challenges: List[str] = Field(default_factory=list, max_items=5)
    current_tools: List[str] = Field(default_factory=list, max_items=10)
    goals: List[str] = Field(default_factory=list, max_items=5)
    estimated_monthly_spend: Optional[float] = Field(None, ge=0, le=50000)
    user_email: Optional[str] = Field(None, description="User email for demo mode detection")

class SuiteSelectionRequest(BaseModel):
    selected_suites: List[str] = Field(..., min_items=0, max_items=4)
    company_size: str = Field(..., description="startup, small, medium, or enterprise")
    annual_billing: bool = Field(default=False)
    user_email: Optional[str] = Field(None, description="User email for billing bypass check")

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
    Enhanced with demo mode for authorized users
    """
    try:
        # Check for demo mode (billing bypass users)
        demo_mode_info = None
        is_demo_user = False
        
        if profile_request.user_email:
            bypass_check = check_billing_bypass_before_payment(
                profile_request.user_email, 
                ["ml_suite", "financial_suite", "ai_suite", "hr_suite"]
            )
            
            if bypass_check["bypass_billing"]:
                is_demo_user = True
                demo_mode_info = {
                    "demo_mode": True,
                    "demo_user_type": bypass_check["reason"],
                    "full_access": True,
                    "message": "Welcome! You have full access to explore all PulseBridge features.",
                    "special_features": [
                        "Complete suite access",
                        "Advanced analytics preview",
                        "Priority feature demos",
                        "White-glove onboarding experience"
                    ]
                }
                
                logger.info(f"Demo mode activated for {profile_request.user_email}: {bypass_check['reason']}")
        
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
        
        # Generate smart recommendations (enhanced for demo users)
        if is_demo_user:
            # Demo users get all suites recommended for full experience
            recommended_suites = ["ml_suite", "financial_suite", "ai_suite", "hr_suite"]
        else:
            recommended_suites = pricing_engine.get_smart_recommendations(profile)
        
        # Calculate pricing for recommendations
        pricing = pricing_engine.calculate_pricing(recommended_suites, company_size)
        
        # Generate ROI analysis (enhanced for demo users)
        roi_analysis = pricing_engine.get_roi_analysis(recommended_suites, company_size)
        
        # Add demo-specific ROI insights
        if is_demo_user:
            roi_analysis["demo_insights"] = {
                "potential_savings": "Up to $50,000+ annually in operational efficiency",
                "time_savings": "15-25 hours per week in automated workflows",
                "revenue_impact": "25-40% improvement in lead conversion rates",
                "demo_scenarios": [
                    "ML Suite: Predictive analytics for customer churn prevention",
                    "Financial Suite: Automated invoice processing and cash flow forecasting", 
                    "AI Suite: Intelligent lead scoring and personalized campaigns",
                    "HR Suite: Automated recruitment and performance analytics"
                ]
            }
        
        # Create session ID for tracking
        session_id = str(uuid.uuid4())
        onboarding_sessions[session_id] = {
            "profile": profile,
            "recommended_suites": recommended_suites,
            "created_at": datetime.now(timezone.utc),
            "current_step": "company_profile_complete",
            "demo_mode": is_demo_user,
            "user_email": profile_request.user_email
        }
        
        # Background task for analytics
        background_tasks.add_task(
            track_onboarding_step,
            "company_profile_complete",
            session_id,
            {"company_size": company_size.value, "industry": profile.industry, "demo_mode": is_demo_user}
        )
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "demo_mode_info": demo_mode_info,
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
        
        # Add demo-specific next steps and guidance
        if is_demo_user:
            response_data["demo_guidance"] = {
                "welcome_message": f"Welcome to your personalized PulseBridge demo experience!",
                "next_actions": [
                    "Explore all 4 business suites with full access",
                    "Experience AI-powered automation workflows",
                    "Test real-time analytics and reporting",
                    "Configure your personalized dashboard"
                ],
                "demo_duration": "Unlimited access during evaluation period",
                "support_contact": "Your dedicated success manager will reach out within 24 hours"
            }
        
        return response_data
        
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
                "base_price": 69.0,  # Updated to match new Starter tier
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
    Calculate real-time pricing based on suite selection with billing bypass support
    """
    try:
        # Check for billing bypass first
        billing_bypass_info = None
        if pricing_request.user_email:
            bypass_check = check_billing_bypass_before_payment(
                pricing_request.user_email, 
                pricing_request.selected_suites
            )
            
            if bypass_check["bypass_billing"]:
                billing_bypass_info = {
                    "bypass_active": True,
                    "reason": bypass_check["reason"],
                    "allowed_suites": bypass_check["allowed_suites"],
                    "message": f"Billing bypassed: {bypass_check['reason']}"
                }
                
                logger.info(f"Billing bypass active for {pricing_request.user_email}: {bypass_check['reason']}")
        
        # Validate company size
        try:
            company_size = CompanySize(pricing_request.company_size.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid company size: {pricing_request.company_size}"
            )
        
        # Calculate pricing (even for bypass users to show value)
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
        
        response_data = {
            "success": True,
            "billing_bypass": billing_bypass_info,
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
        
        return response_data
        
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

@router.post("/interactive-demo-experience")
async def create_interactive_demo_experience(
    session_id: str,
    selected_suites: List[str],
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhanced demo experience for authorized users with full feature access
    """
    try:
        # Check if user is authorized for enhanced demo
        is_authorized_user = False
        demo_privileges = {}
        
        if user_email:
            bypass_check = check_billing_bypass_before_payment(user_email, selected_suites)
            
            if bypass_check["bypass_billing"]:
                is_authorized_user = True
                demo_privileges = {
                    "full_feature_access": True,
                    "live_data_access": True,
                    "advanced_analytics": True,
                    "white_glove_support": True,
                    "custom_configurations": True,
                    "priority_demos": True
                }
        
        # Get session data
        session_data = onboarding_sessions.get(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate enhanced demo experience
        demo_experience = {
            "session_id": session_id,
            "demo_type": "interactive_full_access" if is_authorized_user else "standard_demo",
            "authorized_user": is_authorized_user,
            "demo_privileges": demo_privileges,
            "available_suites": selected_suites,
            "interactive_modules": []
        }
        
        # Generate interactive modules for each selected suite
        for suite in selected_suites:
            if suite == "ml_suite":
                module = {
                    "suite_name": "ML & Predictive Analytics",
                    "interactive_features": [
                        {
                            "name": "Customer Churn Prediction",
                            "description": "AI-powered analysis of customer behavior patterns",
                            "demo_data": "Live customer dataset with 94% accuracy prediction" if is_authorized_user else "Sample dataset preview",
                            "interaction_type": "live_dashboard" if is_authorized_user else "video_walkthrough"
                        },
                        {
                            "name": "Revenue Forecasting",
                            "description": "Machine learning models for sales projection",
                            "demo_data": "Real-time revenue models" if is_authorized_user else "Static forecast examples",
                            "interaction_type": "configurable_model" if is_authorized_user else "demo_screenshots"
                        },
                        {
                            "name": "Automated Lead Scoring",
                            "description": "AI-driven qualification of prospects",
                            "demo_data": "Live lead pipeline analysis" if is_authorized_user else "Example lead scores",
                            "interaction_type": "interactive_scoring" if is_authorized_user else "example_walkthrough"
                        }
                    ]
                }
            
            elif suite == "financial_suite":
                module = {
                    "suite_name": "Financial Management Suite",
                    "interactive_features": [
                        {
                            "name": "Automated Invoice Processing",
                            "description": "AI-powered invoice recognition and processing",
                            "demo_data": "Upload and process real invoices" if is_authorized_user else "Sample invoice processing",
                            "interaction_type": "file_upload_demo" if is_authorized_user else "video_demo"
                        },
                        {
                            "name": "Cash Flow Forecasting",
                            "description": "Predictive cash flow analysis and planning",
                            "demo_data": "Real financial data integration" if is_authorized_user else "Example cash flow charts",
                            "interaction_type": "live_financial_dashboard" if is_authorized_user else "static_examples"
                        },
                        {
                            "name": "Expense Automation",
                            "description": "Smart categorization and approval workflows",
                            "demo_data": "Connect to real expense sources" if is_authorized_user else "Demo expense categories",
                            "interaction_type": "workflow_builder" if is_authorized_user else "feature_overview"
                        }
                    ]
                }
            
            elif suite == "ai_suite":
                module = {
                    "suite_name": "Conversational AI Suite",
                    "interactive_features": [
                        {
                            "name": "Intelligent Chatbot Builder",
                            "description": "Create and deploy AI-powered customer service bots",
                            "demo_data": "Build and test live chatbot" if is_authorized_user else "Pre-built chatbot examples",
                            "interaction_type": "chatbot_builder" if is_authorized_user else "demo_conversation"
                        },
                        {
                            "name": "Email Campaign AI",
                            "description": "AI-generated personalized email campaigns",
                            "demo_data": "Generate real campaign content" if is_authorized_user else "Sample email templates",
                            "interaction_type": "content_generator" if is_authorized_user else "template_gallery"
                        },
                        {
                            "name": "Voice Integration",
                            "description": "Voice-to-text and intelligent call analysis",
                            "demo_data": "Record and analyze real calls" if is_authorized_user else "Sample call analytics",
                            "interaction_type": "voice_recorder" if is_authorized_user else "audio_examples"
                        }
                    ]
                }
            
            elif suite == "hr_suite":
                module = {
                    "suite_name": "HR Management Suite", 
                    "interactive_features": [
                        {
                            "name": "Automated Recruitment",
                            "description": "AI-powered candidate screening and matching",
                            "demo_data": "Upload real job descriptions and resumes" if is_authorized_user else "Sample candidate matching",
                            "interaction_type": "recruitment_pipeline" if is_authorized_user else "matching_examples"
                        },
                        {
                            "name": "Performance Analytics",
                            "description": "Employee performance tracking and insights",
                            "demo_data": "Live performance dashboard" if is_authorized_user else "Anonymous performance metrics",
                            "interaction_type": "analytics_dashboard" if is_authorized_user else "chart_examples"
                        },
                        {
                            "name": "Onboarding Automation",
                            "description": "Streamlined new hire processes",
                            "demo_data": "Create real onboarding workflows" if is_authorized_user else "Sample onboarding steps",
                            "interaction_type": "workflow_designer" if is_authorized_user else "process_overview"
                        }
                    ]
                }
            
            demo_experience["interactive_modules"].append(module)
        
        # Add demo completion pathway
        demo_experience["completion_pathway"] = {
            "current_step": 1,
            "total_steps": 5,
            "steps": [
                "Explore Interactive Features",
                "Customize Your Dashboard", 
                "Test Real Data Integration",
                "Configure Automation Rules",
                "Complete Setup & Go Live" if is_authorized_user else "Schedule Implementation Call"
            ]
        }
        
        # Enhanced support for authorized users
        if is_authorized_user:
            demo_experience["premium_support"] = {
                "dedicated_success_manager": True,
                "technical_implementation_support": True,
                "custom_integration_consultation": True,
                "priority_feature_requests": True,
                "direct_development_team_access": True
            }
        
        return {
            "success": True,
            "demo_experience": demo_experience,
            "message": "Enhanced demo experience activated!" if is_authorized_user else "Standard demo experience ready"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interactive demo creation failed: {e}")
        raise HTTPException(status_code=500, detail="Demo experience creation failed")

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

@router.post("/complete-demo-experience")
async def complete_demo_experience(
    session_id: str,
    user_email: str,
    selected_configuration: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Complete the demo experience and transition authorized users to full platform access
    """
    try:
        # Verify session exists
        session_data = onboarding_sessions.get(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check authorization
        bypass_check = check_billing_bypass_before_payment(user_email, ["ml_suite", "financial_suite", "ai_suite", "hr_suite"])
        
        if not bypass_check["bypass_billing"]:
            raise HTTPException(status_code=403, detail="Demo completion requires authorized access")
        
        # Create platform configuration
        platform_configuration = {
            "user_email": user_email,
            "company_profile": session_data["profile"].__dict__,
            "selected_suites": selected_configuration.get("selected_suites", []),
            "custom_settings": selected_configuration.get("custom_settings", {}),
            "integration_preferences": selected_configuration.get("integrations", {}),
            "demo_completion_date": datetime.now(timezone.utc).isoformat(),
            "access_level": "full_platform_access",
            "billing_status": "bypass_active",
            "support_tier": "premium"
        }
        
        # Generate onboarding completion summary
        completion_summary = {
            "demo_experience_completed": True,
            "total_time_spent": (datetime.now(timezone.utc) - session_data["created_at"]).total_seconds() / 60,  # minutes
            "features_explored": len(selected_configuration.get("selected_suites", [])),
            "configuration_saved": True,
            "platform_ready": True
        }
        
        # Create success pathway
        success_pathway = {
            "immediate_access": {
                "dashboard_url": "https://app.pulsebridge.ai/dashboard",
                "login_method": "email_verification",
                "first_login_bonus": "Advanced analytics pack unlocked"
            },
            "onboarding_support": {
                "success_manager_contact": "success@pulsebridge.ai",
                "implementation_guide": "https://docs.pulsebridge.ai/implementation",
                "video_tutorials": "https://learn.pulsebridge.ai/tutorials",
                "community_access": "https://community.pulsebridge.ai"
            },
            "next_milestones": [
                {
                    "milestone": "Connect Your First Data Source",
                    "estimated_time": "5 minutes",
                    "reward": "Custom dashboard themes unlocked"
                },
                {
                    "milestone": "Configure Your First Automation",
                    "estimated_time": "15 minutes", 
                    "reward": "Advanced workflow templates unlocked"
                },
                {
                    "milestone": "Generate Your First Report",
                    "estimated_time": "10 minutes",
                    "reward": "Premium reporting features unlocked"
                }
            ]
        }
        
        # Track completion
        background_tasks.add_task(
            track_onboarding_step,
            "demo_experience_completed",
            session_id,
            {
                "user_email": user_email,
                "completion_type": "full_demo_experience",
                "selected_suites": selected_configuration.get("selected_suites", []),
                "bypass_reason": bypass_check["reason"]
            }
        )
        
        # Send welcome email
        background_tasks.add_task(
            send_demo_completion_email,
            user_email,
            platform_configuration,
            completion_summary
        )
        
        return {
            "success": True,
            "message": "Congratulations! Your PulseBridge demo experience is complete.",
            "platform_configuration": platform_configuration,
            "completion_summary": completion_summary,
            "success_pathway": success_pathway,
            "authorization_status": {
                "billing_bypass_active": True,
                "access_level": "unlimited",
                "expires_at": None,  # Unlimited for internal users
                "support_tier": "premium"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo completion failed: {e}")
        raise HTTPException(status_code=500, detail="Demo completion failed")

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

async def send_demo_completion_email(user_email: str, platform_config: Dict[str, Any], completion_summary: Dict[str, Any]):
    """Background task for sending demo completion email"""
    try:
        # In production, this would:
        # - Send personalized welcome email
        # - Include custom dashboard setup guide
        # - Provide next steps and milestones
        # - Include contact information for success manager
        
        logger.info(f"Demo completion email sent to {user_email}")
        
        # Email content would include:
        # - Welcome message with company name
        # - Summary of configured features
        # - Links to platform access
        # - Success manager contact info
        # - Implementation timeline
        # - Resource links and tutorials
        
    except Exception as e:
        logger.error(f"Demo completion email failed: {e}")