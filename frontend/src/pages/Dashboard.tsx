import { useEffect, useState } from 'react'
import { Grid, Paper, Typography, Box } from '@mui/material'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import { telemetryApi, fleetApi } from '../services/api'
import wsService from '../services/websocket'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

export default function Dashboard() {
  const [telemetry, setTelemetry] = useState<any>({})
  const [fleetStatus, setFleetStatus] = useState<any>({})

  useEffect(() => {
    // Fetch initial data
    loadTelemetry()
    loadFleetStatus()

    // Connect WebSocket
    wsService.connect()
    wsService.on('telemetry', (data: any) => {
      setTelemetry(data)
    })

    return () => {
      wsService.disconnect()
    }
  }, [])

  const loadTelemetry = async () => {
    try {
      const response = await telemetryApi.getAll()
      setTelemetry(response.data.telemetry || {})
    } catch (error) {
      console.error('Failed to load telemetry:', error)
    }
  }

  const loadFleetStatus = async () => {
    try {
      const response = await fleetApi.getStatus()
      setFleetStatus(response.data)
    } catch (error) {
      console.error('Failed to load fleet status:', error)
    }
  }

  const dronePositions = Object.entries(telemetry).map(([id, data]: [string, any]) => ({
    id,
    position: [data.position.latitude, data.position.longitude] as [number, number],
    altitude: data.position.altitude,
    battery: data.battery.percentage,
    status: data.status,
  }))

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Total Drones</Typography>
            <Typography variant="h3">{fleetStatus.total_drones || 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Active Drones</Typography>
            <Typography variant="h3">{fleetStatus.active_drones || 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Active Missions</Typography>
            <Typography variant="h3">{fleetStatus.active_missions || 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Simulation</Typography>
            <Typography variant="h3" color={fleetStatus.is_running ? 'success.main' : 'error.main'}>
              {fleetStatus.is_running ? 'Running' : 'Stopped'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <MapContainer
          center={[37.7749, -122.4194]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {dronePositions.map((drone) => (
            <Marker key={drone.id} position={drone.position}>
              <Popup>
                <div>
                  <strong>Drone {drone.id.substring(0, 8)}</strong>
                  <br />
                  Status: {drone.status}
                  <br />
                  Altitude: {drone.altitude.toFixed(1)} m
                  <br />
                  Battery: {drone.battery.toFixed(1)}%
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </Paper>
    </Box>
  )
}
