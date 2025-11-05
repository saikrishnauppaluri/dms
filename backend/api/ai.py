"""
Edge-AI API endpoints
"""
from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import Optional

from models import AIModelConfig

router = APIRouter()


@router.post("/{drone_id}/enable")
async def enable_edge_ai(
    drone_id: UUID,
    model_name: str = "crack_detector",
    custom_config: Optional[AIModelConfig] = None
):
    """Enable edge-AI for a drone"""
    from core import get_edge_ai_manager, get_fleet_manager

    fleet = get_fleet_manager()
    if drone_id not in fleet.drones:
        raise HTTPException(status_code=404, detail="Drone not found")

    ai_manager = get_edge_ai_manager()
    simulator = ai_manager.create_simulator(drone_id, model_name, custom_config)

    return {
        "status": "enabled",
        "drone_id": str(drone_id),
        "model_name": simulator.config.model_name
    }


@router.delete("/{drone_id}/disable")
async def disable_edge_ai(drone_id: UUID):
    """Disable edge-AI for a drone"""
    from core import get_edge_ai_manager
    ai_manager = get_edge_ai_manager()
    ai_manager.remove_simulator(drone_id)
    return {"status": "disabled"}


@router.get("/{drone_id}/statistics")
async def get_ai_statistics(drone_id: UUID):
    """Get edge-AI statistics for a drone"""
    from core import get_edge_ai_manager
    ai_manager = get_edge_ai_manager()

    simulator = ai_manager.get_simulator(drone_id)
    if not simulator:
        raise HTTPException(status_code=404, detail="Edge-AI not enabled for this drone")

    return simulator.get_statistics()


@router.get("/statistics/all")
async def get_all_ai_statistics():
    """Get edge-AI statistics for all drones"""
    from core import get_edge_ai_manager
    ai_manager = get_edge_ai_manager()
    return ai_manager.get_all_statistics()


@router.get("/models")
async def list_available_models():
    """List available AI models"""
    from core import get_edge_ai_manager
    ai_manager = get_edge_ai_manager()

    models = []
    for name, config in ai_manager.default_configs.items():
        models.append({
            "name": name,
            "version": config.model_version,
            "type": config.model_type,
            "classes": config.classes
        })

    return {"models": models}
