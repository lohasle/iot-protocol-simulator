"""
Metrics API router
"""

from typing import List
from fastapi import APIRouter
from src.models.schemas import Metric
from src.services.simulation_engine import simulation_engine

router = APIRouter()


@router.get("/", response_model=List[Metric])
async def get_metrics():
    """Get all current metrics"""
    metrics = simulation_engine.get_metrics()
    return [
        Metric(name=name, value=value)
        for name, value in metrics.items()
    ]


@router.get("/{name}", response_model=Metric)
async def get_metric(name: str):
    """Get specific metric by name"""
    metrics = simulation_engine.get_metrics()
    if name not in metrics:
        raise HTTPException(status_code=404, detail="Metric not found")
    return Metric(name=name, value=metrics[name])


@router.get("/{name}/history")
async def get_metric_history(name: str, duration: str = "1h"):
    """Get metric history (placeholder)"""
    # In a real implementation, this would query a time-series database
    return [
        Metric(name=name, value=value)
        for value in [100, 120, 110, 130, 125]
    ]
