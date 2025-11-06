import { useEffect, useState } from 'react'
import { Grid, Paper, Typography, Box } from '@mui/material'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet'
import L from 'leaflet'
import { telemetryApi, fleetApi, dronesApi, missionsApi } from '../services/api'
import wsService from '../services/websocket'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Create custom drone icon with different colors based on status
const createDroneIcon = (status: string, heading: number = 0) => {
  const colorMap: Record<string, string> = {
    idle: '#9e9e9e',
    armed: '#ff9800',
    taking_off: '#2196f3',
    in_flight: '#4caf50',
    hovering: '#00bcd4',
    landing: '#ff9800',
    landed: '#9e9e9e',
    rth: '#ff5722',
    emergency: '#f44336',
    offline: '#616161',
  }

  const color = colorMap[status] || '#9e9e9e'

  const svg = `
    <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
      <g transform="rotate(${heading} 20 20)">
        <!-- Drone body -->
        <circle cx="20" cy="20" r="6" fill="${color}" stroke="white" stroke-width="2"/>
        <!-- Arms -->
        <line x1="20" y1="20" x2="10" y2="10" stroke="${color}" stroke-width="2"/>
        <line x1="20" y1="20" x2="30" y2="10" stroke="${color}" stroke-width="2"/>
        <line x1="20" y1="20" x2="10" y2="30" stroke="${color}" stroke-width="2"/>
        <line x1="20" y1="20" x2="30" y2="30" stroke="${color}" stroke-width="2"/>
        <!-- Propellers -->
        <circle cx="10" cy="10" r="4" fill="${color}" opacity="0.6"/>
        <circle cx="30" cy="10" r="4" fill="${color}" opacity="0.6"/>
        <circle cx="10" cy="30" r="4" fill="${color}" opacity="0.6"/>
        <circle cx="30" cy="30" r="4" fill="${color}" opacity="0.6"/>
        <!-- Front indicator -->
        <circle cx="20" cy="14" r="2" fill="white"/>
      </g>
    </svg>
  `

  return L.divIcon({
    html: svg,
    className: 'drone-icon',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  })
}

// Waypoint icon
const waypointIcon = L.divIcon({
  html: `
    <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="#2196f3" opacity="0.3" stroke="#2196f3" stroke-width="2"/>
      <circle cx="12" cy="12" r="4" fill="#2196f3"/>
    </svg>
  `,
  className: 'waypoint-icon',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
})

export default function Dashboard() {
  const [telemetry, setTelemetry] = useState<any>({})
  const [fleetStatus, setFleetStatus] = useState<any>({})
  const [drones, setDrones] = useState<any[]>([])
  const [missions, setMissions] = useState<any>({})

  useEffect(() => {
    // Fetch initial data
    loadTelemetry()
    loadFleetStatus()
    loadDrones()

    // Connect WebSocket
    wsService.connect()
    wsService.on('telemetry', (data: any) => {
      setTelemetry(data)
    })

    // Poll for updates
    const interval = setInterval(() => {
      loadTelemetry()
      loadFleetStatus()
      loadDrones()
    }, 2000)

    return () => {
      clearInterval(interval)
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

  const loadDrones = async () => {
    try {
      const response = await dronesApi.list()
      const dronesList = response.data.drones || []
      setDrones(dronesList)

      // Load missions for drones that have active missions
      dronesList.forEach((drone: any) => {
        if (drone.mission_id) {
          loadMission(drone.mission_id)
        }
      })
    } catch (error) {
      console.error('Failed to load drones:', error)
    }
  }

  const loadMission = async (missionId: string) => {
    if (!missionId || missions[missionId]) return

    try {
      const response = await missionsApi.get(missionId)
      setMissions((prev: any) => ({
        ...prev,
        [missionId]: response.data
      }))
    } catch (error) {
      console.error('Failed to load mission:', error)
    }
  }

  // Get drone positions from telemetry merged with drone data
  const dronePositions = drones.map(drone => {
    const tel = telemetry[drone.id]
    return {
      id: drone.id,
      name: drone.name,
      position: tel?.position || drone.position,
      altitude: tel?.position.altitude || drone.position.altitude,
      battery: tel?.battery.percentage || drone.battery?.percentage || 0,
      status: tel?.status || drone.status,
      heading: tel?.attitude?.yaw || 0,
      mission_id: drone.mission_id,
    }
  })

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
          center={dronePositions.length > 0 ? [dronePositions[0].position.latitude, dronePositions[0].position.longitude] : [37.7749, -122.4194]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Draw drones with custom icons */}
          {dronePositions.map((drone) => (
            <Marker
              key={drone.id}
              position={[drone.position.latitude, drone.position.longitude]}
              icon={createDroneIcon(drone.status, drone.heading)}
            >
              <Popup>
                <div>
                  <strong>{drone.name || `Drone ${drone.id.substring(0, 8)}`}</strong>
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

          {/* Draw waypoints and flight paths for drones with active missions */}
          {dronePositions.map((drone) => {
            if (!drone.mission_id) return null

            const mission = missions[drone.mission_id]
            if (!mission || !mission.waypoints) return null

            const waypointPositions = mission.waypoints.map((wp: any) =>
              [wp.position.latitude, wp.position.longitude] as [number, number]
            )

            return (
              <div key={`mission-${drone.id}`}>
                {/* Draw flight path */}
                <Polyline
                  positions={waypointPositions}
                  color="#2196f3"
                  weight={2}
                  opacity={0.6}
                  dashArray="5, 10"
                />

                {/* Draw waypoints */}
                {mission.waypoints.map((wp: any, idx: number) => (
                  <Marker
                    key={`wp-${drone.id}-${idx}`}
                    position={[wp.position.latitude, wp.position.longitude]}
                    icon={waypointIcon}
                  >
                    <Popup>
                      <div>
                        <strong>Waypoint {idx + 1}</strong>
                        <br />
                        Mission: {mission.name}
                        <br />
                        Altitude: {wp.position.altitude} m
                        <br />
                        Speed: {wp.speed || 'default'} m/s
                      </div>
                    </Popup>
                  </Marker>
                ))}

                {/* Draw altitude circles around waypoints */}
                {mission.waypoints.map((wp: any, idx: number) => (
                  <Circle
                    key={`circle-${drone.id}-${idx}`}
                    center={[wp.position.latitude, wp.position.longitude]}
                    radius={wp.position.altitude / 2}
                    pathOptions={{
                      color: '#2196f3',
                      fillColor: '#2196f3',
                      fillOpacity: 0.05,
                      weight: 1,
                    }}
                  />
                ))}
              </div>
            )
          })}
        </MapContainer>
      </Paper>
    </Box>
  )
}
