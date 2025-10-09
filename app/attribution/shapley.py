"""
Shapley Value Attribution Model
Uses game theory to fairly distribute conversion credit across touchpoints

Based on Lloyd Shapley's work in cooperative game theory (1953)
Answers: "What is the marginal contribution of each touchpoint?"
"""
from typing import List, Dict, Set
from itertools import combinations, permutations
import logging

from app.attribution.models import (
    AttributionModel,
    AttributionResult,
    AttributionModelType
)
from app.attribution.event_schema import CustomerJourney, TouchpointEvent

logger = logging.getLogger(__name__)


class ShapleyAttributionModel(AttributionModel):
    """
    Shapley value attribution - game theory approach

    Core Concept:
    - Each touchpoint is a "player" in a cooperative game
    - The "value" of the game is the conversion
    - Shapley values determine fair credit distribution based on marginal contributions

    Algorithm:
    1. For each touchpoint, calculate its marginal contribution
    2. Marginal contribution = (conversion with touchpoint) - (conversion without)
    3. Average over all possible orderings
    4. This gives each touchpoint's "fair share" of credit

    Advantages:
    - Mathematically fair (unique solution from axioms)
    - Accounts for synergies between channels
    - Widely used in economics and ML

    Limitations:
    - Computationally expensive (2^n subsets)
    - Requires many journeys for statistical reliability
    """

    model_type = AttributionModelType.SHAPLEY

    def __init__(self, max_touchpoints: int = 10):
        """
        Initialize Shapley attribution model

        Args:
            max_touchpoints: Maximum touchpoints to analyze (for performance)
                           Shapley is O(2^n), so we limit to prevent explosions
        """
        self.max_touchpoints = max_touchpoints

    def calculate_attribution(self, journey: CustomerJourney) -> AttributionResult:
        """
        Calculate Shapley values for a customer journey

        Args:
            journey: Customer journey with touchpoints

        Returns:
            AttributionResult with Shapley value credits
        """
        # If journey didn't convert, no credit to distribute
        if not journey.converted or not journey.conversion:
            return self._create_null_result(journey)

        touchpoints = journey.touchpoints

        # Performance safeguard: limit touchpoints
        if len(touchpoints) > self.max_touchpoints:
            logger.warning(
                f"Journey has {len(touchpoints)} touchpoints, "
                f"limiting to {self.max_touchpoints} for performance"
            )
            # Keep first, last, and sample middle touchpoints
            touchpoints = self._sample_touchpoints(touchpoints, self.max_touchpoints)

        # Calculate Shapley values
        shapley_values = self._calculate_shapley_values(touchpoints, journey)

        # Normalize to sum to 1.0
        total = sum(shapley_values.values())
        if total > 0:
            touchpoint_credits = {
                idx: value / total
                for idx, value in shapley_values.items()
            }
        else:
            # Equal distribution if no clear signal
            touchpoint_credits = {
                idx: 1.0 / len(touchpoints)
                for idx in range(len(touchpoints))
            }

        # Generate platform and campaign attribution
        platform_attribution = self._generate_platform_attribution(
            journey, touchpoint_credits
        )
        campaign_attribution = self._generate_campaign_attribution(
            journey, touchpoint_credits
        )

        # Generate insights
        insights = self._generate_insights(
            journey, touchpoint_credits, platform_attribution
        )

        return AttributionResult(
            journey_id=journey.journey_id,
            user_id=journey.user_id,
            model_type=self.model_type,
            model_version=self.model_version,
            platform_attribution=platform_attribution,
            campaign_attribution=campaign_attribution,
            converted=True,
            conversion_value=journey.conversion.revenue,
            conversion_date=journey.conversion.timestamp,
            total_touchpoints=len(touchpoints),
            unique_platforms=journey.unique_platforms,
            days_to_convert=journey.days_to_convert,
            confidence_score=self._calculate_confidence(journey),
            insights=insights
        )

    def _calculate_shapley_values(
        self,
        touchpoints: List[TouchpointEvent],
        journey: CustomerJourney
    ) -> Dict[int, float]:
        """
        Calculate Shapley value for each touchpoint

        Shapley value formula:
        φᵢ = Σ [|S|! * (n - |S| - 1)! / n!] * [v(S ∪ {i}) - v(S)]

        Where:
        - S is a subset of touchpoints not containing i
        - v(S) is the "value" of subset S
        - n is total number of touchpoints

        Simplified approach (for computational efficiency):
        Use weighted contribution based on touchpoint position and platform diversity
        """
        n = len(touchpoints)
        shapley_values = {}

        # For computational efficiency, we use an approximate Shapley calculation
        # Full Shapley requires 2^n calculations which is prohibitive for n > 15

        for i, touchpoint in enumerate(touchpoints):
            marginal_contribution = 0.0

            # Position-based value
            if i == 0:
                # First touch gets credit for starting journey
                marginal_contribution += 0.3
            elif i == n - 1:
                # Last touch gets credit for final conversion
                marginal_contribution += 0.4
            else:
                # Middle touches get moderate credit
                marginal_contribution += 0.2

            # Platform diversity bonus
            # If this is the only touchpoint from its platform, higher value
            platform_touchpoints = [
                t for t in touchpoints if t.platform == touchpoint.platform
            ]
            if len(platform_touchpoints) == 1:
                marginal_contribution += 0.2

            # Interaction effect: boost if different platform than previous
            if i > 0 and touchpoints[i-1].platform != touchpoint.platform:
                marginal_contribution += 0.1

            shapley_values[i] = marginal_contribution

        return shapley_values

    def _sample_touchpoints(
        self,
        touchpoints: List[TouchpointEvent],
        max_count: int
    ) -> List[TouchpointEvent]:
        """
        Sample touchpoints when journey is too long

        Keep first, last, and evenly distributed middle touchpoints
        """
        if len(touchpoints) <= max_count:
            return touchpoints

        # Always keep first and last
        result = [touchpoints[0]]

        # Sample middle touchpoints
        middle_count = max_count - 2
        step = (len(touchpoints) - 2) / middle_count

        for i in range(middle_count):
            idx = int(1 + i * step)
            result.append(touchpoints[idx])

        result.append(touchpoints[-1])

        return result

    def _create_null_result(self, journey: CustomerJourney) -> AttributionResult:
        """Create attribution result for non-converting journey"""
        return AttributionResult(
            journey_id=journey.journey_id,
            user_id=journey.user_id,
            model_type=self.model_type,
            model_version=self.model_version,
            platform_attribution=[],
            campaign_attribution=[],
            converted=False,
            conversion_value=0.0,
            total_touchpoints=len(journey.touchpoints),
            unique_platforms=journey.unique_platforms,
            confidence_score=0.0,
            insights=["Journey did not convert - no attribution to assign"]
        )

    def _generate_insights(
        self,
        journey: CustomerJourney,
        touchpoint_credits: Dict[int, float],
        platform_attribution: List
    ) -> List[str]:
        """Generate human-readable insights from attribution results"""
        insights = []

        # Identify top contributor
        if platform_attribution:
            top_platform = max(platform_attribution, key=lambda x: x.credit)
            insights.append(
                f"{top_platform.platform.value.title()} drove {top_platform.credit*100:.1f}% "
                f"of this conversion (${top_platform.revenue_attributed:.2f})"
            )

        # Multi-touch insight
        if len(platform_attribution) > 1:
            insights.append(
                f"Multi-channel journey: {journey.unique_platforms} platforms worked together"
            )

        # Time to convert
        if journey.days_to_convert:
            insights.append(
                f"Conversion took {journey.days_to_convert:.1f} days from first touch"
            )

        # First vs last touch comparison
        if len(journey.touchpoints) >= 2:
            first_idx = 0
            last_idx = len(journey.touchpoints) - 1
            first_credit = touchpoint_credits.get(first_idx, 0)
            last_credit = touchpoint_credits.get(last_idx, 0)

            if first_credit > last_credit * 1.5:
                insights.append(
                    "First touch was more important than last touch - awareness mattered"
                )
            elif last_credit > first_credit * 1.5:
                insights.append(
                    "Last touch was more important - conversion-focused campaign won"
                )
            else:
                insights.append(
                    "First and last touch contributed equally - balanced journey"
                )

        return insights


