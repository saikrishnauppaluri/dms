import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Alert,
  Paper,
  Stack
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import { scenariosApi, fleetApi } from '../services/api'

export default function Scenarios() {
  const [scenarios, setScenarios] = useState<any[]>([])
  const [loading, setLoading] = useState<string | null>(null)
  const [fleetStatus, setFleetStatus] = useState<any>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  useEffect(() => {
    loadScenarios()
    loadFleetStatus()

    const interval = setInterval(loadFleetStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const loadScenarios = async () => {
    try {
      const response = await scenariosApi.list()
      setScenarios(response.data.scenarios || [])
    } catch (error) {
      console.error('Failed to load scenarios:', error)
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

  const handleLoadScenario = async (scenarioId: string) => {
    try {
      setLoading(scenarioId)
      setMessage(null)
      await scenariosApi.load(scenarioId)
      await fleetApi.start()
      setMessage({ type: 'success', text: 'Scenario loaded and started! Check the Drones page to see them in action.' })
      await loadFleetStatus()
    } catch (error: any) {
      console.error('Failed to load scenario:', error)
      setMessage({ type: 'error', text: `Failed to load scenario: ${error.message || 'Unknown error'}` })
    } finally {
      setLoading(null)
    }
  }

  const handleStopFleet = async () => {
    try {
      await fleetApi.stop()
      setMessage({ type: 'success', text: 'Fleet simulation stopped' })
      await loadFleetStatus()
    } catch (error: any) {
      setMessage({ type: 'error', text: `Failed to stop fleet: ${error.message || 'Unknown error'}` })
    }
  }

  const handleStartFleet = async () => {
    try {
      await fleetApi.start()
      setMessage({ type: 'success', text: 'Fleet simulation started' })
      await loadFleetStatus()
    } catch (error: any) {
      setMessage({ type: 'error', text: `Failed to start fleet: ${error.message || 'Unknown error'}` })
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          Pre-built Scenarios
        </Typography>
        {fleetStatus && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Chip
              label={fleetStatus.is_running ? 'Simulation Running' : 'Simulation Stopped'}
              color={fleetStatus.is_running ? 'success' : 'default'}
            />
            {fleetStatus.is_running ? (
              <Button
                variant="outlined"
                color="error"
                startIcon={<StopIcon />}
                onClick={handleStopFleet}
              >
                Stop Simulation
              </Button>
            ) : (
              <Button
                variant="outlined"
                color="success"
                startIcon={<PlayArrowIcon />}
                onClick={handleStartFleet}
                disabled={fleetStatus.total_drones === 0}
              >
                Start Simulation
              </Button>
            )}
          </Box>
        )}
      </Box>

      {message && (
        <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      {fleetStatus && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Drones
              </Typography>
              <Typography variant="h5">{fleetStatus.total_drones}</Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Active Drones
              </Typography>
              <Typography variant="h5" color="success.main">
                {fleetStatus.active_drones}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Active Missions
              </Typography>
              <Typography variant="h5" color="info.main">
                {fleetStatus.active_missions}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="subtitle2" color="text.secondary">
                Simulation Speed
              </Typography>
              <Typography variant="h5">{fleetStatus.sim_speed}x</Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      <Typography variant="body1" color="text.secondary" paragraph>
        Select a scenario to quickly set up and test the DMS simulator. Each scenario includes pre-configured drones and missions.
      </Typography>

      <Grid container spacing={3}>
        {scenarios.map((scenario) => (
          <Grid item xs={12} sm={6} md={4} key={scenario.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {scenario.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {scenario.description}
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  <Chip label={`${scenario.num_drones} drone${scenario.num_drones > 1 ? 's' : ''}`} size="small" color="primary" />
                  <Chip
                    label={`~${Math.floor(scenario.expected_duration / 60)} min`}
                    size="small"
                    variant="outlined"
                  />
                  {scenario.ai_model && (
                    <Chip label={`AI: ${scenario.ai_model}`} size="small" color="secondary" variant="outlined" />
                  )}
                </Stack>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  color="primary"
                  variant="contained"
                  onClick={() => handleLoadScenario(scenario.id)}
                  disabled={loading === scenario.id || fleetStatus?.is_running}
                  fullWidth
                  startIcon={<PlayArrowIcon />}
                >
                  {loading === scenario.id ? 'Loading...' : 'Load & Start'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {scenarios.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No scenarios available. Check your backend connection.
        </Alert>
      )}
    </Box>
  )
}
