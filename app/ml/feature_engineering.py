"""
Feature Engineering Pipeline for Budget Optimization ML Model
Transforms raw campaign data into ML-ready features
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from app.ml.meta_data_collector import CampaignPerformanceData

logger = logging.getLogger(__name__)


@dataclass
class FeatureSet:
    """Structured feature set for ML model"""
    # Raw features
    daily_spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float

    # Calculated rate features
    ctr: float
    cpc: float
    cpa: float
    roas: float
    conversion_rate: float

    # Trend features (7-day moving averages)
    spend_trend_7d: float
    roas_trend_7d: float
    conversion_trend_7d: float

    # Time-based features
    day_of_week: int  # 0=Monday, 6=Sunday
    is_weekend: bool
    week_of_month: int
    day_of_month: int

    # Performance indicators
    spend_efficiency: float  # Revenue per dollar spent
    engagement_rate: float  # Clicks per impression
    value_per_conversion: float

    # Target variable (what we're predicting)
    optimal_next_day_budget: float


class FeatureEngineer:
    """Engineers ML features from raw campaign performance data"""

    def __init__(self):
        self.min_data_points = 14  # Minimum days needed for reliable features

    def engineer_features(
        self,
        performance_data: List[CampaignPerformanceData],
        predict_days_ahead: int = 1
    ) -> pd.DataFrame:
        """
        Convert raw performance data into ML-ready feature matrix

        Args:
            performance_data: List of daily performance data points
            predict_days_ahead: How many days ahead to predict budget for

        Returns:
            DataFrame with engineered features and target variable
        """
        if len(performance_data) < self.min_data_points:
            logger.warning(f"Insufficient data: {len(performance_data)} days (need {self.min_data_points})")
            return pd.DataFrame()

        # Sort by date
        sorted_data = sorted(performance_data, key=lambda x: x.date)

        features = []

        # Generate features for each day (except the last predict_days_ahead days)
        for i in range(len(sorted_data) - predict_days_ahead):
            current_day = sorted_data[i]
            target_day = sorted_data[i + predict_days_ahead]

            # Calculate trend features (7-day moving averages)
            window_start = max(0, i - 6)
            window_data = sorted_data[window_start:i + 1]

            spend_trend = np.mean([d.spend for d in window_data])
            roas_trend = np.mean([d.roas for d in window_data])
            conversion_trend = np.mean([d.conversions for d in window_data])

            # Calculate derived metrics
            engagement_rate = current_day.clicks / current_day.impressions if current_day.impressions > 0 else 0
            spend_efficiency = current_day.revenue / current_day.spend if current_day.spend > 0 else 0
            value_per_conversion = current_day.revenue / current_day.conversions if current_day.conversions > 0 else 0

            # Time-based features
            day_of_week = current_day.date.weekday()
            is_weekend = day_of_week in [5, 6]
            week_of_month = (current_day.date.day - 1) // 7 + 1
            day_of_month = current_day.date.day

            feature_row = {
                # Raw features
                "daily_spend": current_day.spend,
                "impressions": current_day.impressions,
                "clicks": current_day.clicks,
                "conversions": current_day.conversions,
                "revenue": current_day.revenue,

                # Rate features
                "ctr": current_day.ctr,
                "cpc": current_day.cpc,
                "cpa": current_day.cpa,
                "roas": current_day.roas,
                "conversion_rate": current_day.conversion_rate,

                # Trend features
                "spend_trend_7d": spend_trend,
                "roas_trend_7d": roas_trend,
                "conversion_trend_7d": conversion_trend,

                # Time features
                "day_of_week": day_of_week,
                "is_weekend": 1 if is_weekend else 0,
                "week_of_month": week_of_month,
                "day_of_month": day_of_month,

                # Performance indicators
                "spend_efficiency": spend_efficiency,
                "engagement_rate": engagement_rate,
                "value_per_conversion": value_per_conversion,

                # Target variable (next day's optimal budget based on actual performance)
                "optimal_next_day_budget": self._calculate_optimal_budget(current_day, target_day),

                # Metadata
                "date": current_day.date,
                "campaign_id": current_day.campaign_id
            }

            features.append(feature_row)

        df = pd.DataFrame(features)
        logger.info(f"Engineered {len(df)} feature rows with {len(df.columns)} features")

        return df

    def _calculate_optimal_budget(
        self,
        current_day: CampaignPerformanceData,
        target_day: CampaignPerformanceData
    ) -> float:
        """
        Calculate what the "optimal" budget should have been based on actual performance

        This is our target variable for supervised learning. We look at what actually
        happened and determine what budget would have been ideal.

        Logic:
        - If ROAS > 3.0 and high conversion rate: Increase budget (room to scale)
        - If ROAS 2.0-3.0: Maintain budget (stable performance)
        - If ROAS < 2.0: Decrease budget (inefficient spending)
        - Factor in conversion trends
        """
        current_roas = current_day.roas
        target_roas = target_day.roas
        current_spend = current_day.spend
        target_spend = target_day.spend

        # Base the optimal budget on target day's actual ROAS performance
        if target_roas >= 3.5:
            # Excellent performance - could have spent more
            optimal_multiplier = 1.20  # 20% increase
        elif target_roas >= 2.5:
            # Good performance - moderate increase
            optimal_multiplier = 1.10  # 10% increase
        elif target_roas >= 2.0:
            # Acceptable performance - maintain
            optimal_multiplier = 1.0
        elif target_roas >= 1.5:
            # Below target - decrease
            optimal_multiplier = 0.9  # 10% decrease
        else:
            # Poor performance - significant decrease
            optimal_multiplier = 0.75  # 25% decrease

        # Adjust for conversion rate trends
        if target_day.conversion_rate > current_day.conversion_rate * 1.2:
            # Conversion rate improving - more aggressive scaling
            optimal_multiplier *= 1.1
        elif target_day.conversion_rate < current_day.conversion_rate * 0.8:
            # Conversion rate declining - be conservative
            optimal_multiplier *= 0.9

        optimal_budget = current_spend * optimal_multiplier

        # Safety bounds (don't recommend extreme changes)
        min_budget = current_spend * 0.5  # No more than 50% decrease
        max_budget = current_spend * 2.0  # No more than 100% increase

        return np.clip(optimal_budget, min_budget, max_budget)

    def prepare_training_data(
        self,
        feature_df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare features and target for ML model training

        Args:
            feature_df: DataFrame from engineer_features()

        Returns:
            Tuple of (X, y, feature_names)
            - X: Feature matrix (numpy array)
            - y: Target vector (numpy array)
            - feature_names: List of feature column names
        """
        # Exclude metadata columns and target from features
        exclude_cols = ["optimal_next_day_budget", "date", "campaign_id"]
        feature_cols = [col for col in feature_df.columns if col not in exclude_cols]

        X = feature_df[feature_cols].values
        y = feature_df["optimal_next_day_budget"].values

        logger.info(f"Prepared training data: X shape {X.shape}, y shape {y.shape}")

        return X, y, feature_cols

    def create_prediction_features(
        self,
        recent_performance: List[CampaignPerformanceData],
        prediction_date: datetime
    ) -> Dict[str, float]:
        """
        Create feature vector for a single prediction

        Args:
            recent_performance: Recent performance data (at least 7 days)
            prediction_date: Date to predict budget for

        Returns:
            Dictionary of feature name -> value
        """
        if len(recent_performance) < 7:
            raise ValueError("Need at least 7 days of recent performance data")

        # Get most recent day as current
        current_day = recent_performance[-1]

        # Calculate 7-day trends
        spend_trend = np.mean([d.spend for d in recent_performance])
        roas_trend = np.mean([d.roas for d in recent_performance])
        conversion_trend = np.mean([d.conversions for d in recent_performance])

        # Calculate derived metrics
        engagement_rate = current_day.clicks / current_day.impressions if current_day.impressions > 0 else 0
        spend_efficiency = current_day.revenue / current_day.spend if current_day.spend > 0 else 0
        value_per_conversion = current_day.revenue / current_day.conversions if current_day.conversions > 0 else 0

        # Time-based features for prediction date
        day_of_week = prediction_date.weekday()
        is_weekend = day_of_week in [5, 6]
        week_of_month = (prediction_date.day - 1) // 7 + 1
        day_of_month = prediction_date.day

        features = {
            "daily_spend": current_day.spend,
            "impressions": current_day.impressions,
            "clicks": current_day.clicks,
            "conversions": current_day.conversions,
            "revenue": current_day.revenue,
            "ctr": current_day.ctr,
            "cpc": current_day.cpc,
            "cpa": current_day.cpa,
            "roas": current_day.roas,
            "conversion_rate": current_day.conversion_rate,
            "spend_trend_7d": spend_trend,
            "roas_trend_7d": roas_trend,
            "conversion_trend_7d": conversion_trend,
            "day_of_week": day_of_week,
            "is_weekend": 1 if is_weekend else 0,
            "week_of_month": week_of_month,
            "day_of_month": day_of_month,
            "spend_efficiency": spend_efficiency,
            "engagement_rate": engagement_rate,
            "value_per_conversion": value_per_conversion
        }

        return features
