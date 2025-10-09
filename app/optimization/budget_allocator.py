"""
Budget Allocation Optimizer
Uses mathematical optimization to allocate budget across campaigns for maximum ROAS

Approach: Gradient-based optimization with constraints
- Maximize: Total Revenue
- Subject to: Total budget constraint, min/max per campaign
- Method: Gradient ascent with projected gradients
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CampaignPerformance:
    """Historical performance data for a campaign"""
    campaign_id: str
    platform: str
    current_budget: float

    # Performance metrics
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float

    # Calculated metrics
    ctr: float
    cpc: float
    cpa: float
    roas: float

    # Constraints
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None


@dataclass
class BudgetAllocation:
    """Optimized budget allocation result"""
    campaign_id: str
    current_budget: float
    recommended_budget: float
    budget_change: float
    budget_change_pct: float
    expected_revenue: float
    expected_roas: float
    confidence: float


class BudgetAllocator:
    """
    Budget allocation optimizer using gradient-based optimization

    Core idea:
    - Each campaign has a diminishing returns curve (revenue vs budget)
    - Allocate budget to equalize marginal ROAS across campaigns
    - Use historical data to estimate response curves
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        max_iterations: int = 100,
        convergence_threshold: float = 0.01
    ):
        """
        Initialize budget allocator

        Args:
            learning_rate: Step size for gradient ascent
            max_iterations: Maximum optimization iterations
            convergence_threshold: Stop when changes < threshold
        """
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

    def optimize(
        self,
        campaigns: List[CampaignPerformance],
        total_budget: float,
        min_budget_per_campaign: float = 10.0,
        max_change_pct: float = 0.5  # Max 50% change per campaign
    ) -> List[BudgetAllocation]:
        """
        Optimize budget allocation across campaigns

        Args:
            campaigns: List of campaign performance data
            total_budget: Total budget to allocate
            min_budget_per_campaign: Minimum budget per campaign
            max_change_pct: Maximum percentage change allowed

        Returns:
            List of optimized budget allocations
        """
        if not campaigns:
            return []

        if len(campaigns) == 1:
            # Only one campaign, give it all the budget
            campaign = campaigns[0]
            recommended = total_budget
            return [BudgetAllocation(
                campaign_id=campaign.campaign_id,
                current_budget=campaign.current_budget,
                recommended_budget=recommended,
                budget_change=recommended - campaign.current_budget,
                budget_change_pct=(recommended - campaign.current_budget) / campaign.current_budget if campaign.current_budget > 0 else 0,
                expected_revenue=self._estimate_revenue(campaign, recommended),
                expected_roas=self._estimate_roas(campaign, recommended),
                confidence=0.8
            )]

        # Initialize budgets (start with current allocation)
        budgets = {c.campaign_id: c.current_budget for c in campaigns}

        # Set constraints
        min_budgets = {
            c.campaign_id: c.min_budget or min_budget_per_campaign
            for c in campaigns
        }
        max_budgets = {
            c.campaign_id: c.max_budget or (c.current_budget * (1 + max_change_pct))
            for c in campaigns
        }

        # Normalize to total budget
        current_total = sum(budgets.values())
        if current_total > 0:
            scale = total_budget / current_total
            budgets = {cid: b * scale for cid, b in budgets.items()}
        else:
            # Equal distribution as starting point
            equal_budget = total_budget / len(campaigns)
            budgets = {c.campaign_id: equal_budget for c in campaigns}

        # Gradient ascent optimization
        for iteration in range(self.max_iterations):
            # Calculate gradients (marginal ROAS)
            gradients = {}
            for campaign in campaigns:
                budget = budgets[campaign.campaign_id]
                gradients[campaign.campaign_id] = self._marginal_roas(campaign, budget)

            # Update budgets in direction of gradient
            old_budgets = budgets.copy()
            total_gradient = sum(gradients.values())

            if total_gradient == 0:
                break

            for campaign in campaigns:
                cid = campaign.campaign_id

                # Move budget proportional to relative gradient strength
                gradient_weight = gradients[cid] / total_gradient if total_gradient != 0 else 0

                # If this campaign has above-average marginal ROAS, increase budget
                # If below-average, decrease budget
                avg_gradient = sum(gradients.values()) / len(gradients)
                if gradients[cid] > avg_gradient:
                    change = self.learning_rate * (gradients[cid] - avg_gradient) * total_budget
                else:
                    change = -self.learning_rate * (avg_gradient - gradients[cid]) * total_budget

                budgets[cid] += change

                # Apply constraints
                budgets[cid] = max(min_budgets[cid], min(max_budgets[cid], budgets[cid]))

            # Re-normalize to maintain total budget
            current_sum = sum(budgets.values())
            if current_sum > 0:
                scale = total_budget / current_sum
                budgets = {cid: b * scale for cid, b in budgets.items()}

            # Check convergence
            max_change = max(abs(budgets[cid] - old_budgets[cid]) for cid in budgets)
            if max_change < self.convergence_threshold:
                logger.info(f"Budget optimization converged in {iteration+1} iterations")
                break

        # Build results
        results = []
        for campaign in campaigns:
            recommended = budgets[campaign.campaign_id]

            results.append(BudgetAllocation(
                campaign_id=campaign.campaign_id,
                current_budget=campaign.current_budget,
                recommended_budget=recommended,
                budget_change=recommended - campaign.current_budget,
                budget_change_pct=(recommended - campaign.current_budget) / campaign.current_budget if campaign.current_budget > 0 else 0,
                expected_revenue=self._estimate_revenue(campaign, recommended),
                expected_roas=self._estimate_roas(campaign, recommended),
                confidence=self._calculate_confidence(campaign)
            ))

        return results

    def _marginal_roas(self, campaign: CampaignPerformance, budget: float) -> float:
        """
        Calculate marginal ROAS at given budget level

        This is the derivative of revenue with respect to budget.
        We use a power law model: Revenue = a * Budget^b
        Where b < 1 (diminishing returns)

        Marginal Revenue = a * b * Budget^(b-1)
        Marginal ROAS = Marginal Revenue / 1 = a * b * Budget^(b-1)
        """
        if campaign.spend == 0 or campaign.revenue == 0:
            return 0.0

        # Estimate power law parameters from historical data
        # Revenue = a * Spend^b
        # ROAS = Revenue / Spend = a * Spend^(b-1)
        #
        # From historical: a = Revenue / Spend^b
        # Assume b = 0.8 (typical diminishing returns)

        b = 0.8  # Diminishing returns exponent
        a = campaign.revenue / (campaign.spend ** b) if campaign.spend > 0 else 0

        # Marginal ROAS at new budget level
        marginal_roas = a * b * (budget ** (b - 1))

        return max(0, marginal_roas)

    def _estimate_revenue(self, campaign: CampaignPerformance, budget: float) -> float:
        """Estimate revenue at given budget level"""
        if campaign.spend == 0:
            return 0.0

        # Power law model
        b = 0.8
        a = campaign.revenue / (campaign.spend ** b) if campaign.spend > 0 else 0

        estimated_revenue = a * (budget ** b)
        return max(0, estimated_revenue)

    def _estimate_roas(self, campaign: CampaignPerformance, budget: float) -> float:
        """Estimate ROAS at given budget level"""
        if budget == 0:
            return 0.0

        revenue = self._estimate_revenue(campaign, budget)
        return revenue / budget

    def _calculate_confidence(self, campaign: CampaignPerformance) -> float:
        """
        Calculate confidence in optimization recommendation

        Higher confidence when:
        - More historical data (conversions)
        - Stable performance (not too volatile)
        - Clear ROAS signal
        """
        confidence = 0.5  # Base confidence

        # More conversions = higher confidence
        if campaign.conversions > 100:
            confidence += 0.3
        elif campaign.conversions > 50:
            confidence += 0.2
        elif campaign.conversions > 20:
            confidence += 0.1

        # Good ROAS = higher confidence
        if campaign.roas > 2.0:
            confidence += 0.2
        elif campaign.roas > 1.0:
            confidence += 0.1

        return min(confidence, 1.0)


