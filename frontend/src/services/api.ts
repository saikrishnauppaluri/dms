import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Drones
export const dronesApi = {
  list: () => api.get('/drones'),
  get: (id: string) => api.get(`/drones/${id}`),
  create: (data: any) => api.post('/drones', data),
  update: (id: string, data: any) => api.patch(`/drones/${id}`, data),
  delete: (id: string) => api.delete(`/drones/${id}`),
  sendCommand: (id: string, command: any) => api.post(`/drones/${id}/command`, command),
  getTelemetry: (id: string) => api.get(`/drones/${id}/telemetry`),
}

// Missions
export const missionsApi = {
  list: () => api.get('/missions'),
  get: (id: string) => api.get(`/missions/${id}`),
  create: (data: any) => api.post('/missions', data),
  update: (id: string, data: any) => api.patch(`/missions/${id}`, data),
  delete: (id: string) => api.delete(`/missions/${id}`),
  assign: (id: string, data: any) => api.post(`/missions/${id}/assign`, data),
  command: (id: string, command: any) => api.post(`/missions/${id}/command`, command),
  getProgress: (id: string) => api.get(`/missions/${id}/progress`),
}

// Telemetry
export const telemetryApi = {
  getAll: () => api.get('/telemetry'),
  get: (droneId: string) => api.get(`/telemetry/${droneId}`),
}

// Events
export const eventsApi = {
  list: (params?: any) => api.get('/events', { params }),
  listAlerts: (params?: any) => api.get('/events/alerts', { params }),
}

// Fleet
export const fleetApi = {
  getStatus: () => api.get('/fleet/status'),
  start: () => api.post('/fleet/start'),
  stop: () => api.post('/fleet/stop'),
  setSpeed: (speed: number) => api.post('/fleet/speed', { speed }),
}

// Scenarios
export const scenariosApi = {
  list: () => api.get('/scenarios'),
  get: (id: string) => api.get(`/scenarios/${id}`),
  load: (id: string) => api.post(`/scenarios/${id}/load`),
}

// Edge-AI
export const aiApi = {
  enable: (droneId: string, modelName: string) =>
    api.post(`/ai/${droneId}/enable`, { model_name: modelName }),
  disable: (droneId: string) => api.delete(`/ai/${droneId}/disable`),
  getStatistics: (droneId: string) => api.get(`/ai/${droneId}/statistics`),
  getAllStatistics: () => api.get('/ai/statistics/all'),
  listModels: () => api.get('/ai/models'),
}

export default api
