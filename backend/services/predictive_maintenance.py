"""
Predictive Maintenance Engine
Uses Random Forest and LSTM for failure prediction
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class PredictiveMaintenanceEngine:
    def __init__(self):
        self.failure_classifier = None
        self.remaining_life_regressor = None
        self.scaler = StandardScaler()
        self.device_health = defaultdict(float)
        self.failure_patterns = defaultdict(list)
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            self.failure_classifier = joblib.load('models/failure_classifier.pkl')
            self.remaining_life_regressor = joblib.load('models/remaining_life_regressor.pkl')
            logger.info("Loaded existing predictive maintenance models")
        except:
            logger.info("Creating new predictive maintenance models")
            self.create_models()
    
    def create_models(self):
        """Create new models"""
        self.failure_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.remaining_life_regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            random_state=42
        )
    
    async def update_model(self, telemetry: Dict):
        """Update model with new telemetry data"""
        device_id = telemetry.get('device_id')
        
        # Update health score
        health_score = self.calculate_health_score(telemetry)
        self.device_health[device_id] = health_score
        
        # Predict failure probability
        failure_prob = await self.predict_failure_probability(telemetry)
        
        if failure_prob > 0.8:
            self.failure_patterns[device_id].append({
                'timestamp': datetime.utcnow(),
                'probability': failure_prob,
                'telemetry': telemetry
            })
    
    def calculate_health_score(self, telemetry: Dict) -> float:
        """Calculate device health score (0-1, 1 is perfect)"""
        health_factors = {
            'temperature': (telemetry.get('temperature', 25) - 25) / 25,  # Deviation from ideal
            'vibration': telemetry.get('vibration', 0) / 5,  # Normalized vibration
            'cpu_usage': telemetry.get('cpu_usage', 0) / 100,
            'memory_usage': telemetry.get('memory_usage', 0) / 100,
            'uptime': min(telemetry.get('uptime', 0) / (30*24*3600), 1)  # Uptime degradation
        }
        
        # Weighted score
        weights = {
            'temperature': 0.25,
            'vibration': 0.25,
            'cpu_usage': 0.20,
            'memory_usage': 0.20,
            'uptime': 0.10
        }
        
        health_score = 1.0 - sum(weights[k] * min(max(health_factors[k], 0), 1) for k in health_factors)
        return max(0, min(health_score, 1))
    
    async def predict_failure_probability(self, telemetry: Dict) -> float:
        """Predict probability of failure in next 24 hours"""
        features = self.extract_features(telemetry)
        features_scaled = self.scaler.transform([features])
        
        if self.failure_classifier:
            prob = self.failure_classifier.predict_proba(features_scaled)[0][1]
            return float(prob)
        
        return 0.0
    
    async def predict_remaining_life(self, device_id: str, telemetry_history: List[Dict]) -> Dict:
        """Predict remaining useful life (RUL) in days"""
        if len(telemetry_history) < 10:
            return {'remaining_days': None, 'confidence': 0}
        
        # Prepare features from recent history
        recent = telemetry_history[-30:]  # Last 30 readings
        features = self.extract_sequence_features(recent)
        features_scaled = self.scaler.transform([features])
        
        if self.remaining_life_regressor:
            remaining_hours = self.remaining_life_regressor.predict(features_scaled)[0]
            remaining_days = remaining_hours / 24
            
            return {
                'remaining_days': round(remaining_days, 1),
                'remaining_hours': round(remaining_hours, 1),
                'confidence': self.calculate_confidence(recent),
                'recommendation': self.get_maintenance_recommendation(remaining_days)
            }
        
        return {'remaining_days': None, 'confidence': 0}
    
    async def get_device_health(self, device_id: str) -> float:
        """Get current device health score"""
        return self.device_health.get(device_id, 1.0)
    
    async def get_recommendation(self, device_id: str) -> str:
        """Get maintenance recommendation"""
        health = self.device_health.get(device_id, 1.0)
        
        if health < 0.3:
            return "IMMEDIATE MAINTENANCE REQUIRED - Device at critical risk"
        elif health < 0.5:
            return "Schedule maintenance within 7 days"
        elif health < 0.7:
            return "Monitor device closely, plan maintenance in 30 days"
        else:
            return "Device operating normally, routine checks recommended"
    
    def extract_features(self, telemetry: Dict) -> List[float]:
        """Extract feature vector for prediction"""
        return [
            telemetry.get('temperature', 25),
            telemetry.get('vibration', 0),
            telemetry.get('current', 0),
            telemetry.get('voltage', 0),
            telemetry.get('power_consumption', 0),
            telemetry.get('cpu_usage', 0),
            telemetry.get('memory_usage', 0),
            telemetry.get('uptime', 0),
            telemetry.get('error_rate', 0),
            telemetry.get('packet_loss', 0)
        ]
    
    def extract_sequence_features(self, telemetry_history: List[Dict]) -> List[float]:
        """Extract features from telemetry sequence"""
        df = pd.DataFrame(telemetry_history)
        
        features = []
        for col in ['temperature', 'vibration', 'current', 'cpu_usage', 'memory_usage']:
            if col in df:
                features.append(df[col].mean())
                features.append(df[col].std())
                features.append(df[col].max())
                features.append(df[col].min())
                features.append(df[col].iloc[-1] - df[col].iloc[0])  # Trend
        
        return features
    
    def calculate_confidence(self, history: List[Dict]) -> float:
        """Calculate prediction confidence based on data quality"""
        if len(history) < 30:
            return 0.5
        return 0.9
    
    def get_maintenance_recommendation(self, remaining_days: float) -> str:
        """Get recommendation based on remaining life"""
        if remaining_days < 7:
            return "Critical: Immediate maintenance required"
        elif remaining_days < 30:
            return "High priority: Schedule maintenance in next 2 weeks"
        elif remaining_days < 90:
            return "Medium priority: Plan maintenance in next month"
        else:
            return "Low priority: Continue regular monitoring"