# Drone Management System (DMS) Simulator

A production-quality drone management simulator for mission planning, fleet coordination, AI-onboard analytics, and integration testing.

## Features

- **Mission Planning**: Create, edit, and execute complex mission plans with waypoints, altitudes, speeds, and camera actions
- **Fleet Orchestration**: Manage up to 50+ concurrent virtual drones with conflict avoidance and task assignment
- **Realistic Physics**: 3D flight dynamics, battery modeling, wind effects, and environmental simulation
- **Sensor Simulation**: GPS, IMU, camera, LiDAR with configurable noise and failure modes
- **Edge-AI Integration**: Plug-in architecture for onboard AI model simulation
- **Telemetry & APIs**: Real-time WebSocket/MQTT streams and comprehensive REST API
- **Operator Dashboard**: React-based web UI with live maps, telemetry, and mission control
- **Failure Scenarios**: Simulate common failures and emergency behaviors
- **ViSNET Integration**: Direct integration hooks for ViSNET AI platform

## Quick Start

```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Start backend
cd backend && python run.py

# Start frontend (in new terminal)
cd frontend && npm start

# Or use Docker Compose
docker-compose up
```

## Architecture

```
dms/
├── backend/              # Python simulation engine
│   ├── core/            # Core simulation components
│   ├── api/             # REST API & WebSocket
│   ├── models/          # Data models
│   ├── scenarios/       # Pre-built scenarios
│   └── tests/           # Unit & integration tests
├── frontend/            # React operator dashboard
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── services/    # API clients
│   │   └── pages/       # Main pages
├── docker/              # Docker configurations
├── k8s/                 # Kubernetes manifests
└── docs/                # Documentation
```

## Documentation

- [API Documentation](docs/API.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Scenario Guide](docs/SCENARIOS.md)
- [Development Guide](docs/DEVELOPMENT.md)

## Requirements

- Python 3.9+
- Node.js 16+
- Docker & Kubernetes (for production deployment)
- PostgreSQL 13+ (for production)

## License

MIT License - See LICENSE file for details
