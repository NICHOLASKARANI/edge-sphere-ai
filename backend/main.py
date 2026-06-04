from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import random

app = FastAPI(title="EdgeSphere AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Device(BaseModel):
    device_id: str
    device_type: str
    status: str
    firmware_version: str
    last_seen: str
    location: Optional[str] = None

class Telemetry(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    vibration: float
    cpu_usage: float
    timestamp: str

# In-memory storage
devices_db = {}
telemetry_db = {}
anomalies_db = []

@app.get("/")
async def root():
    return {"message": "EdgeSphere AI API", "status": "operational", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/devices/register")
async def register_device(device: Device):
    device.last_seen = datetime.now().isoformat()
    devices_db[device.device_id] = device.dict()
    return {"message": "Device registered", "device_id": device.device_id}

@app.get("/api/v1/devices")
async def get_devices():
    return list(devices_db.values())

@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str):
    if device_id not in devices_db:
        raise HTTPException(status_code=404, detail="Device not found")
    return devices_db[device_id]

@app.post("/api/v1/telemetry")
async def receive_telemetry(telemetry: Telemetry):
    if telemetry.device_id not in telemetry_db:
        telemetry_db[telemetry.device_id] = []
    
    telemetry_db[telemetry.device_id].append(telemetry.dict())
    
    # Anomaly detection
    if telemetry.temperature > 50 or telemetry.vibration > 5:
        anomaly = {
            "device_id": telemetry.device_id,
            "type": "critical" if telemetry.temperature > 70 else "warning",
            "message": f"High {'temperature' if telemetry.temperature > 50 else 'vibration'} detected",
            "value": telemetry.temperature if telemetry.temperature > 50 else telemetry.vibration,
            "timestamp": datetime.now().isoformat()
        }
        anomalies_db.append(anomaly)
        
    # Update device last seen
    if telemetry.device_id in devices_db:
        devices_db[telemetry.device_id]["last_seen"] = datetime.now().isoformat()
    
    return {"message": "Telemetry received", "anomaly_detected": telemetry.temperature > 50 or telemetry.vibration > 5}

@app.get("/api/v1/telemetry/{device_id}")
async def get_telemetry(device_id: str, limit: int = 100):
    if device_id not in telemetry_db:
        return []
    return telemetry_db[device_id][-limit:]

@app.get("/api/v1/anomalies")
async def get_anomalies():
    return anomalies_db

@app.get("/api/v1/stats")
async def get_stats():
    return {
        "total_devices": len(devices_db),
        "online_devices": sum(1 for d in devices_db.values() if d.get("status") == "online"),
        "total_telemetry": sum(len(t) for t in telemetry_db.values()),
        "anomalies_count": len(anomalies_db)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 EdgeSphere AI Backend Starting...")
    print("📡 API available at: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
