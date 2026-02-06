"""
Devices API router
"""

from typing import List
from fastapi import APIRouter, HTTPException
from src.models.schemas import Device, DeviceCreate, DeviceUpdate
from src.services.simulation_engine import simulation_engine

router = APIRouter()


@router.get("/", response_model=List[Device])
async def get_devices():
    """Get all devices"""
    return simulation_engine.get_devices()


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str):
    """Get device by ID"""
    devices = simulation_engine.get_devices()
    device = next((d for d in devices if d["id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/", response_model=Device, status_code=201)
async def create_device(device: DeviceCreate):
    """Create a new device"""
    new_device = {
        "id": f"device-{len(simulation_engine.get_devices()) + 1}",
        "name": device.name,
        "type": device.type.value,
        "ip": device.ip,
        "protocols": [p.value for p in device.protocols],
        "status": "online",
        "metadata": device.metadata,
    }
    return new_device


@router.put("/{device_id}", response_model=Device)
async def update_device(device_id: str, updates: DeviceUpdate):
    """Update device"""
    devices = simulation_engine.get_devices()
    index = next((i for i, d in enumerate(devices) if d["id"] == device_id), -1)
    
    if index == -1:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if updates.name:
        devices[index]["name"] = updates.name
    if updates.status:
        devices[index]["status"] = updates.status.value if hasattr(updates.status, 'value') else updates.status
    if updates.metadata:
        devices[index]["metadata"] = updates.metadata
    
    return devices[index]


@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: str):
    """Delete device"""
    # In simulation mode, we don't actually delete, just mark as offline
    devices = simulation_engine.get_devices()
    index = next((i for i, d in enumerate(devices) if d["id"] == device_id), -1)
    
    if index == -1:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Mark as offline instead of deleting
    devices[index]["status"] = "offline"
    return None


@router.get("/{device_id}/status")
async def get_device_status(device_id: str):
    """Get device status"""
    devices = simulation_engine.get_devices()
    device = next((d for d in devices if d["id"] == device_id), None)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "id": device["id"],
        "status": device["status"],
        "last_seen": "2024-01-01T00:00:00",
    }
