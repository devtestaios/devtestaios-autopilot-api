"""
Tests for Optimization Engine
Tests budget allocation, bid optimization, and execution
"""
import pytest
from datetime import datetime, timedelta

from app.optimization import (
    BudgetAllocator,
    BidOptimizer,
    CampaignPerformance,
    BudgetAllocation,
    BidContext,
    BidRecommendation,
    PerformanceSnapshot
)
from app.optimization_engine import (
    CampaignOptimizationEngine,
    OptimizationExecutor,
    PerformanceMetrics,
    OptimizationType,
    Priority
)


# ============================================================================
# Budget Allocator Tests
# ============================================================================

def test_budget_allocator_single_campaign():
    """Test budget allocation with single campaign"""
    allocator = BudgetAllocator()

    campaign = CampaignPerformance(
        campaign_id="campaign_1",
        platform="meta",
        current_budget=100.0,
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=300.0,
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=3.0
    )

    allocations = allocator.optimize(
        campaigns=[campaign],
        total_budget=150.0
    )

    assert len(allocations) == 1
    allocation = allocations[0]

    assert allocation.campaign_id == "campaign_1"
    assert allocation.recommended_budget == 150.0
    assert allocation.budget_change == 50.0
    assert allocation.budget_change_pct == 0.5


def test_budget_allocator_multiple_campaigns():
    """Test budget allocation across multiple campaigns"""
    allocator = BudgetAllocator(learning_rate=0.1, max_iterations=50)

    campaigns = [
        CampaignPerformance(
            campaign_id="high_performer",
            platform="meta",
            current_budget=100.0,
            impressions=10000,
            clicks=500,
            conversions=50,
            spend=100.0,
            revenue=400.0,  # ROAS 4.0 - high performer
            ctr=0.05,
            cpc=0.20,
            cpa=2.0,
            roas=4.0
        ),
        CampaignPerformance(
            campaign_id="low_performer",
            platform="google",
            current_budget=100.0,
            impressions=8000,
            clicks=200,
            conversions=10,
            spend=100.0,
            revenue=100.0,  # ROAS 1.0 - low performer
            ctr=0.025,
            cpc=0.50,
            cpa=10.0,
            roas=1.0
        )
    ]

    allocations = allocator.optimize(
        campaigns=campaigns,
        total_budget=200.0
    )

    assert len(allocations) == 2

    # High performer should get more budget
    high_perf_allocation = next(a for a in allocations if a.campaign_id == "high_performer")
    low_perf_allocation = next(a for a in allocations if a.campaign_id == "low_performer")

    assert high_perf_allocation.recommended_budget > low_perf_allocation.recommended_budget

    # Total budget should be allocated
    total_allocated = sum(a.recommended_budget for a in allocations)
    assert abs(total_allocated - 200.0) < 1.0  # Within $1


def test_budget_allocator_respects_constraints():
    """Test that budget allocator respects min/max constraints"""
    allocator = BudgetAllocator()

    campaign = CampaignPerformance(
        campaign_id="campaign_1",
        platform="meta",
        current_budget=100.0,
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=300.0,
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=3.0,
        min_budget=80.0,
        max_budget=120.0
    )

    allocations = allocator.optimize(
        campaigns=[campaign],
        total_budget=200.0  # Try to allocate more than max
    )

    allocation = allocations[0]

    # Should respect max constraint
    assert allocation.recommended_budget <= 120.0
    assert allocation.recommended_budget >= 80.0


# ============================================================================
# Bid Optimizer Tests
# ============================================================================

def test_bid_optimizer_basic():
    """Test basic bid optimization"""
    optimizer = BidOptimizer(target_roas=2.0)

    context = BidContext(
        campaign_id="campaign_1",
        ad_set_id="adset_1",
        platform="meta",
        historical_cvr=0.05,  # 5% conversion rate
        historical_roas=2.5
    )

    recommendation = optimizer.optimize_bid(
        context=context,
        current_bid=1.0,
        avg_order_value=50.0
    )

    assert recommendation.campaign_id == "campaign_1"
    assert recommendation.current_bid == 1.0
    assert recommendation.recommended_bid > 0
    assert recommendation.expected_roas > 0


