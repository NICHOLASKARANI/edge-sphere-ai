import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Dashboard from './pages/Dashboard';
import DeviceManagement from './pages/DeviceManagement';
import Analytics from './pages/Analytics';
import OTAManagement from './pages/OTAManagement';
import PredictiveMaintenance from './pages/PredictiveMaintenance';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { useWebSocket } from './hooks/useWebSocket';
import { useDeviceStore } from './stores/deviceStore';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00A8FF',
    },
    secondary: {
      main: '#FF6B6B',
    },
    background: {
      default: '#0A0E27',
      paper: '#141B3D',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          background: 'linear-gradient(135deg, #141B3D 0%, #0F1435 100%)',
        },
      },
    },
  },
});

const App: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { devices, fetchDevices } = useDeviceStore();
  const { isConnected, telemetryData } = useWebSocket();

  useEffect(() => {
    fetchDevices();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Sidebar open={isSidebarOpen} onToggle={() => setIsSidebarOpen(!isSidebarOpen)} />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              marginLeft: isSidebarOpen ? '240px' : '72px',
              transition: 'margin-left 0.3s',
              minHeight: '100vh',
            }}
          >
            <Header connectionStatus={isConnected} deviceCount={devices.length} />
            <Box sx={{ p: 3 }}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard telemetryData={telemetryData} />} />
                <Route path="/devices" element={<DeviceManagement devices={devices} />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/ota" element={<OTAManagement />} />
                <Route path="/predictive-maintenance" element={<PredictiveMaintenance />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;