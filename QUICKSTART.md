# DMS Simulator - Quick Start Guide

Get the Drone Management System Simulator up and running in 5 minutes!

## Option 1: Docker Compose (Recommended)

### Prerequisites
- Docker and Docker Compose installed

### Steps

1. **Start the system**
```bash
docker-compose up -d
```

2. **Access the applications**
- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Grafana (Monitoring): http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

3. **Load a scenario**
- Open http://localhost:3000
- Navigate to "Scenarios" in the sidebar
- Click "Load Scenario" on any pre-built scenario
- View drones on the Dashboard map

4. **Stop the system**
```bash
docker-compose down
```

---

## Option 2: Local Development

### Prerequisites
- Python 3.9+
- Node.js 16+

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start backend server
python run.py
```

Backend will be available at: http://localhost:8000

### Frontend Setup

In a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will be available at: http://localhost:3000

---

## Quick Test

### Using the UI

1. **Load a Scenario**
   - Go to http://localhost:3000/scenarios
   - Click "Load Scenario" on "Standard Bridge Inspection"
   - Wait for the scenario to load

2. **View Dashboard**
   - Go to http://localhost:3000
   - See drone on the map
   - Watch real-time telemetry updates

3. **Monitor Events**
   - Go to http://localhost:3000/events
   - See system events and alerts

### Using the API

```bash
# Check system health
curl http://localhost:8000/health

# List available scenarios
curl http://localhost:8000/api/v1/scenarios

# Get fleet status
curl http://localhost:8000/api/v1/fleet/status

# Start simulation
curl -X POST http://localhost:8000/api/v1/fleet/start

# Get telemetry
curl http://localhost:8000/api/v1/telemetry
```

### Using WebSocket

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onopen = () => {
  console.log('Connected to DMS simulator');
};
```

---

## Pre-built Scenarios

### 1. Standard Bridge Inspection
- **Drones:** 1
- **Duration:** ~10 minutes
- **Features:** Crack detection, waypoint navigation

### 2. Multi-Drone Tower Inspection
- **Drones:** 3
- **Duration:** ~8 minutes
- **Features:** Coordinated inspection, GPS drift simulation

### 3. BVLOS Corridor Mission
- **Drones:** 1
- **Duration:** ~15 minutes
- **Features:** Long-range flight, wind effects, battery management

### 4. Urban Smart-City Patrol
- **Drones:** 2
- **Duration:** ~12 minutes
- **Features:** Geofencing, dynamic obstacles, conflict avoidance

### 5. EHS Safety Sweep
- **Drones:** 1
- **Duration:** ~9 minutes
- **Features:** PPE detection, construction site inspection

### 6. Failure Stress Test
- **Drones:** 3
- **Duration:** ~10 minutes
- **Features:** Multiple failure modes, auto-reassignment

---

## Common Tasks

### Create a Custom Drone

```bash
curl -X POST http://localhost:8000/api/v1/drones \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Drone",
    "spec": {
      "model": "DJI Matrice 300",
      "max_speed": 17.0,
      "max_altitude": 120.0,
      "max_flight_time": 3300,
      "battery_capacity": 5880.0,
      "weight": 6.3,
      "payload_capacity": 2.7
    },
    "home_position": {
      "latitude": 37.7749,
      "longitude": -122.4194,
      "altitude": 0.0
    }
  }'
```

### Create a Custom Mission

```bash
curl -X POST http://localhost:8000/api/v1/missions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom Mission",
    "waypoints": [
      {
        "sequence": 0,
        "position": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 30.0},
        "speed": 5.0
      },
      {
        "sequence": 1,
        "position": {"latitude": 37.7750, "longitude": -122.4195, "altitude": 30.0},
        "speed": 5.0
      }
    ],
    "home_position": {"latitude": 37.7749, "longitude": -122.4194, "altitude": 0.0}
  }'
```

### Enable Edge-AI

```bash
# Enable crack detection AI
curl -X POST http://localhost:8000/api/v1/ai/{drone_id}/enable \
  -H "Content-Type: application/json" \
  -d '{"model_name": "crack_detector"}'

# Get AI statistics
curl http://localhost:8000/api/v1/ai/{drone_id}/statistics
```

### Inject a Failure

```bash
curl -X POST http://localhost:8000/api/v1/drones/{drone_id}/failures \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gps_drift",
    "severity": 0.7,
    "duration": 30
  }'
```

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check logs
docker-compose logs backend
```

### Frontend won't connect
```bash
# Check if backend is running
curl http://localhost:8000/health

# Clear browser cache
# Check browser console for errors
```

### No drones on map
1. Make sure simulation is started
2. Load a scenario first
3. Check fleet status: `curl http://localhost:8000/api/v1/fleet/status`

### WebSocket not connecting
1. Verify backend is running
2. Check browser console
3. Try: `wscat -c ws://localhost:8000/ws`

---

## Next Steps

1. **Explore Documentation**
   - API Documentation: http://localhost:8000/docs
   - Full docs: `/docs` directory

2. **Try Different Scenarios**
   - Load each pre-built scenario
   - Observe different behaviors

3. **Create Custom Missions**
   - Design your own waypoint patterns
   - Test different parameters

4. **Integrate with ViSNET**
   - Configure ViSNET API credentials
   - Test image upload and detection flow

5. **Deploy to Production**
   - See `docs/DEPLOYMENT.md`
   - Configure Kubernetes
   - Set up monitoring

---

## Getting Help

- **Documentation:** `/docs` directory
- **API Reference:** http://localhost:8000/docs
- **Architecture:** `docs/ARCHITECTURE.md`
- **Deployment:** `docs/DEPLOYMENT.md`
- **Issues:** GitHub Issues

---

## System Requirements

### Minimum
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB

### Recommended
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB
- SSD for database

### For 50 Drones
- CPU: 8+ cores
- RAM: 16+ GB
- High-speed SSD

---

Happy simulating! 🚁
