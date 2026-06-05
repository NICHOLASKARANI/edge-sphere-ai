"""
Advanced Predictive Maintenance Models
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceAdvanced:
    def __init__(self):
        self.rul_model = None  # Remaining Useful Life
        self.failure_model = None  # Failure probability
        self.quality_model = None  # Quality prediction
        self.scaler = StandardScaler()
        
    def train_remaining_useful_life(self, historical_data: pd.DataFrame):
        """
        Train RUL prediction model using sensor data
        """
        features = ['temperature', 'vibration', 'current', 'voltage', 
                   'power_consumption', 'cpu_usage', 'error_rate']
        
        X = historical_data[features].values
        y = historical_data['remaining_life_hours'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest Regressor
        self.rul_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42
        )
        self.rul_model.fit(X_scaled, y)
        
        # Save model
        joblib.dump(self.rul_model, 'models/rul_model.pkl')
        joblib.dump(self.scaler, 'models/scaler.pkl')
        
        return self.rul_model
    
    def predict_failure_probability(self, telemetry: Dict) -> Dict:
        """
        Predict probability of failure in next 24h, 7d, 30d
        """
        features = self.extract_features(telemetry)
        features_scaled = self.scaler.transform([features])
        
        # Get failure probability from model
        if self.failure_model:
            prob_24h = self.failure_model.predict_proba(features_scaled)[0][1]
        else:
            # Fallback rule-based prediction
            prob_24h = self.calculate_risk_score(telemetry)
        
        return {
            '24h_probability': round(prob_24h * 100, 1),
            '7d_probability': round(min(prob_24h * 1.5, 1) * 100, 1),
            '30d_probability': round(min(prob_24h * 2.5, 1) * 100, 1),
            'risk_level': self.get_risk_level(prob_24h),
            'recommended_action': self.get_maintenance_action(prob_24h)
        }
    
    def predict_quality_score(self, telemetry_history: List[Dict]) -> float:
        """
        Predict product quality score based on device telemetry
        """
        if len(telemetry_history) < 10:
            return 95.0  # Default high quality
        
        # Extract quality indicators
        quality_indicators = []
        for reading in telemetry_history[-50:]:
            quality_score = 100
            if reading.get('temperature', 25) > 45:
                quality_score -= 10
            if reading.get('vibration', 0) > 3:
                quality_score -= 15
            if reading.get('current', 0) > 2.5:
                quality_score -= 5
            quality_indicators.append(max(0, quality_score))
        
        return round(np.mean(quality_indicators), 1)
    
    def calculate_risk_score(self, telemetry: Dict) -> float:
        """
        Calculate risk score based on current telemetry
        """
        risk = 0.0
        
        # Temperature risk
        temp = telemetry.get('temperature', 25)
        if temp > 60:
            risk += 0.4
        elif temp > 50:
            risk += 0.2
        elif temp > 40:
            risk += 0.1
        
        # Vibration risk
        vib = telemetry.get('vibration', 0)
        if vib > 8:
            risk += 0.3
        elif vib > 5:
            risk += 0.15
        
        # Current risk
        current = telemetry.get('current', 0)
        if current > 3:
            risk += 0.2
        elif current > 2:
            risk += 0.1
        
        return min(risk, 1.0)
    
    def get_risk_level(self, probability: float) -> str:
        if probability > 0.7:
            return "Critical"
        elif probability > 0.4:
            return "High"
        elif probability > 0.2:
            return "Medium"
        else:
            return "Low"
    
    def get_maintenance_action(self, probability: float) -> str:
        if probability > 0.7:
            return "Immediate maintenance required - Stop production"
        elif probability > 0.4:
            return "Schedule maintenance within 24 hours"
        elif probability > 0.2:
            return "Plan maintenance for next scheduled downtime"
        else:
            return "Continue normal monitoring"
    
    def extract_features(self, telemetry: Dict) -> List[float]:
        return [
            telemetry.get('temperature', 25),
            telemetry.get('vibration', 0),
            telemetry.get('current', 0),
            telemetry.get('voltage', 0),
            telemetry.get('power_consumption', 0),
            telemetry.get('cpu_usage', 0),
            telemetry.get('error_rate', 0)
        ]