import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip
} from '@mui/material'
import { scenariosApi, fleetApi } from '../services/api'

export default function Scenarios() {
  const [scenarios, setScenarios] = useState<any[]>([])
  const [loading, setLoading] = useState<string | null>(null)

  useEffect(() => {
    loadScenarios()
  }, [])

  const loadScenarios = async () => {
    try {
      const response = await scenariosApi.list()
      setScenarios(response.data.scenarios || [])
    } catch (error) {
      console.error('Failed to load scenarios:', error)
    }
  }

  const handleLoadScenario = async (scenarioId: string) => {
    try {
      setLoading(scenarioId)
      await scenariosApi.load(scenarioId)
      await fleetApi.start()
      alert('Scenario loaded and started successfully!')
    } catch (error) {
      console.error('Failed to load scenario:', error)
      alert('Failed to load scenario')
    } finally {
      setLoading(null)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Pre-built Scenarios
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Select a scenario to quickly set up and test the DMS simulator
      </Typography>

      <Grid container spacing={2}>
        {scenarios.map((scenario) => (
          <Grid item xs={12} sm={6} md={4} key={scenario.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {scenario.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {scenario.description}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip label={`${scenario.num_drones} drones`} size="small" />
                  <Chip
                    label={`~${Math.floor(scenario.expected_duration / 60)} min`}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  color="primary"
                  variant="contained"
                  onClick={() => handleLoadScenario(scenario.id)}
                  disabled={loading === scenario.id}
                >
                  {loading === scenario.id ? 'Loading...' : 'Load Scenario'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
