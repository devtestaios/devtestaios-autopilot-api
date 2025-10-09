"""
Markov Chain Attribution Model
Uses probabilistic transitions to calculate channel credit

Based on Markov chain theory - models customer journeys as state transitions
Answers: "What is the probability of conversion given this path?"
"""
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import logging

from app.attribution.models import (
    AttributionModel,
    AttributionResult,
    AttributionModelType
)
from app.attribution.event_schema import CustomerJourney, Platform

logger = logging.getLogger(__name__)


class MarkovChainAttributionModel(AttributionModel):
    """
    Markov chain attribution model

    Core Concept:
    - Customer journey is a Markov chain (sequence of state transitions)
    - Each touchpoint (platform/campaign) is a state
    - Calculate probability of reaching "conversion" state via each path
    - Credit = "removal effect" (how much conversion drops if we remove this channel)

    Algorithm:
    1. Build transition probability matrix from historical journeys
    2. For each channel, calculate P(conversion | include channel)
    3. Calculate P(conversion | remove channel)
    4. Credit = P(with) - P(without) / Σ all removal effects

    Advantages:
    - Data-driven (learns from actual journey patterns)
    - Captures sequence effects (order matters)
    - Handles multi-touch naturally

    Limitations:
    - Requires large dataset (many journeys)
    - Assumes Markov property (current state only depends on previous state)
    - Can be unstable with rare paths
    """

    model_type = AttributionModelType.MARKOV

    def __init__(self, min_support: int = 5):
        """
        Initialize Markov attribution model

        Args:
            min_support: Minimum number of journeys needed to trust a transition
        """
        self.min_support = min_support

        # Transition probabilities: (from_state, to_state) -> probability
        self.transitions: Dict[Tuple[str, str], float] = {}

        # Transition counts (for learning)
        self.transition_counts: Dict[Tuple[str, str], int] = defaultdict(int)

        # State counts
        self.state_counts: Dict[str, int] = defaultdict(int)

        # Conversion probability from each state
        self.conversion_probs: Dict[str, float] = {}

        self.is_trained = False

    def train(self, journeys: List[CustomerJourney]):
        """
        Train Markov model on historical journeys

        Learns:
        - Transition probabilities between channels
        - Conversion probabilities from each channel
        """
        logger.info(f"Training Markov model on {len(journeys)} journeys")

        # Reset counts
        self.transition_counts = defaultdict(int)
        self.state_counts = defaultdict(int)
        conversion_counts = defaultdict(int)

        for journey in journeys:
            # Extract state sequence (platform names)
            states = [t.platform.value for t in journey.touchpoints]

            # Add START state
            states = ["START"] + states

            # Add CONVERSION or NULL end state
            if journey.converted:
                states.append("CONVERSION")
            else:
                states.append("NULL")

            # Count transitions
            for i in range(len(states) - 1):
                from_state = states[i]
                to_state = states[i + 1]

                self.transition_counts[(from_state, to_state)] += 1
                self.state_counts[from_state] += 1

                # Track conversions from each state
                if to_state == "CONVERSION":
                    conversion_counts[from_state] += 1

        # Calculate transition probabilities
        for (from_state, to_state), count in self.transition_counts.items():
            if self.state_counts[from_state] > 0:
                self.transitions[(from_state, to_state)] = (
                    count / self.state_counts[from_state]
                )

        # Calculate conversion probabilities from each state
        for state, total_count in self.state_counts.items():
            if total_count >= self.min_support:
                conv_count = conversion_counts.get(state, 0)
                self.conversion_probs[state] = conv_count / total_count
            else:
                # Not enough data - use overall average
                total_conv = sum(conversion_counts.values())
                total_all = sum(self.state_counts.values())
                self.conversion_probs[state] = total_conv / total_all if total_all > 0 else 0

        self.is_trained = True
        logger.info(
            f"Trained on {len(self.transitions)} transitions, "
            f"{len(self.state_counts)} states"
        )

    def calculate_attribution(self, journey: CustomerJourney) -> AttributionResult:
        """
        Calculate Markov attribution for a journey

        Uses "removal effect" method:
        Credit(channel) = (Conversion prob with channel - Conversion prob without) / Total removal effect
        """
        if not journey.converted or not journey.conversion:
            return self._create_null_result(journey)

        if not self.is_trained:
            logger.warning(
                "Markov model not trained - falling back to linear attribution"
            )
            return self._fallback_linear(journey)

        # Get unique platforms in journey
        platforms = list(set(t.platform for t in journey.touchpoints))

        # Calculate removal effect for each platform
        removal_effects = {}
        baseline_conversion_prob = self._calculate_conversion_probability(
            journey, remove_platform=None
        )

        for platform in platforms:
            # Probability if we remove this platform
            prob_without = self._calculate_conversion_probability(
                journey, remove_platform=platform
            )

            # Removal effect = baseline - without
            removal_effect = baseline_conversion_prob - prob_without
            removal_effects[platform] = max(removal_effect, 0)  # Can't be negative

        # Total removal effect
        total_removal = sum(removal_effects.values())

        # Calculate credits (normalize removal effects)
        if total_removal > 0:
            touchpoint_credits = {}
            for idx, touchpoint in enumerate(journey.touchpoints):
                credit = removal_effects[touchpoint.platform] / total_removal
                touchpoint_credits[idx] = credit
        else:
            # Equal distribution if no clear signal
            touchpoint_credits = {
                idx: 1.0 / len(journey.touchpoints)
                for idx in range(len(journey.touchpoints))
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
            journey, removal_effects, platform_attribution
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
            total_touchpoints=len(journey.touchpoints),
            unique_platforms=journey.unique_platforms,
            days_to_convert=journey.days_to_convert,
            confidence_score=self._calculate_confidence(journey),
            insights=insights
        )

    def _calculate_conversion_probability(
        self,
        journey: CustomerJourney,
        remove_platform: Optional[Platform] = None
    ) -> float:
        """
        Calculate probability of conversion for this journey

        If remove_platform is specified, calculate probability
        without that platform's touchpoints
        """
        # Filter touchpoints
        if remove_platform:
            touchpoints = [
                t for t in journey.touchpoints
                if t.platform != remove_platform
            ]
        else:
            touchpoints = journey.touchpoints

        if not touchpoints:
            return 0.0

        # Build state sequence
        states = ["START"] + [t.platform.value for t in touchpoints]

        # Calculate probability of this path
        probability = 1.0
        for i in range(len(states) - 1):
            from_state = states[i]
            to_state = states[i + 1]

            # Get transition probability
            transition_prob = self.transitions.get((from_state, to_state), 0.1)
            probability *= transition_prob

        # Multiply by conversion probability from last state
        last_state = states[-1]
        conv_prob = self.conversion_probs.get(last_state, 0.1)
        probability *= conv_prob

        return probability

    def _fallback_linear(self, journey: CustomerJourney) -> AttributionResult:
        """Fallback to linear attribution when model not trained"""
        n = len(journey.touchpoints)
        equal_credit = 1.0 / n if n > 0 else 0

        touchpoint_credits = {idx: equal_credit for idx in range(n)}

        platform_attribution = self._generate_platform_attribution(
            journey, touchpoint_credits
        )
        campaign_attribution = self._generate_campaign_attribution(
            journey, touchpoint_credits
        )

        return AttributionResult(
            journey_id=journey.journey_id,
            user_id=journey.user_id,
            model_type=AttributionModelType.LINEAR,
            model_version=self.model_version,
            platform_attribution=platform_attribution,
            campaign_attribution=campaign_attribution,
            converted=journey.converted,
            conversion_value=journey.conversion.revenue if journey.conversion else 0,
            conversion_date=journey.conversion.timestamp if journey.conversion else None,
            total_touchpoints=n,
            unique_platforms=journey.unique_platforms,
            days_to_convert=journey.days_to_convert,
            confidence_score=0.5,
            insights=["Using linear attribution (model not trained)"]
        )

    def _create_null_result(self, journey: CustomerJourney) -> AttributionResult:
        """Create result for non-converting journey"""
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
        removal_effects: Dict[Platform, float],
        platform_attribution: List
    ) -> List[str]:
        """Generate human-readable insights"""
        insights = []

        # Identify most critical platform
        if removal_effects:
            max_removal = max(removal_effects.values())
            critical_platforms = [
                p for p, effect in removal_effects.items()
                if effect == max_removal
            ]

            if critical_platforms:
                platform_name = critical_platforms[0].value.title()
                insights.append(
                    f"{platform_name} was most critical - conversion probability "
                    f"drops {max_removal*100:.1f}% without it"
                )

        # Multi-channel synergy
        if len(removal_effects) > 1:
            total_individual = sum(removal_effects.values())
            if total_individual > 1.0:
                insights.append(
                    f"Strong channel synergy detected - channels work better together"
                )

        # Sequence insight
        if len(journey.touchpoints) >= 3:
            first_platform = journey.touchpoints[0].platform.value
            last_platform = journey.touchpoints[-1].platform.value

            if first_platform != last_platform:
                insights.append(
                    f"Successful cross-channel path: {first_platform} → ... → {last_platform}"
                )

        return insights

    def get_top_paths(self, n: int = 10) -> List[Tuple[List[str], float]]:
        """
        Get top N most common conversion paths

        Returns:
            List of (path, conversion_probability) tuples
        """
        if not self.is_trained:
            return []

        # This would require tracking complete paths during training
        # Simplified version: return top individual transitions to conversion

        conversion_transitions = [
            ((from_state, to_state), prob)
            for (from_state, to_state), prob in self.transitions.items()
            if to_state == "CONVERSION"
        ]

        # Sort by probability
        conversion_transitions.sort(key=lambda x: x[1], reverse=True)

        return [
            ([from_state], prob)
            for (from_state, _), prob in conversion_transitions[:n]
        ]
