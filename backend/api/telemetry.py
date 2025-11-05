"""
Telemetry API endpoints
"""
from fastapi import APIRouter, HTTPException
from uuid import UUID

router = APIRouter()


@router.get("/")
async def get_all_telemetry():
    """Get current telemetry for all drones"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()

    telemetry = await fleet.get_telemetry_all()

    return {
        "telemetry": {str(k): v for k, v in telemetry.items()},
        "count": len(telemetry)
    }


@router.get("/{drone_id}")
async def get_drone_telemetry(drone_id: UUID):
    """Get current telemetry for specific drone"""
    from core import get_fleet_manager
    fleet = get_fleet_manager()

    if drone_id not in fleet.simulators:
        raise HTTPException(status_code=404, detail="Drone not found")

    simulator = fleet.simulators[drone_id]

    if not simulator.telemetry_history:
        raise HTTPException(status_code=404, detail="No telemetry available")

    return simulator.telemetry_history[-1]
