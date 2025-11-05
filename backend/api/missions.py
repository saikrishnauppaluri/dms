"""
Missions API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from models import (
    Mission, MissionCreate, MissionUpdate, MissionResponse,
    MissionListResponse, MissionAssignment, MissionCommand,
    MissionStatus
)
from core import get_fleet_manager

router = APIRouter()


@router.post("/", response_model=MissionResponse, status_code=201)
async def create_mission(mission_data: MissionCreate):
    """Create a new mission"""
    fleet = get_fleet_manager()

    mission = Mission(
        name=mission_data.name,
        description=mission_data.description,
        waypoints=mission_data.waypoints,
        home_position=mission_data.home_position,
        parameters=mission_data.parameters,
        geofence_zones=mission_data.geofence_zones,
        scenario_id=mission_data.scenario_id
    )

    await fleet.add_mission(mission)

    return MissionResponse(mission=mission)


@router.get("/", response_model=MissionListResponse)
async def list_missions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """List all missions"""
    fleet = get_fleet_manager()
    missions = list(fleet.missions.values())

    if status:
        missions = [m for m in missions if m.status.value == status]

    total = len(missions)
    start = (page - 1) * page_size
    end = start + page_size
    missions = missions[start:end]

    return MissionListResponse(
        missions=missions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: UUID):
    """Get mission by ID"""
    fleet = get_fleet_manager()

    if mission_id not in fleet.missions:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = fleet.missions[mission_id]
    return MissionResponse(mission=mission)


@router.patch("/{mission_id}", response_model=MissionResponse)
async def update_mission(mission_id: UUID, update_data: MissionUpdate):
    """Update mission"""
    fleet = get_fleet_manager()

    if mission_id not in fleet.missions:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = fleet.missions[mission_id]

    # Update fields
    if update_data.name is not None:
        mission.name = update_data.name
    if update_data.description is not None:
        mission.description = update_data.description
    if update_data.status is not None:
        mission.status = update_data.status
    if update_data.waypoints is not None:
        mission.waypoints = update_data.waypoints
    if update_data.parameters is not None:
        mission.parameters = update_data.parameters
    if update_data.geofence_zones is not None:
        mission.geofence_zones = update_data.geofence_zones
    if update_data.assigned_drone_ids is not None:
        mission.assigned_drone_ids = update_data.assigned_drone_ids

    return MissionResponse(mission=mission)


@router.delete("/{mission_id}", status_code=204)
async def delete_mission(mission_id: UUID):
    """Delete mission"""
    fleet = get_fleet_manager()

    if mission_id not in fleet.missions:
        raise HTTPException(status_code=404, detail="Mission not found")

    del fleet.missions[mission_id]


@router.post("/{mission_id}/assign")
async def assign_mission(mission_id: UUID, assignment: MissionAssignment):
    """Assign mission to drones"""
    fleet = get_fleet_manager()

    try:
        await fleet.assign_mission(
            mission_id,
            assignment.drone_ids,
            assignment.start_immediately
        )
        return {"status": "success", "mission_id": str(mission_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{mission_id}/command")
async def mission_command(mission_id: UUID, command: MissionCommand):
    """Send command to mission"""
    fleet = get_fleet_manager()

    if mission_id not in fleet.missions:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = fleet.missions[mission_id]

    # Execute command on all assigned drones
    for drone_id in mission.assigned_drone_ids:
        if drone_id not in fleet.simulators:
            continue

        simulator = fleet.simulators[drone_id]

        if command.command == "start":
            await simulator.start_mission(mission)
        elif command.command == "pause":
            # Hover in place
            from models import DroneStatus
            simulator.drone.status = DroneStatus.HOVERING
        elif command.command == "resume":
            from models import DroneStatus
            simulator.drone.status = DroneStatus.IN_FLIGHT
        elif command.command == "abort":
            await simulator.initiate_rth("Mission aborted")
            mission.status = MissionStatus.ABORTED

    return {"status": "success", "command": command.command}


@router.get("/{mission_id}/progress")
async def get_mission_progress(mission_id: UUID):
    """Get mission progress"""
    fleet = get_fleet_manager()

    if mission_id not in fleet.missions:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = fleet.missions[mission_id]
    progress_list = []

    for drone_id in mission.assigned_drone_ids:
        if drone_id not in fleet.simulators:
            continue

        simulator = fleet.simulators[drone_id]

        from models import MissionProgress
        progress = MissionProgress(
            mission_id=mission_id,
            drone_id=drone_id,
            status=mission.status,
            current_waypoint=simulator.current_waypoint_index,
            total_waypoints=len(mission.waypoints),
            distance_to_waypoint=simulator._get_distance_to_waypoint() or 0.0,
            distance_traveled=simulator.distance_traveled,
            total_distance=0.0,  # TODO: Calculate
            elapsed_time=simulator.sim_time - (simulator.mission_start_time or 0),
            completion_percentage=(simulator.current_waypoint_index / len(mission.waypoints) * 100)
            if mission.waypoints else 0
        )
        progress_list.append(progress)

    return {"mission_id": str(mission_id), "progress": progress_list}
