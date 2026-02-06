"""
Packets API router
"""

from typing import List
from fastapi import APIRouter
from src.models.schemas import Packet
from src.services.simulation_engine import simulation_engine

router = APIRouter()


@router.get("/", response_model=List[Packet])
async def get_packets(limit: int = 100):
    """Get recent packets"""
    return simulation_engine.get_packets(limit)


@router.get("/{packet_id}", response_model=Packet)
async def get_packet(packet_id: str):
    """Get packet by ID"""
    packets = simulation_engine.get_packets()
    packet = next((p for p in packets if p.id == packet_id), None)
    if not packet:
        raise HTTPException(status_code=404, detail="Packet not found")
    return packet


@router.delete("/", status_code=204)
async def clear_packets():
    """Clear all packets"""
    simulation_engine.clear_packets()
    return None
