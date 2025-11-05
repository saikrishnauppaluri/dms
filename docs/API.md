# DMS Simulator API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently using API keys. Include in header:
```
X-API-Key: your-api-key
```

## WebSocket
Real-time telemetry streaming:
```
ws://localhost:8000/ws
```

---

## Drones API

### List Drones
```http
GET /drones
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 100)
- `status` (string): Filter by status

**Response:**
```json
{
  "drones": [...],
  "total": 10,
  "page": 1,
  "page_size": 50
}
```

### Get Drone
```http
GET /drones/{drone_id}
```

### Create Drone
```http
POST /drones
Content-Type: application/json

{
  "name": "Inspector 1",
  "spec": {
    "model": "DJI Matrice 300",
    "max_speed": 17.0,
    "max_altitude": 120.0,
    "max_flight_time": 3300,
    "battery_capacity": 5880.0
  },
  "home_position": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 0.0
  }
}
```

### Send Command
```http
POST /drones/{drone_id}/command
Content-Type: application/json

{
  "command": "takeoff",
  "parameters": {
    "altitude": 10.0
  }
}
```

**Available Commands:**
- `arm`: Arm the drone
- `takeoff`: Take off to specified altitude
- `land`: Land at current location
- `rth`: Return to home
- `set_mode`: Change control mode

---

## Missions API

### List Missions
```http
GET /missions?status=active
```

### Create Mission
```http
POST /missions
Content-Type: application/json

{
  "name": "Bridge Inspection",
  "description": "Inspect Golden Gate Bridge",
  "waypoints": [
    {
      "sequence": 0,
      "position": {
        "latitude": 37.8199,
        "longitude": -122.4783,
        "altitude": 30.0
      },
      "speed": 5.0,
      "gimbal_pitch": -45.0
    }
  ],
  "home_position": {
    "latitude": 37.8199,
    "longitude": -122.4783,
    "altitude": 0.0
  },
  "parameters": {
    "default_speed": 10.0,
    "rth_altitude": 80.0
  }
}
```

### Assign Mission
```http
POST /missions/{mission_id}/assign
Content-Type: application/json

{
  "drone_ids": ["uuid1", "uuid2"],
  "start_immediately": true
}
```

### Mission Commands
```http
POST /missions/{mission_id}/command
Content-Type: application/json

{
  "command": "start"
}
```

**Commands:** `start`, `pause`, `resume`, `abort`

---

## Telemetry API

### Get All Telemetry
```http
GET /telemetry
```

### Get Drone Telemetry
```http
GET /telemetry/{drone_id}
```

**Response:**
```json
{
  "drone_id": "uuid",
  "timestamp": "2025-01-01T12:00:00Z",
  "position": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 50.0
  },
  "velocity": {
    "vx": 5.0,
    "vy": 0.0,
    "vz": 0.0
  },
  "attitude": {
    "roll": 0.0,
    "pitch": 5.0,
    "yaw": 90.0
  },
  "battery": {
    "percentage": 85.0,
    "voltage": 22.2,
    "current": 15.5,
    "remaining_time": 1200
  },
  "gps": {
    "satellites": 18,
    "hdop": 0.8,
    "fix_type": 3
  },
  "status": "in_flight"
}
```

---

## Events API

### List Events
```http
GET /events?severity=warning&page=1&page_size=50
```

### List Alerts
```http
GET /events/alerts?resolved=false
```

---

## Fleet API

### Get Fleet Status
```http
GET /fleet/status
```

**Response:**
```json
{
  "total_drones": 10,
  "active_drones": 8,
  "status_breakdown": {
    "in_flight": 5,
    "hovering": 2,
    "idle": 3
  },
  "active_missions": 3,
  "is_running": true,
  "sim_speed": 1.0
}
```

### Start Fleet Simulation
```http
POST /fleet/start
```

### Stop Fleet Simulation
```http
POST /fleet/stop
```

### Set Simulation Speed
```http
POST /fleet/speed
Content-Type: application/json

{
  "speed": 2.0
}
```

---

## Scenarios API

### List Scenarios
```http
GET /scenarios
```

### Load Scenario
```http
POST /scenarios/{scenario_id}/load
```

**Available Scenarios:**
- `bridge_inspection`: Standard bridge inspection
- `tower_inspection`: Multi-drone tower inspection
- `bvlos_corridor`: Long-range BVLOS mission
- `urban_patrol`: Urban smart-city patrol
- `ehs_safety`: EHS safety sweep
- `stress_test`: Failure stress test

---

## Edge-AI API

### Enable AI for Drone
```http
POST /ai/{drone_id}/enable
Content-Type: application/json

{
  "model_name": "crack_detector"
}
```

### Get AI Statistics
```http
GET /ai/{drone_id}/statistics
```

### List Available Models
```http
GET /ai/models
```

---

## WebSocket Messages

### Connection
Client receives on connection:
```json
{
  "type": "connected",
  "message": "Connected to DMS telemetry stream",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Telemetry Stream
Server broadcasts every 100ms:
```json
{
  "type": "telemetry",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": {
    "drone-uuid-1": { /* telemetry data */ },
    "drone-uuid-2": { /* telemetry data */ }
  }
}
```

### Events
Server broadcasts events:
```json
{
  "type": "event",
  "data": {
    "event_type": "drone_failure",
    "severity": "error",
    "title": "GPS drift detected",
    ...
  }
}
```

### Alerts
```json
{
  "type": "alert",
  "data": {
    "alert_type": "conflict_warning",
    "severity": "warning",
    "message": "Drones too close",
    ...
  }
}
```

### Client Commands
Client can send:
```json
{
  "type": "ping"
}
```

Server responds:
```json
{
  "type": "pong",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message"
}
```

**Status Codes:**
- 200: Success
- 201: Created
- 204: No Content
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error
