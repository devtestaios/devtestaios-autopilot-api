"""
FastAPI endpoints for Real-Time Campaign Optimization Engine
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json

from optimization_engine import (
    CampaignOptimizationEngine, 
    OptimizationExecutor,
    PerformanceMetrics,
    OptimizationRecommendation,
    OptimizationType,
    Priority
)

router = APIRouter(prefix="/api/v1/optimization", tags=["optimization"])

# Global instances
optimization_engine = CampaignOptimizationEngine()
optimization_executor = OptimizationExecutor()

# Pydantic models for API
class PerformanceMetricsRequest(BaseModel):
    campaign_id: str
    platform: str
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    ctr: float
    cpc: float
    cpa: float
    roas: float
    quality_score: Optional[float] = None

class OptimizationRecommendationResponse(BaseModel):
    campaign_id: str
    optimization_type: str
    current_value: float
    recommended_value: float
    expected_impact: str
    confidence_score: float
    priority: str
    reasoning: str
    estimated_improvement: Dict[str, float]
    risk_assessment: str
    auto_execute: bool
    created_at: datetime

class OptimizationExecutionRequest(BaseModel):
    recommendation_id: str
    campaign_id: str
    optimization_type: str
    recommended_value: float
    force_execute: bool = False

class OptimizationExecutionResponse(BaseModel):
    success: bool
    message: str
    execution_id: str
    timestamp: datetime
    details: Dict[str, Any]

class CampaignOptimizationStatus(BaseModel):
    campaign_id: str
    optimization_score: float
    status: str  # 'optimal', 'needs_attention', 'critical'
    active_optimizations: int
    last_optimization: Optional[datetime]
    recommendations_count: int

@router.post("/analyze", response_model=List[OptimizationRecommendationResponse])
async def analyze_campaign_performance(metrics: PerformanceMetricsRequest):
    """
    Analyze campaign performance and return optimization recommendations
    """
    try:
        # Convert request to internal metrics format
        performance_metrics = PerformanceMetrics(
            campaign_id=metrics.campaign_id,
            platform=metrics.platform,
            impressions=metrics.impressions,
            clicks=metrics.clicks,
            conversions=metrics.conversions,
            spend=metrics.spend,
            revenue=metrics.revenue,
            ctr=metrics.ctr,
            cpc=metrics.cpc,
            cpa=metrics.cpa,
            roas=metrics.roas,
            quality_score=metrics.quality_score
        )
        
        # Get optimization recommendations
        recommendations = await optimization_engine.analyze_campaign_performance(performance_metrics)
        
        # Convert to response format
        response_recommendations = []
        for rec in recommendations:
            response_recommendations.append(OptimizationRecommendationResponse(
                campaign_id=rec.campaign_id,
                optimization_type=rec.optimization_type.value,
                current_value=rec.current_value,
                recommended_value=rec.recommended_value,
                expected_impact=rec.expected_impact,
                confidence_score=rec.confidence_score,
                priority=rec.priority.value,
                reasoning=rec.reasoning,
                estimated_improvement=rec.estimated_improvement,
                risk_assessment=rec.risk_assessment,
                auto_execute=rec.auto_execute,
                created_at=rec.created_at
            ))
        
        return response_recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/execute", response_model=OptimizationExecutionResponse)
async def execute_optimization(
    request: OptimizationExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute an optimization recommendation
    """
    try:
        # Create optimization recommendation object
        optimization_type = OptimizationType(request.optimization_type)
        
        recommendation = OptimizationRecommendation(
            campaign_id=request.campaign_id,
            optimization_type=optimization_type,
            current_value=0,  # Would be fetched from actual campaign
            recommended_value=request.recommended_value,
            expected_impact="Manual execution",
            confidence_score=1.0,
            priority=Priority.HIGH,
            reasoning="Manual execution request",
            estimated_improvement={},
            risk_assessment="User approved",
            auto_execute=True
        )
        
        # Execute the optimization
        result = await optimization_executor.execute_optimization(recommendation)
        
        execution_id = f"exec_{request.campaign_id}_{int(datetime.utcnow().timestamp())}"
        
        return OptimizationExecutionResponse(
            success=result.get('success', False),
            message=result.get('message', 'Execution completed'),
            execution_id=execution_id,
            timestamp=datetime.utcnow(),
            details=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/status/{campaign_id}", response_model=CampaignOptimizationStatus)
async def get_campaign_optimization_status(campaign_id: str):
    """
    Get optimization status for a specific campaign
    """
    try:
        # Mock performance metrics for status calculation
        # In real implementation, this would fetch latest campaign data
        mock_metrics = PerformanceMetrics(
            campaign_id=campaign_id,
            platform="google_ads",
            impressions=10000,
            clicks=300,
            conversions=25,
            spend=500.0,
            revenue=1500.0,
            ctr=0.03,
            cpc=1.67,
            cpa=20.0,
            roas=3.0
        )
        
        # Calculate optimization score
        optimization_score = optimization_engine.calculate_optimization_score(mock_metrics)
        
        # Determine status based on score
        if optimization_score >= 80:
            status = "optimal"
        elif optimization_score >= 60:
            status = "needs_attention"
        else:
            status = "critical"
        
        # Get recommendations count
        recommendations = await optimization_engine.analyze_campaign_performance(mock_metrics)
        
        return CampaignOptimizationStatus(
            campaign_id=campaign_id,
            optimization_score=optimization_score,
            status=status,
            active_optimizations=len([r for r in recommendations if r.auto_execute]),
            last_optimization=datetime.utcnow(),  # Mock data
            recommendations_count=len(recommendations)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/recommendations/all")
async def get_all_campaign_recommendations():
    """
    Get optimization recommendations for all campaigns
    """
    try:
        # Mock multiple campaigns
        campaigns = [
            {"id": "campaign_1", "name": "Holiday Sale 2024", "platform": "google_ads"},
            {"id": "campaign_2", "name": "Retargeting Campaign", "platform": "meta"},
            {"id": "campaign_3", "name": "Brand Awareness", "platform": "linkedin"}
        ]
        
        all_recommendations = []
        
        for campaign in campaigns:
            # Mock metrics for each campaign
            metrics = PerformanceMetrics(
                campaign_id=campaign["id"],
                platform=campaign["platform"],
                impressions=5000 + (hash(campaign["id"]) % 10000),
                clicks=150 + (hash(campaign["id"]) % 200),
                conversions=10 + (hash(campaign["id"]) % 20),
                spend=250.0 + (hash(campaign["id"]) % 500),
                revenue=750.0 + (hash(campaign["id"]) % 1500),
                ctr=0.02 + (hash(campaign["id"]) % 100) / 10000,
                cpc=1.0 + (hash(campaign["id"]) % 200) / 100,
                cpa=15.0 + (hash(campaign["id"]) % 50),
                roas=2.0 + (hash(campaign["id"]) % 300) / 100
            )
            
            campaign_recs = await optimization_engine.analyze_campaign_performance(metrics)
            
            for rec in campaign_recs:
                all_recommendations.append({
                    "campaign_id": rec.campaign_id,
                    "campaign_name": campaign["name"],
                    "platform": campaign["platform"],
                    "optimization_type": rec.optimization_type.value,
                    "expected_impact": rec.expected_impact,
                    "confidence_score": rec.confidence_score,
                    "priority": rec.priority.value,
                    "reasoning": rec.reasoning,
                    "auto_execute": rec.auto_execute,
                    "created_at": rec.created_at
                })
        
        return {
            "total_recommendations": len(all_recommendations),
            "auto_executable": len([r for r in all_recommendations if r["auto_execute"]]),
            "high_priority": len([r for r in all_recommendations if r["priority"] == "high"]),
            "recommendations": all_recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.post("/batch-execute")
async def batch_execute_optimizations(
    campaign_ids: List[str],
    optimization_types: List[str],
    background_tasks: BackgroundTasks
):
    """
    Execute multiple optimizations in batch
    """
    try:
        results = []
        
        for campaign_id, opt_type in zip(campaign_ids, optimization_types):
            try:
                # Create and execute optimization
                recommendation = OptimizationRecommendation(
                    campaign_id=campaign_id,
                    optimization_type=OptimizationType(opt_type),
                    current_value=100.0,  # Mock current value
                    recommended_value=150.0,  # Mock recommended value
                    expected_impact="Batch execution",
                    confidence_score=0.8,
                    priority=Priority.MEDIUM,
                    reasoning="Batch optimization request",
                    estimated_improvement={},
                    risk_assessment="Batch approved",
                    auto_execute=True
                )
                
                result = await optimization_executor.execute_optimization(recommendation)
                
                results.append({
                    "campaign_id": campaign_id,
                    "optimization_type": opt_type,
                    "success": result.get('success', False),
                    "message": result.get('message', ''),
                    "timestamp": datetime.utcnow()
                })
                
            except Exception as e:
                results.append({
                    "campaign_id": campaign_id,
                    "optimization_type": opt_type,
                    "success": False,
                    "message": f"Failed: {str(e)}",
                    "timestamp": datetime.utcnow()
                })
        
        successful_executions = len([r for r in results if r["success"]])
        
        return {
            "total_attempted": len(results),
            "successful": successful_executions,
            "failed": len(results) - successful_executions,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")

@router.get("/performance-insights/{campaign_id}")
async def get_performance_insights(campaign_id: str):
    """
    Get detailed performance insights and optimization opportunities
    """
    try:
        # Mock detailed insights
        insights = {
            "campaign_id": campaign_id,
            "optimization_score": 75,
            "performance_grade": "B+",
            "key_insights": [
                {
                    "category": "Budget Efficiency",
                    "score": 85,
                    "insight": "Budget is being utilized efficiently with strong ROAS",
                    "recommendation": "Consider increasing budget by 20% to scale performance"
                },
                {
                    "category": "Audience Targeting",
                    "score": 70,
                    "insight": "CTR is slightly below optimal range",
                    "recommendation": "Refine audience targeting to improve relevance"
                },
                {
                    "category": "Creative Performance",
                    "score": 60,
                    "insight": "Ad creative may need refreshing",
                    "recommendation": "Test new creative variants to combat ad fatigue"
                },
                {
                    "category": "Keyword Optimization",
                    "score": 80,
                    "insight": "Most keywords performing well",
                    "recommendation": "Pause 3 underperforming keywords to reduce waste"
                }
            ],
            "performance_trends": {
                "7_day_roas_trend": [3.2, 3.4, 3.1, 3.6, 3.8, 3.5, 3.7],
                "7_day_cpc_trend": [1.85, 1.78, 1.92, 1.67, 1.71, 1.83, 1.75],
                "7_day_conversion_rate_trend": [2.1, 2.3, 2.0, 2.5, 2.7, 2.4, 2.6]
            },
            "optimization_opportunities": [
                {
                    "type": "budget_increase",
                    "potential_impact": "+25% revenue",
                    "confidence": 0.85,
                    "effort": "low"
                },
                {
                    "type": "audience_refinement",
                    "potential_impact": "+15% CTR",
                    "confidence": 0.70,
                    "effort": "medium"
                }
            ],
            "next_optimization_date": datetime.utcnow().isoformat()
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

# Health check endpoint
@router.get("/health")
async def optimization_engine_health():
    """Check optimization engine health"""
    return {
        "status": "healthy",
        "engine_version": "1.0.0",
        "capabilities": [
            "budget_optimization",
            "bid_management", 
            "performance_analysis",
            "automated_execution",
            "risk_assessment"
        ],
        "uptime": "24/7",
        "last_check": datetime.utcnow()
    }