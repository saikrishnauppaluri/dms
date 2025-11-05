"""
Sensor simulation with realistic noise and failure modes
"""
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
import random

from models import Position3D, Attitude, GPSInfo, SensorType
from .physics import PhysicsState


@dataclass
class SensorConfig:
    """Sensor configuration parameters"""
    # GPS
    gps_accuracy: float = 2.5  # meters (CEP)
    gps_update_hz: float = 10.0
    gps_drift_rate: float = 0.1  # m/s max drift

    # Barometer
    baro_noise_std: float = 0.5  # meters
    baro_bias: float = 0.0

    # Magnetometer
    mag_noise_std: float = 2.0  # degrees
    mag_declination: float = 0.0  # local magnetic declination

    # IMU
    accel_noise_std: float = 0.02  # m/s^2
    accel_bias: float = 0.01
    gyro_noise_std: float = 0.1  # deg/s
    gyro_bias: float = 0.05

    # Rangefinder
    rangefinder_max_range: float = 40.0  # meters
    rangefinder_accuracy: float = 0.05  # meters


class SensorSimulator:
    """Simulates realistic sensor readings with noise and failures"""

    def __init__(self, config: Optional[SensorConfig] = None):
        self.config = config or SensorConfig()
        self.gps_drift = np.zeros(2)  # Accumulated GPS drift [lat, lon]
        self.last_gps_update = 0.0
        self.sensor_failures = {}  # Track active sensor failures

    def simulate_gps(
        self,
        true_position: np.ndarray,
        timestamp: float
    ) -> Tuple[Position3D, GPSInfo]:
        """
        Simulate GPS reading with realistic noise and multipath effects

        Args:
            true_position: True position [lat, lon, alt]
            timestamp: Current simulation time

        Returns:
            Tuple of (measured position, GPS info)
        """
        # Check if GPS has failed
        if SensorType.GPS in self.sensor_failures:
            failure = self.sensor_failures[SensorType.GPS]
            if failure['active']:
                # Return degraded GPS
                return self._get_degraded_gps(true_position, failure['severity'])

        # Update GPS drift (random walk)
        dt = timestamp - self.last_gps_update
        if dt > 0:
            drift_change = np.random.randn(2) * self.config.gps_drift_rate * dt
            self.gps_drift += drift_change
            # Limit drift accumulation
            self.gps_drift = np.clip(self.gps_drift, -10.0, 10.0)
            self.last_gps_update = timestamp

        # Convert drift to degrees (approximate)
        meters_per_degree = 111000.0
        drift_lat = self.gps_drift[0] / meters_per_degree
        drift_lon = self.gps_drift[1] / (meters_per_degree * np.cos(np.radians(true_position[0])))

        # Add random noise (Gaussian)
        noise_meters = np.random.randn(3) * self.config.gps_accuracy

        noise_lat = noise_meters[0] / meters_per_degree
        noise_lon = noise_meters[1] / (meters_per_degree * np.cos(np.radians(true_position[0])))
        noise_alt = noise_meters[2]

        # Measured position
        measured_lat = true_position[0] + drift_lat + noise_lat
        measured_lon = true_position[1] + drift_lon + noise_lon
        measured_alt = true_position[2] + noise_alt

        # GPS quality (varies with noise and drift)
        total_error = np.linalg.norm([self.gps_drift[0], self.gps_drift[1], noise_meters[2]])
        satellites = max(4, min(20, int(20 - total_error / 2)))
        hdop = 0.5 + total_error / 5.0
        fix_type = 3 if satellites >= 6 else 2

        position = Position3D(
            latitude=measured_lat,
            longitude=measured_lon,
            altitude=measured_alt
        )

        gps_info = GPSInfo(
            satellites=satellites,
            hdop=hdop,
            fix_type=fix_type
        )

        return position, gps_info

    def simulate_barometer(self, true_altitude: float) -> float:
        """Simulate barometric altitude with noise"""
        if SensorType.BAROMETER in self.sensor_failures:
            failure = self.sensor_failures[SensorType.BAROMETER]
            if failure['active']:
                # Return faulty reading
                return true_altitude + np.random.randn() * 10.0

        noise = np.random.randn() * self.config.baro_noise_std
        return true_altitude + self.config.baro_bias + noise

    def simulate_magnetometer(self, true_yaw: float) -> float:
        """Simulate magnetometer (compass) reading"""
        if SensorType.MAGNETOMETER in self.sensor_failures:
            failure = self.sensor_failures[SensorType.MAGNETOMETER]
            if failure['active']:
                # Return random heading
                return random.uniform(0, 360)

        noise = np.random.randn() * self.config.mag_noise_std
        measured_yaw = true_yaw + self.config.mag_declination + noise

        # Normalize to [0, 360)
        while measured_yaw < 0:
            measured_yaw += 360
        while measured_yaw >= 360:
            measured_yaw -= 360

        return measured_yaw

    def simulate_imu(
        self,
        true_acceleration: np.ndarray,
        true_angular_velocity: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate IMU (accelerometer + gyroscope) readings

        Args:
            true_acceleration: True acceleration [ax, ay, az] m/s^2
            true_angular_velocity: True angular velocity [p, q, r] deg/s

        Returns:
            Tuple of (measured acceleration, measured angular velocity)
        """
        if SensorType.IMU in self.sensor_failures:
            failure = self.sensor_failures[SensorType.IMU]
            if failure['active']:
                # Return noisy IMU data
                accel_noise = np.random.randn(3) * 1.0
                gyro_noise = np.random.randn(3) * 10.0
                return true_acceleration + accel_noise, true_angular_velocity + gyro_noise

        # Accelerometer
        accel_noise = np.random.randn(3) * self.config.accel_noise_std
        accel_bias = np.ones(3) * self.config.accel_bias
        measured_accel = true_acceleration + accel_noise + accel_bias

        # Gyroscope
        gyro_noise = np.random.randn(3) * self.config.gyro_noise_std
        gyro_bias = np.ones(3) * self.config.gyro_bias
        measured_gyro = true_angular_velocity + gyro_noise + gyro_bias

        return measured_accel, measured_gyro

    def simulate_rangefinder(self, true_altitude_agl: float) -> Optional[float]:
        """
        Simulate rangefinder (ultrasonic/laser) reading

        Args:
            true_altitude_agl: True altitude above ground level

        Returns:
            Measured altitude or None if out of range
        """
        if true_altitude_agl > self.config.rangefinder_max_range:
            return None

        noise = np.random.randn() * self.config.rangefinder_accuracy
        return max(0, true_altitude_agl + noise)

    def simulate_lidar(
        self,
        true_position: np.ndarray,
        true_attitude: np.ndarray,
        terrain_height: float = 0.0
    ) -> Optional[np.ndarray]:
        """
        Simulate LiDAR point cloud (simplified)

        Args:
            true_position: True position [lat, lon, alt]
            true_attitude: True attitude [roll, pitch, yaw]
            terrain_height: Ground terrain height

        Returns:
            Simplified point cloud or None if LiDAR not available
        """
        # Simplified: return distance measurements in 8 directions
        altitude_agl = true_position[2] - terrain_height

        if altitude_agl > 100:  # Max LiDAR range
            return None

        # Simulate 8 ray measurements
        angles = np.linspace(0, 2 * np.pi, 9)[:-1]
        distances = []

        for angle in angles:
            # Add some variation based on direction
            base_distance = altitude_agl / np.cos(np.radians(true_attitude[1]))  # pitch effect
            noise = np.random.randn() * 0.1
            distance = base_distance + noise
            distances.append(max(0, distance))

        return np.array(distances)

    def inject_failure(
        self,
        sensor_type: SensorType,
        severity: float = 0.5,
        duration: Optional[float] = None
    ):
        """
        Inject a sensor failure

        Args:
            sensor_type: Type of sensor to fail
            severity: Failure severity 0-1 (0=minor, 1=complete failure)
            duration: Duration in seconds (None = permanent until cleared)
        """
        self.sensor_failures[sensor_type] = {
            'active': True,
            'severity': severity,
            'duration': duration,
            'start_time': 0  # Will be set by calling code
        }

    def clear_failure(self, sensor_type: SensorType):
        """Clear a sensor failure"""
        if sensor_type in self.sensor_failures:
            self.sensor_failures[sensor_type]['active'] = False

    def _get_degraded_gps(
        self,
        true_position: np.ndarray,
        severity: float
    ) -> Tuple[Position3D, GPSInfo]:
        """Get degraded GPS reading during failure"""
        # Increase noise proportional to severity
        noise_multiplier = 1.0 + severity * 50.0

        noise_meters = np.random.randn(3) * self.config.gps_accuracy * noise_multiplier

        meters_per_degree = 111000.0
        noise_lat = noise_meters[0] / meters_per_degree
        noise_lon = noise_meters[1] / (meters_per_degree * np.cos(np.radians(true_position[0])))
        noise_alt = noise_meters[2]

        position = Position3D(
            latitude=true_position[0] + noise_lat,
            longitude=true_position[1] + noise_lon,
            altitude=true_position[2] + noise_alt
        )

        # Degraded GPS quality
        satellites = max(0, int(20 * (1 - severity)))
        hdop = 1.0 + severity * 10.0
        fix_type = 0 if severity > 0.8 else (2 if severity > 0.5 else 3)

        gps_info = GPSInfo(
            satellites=satellites,
            hdop=hdop,
            fix_type=fix_type
        )

        return position, gps_info


class CameraSim:
    """Camera and gimbal simulation"""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fov: float = 84.0,
        gimbal_range: Tuple[float, float] = (-90, 30)
    ):
        self.width = width
        self.height = height
        self.fov = fov  # Field of view in degrees
        self.gimbal_pitch_range = gimbal_range

        # Current gimbal state
        self.gimbal_pitch = 0.0
        self.gimbal_yaw = 0.0
        self.gimbal_roll = 0.0

    def set_gimbal_angle(self, pitch: float, yaw: float = 0.0, roll: float = 0.0):
        """Set gimbal angles"""
        self.gimbal_pitch = np.clip(pitch, *self.gimbal_pitch_range)
        self.gimbal_yaw = yaw
        self.gimbal_roll = roll

    def get_footprint(
        self,
        altitude_agl: float,
        pitch: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate camera footprint on ground

        Args:
            altitude_agl: Altitude above ground level
            pitch: Gimbal pitch (None = use current)

        Returns:
            Tuple of (width, height) of footprint in meters
        """
        if pitch is None:
            pitch = self.gimbal_pitch

        # Effective altitude considering pitch
        effective_alt = altitude_agl / np.cos(np.radians(pitch))

        # Calculate footprint using FOV
        fov_rad = np.radians(self.fov)
        footprint_diag = 2 * effective_alt * np.tan(fov_rad / 2)

        # Aspect ratio
        aspect_ratio = self.width / self.height
        footprint_height = footprint_diag / np.sqrt(1 + aspect_ratio ** 2)
        footprint_width = footprint_height * aspect_ratio

        return footprint_width, footprint_height

    def simulate_capture(
        self,
        position: Position3D,
        attitude: Attitude,
        timestamp: float
    ) -> dict:
        """
        Simulate camera capture

        Args:
            position: Drone position
            attitude: Drone attitude
            timestamp: Capture timestamp

        Returns:
            Camera frame metadata
        """
        return {
            'timestamp': timestamp,
            'position': {
                'latitude': position.latitude,
                'longitude': position.longitude,
                'altitude': position.altitude
            },
            'attitude': {
                'roll': attitude.roll,
                'pitch': attitude.pitch,
                'yaw': attitude.yaw
            },
            'gimbal': {
                'pitch': self.gimbal_pitch,
                'yaw': self.gimbal_yaw,
                'roll': self.gimbal_roll
            },
            'camera': {
                'width': self.width,
                'height': self.height,
                'fov': self.fov
            }
        }
