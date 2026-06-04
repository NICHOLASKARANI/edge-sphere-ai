"""
AI Anomaly Detection Service
Uses LSTM Autoencoder for time-series anomaly detection
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from typing import Dict, List, Tuple, Optional
import pandas as pd
from datetime import datetime, timedelta
import joblib
import logging
from collections import deque

logger = logging.getLogger(__name__)

class AIAnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.sequence_length = 100
        self.feature_columns = [
            'temperature', 'humidity', 'vibration', 'current',
            'voltage', 'power_consumption', 'rssi', 'cpu_usage',
            'memory_usage', 'uptime'
        ]
        self.threshold = 0.95
        self.window_buffer = {}
        self.load_model()
    
    def load_model(self):
        """Load or create anomaly detection model"""
        try:
            self.model = tf.keras.models.load_model('models/anomaly_detection.h5')
            self.scaler = joblib.load('models/scaler.pkl')
            logger.info("Loaded existing anomaly detection model")
        except:
            logger.info("Creating new anomaly detection model")
            self.create_model()
    
    def create_model(self):
        """Create LSTM Autoencoder model"""
        input_dim = len(self.feature_columns)
        
        # Encoder
        encoder_input = layers.Input(shape=(self.sequence_length, input_dim))
        encoded = layers.LSTM(64, return_sequences=True)(encoder_input)
        encoded = layers.LSTM(32, return_sequences=False)(encoded)
        
        # Decoder
        decoded = layers.RepeatVector(self.sequence_length)(encoded)
        decoded = layers.LSTM(32, return_sequences=True)(decoded)
        decoded = layers.LSTM(64, return_sequences=True)(decoded)
        decoded = layers.TimeDistributed(layers.Dense(input_dim))(decoded)
        
        # Autoencoder
        self.model = models.Model(encoder_input, decoded)
        self.model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("Created new LSTM autoencoder model")
    
    async def detect(self, telemetry_data: Dict) -> Optional[Dict]:
        """
        Detect anomalies in telemetry data
        Returns anomaly info if detected, None otherwise
        """
        device_id = telemetry_data.get('device_id')
        
        if device_id not in self.window_buffer:
            self.window_buffer[device_id] = deque(maxlen=self.sequence_length)
        
        # Extract features
        features = self.extract_features(telemetry_data)
        self.window_buffer[device_id].append(features)
        
        if len(self.window_buffer[device_id]) < self.sequence_length:
            return None
        
        # Prepare sequence
        sequence = np.array(self.window_buffer[device_id])
        sequence = sequence.reshape(1, self.sequence_length, -1)
        
        # Normalize
        sequence_normalized = self.scaler.transform(sequence.reshape(-1, len(self.feature_columns)))
        sequence_normalized = sequence_normalized.reshape(1, self.sequence_length, -1)
        
        # Predict and calculate reconstruction error
        reconstruction = self.model.predict(sequence_normalized, verbose=0)
        mse = np.mean(np.square(sequence_normalized - reconstruction))
        
        # Check anomaly
        if mse > self.threshold:
            # Identify which features contributed to anomaly
            feature_errors = np.mean(np.square(sequence_normalized - reconstruction), axis=(0, 1))
            anomalous_features = [
                self.feature_columns[i] 
                for i, error in enumerate(feature_errors) 
                if error > self.threshold
            ]
            
            severity = self.calculate_severity(mse)
            
            return {
                'device_id': device_id,
                'timestamp': datetime.utcnow().isoformat(),
                'mse_score': float(mse),
                'threshold': self.threshold,
                'severity': severity,
                'anomalous_features': anomalous_features,
                'recommendation': self.get_recommendation(anomalous_features, severity)
            }
        
        return None
    
    def extract_features(self, telemetry: Dict) -> List[float]:
        """Extract feature vector from telemetry data"""
        features = []
        for col in self.feature_columns:
            value = telemetry.get(col, 0.0)
            features.append(float(value))
        return features
    
    def calculate_severity(self, mse_score: float) -> str:
        """Calculate anomaly severity"""
        if mse_score > self.threshold * 1.5:
            return 'critical'
        elif mse_score > self.threshold * 1.2:
            return 'high'
        elif mse_score > self.threshold:
            return 'medium'
        return 'low'
    
    def get_recommendation(self, anomalous_features: List[str], severity: str) -> str:
        """Generate recommendation based on anomalies"""
        recommendations = {
            'temperature': 'Check cooling system, reduce workload',
            'vibration': 'Inspect mechanical components, check mounting',
            'current': 'Check power supply, possible short circuit',
            'cpu_usage': 'Optimize code, check for infinite loops',
            'memory_usage': 'Check for memory leaks, restart device',
            'rssi': 'Check network connectivity, move closer to gateway',
            'power_consumption': 'Check battery health, power supply'
        }
        
        for feature in anomalous_features:
            if feature in recommendations:
                return recommendations[feature]
        
        if severity == 'critical':
            return 'Immediate intervention required - device shutdown recommended'
        elif severity == 'high':
            return 'Schedule maintenance within 24 hours'
        
        return 'Monitor device closely for next 48 hours'
    
    async def train_model(self, historical_data: pd.DataFrame):
        """Train the anomaly detection model"""
        logger.info("Training anomaly detection model...")
        
        # Prepare sequences
        X = []
        for i in range(len(historical_data) - self.sequence_length):
            X.append(historical_data[self.feature_columns].iloc[i:i+self.sequence_length].values)
        
        X = np.array(X)
        
        # Train autoencoder
        history = self.model.fit(
            X, X,
            epochs=50,
            batch_size=32,
            validation_split=0.1,
            verbose=1
        )
        
        # Calculate threshold (99th percentile of reconstruction errors)
        reconstructions = self.model.predict(X, verbose=0)
        mse = np.mean(np.square(X - reconstructions), axis=(1, 2))
        self.threshold = np.percentile(mse, 99)
        
        # Save model
        self.model.save('models/anomaly_detection.h5')
        joblib.dump(self.scaler, 'models/scaler.pkl')
        
        logger.info(f"Model trained. Threshold set to: {self.threshold}")
        return history.history