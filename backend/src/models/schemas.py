"""
Pydantic models for IoT Protocol Simulator
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    PLC = "plc"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    GATEWAY = "gateway"
    SERVER = "server"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class ProtocolType(str, Enum):
    MODBUS = "modbus"
    MQTT = "mqtt"
    OPCUA = "opcua"
    BACnet = "bacnet"
    COAP = "coap"
    TCP = "tcp"


# Device models
class DeviceBase(BaseModel):
    name: str
    type: DeviceType
    ip: str
    protocols: List[ProtocolType]
    metadata: Optional[dict] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[DeviceStatus] = None
    metadata: Optional[dict] = None


class Device(DeviceBase):
    id: str
    status: DeviceStatus = DeviceStatus.ONLINE
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# Packet models
class PacketBase(BaseModel):
    source: str
    destination: str
    protocol: ProtocolType
    length: int
    info: str
    payload: Optional[str] = None


class Packet(PacketBase):
    id: str = Field(default_factory=lambda: f"packet-{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Protocol configuration models
class ProtocolConfig(BaseModel):
    protocol: ProtocolType
    enabled: bool = True
    port: int
    settings: dict = {}


class ProtocolStatus(BaseModel):
    protocol: ProtocolType
    running: bool
    port: int
    connections: int
    message_rate: float


# Simulation models
class SimulationState(BaseModel):
    running: bool = False
    start_time: Optional[datetime] = None
    packets_per_second: float = 0.0
    active_devices: int = 0


class SimulationControl(BaseModel):
    action: str  # start, stop, reset


# Metric models
class Metric(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Alert models
class AlertType(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: f"alert-{datetime.utcnow().timestamp()}")
    type: AlertType
    title: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    device_id: Optional[str] = None


# WebSocket message models
class WSMessage(BaseModel):
    type: str
    payload: Optional[dict] = None


# API response models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
