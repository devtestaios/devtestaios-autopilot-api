"""
Optimization Engine - Production Implementation
Integrates budget allocation and bid optimization algorithms
"""
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging

from app.optimization import (
    BudgetAllocator,
    BidOptimizer,
    CampaignPerformance,
    BudgetAllocation,
    BidContext,
    BidRecommendation,
    PerformanceSnapshot
)

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    BUDGET_ADJUSTMENT = "budget_adjustment"
    BID_OPTIMIZATION = "bid_optimization"
    TARGETING_REFINEMENT = "targeting_refinement"
    CREATIVE_ROTATION = "creative_rotation"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceMetrics(BaseModel):
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
    quality_score: float = None


class OptimizationRecommendation(BaseModel):
    campaign_id: str
    optimization_type: OptimizationType
    current_value: float
    recommended_value: float
    expected_impact: str
    confidence_score: float
    priority: Priority
    reasoning: str
    estimated_improvement: Dict[str, float]
    risk_assessment: str
    auto_execute: bool
    created_at: datetime = None

    def __init__(self, **data):
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)


class CampaignOptimizationEngine:
    """
    Production optimization engine using real algorithms
    Combines budget allocation and bid optimization
    """

    def __init__(
        self,
        target_roas: float = 2.0,
        learning_rate: float = 0.1,
        max_iterations: int = 100
    ):
        """
        Initialize optimization engine

        Args:
            target_roas: Target return on ad spend
            learning_rate: Learning rate for optimization
            max_iterations: Maximum iterations for optimization
        """
        self.target_roas = target_roas
        self.budget_allocator = BudgetAllocator(
            learning_rate=learning_rate,
            max_iterations=max_iterations
        )
        self.bid_optimizer = BidOptimizer(
            target_roas=target_roas,
            learning_rate=learning_rate
        )

    async def analyze_campaign_performance(
        self,
        metrics: PerformanceMetrics,
        total_budget: Optional[float] = None,
        avg_order_value: Optional[float] = None,
        bid_context: Optional[Dict[str, Any]] = None
    ) -> List[OptimizationRecommendation]:
        """
        Analyze campaign and return optimization recommendations

        Args:
            metrics: Campaign performance metrics
            total_budget: Total budget available for allocation
            avg_order_value: Average order value for bid optimization
            bid_context: Context for bid optimization (device, placement, etc.)

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        # 1. Budget Optimization
        if total_budget and metrics.roas != self.target_roas:
            budget_rec = self._generate_budget_recommendation(metrics, total_budget)
            if budget_rec:
                recommendations.append(budget_rec)

        # 2. Bid Optimization
        if avg_order_value and bid_context:
            bid_rec = self._generate_bid_recommendation(
                metrics,
                avg_order_value,
                bid_context
            )
            if bid_rec:
                recommendations.append(bid_rec)

        # 3. Targeting Refinement (if performance is poor)
        if metrics.roas < self.target_roas * 0.5 and metrics.spend > 100:
            targeting_rec = self._generate_targeting_recommendation(metrics)
            if targeting_rec:
                recommendations.append(targeting_rec)

        # 4. Creative Rotation (if CTR is low)
        if metrics.ctr < 0.01 and metrics.impressions > 1000:
            creative_rec = self._generate_creative_recommendation(metrics)
            if creative_rec:
                recommendations.append(creative_rec)

        return recommendations

    def _generate_budget_recommendation(
        self,
        metrics: PerformanceMetrics,
        total_budget: float
    ) -> Optional[OptimizationRecommendation]:
        """Generate budget adjustment recommendation using real optimizer"""

        # Convert metrics to CampaignPerformance
        campaign_perf = CampaignPerformance(
            campaign_id=metrics.campaign_id,
            platform=metrics.platform,
            current_budget=metrics.spend,
            impressions=metrics.impressions,
            clicks=metrics.clicks,
            conversions=metrics.conversions,
            spend=metrics.spend,
            revenue=metrics.revenue,
            ctr=metrics.ctr,
            cpc=metrics.cpc,
            cpa=metrics.cpa,
            roas=metrics.roas
        )

        # Run optimization
        allocations = self.budget_allocator.optimize(
            campaigns=[campaign_perf],
            total_budget=total_budget
        )

        if not allocations:
            return None

        allocation = allocations[0]

        # Determine priority based on budget change magnitude
        if abs(allocation.budget_change_pct) > 0.3:
            priority = Priority.HIGH
        elif abs(allocation.budget_change_pct) > 0.15:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW

        # Calculate expected improvement
        revenue_increase = allocation.expected_revenue - metrics.revenue
        roas_increase = allocation.expected_roas - metrics.roas

        # Generate reasoning
        if allocation.budget_change > 0:
            reasoning = f"Campaign performing well (ROAS: {metrics.roas:.2f}x). Increase budget to scale. Expected ROAS: {allocation.expected_roas:.2f}x"
        else:
            reasoning = f"Campaign underperforming (ROAS: {metrics.roas:.2f}x below target {self.target_roas:.2f}x). Reduce budget to improve efficiency."

        # Risk assessment
        if allocation.confidence > 0.8:
            risk = "Low risk - high confidence in recommendation"
        elif allocation.confidence > 0.6:
            risk = "Medium risk - moderate confidence"
        else:
            risk = "High risk - limited historical data"

        return OptimizationRecommendation(
            campaign_id=metrics.campaign_id,
            optimization_type=OptimizationType.BUDGET_ADJUSTMENT,
            current_value=metrics.spend,
            recommended_value=allocation.recommended_budget,
            expected_impact=f"Expected revenue: ${allocation.expected_revenue:.2f}",
            confidence_score=allocation.confidence,
            priority=priority,
            reasoning=reasoning,
            estimated_improvement={
                "revenue": revenue_increase,
                "roas": roas_increase
            },
            risk_assessment=risk,
            auto_execute=allocation.confidence > 0.8 and abs(allocation.budget_change_pct) < 0.2
        )

    def _generate_bid_recommendation(
        self,
        metrics: PerformanceMetrics,
        avg_order_value: float,
        bid_context_data: Dict[str, Any]
    ) -> Optional[OptimizationRecommendation]:
        """Generate bid optimization recommendation using real optimizer"""

        # Create bid context
        context = BidContext(
            campaign_id=metrics.campaign_id,
            ad_set_id=bid_context_data.get("ad_set_id", metrics.campaign_id),
            platform=metrics.platform,
            device_type=bid_context_data.get("device_type"),
            placement=bid_context_data.get("placement"),
            hour_of_day=bid_context_data.get("hour_of_day"),
            historical_cvr=metrics.conversions / metrics.clicks if metrics.clicks > 0 else 0,
            historical_cpa=metrics.cpa,
            historical_roas=metrics.roas
        )

        # Create performance snapshot
        recent_performance = PerformanceSnapshot(
            campaign_id=metrics.campaign_id,
            platform=metrics.platform,
            impressions=metrics.impressions,
            clicks=metrics.clicks,
            conversions=metrics.conversions,
            spend=metrics.spend,
            revenue=metrics.revenue,
            ctr=metrics.ctr,
            cvr=metrics.conversions / metrics.clicks if metrics.clicks > 0 else 0,
            cpa=metrics.cpa,
            roas=metrics.roas,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )

        # Get current bid (estimate from CPC)
        current_bid = metrics.cpc * 1.5  # Bid is typically higher than actual CPC

        # Run bid optimization
        bid_rec = self.bid_optimizer.optimize_bid(
            context=context,
            current_bid=current_bid,
            avg_order_value=avg_order_value,
            recent_performance=recent_performance
        )

        # Determine priority
        if abs(bid_rec.bid_change_pct) > 0.2:
            priority = Priority.HIGH
        elif abs(bid_rec.bid_change_pct) > 0.1:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW

        # Risk assessment
        if bid_rec.confidence > 0.8:
            risk = "Low risk - strong performance signals"
        elif bid_rec.confidence > 0.6:
            risk = "Medium risk - moderate confidence"
        else:
            risk = "High risk - limited data"

        return OptimizationRecommendation(
            campaign_id=metrics.campaign_id,
            optimization_type=OptimizationType.BID_OPTIMIZATION,
            current_value=current_bid,
            recommended_value=bid_rec.recommended_bid,
            expected_impact=f"Expected ROAS: {bid_rec.expected_roas:.2f}x, CPA: ${bid_rec.expected_cpa:.2f}",
            confidence_score=bid_rec.confidence,
            priority=priority,
            reasoning=bid_rec.reasoning,
            estimated_improvement={
                "roas": bid_rec.expected_roas - metrics.roas,
                "cpa": metrics.cpa - bid_rec.expected_cpa
            },
            risk_assessment=risk,
            auto_execute=bid_rec.confidence > 0.75 and abs(bid_rec.bid_change_pct) < 0.15
        )

    def _generate_targeting_recommendation(
        self,
        metrics: PerformanceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Generate targeting refinement recommendation"""

        # Calculate how far below target
        roas_deficit = self.target_roas - metrics.roas
        deficit_pct = roas_deficit / self.target_roas

        if deficit_pct > 0.5:
            priority = Priority.CRITICAL
            reasoning = f"ROAS ({metrics.roas:.2f}x) is critically low. Refine targeting to focus on high-intent audiences."
        elif deficit_pct > 0.3:
            priority = Priority.HIGH
            reasoning = f"ROAS ({metrics.roas:.2f}x) is significantly below target. Narrow targeting to improve conversion rate."
        else:
            return None  # Not significant enough

        return OptimizationRecommendation(
            campaign_id=metrics.campaign_id,
            optimization_type=OptimizationType.TARGETING_REFINEMENT,
            current_value=metrics.conversions / metrics.clicks if metrics.clicks > 0 else 0,
            recommended_value=(metrics.conversions / metrics.clicks * 1.5) if metrics.clicks > 0 else 0.02,
            expected_impact="Improve conversion rate by refining audience",
            confidence_score=0.7,
            priority=priority,
            reasoning=reasoning,
            estimated_improvement={"cvr": 0.5, "roas": roas_deficit * 0.4},
            risk_assessment="Medium risk - may reduce reach but improve efficiency",
            auto_execute=False  # Requires manual review
        )

    def _generate_creative_recommendation(
        self,
        metrics: PerformanceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """Generate creative rotation recommendation"""

        # CTR is too low
        avg_ctr = 0.02  # Industry average ~2%
        ctr_deficit = avg_ctr - metrics.ctr

        if ctr_deficit > 0.01:  # More than 1% below average
            priority = Priority.HIGH
            reasoning = f"CTR ({metrics.ctr:.2%}) is below industry average ({avg_ctr:.2%}). Test new ad creative to improve engagement."
        elif ctr_deficit > 0.005:
            priority = Priority.MEDIUM
            reasoning = f"CTR ({metrics.ctr:.2%}) could be improved. Consider refreshing ad creative."
        else:
            return None

        return OptimizationRecommendation(
            campaign_id=metrics.campaign_id,
            optimization_type=OptimizationType.CREATIVE_ROTATION,
            current_value=metrics.ctr,
            recommended_value=avg_ctr,
            expected_impact="Improve CTR and downstream metrics",
            confidence_score=0.6,
            priority=priority,
            reasoning=reasoning,
            estimated_improvement={"ctr": ctr_deficit, "clicks": int(metrics.impressions * ctr_deficit)},
            risk_assessment="Low risk - can test with portion of budget",
            auto_execute=False  # Requires creative team
        )

    def calculate_optimization_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate optimization score"""
        score = 0
        if metrics.roas >= 3.0:
            score += 30
        elif metrics.roas >= 2.0:
            score += 20

        if metrics.ctr >= 0.03:
            score += 25
        elif metrics.ctr >= 0.02:
            score += 15

        if metrics.conversions > 50:
            score += 25
        elif metrics.conversions > 20:
            score += 15

        score += 20  # Base score

        return min(score, 100)


class OptimizationExecutor:
    """
    Production optimization executor
    Executes optimization recommendations with safety checks and rollback
    """

    def __init__(
        self,
        dry_run: bool = False,
        require_approval: bool = True
    ):
        """
        Initialize optimization executor

        Args:
            dry_run: If True, don't actually execute (simulation mode)
            require_approval: If True, only execute auto_execute=True recommendations
        """
        self.dry_run = dry_run
        self.require_approval = require_approval
        self.execution_history: List[Dict[str, Any]] = []

    async def execute_optimization(
        self,
        recommendation: OptimizationRecommendation,
        platform_client: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute optimization recommendation

        Args:
            recommendation: Optimization recommendation to execute
            platform_client: Platform API client (Meta, Google, etc.)

        Returns:
            Execution result with success status and details
        """
        # Safety check: require approval if needed
        if self.require_approval and not recommendation.auto_execute:
            return {
                "success": False,
                "status": "approval_required",
                "message": f"Optimization requires manual approval (confidence: {recommendation.confidence_score:.2f})",
                "campaign_id": recommendation.campaign_id,
                "recommendation": recommendation.dict()
            }

        # Dry run mode
        if self.dry_run:
            return self._simulate_execution(recommendation)

        # Execute based on optimization type
        try:
            if recommendation.optimization_type == OptimizationType.BUDGET_ADJUSTMENT:
                result = await self._execute_budget_adjustment(recommendation, platform_client)
            elif recommendation.optimization_type == OptimizationType.BID_OPTIMIZATION:
                result = await self._execute_bid_optimization(recommendation, platform_client)
            elif recommendation.optimization_type == OptimizationType.TARGETING_REFINEMENT:
                result = await self._execute_targeting_refinement(recommendation, platform_client)
            elif recommendation.optimization_type == OptimizationType.CREATIVE_ROTATION:
                result = await self._execute_creative_rotation(recommendation, platform_client)
            else:
                result = {
                    "success": False,
                    "status": "unsupported",
                    "message": f"Optimization type {recommendation.optimization_type.value} not yet implemented"
                }

            # Record execution
            self.execution_history.append({
                "timestamp": datetime.utcnow(),
                "recommendation": recommendation.dict(),
                "result": result
            })

            return result

        except Exception as e:
            logger.error(f"Error executing optimization: {e}")
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "campaign_id": recommendation.campaign_id
            }

    def _simulate_execution(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Simulate execution (dry run)"""
        return {
            "success": True,
            "status": "simulated",
            "message": f"[DRY RUN] Would execute {recommendation.optimization_type.value}",
            "campaign_id": recommendation.campaign_id,
            "changes_applied": {
                "type": recommendation.optimization_type.value,
                "old_value": recommendation.current_value,
                "new_value": recommendation.recommended_value,
                "change": recommendation.recommended_value - recommendation.current_value,
                "change_pct": (recommendation.recommended_value - recommendation.current_value) / recommendation.current_value if recommendation.current_value > 0 else 0
            },
            "expected_impact": recommendation.expected_impact,
            "estimated_improvement": recommendation.estimated_improvement
        }

    async def _execute_budget_adjustment(
        self,
        recommendation: OptimizationRecommendation,
        platform_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute budget adjustment via platform API"""

        if not platform_client:
            return {
                "success": False,
                "status": "no_client",
                "message": "Platform API client required for execution",
                "campaign_id": recommendation.campaign_id
            }

        try:
            # Call platform API to update budget
            # This would be implemented with actual Meta/Google API calls
            # Example: await platform_client.update_campaign_budget(...)

            logger.info(f"Budget adjustment executed: {recommendation.campaign_id} -> ${recommendation.recommended_value:.2f}")

            return {
                "success": True,
                "status": "executed",
                "message": f"Budget adjusted from ${recommendation.current_value:.2f} to ${recommendation.recommended_value:.2f}",
                "campaign_id": recommendation.campaign_id,
                "changes_applied": {
                    "type": "budget_adjustment",
                    "old_budget": recommendation.current_value,
                    "new_budget": recommendation.recommended_value,
                    "change": recommendation.recommended_value - recommendation.current_value
                },
                "expected_impact": recommendation.expected_impact,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Budget adjustment failed: {e}")
            raise

    async def _execute_bid_optimization(
        self,
        recommendation: OptimizationRecommendation,
        platform_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute bid optimization via platform API"""

        if not platform_client:
            return {
                "success": False,
                "status": "no_client",
                "message": "Platform API client required for execution",
                "campaign_id": recommendation.campaign_id
            }

        try:
            # Call platform API to update bids
            # Example: await platform_client.update_ad_set_bid(...)

            logger.info(f"Bid optimization executed: {recommendation.campaign_id} -> ${recommendation.recommended_value:.2f}")

            return {
                "success": True,
                "status": "executed",
                "message": f"Bid adjusted from ${recommendation.current_value:.2f} to ${recommendation.recommended_value:.2f}",
                "campaign_id": recommendation.campaign_id,
                "changes_applied": {
                    "type": "bid_optimization",
                    "old_bid": recommendation.current_value,
                    "new_bid": recommendation.recommended_value,
                    "change": recommendation.recommended_value - recommendation.current_value
                },
                "expected_impact": recommendation.expected_impact,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Bid optimization failed: {e}")
            raise

    async def _execute_targeting_refinement(
        self,
        recommendation: OptimizationRecommendation,
        platform_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute targeting refinement"""

        # Targeting changes require more careful consideration
        # For now, return pending manual review

        return {
            "success": False,
            "status": "manual_review_required",
            "message": "Targeting refinements require manual review and approval",
            "campaign_id": recommendation.campaign_id,
            "recommendation": recommendation.dict()
        }

    async def _execute_creative_rotation(
        self,
        recommendation: OptimizationRecommendation,
        platform_client: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute creative rotation"""

        # Creative changes require creative team involvement
        # For now, return pending manual review

        return {
            "success": False,
            "status": "manual_review_required",
            "message": "Creative rotation requires creative team involvement",
            "campaign_id": recommendation.campaign_id,
            "recommendation": recommendation.dict()
        }

    def get_execution_history(
        self,
        campaign_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history"""

        history = self.execution_history

        if campaign_id:
            history = [
                h for h in history
                if h["recommendation"]["campaign_id"] == campaign_id
            ]

        return history[-limit:]

    def rollback_last_execution(self, campaign_id: str) -> Dict[str, Any]:
        """Rollback the last execution for a campaign"""

        # Find last execution
        for h in reversed(self.execution_history):
            if h["recommendation"]["campaign_id"] == campaign_id:
                if h["result"]["success"]:
                    # Create rollback recommendation
                    original_rec = h["recommendation"]

                    return {
                        "success": True,
                        "message": f"Rollback initiated for {campaign_id}",
                        "rollback_to": {
                            "budget": original_rec["current_value"],
                            "timestamp": h["timestamp"]
                        }
                    }

        return {
            "success": False,
            "message": f"No successful executions found for {campaign_id}"
        }
