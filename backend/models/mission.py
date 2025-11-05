"""
Mission and waypoint models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .base import BaseEntity, Position3D, MissionStatus


class WaypointAction(BaseModel):
    """Action to perform at waypoint"""
    type: str = Field(..., description="Action type: photo, video_start, video_stop, loiter, roi")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    duration: Optional[float] = Field(None, description="Action duration (seconds)")


class Waypoint(BaseModel):
    """Mission waypoint"""
    sequence: int = Field(..., description="Waypoint sequence number")
    position: Position3D = Field(..., description="Waypoint position")
    speed: Optional[float] = Field(None, description="Speed to waypoint (m/s)")
    heading: Optional[float] = Field(None, description="Heading at waypoint (degrees)")
    gimbal_pitch: Optional[float] = Field(None, description="Gimbal pitch angle (degrees)")
    gimbal_yaw: Optional[float] = Field(None, description="Gimbal yaw angle (degrees)")
    actions: List[WaypointAction] = Field(default_factory=list, description="Actions at waypoint")
    loiter_time: float = Field(0.0, description="Loiter time at waypoint (seconds)")


class GeofenceZone(BaseModel):
    """Geofence zone definition"""
    type: str = Field(..., description="Zone type: polygon, circle, cylinder")
    coordinates: List[Position3D] = Field(..., description="Zone boundary coordinates")
    altitude_min: Optional[float] = Field(None, description="Minimum altitude (m)")
    altitude_max: Optional[float] = Field(None, description="Maximum altitude (m)")
    action: str = Field("warn", description="Action on breach: warn, rth, land")


class MissionParameters(BaseModel):
    """Mission execution parameters"""
    default_speed: float = Field(10.0, description="Default flight speed (m/s)")
    default_altitude: float = Field(50.0, description="Default altitude (m)")
    rth_altitude: float = Field(80.0, description="Return to home altitude (m)")
    auto_continue: bool = Field(True, description="Auto-continue on waypoint reach")
    finish_action: str = Field("rth", description="Action on mission complete: rth, land, hover")
    max_distance: Optional[float] = Field(None, description="Maximum distance from home (m)")
    lost_signal_action: str = Field("rth", description="Action on signal loss: rth, land, hover")


class Mission(BaseEntity):
    """Mission entity"""
    name: str = Field(..., description="Mission name")
    description: Optional[str] = Field(None, description="Mission description")
    status: MissionStatus = Field(MissionStatus.DRAFT, description="Mission status")

    # Mission definition
    waypoints: List[Waypoint] = Field(..., description="Mission waypoints")
    home_position: Position3D = Field(..., description="Home/launch position")
    parameters: MissionParameters = Field(default_factory=MissionParameters)
    geofence_zones: List[GeofenceZone] = Field(default_factory=list, description="Geofence zones")

    # Assignment
    assigned_drone_ids: List[UUID] = Field(default_factory=list, description="Assigned drone IDs")

    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_waypoint: Optional[int] = None

    # Metadata
    scenario_id: Optional[str] = Field(None, description="Scenario template ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MissionProgress(BaseModel):
    """Mission execution progress"""
    mission_id: UUID
    drone_id: UUID
    status: MissionStatus
    current_waypoint: int
    total_waypoints: int
    distance_to_waypoint: float
    distance_traveled: float
    total_distance: float
    elapsed_time: float
    estimated_remaining_time: Optional[float] = None
    completion_percentage: float


class MissionCreate(BaseModel):
    """Mission creation request"""
    name: str
    description: Optional[str] = None
    waypoints: List[Waypoint]
    home_position: Position3D
    parameters: MissionParameters = Field(default_factory=MissionParameters)
    geofence_zones: List[GeofenceZone] = Field(default_factory=list)
    scenario_id: Optional[str] = None


class MissionUpdate(BaseModel):
    """Mission update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MissionStatus] = None
    waypoints: Optional[List[Waypoint]] = None
    parameters: Optional[MissionParameters] = None
    geofence_zones: Optional[List[GeofenceZone]] = None
    assigned_drone_ids: Optional[List[UUID]] = None


class MissionAssignment(BaseModel):
    """Assign mission to drones"""
    mission_id: UUID
    drone_ids: List[UUID]
    start_immediately: bool = False


class MissionCommand(BaseModel):
    """Mission control command"""
    mission_id: UUID
    command: str = Field(..., description="Command: start, pause, resume, abort, rth")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MissionResponse(BaseModel):
    """Mission API response"""
    mission: Mission
    progress: Optional[List[MissionProgress]] = None


class MissionListResponse(BaseModel):
    """List of missions response"""
    missions: List[Mission]
    total: int
    page: int = 1
    page_size: int = 50
