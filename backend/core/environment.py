"""
Environmental simulation including weather, wind, and dynamic obstacles
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from models import EnvironmentInfo, WindInfo, Position3D


@dataclass
class Obstacle:
    """Dynamic obstacle"""
    id: str
    position: Position3D
    velocity: np.ndarray  # [vx, vy, vz] m/s
    size: Tuple[float, float, float]  # [width, depth, height] m
    obstacle_type: str  # "bird", "crane", "structure", etc.


class EnvironmentSimulator:
    """
    Simulates environmental conditions:
    - Wind patterns and gusts
    - Weather changes
    - Dynamic obstacles (birds, cranes, etc.)
    - Terrain elevation
    """

    def __init__(self):
        # Base environmental conditions
        self.base_temperature = 20.0  # Celsius
        self.base_pressure = 1013.25  # hPa
        self.base_humidity = 50.0  # %

        # Wind model
        self.base_wind_speed = 5.0  # m/s
        self.base_wind_direction = 0.0  # degrees
        self.wind_variability = 2.0  # m/s
        self.gust_probability = 0.1  # probability per second
        self.gust_strength = 8.0  # m/s

        # Dynamic obstacles
        self.obstacles: List[Obstacle] = []

        # Terrain elevation data (simplified)
        self.terrain_heights: Dict[Tuple[float, float], float] = {}

    def get_environment_at(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime
    ) -> EnvironmentInfo:
        """
        Get environmental conditions at a specific location and time

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            timestamp: Current timestamp

        Returns:
            Environmental information
        """
        # Time-based variations
        hour = timestamp.hour
        day_factor = np.sin((hour - 6) / 24 * 2 * np.pi)  # Peak at noon

        # Temperature varies with time of day
        temperature = self.base_temperature + day_factor * 10.0

        # Pressure (simplified)
        pressure = self.base_pressure + np.random.randn() * 2.0

        # Humidity
        humidity = self.base_humidity + np.random.randn() * 10.0
        humidity = np.clip(humidity, 0, 100)

        # Wind
        wind = self._simulate_wind(latitude, longitude, timestamp)

        return EnvironmentInfo(
            temperature=temperature,
            pressure=pressure,
            humidity=humidity,
            wind=wind
        )

    def _simulate_wind(
        self,
        latitude: float,
        longitude: float,
        timestamp: datetime
    ) -> WindInfo:
        """Simulate wind conditions"""
        # Base wind with some spatial variation
        spatial_factor = np.sin(latitude * 10) * np.cos(longitude * 10)
        wind_speed = self.base_wind_speed + spatial_factor * self.wind_variability

        # Add temporal variation
        hour = timestamp.hour
        time_factor = 1.0 + 0.3 * np.sin(hour / 24 * 2 * np.pi)
        wind_speed *= time_factor

        # Add random variation
        wind_speed += np.random.randn() * 1.0
        wind_speed = max(0, wind_speed)

        # Wind direction with some variation
        wind_direction = self.base_wind_direction + np.random.randn() * 20.0
        wind_direction = wind_direction % 360

        # Simulate gusts
        gust_speed = 0.0
        if np.random.random() < self.gust_probability:
            gust_speed = np.random.uniform(5.0, self.gust_strength)

        return WindInfo(
            speed=wind_speed,
            direction=wind_direction,
            gust_speed=gust_speed
        )

    def add_obstacle(
        self,
        obstacle_id: str,
        position: Position3D,
        velocity: np.ndarray,
        size: Tuple[float, float, float],
        obstacle_type: str = "generic"
    ):
        """Add a dynamic obstacle"""
        obstacle = Obstacle(
            id=obstacle_id,
            position=position,
            velocity=velocity,
            size=size,
            obstacle_type=obstacle_type
        )
        self.obstacles.append(obstacle)

    def update_obstacles(self, dt: float):
        """Update obstacle positions"""
        for obstacle in self.obstacles:
            # Update position based on velocity
            pos = obstacle.position
            vel = obstacle.velocity

            # Simple integration
            new_lat = pos.latitude + (vel[0] * dt) / 111000.0
            new_lon = pos.longitude + (vel[1] * dt) / (111000.0 * np.cos(np.radians(pos.latitude)))
            new_alt = pos.altitude + vel[2] * dt

            obstacle.position = Position3D(
                latitude=new_lat,
                longitude=new_lon,
                altitude=max(0, new_alt)
            )

    def check_collision(
        self,
        position: Position3D,
        drone_size: float = 0.5
    ) -> Optional[Obstacle]:
        """
        Check if drone position collides with any obstacle

        Args:
            position: Drone position
            drone_size: Drone size (radius) in meters

        Returns:
            Colliding obstacle or None
        """
        for obstacle in self.obstacles:
            distance = self._calculate_distance_3d(position, obstacle.position)

            # Simple sphere-box collision check
            obstacle_radius = max(obstacle.size) / 2
            if distance < (drone_size + obstacle_radius):
                return obstacle

        return None

    def get_terrain_height(self, latitude: float, longitude: float) -> float:
        """
        Get terrain height at position

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Terrain height in meters above sea level
        """
        # Round to grid
        lat_key = round(latitude, 4)
        lon_key = round(longitude, 4)
        key = (lat_key, lon_key)

        if key in self.terrain_heights:
            return self.terrain_heights[key]

        # Generate terrain height (simplified - could load from DEM data)
        # Using Perlin-like noise
        height = 0.0
        height += 50.0 * np.sin(latitude * 0.01) * np.cos(longitude * 0.01)
        height += 20.0 * np.sin(latitude * 0.1) * np.cos(longitude * 0.1)
        height = max(0, height)

        self.terrain_heights[key] = height
        return height

    def set_wind(self, speed: float, direction: float, gust_speed: float = 0.0):
        """Manually set wind conditions"""
        self.base_wind_speed = speed
        self.base_wind_direction = direction
        self.gust_strength = gust_speed

    def set_weather(self, temperature: float, pressure: float, humidity: float):
        """Manually set weather conditions"""
        self.base_temperature = temperature
        self.base_pressure = pressure
        self.base_humidity = humidity

    def create_bird_flock(
        self,
        center: Position3D,
        count: int = 10,
        spread: float = 50.0
    ):
        """Create a flock of bird obstacles"""
        for i in range(count):
            # Random position around center
            offset_x = np.random.uniform(-spread, spread)
            offset_y = np.random.uniform(-spread, spread)
            offset_z = np.random.uniform(-20, 20)

            pos = Position3D(
                latitude=center.latitude + offset_x / 111000.0,
                longitude=center.longitude + offset_y / 111000.0,
                altitude=center.altitude + offset_z
            )

            # Random velocity (birds flying)
            velocity = np.array([
                np.random.uniform(-5, 5),
                np.random.uniform(-5, 5),
                np.random.uniform(-2, 2)
            ])

            self.add_obstacle(
                obstacle_id=f"bird_{i}",
                position=pos,
                velocity=velocity,
                size=(0.5, 0.3, 0.2),
                obstacle_type="bird"
            )

    def create_crane_obstacle(self, position: Position3D, height: float = 50.0):
        """Create a crane obstacle"""
        self.add_obstacle(
            obstacle_id="crane",
            position=position,
            velocity=np.zeros(3),
            size=(20.0, 20.0, height),
            obstacle_type="crane"
        )

    @staticmethod
    def _calculate_distance_3d(pos1: Position3D, pos2: Position3D) -> float:
        """Calculate 3D distance between positions"""
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000 * np.cos(np.radians(pos1.latitude))
        alt_diff = pos2.altitude - pos1.altitude

        return np.sqrt(lat_diff ** 2 + lon_diff ** 2 + alt_diff ** 2)


class GeofenceManager:
    """Manages geofence zones and checks for breaches"""

    def __init__(self):
        self.zones = []

    def add_zone(self, zone):
        """Add a geofence zone"""
        self.zones.append(zone)

    def check_breach(self, position: Position3D) -> Optional[Dict]:
        """
        Check if position breaches any geofence

        Args:
            position: Position to check

        Returns:
            Zone info if breach detected, None otherwise
        """
        for zone in self.zones:
            if self._is_inside_zone(position, zone):
                continue
            else:
                # Outside allowed zone
                return {
                    'zone': zone,
                    'action': zone.action
                }

        return None

    def _is_inside_zone(self, position: Position3D, zone) -> bool:
        """Check if position is inside zone"""
        # Simplified: check altitude first
        if zone.altitude_min is not None and position.altitude < zone.altitude_min:
            return False
        if zone.altitude_max is not None and position.altitude > zone.altitude_max:
            return False

        # Check horizontal boundary
        if zone.type == "circle":
            # First coordinate is center, check radius
            if len(zone.coordinates) > 0:
                center = zone.coordinates[0]
                distance = self._calculate_distance_2d(position, center)
                radius = zone.coordinates[1].latitude if len(zone.coordinates) > 1 else 100.0
                return distance <= radius

        elif zone.type == "polygon":
            # Point-in-polygon check (simplified)
            return self._point_in_polygon(position, zone.coordinates)

        return True

    @staticmethod
    def _calculate_distance_2d(pos1: Position3D, pos2: Position3D) -> float:
        """Calculate 2D distance"""
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000 * np.cos(np.radians(pos1.latitude))
        return np.sqrt(lat_diff ** 2 + lon_diff ** 2)

    @staticmethod
    def _point_in_polygon(point: Position3D, polygon: List[Position3D]) -> bool:
        """Check if point is inside polygon (ray casting algorithm)"""
        if len(polygon) < 3:
            return False

        inside = False
        j = len(polygon) - 1

        for i in range(len(polygon)):
            xi, yi = polygon[i].latitude, polygon[i].longitude
            xj, yj = polygon[j].latitude, polygon[j].longitude

            if ((yi > point.longitude) != (yj > point.longitude)) and \
               (point.latitude < (xj - xi) * (point.longitude - yi) / (yj - yi) + xi):
                inside = not inside

            j = i

        return inside
