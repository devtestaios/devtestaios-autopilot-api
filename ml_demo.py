# ML Optimizer Testing & Demo Script
# Real machine learning budget optimization for Meta ads

import requests
import json
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "https://autopilot-api-1.onrender.com"
ML_BASE = f"{BASE_URL}/api/v1/ml"

def test_ml_health():
    """Test ML system health"""
    print("🔍 Testing ML System Health...")
    response = requests.get(f"{ML_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_model_training():
    """Test ML model training with sample campaign data"""
    print("\n🧠 Testing ML Model Training...")
    
    # Sample training request
    training_data = {
        "campaign_ids": ["campaign_123", "campaign_456", "campaign_789"],
        "access_token": "sample_token_for_demo",
        "days_back": 30,
        "include_audience_insights": True
    }
    
    response = requests.post(f"{ML_BASE}/train", json=training_data)
    print(f"Training Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_budget_prediction():
    """Test budget prediction capabilities"""
    print("\n💰 Testing Budget Prediction...")
    
    # Sample prediction request
    prediction_data = {
        "campaign_performance": {
            "impressions": 150000,
            "clicks": 3500,
            "conversions": 85,
            "spend": 1250.50,
            "cpm": 8.34,
            "ctr": 2.33,
            "conversion_rate": 2.43
        },
        "prediction_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "confidence_threshold": 0.8
    }
    
    response = requests.post(f"{ML_BASE}/predict", json=prediction_data)
    print(f"Prediction Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_model_info():
    """Get current model information"""
    print("\n📊 Getting Model Information...")
    
    response = requests.get(f"{ML_BASE}/model/info")
    print(f"Model Info Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 PulseBridge.ai ML Optimizer Demo")
    print("=" * 60)
    
    # Run comprehensive ML tests
    health = test_ml_health()
    model_info = test_model_info()
    
    if health.get("status") == "healthy":
        # Test training (will show ML pipeline even if not fully trained)
        training_result = test_model_training()
        
        # Test prediction capabilities
        prediction_result = test_budget_prediction()
        
        print("\n" + "=" * 60)
        print("✅ ML Optimizer Demo Complete!")
        print("🎯 Key Capabilities Demonstrated:")
        print("   • Real-time health monitoring")
        print("   • ML model training pipeline")
        print("   • Intelligent budget predictions")
        print("   • Model persistence & management")
        print("=" * 60)
    else:
        print("❌ ML system not healthy - check deployment")