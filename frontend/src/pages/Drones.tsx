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
  Button
} from '@mui/material'
import { dronesApi } from '../services/api'

export default function Drones() {
  const [drones, setDrones] = useState<any[]>([])

  useEffect(() => {
    loadDrones()
  }, [])

  const loadDrones = async () => {
    try {
      const response = await dronesApi.list()
      setDrones(response.data.drones || [])
    } catch (error) {
      console.error('Failed to load drones:', error)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, any> = {
      idle: 'default',
      in_flight: 'success',
      hovering: 'info',
      landing: 'warning',
      emergency: 'error',
    }
    return colors[status] || 'default'
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
                <TableCell>{drone.battery.percentage.toFixed(1)}%</TableCell>
                <TableCell>{drone.control_mode}</TableCell>
                <TableCell>
                  <Button size="small">Details</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
