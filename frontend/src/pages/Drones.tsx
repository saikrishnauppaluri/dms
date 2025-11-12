import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
<<<<<<< HEAD
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Divider
=======
  ButtonGroup,
  CircularProgress,
  Alert,
  Snackbar
>>>>>>> fix-drone-simulation-waypoints
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet'
import L from 'leaflet'
import { dronesApi, missionsApi, telemetryApi } from '../services/api'
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
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="#2196f3" opacity="0.3" stroke="#2196f3" stroke-width="2"/>
      <circle cx="12" cy="12" r="4" fill="#2196f3"/>
    </svg>
  `,
  className: 'waypoint-icon',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
})

export default function Drones() {
  const [drones, setDrones] = useState<any[]>([])
<<<<<<< HEAD
  const [telemetry, setTelemetry] = useState<any>({})
  const [missions, setMissions] = useState<any>({})
  const [selectedDrone, setSelectedDrone] = useState<any>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    loadDrones()
    loadTelemetry()

    // Connect WebSocket for real-time updates
    wsService.connect()
    wsService.on('telemetry', (data: any) => {
      setTelemetry(data)
    })

    const interval = setInterval(() => {
      loadDrones()
      loadTelemetry()
    }, 2000)

    return () => {
      clearInterval(interval)
      wsService.disconnect()
    }
=======
  const [loadingCommand, setLoadingCommand] = useState<Record<string, boolean>>({})
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })

  useEffect(() => {
    loadDrones()
    // Refresh drone list periodically
    const interval = setInterval(loadDrones, 2000)
    return () => clearInterval(interval)
>>>>>>> fix-drone-simulation-waypoints
  }, [])

  const loadDrones = async () => {
    try {
      const response = await dronesApi.list()
      const dronesList = response.data.drones || []
      setDrones(dronesList)

      // Auto-load missions for drones that have active missions
      dronesList.forEach((drone: any) => {
        if (drone.mission_id) {
          loadMission(drone.mission_id)
        }
      })
    } catch (error) {
      console.error('Failed to load drones:', error)
    }
  }

<<<<<<< HEAD
  const loadTelemetry = async () => {
    try {
      const response = await telemetryApi.getAll()
      setTelemetry(response.data.telemetry || {})
    } catch (error) {
      console.error('Failed to load telemetry:', error)
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
=======
  const sendCommand = async (droneId: string, command: string, params?: any) => {
    const loadingKey = `${droneId}-${command}`
    setLoadingCommand(prev => ({ ...prev, [loadingKey]: true }))

    try {
      await dronesApi.sendCommand(droneId, { command, ...params })
      setSnackbar({
        open: true,
        message: `Command "${command}" sent successfully`,
        severity: 'success'
      })
      // Reload drones to update status
      setTimeout(loadDrones, 500)
    } catch (error: any) {
      console.error(`Failed to send command ${command}:`, error)
      setSnackbar({
        open: true,
        message: `Failed to send command: ${error.response?.data?.detail || error.message}`,
        severity: 'error'
      })
    } finally {
      setLoadingCommand(prev => ({ ...prev, [loadingKey]: false }))
>>>>>>> fix-drone-simulation-waypoints
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, any> = {
      idle: 'default',
      armed: 'warning',
      taking_off: 'info',
      in_flight: 'success',
      hovering: 'info',
      landing: 'warning',
      landed: 'default',
<<<<<<< HEAD
      rth: 'warning',
      emergency: 'error',
      offline: 'default',
=======
      emergency: 'error',
      returning_home: 'warning',
>>>>>>> fix-drone-simulation-waypoints
    }
    return colors[status] || 'default'
  }

<<<<<<< HEAD
  const handleDroneClick = async (drone: any) => {
    setSelectedDrone(drone)
    setDrawerOpen(true)

    // Load mission if drone has one
    if (drone.mission_id) {
      await loadMission(drone.mission_id)
    }
  }

  const handleTakeoff = async (droneId: string) => {
    try {
      await dronesApi.sendCommand(droneId, {
        command: 'takeoff',
        parameters: { altitude: 50.0 }
      })
      alert('Takeoff command sent successfully!')
      await loadDrones()
    } catch (error) {
      console.error('Failed to send takeoff command:', error)
      alert('Failed to send takeoff command')
    }
  }

  const handleRTH = async (droneId: string) => {
    try {
      await dronesApi.sendCommand(droneId, {
        command: 'rth',
        parameters: { reason: 'Manual' }
      })
      alert('Return to Home command sent successfully!')
      await loadDrones()
    } catch (error) {
      console.error('Failed to send RTH command:', error)
      alert('Failed to send RTH command')
    }
  }

  const handleLand = async (droneId: string) => {
    try {
      await dronesApi.sendCommand(droneId, {
        command: 'land',
        parameters: {}
      })
      alert('Land command sent successfully!')
      await loadDrones()
    } catch (error) {
      console.error('Failed to send land command:', error)
      alert('Failed to send land command')
    }
  }

  // Calculate map center based on drones
  const mapCenter: [number, number] = drones.length > 0
    ? [drones[0].position.latitude, drones[0].position.longitude]
    : [37.7749, -122.4194]

  // Get drone positions from telemetry
  const dronePositions = drones.map(drone => {
    const tel = telemetry[drone.id]
    return {
      id: drone.id,
      name: drone.name,
      position: tel?.position || drone.position,
      altitude: tel?.position.altitude || drone.position.altitude,
      battery: tel?.battery.percentage || drone.battery.percentage,
      status: tel?.status || drone.status,
      heading: tel?.attitude?.yaw || 0,
      mission_id: drone.mission_id,
      control_mode: drone.control_mode,
    }
  })
=======
  const canArm = (drone: any) => {
    return drone.status === 'idle' && drone.battery.percentage > 20
  }

  const canTakeoff = (drone: any) => {
    return drone.status === 'armed' || drone.status === 'landed'
  }

  const canLand = (drone: any) => {
    return ['in_flight', 'hovering', 'taking_off'].includes(drone.status)
  }

  const canRTH = (drone: any) => {
    return ['in_flight', 'hovering'].includes(drone.status)
  }

  const isLoading = (droneId: string, command: string) => {
    return loadingCommand[`${droneId}-${command}`] || false
  }
>>>>>>> fix-drone-simulation-waypoints

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">Drones</Typography>
        <Button variant="contained" onClick={loadDrones}>
          Refresh
        </Button>
      </Box>

<<<<<<< HEAD
      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Drones
              </Typography>
              <Typography variant="h4">{drones.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                In Flight
              </Typography>
              <Typography variant="h4" color="success.main">
                {drones.filter(d => d.status === 'in_flight' || d.status === 'hovering').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Idle
              </Typography>
              <Typography variant="h4">
                {drones.filter(d => d.status === 'idle' || d.status === 'landed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Emergency
              </Typography>
              <Typography variant="h4" color="error.main">
                {drones.filter(d => d.status === 'emergency').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Map */}
      <Paper sx={{ flexGrow: 1, overflow: 'hidden', position: 'relative' }}>
        <MapContainer
          center={mapCenter}
          zoom={14}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Draw drones */}
          {dronePositions.map((drone) => (
            <Marker
              key={drone.id}
              position={[drone.position.latitude, drone.position.longitude]}
              icon={createDroneIcon(drone.status, drone.heading)}
              eventHandlers={{
                click: () => handleDroneClick(drones.find(d => d.id === drone.id))
              }}
            >
              <Popup>
                <div>
                  <strong>{drone.name}</strong>
                  <br />
                  Status: <Chip label={drone.status} size="small" color={getStatusColor(drone.status)} />
                  <br />
                  Altitude: {drone.altitude.toFixed(1)} m
                  <br />
                  Battery: {drone.battery.toFixed(1)}%
                  <br />
                  Mode: {drone.control_mode}
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Draw waypoints for drones with active missions */}
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
                        Altitude: {wp.position.altitude} m
                        <br />
                        Speed: {wp.speed || 'default'} m/s
                      </div>
                    </Popup>
                  </Marker>
                ))}

                {/* Draw altitude circles */}
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

      {/* Drone Details Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 350, p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Drone Details</Typography>
            <IconButton onClick={() => setDrawerOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>

          {selectedDrone && (
            <>
              <Divider sx={{ mb: 2 }} />

              <List>
                <ListItem>
                  <ListItemText
                    primary="Name"
                    secondary={selectedDrone.name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Model"
                    secondary={selectedDrone.spec.model}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={
                      <Chip
                        label={selectedDrone.status}
                        color={getStatusColor(selectedDrone.status)}
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Battery"
                    secondary={`${selectedDrone.battery.percentage.toFixed(1)}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Control Mode"
                    secondary={selectedDrone.control_mode}
                  />
                </ListItem>

                {telemetry[selectedDrone.id] && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    <ListItem>
                      <ListItemText
                        primary="Position"
                        secondary={`${telemetry[selectedDrone.id].position.latitude.toFixed(6)}, ${telemetry[selectedDrone.id].position.longitude.toFixed(6)}`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Altitude"
                        secondary={`${telemetry[selectedDrone.id].position.altitude.toFixed(1)} m`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Speed"
                        secondary={`${Math.sqrt(
                          Math.pow(telemetry[selectedDrone.id].velocity.vx, 2) +
                          Math.pow(telemetry[selectedDrone.id].velocity.vy, 2)
                        ).toFixed(1)} m/s`}
                      />
                    </ListItem>
                  </>
                )}

                {selectedDrone.mission_id && missions[selectedDrone.mission_id] && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    <ListItem>
                      <ListItemText
                        primary="Mission"
                        secondary={missions[selectedDrone.mission_id].name}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Waypoints"
                        secondary={`${missions[selectedDrone.mission_id].waypoints?.length || 0} total`}
                      />
                    </ListItem>
                    {telemetry[selectedDrone.id]?.current_waypoint !== null && (
                      <ListItem>
                        <ListItemText
                          primary="Current Waypoint"
                          secondary={`${telemetry[selectedDrone.id].current_waypoint + 1} of ${missions[selectedDrone.mission_id].waypoints?.length || 0}`}
                        />
                      </ListItem>
                    )}
                  </>
                )}
              </List>

              <Divider sx={{ my: 2 }} />

              {/* Drone Control Buttons */}
              <Typography variant="h6" sx={{ mb: 2 }}>
                Drone Controls
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button
                  variant="contained"
                  color="success"
                  fullWidth
                  onClick={() => handleTakeoff(selectedDrone.id)}
                  disabled={selectedDrone.status !== 'idle' && selectedDrone.status !== 'landed'}
                >
                  Takeoff
                </Button>
                <Button
                  variant="contained"
                  color="warning"
                  fullWidth
                  onClick={() => handleRTH(selectedDrone.id)}
                  disabled={selectedDrone.status !== 'in_flight' && selectedDrone.status !== 'hovering'}
                >
                  Return to Home (RTH)
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  fullWidth
                  onClick={() => handleLand(selectedDrone.id)}
                  disabled={selectedDrone.status !== 'in_flight' && selectedDrone.status !== 'hovering'}
                >
                  Land
                </Button>
              </Box>

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setDrawerOpen(false)}
                >
                  Close
                </Button>
              </Box>
            </>
          )}
        </Box>
      </Drawer>
=======
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Battery</TableCell>
              <TableCell>Control Mode</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {drones.map((drone) => (
              <TableRow key={drone.id}>
                <TableCell>{drone.name}</TableCell>
                <TableCell>{drone.spec.model}</TableCell>
                <TableCell>
                  <Chip label={drone.status} color={getStatusColor(drone.status)} size="small" />
                </TableCell>
                <TableCell>
                  <Chip
                    label={`${drone.battery.percentage.toFixed(1)}%`}
                    color={drone.battery.percentage < 20 ? 'error' : drone.battery.percentage < 50 ? 'warning' : 'success'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{drone.control_mode}</TableCell>
                <TableCell>
                  <ButtonGroup size="small" variant="outlined">
                    <Button
                      onClick={() => sendCommand(drone.id, 'arm')}
                      disabled={!canArm(drone) || isLoading(drone.id, 'arm')}
                      color="warning"
                    >
                      {isLoading(drone.id, 'arm') ? <CircularProgress size={16} /> : 'ARM'}
                    </Button>
                    <Button
                      onClick={() => sendCommand(drone.id, 'takeoff', { altitude: 50 })}
                      disabled={!canTakeoff(drone) || isLoading(drone.id, 'takeoff')}
                      color="success"
                    >
                      {isLoading(drone.id, 'takeoff') ? <CircularProgress size={16} /> : 'TAKEOFF'}
                    </Button>
                    <Button
                      onClick={() => sendCommand(drone.id, 'land')}
                      disabled={!canLand(drone) || isLoading(drone.id, 'land')}
                      color="error"
                    >
                      {isLoading(drone.id, 'land') ? <CircularProgress size={16} /> : 'LAND'}
                    </Button>
                    <Button
                      onClick={() => sendCommand(drone.id, 'rth', { reason: 'User command' })}
                      disabled={!canRTH(drone) || isLoading(drone.id, 'rth')}
                      color="info"
                    >
                      {isLoading(drone.id, 'rth') ? <CircularProgress size={16} /> : 'RTH'}
                    </Button>
                  </ButtonGroup>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
>>>>>>> fix-drone-simulation-waypoints
    </Box>
  )
}