class MultiPlatformBudgetAllocator:
    """
    Allocate budget across multiple platforms (Meta, Google, LinkedIn, etc.)
    Considers platform-specific constraints and performance
    """

    def __init__(self):
        self.allocator = BudgetAllocator()

    def optimize_cross_platform(
        self,
        platform_campaigns: Dict[str, List[CampaignPerformance]],
        total_budget: float,
        platform_constraints: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, List[BudgetAllocation]]:
        """
        Optimize budget allocation across multiple platforms

        Args:
            platform_campaigns: {platform: [campaigns]}
            total_budget: Total budget across all platforms
            platform_constraints: {platform: {"min": X, "max": Y}}

        Returns:
            {platform: [allocations]}
        """
        platform_constraints = platform_constraints or {}

        # Step 1: Allocate budget across platforms
        platform_budgets = self._allocate_platform_budgets(
            platform_campaigns,
            total_budget,
            platform_constraints
        )

        # Step 2: Allocate within each platform
        results = {}
        for platform, campaigns in platform_campaigns.items():
            if platform in platform_budgets:
                allocations = self.allocator.optimize(
                    campaigns,
                    platform_budgets[platform]
                )
                results[platform] = allocations

        return results

    def _allocate_platform_budgets(
        self,
        platform_campaigns: Dict[str, List[CampaignPerformance]],
        total_budget: float,
        platform_constraints: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Allocate budget across platforms based on aggregate ROAS"""
        platform_roas = {}

        for platform, campaigns in platform_campaigns.items():
            if not campaigns:
                platform_roas[platform] = 0.0
                continue

            # Calculate aggregate ROAS for platform
            total_revenue = sum(c.revenue for c in campaigns)
            total_spend = sum(c.spend for c in campaigns)
            platform_roas[platform] = total_revenue / total_spend if total_spend > 0 else 0.0

        # Allocate proportional to ROAS
        total_roas = sum(platform_roas.values())

        if total_roas == 0:
            # Equal distribution if no data
            equal_budget = total_budget / len(platform_campaigns)
            return {p: equal_budget for p in platform_campaigns}

        budgets = {}
        for platform, roas in platform_roas.items():
            # Allocate proportional to ROAS
            budget = (roas / total_roas) * total_budget

            # Apply constraints
            if platform in platform_constraints:
                min_budget = platform_constraints[platform].get("min", 0)
                max_budget = platform_constraints[platform].get("max", float('inf'))
                budget = max(min_budget, min(max_budget, budget))

            budgets[platform] = budget

        # Normalize to total budget
        current_total = sum(budgets.values())
        if current_total > 0:
            scale = total_budget / current_total
            budgets = {p: b * scale for p, b in budgets.items()}

        return budgets