def test_bid_optimizer_scales_up_high_performer():
    """Test that bid optimizer increases bids for high performers"""
    optimizer = BidOptimizer(target_roas=2.0)

    context = BidContext(
        campaign_id="campaign_1",
        ad_set_id="adset_1",
        platform="meta",
        historical_cvr=0.10,  # High conversion rate
        historical_roas=4.0  # Performing well above target
    )

    # Recent performance is also strong
    recent_performance = PerformanceSnapshot(
        campaign_id="campaign_1",
        platform="meta",
        impressions=5000,
        clicks=250,
        conversions=30,
        spend=50.0,
        revenue=250.0,  # ROAS 5.0
        ctr=0.05,
        cvr=0.12,
        cpa=1.67,
        roas=5.0,
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow()
    )

    recommendation = optimizer.optimize_bid(
        context=context,
        current_bid=1.0,
        avg_order_value=50.0,
        recent_performance=recent_performance
    )

    # Should recommend increasing bid since performance is strong
    assert recommendation.recommended_bid > recommendation.current_bid
    assert recommendation.expected_roas >= optimizer.target_roas


def test_bid_optimizer_scales_down_low_performer():
    """Test that bid optimizer decreases bids for low performers"""
    optimizer = BidOptimizer(target_roas=2.0)

    context = BidContext(
        campaign_id="campaign_1",
        ad_set_id="adset_1",
        platform="meta",
        historical_cvr=0.02,  # Low conversion rate
        historical_roas=0.8  # Below target
    )

    recent_performance = PerformanceSnapshot(
        campaign_id="campaign_1",
        platform="meta",
        impressions=5000,
        clicks=250,
        conversions=5,
        spend=100.0,
        revenue=50.0,  # ROAS 0.5 - poor
        ctr=0.05,
        cvr=0.02,
        cpa=20.0,
        roas=0.5,
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow()
    )

    recommendation = optimizer.optimize_bid(
        context=context,
        current_bid=2.0,
        avg_order_value=50.0,
        recent_performance=recent_performance
    )

    # Should recommend decreasing bid since performance is poor
    assert recommendation.recommended_bid < recommendation.current_bid


def test_bid_optimizer_respects_constraints():
    """Test that bid optimizer respects min/max bid constraints"""
    optimizer = BidOptimizer(
        target_roas=2.0,
        min_bid=0.50,
        max_bid=10.0,
        max_bid_change_pct=0.20
    )

    context = BidContext(
        campaign_id="campaign_1",
        ad_set_id="adset_1",
        platform="meta",
        historical_cvr=0.01,
        historical_roas=10.0
    )

    recommendation = optimizer.optimize_bid(
        context=context,
        current_bid=5.0,
        avg_order_value=100.0
    )

    # Should respect constraints
    assert recommendation.recommended_bid >= 0.50
    assert recommendation.recommended_bid <= 10.0

    # Should respect max change percentage
    max_allowed_change = 5.0 * 0.20
    assert abs(recommendation.recommended_bid - 5.0) <= max_allowed_change + 0.01


def test_bid_optimizer_contextual_adjustments():
    """Test that bid optimizer applies contextual adjustments"""
    optimizer = BidOptimizer(target_roas=2.0)

    # Desktop placement during peak hours
    context_desktop = BidContext(
        campaign_id="campaign_1",
        ad_set_id="adset_1",
        platform="meta",
        device_type="desktop",
        placement="feed",
        hour_of_day=14,  # 2pm - peak hour
        historical_cvr=0.05,
        historical_roas=2.0
    )

    # Mobile story placement during off-hours
    context_mobile = BidContext(
        campaign_id="campaign_1",
        ad_set_id="adset_2",
        platform="meta",
        device_type="mobile",
        placement="story",
        hour_of_day=3,  # 3am - off-peak
        historical_cvr=0.05,
        historical_roas=2.0
    )

    rec_desktop = optimizer.optimize_bid(context_desktop, 1.0, 50.0)
    rec_mobile = optimizer.optimize_bid(context_mobile, 1.0, 50.0)

    # Desktop during peak should have higher expected CVR and higher bid
    assert rec_desktop.expected_cvr > rec_mobile.expected_cvr


