"""
ML Service Integration for PulseBridge.ai
Microservice approach for ML capabilities without affecting main deployment
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import json

logger = logging.getLogger(__name__)

class MLServiceClient:
    """Client for ML microservice - handles predictive analytics separately"""
    
    def __init__(self):
        # ML service URL - can be separate deployment or local service
        self.ml_service_url = os.getenv('ML_SERVICE_URL', 'http://localhost:8001')
        self.api_key = os.getenv('ML_SERVICE_API_KEY', 'dev-key')
        self.timeout = 30
        
    async def is_available(self) -> bool:
        """Check if ML service is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ml_service_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"ML service not available: {e}")
            return False
    
    async def predict_campaign_performance(
        self, 
        platform: str,
        campaign_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict campaign performance using ML models"""
        try:
            payload = {
                "platform": platform,
                "campaign_data": campaign_data,
                "historical_data": historical_data,
                "prediction_type": "campaign_performance"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ml_service_url}/predict/campaign-performance",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "predictions": result.get("predictions", {}),
                            "confidence": result.get("confidence", 0.0),
                            "model_version": result.get("model_version", "1.0"),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"ML service error: {error_text}")
                        return self._fallback_prediction(campaign_data)
        
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._fallback_prediction(campaign_data)
    
    async def optimize_budget_allocation(
        self,
        campaigns: List[Dict[str, Any]],
        total_budget: float,
        optimization_goal: str = "roi"
    ) -> Dict[str, Any]:
        """Optimize budget allocation across campaigns using ML"""
        try:
            payload = {
                "campaigns": campaigns,
                "total_budget": total_budget,
                "optimization_goal": optimization_goal
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ml_service_url}/optimize/budget-allocation",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "optimized_budgets": result.get("optimized_budgets", {}),
                            "expected_improvement": result.get("expected_improvement", 0.0),
                            "confidence": result.get("confidence", 0.0),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return self._fallback_budget_optimization(campaigns, total_budget)
        
        except Exception as e:
            logger.error(f"Budget optimization failed: {e}")
            return self._fallback_budget_optimization(campaigns, total_budget)
    
    async def detect_anomalies(
        self,
        metrics_data: List[Dict[str, Any]],
        metric_name: str
    ) -> Dict[str, Any]:
        """Detect anomalies in performance metrics"""
        try:
            payload = {
                "metrics_data": metrics_data,
                "metric_name": metric_name,
                "detection_sensitivity": "medium"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ml_service_url}/analyze/anomaly-detection",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "anomalies_detected": result.get("anomalies", []),
                            "anomaly_score": result.get("score", 0.0),
                            "recommendations": result.get("recommendations", []),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return self._fallback_anomaly_detection(metrics_data)
        
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return self._fallback_anomaly_detection(metrics_data)
    
    async def score_leads(
        self,
        leads_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Score leads using ML models"""
        try:
            payload = {
                "leads_data": leads_data,
                "scoring_model": "lead_conversion_probability"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ml_service_url}/score/leads",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "scored_leads": result.get("scored_leads", []),
                            "model_accuracy": result.get("accuracy", 0.0),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return self._fallback_lead_scoring(leads_data)
        
        except Exception as e:
            logger.error(f"Lead scoring failed: {e}")
            return self._fallback_lead_scoring(leads_data)
    
    def _fallback_prediction(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction when ML service unavailable"""
        # Simple rule-based prediction
        budget = campaign_data.get("budget", 1000)
        platform = campaign_data.get("platform", "unknown")
        
        # Basic platform multipliers
        platform_multipliers = {
            "google": 1.3,
            "facebook": 1.1,
            "instagram": 1.2,
            "linkedin": 0.9
        }
        
        multiplier = platform_multipliers.get(platform.lower(), 1.0)
        predicted_clicks = int(budget * 0.1 * multiplier)
        predicted_conversions = int(predicted_clicks * 0.02)
        
        return {
            "success": True,
            "predictions": {
                "clicks": predicted_clicks,
                "conversions": predicted_conversions,
                "ctr": 2.0,
                "conversion_rate": 2.0,
                "cost_per_conversion": budget / max(predicted_conversions, 1)
            },
            "confidence": 0.5,
            "model_version": "fallback",
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _fallback_budget_optimization(
        self, 
        campaigns: List[Dict[str, Any]], 
        total_budget: float
    ) -> Dict[str, Any]:
        """Fallback budget optimization"""
        if not campaigns:
            return {
                "success": False,
                "error": "No campaigns provided for optimization",
                "optimized_budgets": {},
                "expected_improvement": 0.0,
                "confidence": 0.0,
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate budget allocation based on performance
        optimized_budgets = {}
        total_performance_score = 0.0
        campaign_scores = {}
        
        # Calculate performance scores for each campaign
        for campaign in campaigns:
            campaign_id = campaign.get("id", "unknown")
            metrics = campaign.get("performance_metrics", {})
            
            # Calculate a simple performance score
            conversions = metrics.get("conversions", 0)
            cost_per_conversion = metrics.get("cost_per_conversion", float('inf'))
            
            # Higher conversions and lower cost per conversion = better score
            if cost_per_conversion == 0 or cost_per_conversion == float('inf'):
                score = conversions * 0.1  # Low score for campaigns with no cost data
            else:
                score = conversions / cost_per_conversion * 1000  # Normalize score
            
            campaign_scores[campaign_id] = max(score, 0.1)  # Minimum score
            total_performance_score += campaign_scores[campaign_id]
        
        # Allocate budget proportionally to performance scores
        if total_performance_score == 0:
            # Equal distribution as final fallback
            budget_per_campaign = total_budget / len(campaigns)
            for campaign in campaigns:
                campaign_id = campaign.get("id", "unknown")
                optimized_budgets[campaign_id] = budget_per_campaign
        else:
            for campaign in campaigns:
                campaign_id = campaign.get("id", "unknown")
                proportion = campaign_scores[campaign_id] / total_performance_score
                optimized_budgets[campaign_id] = total_budget * proportion
        
        return {
            "success": True,
            "optimized_budgets": optimized_budgets,
            "expected_improvement": 0.05,  # 5% improvement estimate
            "confidence": 0.3,
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _fallback_anomaly_detection(self, metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback anomaly detection"""
        # Simple threshold-based detection
        if not metrics_data:
            return {
                "success": True,
                "anomalies_detected": [],
                "anomaly_score": 0.0,
                "recommendations": [],
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        
        # Calculate basic statistics
        values = [item.get("value", 0) for item in metrics_data if "value" in item]
        if not values:
            return {
                "success": True,
                "anomalies_detected": [],
                "anomaly_score": 0.0,
                "recommendations": [],
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }
        
        avg_value = sum(values) / len(values)
        threshold = avg_value * 1.5  # 50% above average
        
        anomalies = []
        for item in metrics_data[-10:]:  # Check last 10 points
            if item.get("value", 0) > threshold:
                anomalies.append({
                    "timestamp": item.get("timestamp", ""),
                    "value": item.get("value", 0),
                    "severity": "medium",
                    "description": "Value significantly above average"
                })
        
        return {
            "success": True,
            "anomalies_detected": anomalies,
            "anomaly_score": len(anomalies) / 10.0,
            "recommendations": [
                "Monitor recent performance changes",
                "Review campaign settings for unexpected changes"
            ] if anomalies else [],
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _fallback_lead_scoring(self, leads_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback lead scoring"""
        scored_leads = []
        
        for lead in leads_data:
            # Simple scoring based on available data
            score = 50  # Base score
            
            # Adjust based on company size
            company_size = lead.get("company_size", "")
            if "enterprise" in company_size.lower():
                score += 30
            elif "mid" in company_size.lower():
                score += 15
            
            # Adjust based on email domain
            email = lead.get("email", "")
            if any(domain in email for domain in [".gov", ".edu", ".org"]):
                score += 20
            
            # Adjust based on engagement
            engagement = lead.get("engagement_score", 0)
            score += min(engagement * 0.3, 20)
            
            # Normalize to 0-100
            score = min(max(score, 0), 100)
            
            scored_leads.append({
                **lead,
                "ml_score": score,
                "score_category": "hot" if score > 80 else "warm" if score > 60 else "cold",
                "confidence": 0.6
            })
        
        return {
            "success": True,
            "scored_leads": scored_leads,
            "model_accuracy": 0.6,
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }

# Global ML service client
ml_service = MLServiceClient()

async def get_ml_service() -> MLServiceClient:
    """Get ML service client"""
    return ml_service