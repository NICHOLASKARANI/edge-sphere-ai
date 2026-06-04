"""
EdgeSphere AI - Enterprise IoT Device Management Platform
Main Application Entry Point
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, List, Optional
import asyncio

from api.routes import devices, analytics, ota, fleet, ai
from services.mqtt_service import MQTTService
from services.kafka_service import KafkaService
from services.ai_anomaly_detector import AIAnomalyDetector
from services.predictive_maintenance import PredictiveMaintenanceEngine
from database.connection import DatabaseConnection
from models.device import Device
from core.config import settings
from core.security import SecurityManager
from core.telemetry import TelemetryCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
mqtt_service = None
kafka_service = None
anomaly_detector = None
pm_engine = None
security_manager = None
telemetry_collector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global mqtt_service, kafka_service, anomaly_detector, pm_engine
    
    # Startup
    logger.info("Starting EdgeSphere AI Platform...")
    
    # Initialize database
    await DatabaseConnection.initialize()
    
    # Initialize security manager
    security_manager = SecurityManager()
    
    # Initialize MQTT service
    mqtt_service = MQTTService(security_manager)
    await mqtt_service.connect()
    
    # Initialize Kafka service
    kafka_service = KafkaService()
    await kafka_service.start()
    
    # Initialize AI services
    anomaly_detector = AIAnomalyDetector()
    pm_engine = PredictiveMaintenanceEngine()
    
    # Initialize telemetry collector
    telemetry_collector = TelemetryCollector()
    
    # Start background tasks
    asyncio.create_task(process_telemetry_stream())
    asyncio.create_task(monitor_device_health())
    
    logger.info("EdgeSphere AI Platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down EdgeSphere AI Platform...")
    await mqtt_service.disconnect()
    await kafka_service.stop()
    await DatabaseConnection.close()

# Create FastAPI app
app = FastAPI(
    title="EdgeSphere AI",
    description="Enterprise IoT Device Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Include routers
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(ota.router, prefix="/api/v1/ota", tags=["ota"])
app.include_router(fleet.router, prefix="/api/v1/fleet", tags=["fleet"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])

@app.get("/")
async def root():
    return {
        "name": "EdgeSphere AI",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "device_fleet_management",
            "ai_anomaly_detection",
            "predictive_maintenance",
            "ota_updates",
            "real_time_telemetry"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "database": await DatabaseConnection.health_check(),
            "mqtt": mqtt_service.is_connected(),
            "kafka": kafka_service.is_healthy()
        }
    }
    
    if not all(health_status["services"].values()):
        raise HTTPException(status_code=503, detail="Service unhealthy")
    
    return health_status

async def process_telemetry_stream():
    """Background task to process telemetry data"""
    while True:
        try:
            message = await kafka_service.consume("device_telemetry")
            if message:
                # Process anomaly detection
                anomaly = await anomaly_detector.detect(message)
                if anomaly:
                    await handle_anomaly(message, anomaly)
                
                # Update predictive maintenance models
                await pm_engine.update_model(message)
                
                # Store telemetry
                await telemetry_collector.store(message)
                
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}")
            await asyncio.sleep(1)

async def monitor_device_health():
    """Monitor device health and trigger alerts"""
    while True:
        try:
            devices = await Device.get_all_active()
            for device in devices:
                health_score = await pm_engine.get_device_health(device.id)
                if health_score < settings.HEALTH_THRESHOLD:
                    await trigger_health_alert(device, health_score)
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(5)

async def handle_anomaly(telemetry: Dict, anomaly: Dict):
    """Handle detected anomalies"""
    logger.warning(f"Anomaly detected: {anomaly}")
    
    # Store anomaly
    await telemetry_collector.store_anomaly(anomaly)
    
    # Trigger alerts
    if anomaly["severity"] == "critical":
        await send_critical_alert(anomaly)
    
    # Update dashboard via WebSocket
    await notify_dashboard("anomaly", anomaly)

async def trigger_health_alert(device: Device, health_score: float):
    """Trigger device health alerts"""
    alert = {
        "device_id": device.id,
        "health_score": health_score,
        "threshold": settings.HEALTH_THRESHOLD,
        "timestamp": datetime.utcnow().isoformat(),
        "recommended_action": await pm_engine.get_recommendation(device.id)
    }
    
    await notify_dashboard("health_alert", alert)

async def notify_dashboard(event_type: str, data: Dict):
    """Send real-time notifications to dashboard"""
    # Implement WebSocket notification
    pass

async def send_critical_alert(anomaly: Dict):
    """Send critical alerts via configured channels"""
    # Implement email, SMS, webhook notifications
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )