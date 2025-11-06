import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar
} from '@mui/material'
import { MapContainer, TileLayer, Marker, Polyline, Circle, Polygon } from 'react-leaflet'
import L from 'leaflet'
import { missionsApi, dronesApi } from '../services/api'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet default icon
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

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

export default function Missions() {
  const [missions, setMissions] = useState<any[]>([])
  const [drones, setDrones] = useState<any[]>([])
  const [selectedMission, setSelectedMission] = useState<any>(null)
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
  const [startDialogOpen, setStartDialogOpen] = useState(false)
  const [selectedDroneId, setSelectedDroneId] = useState<string>('')
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })

  useEffect(() => {
    loadMissions()
    loadDrones()
  }, [])

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

  const handleViewDetails = (mission: any) => {
    setSelectedMission(mission)
    setDetailsDialogOpen(true)
  }

  const handleStartMission = (mission: any) => {
    setSelectedMission(mission)
    setStartDialogOpen(true)
    setSelectedDroneId('')
  }

  const handleAssignMission = async () => {
    if (!selectedDroneId || !selectedMission) return

    try {
      await missionsApi.assign(selectedMission.id, { drone_ids: [selectedDroneId], start_immediately: false })
      await missionsApi.command(selectedMission.id, { command: 'start' })

      setSnackbar({
        open: true,
        message: `Mission "${selectedMission.name}" assigned to drone and started successfully!`,
        severity: 'success'
      })

      setStartDialogOpen(false)
      loadMissions()
      loadDrones()
    } catch (error) {
      console.error('Failed to assign mission:', error)
      setSnackbar({
        open: true,
        message: 'Failed to assign mission. Please try again.',
        severity: 'error'
      })
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, any> = {
      pending: 'default',
      active: 'success',
      paused: 'warning',
      completed: 'info',
      aborted: 'error',
    }
    return colors[status] || 'default'
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Missions
      </Typography>

      <Grid container spacing={2}>
        {missions.map((mission) => (
          <Grid item xs={12} sm={6} md={4} key={mission.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{mission.name}</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {mission.description || 'No description'}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Chip label={mission.status} color={getStatusColor(mission.status)} size="small" sx={{ mr: 1 }} />
                  <Chip label={`${mission.waypoints.length} waypoints`} size="small" variant="outlined" />
                </Box>
              </CardContent>
              <CardActions>
                <Button size="small" onClick={() => handleViewDetails(mission)}>
                  View Details
                </Button>
                <Button size="small" color="primary" onClick={() => handleStartMission(mission)}>
                  Start
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Mission Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{selectedMission?.name}</DialogTitle>
        <DialogContent>
          {selectedMission && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedMission.description || 'No description'}
              </Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Mission Information
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={
                      <Chip
                        label={selectedMission.status}
                        color={getStatusColor(selectedMission.status)}
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Total Waypoints"
                    secondary={selectedMission.waypoints.length}
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Waypoints
              </Typography>
              <List dense>
                {selectedMission.waypoints.map((wp: any, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemText
                      primary={`Waypoint ${idx + 1}`}
                      secondary={`Lat: ${wp.position.latitude.toFixed(6)}, Lon: ${wp.position.longitude.toFixed(6)}, Alt: ${wp.position.altitude}m`}
                    />
                  </ListItem>
                ))}
              </List>

              {/* Map visualization */}
              {selectedMission.waypoints.length > 0 && (
                <Box sx={{ mt: 2, height: 400 }}>
                  <MapContainer
                    center={[
                      selectedMission.waypoints[0].position.latitude,
                      selectedMission.waypoints[0].position.longitude
                    ]}
                    zoom={14}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {/* Draw flight path */}
                    <Polyline
                      positions={selectedMission.waypoints.map((wp: any) =>
                        [wp.position.latitude, wp.position.longitude] as [number, number]
                      )}
                      color="#2196f3"
                      weight={2}
                      opacity={0.6}
                      dashArray="5, 10"
                    />

                    {/* Draw waypoints */}
                    {selectedMission.waypoints.map((wp: any, idx: number) => (
                      <Marker
                        key={idx}
                        position={[wp.position.latitude, wp.position.longitude]}
                        icon={waypointIcon}
                      />
                    ))}

                    {/* Draw altitude circles */}
                    {selectedMission.waypoints.map((wp: any, idx: number) => (
                      <Circle
                        key={`circle-${idx}`}
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

                    {/* Draw geo-fence zones if any */}
                    {selectedMission.geofence_zones && selectedMission.geofence_zones.map((zone: any, idx: number) => {
                      const zoneColor = zone.action === 'rth' ? '#f44336' : zone.action === 'land' ? '#ff9800' : '#ffc107'

                      if (zone.type === 'circle') {
                        const center = zone.coordinates[0]
                        const radius = center.altitude || 100

                        return (
                          <Circle
                            key={`geofence-circle-${idx}`}
                            center={[center.latitude, center.longitude]}
                            radius={radius}
                            pathOptions={{
                              color: zoneColor,
                              fillColor: zoneColor,
                              fillOpacity: 0.15,
                              weight: 2,
                              dashArray: '10, 5',
                            }}
                          />
                        )
                      } else if (zone.type === 'polygon') {
                        const polygonPositions = zone.coordinates.map((coord: any) =>
                          [coord.latitude, coord.longitude] as [number, number]
                        )

                        return (
                          <Polygon
                            key={`geofence-polygon-${idx}`}
                            positions={polygonPositions}
                            pathOptions={{
                              color: zoneColor,
                              fillColor: zoneColor,
                              fillOpacity: 0.15,
                              weight: 2,
                              dashArray: '10, 5',
                            }}
                          />
                        )
                      }
                      return null
                    })}
                  </MapContainer>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Start Mission Dialog */}
      <Dialog
        open={startDialogOpen}
        onClose={() => setStartDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Assign Mission to Drone</DialogTitle>
        <DialogContent>
          {selectedMission && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body1" gutterBottom>
                Mission: <strong>{selectedMission.name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedMission.waypoints.length} waypoints
              </Typography>

              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Select Drone</InputLabel>
                <Select
                  value={selectedDroneId}
                  onChange={(e) => setSelectedDroneId(e.target.value)}
                  label="Select Drone"
                >
                  {drones
                    .filter(drone => drone.status === 'idle' || drone.status === 'landed')
                    .map((drone) => (
                      <MenuItem key={drone.id} value={drone.id}>
                        {drone.name} - {drone.status} (Battery: {drone.battery?.percentage?.toFixed(0) || 0}%)
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>

              {drones.filter(d => d.status === 'idle' || d.status === 'landed').length === 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  No available drones. All drones are currently busy or not in idle/landed state.
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStartDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAssignMission}
            variant="contained"
            color="primary"
            disabled={!selectedDroneId}
          >
            Assign & Start
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
