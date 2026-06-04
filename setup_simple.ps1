# EdgeSphere AI Simple Windows Setup
# Save this file as setup_simple.ps1 and run in PowerShell as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   EdgeSphere AI Platform Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Create directory structure
Write-Host "`n[1/4] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "backend\app" | Out-Null
New-Item -ItemType Directory -Force -Path "web-dashboard\src" | Out-Null
New-Item -ItemType Directory -Force -Path "web-dashboard\public" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Create backend files
Write-Host "`n[2/4] Creating backend API..." -ForegroundColor Yellow

# requirements.txt
@"
fastapi
uvicorn
pydantic
python-dotenv
"@ | Out-File -FilePath "backend\requirements.txt" -Encoding UTF8

# main.py
$mainPy = @'
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
'@
$mainPy | Out-File -FilePath "backend\main.py" -Encoding UTF8

Write-Host "✓ Backend created" -ForegroundColor Green

# Create React dashboard
Write-Host "`n[3/4] Creating React dashboard..." -ForegroundColor Yellow

# package.json
$packageJson = @'
{
  "name": "edgesphere-dashboard",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.6.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "eslintConfig": {
    "extends": ["react-app"]
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
'@
$packageJson | Out-File -FilePath "web-dashboard\package.json" -Encoding UTF8

# App.js
$appJs = @'
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function App() {
  const [devices, setDevices] = useState([]);
  const [stats, setStats] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [telemetry, setTelemetry] = useState([]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [devicesRes, statsRes, anomaliesRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/devices`),
        axios.get(`${API_URL}/api/v1/stats`),
        axios.get(`${API_URL}/api/v1/anomalies`)
      ]);
      setDevices(devicesRes.data);
      setStats(statsRes.data);
      setAnomalies(anomaliesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const fetchTelemetry = async (deviceId) => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/telemetry/${deviceId}`);
      setTelemetry(res.data);
      setSelectedDevice(deviceId);
    } catch (error) {
      console.error('Error fetching telemetry:', error);
    }
  };

  const registerDevice = async () => {
    const deviceId = prompt('Enter Device ID (e.g., ESP32_001):');
    if (!deviceId) return;
    
    const deviceType = prompt('Enter Device Type (ESP32/STM32/RPi):', 'ESP32');
    try {
      await axios.post(`${API_URL}/api/v1/devices/register`, {
        device_id: deviceId,
        device_type: deviceType,
        status: 'online',
        firmware_version: '1.0.0',
        last_seen: new Date().toISOString()
      });
      fetchData();
      alert('Device registered successfully!');
    } catch (error) {
      alert('Error registering device');
    }
  };

  const sendTestTelemetry = async () => {
    const deviceId = prompt('Enter Device ID:');
    if (!deviceId) return;
    
    const temp = parseFloat(prompt('Enter Temperature (C):', '25'));
    const vib = parseFloat(prompt('Enter Vibration (mm/s):', '0.5'));
    
    try {
      await axios.post(`${API_URL}/api/v1/telemetry`, {
        device_id: deviceId,
        temperature: temp,
        humidity: 50,
        vibration: vib,
        cpu_usage: 30,
        timestamp: new Date().toISOString()
      });
      alert('Telemetry sent!');
      if (selectedDevice === deviceId) {
        fetchTelemetry(deviceId);
      }
      fetchData();
    } catch (error) {
      alert('Error sending telemetry');
    }
  };

  return (
    <div style={{ 
      fontFamily: 'Arial, sans-serif', 
      maxWidth: '1400px', 
      margin: '0 auto', 
      padding: '20px',
      background: '#0a0e27',
      minHeight: '100vh',
      color: '#fff'
    }}>
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '20px',
        borderRadius: '10px',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: 0 }}>🚀 EdgeSphere AI Platform</h1>
        <p>Enterprise IoT Device Management with AI Anomaly Detection</p>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h3>Total Devices</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.total_devices || 0}</p>
        </div>
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h3>Online Devices</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0, color: '#4caf50' }}>{stats.online_devices || 0}</p>
        </div>
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h3>Telemetry Points</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.total_telemetry || 0}</p>
        </div>
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h3>Anomalies</h3>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0, color: '#ff6b6b' }}>{stats.anomalies_count || 0}</p>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={registerDevice} style={{ 
          background: '#4caf50', 
          color: 'white', 
          padding: '10px 20px',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}>
          + Register Device
        </button>
        <button onClick={sendTestTelemetry} style={{ 
          background: '#2196f3', 
          color: 'white', 
          padding: '10px 20px',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}>
          Send Test Telemetry
        </button>
      </div>

      {/* Devices and Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Devices List */}
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h2>📱 Connected Devices</h2>
          {devices.length === 0 ? (
            <p>No devices registered. Click "Register Device" to add one.</p>
          ) : (
            <div>
              {devices.map(device => (
                <div 
                  key={device.device_id}
                  onClick={() => fetchTelemetry(device.device_id)}
                  style={{
                    background: selectedDevice === device.device_id ? '#1a2350' : '#0f1435',
                    padding: '15px',
                    marginBottom: '10px',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    border: selectedDevice === device.device_id ? '1px solid #667eea' : 'none'
                  }}
                >
                  <strong>{device.device_id}</strong>
                  <div style={{ fontSize: '12px', color: '#aaa', marginTop: '5px' }}>
                    Type: {device.device_type} | Status: {device.status} | Last Seen: {new Date(device.last_seen).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Telemetry Data */}
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h2>📊 Telemetry Data</h2>
          {!selectedDevice ? (
            <p>Select a device to view telemetry</p>
          ) : telemetry.length === 0 ? (
            <p>No telemetry data for {selectedDevice}. Send test telemetry to see data.</p>
          ) : (
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '12px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #333' }}>
                    <th>Time</th>
                    <th>Temp (°C)</th>
                    <th>Vibration</th>
                    <th>CPU %</th>
                  </tr>
                </thead>
                <tbody>
                  {telemetry.slice().reverse().map((t, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #333' }}>
                      <td>{new Date(t.timestamp).toLocaleTimeString()}</td>
                      <td style={{ color: t.temperature > 50 ? '#ff6b6b' : '#fff' }}>{t.temperature}</td>
                      <td style={{ color: t.vibration > 5 ? '#ff6b6b' : '#fff' }}>{t.vibration}</td>
                      <td>{t.cpu_usage}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Anomalies */}
      {anomalies.length > 0 && (
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px', marginTop: '20px' }}>
          <h2 style={{ color: '#ff6b6b' }}>⚠️ Recent Anomalies</h2>
          {anomalies.map((a, i) => (
            <div key={i} style={{ 
              background: a.type === 'critical' ? '#ff000020' : '#ffa50020',
              padding: '10px',
              marginBottom: '10px',
              borderRadius: '5px',
              borderLeft: `3px solid ${a.type === 'critical' ? '#ff0000' : '#ffa500'}`
            }}>
              <strong>{a.device_id}</strong> - {a.message}
              <div style={{ fontSize: '11px', color: '#aaa' }}>{new Date(a.timestamp).toLocaleString()}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '20px', textAlign: 'center', color: '#aaa', fontSize: '12px' }}>
        <p>EdgeSphere AI - Enterprise IoT Device Management Platform | Version 1.0.0</p>
      </div>
    </div>
  );
}

export default App;
'@
$appJs | Out-File -FilePath "web-dashboard\src\App.js" -Encoding UTF8

# index.js
$indexJs = @'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'@
$indexJs | Out-File -FilePath "web-dashboard\src\index.js" -Encoding UTF8

# index.html
$indexHtml = @'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>EdgeSphere AI - IoT Device Management</title>
</head>
<body style="margin: 0; padding: 0;">
  <div id="root"></div>
</body>
</html>
'@
$indexHtml | Out-File -FilePath "web-dashboard\public\index.html" -Encoding UTF8

Write-Host "✓ Dashboard created" -ForegroundColor Green

# Create start scripts
Write-Host "`n[4/4] Creating start scripts..." -ForegroundColor Yellow

# start_backend.ps1
$startBackend = @'
Write-Host "Starting EdgeSphere AI Backend..." -ForegroundColor Cyan
cd backend
python -m pip install --quiet fastapi uvicorn pydantic python-dotenv
python main.py
Read-Host "Press Enter to exit"
'@
$startBackend | Out-File -FilePath "start_backend.bat" -Encoding ASCII

# start_dashboard.ps1
$startDashboard = @'
@echo off
echo Starting EdgeSphere AI Dashboard...
cd web-dashboard
if not exist node_modules (
  echo Installing dependencies (first time only)...
  call npm install
)
npm start
'@
$startDashboard | Out-File -FilePath "start_dashboard.bat" -Encoding ASCII

# start_all.bat
$startAll = @'
@echo off
echo ========================================
echo    EdgeSphere AI Platform
echo ========================================
echo.
echo Starting Backend Server...
start "EdgeSphere Backend" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak >nul
echo Starting Dashboard...
start "EdgeSphere Dashboard" cmd /k "cd web-dashboard && npm start"
echo.
echo ========================================
echo Platform starting!
echo Backend: http://localhost:8000
echo Dashboard: http://localhost:3000
echo ========================================
echo.
echo Press any key to stop all services...
pause >nul
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
echo Services stopped.
'@
$startAll | Out-File -FilePath "start_all.bat" -Encoding ASCII

Write-Host "✓ Start scripts created" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ EdgeSphere AI Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the platform:" -ForegroundColor Yellow
Write-Host "  Double-click: start_all.bat" -ForegroundColor White
Write-Host ""
Write-Host "Or manually:" -ForegroundColor Yellow
Write-Host "  1. Run: start_backend.bat" -ForegroundColor Gray
Write-Host "  2. Run: start_dashboard.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "Access:" -ForegroundColor Yellow
Write-Host "  📊 Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  🔌 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  📖 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
