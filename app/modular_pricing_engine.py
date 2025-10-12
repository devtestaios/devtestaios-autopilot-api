"""
Modular Suite Pricing Engine for PulseBridge.ai
Enables flexible suite selection with intelligent bundling and company-size pricing
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CompanySize(Enum):
    STARTUP = "startup"           # 1-10 employees
    SMALL_BUSINESS = "small"      # 11-50 employees  
    MEDIUM_BUSINESS = "medium"    # 51-200 employees
    ENTERPRISE = "enterprise"     # 201+ employees

class Suite(Enum):
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    FINANCIAL_MANAGEMENT = "financial_management"
    CONVERSATIONAL_AI = "conversational_ai"
    HR_MANAGEMENT = "hr_management"

@dataclass
class SuiteInfo:
    name: str
    description: str
    base_price: Decimal
    features: List[str]
    endpoints: int
    value_proposition: str
    typical_savings: str

@dataclass
class CompanySizeMultiplier:
    size: CompanySize
    multiplier: Decimal
    description: str
    max_users: Optional[int]

@dataclass
class PricingCalculation:
    base_platform_price: Decimal
    selected_suites: List[str]
    suite_costs: Dict[str, Decimal]
    subtotal: Decimal
    bundle_discount_percent: Decimal
    bundle_discount_amount: Decimal
    company_size_multiplier: Decimal
    size_adjusted_total: Decimal
    annual_discount_percent: Decimal
    annual_discount_amount: Decimal
    final_monthly_price: Decimal
    final_annual_price: Decimal
    total_savings: Decimal
    recommended_plan: str

@dataclass
class OnboardingProfile:
    company_name: str
    industry: str
    company_size: CompanySize
    employees_count: Optional[int]
    primary_challenges: List[str]
    current_tools: List[str]
    goals: List[str]
    estimated_monthly_spend: Optional[Decimal]

class ModularPricingEngine:
    """
    Advanced pricing engine for PulseBridge.ai's modular suite architecture
    """
    
    def __init__(self):
        self.base_platform_price = Decimal("69.00")  # Updated base price to match Starter tier
        
        # Suite pricing (base startup pricing) - adjusted to work with new structure
        self.suite_catalog = {
            Suite.PREDICTIVE_ANALYTICS: SuiteInfo(
                name="Predictive Analytics Suite",
                description="AI-powered forecasting, campaign optimization, and market trend analysis",
                base_price=Decimal("100.00"),  # Reduced from 149
                features=[
                    "ML Campaign Performance Forecasting",
                    "Revenue Prediction Models", 
                    "Budget Optimization Algorithms",
                    "Anomaly Detection & Alerts",
                    "Market Trend Analysis",
                    "Customer Lifetime Value Prediction"
                ],
                endpoints=6,
                value_proposition="Increase ROI by 40% with AI predictions",
                typical_savings="$2,000-5,000/month in optimized ad spend"
            ),
            Suite.FINANCIAL_MANAGEMENT: SuiteInfo(
                name="Financial Management Suite", 
                description="Complete budget management, invoicing, and billing automation",
                base_price=Decimal("75.00"),  # Reduced from 99
                features=[
                    "Advanced Budget Allocation & Tracking",
                    "Professional Invoice Generation",
                    "Automated Billing & Recurring Payments",
                    "ROI Analysis & Financial Reporting",
                    "Multi-currency Support",
                    "Tax Calculation & Compliance"
                ],
                endpoints=12,
                value_proposition="Reduce financial admin by 80%",
                typical_savings="$1,500-3,000/month in accounting costs"
            ),
            Suite.CONVERSATIONAL_AI: SuiteInfo(
                name="Conversational AI Suite",
                description="Multi-language AI communication with voice integration",
                base_price=Decimal("60.00"),  # Reduced from 79
                features=[
                    "Multi-language Conversational AI",
                    "Real-time Sentiment Analysis",
                    "Voice-to-Text & Text-to-Voice",
                    "Intent Classification & Routing",
                    "Conversation Analytics",
                    "24/7 Automated Customer Support"
                ],
                endpoints=13,
                value_proposition="Handle 90% of customer inquiries automatically",
                typical_savings="$3,000-8,000/month in support costs"
            ),
            Suite.HR_MANAGEMENT: SuiteInfo(
                name="HR Management Suite",
                description="Complete employee lifecycle management and performance tracking",
                base_price=Decimal("40.00"),  # Reduced from 69
                features=[
                    "Employee Lifecycle Management",
                    "Performance Review System",
                    "Leave Request Automation",
                    "Recruitment Pipeline Management",
                    "Training Program Tracking",
                    "HR Analytics & Insights"
                ],
                endpoints=10,
                value_proposition="Streamline HR processes by 70%",
                typical_savings="$2,000-4,000/month in HR software & admin"
            )
        }
        
        # Company size multipliers
        self.size_multipliers = {
            CompanySize.STARTUP: CompanySizeMultiplier(
                size=CompanySize.STARTUP,
                multiplier=Decimal("1.0"),
                description="1-10 employees",
                max_users=10
            ),
            CompanySize.SMALL_BUSINESS: CompanySizeMultiplier(
                size=CompanySize.SMALL_BUSINESS,
                multiplier=Decimal("1.5"),
                description="11-50 employees",
                max_users=50
            ),
            CompanySize.MEDIUM_BUSINESS: CompanySizeMultiplier(
                size=CompanySize.MEDIUM_BUSINESS,
                multiplier=Decimal("2.0"),
                description="51-200 employees", 
                max_users=200
            ),
            CompanySize.ENTERPRISE: CompanySizeMultiplier(
                size=CompanySize.ENTERPRISE,
                multiplier=Decimal("3.0"),
                description="201+ employees",
                max_users=None
            )
        }
    
    def calculate_pricing(
        self,
        selected_suites: List[str],
        company_size: CompanySize = CompanySize.STARTUP,
        annual_billing: bool = False
    ) -> PricingCalculation:
        """Calculate modular pricing with intelligent bundling"""
        
        try:
            # Base platform cost
            base_cost = self.base_platform_price
            
            # Calculate suite costs
            suite_costs = {}
            suite_total = Decimal("0.00")
            
            for suite_key in selected_suites:
                try:
                    suite = Suite(suite_key)
                    suite_info = self.suite_catalog[suite]
                    suite_costs[suite_key] = suite_info.base_price
                    suite_total += suite_info.base_price
                except (ValueError, KeyError):
                    logger.warning(f"Unknown suite: {suite_key}")
                    continue
            
            subtotal = base_cost + suite_total
            
            # Bundle discount calculation
            num_suites = len(selected_suites)
            if num_suites >= 4:
                bundle_discount_percent = Decimal("30.0")  # All 4 suites
            elif num_suites == 3:
                bundle_discount_percent = Decimal("20.0")  # 3 suites
            elif num_suites == 2:
                bundle_discount_percent = Decimal("10.0")  # 2 suites
            else:
                bundle_discount_percent = Decimal("0.0")   # Single suite or platform only
            
            bundle_discount_amount = (suite_total * bundle_discount_percent / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            
            after_bundle_discount = subtotal - bundle_discount_amount
            
            # Company size multiplier
            size_multiplier = self.size_multipliers[company_size].multiplier
            size_adjusted_total = (after_bundle_discount * size_multiplier).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            
            # Annual discount (2 months free = 16.67% discount)
            annual_discount_percent = Decimal("16.67") if annual_billing else Decimal("0.0")
            annual_discount_amount = (size_adjusted_total * annual_discount_percent / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ) if annual_billing else Decimal("0.0")
            
            final_monthly_price = size_adjusted_total - annual_discount_amount
            final_annual_price = final_monthly_price * 12 if not annual_billing else size_adjusted_total * 10  # 10 months when annual
            
            # Calculate total savings
            total_savings = bundle_discount_amount + annual_discount_amount
            
            # Generate recommended plan name
            recommended_plan = self._generate_plan_name(selected_suites, company_size)
            
            return PricingCalculation(
                base_platform_price=base_cost,
                selected_suites=selected_suites,
                suite_costs=suite_costs,
                subtotal=subtotal,
                bundle_discount_percent=bundle_discount_percent,
                bundle_discount_amount=bundle_discount_amount,
                company_size_multiplier=size_multiplier,
                size_adjusted_total=size_adjusted_total,
                annual_discount_percent=annual_discount_percent,
                annual_discount_amount=annual_discount_amount,
                final_monthly_price=final_monthly_price,
                final_annual_price=final_annual_price,
                total_savings=total_savings,
                recommended_plan=recommended_plan
            )
            
        except Exception as e:
            logger.error(f"Pricing calculation failed: {e}")
            # Return fallback pricing
            return PricingCalculation(
                base_platform_price=Decimal("29.00"),
                selected_suites=[],
                suite_costs={},
                subtotal=Decimal("29.00"),
                bundle_discount_percent=Decimal("0.0"),
                bundle_discount_amount=Decimal("0.0"),
                company_size_multiplier=Decimal("1.0"),
                size_adjusted_total=Decimal("29.00"),
                annual_discount_percent=Decimal("0.0"),
                annual_discount_amount=Decimal("0.0"),
                final_monthly_price=Decimal("29.00"),
                final_annual_price=Decimal("348.00"),
                total_savings=Decimal("0.0"),
                recommended_plan="Platform Basic"
            )
    
    def get_smart_recommendations(self, profile: OnboardingProfile) -> List[str]:
        """Generate smart suite recommendations based on company profile"""
        
        recommendations = []
        
        # Always recommend based on company challenges
        challenge_mapping = {
            "marketing_optimization": [Suite.PREDICTIVE_ANALYTICS.value],
            "financial_management": [Suite.FINANCIAL_MANAGEMENT.value],
            "customer_support": [Suite.CONVERSATIONAL_AI.value],
            "employee_management": [Suite.HR_MANAGEMENT.value],
            "data_analysis": [Suite.PREDICTIVE_ANALYTICS.value],
            "automation": [Suite.CONVERSATIONAL_AI.value, Suite.HR_MANAGEMENT.value]
        }
        
        for challenge in profile.primary_challenges:
            if challenge in challenge_mapping:
                recommendations.extend(challenge_mapping[challenge])
        
        # Industry-based recommendations
        industry_recommendations = {
            "marketing_agency": [Suite.PREDICTIVE_ANALYTICS.value, Suite.FINANCIAL_MANAGEMENT.value],
            "ecommerce": [Suite.PREDICTIVE_ANALYTICS.value, Suite.CONVERSATIONAL_AI.value],
            "consulting": [Suite.FINANCIAL_MANAGEMENT.value, Suite.HR_MANAGEMENT.value],
            "saas": [Suite.PREDICTIVE_ANALYTICS.value, Suite.CONVERSATIONAL_AI.value],
            "healthcare": [Suite.HR_MANAGEMENT.value, Suite.CONVERSATIONAL_AI.value],
            "education": [Suite.HR_MANAGEMENT.value, Suite.CONVERSATIONAL_AI.value]
        }
        
        if profile.industry.lower() in industry_recommendations:
            recommendations.extend(industry_recommendations[profile.industry.lower()])
        
        # Company size recommendations
        if profile.company_size in [CompanySize.MEDIUM_BUSINESS, CompanySize.ENTERPRISE]:
            # Larger companies typically need HR and Financial management
            recommendations.extend([Suite.HR_MANAGEMENT.value, Suite.FINANCIAL_MANAGEMENT.value])
        
        # Remove duplicates while preserving order
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        # Ensure at least one recommendation
        if not unique_recommendations:
            unique_recommendations = [Suite.PREDICTIVE_ANALYTICS.value]
        
        return unique_recommendations[:3]  # Limit to top 3 recommendations
    
    def get_roi_analysis(self, selected_suites: List[str], company_size: CompanySize) -> Dict[str, Any]:
        """Calculate ROI analysis for selected suites"""
        
        pricing = self.calculate_pricing(selected_suites, company_size)
        monthly_cost = float(pricing.final_monthly_price)
        
        # Calculate potential savings based on suite selection
        total_monthly_savings = 0
        savings_breakdown = {}
        
        for suite_key in selected_suites:
            try:
                suite = Suite(suite_key)
                suite_info = self.suite_catalog[suite]
                
                # Extract savings estimates (simplified)
                if "2,000-5,000" in suite_info.typical_savings:
                    avg_savings = 3500
                elif "1,500-3,000" in suite_info.typical_savings:
                    avg_savings = 2250
                elif "3,000-8,000" in suite_info.typical_savings:
                    avg_savings = 5500
                elif "2,000-4,000" in suite_info.typical_savings:
                    avg_savings = 3000
                else:
                    avg_savings = 2000
                
                savings_breakdown[suite_info.name] = avg_savings
                total_monthly_savings += avg_savings
                
            except (ValueError, KeyError):
                continue
        
        # Calculate ROI metrics
        monthly_net_savings = total_monthly_savings - monthly_cost
        annual_net_savings = monthly_net_savings * 12
        roi_percentage = ((total_monthly_savings - monthly_cost) / monthly_cost * 100) if monthly_cost > 0 else 0
        payback_period_days = (monthly_cost / (total_monthly_savings / 30)) if total_monthly_savings > 0 else 999
        
        return {
            "monthly_investment": monthly_cost,
            "monthly_savings": total_monthly_savings,
            "monthly_net_benefit": monthly_net_savings,
            "annual_net_benefit": annual_net_savings,
            "roi_percentage": round(roi_percentage, 1),
            "payback_period_days": min(round(payback_period_days, 0), 999),
            "savings_breakdown": savings_breakdown,
            "break_even_point": f"{round(payback_period_days, 0)} days"
        }
    
    def _generate_plan_name(self, selected_suites: List[str], company_size: CompanySize) -> str:
        """Generate a user-friendly plan name"""
        
        size_prefix = {
            CompanySize.STARTUP: "Startup",
            CompanySize.SMALL_BUSINESS: "Business",
            CompanySize.MEDIUM_BUSINESS: "Professional", 
            CompanySize.ENTERPRISE: "Enterprise"
        }[company_size]
        
        if len(selected_suites) == 4:
            return f"{size_prefix} Complete"
        elif len(selected_suites) == 3:
            return f"{size_prefix} Advanced"
        elif len(selected_suites) == 2:
            return f"{size_prefix} Growth"
        elif len(selected_suites) == 1:
            return f"{size_prefix} Essential"
        else:
            return f"{size_prefix} Platform"
    
    def get_suite_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Return the complete suite catalog for frontend"""
        
        catalog = {}
        for suite, info in self.suite_catalog.items():
            catalog[suite.value] = {
                "name": info.name,
                "description": info.description,
                "base_price": float(info.base_price),
                "features": info.features,
                "endpoints": info.endpoints,
                "value_proposition": info.value_proposition,
                "typical_savings": info.typical_savings
            }
        
        return catalog
    
    def get_competitor_comparison(self, selected_suites: List[str]) -> Dict[str, Any]:
        """Generate competitor comparison for the selected suite combination"""
        
        # Mapping of our suites to competitor tools
        competitor_tools = {
            Suite.PREDICTIVE_ANALYTICS.value: [
                {"name": "HubSpot Marketing Hub Professional", "price": 890},
                {"name": "Salesforce Analytics Cloud", "price": 1200},
                {"name": "Google Analytics 360", "price": 1250}
            ],
            Suite.FINANCIAL_MANAGEMENT.value: [
                {"name": "QuickBooks Advanced", "price": 180},
                {"name": "FreshBooks", "price": 50},
                {"name": "Xero Premium", "price": 70}
            ],
            Suite.CONVERSATIONAL_AI.value: [
                {"name": "Intercom", "price": 500},
                {"name": "Drift", "price": 400},
                {"name": "LiveChat", "price": 200}
            ],
            Suite.HR_MANAGEMENT.value: [
                {"name": "BambooHR", "price": 250},
                {"name": "Workday", "price": 500},
                {"name": "ADP Workforce Now", "price": 300}
            ]
        }
        
        total_competitor_cost = 0
        tools_replaced = []
        
        for suite in selected_suites:
            if suite in competitor_tools:
                tool = competitor_tools[suite][0]  # Use primary competitor
                total_competitor_cost += tool["price"]
                tools_replaced.append(tool)
        
        our_pricing = self.calculate_pricing(selected_suites)
        our_cost = float(our_pricing.final_monthly_price)
        
        savings_vs_competitors = total_competitor_cost - our_cost
        savings_percentage = (savings_vs_competitors / total_competitor_cost * 100) if total_competitor_cost > 0 else 0
        
        return {
            "tools_replaced": tools_replaced,
            "competitor_total_cost": total_competitor_cost,
            "our_cost": our_cost,
            "monthly_savings": savings_vs_competitors,
            "savings_percentage": round(savings_percentage, 1),
            "tool_count_reduced": f"{len(tools_replaced)} tools → 1 platform"
        }