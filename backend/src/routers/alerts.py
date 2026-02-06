"""
Alerts API router
"""

from typing import List
from fastapi import APIRouter, HTTPException
from src.models.schemas import Alert

router = APIRouter()

# In-memory alerts storage
alerts_storage = []


@router.get("/", response_model=List[Alert])
async def get_alerts(limit: int = 50):
    """Get all alerts"""
    return alerts_storage[:limit]


@router.delete("/{alert_id}", status_code=204)
async def dismiss_alert(alert_id: str):
    """Dismiss/remove an alert"""
    global alerts_storage
    index = next((i for i, a in enumerate(alerts_storage) if a.id == alert_id), -1)
    
    if index == -1:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alerts_storage.pop(index)
    return None


@router.delete("/", status_code=204)
async def clear_alerts():
    """Clear all alerts"""
    global alerts_storage
    alerts_storage.clear()
    return None
