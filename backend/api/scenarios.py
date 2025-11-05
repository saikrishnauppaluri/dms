"""
Scenarios API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()


@router.get("/")
async def list_scenarios():
    """List all available scenarios"""
    from scenarios import get_all_scenarios

    scenarios = get_all_scenarios()

    # Return summary info
    summary = []
    for scenario_id, scenario in scenarios.items():
        summary.append({
            "id": scenario_id,
            "name": scenario["name"],
            "description": scenario["description"],
            "num_drones": len(scenario.get("drones", [])),
            "expected_duration": scenario.get("expected_duration", 0)
        })

    return {"scenarios": summary}


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get specific scenario"""
    from scenarios import get_scenario as get_scenario_func

    scenario = get_scenario_func(scenario_id)

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return scenario


@router.post("/{scenario_id}/load")
async def load_scenario(scenario_id: str):
    """Load and activate a scenario"""
    from scenarios import get_scenario as get_scenario_func
    from core import get_fleet_manager, get_edge_ai_manager

    scenario = get_scenario_func(scenario_id)

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    fleet = get_fleet_manager()
    ai_manager = get_edge_ai_manager()

    # Add drones
    drone_ids = []
    for drone_data in scenario.get("drones", []):
        simulator = await fleet.add_drone(drone_data)
        drone_ids.append(drone_data.id)

        # Enable AI if specified
        if "ai_model" in scenario:
            ai_manager.create_simulator(drone_data.id, scenario["ai_model"])

    # Add mission(s)
    if "mission" in scenario:
        mission = scenario["mission"]
        await fleet.add_mission(mission)
        # Assign to all drones
        await fleet.assign_mission(mission.id, drone_ids, start_immediately=False)

    elif "missions" in scenario:
        for i, mission in enumerate(scenario["missions"]):
            await fleet.add_mission(mission)
            if i < len(drone_ids):
                await fleet.assign_mission(mission.id, [drone_ids[i]], start_immediately=False)

    # Set environment if specified
    if "environment" in scenario:
        env_data = scenario["environment"]
        fleet.environment.set_wind(
            env_data.get("wind_speed", 5.0),
            env_data.get("wind_direction", 0.0),
            env_data.get("gust_speed", 0.0)
        )

    # Start fleet
    await fleet.start()

    return {
        "status": "loaded",
        "scenario_id": scenario_id,
        "drones_created": len(drone_ids),
        "missions_created": 1 if "mission" in scenario else len(scenario.get("missions", []))
    }
