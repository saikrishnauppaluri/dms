"""
Main drone simulator - integrates physics, sensors, and mission execution
"""
import asyncio
import numpy as np
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
import math

from models import (
    Drone, DroneStatus, ControlMode, Telemetry,
    Position3D, Velocity3D, Attitude, BatteryInfo, GPSInfo,
    Mission, Waypoint, MissionStatus, EnvironmentInfo,
    FailureType, EmergencyAction
)
from .physics import PhysicsEngine, PhysicsState, BatteryModel
from .sensors import SensorSimulator, CameraSim, SensorConfig
from config import settings


class DroneSimulator:
    """
    Complete drone simulator integrating:
    - Physics simulation
    - Sensor simulation
    - Mission execution
    - Failure handling
    - Emergency behaviors
    """

    def __init__(self, drone: Drone, environment: EnvironmentInfo):
        self.drone = drone
        self.environment = environment

        # Initialize subsystems
        self.physics = PhysicsEngine(drone.spec)
        self.sensors = SensorSimulator()
        self.camera = CameraSim()
        self.battery_model = BatteryModel(drone.spec.battery_capacity)

        # Initialize physics state
        self.physics_state = self.physics.init_state(drone.position)

        # Mission tracking
        self.current_mission: Optional[Mission] = None
        self.current_waypoint_index: int = 0
        self.mission_start_time: Optional[float] = None
        self.distance_traveled: float = 0.0

        # Control
        self.target_position: Optional[Position3D] = None
        self.target_velocity = np.zeros(3)
        self.target_yaw: float = 0.0

        # Timing
        self.sim_time: float = 0.0
        self.last_update: float = 0.0

        # Failures
        self.active_failures: Dict[FailureType, Dict[str, Any]] = {}

        # State tracking
        self.takeoff_altitude: float = 0.0
        self.is_armed: bool = False

        # Telemetry history for averaging
        self.telemetry_history: List[Telemetry] = []

    async def update(self, dt: float) -> Telemetry:
        """
        Update simulation for one timestep

        Args:
            dt: Time step in seconds

        Returns:
            Current telemetry
        """
        self.sim_time += dt

        # Handle drone status-specific behavior
        if self.drone.status == DroneStatus.IDLE:
            # Do nothing when idle
            pass

        elif self.drone.status == DroneStatus.ARMED:
            # Ready to take off
            pass

        elif self.drone.status == DroneStatus.TAKING_OFF:
            await self._handle_takeoff()

        elif self.drone.status == DroneStatus.IN_FLIGHT:
            await self._handle_flight()

        elif self.drone.status == DroneStatus.HOVERING:
            await self._handle_hover()

        elif self.drone.status == DroneStatus.LANDING:
            await self._handle_landing()

        elif self.drone.status == DroneStatus.RTH:
            await self._handle_rth()

        elif self.drone.status == DroneStatus.EMERGENCY:
            await self._handle_emergency()

        # Update physics
        self.physics_state = self.physics.update(
            self.physics_state,
            self.target_velocity,
            self.target_yaw,
            self.environment
        )

        # Check battery and trigger RTH if needed
        battery_pct = self.physics.get_battery_percentage(self.physics_state)
        if battery_pct < 20 and self.drone.status not in [DroneStatus.RTH, DroneStatus.LANDING, DroneStatus.EMERGENCY]:
            await self.initiate_rth("Low battery")

        # Generate telemetry
        telemetry = await self._generate_telemetry()

        # Store in history
        self.telemetry_history.append(telemetry)
        if len(self.telemetry_history) > 100:
            self.telemetry_history.pop(0)

        return telemetry

    async def start_mission(self, mission: Mission):
        """Start executing a mission"""
        self.current_mission = mission
        self.current_waypoint_index = 0
        self.mission_start_time = self.sim_time
        self.distance_traveled = 0.0

        # Arm and take off if not already in flight
        if self.drone.status == DroneStatus.IDLE:
            await self.arm()
            await self.takeoff(mission.waypoints[0].position.altitude if mission.waypoints else 10.0)

        self.drone.status = DroneStatus.IN_FLIGHT
        self.drone.mission_id = mission.id

    async def arm(self):
        """Arm the drone"""
        if self.drone.status == DroneStatus.IDLE:
            self.is_armed = True
            self.drone.status = DroneStatus.ARMED

    async def takeoff(self, altitude: float = 10.0):
        """Initiate takeoff"""
        if self.drone.status in [DroneStatus.ARMED, DroneStatus.IDLE]:
            self.takeoff_altitude = altitude
            self.drone.status = DroneStatus.TAKING_OFF
            self.target_position = Position3D(
                latitude=self.drone.position.latitude,
                longitude=self.drone.position.longitude,
                altitude=altitude
            )

    async def land(self):
        """Initiate landing"""
        if self.drone.status in [DroneStatus.IN_FLIGHT, DroneStatus.HOVERING, DroneStatus.RTH]:
            self.drone.status = DroneStatus.LANDING
            self.target_position = Position3D(
                latitude=self.physics_state.position[0],
                longitude=self.physics_state.position[1],
                altitude=0.0
            )

    async def initiate_rth(self, reason: str = "Manual"):
        """Initiate return to home"""
        self.drone.status = DroneStatus.RTH
        self.target_position = self.drone.home_position
        # TODO: Log event

    async def inject_failure(
        self,
        failure_type: FailureType,
        severity: float = 0.5,
        duration: Optional[float] = None
    ):
        """Inject a failure into the simulation"""
        self.active_failures[failure_type] = {
            'severity': severity,
            'duration': duration,
            'start_time': self.sim_time
        }

        # Handle specific failures
        if failure_type == FailureType.GPS_DRIFT:
            from .sensors import SensorType
            self.sensors.inject_failure(SensorType.GPS, severity, duration)

        elif failure_type == FailureType.BATTERY_DROP:
            # Instant battery drop
            drop_percentage = severity * 30  # Up to 30% drop
            drop_wh = (drop_percentage / 100) * self.physics.battery_capacity_wh
            self.physics_state.battery_wh = max(0, self.physics_state.battery_wh - drop_wh)

        elif failure_type == FailureType.COMM_LOSS:
            # Trigger emergency action
            await self._trigger_emergency_action(EmergencyAction.RTH)

        elif failure_type == FailureType.MOTOR_FAILURE:
            # Force emergency landing
            await self._trigger_emergency_action(EmergencyAction.LAND)

    async def _handle_takeoff(self):
        """Handle takeoff behavior"""
        current_alt = self.physics_state.position[2]

        if current_alt >= self.takeoff_altitude * 0.95:
            # Reached takeoff altitude
            self.drone.status = DroneStatus.HOVERING
            if self.current_mission:
                self.drone.status = DroneStatus.IN_FLIGHT
        else:
            # Climb to takeoff altitude
            self.target_velocity = np.array([0, 0, self.drone.spec.climb_rate])

    async def _handle_flight(self):
        """Handle in-flight navigation to waypoints"""
        if not self.current_mission or not self.current_mission.waypoints:
            # No mission, hover
            self.drone.status = DroneStatus.HOVERING
            return

        # Get current waypoint
        if self.current_waypoint_index >= len(self.current_mission.waypoints):
            # Mission complete
            await self._complete_mission()
            return

        waypoint = self.current_mission.waypoints[self.current_waypoint_index]

        # Calculate navigation to waypoint
        await self._navigate_to_waypoint(waypoint)

        # Check if reached waypoint
        if self._is_at_waypoint(waypoint):
            await self._handle_waypoint_reached(waypoint)

    async def _handle_hover(self):
        """Handle hovering behavior"""
        # Maintain current position
        self.target_velocity = np.zeros(3)

    async def _handle_landing(self):
        """Handle landing behavior"""
        current_alt = self.physics_state.position[2]

        if current_alt <= 0.5:
            # Touched down
            self.drone.status = DroneStatus.LANDED
            self.is_armed = False
            self.physics_state.velocity = np.zeros(3)
        else:
            # Descend
            self.target_velocity = np.array([0, 0, -self.drone.spec.descent_rate * 0.5])

    async def _handle_rth(self):
        """Handle return to home"""
        home = self.drone.home_position

        # Navigate to home at RTH altitude
        rth_alt = self.current_mission.parameters.rth_altitude if self.current_mission else 80.0

        current_pos = self.physics_state.position
        distance = self._calculate_distance(
            current_pos[0], current_pos[1],
            home.latitude, home.longitude
        )

        if distance < 5.0:
            # Close to home, initiate landing
            await self.land()
        else:
            # Navigate home
            bearing = self._calculate_bearing(
                current_pos[0], current_pos[1],
                home.latitude, home.longitude
            )
            speed = self.drone.spec.cruise_speed
            self.target_velocity[0] = speed * np.cos(np.radians(bearing))
            self.target_velocity[1] = speed * np.sin(np.radians(bearing))
            self.target_velocity[2] = (rth_alt - current_pos[2]) * 0.5
            self.target_yaw = bearing

    async def _handle_emergency(self):
        """Handle emergency state"""
        # Emergency land at current location
        await self.land()

    async def _navigate_to_waypoint(self, waypoint: Waypoint):
        """Calculate velocity to navigate to waypoint"""
        target_pos = waypoint.position
        current_pos = self.physics_state.position

        # Calculate bearing and distance
        bearing = self._calculate_bearing(
            current_pos[0], current_pos[1],
            target_pos.latitude, target_pos.longitude
        )
        distance = self._calculate_distance(
            current_pos[0], current_pos[1],
            target_pos.latitude, target_pos.longitude
        )

        # Calculate desired speed
        speed = waypoint.speed or self.current_mission.parameters.default_speed
        speed = min(speed, self.drone.spec.max_speed)

        # Slow down as approaching waypoint
        if distance < 10:
            speed *= (distance / 10)

        # Set target velocity
        self.target_velocity[0] = speed * np.cos(np.radians(bearing))
        self.target_velocity[1] = speed * np.sin(np.radians(bearing))
        self.target_velocity[2] = (target_pos.altitude - current_pos[2]) * 0.5

        # Set target yaw
        self.target_yaw = waypoint.heading if waypoint.heading is not None else bearing

    def _is_at_waypoint(self, waypoint: Waypoint, threshold: float = 2.0) -> bool:
        """Check if drone has reached waypoint"""
        current_pos = self.physics_state.position
        distance = self._calculate_distance(
            current_pos[0], current_pos[1],
            waypoint.position.latitude, waypoint.position.longitude
        )
        alt_diff = abs(current_pos[2] - waypoint.position.altitude)

        return distance < threshold and alt_diff < 2.0

    async def _handle_waypoint_reached(self, waypoint: Waypoint):
        """Handle actions when waypoint is reached"""
        # Execute waypoint actions
        for action in waypoint.actions:
            await self._execute_waypoint_action(action)

        # Loiter if specified
        if waypoint.loiter_time > 0:
            await asyncio.sleep(waypoint.loiter_time)

        # Move to next waypoint
        self.current_waypoint_index += 1

    async def _execute_waypoint_action(self, action):
        """Execute a waypoint action"""
        # TODO: Implement specific actions (photo, video, etc.)
        pass

    async def _complete_mission(self):
        """Handle mission completion"""
        if self.current_mission.parameters.finish_action == "rth":
            await self.initiate_rth("Mission complete")
        elif self.current_mission.parameters.finish_action == "land":
            await self.land()
        else:
            self.drone.status = DroneStatus.HOVERING

    async def _trigger_emergency_action(self, action: EmergencyAction):
        """Trigger an emergency action"""
        self.drone.status = DroneStatus.EMERGENCY

        if action == EmergencyAction.HOVER:
            self.drone.status = DroneStatus.HOVERING
        elif action == EmergencyAction.LAND:
            await self.land()
        elif action == EmergencyAction.RTH:
            await self.initiate_rth("Emergency")

    async def _generate_telemetry(self) -> Telemetry:
        """Generate current telemetry data"""
        # Simulate sensor readings
        measured_pos, gps_info = self.sensors.simulate_gps(
            self.physics_state.position,
            self.sim_time
        )

        measured_baro_alt = self.sensors.simulate_barometer(
            self.physics_state.position[2]
        )

        # Battery
        battery_pct = self.physics.get_battery_percentage(self.physics_state)
        power_w = self.physics._calculate_power_consumption(
            self.physics_state.velocity,
            self.environment
        )
        current_a = power_w / self.battery_model.voltage
        voltage = self.battery_model.get_voltage(
            battery_pct / 100.0,
            current_a,
            self.environment.temperature
        )
        remaining_time = int(self.physics.get_estimated_flight_time(
            self.physics_state,
            power_w
        ))

        battery_info = BatteryInfo(
            percentage=battery_pct,
            voltage=voltage,
            current=current_a,
            remaining_time=remaining_time
        )

        # Create telemetry
        telemetry = Telemetry(
            drone_id=self.drone.id,
            timestamp=datetime.utcnow(),
            position=measured_pos,
            velocity=Velocity3D(
                vx=self.physics_state.velocity[0],
                vy=self.physics_state.velocity[1],
                vz=self.physics_state.velocity[2]
            ),
            attitude=Attitude(
                roll=self.physics_state.attitude[0],
                pitch=self.physics_state.attitude[1],
                yaw=self.physics_state.attitude[2]
            ),
            status=self.drone.status,
            control_mode=self.drone.control_mode,
            battery=battery_info,
            gps=gps_info,
            environment=self.environment,
            mission_id=self.drone.mission_id,
            current_waypoint=self.current_waypoint_index if self.current_mission else None,
            distance_to_waypoint=self._get_distance_to_waypoint(),
            cpu_usage=np.random.uniform(20, 60),
            memory_usage=np.random.uniform(30, 70),
            temperature=25.0 + np.random.randn() * 2
        )

        return telemetry

    def _get_distance_to_waypoint(self) -> Optional[float]:
        """Get distance to current waypoint"""
        if not self.current_mission or self.current_waypoint_index >= len(self.current_mission.waypoints):
            return None

        waypoint = self.current_mission.waypoints[self.current_waypoint_index]
        return self._calculate_distance(
            self.physics_state.position[0],
            self.physics_state.position[1],
            waypoint.position.latitude,
            waypoint.position.longitude
        )

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two lat/lon points in meters"""
        # Haversine formula
        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    def _calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2 in degrees"""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dlambda = math.radians(lon2 - lon1)

        y = math.sin(dlambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)

        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
