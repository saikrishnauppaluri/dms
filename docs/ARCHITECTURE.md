# DMS Simulator Architecture

## System Overview

The Drone Management System (DMS) Simulator is a production-quality simulation platform designed to model realistic drone behavior for mission planning, fleet coordination, edge-AI analytics, and integration testing.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Dashboard │  │ Missions │  │  Drones  │  │ Scenarios│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └─────────────┴──────────────┴─────────────┘              │
│                         │                                         │
│                    HTTP/WS API                                   │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  REST API Layer                         │    │
│  │  ┌──────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌──────┐   │    │
│  │  │Drones│ │Missions│ │Telemetr│ │ Events │ │  AI  │   │    │
│  │  └───┬──┘ └───┬────┘ └───┬───┘ └───┬────┘ └───┬──┘   │    │
│  └──────┼────────┼──────────┼─────────┼────────────┼──────┘    │
│         │        │          │         │            │            │
│  ┌──────┴────────┴──────────┴─────────┴────────────┴──────┐    │
│  │             Core Simulation Engine                      │    │
│  │  ┌────────────┐  ┌───────────┐  ┌────────────┐        │    │
│  │  │   Fleet    │  │  Drone    │  │ Environment│        │    │
│  │  │  Manager   │  │ Simulator │  │ Simulator  │        │    │
│  │  └─────┬──────┘  └─────┬─────┘  └─────┬──────┘        │    │
│  │        │                │                │              │    │
│  │  ┌─────┴──────┐  ┌──────┴──────┐  ┌────┴────┐         │    │
│  │  │  Physics   │  │   Sensors   │  │ Edge-AI │         │    │
│  │  │  Engine    │  │  Simulator  │  │Simulator│         │    │
│  │  └────────────┘  └─────────────┘  └─────────┘         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Integration Layer                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │  ViSNET  │  │   GIS    │  │   ERP    │             │   │
│  │  └──────────┘  └──────────┘  └──────────┘             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐                ┌──────────────┐               │
│  │  WebSocket  │                │  Prometheus  │               │
│  │   Server    │                │   Metrics    │               │
│  └─────────────┘                └──────────────┘               │
└──────────────────────────────────────────────────────────────────┘
                          │                    │
         ┌────────────────┼────────────────┬───┘
         │                │                │
    ┌────┴────┐     ┌─────┴────┐    ┌────┴────┐
    │PostgreSQL│     │   MQTT   │    │ Grafana │
    └──────────┘     │  Broker  │    └─────────┘
                     └──────────┘
```

## Core Components

### 1. Frontend (React + TypeScript)

**Technology Stack:**
- React 18
- TypeScript
- Material-UI (MUI)
- Leaflet (Maps)
- Recharts (Visualizations)
- Axios (HTTP)
- WebSocket (Real-time)

**Key Features:**
- Dashboard with live map view
- Drone fleet management
- Mission planning interface
- Real-time telemetry display
- Event/alert monitoring
- Scenario selection

### 2. Backend (Python + FastAPI)

**Technology Stack:**
- Python 3.9+
- FastAPI
- Pydantic (Data validation)
- SQLAlchemy (ORM)
- asyncio (Async operations)
- NumPy/SciPy (Physics)

**API Layer:**
- RESTful API
- WebSocket server
- MQTT integration
- OpenAPI/Swagger docs

### 3. Core Simulation Engine

#### Fleet Manager
- Coordinates multiple drone simulators
- Conflict detection and avoidance
- Task assignment and re-assignment
- Fleet health monitoring

#### Drone Simulator
- Individual drone behavior
- Mission execution
- Emergency handling
- Telemetry generation

#### Physics Engine
- 3D kinematics and dynamics
- Battery discharge modeling
- Wind and environmental effects
- Aerodynamic forces

#### Sensor Simulator
- GPS with realistic noise
- IMU (accelerometer + gyroscope)
- Barometer, magnetometer
- Camera and gimbal
- LiDAR (optional)

#### Environment Simulator
- Wind patterns and gusts
- Weather conditions
- Dynamic obstacles
- Terrain elevation
- Geofencing

#### Edge-AI Simulator
- Pluggable AI models
- Performance simulation (latency, FPS)
- Resource constraints (CPU, memory)
- Detection generation with configurable accuracy

### 4. Integration Layer

#### ViSNET Integration
- Image upload
- Detection submission
- Work order creation
- Asset condition updates

#### GIS Integration
- WMS/WMTS layer support
- Terrain data
- Asset layers

#### ERP/CMMS Integration
- Maintenance ticket creation
- Asset register updates

## Data Flow

### 1. Telemetry Flow

```
Drone Simulator → Physics Update → Sensor Reading → Telemetry Object
    ↓
Fleet Manager → WebSocket Server → Frontend
    ↓
Database (Historical)
```

Update Rate: 10 Hz (configurable)

### 2. Mission Execution Flow

```
User → Frontend → API → Fleet Manager
    ↓
Mission Assignment → Drone Simulator
    ↓
Waypoint Navigation → Physics Engine → Telemetry
    ↓
Camera Actions → Edge-AI → Detections → ViSNET
```

### 3. Failure Injection Flow

```
User/Scenario → API → Drone Simulator
    ↓
Failure Trigger → Sensor/System Degradation
    ↓