# ============================================================================
# Campaign Optimization Engine Tests
# ============================================================================

@pytest.mark.asyncio
async def test_optimization_engine_budget_recommendation():
    """Test that optimization engine generates budget recommendations"""
    engine = CampaignOptimizationEngine(target_roas=2.0)

    metrics = PerformanceMetrics(
        campaign_id="campaign_1",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=300.0,  # ROAS 3.0 - above target
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=3.0
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0
    )

    assert len(recommendations) > 0

    # Should have budget recommendation
    budget_recs = [r for r in recommendations if r.optimization_type == OptimizationType.BUDGET_ADJUSTMENT]
    assert len(budget_recs) > 0

    budget_rec = budget_recs[0]
    assert budget_rec.campaign_id == "campaign_1"
    # High performer should get budget increase
    assert budget_rec.recommended_value > budget_rec.current_value


@pytest.mark.asyncio
async def test_optimization_engine_bid_recommendation():
    """Test that optimization engine generates bid recommendations"""
    engine = CampaignOptimizationEngine(target_roas=2.0)

    metrics = PerformanceMetrics(
        campaign_id="campaign_1",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=300.0,
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=3.0
    )

    bid_context = {
        "ad_set_id": "adset_1",
        "device_type": "desktop",
        "placement": "feed"
    }

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0,
        avg_order_value=60.0,
        bid_context=bid_context
    )

    # Should have bid recommendation
    bid_recs = [r for r in recommendations if r.optimization_type == OptimizationType.BID_OPTIMIZATION]
    assert len(bid_recs) > 0

    bid_rec = bid_recs[0]
    assert bid_rec.campaign_id == "campaign_1"
    assert bid_rec.recommended_value > 0


@pytest.mark.asyncio
async def test_optimization_engine_targeting_recommendation():
    """Test that optimization engine suggests targeting refinement for poor performers"""
    engine = CampaignOptimizationEngine(target_roas=2.0)

    metrics = PerformanceMetrics(
        campaign_id="poor_campaign",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=5,  # Very low conversions
        spend=200.0,
        revenue=100.0,  # ROAS 0.5 - very poor
        ctr=0.05,
        cpc=0.40,
        cpa=40.0,
        roas=0.5
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=300.0
    )

    # Should have targeting refinement recommendation
    targeting_recs = [r for r in recommendations if r.optimization_type == OptimizationType.TARGETING_REFINEMENT]
    assert len(targeting_recs) > 0

    targeting_rec = targeting_recs[0]
    assert targeting_rec.priority in [Priority.HIGH, Priority.CRITICAL]


@pytest.mark.asyncio
async def test_optimization_engine_creative_recommendation():
    """Test that optimization engine suggests creative rotation for low CTR"""
    engine = CampaignOptimizationEngine(target_roas=2.0)

    metrics = PerformanceMetrics(
        campaign_id="low_ctr_campaign",
        platform="meta",
        impressions=20000,
        clicks=100,  # Very low CTR (0.5%)
        conversions=10,
        spend=100.0,
        revenue=200.0,
        ctr=0.005,  # 0.5% - very low
        cpc=1.0,
        cpa=10.0,
        roas=2.0
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0
    )

    # Should have creative rotation recommendation
    creative_recs = [r for r in recommendations if r.optimization_type == OptimizationType.CREATIVE_ROTATION]
    assert len(creative_recs) > 0

    creative_rec = creative_recs[0]
    assert creative_rec.priority in [Priority.MEDIUM, Priority.HIGH]


