"""
Fleet management API endpoints
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def get_fleet_status():
    """Get fleet status"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()
    return await fleet.get_fleet_status()


@router.post("/start")
async def start_fleet():
    """Start fleet simulation"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()
    await fleet.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_fleet():
    """Stop fleet simulation"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()
    await fleet.stop()
    return {"status": "stopped"}


@router.post("/speed")
async def set_simulation_speed(speed: float):
    """Set simulation speed multiplier"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()
    fleet.sim_speed = max(0.1, min(10.0, speed))
    return {"speed": fleet.sim_speed}
