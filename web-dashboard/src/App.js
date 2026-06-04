import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function App() {
  const [devices, setDevices] = useState([]);
  const [stats, setStats] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  const [newDeviceId, setNewDeviceId] = useState('');
  const [tempValue, setTempValue] = useState('25');
  const [vibValue, setVibValue] = useState('0.5');

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
    if (!newDeviceId) {
      alert('Please enter a Device ID');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/v1/devices/register`, {
        device_id: newDeviceId,
        device_type: 'ESP32',
        status: 'online',
        firmware_version: '1.0.0',
        last_seen: new Date().toISOString(),
        location: 'Factory Floor'
      });
      setNewDeviceId('');
      fetchData();
      alert('Device registered successfully!');
    } catch (error) {
      alert('Error registering device');
    }
  };

  const sendTelemetry = async (deviceId) => {
    const temp = parseFloat(tempValue);
    const vib = parseFloat(vibValue);
    
    try {
      await axios.post(`${API_URL}/api/v1/telemetry`, {
        device_id: deviceId,
        temperature: temp,
        humidity: 50,
        vibration: vib,
        cpu_usage: Math.floor(Math.random() * 50) + 20,
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
        <h1 style={{ margin: 0 }}>EdgeSphere AI Platform</h1>
        <p>Enterprise IoT Device Management with AI Anomaly Detection</p>
        <p style={{ fontSize: '12px', marginTop: '10px' }}>
          🟢 Backend Status: Connected to {API_URL}
        </p>
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

      {/* Register Device Section */}
      <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
        <h2>Register New Device</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            placeholder="Device ID (e.g., ESP32_001)"
            value={newDeviceId}
            onChange={(e) => setNewDeviceId(e.target.value)}
            style={{ padding: '10px', borderRadius: '5px', border: 'none', flex: 1 }}
          />
          <button onClick={registerDevice} style={{ 
            background: '#4caf50', 
            color: 'white', 
            padding: '10px 20px',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}>
            Register Device
          </button>
        </div>
      </div>

      {/* Send Telemetry Section */}
      {selectedDevice && (
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
          <h2>Send Telemetry to: {selectedDevice}</h2>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <input 
              type="number" 
              placeholder="Temperature (°C)"
              value={tempValue}
              onChange={(e) => setTempValue(e.target.value)}
              style={{ padding: '10px', borderRadius: '5px', border: 'none', width: '150px' }}
            />
            <input 
              type="number" 
              placeholder="Vibration (mm/s)"
              value={vibValue}
              onChange={(e) => setVibValue(e.target.value)}
              style={{ padding: '10px', borderRadius: '5px', border: 'none', width: '150px' }}
            />
            <button onClick={() => sendTelemetry(selectedDevice)} style={{ 
              background: '#2196f3', 
              color: 'white', 
              padding: '10px 20px',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}>
              Send Telemetry
            </button>
          </div>
        </div>
      )}

      {/* Devices and Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Devices List */}
        <div style={{ background: '#141b3d', padding: '20px', borderRadius: '10px' }}>
          <h2>Connected Devices</h2>
          {devices.length === 0 ? (
            <p>No devices registered. Register a device above.</p>
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
                    border: selectedDevice === device.device_id ? '2px solid #667eea' : '1px solid #2a3450'
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
          <h2>Telemetry Data</h2>
          {!selectedDevice ? (
            <p>Select a device to view telemetry</p>
          ) : telemetry.length === 0 ? (
            <p>No telemetry data for {selectedDevice}. Send telemetry to see data.</p>
          ) : (
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #333' }}>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Time</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Temp</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Vibration</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>CPU</th>
                  </tr>
                </thead>
                <tbody>
                  {telemetry.slice().reverse().map((t, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #333' }}>
                      <td style={{ padding: '8px' }}>{new Date(t.timestamp).toLocaleTimeString()}</td>
                      <td style={{ padding: '8px', color: t.temperature > 50 ? '#ff6b6b' : '#fff', fontWeight: t.temperature > 50 ? 'bold' : 'normal' }}>
                        {t.temperature}°C
                      </td>
                      <td style={{ padding: '8px', color: t.vibration > 5 ? '#ff6b6b' : '#fff', fontWeight: t.vibration > 5 ? 'bold' : 'normal' }}>
                        {t.vibration} mm/s
                      </td>
                      <td style={{ padding: '8px' }}>{t.cpu_usage}%</td>
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
          <h2 style={{ color: '#ff6b6b' }}>AI Detected Anomalies</h2>
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
        <p>EdgeSphere AI - Enterprise IoT Device Management Platform | AI-Powered Anomaly Detection | Version 1.0.0</p>
        <p>📍 Minewing Technologies - Smart Manufacturing Solution</p>
      </div>
    </div>
  );
}

export default App;
