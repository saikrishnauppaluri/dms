# DMS Simulator Deployment Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Production Configuration](#production-configuration)
6. [Monitoring & Observability](#monitoring--observability)

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose (for containerized deployment)
- Kubernetes cluster (for production)

### Local Quick Start

1. **Clone Repository**
```bash
git clone <repository-url>
cd dms
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend will be available at: `http://localhost:8000`

3. **Frontend Setup** (in new terminal)
```bash
cd frontend
npm install
npm start
```

Frontend will be available at: `http://localhost:3000`

4. **Access Application**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

---

## Local Development

### Backend Development

1. **Create Virtual Environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
Create `.env` file:
```env
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./dms.db
API_HOST=0.0.0.0
API_PORT=8000
```

4. **Run Server**
```bash
python run.py
```

Or with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Configure Environment**
Create `.env.local`:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

3. **Run Development Server**
```bash
npm run dev
```

4. **Build for Production**
```bash
npm run build
```

---

## Docker Deployment

### Using Docker Compose

1. **Start All Services**
```bash
docker-compose up -d
```

This starts:
- Backend API (port 8000)
- Frontend (port 3000)
- PostgreSQL database
- MQTT broker
- Prometheus (port 9090)
- Grafana (port 3001)

2. **View Logs**
```bash
docker-compose logs -f
```

3. **Stop Services**
```bash
docker-compose down
```

4. **Rebuild After Changes**
```bash
docker-compose up -d --build
```

### Individual Container Build

**Backend:**
```bash
cd backend
docker build -t dms-backend:latest .
docker run -p 8000:8000 dms-backend:latest
```

**Frontend:**
```bash
cd frontend
docker build -t dms-frontend:latest .
docker run -p 3000:80 dms-frontend:latest
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (EKS, GKE, AKS, or local minikube)
- kubectl configured
- Container registry access

### 1. Build and Push Images

```bash
# Backend
docker build -t your-registry/dms-backend:v1.0.0 ./backend
docker push your-registry/dms-backend:v1.0.0

# Frontend
docker build -t your-registry/dms-frontend:v1.0.0 ./frontend
docker push your-registry/dms-frontend:v1.0.0
```

### 2. Create Namespace

```bash
kubectl create namespace dms
```

### 3. Create Secrets

```bash
kubectl create secret generic dms-secrets \
  --from-literal=database-url="postgresql+asyncpg://user:pass@postgres:5432/dms" \
  --namespace=dms
```

### 4. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres.yaml --namespace=dms
```

### 5. Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml --namespace=dms
```

### 6. Verify Deployment

```bash
kubectl get pods --namespace=dms
kubectl get services --namespace=dms
```

### 7. Access Application

**Using LoadBalancer:**
```bash
kubectl get svc dms-frontend-service --namespace=dms
# Access via EXTERNAL-IP
```

**Using Port Forward (for testing):**
```bash
kubectl port-forward svc/dms-frontend-service 3000:80 --namespace=dms
```

### Scaling

**Manual Scaling:**
```bash
kubectl scale deployment dms-backend --replicas=5 --namespace=dms
```

**Horizontal Pod Autoscaler** is configured in deployment.yaml:
- Min replicas: 3
- Max replicas: 10
- CPU threshold: 70%
- Memory threshold: 80%

---

## Production Configuration

### Backend Configuration

For production, update `backend/.env`:

```env
# Application
DEBUG=False
LOG_LEVEL=INFO

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/dms

# Security
SECRET_KEY=<generate-strong-secret-key>

# API
API_HOST=0.0.0.0
API_PORT=8000

# MQTT
MQTT_BROKER=mqtt-broker.production.com
MQTT_PORT=1883
MQTT_USERNAME=dms
MQTT_PASSWORD=<secure-password>

# ViSNET Integration
VISNET_API_URL=https://api.visnet.ai
VISNET_API_KEY=<your-api-key>

# Performance
MAX_DRONES=50
TELEMETRY_UPDATE_HZ=10
```

### Frontend Configuration

Update `frontend/.env.production`:

```env
VITE_API_URL=https://api.dms.example.com/api/v1
VITE_WS_URL=wss://api.dms.example.com/ws
```

### Database Setup

**PostgreSQL (Recommended for Production):**

```bash
# Create database
psql -U postgres
CREATE DATABASE dms;
CREATE USER dms WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE dms TO dms;
```

**Run Migrations:**
```bash
cd backend
alembic upgrade head
```

### NGINX Reverse Proxy

Example NGINX configuration:

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name dms.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dms.example.com;

    ssl_certificate /etc/ssl/certs/dms.crt;
    ssl_certificate_key /etc/ssl/private/dms.key;

    # Frontend
    location / {
        root /var/www/dms/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Monitoring & Observability

### Prometheus Metrics

Metrics exposed at: `http://localhost:8000/metrics`

**Key Metrics:**
- `dms_drones_total`: Total number of drones
- `dms_missions_active`: Active missions
- `dms_telemetry_updates_total`: Telemetry updates
- `dms_api_requests_total`: API request count
- `dms_websocket_connections`: Active WebSocket connections

### Grafana Dashboards

Access Grafana: `http://localhost:3001`
- Username: `admin`
- Password: `admin` (change on first login)

**Pre-configured Dashboards:**
1. Fleet Overview
2. Drone Telemetry
3. API Performance
4. System Health

### Logs

**View Backend Logs:**
```bash
# Docker
docker-compose logs -f backend

# Kubernetes
kubectl logs -f deployment/dms-backend --namespace=dms
```

**Log Aggregation:**

For production, use:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- Cloud-native solutions (CloudWatch, Stackdriver)

### Health Checks

**Backend Health:**
```bash
curl http://localhost:8000/health
```

**Kubernetes Liveness/Readiness:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Backup & Recovery

### Database Backup

**PostgreSQL:**
```bash
# Backup
pg_dump -U dms -h localhost dms > dms_backup_$(date +%Y%m%d).sql

# Restore
psql -U dms -h localhost dms < dms_backup_20250101.sql
```

### Data Volumes

**Docker Volumes:**
```bash
# Backup
docker run --rm -v dms_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore
docker run --rm -v dms_postgres_data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres_backup.tar.gz --strip 1"
```

---

## Troubleshooting

### Backend Won't Start

1. Check Python version: `python --version`
2. Verify dependencies: `pip install -r requirements.txt`
3. Check logs: `docker-compose logs backend`
4. Verify database connection in `.env`

### Frontend Build Errors

1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear cache: `npm run clean`
3. Check Node version: `node --version`

### WebSocket Connection Issues

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `main.py`
3. Test WebSocket: Use browser console or wscat
4. Check proxy/load balancer configuration

### Database Connection Errors

1. Verify PostgreSQL is running: `docker-compose ps`
2. Check credentials in `.env`
3. Test connection: `psql -U dms -h localhost`

### Performance Issues

1. Check resource usage: `docker stats`
2. Increase replicas: `kubectl scale deployment dms-backend --replicas=5`
3. Review Prometheus metrics
4. Check database query performance

---

## Security Considerations

1. **Change Default Passwords** in production
2. **Use HTTPS** for all external communication
3. **Enable Authentication** on all endpoints
4. **Restrict CORS** to specific origins
5. **Regular Updates** of dependencies
6. **Secret Management** using vault/sealed secrets
7. **Network Policies** in Kubernetes
8. **Database Encryption** at rest and in transit

---

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: `/docs`
- API Docs: `http://localhost:8000/docs`
