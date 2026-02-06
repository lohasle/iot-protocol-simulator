"""
Protocols API router
"""

from typing import List
from fastapi import APIRouter, HTTPException
from src.models.schemas import ProtocolConfig, ProtocolStatus, ProtocolType

router = APIRouter()

# Protocol configurations
protocol_configs = {
    ProtocolType.MODBUS: {"port": 502, "enabled": True},
    ProtocolType.MQTT: {"port": 1883, "enabled": True},
    ProtocolType.OPCUA: {"port": 4840, "enabled": True},
    ProtocolType.BACnet: {"port": 47808, "enabled": True},
    ProtocolType.COAP: {"port": 5683, "enabled": True},
    ProtocolType.TCP: {"port": 8080, "enabled": False},
}


@router.get("/", response_model=List[ProtocolConfig])
async def get_protocols():
    """Get all protocol configurations"""
    return [
        ProtocolConfig(
            protocol=proto,
            enabled=config["enabled"],
            port=config["port"],
            settings={},
        )
        for proto, config in protocol_configs.items()
    ]


@router.get("/{protocol}", response_model=ProtocolStatus)
async def get_protocol_status(protocol: str):
    """Get protocol status"""
    try:
        proto = ProtocolType(protocol)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid protocol")
    
    config = protocol_configs.get(proto, {"port": 0, "enabled": False})
    
    return ProtocolStatus(
        protocol=proto,
        running=config["enabled"],
        port=config["port"],
        connections=0,
        message_rate=0.0,
    )


@router.put("/{protocol}", response_model=ProtocolConfig)
async def update_protocol_config(protocol: str, config: ProtocolConfig):
    """Update protocol configuration"""
    try:
        proto = ProtocolType(protocol)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid protocol")
    
    if proto not in protocol_configs:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    protocol_configs[proto] = {
        "enabled": config.enabled,
        "port": config.port,
        "settings": config.settings,
    }
    
    return config


@router.post("/{protocol}/start", response_model=ProtocolStatus)
async def start_protocol(protocol: str):
    """Start protocol simulation"""
    try:
        proto = ProtocolType(protocol)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid protocol")
    
    if proto not in protocol_configs:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    protocol_configs[proto]["enabled"] = True
    
    return ProtocolStatus(
        protocol=proto,
        running=True,
        port=protocol_configs[proto]["port"],
        connections=0,
        message_rate=100.0,
    )


@router.post("/{protocol}/stop", response_model=ProtocolStatus)
async def stop_protocol(protocol: str):
    """Stop protocol simulation"""
    try:
        proto = ProtocolType(protocol)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid protocol")
    
    if proto not in protocol_configs:
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    protocol_configs[proto]["enabled"] = False
    
    return ProtocolStatus(
        protocol=proto,
        running=False,
        port=protocol_configs[proto]["port"],
        connections=0,
        message_rate=0.0,
    )
