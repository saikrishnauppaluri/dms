"""
DMS API Package
"""
from fastapi import APIRouter

from .drones import router as drones_router
from .missions import router as missions_router
from .telemetry import router as telemetry_router
from .events import router as events_router
from .fleet import router as fleet_router
from .ai import router as ai_router
from .scenarios import router as scenarios_router

api_router = APIRouter()

# Include all routers
api_router.include_router(drones_router, prefix="/drones", tags=["drones"])
api_router.include_router(missions_router, prefix="/missions", tags=["missions"])
api_router.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(fleet_router, prefix="/fleet", tags=["fleet"])
api_router.include_router(ai_router, prefix="/ai", tags=["edge-ai"])
api_router.include_router(scenarios_router, prefix="/scenarios", tags=["scenarios"])

__all__ = ['api_router']
