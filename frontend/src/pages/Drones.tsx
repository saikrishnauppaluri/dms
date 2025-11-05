import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  ButtonGroup,
  CircularProgress,
  Alert,
  Snackbar
} from '@mui/material'
import { dronesApi } from '../services/api'

export default function Drones() {
  const [drones, setDrones] = useState<any[]>([])
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
  }, [])

  const loadDrones = async () => {
    try {
      const response = await dronesApi.list()
      setDrones(response.data.drones || [])
    } catch (error) {
      console.error('Failed to load drones:', error)
    }
  }

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
      emergency: 'error',
      returning_home: 'warning',
    }
    return colors[status] || 'default'
  }

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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">Drones</Typography>
        <Button variant="contained" onClick={loadDrones}>
          Refresh
        </Button>
      </Box>

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
    </Box>
  )
}
