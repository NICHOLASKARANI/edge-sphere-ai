import React from 'react';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import DeviceMap from '../components/DeviceMap';
import AlertsWidget from '../components/AlertsWidget';
import { useDeviceStore } from '../stores/deviceStore';
import { useAnalyticsStore } from '../stores/analyticsStore';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend);

interface DashboardProps {
  telemetryData: any[];
}

const Dashboard: React.FC<DashboardProps> = ({ telemetryData }) => {
  const { devices, deviceStats } = useDeviceStore();
  const { anomalyStats, healthScores } = useAnalyticsStore();

  const telemetryChartData = {
    labels: telemetryData.slice(-20).map(d => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Temperature (°C)',
        data: telemetryData.slice(-20).map(d => d.temperature),
        borderColor: 'rgb(0, 168, 255)',
        backgroundColor: 'rgba(0, 168, 255, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Vibration (mm/s)',
        data: telemetryData.slice(-20).map(d => d.vibration),
        borderColor: 'rgb(255, 107, 107)',
        backgroundColor: 'rgba(255, 107, 107, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const deviceStatusData = {
    labels: ['Online', 'Offline', 'Maintenance', 'Error'],
    datasets: [
      {
        data: [
          deviceStats.online,
          deviceStats.offline,
          deviceStats.maintenance,
          deviceStats.error,
        ],
        backgroundColor: ['#00A8FF', '#6B7280', '#FFB347', '#FF6B6B'],
        borderWidth: 0,
      },
    ],
  };

  const anomalyChartData = {
    labels: anomalyStats.map(s => s.device_id),
    datasets: [
      {
        label: 'Anomaly Score',
        data: anomalyStats.map(s => s.score),
        backgroundColor: 'rgba(255, 107, 107, 0.7)',
      },
    ],
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        EdgeSphere AI Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Total Devices
            </Typography>
            <Typography variant="h3">
              {deviceStats.total}
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Online Devices
            </Typography>
            <Typography variant="h3" color="#00A8FF">
              {deviceStats.online}
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Anomalies (24h)
            </Typography>
            <Typography variant="h3" color="#FF6B6B">
              {anomalyStats.length}
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              Avg. Health Score
            </Typography>
            <Typography variant="h3">
              {healthScores.average.toFixed(1)}%
            </Typography>
          </Paper>
        </Grid>
        
        {/* Telemetry Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Real-time Telemetry
            </Typography>
            <Line
              data={telemetryChartData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top' as const,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }}
            />
          </Paper>
        </Grid>
        
        {/* Device Status */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Device Status
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Doughnut
                data={deviceStatusData}
                options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      position: 'bottom' as const,
                    },
                  },
                }}
              />
            </Box>
          </Paper>
        </Grid>
        
        {/* Device Map */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Device Locations
            </Typography>
            <DeviceMap devices={devices} />
          </Paper>
        </Grid>
        
        {/* Anomaly Alerts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Recent Anomalies
            </Typography>
            <AlertsWidget alerts={anomalyStats} />
          </Paper>
        </Grid>
        
        {/* Anomaly Analysis */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Device Anomaly Analysis
            </Typography>
            <Bar
              data={anomalyChartData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top' as const,
                  },
                },
              }}
            />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;