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
from app.optimization.platform_executors import (
    MetaAdsExecutor,
    GoogleAdsExecutor,
    PlatformExecutorFactory
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
    # Platform Executors
    "MetaAdsExecutor",
    "GoogleAdsExecutor",
    "PlatformExecutorFactory",
]
