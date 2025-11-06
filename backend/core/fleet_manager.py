"""
Fleet management for coordinating multiple drones
"""
import asyncio
from typing import Dict, List, Optional, Set
from uuid import UUID
import numpy as np
from datetime import datetime

from models import (
    Drone, DroneStatus, Mission, MissionStatus,
    Position3D, Telemetry, Alert, Event, EventSeverity
)
from .drone_simulator import DroneSimulator
from .environment import EnvironmentSimulator
from config import settings


class FleetManager:
    """
    Manages multiple drone simulators with:
    - Concurrent simulation
    - Conflict avoidance
    - Task assignment and re-assignment
    - Fleet health monitoring
    """

    def __init__(self):
        self.drones: Dict[UUID, Drone] = {}
        self.simulators: Dict[UUID, DroneSimulator] = {}
        self.missions: Dict[UUID, Mission] = {}
        self.environment = EnvironmentSimulator()

        # Fleet coordination
        self.min_separation = 20.0  # meters
        self.alert_separation = 30.0  # meters

        # Simulation control
        self.is_running = False
        self.update_task: Optional[asyncio.Task] = None
        self.sim_speed = 1.0  # Real-time multiplier

        # Event tracking
        self.events: List[Event] = []
        self.alerts: List[Alert] = []

    async def add_drone(self, drone: Drone) -> DroneSimulator:
        """Add a drone to the fleet"""
        if len(self.drones) >= settings.MAX_DRONES:
            raise ValueError(f"Maximum number of drones ({settings.MAX_DRONES}) reached")

        self.drones[drone.id] = drone

        # Create simulator
        env_data = self.environment.get_environment_at(
            drone.position.latitude,
            drone.position.longitude,
            datetime.utcnow()
        )
        simulator = DroneSimulator(drone, env_data)
        self.simulators[drone.id] = simulator

        # Log event
        await self._log_event(
            event_type="drone_added",
            severity=EventSeverity.INFO,
            source="fleet",
            source_id=drone.id,
            title=f"Drone {drone.name} added to fleet"
        )

        return simulator

    async def remove_drone(self, drone_id: UUID):
        """Remove a drone from the fleet"""
        if drone_id in self.drones:
            drone = self.drones[drone_id]
            del self.drones[drone_id]
            del self.simulators[drone_id]

            await self._log_event(
                event_type="drone_removed",
                severity=EventSeverity.INFO,
                source="fleet",
                source_id=drone_id,
                title=f"Drone {drone.name} removed from fleet"
            )

    async def add_mission(self, mission: Mission):
        """Add a mission to the fleet"""
        self.missions[mission.id] = mission

    async def assign_mission(self, mission_id: UUID, drone_ids: List[UUID], start_immediately: bool = False):
        """Assign mission to one or more drones"""
        if mission_id not in self.missions:
            raise ValueError(f"Mission {mission_id} not found")

        mission = self.missions[mission_id]

        # Assign to drones
        for drone_id in drone_ids:
            if drone_id not in self.drones:
                raise ValueError(f"Drone {drone_id} not found")

            drone = self.drones[drone_id]
            simulator = self.simulators[drone_id]

            # Check if drone is available
            if drone.status not in [DroneStatus.IDLE, DroneStatus.LANDED]:
                await self._create_alert(
                    alert_type="assignment_failed",
                    drone_id=drone_id,
                    mission_id=mission_id,
                    title=f"Cannot assign mission to {drone.name}",
                    message=f"Drone is currently {drone.status.value}"
                )
                continue

            # Assign mission
            drone.mission_id = mission_id
            if start_immediately:
                await simulator.start_mission(mission)

        mission.assigned_drone_ids = drone_ids
        mission.status = MissionStatus.ACTIVE if start_immediately else MissionStatus.READY

    async def start(self):
        """Start fleet simulation"""
        if self.is_running:
            return

        self.is_running = True
        self.update_task = asyncio.create_task(self._simulation_loop())

        await self._log_event(
            event_type="fleet_started",
            severity=EventSeverity.INFO,
            source="fleet",
            title="Fleet simulation started"
        )

    async def stop(self):
        """Stop fleet simulation"""
        if not self.is_running:
            return

        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # Set all drones to landed status when simulation stops
        for drone_id, drone in self.drones.items():
            if drone.status not in [DroneStatus.OFFLINE, DroneStatus.LANDED]:
                drone.status = DroneStatus.LANDED
                drone.mission_id = None
                simulator = self.simulators[drone_id]
                simulator.is_armed = False
                simulator.current_mission = None
                simulator.current_waypoint_index = 0

        # Update all missions to pending status
        for mission in self.missions.values():
            if mission.status == MissionStatus.ACTIVE:
                mission.status = MissionStatus.PENDING
                mission.assigned_drone_ids = []

        await self._log_event(
            event_type="fleet_stopped",
            severity=EventSeverity.INFO,
            source="fleet",
            title="Fleet simulation stopped"
        )

    async def _simulation_loop(self):
        """Main simulation loop"""
        dt = 1.0 / settings.PHYSICS_UPDATE_HZ

        while self.is_running:
            try:
                # Update all drone simulators
                update_tasks = [
                    simulator.update(dt * self.sim_speed)
                    for simulator in self.simulators.values()
                ]
                telemetry_list = await asyncio.gather(*update_tasks)

                # Check for conflicts
                await self._check_conflicts(telemetry_list)

                # Check for failures and auto-reassign if needed
                await self._check_drone_health()

                # Sleep for real-time sync
                await asyncio.sleep(dt / self.sim_speed)

            except Exception as e:
                await self._log_event(
                    event_type="simulation_error",
                    severity=EventSeverity.ERROR,
                    source="fleet",
                    title="Simulation error",
                    description=str(e)
                )

    async def _check_conflicts(self, telemetry_list: List[Telemetry]):
        """Check for potential drone conflicts"""
        positions = {}
        for telemetry in telemetry_list:
            if telemetry.status in [DroneStatus.IN_FLIGHT, DroneStatus.HOVERING]:
                positions[telemetry.drone_id] = telemetry.position

        # Check all pairs
        drone_ids = list(positions.keys())
        for i in range(len(drone_ids)):
            for j in range(i + 1, len(drone_ids)):
                drone_id1 = drone_ids[i]
                drone_id2 = drone_ids[j]

                pos1 = positions[drone_id1]
                pos2 = positions[drone_id2]

                distance = self._calculate_3d_distance(pos1, pos2)

                if distance < self.min_separation:
                    # Critical conflict - trigger emergency action
                    await self._handle_conflict(drone_id1, drone_id2, distance, critical=True)
                elif distance < self.alert_separation:
                    # Warning - create alert
                    await self._handle_conflict(drone_id1, drone_id2, distance, critical=False)

    async def _handle_conflict(
        self,
        drone_id1: UUID,
        drone_id2: UUID,
        distance: float,
        critical: bool
    ):
        """Handle conflict between two drones"""
        drone1 = self.drones.get(drone_id1)
        drone2 = self.drones.get(drone_id2)

        if not drone1 or not drone2:
            return

        if critical:
            # Emergency: command one drone to climb
            simulator1 = self.simulators[drone_id1]
            await simulator1.initiate_rth("Conflict avoidance")

            await self._log_event(
                event_type="conflict_critical",
                severity=EventSeverity.CRITICAL,
                source="fleet",
                title="Critical conflict detected",
                description=f"Drones {drone1.name} and {drone2.name} within {distance:.1f}m",
                data={
                    "drone_id1": str(drone_id1),
                    "drone_id2": str(drone_id2),
                    "distance": distance
                }
            )
        else:
            # Warning only
            await self._create_alert(
                alert_type="conflict_warning",
                title="Drones too close",
                message=f"Drones {drone1.name} and {drone2.name} within {distance:.1f}m",
                action_required=False
            )

    async def _check_drone_health(self):
        """Monitor drone health and handle failures"""
        for drone_id, drone in self.drones.items():
            simulator = self.simulators[drone_id]

            # Check if drone failed during mission
            if drone.status == DroneStatus.EMERGENCY and drone.mission_id:
                mission = self.missions.get(drone.mission_id)
                if mission and mission.status == MissionStatus.ACTIVE:
                    # Try to reassign to another drone
                    await self._reassign_mission(mission, failed_drone_id=drone_id)

    async def _reassign_mission(self, mission: Mission, failed_drone_id: UUID):
        """Reassign mission from failed drone to available drone"""
        # Find available drones
        available_drones = [
            drone_id for drone_id, drone in self.drones.items()
            if drone.status in [DroneStatus.IDLE, DroneStatus.LANDED]
            and drone_id != failed_drone_id
        ]

        if not available_drones:
            await self._log_event(
                event_type="reassignment_failed",
                severity=EventSeverity.ERROR,
                source="fleet",
                source_id=mission.id,
                title="Mission reassignment failed",
                description="No available drones for reassignment"
            )
            mission.status = MissionStatus.FAILED
            return

        # Assign to first available drone
        new_drone_id = available_drones[0]
        await self.assign_mission(mission.id, [new_drone_id], start_immediately=True)

        await self._log_event(
            event_type="mission_reassigned",
            severity=EventSeverity.WARNING,
            source="fleet",
            source_id=mission.id,
            title="Mission reassigned",
            description=f"Mission reassigned from {failed_drone_id} to {new_drone_id}"
        )

    async def get_fleet_status(self) -> Dict:
        """Get current fleet status"""
        status_counts = {}
        for drone in self.drones.values():
            status = drone.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_drones": len(self.drones),
            "active_drones": sum(1 for d in self.drones.values() if d.status != DroneStatus.OFFLINE),
            "status_breakdown": status_counts,
            "active_missions": sum(1 for m in self.missions.values() if m.status == MissionStatus.ACTIVE),
            "is_running": self.is_running,
            "sim_speed": self.sim_speed
        }

    async def get_telemetry_all(self) -> Dict[UUID, Telemetry]:
        """Get current telemetry for all drones"""
        telemetry = {}
        for drone_id, simulator in self.simulators.items():
            if simulator.telemetry_history:
                telemetry[drone_id] = simulator.telemetry_history[-1]
        return telemetry

    async def _log_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        title: str,
        source_id: Optional[UUID] = None,
        description: Optional[str] = None,
        data: Optional[Dict] = None
    ):
        """Log an event"""
        event = Event(
            event_type=event_type,
            severity=severity,
            source=source,
            source_id=source_id,
            title=title,
            description=description,
            data=data or {}
        )
        self.events.append(event)

        # Keep only recent events
        if len(self.events) > 1000:
            self.events = self.events[-1000:]

    async def _create_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        drone_id: Optional[UUID] = None,
        mission_id: Optional[UUID] = None,
        action_required: bool = False,
        severity: str = EventSeverity.WARNING
    ):
        """Create an alert"""
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            drone_id=drone_id,
            mission_id=mission_id,
            title=title,
            message=message,
            action_required=action_required
        )
        self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 500:
            self.alerts = self.alerts[-500:]

    @staticmethod
    def _calculate_3d_distance(pos1: Position3D, pos2: Position3D) -> float:
        """Calculate 3D distance between two positions"""
        # Approximate conversion for small distances
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000 * np.cos(np.radians(pos1.latitude))
        alt_diff = pos2.altitude - pos1.altitude

        return np.sqrt(lat_diff ** 2 + lon_diff ** 2 + alt_diff ** 2)


# Singleton instance
_fleet_manager: Optional[FleetManager] = None


def get_fleet_manager() -> FleetManager:
    """Get the global fleet manager instance"""
    global _fleet_manager
    if _fleet_manager is None:
        _fleet_manager = FleetManager()
    return _fleet_manager
