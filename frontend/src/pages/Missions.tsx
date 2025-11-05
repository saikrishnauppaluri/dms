import { useEffect, useState } from 'react'
import { Box, Typography, Paper, Grid, Card, CardContent, CardActions, Button, Chip } from '@mui/material'
import { missionsApi } from '../services/api'

export default function Missions() {
  const [missions, setMissions] = useState<any[]>([])

  useEffect(() => {
    loadMissions()
  }, [])

  const loadMissions = async () => {
    try {
      const response = await missionsApi.list()
      setMissions(response.data.missions || [])
    } catch (error) {
      console.error('Failed to load missions:', error)
    }
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
                  <Chip label={mission.status} size="small" sx={{ mr: 1 }} />
                  <Chip label={`${mission.waypoints.length} waypoints`} size="small" variant="outlined" />
                </Box>
              </CardContent>
              <CardActions>
                <Button size="small">View Details</Button>
                <Button size="small" color="primary">
                  Start
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
