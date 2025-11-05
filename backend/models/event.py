"""
Event, alert, and failure models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from .base import BaseEntity, FailureType, EmergencyAction


class EventSeverity(str):
    """Event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Event(BaseEntity):
    """System event"""
    event_type: str = Field(..., description="Event type")
    severity: str = Field(EventSeverity.INFO, description="Event severity")
    source: str = Field(..., description="Event source: drone_id, system, mission_id")
    source_id: Optional[UUID] = Field(None, description="Source entity ID")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    acknowledged: bool = Field(False, description="Event acknowledged")
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class Alert(BaseEntity):
    """Alert for operator attention"""
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(EventSeverity.WARNING, description="Alert severity")
    drone_id: Optional[UUID] = Field(None, description="Related drone ID")
    mission_id: Optional[UUID] = Field(None, description="Related mission ID")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    action_required: bool = Field(False, description="Requires operator action")
    resolved: bool = Field(False, description="Alert resolved")
    resolved_at: Optional[datetime] = None


class Failure(BaseEntity):
    """Simulated failure"""
    drone_id: UUID = Field(..., description="Affected drone ID")
    failure_type: FailureType = Field(..., description="Failure type")
    severity: float = Field(..., ge=0, le=1, description="Failure severity (0-1)")
    description: str = Field(..., description="Failure description")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(None, description="Failure end time (for intermittent)")
    is_intermittent: bool = Field(False, description="Intermittent failure")
    recovery_action: Optional[EmergencyAction] = Field(None, description="Recovery action taken")
    resolved: bool = Field(False, description="Failure resolved")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Failure-specific parameters")


class FailureScenario(BaseModel):
    """Failure scenario definition"""
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    failures: List[Dict[str, Any]] = Field(..., description="Failures to inject")
    trigger_condition: Dict[str, Any] = Field(..., description="When to trigger")


class DetectionResult(BaseModel):
    """Edge-AI detection result"""
    detection_id: UUID = Field(..., description="Detection ID")
    drone_id: UUID = Field(..., description="Drone ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Detection details
    class_name: str = Field(..., description="Detected class")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Bounding box coordinates")

    # Location
    image_id: Optional[str] = Field(None, description="Image ID")
    position: Optional[Dict[str, float]] = Field(None, description="GPS position")
    altitude: Optional[float] = Field(None, description="Altitude (m)")

    # AI model info
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    inference_time_ms: float = Field(..., description="Inference time (ms)")

    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIModelConfig(BaseModel):
    """Edge-AI model configuration"""
    model_name: str = Field(..., description="Model name")
    model_version: str = Field("1.0.0", description="Model version")
    model_type: str = Field(..., description="Model type: detection, segmentation, classification")
    framework: str = Field("pytorch", description="Framework: pytorch, onnx, tensorflow")

    # Performance
    inference_time_ms: float = Field(100.0, description="Average inference time (ms)")
    cpu_usage: float = Field(50.0, description="CPU usage %")
    memory_mb: float = Field(500.0, description="Memory usage (MB)")
    gpu_usage: Optional[float] = Field(None, description="GPU usage %")

    # Detection parameters
    confidence_threshold: float = Field(0.5, ge=0, le=1, description="Confidence threshold")
    false_positive_rate: float = Field(0.05, ge=0, le=1, description="False positive rate")
    false_negative_rate: float = Field(0.10, ge=0, le=1, description="False negative rate")

    # Classes
    classes: List[str] = Field(..., description="Detectable classes")

    # Constraints
    max_fps: float = Field(10.0, description="Maximum processing FPS")
    enable_throttling: bool = Field(True, description="Enable throttling under load")


class CameraFrame(BaseModel):
    """Camera frame metadata"""
    frame_id: UUID = Field(..., description="Frame ID")
    drone_id: UUID = Field(..., description="Drone ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Camera info
    image_path: Optional[str] = Field(None, description="Image file path")
    width: int = Field(1920, description="Image width")
    height: int = Field(1080, description="Image height")
    format: str = Field("jpeg", description="Image format")

    # Camera state
    gimbal_pitch: float = Field(0.0, description="Gimbal pitch (degrees)")
    gimbal_yaw: float = Field(0.0, description="Gimbal yaw (degrees)")
    gimbal_roll: float = Field(0.0, description="Gimbal roll (degrees)")
    fov: float = Field(84.0, description="Field of view (degrees)")

    # Location
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    altitude: float = Field(..., description="Altitude (m)")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventCreate(BaseModel):
    """Create event request"""
    event_type: str
    severity: str = EventSeverity.INFO
    source: str
    source_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class EventListResponse(BaseModel):
    """List events response"""
    events: List[Event]
    total: int
    page: int = 1
    page_size: int = 100