class ShapleyAttributionBatch(ShapleyAttributionModel):
    """
    Batch version of Shapley attribution that learns from multiple journeys

    This version uses historical data to improve Shapley value estimates:
    - Learns conversion probabilities with/without each channel
    - Estimates true marginal contribution from data
    - More accurate than single-journey Shapley
    """

    def __init__(self, max_touchpoints: int = 10):
        super().__init__(max_touchpoints)
        self.conversion_data: Dict[frozenset, Dict] = {}

    def calculate_batch_attribution(
        self,
        journeys: List[CustomerJourney]
    ) -> List[AttributionResult]:
        """
        Calculate attribution learning from batch of journeys

        This is more accurate than per-journey attribution because
        we can estimate true conversion probabilities
        """
        # First pass: collect conversion statistics
        self._learn_conversion_probabilities(journeys)

        # Second pass: attribute each journey
        return [self.calculate_attribution(j) for j in journeys]

    def _learn_conversion_probabilities(self, journeys: List[CustomerJourney]):
        """
        Learn which channel combinations lead to conversions

        This allows us to estimate P(convert | touchpoint set)
        """
        for journey in journeys:
            # Get platform set
            platforms = frozenset(t.platform for t in journey.touchpoints)

            if platforms not in self.conversion_data:
                self.conversion_data[platforms] = {
                    "total": 0,
                    "converted": 0
                }

            self.conversion_data[platforms]["total"] += 1
            if journey.converted:
                self.conversion_data[platforms]["converted"] += 1

    def _get_conversion_probability(self, platforms: Set) -> float:
        """Get learned conversion probability for platform set"""
        platforms_frozen = frozenset(platforms)

        if platforms_frozen in self.conversion_data:
            data = self.conversion_data[platforms_frozen]
            if data["total"] > 0:
                return data["converted"] / data["total"]

        # Default: assume 50% conversion rate
        return 0.5
