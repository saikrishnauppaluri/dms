"""
Pre-built simulation scenarios
"""
from typing import Dict, List
from uuid import uuid4

from models import (
    Mission, Waypoint, Position3D, MissionParameters,
    GeofenceZone, WaypointAction, DroneSpec, Drone,
    ControlMode, DroneStatus, BatteryInfo, GPSInfo
)


class ScenarioBuilder:
    """Builder for simulation scenarios"""

    @staticmethod
    def create_standard_bridge_inspection() -> Dict:
        """
        Scenario 1: Standard Bridge Inspection
        Single drone, 10 waypoints, 30m altitude, edge-AI detects cracks
        """
        # Bridge location (example coordinates)
        base_lat = 37.7749
        base_lon = -122.4194

        waypoints = []
        for i in range(10):
            waypoints.append(Waypoint(
                sequence=i,
                position=Position3D(
                    latitude=base_lat + (i * 0.0001),
                    longitude=base_lon,
                    altitude=30.0
                ),
                speed=5.0,
                gimbal_pitch=-45.0,
                actions=[
                    WaypointAction(
                        type="photo",
                        parameters={"interval": 2.0}
                    )
                ],
                loiter_time=3.0
            ))

        mission = Mission(
            name="Standard Bridge Inspection",
            description="Inspect bridge structure with crack detection",
            waypoints=waypoints,
            home_position=Position3D(
                latitude=base_lat,
                longitude=base_lon,
                altitude=0.0
            ),
            parameters=MissionParameters(
                default_speed=5.0,
                default_altitude=30.0,
                rth_altitude=50.0
            ),
            scenario_id="bridge_inspection"
        )

        # Drone spec
        drone = Drone(
            name="Bridge Inspector 1",
            spec=DroneSpec(
                model="DJI Matrice 300",
                max_speed=17.0,
                max_altitude=120.0,
                max_flight_time=3300,
                battery_capacity=5880.0,
                weight=6.3,
                payload_capacity=2.7
            ),
            home_position=mission.home_position,
            position=mission.home_position,
            status=DroneStatus.IDLE,
            control_mode=ControlMode.AUTONOMOUS,
            battery=BatteryInfo(percentage=100.0, voltage=52.8),
            gps=GPSInfo(satellites=18, hdop=0.8, fix_type=3)
        )

        return {
            "id": "bridge_inspection",
            "name": "Standard Bridge Inspection",
            "description": "Single drone bridge inspection with crack detection",
            "mission": mission,
            "drones": [drone],
            "ai_model": "crack_detector",
            "expected_duration": 600  # seconds
        }

    @staticmethod
    def create_multi_drone_tower_inspection() -> Dict:
        """
        Scenario 2: Multi-Drone Tower Inspection
        3 drones coordinate to inspect transmission tower
        One experiences GPS drift
        """
        base_lat = 37.7800
        base_lon = -122.4100

        # Create 3 missions for different tower sides
        missions = []
        drones = []

        for i in range(3):
            angle = i * 120  # 120 degrees apart

            waypoints = []
            for j in range(8):
                alt = 10 + (j * 5)  # Climb tower
                lat_offset = 0.0001 * (i + 1)
                lon_offset = 0.0001 * (i + 1)

                waypoints.append(Waypoint(
                    sequence=j,
                    position=Position3D(
                        latitude=base_lat + lat_offset,
                        longitude=base_lon + lon_offset,
                        altitude=alt
                    ),
                    speed=3.0,
                    heading=angle,
                    gimbal_pitch=-30.0,
                    actions=[
                        WaypointAction(
                            type="photo",
                            parameters={}
                        )
                    ],
                    loiter_time=2.0
                ))

            mission = Mission(
                name=f"Tower Inspection Side {i+1}",
                description=f"Inspect tower from side {i+1}",
                waypoints=waypoints,
                home_position=Position3D(
                    latitude=base_lat + lat_offset,
                    longitude=base_lon + lon_offset,
                    altitude=0.0
                ),
                parameters=MissionParameters(
                    default_speed=3.0,
                    max_distance=100.0
                ),
                scenario_id="tower_inspection"
            )
            missions.append(mission)

            # Create drone
            drone = Drone(
                name=f"Tower Inspector {i+1}",
                spec=DroneSpec(
                    model="DJI Mavic 3 Enterprise",
                    max_speed=19.0,
                    max_altitude=120.0,
                    max_flight_time=2700,
                    battery_capacity=5000.0,
                    weight=1.0,
                    payload_capacity=0.5
                ),
                home_position=mission.home_position,
                position=mission.home_position,
                status=DroneStatus.IDLE,
                control_mode=ControlMode.AUTONOMOUS,
                battery=BatteryInfo(percentage=100.0, voltage=15.4),
                gps=GPSInfo(satellites=16, hdop=1.0, fix_type=3)
            )
            drones.append(drone)

        return {
            "id": "tower_inspection",
            "name": "Multi-Drone Tower Inspection",
            "description": "3 drones coordinate tower inspection, one with GPS drift",
            "missions": missions,
            "drones": drones,
            "failures": [
                {
                    "drone_index": 1,
                    "type": "gps_drift",
                    "delay": 120,
                    "severity": 0.6
                }
            ],
            "expected_duration": 480
        }

    @staticmethod
    def create_bvlos_corridor_mission() -> Dict:
        """
        Scenario 3: BVLOS Corridor Mission
        Long-range flight with wind and battery depletion
        """
        start_lat = 37.7900
        start_lon = -122.4000

        # Long corridor
        waypoints = []
        for i in range(15):
            waypoints.append(Waypoint(
                sequence=i,
                position=Position3D(
                    latitude=start_lat + (i * 0.001),  # ~1.5 km total
                    longitude=start_lon,
                    altitude=80.0
                ),
                speed=12.0,
                actions=[
                    WaypointAction(
                        type="video_start" if i == 0 else "video_stop" if i == 14 else "photo",
                        parameters={}
                    )
                ]
            ))

        mission = Mission(
            name="BVLOS Corridor Mission",
            description="Long-range corridor inspection",
            waypoints=waypoints,
            home_position=Position3D(
                latitude=start_lat,
                longitude=start_lon,
                altitude=0.0
            ),
            parameters=MissionParameters(
                default_speed=12.0,
                rth_altitude=100.0,
                max_distance=2000.0
            ),
            scenario_id="bvlos_corridor"
        )

        drone = Drone(
            name="Long Range Scout",
            spec=DroneSpec(
                model="DJI Matrice 30T",
                max_speed=23.0,
                max_altitude=120.0,
                max_flight_time=2460,
                battery_capacity=5880.0,
                weight=3.7,
                payload_capacity=0.4
            ),
            home_position=mission.home_position,
            position=mission.home_position,
            status=DroneStatus.IDLE,
            control_mode=ControlMode.AUTONOMOUS,
            battery=BatteryInfo(percentage=85.0, voltage=44.4),  # Not full charge
            gps=GPSInfo(satellites=20, hdop=0.7, fix_type=3)
        )

        return {
            "id": "bvlos_corridor",
            "name": "BVLOS Corridor Mission",
            "description": "Long-range mission with wind and battery management",
            "mission": mission,
            "drones": [drone],
            "environment": {
                "wind_speed": 8.0,
                "wind_direction": 90.0,
                "gust_speed": 12.0
            },
            "expected_duration": 900
        }

    @staticmethod
    def create_urban_smart_city_patrol() -> Dict:
        """
        Scenario 4: Urban Smart-City Patrol
        Multiple drones, dynamic obstacles, geofence
        """
        center_lat = 37.7850
        center_lon = -122.4050

        # Define geofence
        geofence = GeofenceZone(
            type="polygon",
            coordinates=[
                Position3D(latitude=center_lat + 0.001, longitude=center_lon + 0.001, altitude=0),
                Position3D(latitude=center_lat + 0.001, longitude=center_lon - 0.001, altitude=0),
                Position3D(latitude=center_lat - 0.001, longitude=center_lon - 0.001, altitude=0),
                Position3D(latitude=center_lat - 0.001, longitude=center_lon + 0.001, altitude=0)
            ],
            altitude_min=5.0,
            altitude_max=100.0,
            action="rth"
        )

        # Grid patrol pattern
        waypoints = []
        grid_size = 5
        idx = 0
        for i in range(grid_size):
            for j in range(grid_size):
                waypoints.append(Waypoint(
                    sequence=idx,
                    position=Position3D(
                        latitude=center_lat + (i - 2) * 0.0002,
                        longitude=center_lon + (j - 2) * 0.0002,
                        altitude=50.0
                    ),
                    speed=8.0,
                    gimbal_pitch=-60.0
                ))
                idx += 1

        mission = Mission(
            name="Urban Patrol",
            description="Smart city surveillance patrol",
            waypoints=waypoints,
            home_position=Position3D(
                latitude=center_lat,
                longitude=center_lon,
                altitude=0.0
            ),
            parameters=MissionParameters(
                default_speed=8.0,
                default_altitude=50.0
            ),
            geofence_zones=[geofence],
            scenario_id="urban_patrol"
        )

        drones = []
        for i in range(2):
            drone = Drone(
                name=f"City Patrol {i+1}",
                spec=DroneSpec(
                    model="Autel EVO II",
                    max_speed=20.0,
                    max_altitude=120.0,
                    max_flight_time=2400,
                    battery_capacity=7100.0,
                    weight=1.1,
                    payload_capacity=0.3
                ),
                home_position=Position3D(
                    latitude=center_lat + (i * 0.0001),
                    longitude=center_lon,
                    altitude=0.0
                ),
                position=Position3D(
                    latitude=center_lat + (i * 0.0001),
                    longitude=center_lon,
                    altitude=0.0
                ),
                status=DroneStatus.IDLE,
                control_mode=ControlMode.AUTONOMOUS,
                battery=BatteryInfo(percentage=100.0, voltage=11.6),
                gps=GPSInfo(satellites=17, hdop=0.9, fix_type=3)
            )
            drones.append(drone)

        return {
            "id": "urban_patrol",
            "name": "Urban Smart-City Patrol",
            "description": "Multi-drone patrol with geofencing and dynamic obstacles",
            "mission": mission,
            "drones": drones,
            "ai_model": "object_detector",
            "obstacles": [
                {"type": "crane", "delay": 180}
            ],
            "expected_duration": 720
        }

    @staticmethod
    def create_ehs_safety_sweep() -> Dict:
        """
        Scenario 5: EHS Safety Sweep
        PPE violation detection on construction site
        """
        site_lat = 37.7750
        site_lon = -122.4150

        # Sweep pattern over site
        waypoints = []
        for i in range(6):
            for j in range(6):
                waypoints.append(Waypoint(
                    sequence=i * 6 + j,
                    position=Position3D(
                        latitude=site_lat + (i * 0.00015),
                        longitude=site_lon + (j * 0.00015),
                        altitude=25.0
                    ),
                    speed=4.0,
                    gimbal_pitch=-75.0,
                    actions=[
                        WaypointAction(
                            type="photo",
                            parameters={"ai_detect": True}
                        )
                    ],
                    loiter_time=2.0
                ))

        mission = Mission(
            name="EHS Safety Inspection",
            description="Construction site safety sweep for PPE compliance",
            waypoints=waypoints,
            home_position=Position3D(
                latitude=site_lat,
                longitude=site_lon,
                altitude=0.0
            ),
            parameters=MissionParameters(
                default_speed=4.0,
                default_altitude=25.0
            ),
            scenario_id="ehs_safety"
        )

        drone = Drone(
            name="Safety Inspector",
            spec=DroneSpec(
                model="DJI Mavic 2 Enterprise",
                max_speed=18.0,
                max_altitude=120.0,
                max_flight_time=1860,
                battery_capacity=3850.0,
                weight=0.9,
                payload_capacity=0.2
            ),
            home_position=mission.home_position,
            position=mission.home_position,
            status=DroneStatus.IDLE,
            control_mode=ControlMode.AUTONOMOUS,
            battery=BatteryInfo(percentage=100.0, voltage=15.4),
            gps=GPSInfo(satellites=18, hdop=0.8, fix_type=3)
        )

        return {
            "id": "ehs_safety",
            "name": "EHS Safety Sweep",
            "description": "Construction site safety inspection with PPE detection",
            "mission": mission,
            "drones": [drone],
            "ai_model": "ppe_detector",
            "expected_duration": 540
        }

    @staticmethod
    def create_failure_stress_test() -> Dict:
        """
        Scenario 6: Failure Stress Test
        Random failures to test failover and recovery
        """
        base_lat = 37.7800
        base_lon = -122.4200

        # Complex mission pattern
        waypoints = []
        for i in range(20):
            waypoints.append(Waypoint(
                sequence=i,
                position=Position3D(
                    latitude=base_lat + (i % 5) * 0.0002,
                    longitude=base_lon + (i // 5) * 0.0002,
                    altitude=40.0 + (i % 3) * 10
                ),
                speed=10.0
            ))

        missions = []
        drones = []

        for i in range(3):
            mission = Mission(
                name=f"Stress Test Mission {i+1}",
                description="Failure stress test mission",
                waypoints=waypoints,
                home_position=Position3D(
                    latitude=base_lat + (i * 0.00005),
                    longitude=base_lon,
                    altitude=0.0
                ),
                parameters=MissionParameters(
                    default_speed=10.0
                ),
                scenario_id="stress_test"
            )
            missions.append(mission)

            drone = Drone(
                name=f"Stress Test Drone {i+1}",
                spec=DroneSpec(
                    model="Generic Quadcopter",
                    max_speed=15.0,
                    max_altitude=120.0,
                    max_flight_time=1800,
                    battery_capacity=5000.0,
                    weight=1.5,
                    payload_capacity=0.5
                ),
                home_position=mission.home_position,
                position=mission.home_position,
                status=DroneStatus.IDLE,
                control_mode=ControlMode.AUTONOMOUS,
                battery=BatteryInfo(percentage=100.0, voltage=22.2),
                gps=GPSInfo(satellites=15, hdop=1.2, fix_type=3)
            )
            drones.append(drone)

        return {
            "id": "stress_test",
            "name": "Failure Stress Test",
            "description": "Test failover with random comm dropouts, motor failures, and emergency landings",
            "missions": missions,
            "drones": drones,
            "failures": [
                {"drone_index": 0, "type": "comm_loss", "delay": 60, "severity": 0.8, "duration": 30},
                {"drone_index": 1, "type": "battery_drop", "delay": 120, "severity": 0.5},
                {"drone_index": 2, "type": "motor_failure", "delay": 180, "severity": 1.0}
            ],
            "expected_duration": 600
        }


def get_all_scenarios() -> Dict[str, Dict]:
    """Get all available scenarios"""
    builder = ScenarioBuilder()

    return {
        "bridge_inspection": builder.create_standard_bridge_inspection(),
        "tower_inspection": builder.create_multi_drone_tower_inspection(),
        "bvlos_corridor": builder.create_bvlos_corridor_mission(),
        "urban_patrol": builder.create_urban_smart_city_patrol(),
        "ehs_safety": builder.create_ehs_safety_sweep(),
        "stress_test": builder.create_failure_stress_test()
    }


def get_scenario(scenario_id: str) -> Dict:
    """Get specific scenario by ID"""
    scenarios = get_all_scenarios()
    return scenarios.get(scenario_id)
