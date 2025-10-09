"""
Optimization Package
Real optimization algorithms for budget allocation and bid optimization
"""

from app.optimization.budget_allocator import (
    BudgetAllocator,
    MultiPlatformBudgetAllocator,
    CampaignPerformance,
    BudgetAllocation
)
from app.optimization.bid_optimizer import (
    BidOptimizer,
    DynamicBidAdjustment,
    BidContext,
    BidRecommendation,
    PerformanceSnapshot
)

__all__ = [
    # Budget Optimization
    "BudgetAllocator",
    "MultiPlatformBudgetAllocator",
    "CampaignPerformance",
    "BudgetAllocation",
    # Bid Optimization
    "BidOptimizer",
    "DynamicBidAdjustment",
    "BidContext",
    "BidRecommendation",
    "PerformanceSnapshot",
]
