"""
Base models and enums for DMS
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class DroneStatus(str, Enum):
    """Drone status enumeration"""
    IDLE = "idle"
    PREFLIGHT = "preflight"
    ARMED = "armed"
    TAKING_OFF = "taking_off"
    IN_FLIGHT = "in_flight"
    HOVERING = "hovering"
    LANDING = "landing"
    LANDED = "landed"
    RTH = "return_to_home"
    EMERGENCY = "emergency"
    ERROR = "error"
    OFFLINE = "offline"


class MissionStatus(str, Enum):
    """Mission status enumeration"""
    DRAFT = "draft"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ControlMode(str, Enum):
    """Control mode enumeration"""
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"


class FailureType(str, Enum):
    """Failure type enumeration"""
    COMM_LOSS = "comm_loss"
    GPS_DRIFT = "gps_drift"
    MOTOR_FAILURE = "motor_failure"
    BATTERY_DROP = "battery_drop"
    SENSOR_FAULT = "sensor_fault"
    BIRD_STRIKE = "bird_strike"
    RTC_LOSS = "rtc_loss"
    PAYLOAD_FAILURE = "payload_failure"


class EmergencyAction(str, Enum):
    """Emergency action enumeration"""
    HOVER = "hover"
    LAND = "land"
    RTH = "return_to_home"
    SAFE_WAYPOINT = "safe_waypoint"
    FALLBACK_CHANNEL = "fallback_channel"


class SensorType(str, Enum):
    """Sensor type enumeration"""
    GPS = "gps"
    IMU = "imu"
    BAROMETER = "barometer"
    MAGNETOMETER = "magnetometer"
    RANGEFINDER = "rangefinder"
    LIDAR = "lidar"
    CAMERA = "camera"


# Base models

class Position3D(BaseModel):
    """3D Position"""
    latitude: float = Field(..., description="Latitude in degrees")
    longitude: float = Field(..., description="Longitude in degrees")
    altitude: float = Field(..., description="Altitude in meters (MSL)")


class Velocity3D(BaseModel):
    """3D Velocity"""
    vx: float = Field(0.0, description="Velocity X (m/s)")
    vy: float = Field(0.0, description="Velocity Y (m/s)")
    vz: float = Field(0.0, description="Velocity Z (m/s)")


class Attitude(BaseModel):
    """Drone attitude (orientation)"""
    roll: float = Field(0.0, description="Roll in degrees")
    pitch: float = Field(0.0, description="Pitch in degrees")
    yaw: float = Field(0.0, description="Yaw in degrees")


class BatteryInfo(BaseModel):
    """Battery information"""
    percentage: float = Field(..., ge=0, le=100, description="Battery percentage")
    voltage: float = Field(..., description="Battery voltage (V)")
    current: float = Field(0.0, description="Current draw (A)")
    remaining_time: Optional[int] = Field(None, description="Estimated remaining time (seconds)")


class GPSInfo(BaseModel):
    """GPS information"""
    satellites: int = Field(..., description="Number of satellites")
    hdop: float = Field(..., description="Horizontal dilution of precision")
    fix_type: int = Field(..., description="GPS fix type (0=no fix, 2=2D, 3=3D)")


class WindInfo(BaseModel):
    """Wind information"""
    speed: float = Field(0.0, description="Wind speed (m/s)")
    direction: float = Field(0.0, description="Wind direction (degrees)")
    gust_speed: float = Field(0.0, description="Gust speed (m/s)")


class EnvironmentInfo(BaseModel):
    """Environmental information"""
    temperature: float = Field(20.0, description="Temperature (Celsius)")
    pressure: float = Field(1013.25, description="Pressure (hPa)")
    humidity: float = Field(50.0, description="Humidity (%)")
    wind: WindInfo = Field(default_factory=WindInfo)


class BaseEntity(BaseModel):
    """Base entity with common fields"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
