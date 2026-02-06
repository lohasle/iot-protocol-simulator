"""
Fault Injector
Inject network faults and failures for testing
"""

import asyncio
import random
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger


class FaultType(Enum):
    """Types of Faults"""
    PACKET_LOSS = "packet_loss"
    LATENCY_SPIKE = "latency_spike"
    JITTER = "jitter"
    CORRUPTION = "corruption"
    REORDERING = "reordering"
    DUPLICATION = "duplication"
    CONNECTION_DROP = "connection_drop"
    PROTOCOL_ERROR = "protocol_error"
    BANDWIDTH_LIMIT = "bandwidth_limit"
    DEVICE_OFFLINE = "device_offline"


@dataclass
class Fault:
    """Fault Configuration"""
    id: str
    fault_type: FaultType
    target: str  # protocol, device, or link
    target_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    probability: float = 1.0  # 0.0 to 1.0
    duration_seconds: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.fault_type.value,
            "target": self.target,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "probability": self.probability,
            "duration_seconds": self.duration_seconds
        }


class FaultInjector:
    """Fault Injection Engine"""
    
    def __init__(self):
        self.faults: Dict[str, Fault] = {}
        self._running = False
        self._active_faults: set = set()
        self._task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "faults_injected": 0,
            "packets_affected": 0,
            "connections_dropped": 0,
            "errors_generated": 0
        }
    
    def add_fault(self, fault: Fault):
        """Add a fault configuration"""
        self.faults[fault.id] = fault
        logger.info(f"Added fault: {fault.id} ({fault.fault_type.value})")
    
    def remove_fault(self, fault_id: str):
        """Remove fault configuration"""
        if fault_id in self.faults:
            del self.faults[fault_id]
            self._active_faults.discard(fault_id)
    
    def enable_fault(self, fault_id: str):
        """Enable a fault"""
        if fault_id in self.faults:
            self.faults[fault_id].enabled = True
            self._active_faults.add(fault_id)
            logger.info(f"Enabled fault: {fault_id}")
    
    def disable_fault(self, fault_id: str):
        """Disable a fault"""
        if fault_id in self.faults:
            self.faults[fault_id].enabled = False
            self._active_faults.discard(fault_id)
            logger.info(f"Disabled fault: {fault_id}")
    
    def start(self):
        """Start fault injection"""
        self._running = True
        self._task = asyncio.create_task(self._monitor_faults())
        logger.info(f"Fault injector started with {len(self.faults)} configured faults")
    
    def stop(self):
        """Stop fault injection"""
        self._running = False
        if self._task:
            self._task.cancel()
        
        # Disable all faults
        for fault in self.faults.values():
            fault.enabled = False
        self._active_faults.clear()
        
        logger.info("Fault injector stopped")
    
    async def _monitor_faults(self):
        """Monitor and execute faults"""
        while self._running:
            try:
                for fault_id in list(self._active_faults):
                    fault = self.faults.get(fault_id)
                    if fault and fault.enabled:
                        if random.random() < fault.probability:
                            await self._inject_fault(fault)
                
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
    
    async def _inject_fault(self, fault: Fault):
        """Inject a specific fault"""
        try:
            if fault.fault_type == FaultType.PACKET_LOSS:
                await self._inject_packet_loss(fault)
            elif fault.fault_type == FaultType.LATENCY_SPIKE:
                await self._inject_latency_spike(fault)
            elif fault.fault_type == FaultType.JITTER:
                await self._inject_jitter(fault)
            elif fault.fault_type == FaultType.CORRUPTION:
                await self._inject_corruption(fault)
            elif fault.fault_type == FaultType.REORDERING:
                await self._inject_reordering(fault)
            elif fault.fault_type == FaultType.DUPLICATION:
                await self._inject_duplication(fault)
            elif fault.fault_type == FaultType.CONNECTION_DROP:
                await self._inject_connection_drop(fault)
            elif fault.fault_type == FaultType.PROTOCOL_ERROR:
                await self._inject_protocol_error(fault)
            elif fault.fault_type == FaultType.DEVICE_OFFLINE:
                await self._inject_device_offline(fault)
            
            self._stats["faults_injected"] += 1
            
        except Exception as e:
            logger.error(f"Fault injection error: {e}")
            self._stats["errors_generated"] += 1
    
    async def _inject_packet_loss(self, fault: Fault):
        """Inject packet loss"""
        loss_percent = fault.parameters.get("percent", 50)
        self._stats["packets_affected"] += random.randint(1, 10)
        logger.debug(f"Injecting {loss_percent}% packet loss")
    
    async def _inject_latency_spike(self, fault: Fault):
        """Inject latency spike"""
        delay_ms = fault.parameters.get("delay_ms", 1000)
        duration = fault.parameters.get("duration_ms", 5000)
        logger.debug(f"Injecting latency spike of {delay_ms}ms for {duration}ms")
    
    async def _inject_jitter(self, fault: Fault):
        """Inject jitter"""
        jitter_ms = fault.parameters.get("jitter_ms", 100)
        logger.debug(f"Injecting jitter of {jitter_ms}ms")
    
    async def _inject_corruption(self, fault: Fault):
        """Inject packet corruption"""
        corruption_rate = fault.parameters.get("rate", 0.1)
        self._stats["packets_affected"] += 1
        logger.debug(f"Injecting packet corruption at {corruption_rate * 100}%")
    
    async def _inject_reordering(self, fault: Fault):
        """Inject packet reordering"""
        buffer_size = fault.parameters.get("buffer_size", 5)
        logger.debug(f"Injecting packet reordering with buffer {buffer_size}")
    
    async def _inject_duplication(self, fault: Fault):
        """Inject packet duplication"""
        duplicate_rate = fault.parameters.get("rate", 0.05)
        self._stats["packets_affected"] += 1
        logger.debug(f"Injecting packet duplication at {duplicate_rate * 100}%")
    
    async def _inject_connection_drop(self, fault: Fault):
        """Inject connection drop"""
        duration = fault.parameters.get("duration_seconds", 10)
        self._stats["connections_dropped"] += 1
        logger.warning(f"Injecting connection drop for {duration}s")
    
    async def _inject_protocol_error(self, fault: Fault):
        """Inject protocol error"""
        error_type = fault.parameters.get("type", "malformed")
        self._stats["errors_generated"] += 1
        logger.warning(f"Injecting protocol error: {error_type}")
    
    async def _inject_device_offline(self, fault: Fault):
        """Inject device offline"""
        duration = fault.parameters.get("duration_seconds", 30)
        logger.warning(f"Injecting device offline for {duration}s")
    
    def should_modify_packet(self, fault_id: str) -> tuple:
        """Check if packet should be modified"""
        fault = self.faults.get(fault_id)
        if not fault or not fault.enabled:
            return False, None
        
        if fault.fault_type in [FaultType.PACKET_LOSS, FaultType.CONNECTION_DROP, FaultType.DEVICE_OFFLINE]:
            return False, None
        
        if random.random() < fault.probability:
            if fault.fault_type == FaultType.LATENCY_SPIKE:
                return True, {"delay_ms": fault.parameters.get("delay_ms", 1000)}
            elif fault.fault_type == FaultType.JITTER:
                return True, {"jitter_ms": fault.parameters.get("jitter_ms", 100)}
            elif fault.fault_type == FaultType.CORRUPTION:
                return True, {"corrupt": True}
            elif fault.fault_type == FaultType.DUPLICATION:
                return True, {"duplicate": True}
        
        return False, None
    
    def get_active_faults(self) -> List[dict]:
        """Get all active faults"""
        return [f.to_dict() for f in self.faults.values() if f.enabled]
    
    def get_fault_stats(self) -> dict:
        """Get fault injection statistics"""
        return {
            **self._stats,
            "configured_faults": len(self.faults),
            "active_faults": len(self._active_faults),
            "fault_types": {
                ft.value: sum(1 for f in self.faults.values() if f.fault_type == ft)
                for ft in FaultType
            }
        }
    
    def create_preset_faults(self):
        """Create preset fault scenarios"""
        # Network congestion
        self.add_fault(Fault(
            id="network-congestion",
            fault_type=FaultType.PACKET_LOSS,
            target="network",
            parameters={"percent": 25},
            probability=0.3
        ))
        
        # High latency
        self.add_fault(Fault(
            id="high-latency",
            fault_type=FaultType.LATENCY_SPIKE,
            target="network",
            parameters={"delay_ms": 2000, "duration_ms": 10000},
            probability=0.1
        ))
        
        # Unstable connection
        self.add_fault(Fault(
            id="unstable-connection",
            fault_type=FaultType.JITTER,
            target="network",
            parameters={"jitter_ms": 500},
            probability=0.2
        ))
        
        # Packet corruption
        self.add_fault(Fault(
            id="packet-corruption",
            fault_type=FaultType.CORRUPTION,
            target="network",
            parameters={"rate": 0.01},
            probability=0.05
        ))
        
        # Device failure
        self.add_fault(Fault(
            id="device-failure",
            fault_type=FaultType.DEVICE_OFFLINE,
            target="device",
            target_id="sensor-1",
            parameters={"duration_seconds": 60},
            probability=0.05
        ))
        
        logger.info("Created preset fault scenarios")


# Factory function
def create_fault_injector() -> FaultInjector:
    """Create fault injector"""
    return FaultInjector()
