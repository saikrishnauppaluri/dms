import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider
} from '@mui/material'
import { eventsApi } from '../services/api'
import { format } from 'date-fns'

export default function Events() {
  const [events, setEvents] = useState<any[]>([])

  useEffect(() => {
    loadEvents()
    const interval = setInterval(loadEvents, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const loadEvents = async () => {
    try {
      const response = await eventsApi.list({ page_size: 50 })
      setEvents(response.data.events || [])
    } catch (error) {
      console.error('Failed to load events:', error)
    }
  }

  const getSeverityColor = (severity: string): any => {
    const colors: Record<string, any> = {
      debug: 'default',
      info: 'info',
      warning: 'warning',
      error: 'error',
      critical: 'error',
    }
    return colors[severity] || 'default'
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Events & Alerts
      </Typography>

      <Paper>
        <List>
          {events.map((event, index) => (
            <div key={event.id}>
              <ListItem>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={event.severity}
                        color={getSeverityColor(event.severity)}
                        size="small"
                      />
                      <Typography variant="subtitle1">{event.title}</Typography>
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2" color="text.secondary">
                        {event.description || 'No description'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {format(new Date(event.created_at), 'PPpp')}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
              {index < events.length - 1 && <Divider />}
            </div>
          ))}
        </List>
      </Paper>
    </Box>
  )
}
