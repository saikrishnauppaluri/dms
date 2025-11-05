"""
Tests for physics engine
"""
import pytest
import numpy as np

from core.physics import PhysicsEngine, BatteryModel
from models import DroneSpec, Position3D, EnvironmentInfo, WindInfo


@pytest.fixture
def drone_spec():
    """Create a sample drone specification"""
    return DroneSpec(
        model="Test Drone",
        max_speed=15.0,
        max_altitude=120.0,
        max_flight_time=1800,
        battery_capacity=5000.0,
        weight=1.5,
        payload_capacity=0.5
    )


@pytest.fixture
def physics_engine(drone_spec):
    """Create a physics engine instance"""
    return PhysicsEngine(drone_spec)


def test_physics_engine_initialization(physics_engine, drone_spec):
    """Test physics engine initialization"""
    assert physics_engine.spec == drone_spec
    assert physics_engine.dt > 0
    assert physics_engine.gravity == 9.81


def test_init_state(physics_engine):
    """Test initial state creation"""
    position = Position3D(latitude=37.7749, longitude=-122.4194, altitude=0.0)
    state = physics_engine.init_state(position)

    assert state.position[0] == position.latitude
    assert state.position[1] == position.longitude
    assert state.position[2] == position.altitude
    assert np.all(state.velocity == 0)
    assert state.battery_wh > 0


def test_physics_update(physics_engine):
    """Test physics state update"""
    position = Position3D(latitude=37.7749, longitude=-122.4194, altitude=0.0)
    state = physics_engine.init_state(position)

    environment = EnvironmentInfo(
        temperature=20.0,
        pressure=1013.25,
        humidity=50.0,
        wind=WindInfo(speed=0.0, direction=0.0, gust_speed=0.0)
    )

    # Update with upward velocity
    target_velocity = np.array([0, 0, 3.0])  # Climb at 3 m/s
    new_state = physics_engine.update(state, target_velocity, 0.0, environment)

    # Check that altitude increased
    assert new_state.position[2] > state.position[2]

    # Check that battery decreased
    assert new_state.battery_wh < state.battery_wh


def test_battery_discharge(physics_engine):
    """Test battery discharge over time"""
    position = Position3D(latitude=37.7749, longitude=-122.4194, altitude=50.0)
    state = physics_engine.init_state(position)
    initial_battery = state.battery_wh

    environment = EnvironmentInfo(
        temperature=20.0,
        pressure=1013.25,
        humidity=50.0,
        wind=WindInfo(speed=0.0, direction=0.0, gust_speed=0.0)
    )

    # Hover for 10 seconds (10 * 50 updates)
    for _ in range(500):
        state = physics_engine.update(
            state,
            np.zeros(3),  # Hover
            0.0,
            environment
        )

    # Battery should have decreased
    assert state.battery_wh < initial_battery


def test_battery_percentage(physics_engine):
    """Test battery percentage calculation"""
    position = Position3D(latitude=37.7749, longitude=-122.4194, altitude=0.0)
    state = physics_engine.init_state(position)

    percentage = physics_engine.get_battery_percentage(state)
    assert 95 <= percentage <= 100  # Should be nearly full


def test_battery_model():
    """Test battery model"""
    battery = BatteryModel(capacity_mah=5000.0, voltage=22.2)

    # Test voltage at different states of charge
    voltage_full = battery.get_voltage(1.0, 0.0, 20.0)
    voltage_half = battery.get_voltage(0.5, 0.0, 20.0)
    voltage_low = battery.get_voltage(0.2, 0.0, 20.0)

    # Voltage should decrease with discharge
    assert voltage_full > voltage_half > voltage_low


def test_wind_effect(physics_engine):
    """Test wind effect on drone"""
    position = Position3D(latitude=37.7749, longitude=-122.4194, altitude=50.0)
    state = physics_engine.init_state(position)

    # Strong wind environment
    environment = EnvironmentInfo(
        temperature=20.0,
        pressure=1013.25,
        humidity=50.0,
        wind=WindInfo(speed=10.0, direction=90.0, gust_speed=5.0)
    )

    # Try to hover
    initial_pos = state.position.copy()
    for _ in range(100):
        state = physics_engine.update(
            state,
            np.zeros(3),
            0.0,
            environment
        )

    # Drone should drift due to wind
    position_change = np.linalg.norm(state.position[:2] - initial_pos[:2])
    assert position_change > 0  # Some drift occurred


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
