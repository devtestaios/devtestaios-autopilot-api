"""
Budget Optimizer ML Model
Real machine learning model for Meta ads budget optimization
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import pickle
import os
from pathlib import Path

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

from app.ml.meta_data_collector import MetaDataCollector, CampaignPerformanceData
from app.ml.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class BudgetOptimizerML:
    """
    Machine Learning model for optimizing Meta ads daily budgets
    Uses Gradient Boosting to predict optimal budget based on campaign performance
    """

    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize the ML budget optimizer

        Args:
            model_dir: Directory to save/load trained models
        """
        self.model_dir = model_dir or os.path.join(os.path.dirname(__file__), "models")
        Path(self.model_dir).mkdir(parents=True, exist_ok=True)

        # ML components
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_engineer = FeatureEngineer()

        # Model metadata
        self.feature_names: List[str] = []
        self.is_trained = False
        self.training_metrics: Dict[str, float] = {}
        self.model_version = "1.0.0"
        self.trained_at: Optional[datetime] = None

    async def train_on_campaign(
        self,
        campaign_id: str,
        access_token: Optional[str] = None,
        days_back: int = 90,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train model on a single campaign's historical data

        Args:
            campaign_id: Meta campaign ID
            access_token: Meta API access token
            days_back: Days of historical data to use
            test_size: Proportion of data to use for testing

        Returns:
            Dictionary with training metrics and model info
        """
        logger.info(f"Starting training on campaign {campaign_id}")

        # Collect data
        collector = MetaDataCollector(access_token)
        performance_data = await collector.fetch_campaign_history(campaign_id, days_back)

        if not performance_data:
            raise ValueError(f"No performance data available for campaign {campaign_id}")

        return self._train_on_data(performance_data, test_size)

    async def train_on_multiple_campaigns(
        self,
        campaign_ids: List[str],
        access_token: Optional[str] = None,
        days_back: int = 90,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train model on multiple campaigns' data for better generalization

        Args:
            campaign_ids: List of Meta campaign IDs
            access_token: Meta API access token
            days_back: Days of historical data per campaign
            test_size: Proportion of data for testing

        Returns:
            Training metrics and model info
        """
        logger.info(f"Starting training on {len(campaign_ids)} campaigns")

        # Collect data from all campaigns
        collector = MetaDataCollector(access_token)
        all_campaigns_data = await collector.fetch_multiple_campaigns(campaign_ids, days_back)

        # Combine all performance data
        all_performance_data = []
        for campaign_id, data in all_campaigns_data.items():
            all_performance_data.extend(data)

        if not all_performance_data:
            raise ValueError("No performance data available for any campaigns")

        logger.info(f"Collected {len(all_performance_data)} total data points from {len(all_campaigns_data)} campaigns")

        return self._train_on_data(all_performance_data, test_size)

    def _train_on_data(
        self,
        performance_data: List[CampaignPerformanceData],
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """Internal method to train model on performance data"""

        # Engineer features
        feature_df = self.feature_engineer.engineer_features(performance_data)

        if feature_df.empty:
            raise ValueError("Insufficient data for feature engineering")

        # Prepare training data
        X, y, feature_names = self.feature_engineer.prepare_training_data(feature_df)
        self.feature_names = feature_names

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=True
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        logger.info(f"Training model on {len(X_train)} samples...")
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        train_predictions = self.model.predict(X_train_scaled)
        test_predictions = self.model.predict(X_test_scaled)

        train_mae = mean_absolute_error(y_train, train_predictions)
        test_mae = mean_absolute_error(y_test, test_predictions)
        train_r2 = r2_score(y_train, train_predictions)
        test_r2 = r2_score(y_test, test_predictions)

        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train,
            cv=5, scoring='neg_mean_absolute_error'
        )
        cv_mae = -cv_scores.mean()

        self.training_metrics = {
            "train_mae": float(train_mae),
            "test_mae": float(test_mae),
            "train_r2": float(train_r2),
            "test_r2": float(test_r2),
            "cv_mae": float(cv_mae),
            "n_samples": len(X),
            "n_features": len(feature_names)
        }

        self.is_trained = True
        self.trained_at = datetime.now()

        # Feature importance
        feature_importance = dict(zip(
            feature_names,
            self.model.feature_importances_
        ))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

        logger.info(f"Training complete. Test MAE: ${test_mae:.2f}, Test R²: {test_r2:.3f}")

        return {
            "status": "success",
            "metrics": self.training_metrics,
            "top_features": top_features,
            "model_version": self.model_version,
            "trained_at": self.trained_at.isoformat(),
            "feature_count": len(feature_names)
        }

    def predict_optimal_budget(
        self,
        recent_performance: List[CampaignPerformanceData],
        prediction_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Predict optimal budget for next day based on recent performance

        Args:
            recent_performance: At least 7 days of recent performance data
            prediction_date: Date to predict for (default: tomorrow)

        Returns:
            Dictionary with prediction and confidence metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")

        if len(recent_performance) < 7:
            raise ValueError("Need at least 7 days of recent performance for prediction")

        prediction_date = prediction_date or (datetime.now() + timedelta(days=1))

        # Create features for prediction
        features_dict = self.feature_engineer.create_prediction_features(
            recent_performance,
            prediction_date
        )

        # Convert to numpy array in correct order
        X_pred = np.array([[features_dict[fname] for fname in self.feature_names]])

        # Scale and predict
        X_pred_scaled = self.scaler.transform(X_pred)
        predicted_budget = self.model.predict(X_pred_scaled)[0]

        # Calculate confidence based on recent performance variance
        recent_spends = [d.spend for d in recent_performance[-7:]]
        spend_std = np.std(recent_spends)
        spend_mean = np.mean(recent_spends)
        coefficient_of_variation = spend_std / spend_mean if spend_mean > 0 else 1.0

        # Lower CV = higher confidence
        confidence = max(0.5, 1.0 - coefficient_of_variation)

        # Get current performance metrics
        current_day = recent_performance[-1]

        # Calculate expected impact
        budget_change_pct = ((predicted_budget - current_day.spend) / current_day.spend * 100) if current_day.spend > 0 else 0

        return {
            "predicted_budget": float(predicted_budget),
            "current_budget": float(current_day.spend),
            "budget_change": float(predicted_budget - current_day.spend),
            "budget_change_percentage": float(budget_change_pct),
            "confidence_score": float(confidence),
            "prediction_date": prediction_date.isoformat(),
            "current_roas": float(current_day.roas),
            "recent_7d_avg_roas": float(np.mean([d.roas for d in recent_performance[-7:]])),
            "reasoning": self._generate_reasoning(
                predicted_budget,
                current_day.spend,
                current_day.roas,
                budget_change_pct
            ),
            "model_version": self.model_version
        }

    def _generate_reasoning(
        self,
        predicted_budget: float,
        current_budget: float,
        current_roas: float,
        change_pct: float
    ) -> str:
        """Generate human-readable reasoning for the prediction"""
        if abs(change_pct) < 5:
            return f"Maintain current budget. Performance is stable at {current_roas:.2f}x ROAS."
        elif change_pct > 0:
            return f"Increase budget by {change_pct:.1f}%. Strong ROAS of {current_roas:.2f}x indicates room for profitable scaling."
        else:
            return f"Decrease budget by {abs(change_pct):.1f}%. Current ROAS of {current_roas:.2f}x suggests efficiency optimization needed."

    def save_model(self, filename: Optional[str] = None) -> str:
        """
        Save trained model to disk

        Args:
            filename: Custom filename (default: auto-generated)

        Returns:
            Path to saved model file
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        filename = filename or f"budget_optimizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        filepath = os.path.join(self.model_dir, filename)

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "training_metrics": self.training_metrics,
            "model_version": self.model_version,
            "trained_at": self.trained_at
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {filepath}")
        return filepath

    def load_model(self, filepath: str) -> None:
        """
        Load trained model from disk

        Args:
            filepath: Path to saved model file
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        self.training_metrics = model_data["training_metrics"]
        self.model_version = model_data.get("model_version", "unknown")
        self.trained_at = model_data.get("trained_at")
        self.is_trained = True

        logger.info(f"Model loaded from {filepath}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "is_trained": self.is_trained,
            "model_version": self.model_version,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "training_metrics": self.training_metrics,
            "feature_count": len(self.feature_names),
            "model_type": "GradientBoostingRegressor"
        }