# ============================================================================
# Optimization Executor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_executor_dry_run():
    """Test that executor dry run mode simulates execution"""
    executor = OptimizationExecutor(dry_run=True)

    engine = CampaignOptimizationEngine(target_roas=2.0)
    metrics = PerformanceMetrics(
        campaign_id="campaign_1",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=300.0,
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=3.0
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0
    )

    assert len(recommendations) > 0
    recommendation = recommendations[0]

    result = await executor.execute_optimization(recommendation)

    assert result["success"] == True
    assert result["status"] == "simulated"
    assert "[DRY RUN]" in result["message"]


@pytest.mark.asyncio
async def test_executor_requires_approval():
    """Test that executor requires approval for non-auto-execute recommendations"""
    executor = OptimizationExecutor(dry_run=False, require_approval=True)

    engine = CampaignOptimizationEngine(target_roas=2.0)
    metrics = PerformanceMetrics(
        campaign_id="campaign_1",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=10,  # Low conversions = low confidence
        spend=100.0,
        revenue=150.0,
        ctr=0.05,
        cpc=0.20,
        cpa=10.0,
        roas=1.5
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0
    )

    # Find a recommendation with auto_execute=False (low confidence)
    non_auto_rec = next((r for r in recommendations if not r.auto_execute), None)

    if non_auto_rec:
        result = await executor.execute_optimization(non_auto_rec)

        assert result["success"] == False
        assert result["status"] == "approval_required"


@pytest.mark.asyncio
async def test_executor_execution_history():
    """Test that executor tracks execution history"""
    executor = OptimizationExecutor(dry_run=True)

    engine = CampaignOptimizationEngine(target_roas=2.0)
    metrics = PerformanceMetrics(
        campaign_id="campaign_1",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=300.0,
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=3.0
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0
    )

    # Execute multiple recommendations
    for rec in recommendations[:2]:
        await executor.execute_optimization(rec)

    history = executor.get_execution_history()

    assert len(history) >= 2
    assert "timestamp" in history[0]
    assert "recommendation" in history[0]
    assert "result" in history[0]


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_complete_optimization_workflow():
    """Test complete optimization workflow from analysis to execution"""
    # Step 1: Analyze performance
    engine = CampaignOptimizationEngine(target_roas=2.0)

    metrics = PerformanceMetrics(
        campaign_id="campaign_1",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=50,
        spend=100.0,
        revenue=400.0,  # High ROAS
        ctr=0.05,
        cpc=0.20,
        cpa=2.0,
        roas=4.0
    )

    recommendations = await engine.analyze_campaign_performance(
        metrics=metrics,
        total_budget=200.0,
        avg_order_value=80.0,
        bid_context={"ad_set_id": "adset_1", "device_type": "desktop"}
    )

    assert len(recommendations) > 0

    # Step 2: Execute in dry run mode
    executor = OptimizationExecutor(dry_run=True, require_approval=False)

    for rec in recommendations:
        result = await executor.execute_optimization(rec)
        assert result["success"] == True

    # Step 3: Check history
    history = executor.get_execution_history()
    assert len(history) == len(recommendations)


def test_optimization_score_calculation():
    """Test optimization score calculation"""
    engine = CampaignOptimizationEngine(target_roas=2.0)

    # High performer
    high_metrics = PerformanceMetrics(
        campaign_id="high_performer",
        platform="meta",
        impressions=10000,
        clicks=500,
        conversions=60,
        spend=100.0,
        revenue=400.0,
        ctr=0.05,
        cpc=0.20,
        cpa=1.67,
        roas=4.0
    )

    # Low performer
    low_metrics = PerformanceMetrics(
        campaign_id="low_performer",
        platform="meta",
        impressions=10000,
        clicks=100,
        conversions=5,
        spend=100.0,
        revenue=80.0,
        ctr=0.01,
        cpc=1.0,
        cpa=20.0,
        roas=0.8
    )

    high_score = engine.calculate_optimization_score(high_metrics)
    low_score = engine.calculate_optimization_score(low_metrics)

    assert high_score > low_score
    assert high_score >= 70  # High performers should score high
    assert low_score <= 50   # Low performers should score low
