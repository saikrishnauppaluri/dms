"""
Drone and telemetry models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from .base import (
    BaseEntity, DroneStatus, ControlMode, Position3D,
    Velocity3D, Attitude, BatteryInfo, GPSInfo, EnvironmentInfo
)


class DroneSpec(BaseModel):
    """Drone hardware specifications"""
    model: str = Field(..., description="Drone model name")
    max_speed: float = Field(15.0, description="Maximum speed (m/s)")
    max_altitude: float = Field(120.0, description="Maximum altitude (m)")
    max_flight_time: int = Field(1800, description="Maximum flight time (seconds)")
    battery_capacity: float = Field(5000.0, description="Battery capacity (mAh)")
    weight: float = Field(1.5, description="Drone weight (kg)")
    payload_capacity: float = Field(0.5, description="Payload capacity (kg)")
    cruise_speed: float = Field(10.0, description="Cruise speed (m/s)")
    climb_rate: float = Field(3.0, description="Max climb rate (m/s)")
    descent_rate: float = Field(2.0, description="Max descent rate (m/s)")
    hover_power: float = Field(150.0, description="Hover power consumption (W)")
    cruise_power: float = Field(200.0, description="Cruise power consumption (W)")


class Drone(BaseEntity):
    """Drone entity"""
    name: str = Field(..., description="Drone name")
    spec: DroneSpec = Field(..., description="Drone specifications")
    home_position: Position3D = Field(..., description="Home position")
    status: DroneStatus = Field(DroneStatus.IDLE, description="Current status")
    control_mode: ControlMode = Field(ControlMode.AUTONOMOUS, description="Control mode")
    mission_id: Optional[UUID] = Field(None, description="Current mission ID")
    active: bool = Field(True, description="Is drone active")

    # Current state
    position: Position3D = Field(..., description="Current position")
    velocity: Velocity3D = Field(default_factory=Velocity3D, description="Current velocity")
    attitude: Attitude = Field(default_factory=Attitude, description="Current attitude")
    battery: BatteryInfo = Field(..., description="Battery information")
    gps: GPSInfo = Field(..., description="GPS information")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Telemetry(BaseModel):
    """Real-time telemetry data"""
    drone_id: UUID = Field(..., description="Drone ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Position & Motion
    position: Position3D
    velocity: Velocity3D
    attitude: Attitude

    # Status
    status: DroneStatus
    control_mode: ControlMode

    # Sensors
    battery: BatteryInfo
    gps: GPSInfo
    environment: EnvironmentInfo = Field(default_factory=EnvironmentInfo)

    # Mission
    mission_id: Optional[UUID] = None
    current_waypoint: Optional[int] = None
    distance_to_waypoint: Optional[float] = None

    # System health
    cpu_usage: float = Field(0.0, ge=0, le=100, description="CPU usage %")
    memory_usage: float = Field(0.0, ge=0, le=100, description="Memory usage %")
    temperature: float = Field(25.0, description="Internal temperature (C)")

    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DroneCommand(BaseModel):
    """Command to send to drone"""
    drone_id: UUID
    command: str = Field(..., description="Command name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DroneCreate(BaseModel):
    """Drone creation request"""
    name: str
    spec: DroneSpec
    home_position: Position3D
    control_mode: ControlMode = ControlMode.AUTONOMOUS


class DroneUpdate(BaseModel):
    """Drone update request"""
    name: Optional[str] = None
    status: Optional[DroneStatus] = None
    control_mode: Optional[ControlMode] = None
    home_position: Optional[Position3D] = None
    mission_id: Optional[UUID] = None
    active: Optional[bool] = None


class DroneResponse(BaseModel):
    """Drone API response"""
    drone: Drone
    telemetry: Optional[Telemetry] = None


class DroneListResponse(BaseModel):
    """List of drones response"""
    drones: List[Drone]
    total: int
    page: int = 1
    page_size: int = 50
