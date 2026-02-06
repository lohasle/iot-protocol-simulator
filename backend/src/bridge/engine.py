"""
IoT Protocol Bridge Engine
Unified bridging between different IoT protocols
"""

import asyncio
import json
import yaml
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import hashlib


class BridgeDirection(Enum):
    """Bridge Direction"""
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"
    BIDIRECTIONAL = "bidirectional"


class DataType(Enum):
    """Data Types"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"
    BINARY = "binary"


@dataclass
class BridgeMapping:
    """Mapping configuration"""
    source_protocol: str
    source_topic: str
    target_protocol: str
    target_topic: str
    direction: BridgeDirection = BridgeDirection.SOURCE_TO_TARGET
    transform: Optional[Dict] = None
    
    def to_dict(self) -> dict:
        return {
            "source_protocol": self.source_protocol,
            "source_topic": self.source_topic,
            "target_protocol": self.target_protocol,
            "target_topic": self.target_topic,
            "direction": self.direction.value,
            "transform": self.transform
        }


@dataclass
class BridgeRule:
    """Bridge Rule"""
    name: str
    mappings: List[BridgeMapping]
    enabled: bool = True
    priority: int = 0
    conditions: List[Dict] = field(default_factory=list)
    actions: List[Dict] = field(default_factory=list)


class BridgeEngine:
    """Unified Bridge Engine"""
    
    def __init__(self):
        self.bridges: Dict[str, BridgeRule] = {}
        self.protocol_adapters: Dict[str, Any] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._tasks: List[asyncio.Task] = []
        
        # Statistics
        self._stats = {
            "messages_forwarded": 0,
            "messages_transformed": 0,
            "errors": 0,
            "active_bridges": 0
        }
        
        # Callbacks
        self.on_message: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def register_adapter(self, protocol: str, adapter: Any):
        """Register protocol adapter"""
        self.protocol_adapters[protocol] = adapter
        logger.info(f"Registered adapter for protocol: {protocol}")
    
    def add_bridge(self, rule: BridgeRule):
        """Add a bridge rule"""
        self.bridges[rule.name] = rule
        self._stats["active_bridges"] = len(self.bridges)
        logger.info(f"Added bridge rule: {rule.name} with {len(rule.mappings)} mappings")
    
    def remove_bridge(self, name: str):
        """Remove a bridge rule"""
        if name in self.bridges:
            del self.bridges[name]
            self._stats["active_bridges"] = len(self.bridges)
    
    def load_mappings(self, file_path: str, format: str = "yaml"):
        """Load mappings from file"""
        with open(file_path, 'r') as f:
            if format == "yaml":
                data = yaml.safe_load(f)
            elif format == "json":
                data = json.load(f)
            else:
                raise ValueError(f"Unknown format: {format}")
        
        for item in data.get("mappings", []):
            rule = BridgeRule(
                name=item.get("name", f"bridge-{len(self.bridges)}"),
                mappings=[
                    BridgeMapping(
                        source_protocol=m["source_protocol"],
                        source_topic=m["source_topic"],
                        target_protocol=m["target_protocol"],
                        target_topic=m["target_topic"],
                        direction=BridgeDirection(m.get("direction", "source_to_target")),
                        transform=m.get("transform")
                    )
                    for m in item.get("mappings", [])
                ],
                enabled=item.get("enabled", True),
                priority=item.get("priority", 0)
            )
            self.add_bridge(rule)
    
    def save_mappings(self, file_path: str, format: str = "yaml"):
        """Save mappings to file"""
        data = {
            "bridges": [
                {
                    "name": name,
                    "mappings": [m.to_dict() for m in rule.mappings],
                    "enabled": rule.enabled,
                    "priority": rule.priority
                }
                for name, rule in self.bridges.items()
            ]
        }
        
        with open(file_path, 'w') as f:
            if format == "yaml":
                yaml.dump(data, f)
            elif format == "json":
                json.dump(data, f, indent=2)
    
    async def start(self):
        """Start the bridge engine"""
        self.running = True
        
        # Start message processing
        self._tasks.append(asyncio.create_task(self._process_messages()))
        
        logger.info(f"Bridge engine started with {len(self.bridges)} active bridges")
    
    def stop(self):
        """Stop the bridge engine"""
        self.running = False
        
        for task in self._tasks:
            task.cancel()
        
        self._tasks.clear()
        logger.info("Bridge engine stopped")
    
    async def _process_messages(self):
        """Process messages from queue"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                await self._route_message(message)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                self._stats["errors"] += 1
    
    async def _route_message(self, message: dict):
        """Route message through bridges"""
        protocol = message.get("protocol")
        topic = message.get("topic")
        data = message.get("data")
        
        if not protocol or not topic:
            return
        
        for bridge_name, bridge in self.bridges.items():
            if not bridge.enabled:
                continue
            
            for mapping in bridge.mappings:
                if self._matches_mapping(protocol, topic, mapping):
                    # Check conditions
                    if bridge.conditions and not self._check_conditions(bridge.conditions, data):
                        continue
                    
                    # Transform data
                    transformed = self._transform_data(data, mapping.transform) if mapping.transform else data
                    
                    # Forward to target
                    await self._forward_message(mapping, transformed)
                    
                    self._stats["messages_forwarded"] += 1
                    if mapping.transform:
                        self._stats["messages_transformed"] += 1
    
    def _matches_mapping(self, protocol: str, topic: str, mapping: BridgeMapping) -> bool:
        """Check if message matches mapping"""
        # Check direction
        if mapping.direction == BridgeDirection.TARGET_TO_SOURCE:
            if protocol != mapping.target_protocol or topic != mapping.target_topic:
                return False
        elif mapping.direction == BridgeDirection.SOURCE_TO_TARGET:
            if protocol != mapping.source_protocol or topic != mapping.source_topic:
                return False
        else:  # BIDIRECTIONAL
            if not (
                (protocol == mapping.source_protocol and topic == mapping.source_topic) or
                (protocol == mapping.target_protocol and topic == mapping.target_topic)
            ):
                return False
        
        # Check topic with wildcards
        source_topic = mapping.source_protocol == protocol and mapping.source_topic
        target_topic = mapping.target_protocol == protocol and mapping.target_topic
        check_topic = source_topic or target_topic
        
        if check_topic:
            if not self._topic_matches(topic, check_topic):
                return False
        
        return True
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern with wildcards"""
        if pattern == "#" or pattern == "+":
            return True
        
        # Split by /
        topic_parts = topic.split('/')
        pattern_parts = pattern.split('/')
        
        for i, (t, p) in enumerate(zip(topic_parts, pattern_parts)):
            if p == '#':
                return True
            if p == '+':
                continue
            if t != p:
                return False
        
        return len(topic_parts) == len(pattern_parts)
    
    def _check_conditions(self, conditions: List[Dict], data: Any) -> bool:
        """Check if data meets conditions"""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator", "eq")
            value = condition.get("value")
            
            # Get data value (handle nested fields)
            data_value = data
            for part in field.split('.'):
                if isinstance(data_value, dict):
                    data_value = data_value.get(part)
                else:
                    data_value = None
                    break
            
            # Compare
            if operator == "eq" and data_value != value:
                return False
            elif operator == "ne" and data_value == value:
                return False
            elif operator == "gt" and not (data_value > value):
                return False
            elif operator == "lt" and not (data_value < value):
                return False
            elif operator == "gte" and not (data_value >= value):
                return False
            elif operator == "lte" and not (data_value <= value):
                return False
            elif operator == "in" and data_value not in value:
                return False
            elif operator == "contains" and not (value in str(data_value)):
                return False
        
        return True
    
    def _transform_data(self, data: Any, transform: Optional[Dict]) -> Any:
        """Transform data according to rules"""
        if not transform:
            return data
        
        result = data
        
        # Apply field mappings
        for mapping in transform.get("field_mappings", []):
            source_field = mapping.get("source")
            target_field = mapping.get("target")
            data_type = mapping.get("type")
            
            # Get source value
            value = result
            for part in source_field.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
            
            # Convert type
            if data_type:
                if data_type == DataType.INTEGER.value:
                    value = int(value)
                elif data_type == DataType.FLOAT.value:
                    value = float(value)
                elif data_type == DataType.BOOLEAN.value:
                    value = bool(value)
            
            # Set target value
            if isinstance(result, dict):
                result[target_field] = value
        
        # Apply formulas
        for formula in transform.get("formulas", []):
            field = formula.get("field")
            expression = formula.get("expression")
            
            # Simple expression evaluation (CAUTION: security risk in production!)
            try:
                value = eval(expression, {"__builtins__": {}}, {"data": result})
                if field and isinstance(result, dict):
                    result[field] = value
            except:
                pass
        
        # Apply filters
        for filter_rule in transform.get("filters", []):
            field = filter_rule.get("field")
            action = filter_rule.get("action", "include")
            
            if isinstance(result, dict):
                if action == "exclude" and field in result:
                    del result[field]
                elif action == "keep" and field not in result:
                    result[field] = None
        
        return result
    
    async def _forward_message(self, mapping: BridgeMapping, data: Any):
        """Forward message to target protocol"""
        # Get target adapter
        target_adapter = self.protocol_adapters.get(mapping.target_protocol)
        
        if not target_adapter:
            logger.warning(f"No adapter for protocol: {mapping.target_protocol}")
            return
        
        # Send message
        if hasattr(target_adapter, 'publish'):
            if isinstance(data, dict):
                await target_adapter.publish(mapping.target_topic, data)
            else:
                await target_adapter.publish(mapping.target_topic, {"value": data})
        elif hasattr(target_adapter, 'send'):
            target_adapter.send(mapping.target_topic, data)
        
        if self.on_message:
            self.on_message({
                "from": mapping.source_protocol,
                "to": mapping.target_protocol,
                "topic": mapping.target_topic,
                "data": data
            })
    
    def publish(self, protocol: str, topic: str, data: Any):
        """Publish message to bridge"""
        asyncio.create_task(self.message_queue.put({
            "protocol": protocol,
            "topic": topic,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def get_stats(self) -> dict:
        """Get bridge statistics"""
        return {
            **self._stats,
            "active_bridges": len(self.bridges),
            "queue_size": self.message_queue.qsize()
        }
    
    def get_bridges(self) -> List[dict]:
        """Get all bridges"""
        return [
            {
                "name": name,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "mappings": len(rule.mappings),
                "conditions": len(rule.conditions)
            }
            for name, rule in self.bridges.items()
        ]


# Example mapping configuration
EXAMPLE_MAPPINGS = """
bridges:
  - name: modbus-to-mqtt
    enabled: true
    priority: 1
    mappings:
      - source_protocol: modbus
        source_topic: "holding-registers"
        target_protocol: mqtt
        target_topic: "sensors/modbus"
        direction: source_to_target
        transform:
          field_mappings:
            - source: "value"
              target: "sensor_value"
              type: float
            - source: "address"
              target: "register_address"
              type: integer
          formulas:
            - field: "kwh"
              expression: "data['value'] * 0.001"
  - name: opcua-to-mqtt
    enabled: true
    mappings:
      - source_protocol: opcua
        source_topic: "ns=2:s=Device.Temperature"
        target_protocol: mqtt
        target_topic: "sensors/temperature"
        direction: source_to_target
        transform:
          field_mappings:
            - source: "value"
              target: "temperature"
              type: float
  - name: bacnet-to-modbus
    enabled: true
    mappings:
      - source_protocol: bacnet
        source_topic: "analog-input"
        target_protocol: modbus
        target_topic: "input-registers"
        direction: source_to_target
"""

# Factory function
def create_bridge_engine() -> BridgeEngine:
    """Create a new bridge engine"""
    return BridgeEngine()
