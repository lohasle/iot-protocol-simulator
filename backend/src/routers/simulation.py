"""
Simulation API router
"""

from datetime import datetime
from fastapi import APIRouter
from src.models.schemas import SimulationState
from src.services.simulation_engine import simulation_engine

router = APIRouter()


@router.get("/state", response_model=SimulationState)
async def get_simulation_state():
    """Get current simulation state"""
    return SimulationState(
        running=simulation_engine.is_running,
        start_time=datetime.utcnow() if simulation_engine.is_running else None,
        packets_per_second=simulation_engine.get_metrics().get("msg_rate", 0),
        active_devices=len(simulation_engine.get_devices()),
    )


@router.post("/start")
async def start_simulation():
    """Start the simulation"""
    if not simulation_engine.is_running:
        simulation_engine.start()
    return {"message": "Simulation started"}


@router.post("/stop")
async def stop_simulation():
    """Stop the simulation"""
    if simulation_engine.is_running:
        simulation_engine.stop()
    return {"message": "Simulation stopped"}


@router.post("/reset")
async def reset_simulation():
    """Reset the simulation"""
    simulation_engine.stop()
    simulation_engine.start()
    return {"message": "Simulation reset"}
