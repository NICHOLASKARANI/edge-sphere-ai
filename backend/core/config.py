"""
Configuration Management
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "EdgeSphere AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", False)
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/edgesphere")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # MQTT Configuration
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", 1883))
    MQTT_TLS_PORT: int = int(os.getenv("MQTT_TLS_PORT", 8883))
    MQTT_USERNAME: Optional[str] = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD: Optional[str] = os.getenv("MQTT_PASSWORD")
    
    # AWS IoT Core (optional)
    AWS_IOT_ENDPOINT: Optional[str] = os.getenv("AWS_IOT_ENDPOINT")
    AWS_ACCESS_KEY: Optional[str] = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY: Optional[str] = os.getenv("AWS_SECRET_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Azure IoT Hub (optional)
    AZURE_IOT_HUB_CONNECTION_STRING: Optional[str] = os.getenv("AZURE_IOT_HUB_CONNECTION_STRING")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # AI/ML
    ANOMALY_DETECTION_MODEL_PATH: str = os.getenv("ANOMALY_DETECTION_MODEL_PATH", "models/anomaly_detection.h5")
    PREDICTIVE_MAINTENANCE_MODEL_PATH: str = os.getenv("PREDICTIVE_MAINTENANCE_MODEL_PATH", "models/predictive_maintenance.pkl")
    HEALTH_THRESHOLD: float = float(os.getenv("HEALTH_THRESHOLD", 0.7))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.edgesphere.ai"
    ]
    
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Storage
    FIRMWARE_STORAGE_PATH: str = os.getenv("FIRMWARE_STORAGE_PATH", "/var/edgesphere/firmware")
    TELEMETRY_STORAGE_PATH: str = os.getenv("TELEMETRY_STORAGE_PATH", "/var/edgesphere/telemetry")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", True)
    GRAFANA_URL: Optional[str] = os.getenv("GRAFANA_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()