Emergency Action → Event Generation → Alert
    ↓
Mission Reassignment (if applicable)
```

## Key Design Patterns

### 1. Singleton Pattern
- `FleetManager`: Single instance managing all drones
- `EdgeAIManager`: Single instance managing AI simulators
- `ViSNETIntegration`: Single integration client

### 2. Factory Pattern
- `ScenarioBuilder`: Creates pre-configured scenarios
- Drone creation with specifications

### 3. Observer Pattern
- WebSocket broadcast system
- Event notification system

### 4. Strategy Pattern
- Multiple control modes (Autonomous, Assisted, Manual)
- Configurable emergency actions

## Database Schema

```sql
-- Drones
drones (
    id UUID PRIMARY KEY,
    name VARCHAR,
    spec JSONB,
    home_position JSONB,
    status VARCHAR,
    created_at TIMESTAMP
)

-- Missions
missions (
    id UUID PRIMARY KEY,
    name VARCHAR,
    waypoints JSONB,
    parameters JSONB,
    status VARCHAR,
    created_at TIMESTAMP
)

-- Events
events (
    id UUID PRIMARY KEY,
    event_type VARCHAR,
    severity VARCHAR,
    source VARCHAR,
    data JSONB,
    created_at TIMESTAMP
)

-- Telemetry (Time-series)
telemetry (
    id UUID PRIMARY KEY,
    drone_id UUID,
    timestamp TIMESTAMP,
    position JSONB,
    battery JSONB,
    ...
)
```

## Communication Protocols

### REST API
- HTTP/HTTPS
- JSON payloads
- OpenAPI 3.0 specification
- API key authentication

### WebSocket
- Real-time telemetry streaming
- Event broadcasting
- Bidirectional communication
- Auto-reconnection

### MQTT (Optional)
- Pub/Sub architecture
- Topic hierarchy: `dms/{drone_id}/{data_type}`
- QoS levels supported
- Retained messages for status

## Scalability Architecture

### Horizontal Scaling

**Backend:**
- Stateless API servers
- Load balancer (NGINX/HAProxy)
- Session affinity for WebSocket
- Distributed fleet management

**Database:**
- PostgreSQL with read replicas
- Connection pooling
- Query optimization
- Partitioning for telemetry

**Simulation:**
- Distribute drones across instances
- Message queue for coordination
- Shared state via Redis/database

### Vertical Scaling

**Resource Allocation:**
- Per-drone: ~10 MB memory
- 50 drones: ~500 MB + overhead
- Physics updates: CPU intensive
- Batch processing for efficiency

### Performance Optimization

1. **Telemetry Batching**: Group updates before broadcast
2. **Lazy Evaluation**: Only compute when requested
3. **Caching**: Redis for fleet status, telemetry
4. **Database Indexing**: On drone_id, timestamp, status
5. **Async Operations**: Non-blocking I/O throughout

## Security Architecture

### Authentication & Authorization

- API Key-based authentication
- Role-based access control (RBAC)
- JWT tokens for user sessions
- Service-to-service authentication

### Data Protection

- HTTPS for all external communication
- WebSocket Secure (WSS)
- Database encryption at rest
- Secret management (Vault/K8s Secrets)

### Network Security

- Kubernetes Network Policies
- Firewall rules
- Rate limiting
- DDoS protection

## Monitoring & Observability

### Metrics (Prometheus)

- System metrics: CPU, memory, disk
- Application metrics: API requests, latency
- Business metrics: Active drones, missions
- Custom metrics: Telemetry update rate

### Logging

- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized aggregation (ELK/Loki)
- Request tracing

### Tracing

- Distributed tracing (optional)
- Correlation IDs
- Performance profiling

### Alerting

- Prometheus AlertManager
- Critical system failures
- Resource exhaustion
- Anomaly detection

## Disaster Recovery

### Backup Strategy

- Database: Daily full, hourly incremental
- Configuration: Version control
- Data volumes: Snapshot backups

### High Availability

- Multi-replica deployments
- Health checks and auto-restart
- Rolling updates
- Graceful shutdown

### Recovery Procedures

1. Database restore from backup
2. Redeploy from last known good
3. State reconstruction from logs
4. Manual intervention triggers

## Future Enhancements

1. **ML Integration**: Real model training feedback
2. **Digital Twin**: Sync with real drones
3. **Multi-Region**: Distributed simulation
4. **Advanced Physics**: Rotor dynamics, turbulence
5. **VR/AR Interface**: Immersive control
6. **Blockchain**: Audit trail for compliance

## Technology Choices Rationale

### Python Backend
- Rich scientific libraries (NumPy, SciPy)
- Excellent async support (asyncio)
- FastAPI for performance
- Easy AI/ML integration

### React Frontend
- Component-based architecture
- Strong ecosystem
- TypeScript for type safety
- Good mapping libraries

### PostgreSQL
- ACID compliance
- JSON support for flexibility
- Time-series optimization
- Production-proven

### Docker/Kubernetes
- Containerization
- Orchestration
- Scalability
- Industry standard

## Conclusion

The DMS Simulator provides a comprehensive, scalable, and production-ready platform for testing and validating drone management systems. The modular architecture allows for easy extension and customization while maintaining performance and reliability.
