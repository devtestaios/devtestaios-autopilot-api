"""
Predictive Analytics Module for PulseBridge.ai
Provides AI-powered forecasting and optimization capabilities
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from app.ml_service_integration import get_ml_service

logger = logging.getLogger(__name__)

class PredictiveAnalytics:
    """Advanced predictive analytics for marketing automation"""
    
    def __init__(self):
        self.ml_service = None
    
    async def _get_ml_service(self):
        """Get ML service client"""
        if not self.ml_service:
            self.ml_service = await get_ml_service()
        return self.ml_service
    
    async def forecast_campaign_performance(
        self,
        campaign_id: str,
        campaign_data: Dict[str, Any],
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Forecast campaign performance for next N days"""
        try:
            ml_service = await self._get_ml_service()
            
            # Prepare historical data (mock for now, would come from database)
            historical_data = await self._get_campaign_historical_data(campaign_id)
            
            # Get ML prediction
            prediction = await ml_service.predict_campaign_performance(
                platform=campaign_data.get("platform", "unknown"),
                campaign_data=campaign_data,
                historical_data=historical_data
            )
            
            if prediction["success"]:
                # Generate detailed forecast
                forecast = await self._generate_detailed_forecast(
                    prediction["predictions"],
                    forecast_days,
                    campaign_data
                )
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "forecast_period": f"{forecast_days} days",
                    "predictions": prediction["predictions"],
                    "detailed_forecast": forecast,
                    "confidence": prediction["confidence"],
                    "model_version": prediction.get("model_version", "1.0"),
                    "recommendations": await self._generate_recommendations(prediction),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "ML prediction failed"}
        
        except Exception as e:
            logger.error(f"Campaign forecast failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_multi_platform_budget(
        self,
        campaigns: List[Dict[str, Any]],
        total_budget: float,
        optimization_goal: str = "roi",
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize budget allocation across multiple platforms"""
        try:
            ml_service = await self._get_ml_service()
            
            # Get optimization from ML service
            optimization = await ml_service.optimize_budget_allocation(
                campaigns=campaigns,
                total_budget=total_budget,
                optimization_goal=optimization_goal
            )
            
            if optimization["success"]:
                # Apply constraints if provided
                if constraints:
                    optimization["optimized_budgets"] = await self._apply_budget_constraints(
                        optimization["optimized_budgets"],
                        constraints,
                        total_budget
                    )
                
                # Generate allocation insights
                insights = await self._generate_allocation_insights(
                    optimization["optimized_budgets"],
                    campaigns
                )
                
                return {
                    "success": True,
                    "optimization_goal": optimization_goal,
                    "total_budget": total_budget,
                    "optimized_allocations": optimization["optimized_budgets"],
                    "expected_improvement": optimization["expected_improvement"],
                    "confidence": optimization["confidence"],
                    "insights": insights,
                    "reallocation_summary": await self._calculate_reallocation_summary(
                        campaigns, optimization["optimized_budgets"]
                    ),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Budget optimization failed"}
        
        except Exception as e:
            logger.error(f"Budget optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_performance_anomalies(
        self,
        platform: str,
        metrics: List[Dict[str, Any]],
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """Detect anomalies in campaign performance metrics"""
        try:
            ml_service = await self._get_ml_service()
            
            anomalies_by_metric = {}
            
            # Analyze each metric type
            metric_types = set()
            for metric in metrics:
                metric_types.update(metric.keys())
            
            for metric_name in ["clicks", "conversions", "spend", "ctr", "cpc"]:
                if metric_name in metric_types:
                    metric_data = [
                        {"timestamp": m.get("timestamp"), "value": m.get(metric_name, 0)}
                        for m in metrics if metric_name in m
                    ]
                    
                    if metric_data:
                        anomaly_result = await ml_service.detect_anomalies(
                            metrics_data=metric_data,
                            metric_name=metric_name
                        )
                        
                        if anomaly_result["success"]:
                            anomalies_by_metric[metric_name] = anomaly_result
            
            # Generate overall anomaly report
            overall_report = await self._generate_anomaly_report(anomalies_by_metric, platform)
            
            return {
                "success": True,
                "platform": platform,
                "analysis_period": await self._get_analysis_period(metrics),
                "anomalies_by_metric": anomalies_by_metric,
                "overall_anomaly_score": overall_report["score"],
                "priority_alerts": overall_report["priority_alerts"],
                "recommendations": overall_report["recommendations"],
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def predict_lead_conversion_probability(
        self,
        leads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict conversion probability for leads using ML"""
        try:
            ml_service = await self._get_ml_service()
            
            # Score leads using ML
            scoring_result = await ml_service.score_leads(leads_data=leads)
            
            if scoring_result["success"]:
                scored_leads = scoring_result["scored_leads"]
                
                # Generate insights
                insights = await self._generate_lead_insights(scored_leads)
                
                # Prioritize leads
                prioritized_leads = await self._prioritize_leads(scored_leads)
                
                return {
                    "success": True,
                    "total_leads": len(leads),
                    "scored_leads": scored_leads,
                    "lead_insights": insights,
                    "priority_recommendations": prioritized_leads,
                    "model_accuracy": scoring_result["model_accuracy"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Lead scoring failed"}
        
        except Exception as e:
            logger.error(f"Lead scoring failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_market_trend_analysis(
        self,
        platform: str,
        industry: str,
        time_period: int = 90
    ) -> Dict[str, Any]:
        """Generate market trend analysis for platform/industry combination"""
        try:
            # This would typically connect to external market data APIs
            # For now, generate intelligent analysis based on available data
            
            trends = {
                "industry_growth": await self._analyze_industry_growth(industry),
                "platform_effectiveness": await self._analyze_platform_effectiveness(platform, industry),
                "seasonal_patterns": await self._analyze_seasonal_patterns(platform, time_period),
                "competitive_landscape": await self._analyze_competitive_landscape(platform, industry)
            }
            
            # Generate strategic recommendations
            recommendations = await self._generate_strategic_recommendations(trends, platform, industry)
            
            return {
                "success": True,
                "platform": platform,
                "industry": industry,
                "analysis_period": f"{time_period} days",
                "trend_analysis": trends,
                "strategic_recommendations": recommendations,
                "confidence_score": 0.75,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Market trend analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods
    
    async def _get_campaign_historical_data(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get historical performance data for campaign"""
        # Mock historical data - would come from database in production
        base_date = datetime.now() - timedelta(days=30)
        historical_data = []
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            historical_data.append({
                "date": date.isoformat(),
                "clicks": 100 + (i * 2) + (i % 7) * 10,
                "conversions": 5 + (i % 3),
                "spend": 50 + (i * 1.5),
                "ctr": 2.0 + (i % 5) * 0.1,
                "conversion_rate": 5.0 + (i % 4) * 0.2
            })
        
        return historical_data
    
    async def _generate_detailed_forecast(
        self,
        predictions: Dict[str, Any],
        forecast_days: int,
        campaign_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate day-by-day forecast"""
        forecast = []
        base_date = datetime.now()
        
        daily_clicks = predictions.get("clicks", 100) / forecast_days
        daily_conversions = predictions.get("conversions", 5) / forecast_days
        daily_spend = campaign_data.get("daily_budget", 50)
        
        for i in range(forecast_days):
            date = base_date + timedelta(days=i)
            
            # Add some realistic variance
            variance = 1 + (i % 7) * 0.1 - 0.3  # Weekend effects
            
            forecast.append({
                "date": date.isoformat()[:10],
                "predicted_clicks": int(daily_clicks * variance),
                "predicted_conversions": int(daily_conversions * variance),
                "predicted_spend": daily_spend,
                "confidence": predictions.get("confidence", 0.7) * (1 - i * 0.01)  # Decreasing confidence
            })
        
        return forecast
    
    async def _generate_recommendations(self, prediction: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on predictions"""
        recommendations = []
        
        predictions = prediction.get("predictions", {})
        confidence = prediction.get("confidence", 0.0)
        
        if confidence > 0.8:
            recommendations.append("High confidence predictions - consider increasing budget")
        elif confidence < 0.5:
            recommendations.append("Low confidence - gather more data before major changes")
        
        ctr = predictions.get("ctr", 0)
        if ctr < 1.0:
            recommendations.append("Low CTR predicted - consider refreshing ad creative")
        elif ctr > 3.0:
            recommendations.append("High CTR predicted - excellent creative performance")
        
        conversion_rate = predictions.get("conversion_rate", 0)
        if conversion_rate < 1.0:
            recommendations.append("Low conversion rate - optimize landing page")
        
        return recommendations
    
    async def _apply_budget_constraints(
        self,
        optimized_budgets: Dict[str, float],
        constraints: Dict[str, Any],
        total_budget: float
    ) -> Dict[str, float]:
        """Apply budget constraints to optimization results"""
        # Apply minimum/maximum constraints
        constrained_budgets = {}
        
        for campaign_id, budget in optimized_budgets.items():
            min_budget = constraints.get("min_budget_per_campaign", 0)
            max_budget = constraints.get("max_budget_per_campaign", total_budget)
            
            constrained_budgets[campaign_id] = max(min_budget, min(budget, max_budget))
        
        # Ensure total doesn't exceed limit
        total_allocated = sum(constrained_budgets.values())
        if total_allocated > total_budget:
            scale_factor = total_budget / total_allocated
            for campaign_id in constrained_budgets:
                constrained_budgets[campaign_id] *= scale_factor
        
        return constrained_budgets
    
    async def _generate_allocation_insights(
        self,
        optimized_budgets: Dict[str, float],
        campaigns: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights about budget allocation"""
        insights = []
        
        # Find campaigns with significant budget changes
        for campaign in campaigns:
            campaign_id = campaign.get("id")
            current_budget = campaign.get("budget", 0)
            new_budget = optimized_budgets.get(campaign_id, 0)
            
            if new_budget > current_budget * 1.2:
                insights.append(f"Campaign {campaign_id}: +{((new_budget/current_budget-1)*100):.1f}% budget increase recommended")
            elif new_budget < current_budget * 0.8:
                insights.append(f"Campaign {campaign_id}: -{((1-new_budget/current_budget)*100):.1f}% budget decrease recommended")
        
        return insights
    
    async def _calculate_reallocation_summary(
        self,
        campaigns: List[Dict[str, Any]],
        optimized_budgets: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate summary of budget reallocation"""
        total_current = sum(c.get("budget", 0) for c in campaigns)
        total_optimized = sum(optimized_budgets.values())
        
        increases = 0
        decreases = 0
        
        for campaign in campaigns:
            campaign_id = campaign.get("id")
            current = campaign.get("budget", 0)
            new = optimized_budgets.get(campaign_id, 0)
            
            if new > current:
                increases += (new - current)
            else:
                decreases += (current - new)
        
        return {
            "total_reallocated": increases,
            "campaigns_increased": len([c for c in campaigns if optimized_budgets.get(c.get("id"), 0) > c.get("budget", 0)]),
            "campaigns_decreased": len([c for c in campaigns if optimized_budgets.get(c.get("id"), 0) < c.get("budget", 0)]),
            "net_change": total_optimized - total_current
        }
    
    async def _generate_anomaly_report(
        self,
        anomalies_by_metric: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """Generate overall anomaly report"""
        total_anomalies = 0
        priority_alerts = []
        recommendations = []
        
        for metric_name, result in anomalies_by_metric.items():
            anomalies = result.get("anomalies_detected", [])
            total_anomalies += len(anomalies)
            
            if anomalies:
                priority_alerts.append(f"{metric_name.upper()}: {len(anomalies)} anomalies detected")
                
                if metric_name == "spend":
                    recommendations.append("Unusual spending pattern detected - review campaign settings")
                elif metric_name == "conversions":
                    recommendations.append("Conversion anomalies detected - check tracking implementation")
        
        overall_score = min(total_anomalies / 10.0, 1.0)  # Normalize to 0-1
        
        return {
            "score": overall_score,
            "priority_alerts": priority_alerts,
            "recommendations": recommendations
        }
    
    async def _get_analysis_period(self, metrics: List[Dict[str, Any]]) -> str:
        """Get the time period covered by metrics"""
        if not metrics:
            return "No data"
        
        timestamps = [m.get("timestamp") for m in metrics if m.get("timestamp")]
        if timestamps:
            return f"{min(timestamps)} to {max(timestamps)}"
        
        return f"Last {len(metrics)} data points"
    
    async def _generate_lead_insights(self, scored_leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about lead scoring results"""
        if not scored_leads:
            return {}
        
        scores = [lead.get("ml_score", 0) for lead in scored_leads]
        
        hot_leads = len([s for s in scores if s > 80])
        warm_leads = len([s for s in scores if 60 < s <= 80])
        cold_leads = len([s for s in scores if s <= 60])
        
        return {
            "average_score": sum(scores) / len(scores),
            "score_distribution": {
                "hot": hot_leads,
                "warm": warm_leads,
                "cold": cold_leads
            },
            "conversion_probability": {
                "hot": "70-90%",
                "warm": "30-50%", 
                "cold": "5-15%"
            }
        }
    
    async def _prioritize_leads(self, scored_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize leads based on scores and other factors"""
        # Sort by score (descending)
        sorted_leads = sorted(scored_leads, key=lambda x: x.get("ml_score", 0), reverse=True)
        
        # Return top 10 with action recommendations
        priority_leads = []
        for i, lead in enumerate(sorted_leads[:10]):
            score = lead.get("ml_score", 0)
            
            if score > 80:
                action = "Immediate follow-up recommended"
            elif score > 60:
                action = "Follow-up within 24 hours"
            else:
                action = "Add to nurture campaign"
            
            priority_leads.append({
                "rank": i + 1,
                "lead_id": lead.get("id", ""),
                "name": lead.get("name", ""),
                "score": score,
                "recommended_action": action,
                "urgency": "high" if score > 80 else "medium" if score > 60 else "low"
            })
        
        return priority_leads
    
    # Market analysis helper methods (simplified for now)
    
    async def _analyze_industry_growth(self, industry: str) -> Dict[str, Any]:
        """Analyze industry growth trends"""
        # Mock industry analysis
        growth_rates = {
            "technology": 8.5,
            "healthcare": 6.2,
            "finance": 4.1,
            "retail": 3.8,
            "manufacturing": 2.9
        }
        
        growth = growth_rates.get(industry.lower(), 5.0)
        
        return {
            "annual_growth_rate": growth,
            "trend": "growing" if growth > 4 else "stable" if growth > 2 else "declining",
            "market_maturity": "emerging" if growth > 8 else "mature"
        }
    
    async def _analyze_platform_effectiveness(self, platform: str, industry: str) -> Dict[str, Any]:
        """Analyze platform effectiveness for industry"""
        # Mock platform effectiveness
        effectiveness_matrix = {
            "google": {"b2b": 9, "b2c": 8, "ecommerce": 9},
            "facebook": {"b2b": 6, "b2c": 9, "ecommerce": 8},
            "linkedin": {"b2b": 10, "b2c": 4, "ecommerce": 5},
            "instagram": {"b2b": 4, "b2c": 8, "ecommerce": 9}
        }
        
        # Simplified industry mapping
        industry_type = "b2b" if industry.lower() in ["technology", "finance"] else "b2c"
        
        effectiveness = effectiveness_matrix.get(platform.lower(), {}).get(industry_type, 6)
        
        return {
            "effectiveness_score": effectiveness,
            "recommendation": "highly_recommended" if effectiveness >= 8 else "recommended" if effectiveness >= 6 else "consider_alternatives"
        }
    
    async def _analyze_seasonal_patterns(self, platform: str, time_period: int) -> Dict[str, Any]:
        """Analyze seasonal patterns"""
        # Mock seasonal analysis
        current_month = datetime.now().month
        
        seasonal_factors = {
            "q4": 1.3,  # Holiday season
            "q1": 0.8,  # Post-holiday
            "q2": 1.0,  # Spring
            "q3": 0.9   # Summer
        }
        
        quarter = f"q{(current_month - 1) // 3 + 1}"
        factor = seasonal_factors.get(quarter, 1.0)
        
        return {
            "current_seasonal_factor": factor,
            "trend": "peak" if factor > 1.2 else "normal" if factor > 0.9 else "low",
            "recommendation": "increase_budget" if factor > 1.1 else "maintain_budget" if factor > 0.9 else "reduce_budget"
        }
    
    async def _analyze_competitive_landscape(self, platform: str, industry: str) -> Dict[str, Any]:
        """Analyze competitive landscape"""
        # Mock competitive analysis
        return {
            "competition_level": "high",
            "average_cpc_trend": "increasing",
            "market_saturation": "moderate",
            "opportunity_score": 7.2
        }
    
    async def _generate_strategic_recommendations(
        self,
        trends: Dict[str, Any],
        platform: str,
        industry: str
    ) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Industry growth recommendations
        industry_growth = trends.get("industry_growth", {})
        if industry_growth.get("annual_growth_rate", 0) > 6:
            recommendations.append("High industry growth - consider increasing investment")
        
        # Platform effectiveness recommendations
        platform_eff = trends.get("platform_effectiveness", {})
        if platform_eff.get("effectiveness_score", 0) >= 8:
            recommendations.append(f"{platform} is highly effective for {industry} - prioritize this platform")
        
        # Seasonal recommendations
        seasonal = trends.get("seasonal_patterns", {})
        if seasonal.get("current_seasonal_factor", 1.0) > 1.1:
            recommendations.append("Peak season - consider budget increase")
        
        return recommendations

# Global predictive analytics instance
predictive_analytics = PredictiveAnalytics()

async def get_predictive_analytics() -> PredictiveAnalytics:
    """Get predictive analytics instance"""
    return predictive_analytics