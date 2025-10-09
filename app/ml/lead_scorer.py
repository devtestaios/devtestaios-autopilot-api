"""
Lead Scoring ML Model
AI-powered lead qualification across all platforms
"""
# Graceful ML imports
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    ML_AVAILABLE = True
except ImportError:
    # Fallback imports
    np = None
    pd = None
    GradientBoostingClassifier = None
    RandomForestClassifier = None
    train_test_split = None
    cross_val_score = None
    GridSearchCV = None
    classification_report = None
    confusion_matrix = None
    roc_auc_score = None
    precision_recall_curve = None
    StandardScaler = None
    LabelEncoder = None
    ML_AVAILABLE = False

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class LeadScorerML:
    """
    AI-powered lead scoring system
    Predicts lead quality and recommends follow-up strategies
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'email_engagement_score',
            'website_session_duration', 
            'pages_viewed',
            'form_completion_quality',
            'social_media_activity',
            'company_size_score',
            'industry_relevance',
            'geographic_score',
            'referral_source_quality',
            'time_to_convert'
        ]
        self.is_trained = False
        self.model_version = "1.0.0"
        self.training_date = None
        self.performance_metrics = {}
        
    def prepare_features(self, lead_data: Dict[str, Any]) -> np.ndarray:
        """
        Transform raw lead data into ML-ready features
        
        Args:
            lead_data: Raw lead information from various platforms
            
        Returns:
            Feature vector for ML prediction
        """
        features = {}
        
        # Email engagement scoring (0-100)
        email_data = lead_data.get('email_activity', {})
        features['email_engagement_score'] = self._calculate_email_score(email_data)
        
        # Website behavior scoring (0-100)
        website_data = lead_data.get('website_activity', {})
        features['website_session_duration'] = min(website_data.get('avg_session_duration', 0) / 300, 100)
        features['pages_viewed'] = min(website_data.get('total_pages_viewed', 0) * 5, 100)
        
        # Form completion quality (0-100)
        form_data = lead_data.get('form_submission', {})
        features['form_completion_quality'] = self._calculate_form_quality(form_data)
        
        # Social media activity (0-100)
        social_data = lead_data.get('social_activity', {})
        features['social_media_activity'] = self._calculate_social_score(social_data)
        
        # Company/demographic scoring (0-100)
        company_data = lead_data.get('company_info', {})
        features['company_size_score'] = self._calculate_company_score(company_data)
        features['industry_relevance'] = self._calculate_industry_score(company_data)
        features['geographic_score'] = self._calculate_geo_score(lead_data.get('location', {}))
        
        # Source quality (0-100)
        source_data = lead_data.get('source_info', {})
        features['referral_source_quality'] = self._calculate_source_score(source_data)
        
        # Timing factors (0-100)
        timing_data = lead_data.get('timing', {})
        features['time_to_convert'] = self._calculate_timing_score(timing_data)
        
        # Convert to numpy array in correct order
        feature_vector = np.array([features[col] for col in self.feature_columns]).reshape(1, -1)
        
        return feature_vector
    
    def _calculate_email_score(self, email_data: Dict) -> float:
        """Calculate email engagement score"""
        open_rate = email_data.get('open_rate', 0) * 100
        click_rate = email_data.get('click_rate', 0) * 100 * 2  # Weight clicks higher
        reply_rate = email_data.get('reply_rate', 0) * 100 * 3  # Weight replies highest
        
        return min(open_rate + click_rate + reply_rate, 100)
    
    def _calculate_form_quality(self, form_data: Dict) -> float:
        """Calculate form completion quality score"""
        fields_completed = form_data.get('fields_completed', 0)
        total_fields = form_data.get('total_fields', 1)
        completion_rate = (fields_completed / total_fields) * 100
        
        # Bonus for high-value fields
        high_value_fields = ['phone', 'company', 'job_title', 'budget']
        bonus = sum(10 for field in high_value_fields if form_data.get(field))
        
        return min(completion_rate + bonus, 100)
    
    def _calculate_social_score(self, social_data: Dict) -> float:
        """Calculate social media activity score"""
        linkedin_connections = min(social_data.get('linkedin_connections', 0) / 500 * 50, 50)
        twitter_followers = min(social_data.get('twitter_followers', 0) / 1000 * 25, 25)
        engagement_rate = social_data.get('engagement_rate', 0) * 25
        
        return linkedin_connections + twitter_followers + engagement_rate
    
    def _calculate_company_score(self, company_data: Dict) -> float:
        """Calculate company size/quality score"""
        employee_count = company_data.get('employee_count', 0)
        
        if employee_count >= 1000:
            return 100
        elif employee_count >= 500:
            return 80
        elif employee_count >= 100:
            return 60
        elif employee_count >= 50:
            return 40
        elif employee_count >= 10:
            return 20
        else:
            return 10
    
    def _calculate_industry_score(self, company_data: Dict) -> float:
        """Calculate industry relevance score"""
        industry = company_data.get('industry', '').lower()
        
        # High-value industries for typical B2B SaaS
        high_value = ['technology', 'software', 'finance', 'healthcare', 'consulting']
        medium_value = ['manufacturing', 'retail', 'education', 'real estate']
        
        if any(hv in industry for hv in high_value):
            return 100
        elif any(mv in industry for mv in medium_value):
            return 60
        else:
            return 30
    
    def _calculate_geo_score(self, location_data: Dict) -> float:
        """Calculate geographic desirability score"""
        country = location_data.get('country', '').lower()
        state = location_data.get('state', '').lower()
        
        # High-value geographic regions
        if country in ['united states', 'canada', 'united kingdom', 'australia']:
            if state in ['california', 'new york', 'texas', 'florida']:
                return 100
            else:
                return 80
        elif country in ['germany', 'france', 'netherlands', 'sweden']:
            return 70
        else:
            return 40
    
    def _calculate_source_score(self, source_data: Dict) -> float:
        """Calculate traffic source quality score"""
        source = source_data.get('source', '').lower()
        
        source_scores = {
            'organic_search': 90,
            'direct': 85,
            'referral': 80,
            'linkedin': 75,
            'google_ads': 70,
            'facebook_ads': 60,
            'email': 85,
            'webinar': 95,
            'content_download': 80
        }
        
        return source_scores.get(source, 50)
    
    def _calculate_timing_score(self, timing_data: Dict) -> float:
        """Calculate timing-based score"""
        days_since_first_visit = timing_data.get('days_since_first_visit', 0)
        
        # Sweet spot: 1-7 days (shows interest but not too stale)
        if 1 <= days_since_first_visit <= 7:
            return 100
        elif days_since_first_visit <= 14:
            return 80
        elif days_since_first_visit <= 30:
            return 60
        else:
            return 30
    
    def predict_lead_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict lead quality score and recommended actions
        
        Args:
            lead_data: Raw lead information
            
        Returns:
            Prediction results with score and recommendations
        """
        if not self.is_trained:
            # Return rule-based scoring if ML model not trained yet
            return self._rule_based_scoring(lead_data)
        
        try:
            # Prepare features
            features = self.prepare_features(lead_data)
            scaled_features = self.scaler.transform(features)
            
            # Get prediction and probability
            prediction = self.model.predict(scaled_features)[0]
            probabilities = self.model.predict_proba(scaled_features)[0]
            
            # Convert to 0-100 score
            lead_score = int(probabilities[1] * 100)  # Probability of being high-quality lead
            
            # Generate recommendations
            recommendations = self._generate_recommendations(lead_score, lead_data)
            
            return {
                "lead_score": lead_score,
                "quality_tier": self._get_quality_tier(lead_score),
                "confidence": float(max(probabilities)),
                "recommendations": recommendations,
                "prediction_date": datetime.now().isoformat(),
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Lead scoring prediction failed: {e}")
            return self._rule_based_scoring(lead_data)
    
    def _rule_based_scoring(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based scoring when ML model not available"""
        features = self.prepare_features(lead_data)
        
        # Simple weighted average of features
        weights = [0.15, 0.12, 0.08, 0.20, 0.10, 0.15, 0.10, 0.05, 0.03, 0.02]
        lead_score = int(np.average(features[0], weights=weights))
        
        return {
            "lead_score": lead_score,
            "quality_tier": self._get_quality_tier(lead_score),
            "confidence": 0.7,  # Lower confidence for rule-based
            "recommendations": self._generate_recommendations(lead_score, lead_data),
            "prediction_date": datetime.now().isoformat(),
            "model_version": "rule-based-fallback"
        }
    
    def _get_quality_tier(self, score: int) -> str:
        """Convert numeric score to quality tier"""
        if score >= 80:
            return "HOT"
        elif score >= 60:
            return "WARM"
        elif score >= 40:
            return "COOL"
        else:
            return "COLD"
    
    def _generate_recommendations(self, score: int, lead_data: Dict) -> List[str]:
        """Generate specific follow-up recommendations"""
        recommendations = []
        
        if score >= 80:
            recommendations.extend([
                "IMMEDIATE CALL: Contact within 5 minutes",
                "Assign to top sales rep",
                "Send premium content/demo invitation",
                "Add to high-priority follow-up sequence"
            ])
        elif score >= 60:
            recommendations.extend([
                "Contact within 1 hour",
                "Send personalized email with case studies",
                "Schedule discovery call",
                "Add to warm lead nurture sequence"
            ])
        elif score >= 40:
            recommendations.extend([
                "Add to email nurture campaign",
                "Send educational content",
                "Monitor for additional engagement",
                "Follow up in 3-5 days"
            ])
        else:
            recommendations.extend([
                "Add to long-term nurture campaign",
                "Send quarterly check-in emails",
                "Monitor for engagement signals",
                "Consider disqualifying after 6 months"
            ])
        
        return recommendations
    
    def train_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """
        Train the lead scoring ML model
        
        Args:
            training_data: Historical lead data with outcomes
            
        Returns:
            Training results and performance metrics
        """
        try:
            logger.info(f"Training lead scoring model on {len(training_data)} samples")
            
            # Prepare training data
            X = []
            y = []
            
            for lead in training_data:
                features = self.prepare_features(lead)
                X.append(features[0])
                # Outcome: 1 for converted/qualified leads, 0 for others
                y.append(1 if lead.get('converted', False) else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            # Get predictions for detailed metrics
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            auc_score = roc_auc_score(y_test, y_pred_proba)
            
            self.performance_metrics = {
                "training_accuracy": float(train_score),
                "test_accuracy": float(test_score),
                "auc_score": float(auc_score),
                "training_samples": len(training_data),
                "feature_importance": {
                    feature: float(importance) 
                    for feature, importance in zip(self.feature_columns, self.model.feature_importances_)
                }
            }
            
            self.is_trained = True
            self.training_date = datetime.now()
            
            logger.info(f"Lead scoring model training complete. AUC: {auc_score:.3f}")
            
            return {
                "status": "success",
                "model_performance": self.performance_metrics,
                "training_date": self.training_date.isoformat(),
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Lead scoring model training failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            "is_trained": self.is_trained,
            "model_version": self.model_version,
            "training_date": self.training_date.isoformat() if self.training_date else None,
            "performance_metrics": self.performance_metrics,
            "feature_columns": self.feature_columns,
            "model_type": "GradientBoostingClassifier"
        }
    
    def save_model(self, filepath: Optional[str] = None) -> str:
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        if filepath is None:
            models_dir = Path("app/ml/models")
            models_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"app/ml/models/lead_scorer_{timestamp}.pkl"
        
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_columns": self.feature_columns,
            "model_version": self.model_version,
            "training_date": self.training_date,
            "performance_metrics": self.performance_metrics
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Lead scoring model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_columns = model_data["feature_columns"]
        self.model_version = model_data["model_version"]
        self.training_date = model_data["training_date"]
        self.performance_metrics = model_data["performance_metrics"]
        self.is_trained = True
        
        logger.info(f"Lead scoring model loaded from {filepath}")