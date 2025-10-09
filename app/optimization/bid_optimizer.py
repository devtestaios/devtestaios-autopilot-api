"""
Bid Optimization Engine
Real-time bid adjustment based on conversion probability and target ROAS

Approach:
- Predict conversion probability for each auction
- Calculate optimal bid = value * probability / target_roas
- Adjust bids dynamically based on performance signals
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class BidContext:
    """Context for bid decision"""
    campaign_id: str
    ad_set_id: str
    platform: str

    # Targeting context
    device_type: Optional[str] = None
    placement: Optional[str] = None
    audience_segment: Optional[str] = None
    hour_of_day: Optional[int] = None
    day_of_week: Optional[int] = None

    # Historical performance
    historical_cvr: float = 0.0  # Conversion rate
    historical_cpa: float = 0.0  # Cost per acquisition
    historical_roas: float = 0.0  # Return on ad spend


@dataclass
class BidRecommendation:
    """Bid optimization recommendation"""
    campaign_id: str
    ad_set_id: str
    platform: str

    current_bid: float
    recommended_bid: float
    bid_change: float
    bid_change_pct: float

    expected_cvr: float
    expected_cpa: float
    expected_roas: float

    confidence: float
    reasoning: str


@dataclass
class PerformanceSnapshot:
    """Recent performance snapshot for bid adjustment"""
    campaign_id: str
    platform: str

    # Performance over last hour/day
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float

    # Derived metrics
    ctr: float
    cvr: float
    cpa: float
    roas: float

    # Time range
    start_time: datetime
    end_time: datetime


class BidOptimizer:
    """
    Real-time bid optimizer using conversion probability models

    Core strategy:
    - Optimal bid = (avg_order_value * conversion_rate) / target_roas
    - Adjust based on time-of-day, device, placement performance
    - Use recent performance signals to adjust quickly
    """

    def __init__(
        self,
        target_roas: float = 2.0,
        min_bid: float = 0.50,
        max_bid: float = 50.0,
        max_bid_change_pct: float = 0.20,  # Max 20% change at once
        learning_rate: float = 0.1
    ):
        """
        Initialize bid optimizer

        Args:
            target_roas: Target return on ad spend
            min_bid: Minimum bid allowed
            max_bid: Maximum bid allowed
            max_bid_change_pct: Maximum percentage change per adjustment
            learning_rate: How quickly to respond to performance changes
        """
        self.target_roas = target_roas
        self.min_bid = min_bid
        self.max_bid = max_bid
        self.max_bid_change_pct = max_bid_change_pct
        self.learning_rate = learning_rate

    def optimize_bid(
        self,
        context: BidContext,
        current_bid: float,
        avg_order_value: float,
        recent_performance: Optional[PerformanceSnapshot] = None
    ) -> BidRecommendation:
        """
        Calculate optimal bid for given context

        Args:
            context: Bid context (device, placement, time, etc.)
            current_bid: Current bid amount
            avg_order_value: Average order value (revenue per conversion)
            recent_performance: Recent performance data for quick adjustment

        Returns:
            Bid recommendation with expected impact
        """
        # Step 1: Estimate conversion rate
        estimated_cvr = self._estimate_conversion_rate(context, recent_performance)

        # Step 2: Calculate optimal bid
        # Formula: bid = (value * cvr) / target_roas
        optimal_bid = (avg_order_value * estimated_cvr) / self.target_roas

        # Step 3: Apply performance-based adjustment
        if recent_performance:
            performance_multiplier = self._calculate_performance_multiplier(
                recent_performance,
                context
            )
            optimal_bid *= performance_multiplier

        # Step 4: Apply constraints
        # Limit change magnitude
        max_increase = current_bid * (1 + self.max_bid_change_pct)
        max_decrease = current_bid * (1 - self.max_bid_change_pct)

        recommended_bid = max(
            self.min_bid,
            min(
                self.max_bid,
                max(max_decrease, min(max_increase, optimal_bid))
            )
        )

        # Step 5: Calculate expected metrics
        expected_cpa = recommended_bid / estimated_cvr if estimated_cvr > 0 else 0
        expected_roas = avg_order_value / expected_cpa if expected_cpa > 0 else 0

        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(context, recent_performance)

        # Step 7: Generate reasoning
        reasoning = self._generate_reasoning(
            current_bid,
            recommended_bid,
            estimated_cvr,
            expected_roas,
            context
        )

        return BidRecommendation(
            campaign_id=context.campaign_id,
            ad_set_id=context.ad_set_id,
            platform=context.platform,
            current_bid=current_bid,
            recommended_bid=recommended_bid,
            bid_change=recommended_bid - current_bid,
            bid_change_pct=(recommended_bid - current_bid) / current_bid if current_bid > 0 else 0,
            expected_cvr=estimated_cvr,
            expected_cpa=expected_cpa,
            expected_roas=expected_roas,
            confidence=confidence,
            reasoning=reasoning
        )

    def optimize_campaign_bids(
        self,
        contexts: List[BidContext],
        current_bids: Dict[str, float],
        avg_order_value: float,
        performance_data: Optional[Dict[str, PerformanceSnapshot]] = None
    ) -> List[BidRecommendation]:
        """
        Optimize bids for multiple ad sets in a campaign

        Args:
            contexts: List of bid contexts for each ad set
            current_bids: {ad_set_id: current_bid}
            avg_order_value: Average order value
            performance_data: {ad_set_id: PerformanceSnapshot}

        Returns:
            List of bid recommendations
        """
        recommendations = []

        for context in contexts:
            current_bid = current_bids.get(context.ad_set_id, 1.0)
            recent_performance = performance_data.get(context.ad_set_id) if performance_data else None

            recommendation = self.optimize_bid(
                context=context,
                current_bid=current_bid,
                avg_order_value=avg_order_value,
                recent_performance=recent_performance
            )

            recommendations.append(recommendation)

        return recommendations

    def _estimate_conversion_rate(
        self,
        context: BidContext,
        recent_performance: Optional[PerformanceSnapshot]
    ) -> float:
        """
        Estimate conversion rate based on context and recent performance

        Uses:
        1. Historical CVR from context
        2. Recent performance data (last hour/day)
        3. Contextual modifiers (time, device, placement)
        """
        # Start with historical CVR
        base_cvr = context.historical_cvr

        if base_cvr == 0:
            # No historical data, use conservative estimate
            base_cvr = 0.01  # 1% conversion rate

        # Apply recent performance adjustment
        if recent_performance and recent_performance.clicks > 0:
            recent_cvr = recent_performance.cvr

            # Weight recent vs historical (more recent data = higher weight)
            if recent_performance.clicks >= 100:
                # Strong signal from recent data
                weight_recent = 0.7
            elif recent_performance.clicks >= 20:
                # Moderate signal
                weight_recent = 0.4
            else:
                # Weak signal
                weight_recent = 0.2

            base_cvr = (weight_recent * recent_cvr) + ((1 - weight_recent) * base_cvr)

        # Apply contextual modifiers
        multiplier = 1.0

        # Time-of-day adjustment
        if context.hour_of_day is not None:
            # Peak hours (9am-9pm) typically perform better
            if 9 <= context.hour_of_day <= 21:
                multiplier *= 1.1
            else:
                multiplier *= 0.9

        # Device type adjustment
        if context.device_type:
            if context.device_type == "desktop":
                multiplier *= 1.15  # Desktop typically converts better
            elif context.device_type == "mobile":
                multiplier *= 0.95

        # Placement adjustment
        if context.placement:
            if "feed" in context.placement.lower():
                multiplier *= 1.1  # Feed placements often perform better
            elif "story" in context.placement.lower() or "stories" in context.placement.lower():
                multiplier *= 0.85  # Stories typically lower CVR

        estimated_cvr = base_cvr * multiplier

        # Ensure reasonable bounds
        return max(0.001, min(0.5, estimated_cvr))

    def _calculate_performance_multiplier(
        self,
        recent_performance: PerformanceSnapshot,
        context: BidContext
    ) -> float:
        """
        Calculate bid multiplier based on recent performance

        If performing above target → increase bids (scale up)
        If performing below target → decrease bids (scale down)
        """
        if recent_performance.spend == 0:
            return 1.0

        current_roas = recent_performance.roas

        # Calculate how far we are from target
        roas_ratio = current_roas / self.target_roas

        # Apply learning rate to smooth adjustments
        if roas_ratio > 1.0:
            # Performing above target → increase bids
            # If ROAS is 2x target, we can afford higher bids
            adjustment = 1.0 + (self.learning_rate * (roas_ratio - 1.0))
        else:
            # Performing below target → decrease bids
            adjustment = 1.0 - (self.learning_rate * (1.0 - roas_ratio))

        # Cap adjustment to prevent extreme swings
        return max(0.7, min(1.3, adjustment))

    def _calculate_confidence(
        self,
        context: BidContext,
        recent_performance: Optional[PerformanceSnapshot]
    ) -> float:
        """
        Calculate confidence in bid recommendation

        Higher confidence when:
        - More historical data
        - Recent performance is consistent with historical
        - Strong performance signals
        """
        confidence = 0.5  # Base confidence

        # Historical data confidence
        if context.historical_cvr > 0:
            confidence += 0.2

        if context.historical_roas > self.target_roas:
            confidence += 0.1

        # Recent performance confidence
        if recent_performance:
            if recent_performance.conversions >= 10:
                confidence += 0.15
            elif recent_performance.conversions >= 3:
                confidence += 0.1

            if recent_performance.clicks >= 100:
                confidence += 0.05

        return min(confidence, 1.0)

    def _generate_reasoning(
        self,
        current_bid: float,
        recommended_bid: float,
        estimated_cvr: float,
        expected_roas: float,
        context: BidContext
    ) -> str:
        """Generate human-readable reasoning for bid recommendation"""
        change = recommended_bid - current_bid
        change_pct = (change / current_bid * 100) if current_bid > 0 else 0

        if abs(change_pct) < 5:
            return f"Bid is optimal. Expected CVR: {estimated_cvr:.2%}, ROAS: {expected_roas:.2f}x"

        direction = "increase" if change > 0 else "decrease"

        reasoning_parts = [
            f"Recommend {abs(change_pct):.1f}% {direction} in bid"
        ]

        if change > 0:
            reasoning_parts.append(f"Expected ROAS ({expected_roas:.2f}x) is above target")
            reasoning_parts.append("Room to scale by increasing bids")
        else:
            reasoning_parts.append(f"Expected ROAS ({expected_roas:.2f}x) is below target")
            reasoning_parts.append("Improve efficiency by lowering bids")

        # Add contextual factors
        if context.device_type:
            reasoning_parts.append(f"Optimized for {context.device_type}")

        if context.hour_of_day is not None:
            reasoning_parts.append(f"Time-of-day: {context.hour_of_day}:00")

        return ". ".join(reasoning_parts) + "."


class DynamicBidAdjustment:
    """
    Apply dynamic bid adjustments based on performance signals
    Used for quick reactions to performance changes
    """

    def __init__(
        self,
        check_interval_minutes: int = 60,
        performance_threshold_multiplier: float = 1.5
    ):
        """
        Initialize dynamic bid adjustment

        Args:
            check_interval_minutes: How often to check performance
            performance_threshold_multiplier: Trigger adjustment when performance
                                            deviates by this multiplier
        """
        self.check_interval = timedelta(minutes=check_interval_minutes)
        self.threshold = performance_threshold_multiplier

    def should_adjust(
        self,
        recent_performance: PerformanceSnapshot,
        target_roas: float
    ) -> Tuple[bool, str]:
        """
        Determine if bids should be adjusted based on recent performance

        Returns:
            (should_adjust, reason)
        """
        # Check if we have enough data
        if recent_performance.conversions < 3:
            return False, "Insufficient conversion data"

        current_roas = recent_performance.roas

        # Check for significant deviation
        if current_roas > target_roas * self.threshold:
            return True, f"ROAS ({current_roas:.2f}x) significantly above target ({target_roas:.2f}x) - scale up"

        if current_roas < target_roas / self.threshold:
            return True, f"ROAS ({current_roas:.2f}x) significantly below target ({target_roas:.2f}x) - scale down"

        return False, "Performance within acceptable range"

    def calculate_emergency_adjustment(
        self,
        recent_performance: PerformanceSnapshot,
        target_roas: float
    ) -> float:
        """
        Calculate emergency bid adjustment multiplier

        Returns:
            Multiplier to apply to current bids (0.5 to 1.5)
        """
        if recent_performance.spend == 0:
            return 1.0

        current_roas = recent_performance.roas
        roas_ratio = current_roas / target_roas

        # More aggressive adjustments for emergency situations
        if roas_ratio > self.threshold:
            # Performing great → increase bids by up to 50%
            return min(1.5, 1.0 + (0.5 * (roas_ratio - 1.0)))
        elif roas_ratio < 1 / self.threshold:
            # Performing poorly → decrease bids by up to 50%
            return max(0.5, roas_ratio)

        return 1.0
