"""
Machine Learning Module for PulseBridge.ai
Real ML implementations for campaign optimization
"""
from app.ml.meta_data_collector import MetaDataCollector, CampaignPerformanceData
from app.ml.feature_engineering import FeatureEngineer
from app.ml.budget_optimizer import BudgetOptimizerML

__all__ = [
    "MetaDataCollector",
    "CampaignPerformanceData",
    "FeatureEngineer",
    "BudgetOptimizerML"
]
