"""
Configuration management for DMS Simulator
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "DMS Simulator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # WebSocket
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8001

    # MQTT
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_TOPIC_PREFIX: str = "dms"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dms.db"
    # For production: postgresql+asyncpg://user:pass@localhost/dms

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Simulation
    MAX_DRONES: int = 50
    TELEMETRY_UPDATE_HZ: int = 10
    PHYSICS_UPDATE_HZ: int = 50
    VIDEO_FPS: int = 30

    # Physics
    GRAVITY: float = 9.81  # m/s^2
    AIR_DENSITY: float = 1.225  # kg/m^3 at sea level

    # Failure Simulation
    ENABLE_FAILURES: bool = True
    FAILURE_PROBABILITY: float = 0.01  # 1% chance per second

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Prometheus
    PROMETHEUS_PORT: int = 9090

    # Storage
    DATA_DIR: str = "./data"
    SCENARIOS_DIR: str = "./scenarios"
    LOGS_DIR: str = "./logs"
    RECORDINGS_DIR: str = "./recordings"

    # ViSNET Integration
    VISNET_API_URL: Optional[str] = None
    VISNET_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create required directories
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.SCENARIOS_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
os.makedirs(settings.RECORDINGS_DIR, exist_ok=True)
