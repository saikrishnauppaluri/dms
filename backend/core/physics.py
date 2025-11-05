"""
Physics simulation engine for drone flight dynamics
"""
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
import math

from models import (
    Position3D, Velocity3D, Attitude, DroneSpec,
    EnvironmentInfo, WindInfo
)
from config import settings


@dataclass
class PhysicsState:
    """Complete physics state of a drone"""
    # Position (lat, lon, alt)
    position: np.ndarray  # [3]

    # Velocity (vx, vy, vz in NED frame)
    velocity: np.ndarray  # [3]

    # Acceleration (ax, ay, az in NED frame)
    acceleration: np.ndarray  # [3]

    # Attitude (roll, pitch, yaw in degrees)
    attitude: np.ndarray  # [3]

    # Angular velocity (p, q, r in deg/s)
    angular_velocity: np.ndarray  # [3]

    # Mass (kg)
    mass: float

    # Battery state (Wh remaining)
    battery_wh: float


class PhysicsEngine:
    """
    Realistic drone physics simulation including:
    - 3D kinematics and dynamics
    - Battery discharge modeling
    - Wind and environmental effects
    - Aerodynamic drag
    """

    def __init__(self, spec: DroneSpec):
        self.spec = spec
        self.dt = 1.0 / settings.PHYSICS_UPDATE_HZ
        self.gravity = settings.GRAVITY

        # Aerodynamic coefficients (simplified)
        self.drag_coefficient = 0.5
        self.frontal_area = 0.1  # m^2

        # Battery parameters
        self.battery_voltage = 22.2  # V (6S LiPo typical)
        self.battery_capacity_wh = (spec.battery_capacity / 1000.0) * self.battery_voltage

    def init_state(self, position: Position3D) -> PhysicsState:
        """Initialize physics state at given position"""
        return PhysicsState(
            position=np.array([position.latitude, position.longitude, position.altitude]),
            velocity=np.zeros(3),
            acceleration=np.zeros(3),
            attitude=np.zeros(3),
            angular_velocity=np.zeros(3),
            mass=self.spec.weight,
            battery_wh=self.battery_capacity_wh
        )

    def update(
        self,
        state: PhysicsState,
        target_velocity: np.ndarray,
        target_yaw: float,
        environment: EnvironmentInfo
    ) -> PhysicsState:
        """
        Update physics state for one timestep

        Args:
            state: Current physics state
            target_velocity: Desired velocity [vx, vy, vz] in m/s
            target_yaw: Desired yaw angle in degrees
            environment: Environmental conditions

        Returns:
            Updated physics state
        """
        # Apply wind effects to target velocity
        wind_effect = self._calculate_wind_effect(environment.wind, state.attitude[2])
        effective_velocity = target_velocity + wind_effect

        # Calculate forces
        thrust_force = self._calculate_thrust(state, effective_velocity)
        drag_force = self._calculate_drag(state.velocity, environment)
        weight_force = np.array([0, 0, -state.mass * self.gravity])

        # Total force and acceleration
        total_force = thrust_force + drag_force + weight_force
        acceleration = total_force / state.mass

        # Update velocity and position (using semi-implicit Euler)
        new_velocity = state.velocity + acceleration * self.dt

        # Clamp velocity to drone limits
        speed = np.linalg.norm(new_velocity[:2])
        if speed > self.spec.max_speed:
            new_velocity[:2] *= self.spec.max_speed / speed

        # Clamp vertical velocity
        new_velocity[2] = np.clip(
            new_velocity[2],
            -self.spec.descent_rate,
            self.spec.climb_rate
        )

        # Update position
        new_position = state.position.copy()
        new_position = self._update_position(new_position, new_velocity)

        # Clamp altitude
        new_position[2] = max(0, min(new_position[2], self.spec.max_altitude))

        # Update attitude (simplified: pitch/roll based on velocity, yaw controlled)
        new_attitude = self._update_attitude(state, new_velocity, target_yaw)

        # Calculate power consumption and update battery
        power_w = self._calculate_power_consumption(new_velocity, environment)
        battery_consumed_wh = power_w * (self.dt / 3600.0)
        new_battery_wh = max(0, state.battery_wh - battery_consumed_wh)

        return PhysicsState(
            position=new_position,
            velocity=new_velocity,
            acceleration=acceleration,
            attitude=new_attitude,
            angular_velocity=state.angular_velocity,  # Simplified: not modeling angular dynamics
            mass=state.mass,
            battery_wh=new_battery_wh
        )

    def _calculate_thrust(self, state: PhysicsState, target_velocity: np.ndarray) -> np.ndarray:
        """Calculate thrust force needed to achieve target velocity"""
        # Simple proportional controller
        velocity_error = target_velocity - state.velocity
        kp = 2.0  # Proportional gain
        thrust = velocity_error * kp * state.mass
        return thrust

    def _calculate_drag(self, velocity: np.ndarray, environment: EnvironmentInfo) -> np.ndarray:
        """Calculate aerodynamic drag force"""
        # Air density (adjust for temperature and pressure)
        rho = environment.pressure / (287.05 * (environment.temperature + 273.15))

        # Drag force: F = 0.5 * rho * v^2 * Cd * A
        speed = np.linalg.norm(velocity)
        if speed < 0.01:
            return np.zeros(3)

        drag_magnitude = 0.5 * rho * speed * speed * self.drag_coefficient * self.frontal_area
        drag_direction = -velocity / speed
        return drag_direction * drag_magnitude

    def _calculate_wind_effect(self, wind: WindInfo, yaw: float) -> np.ndarray:
        """Calculate wind effect on velocity"""
        # Convert wind direction to velocity components
        wind_rad = math.radians(wind.direction)
        wind_vx = wind.speed * math.cos(wind_rad)
        wind_vy = wind.speed * math.sin(wind_rad)

        # Add random gusts
        if wind.gust_speed > 0:
            gust_x = np.random.normal(0, wind.gust_speed * 0.3)
            gust_y = np.random.normal(0, wind.gust_speed * 0.3)
            wind_vx += gust_x
            wind_vy += gust_y

        return np.array([wind_vx, wind_vy, 0])

    def _update_position(self, position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        """Update position based on velocity"""
        # For altitude (simple)
        new_alt = position[2] + velocity[2] * self.dt

        # For lat/lon (approximate - convert m/s to degrees)
        # At equator: 1 degree lat/lon ≈ 111km
        meters_per_degree = 111000.0

        dlat = (velocity[0] * self.dt) / meters_per_degree
        dlon = (velocity[1] * self.dt) / (meters_per_degree * math.cos(math.radians(position[0])))

        return np.array([
            position[0] + dlat,
            position[1] + dlon,
            new_alt
        ])

    def _update_attitude(
        self,
        state: PhysicsState,
        velocity: np.ndarray,
        target_yaw: float
    ) -> np.ndarray:
        """Update attitude based on velocity and target yaw"""
        # Roll and pitch based on horizontal velocity (simplified)
        max_tilt = 30.0  # degrees

        # Pitch: forward/backward tilt based on vx
        pitch = -np.clip(velocity[0] * 3.0, -max_tilt, max_tilt)

        # Roll: left/right tilt based on vy
        roll = np.clip(velocity[1] * 3.0, -max_tilt, max_tilt)

        # Yaw: smoothly approach target
        current_yaw = state.attitude[2]
        yaw_error = self._angle_diff(target_yaw, current_yaw)
        max_yaw_rate = 45.0  # deg/s
        yaw_rate = np.clip(yaw_error * 2.0, -max_yaw_rate, max_yaw_rate)
        yaw = current_yaw + yaw_rate * self.dt
        yaw = self._normalize_angle(yaw)

        return np.array([roll, pitch, yaw])

    def _calculate_power_consumption(
        self,
        velocity: np.ndarray,
        environment: EnvironmentInfo
    ) -> float:
        """Calculate power consumption in watts"""
        # Base hover power
        power = self.spec.hover_power

        # Additional power for horizontal movement
        horizontal_speed = np.linalg.norm(velocity[:2])
        if horizontal_speed > 0:
            # Power increases quadratically with speed (simplified)
            power += (self.spec.cruise_power - self.spec.hover_power) * \
                     (horizontal_speed / self.spec.cruise_speed) ** 2

        # Additional power for climbing
        if velocity[2] > 0:
            climb_power = velocity[2] * self.spec.weight * self.gravity * 1.5
            power += climb_power

        # Wind resistance increases power consumption
        wind_speed = environment.wind.speed
        power *= (1.0 + 0.1 * (wind_speed / 10.0))

        # Temperature effects
        temp_factor = 1.0 + 0.01 * (20.0 - environment.temperature)
        power *= temp_factor

        return power

    def get_battery_percentage(self, state: PhysicsState) -> float:
        """Get battery percentage"""
        return (state.battery_wh / self.battery_capacity_wh) * 100.0

    def get_estimated_flight_time(self, state: PhysicsState, avg_power_w: float) -> float:
        """Estimate remaining flight time in seconds"""
        if avg_power_w <= 0:
            return 0
        return (state.battery_wh / avg_power_w) * 3600.0

    @staticmethod
    def _angle_diff(target: float, current: float) -> float:
        """Calculate shortest angular difference"""
        diff = target - current
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return diff

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Normalize angle to [-180, 180]"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle


class BatteryModel:
    """
    Realistic battery discharge modeling with:
    - Non-linear discharge curve
    - Temperature effects
    - C-rating limitations
    - Voltage sag under load
    """

    def __init__(self, capacity_mah: float, voltage: float = 22.2):
        self.capacity_mah = capacity_mah
        self.voltage = voltage
        self.capacity_wh = (capacity_mah / 1000.0) * voltage

        # LiPo discharge curve parameters
        self.v_max = 4.2 * 6  # 6S fully charged
        self.v_nom = 3.7 * 6  # 6S nominal
        self.v_min = 3.3 * 6  # 6S cutoff

    def get_voltage(self, state_of_charge: float, current_a: float, temperature: float) -> float:
        """
        Get battery voltage considering discharge state and load

        Args:
            state_of_charge: SOC from 0 to 1
            current_a: Current draw in amps
            temperature: Battery temperature in Celsius
        """
        # Base voltage from discharge curve
        if state_of_charge > 0.9:
            base_voltage = self.v_max
        elif state_of_charge > 0.2:
            # Linear region
            base_voltage = self.v_nom + (self.v_max - self.v_nom) * ((state_of_charge - 0.2) / 0.7)
        else:
            # Rapid dropoff
            base_voltage = self.v_min + (self.v_nom - self.v_min) * (state_of_charge / 0.2) ** 2

        # Voltage sag under load (simplified internal resistance model)
        internal_resistance = 0.01  # ohms per cell
        voltage_sag = current_a * internal_resistance * 6  # 6S

        # Temperature effects
        temp_factor = 1.0 - 0.005 * (20.0 - temperature)

        return (base_voltage - voltage_sag) * temp_factor

    def is_critical(self, state_of_charge: float) -> bool:
        """Check if battery is critically low"""
        return state_of_charge < 0.2

    def should_rtl(self, state_of_charge: float) -> bool:
        """Check if drone should return to launch"""
        return state_of_charge < 0.3
