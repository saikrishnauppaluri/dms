import { useEffect, useState } from 'react'
import { Grid, Paper, Typography, Box } from '@mui/material'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet'
import L from 'leaflet'
import { telemetryApi, fleetApi, missionsApi, dronesApi } from '../services/api'
import wsService from '../services/websocket'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Custom icons for waypoints
const waypointIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const currentWaypointIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const completedWaypointIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const homeIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

export default function Dashboard() {
  const [telemetry, setTelemetry] = useState<any>({})
  const [fleetStatus, setFleetStatus] = useState<any>({})
  const [missions, setMissions] = useState<any[]>([])
  const [drones, setDrones] = useState<any[]>([])

  useEffect(() => {
    // Fetch initial data
    loadTelemetry()
    loadFleetStatus()
    loadMissions()
    loadDrones()

    // Refresh missions and drones periodically
    const interval = setInterval(() => {
      loadMissions()
      loadDrones()
    }, 5000)

    // Connect WebSocket
    wsService.connect()
    wsService.on('telemetry', (data: any) => {
      setTelemetry(data)
    })

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

  const loadMissions = async () => {
    try {
      const response = await missionsApi.list()
      setMissions(response.data.missions || [])
    } catch (error) {
      console.error('Failed to load missions:', error)
    }
  }

  const loadDrones = async () => {
    try {
      const response = await dronesApi.list()
      setDrones(response.data.drones || [])
    } catch (error) {
      console.error('Failed to load drones:', error)
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

          {/* Render drone markers */}
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

          {/* Render mission waypoints and flight paths */}
          {missions
            .filter(mission => mission.status === 'active' || mission.status === 'in_progress')
            .map((mission) => {
              const drone = drones.find(d => mission.assigned_drone_ids?.includes(d.id))
              const currentWaypointIndex = drone?.current_waypoint_index ?? mission.current_waypoint ?? 0

              // Create flight path coordinates
              const flightPath = mission.waypoints.map((wp: any) => [
                wp.position.latitude,
                wp.position.longitude
              ])

              // Add home position at the start
              if (mission.home_position) {
                flightPath.unshift([
                  mission.home_position.latitude,
                  mission.home_position.longitude
                ])
              }

              return (
                <div key={mission.id}>
                  {/* Home position marker */}
                  {mission.home_position && (
                    <Marker
                      position={[mission.home_position.latitude, mission.home_position.longitude]}
                      icon={homeIcon}
                    >
                      <Popup>
                        <div>
                          <strong>Home Position</strong>
                          <br />
                          Mission: {mission.name}
                          <br />
                          Altitude: {mission.home_position.altitude.toFixed(1)} m
                        </div>
                      </Popup>
                    </Marker>
                  )}

                  {/* Flight path polyline */}
                  <Polyline
                    positions={flightPath}
                    color="#3388ff"
                    weight={3}
                    opacity={0.7}
                    dashArray="10, 10"
                  />

                  {/* Waypoint markers */}
                  {mission.waypoints.map((waypoint: any, index: number) => {
                    let icon = waypointIcon
                    if (index < currentWaypointIndex) {
                      icon = completedWaypointIcon
                    } else if (index === currentWaypointIndex) {
                      icon = currentWaypointIcon
                    }

                    return (
                      <Marker
                        key={`${mission.id}-wp-${index}`}
                        position={[waypoint.position.latitude, waypoint.position.longitude]}
                        icon={icon}
                      >
                        <Popup>
                          <div>
                            <strong>Waypoint {waypoint.sequence}</strong>
                            <br />
                            Mission: {mission.name}
                            <br />
                            Altitude: {waypoint.position.altitude.toFixed(1)} m
                            <br />
                            {waypoint.speed && `Speed: ${waypoint.speed.toFixed(1)} m/s`}
                            {waypoint.speed && <br />}
                            {waypoint.loiter_time > 0 && `Loiter: ${waypoint.loiter_time}s`}
                            {waypoint.loiter_time > 0 && <br />}
                            Status: {index < currentWaypointIndex ? 'Completed' : index === currentWaypointIndex ? 'Current' : 'Pending'}
                            {waypoint.actions.length > 0 && (
                              <>
                                <br />
                                Actions: {waypoint.actions.map((a: any) => a.type).join(', ')}
                              </>
                            )}
                          </div>
                        </Popup>
                      </Marker>
                    )
                  })}
                </div>
              )
            })}
        </MapContainer>
      </Paper>
    </Box>
  )
}
