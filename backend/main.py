"""
Main FastAPI application
"""
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from api import api_router
from api.websocket import websocket_endpoint, telemetry_broadcaster, events_broadcaster


# Background tasks
background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Start background tasks
    tasks = [
        asyncio.create_task(telemetry_broadcaster()),
        asyncio.create_task(events_broadcaster())
    ]
    background_tasks.extend(tasks)

    yield

    # Shutdown
    print("Shutting down...")

    # Cancel background tasks
    for task in background_tasks:
        task.cancel()

    await asyncio.gather(*background_tasks, return_exceptions=True)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-quality Drone Management System Simulator",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry"""
    await websocket_endpoint(websocket)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from core import get_fleet_manager

    fleet = get_fleet_manager()
    fleet_status = await fleet.get_fleet_status()

    return {
        "status": "healthy",
        "fleet": fleet_status
    }


# Metrics endpoint (Prometheus format)
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from core import get_fleet_manager
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response

    # Generate Prometheus metrics
    metrics_output = generate_latest()

    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
