"""
Drones API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from models import (
    Drone, DroneCreate, DroneUpdate, DroneResponse,
    DroneListResponse, DroneCommand, DroneSpec, Position3D
)
from core import get_fleet_manager

router = APIRouter()


@router.post("/", response_model=DroneResponse, status_code=201)
async def create_drone(drone_data: DroneCreate):
    """Create a new drone"""
    fleet = get_fleet_manager()

    # Create drone entity
    drone = Drone(
        name=drone_data.name,
        spec=drone_data.spec,
        home_position=drone_data.home_position,
        position=drone_data.home_position,
        control_mode=drone_data.control_mode,
        battery=models.BatteryInfo(percentage=100.0, voltage=22.2)
    )

    # Add to fleet
    simulator = await fleet.add_drone(drone)

    # Get initial telemetry
    telemetry = None
    if simulator.telemetry_history:
        telemetry = simulator.telemetry_history[-1]

    return DroneResponse(drone=drone, telemetry=telemetry)


@router.get("/", response_model=DroneListResponse)
async def list_drones(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """List all drones"""
    fleet = get_fleet_manager()

    drones = list(fleet.drones.values())

    # Filter by status if specified
    if status:
        drones = [d for d in drones if d.status.value == status]

    # Pagination
    total = len(drones)
    start = (page - 1) * page_size
    end = start + page_size
    drones = drones[start:end]

    return DroneListResponse(
        drones=drones,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: UUID):
    """Get drone by ID"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.drones:
        raise HTTPException(status_code=404, detail="Drone not found")

    drone = fleet.drones[drone_id]
    simulator = fleet.simulators.get(drone_id)

    telemetry = None
    if simulator and simulator.telemetry_history:
        telemetry = simulator.telemetry_history[-1]

    return DroneResponse(drone=drone, telemetry=telemetry)


@router.patch("/{drone_id}", response_model=DroneResponse)
async def update_drone(drone_id: UUID, update_data: DroneUpdate):
    """Update drone"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.drones:
        raise HTTPException(status_code=404, detail="Drone not found")

    drone = fleet.drones[drone_id]

    # Update fields
    if update_data.name is not None:
        drone.name = update_data.name
    if update_data.status is not None:
        drone.status = update_data.status
    if update_data.control_mode is not None:
        drone.control_mode = update_data.control_mode
    if update_data.home_position is not None:
        drone.home_position = update_data.home_position
    if update_data.mission_id is not None:
        drone.mission_id = update_data.mission_id
    if update_data.active is not None:
        drone.active = update_data.active

    return DroneResponse(drone=drone)


@router.delete("/{drone_id}", status_code=204)
async def delete_drone(drone_id: UUID):
    """Delete drone"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.drones:
        raise HTTPException(status_code=404, detail="Drone not found")

    await fleet.remove_drone(drone_id)


@router.post("/{drone_id}/command")
async def send_command(drone_id: UUID, command: DroneCommand):
    """Send command to drone"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.simulators:
        raise HTTPException(status_code=404, detail="Drone not found")

    simulator = fleet.simulators[drone_id]

    # Execute command
    if command.command == "arm":
        await simulator.arm()
    elif command.command == "takeoff":
        altitude = command.parameters.get("altitude", 10.0)
        await simulator.takeoff(altitude)
    elif command.command == "land":
        await simulator.land()
    elif command.command == "rth":
        reason = command.parameters.get("reason", "Manual")
        await simulator.initiate_rth(reason)
    elif command.command == "set_mode":
        mode = command.parameters.get("mode")
        simulator.drone.control_mode = mode
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {command.command}")

    return {"status": "success", "command": command.command}


@router.post("/{drone_id}/failures")
async def inject_failure(drone_id: UUID, failure_data: dict):
    """Inject a failure into drone"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.simulators:
        raise HTTPException(status_code=404, detail="Drone not found")

    simulator = fleet.simulators[drone_id]

    from models import FailureType

    failure_type = FailureType(failure_data.get("type"))
    severity = failure_data.get("severity", 0.5)
    duration = failure_data.get("duration")

    await simulator.inject_failure(failure_type, severity, duration)

    return {"status": "success", "failure_type": failure_type.value}


@router.get("/{drone_id}/telemetry")
async def get_drone_telemetry(drone_id: UUID):
    """Get current telemetry for drone"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.simulators:
        raise HTTPException(status_code=404, detail="Drone not found")

    simulator = fleet.simulators[drone_id]

    if not simulator.telemetry_history:
        raise HTTPException(status_code=404, detail="No telemetry available")

    return simulator.telemetry_history[-1]


@router.get("/{drone_id}/telemetry/history")
async def get_drone_telemetry_history(
    drone_id: UUID,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get telemetry history for drone"""
    fleet = get_fleet_manager()

    if drone_id not in fleet.simulators:
        raise HTTPException(status_code=404, detail="Drone not found")

    simulator = fleet.simulators[drone_id]
    history = simulator.telemetry_history[-limit:]

    return {"drone_id": str(drone_id), "telemetry": history, "count": len(history)}


import models
