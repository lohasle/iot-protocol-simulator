"""
Wireshark-style Packet Capturer
Real-time packet capture and analysis
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import hashlib


class PacketDirection(Enum):
    """Packet Direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    LOCAL = "local"


class PacketProtocol(Enum):
    """Network Protocols"""
    ETHERNET = "ethernet"
    IP = "ip"
    TCP = "tcp"
    UDP = "udp"
    MODBUS = "modbus"
    MQTT = "mqtt"
    OPCUA = "opcua"
    BACNET = "bacnet"
    COAP = "coap"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    UNKNOWN = "unknown"


@dataclass
class CapturedPacket:
    """Captured Packet"""
    id: str
    timestamp: datetime
    direction: PacketDirection
    source: str
    destination: str
    source_port: int
    destination_port: int
    protocol: PacketProtocol
    length: int
    payload: Optional[bytes]
    info: str
    decoded: Optional[dict] = None
    hex_data: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction.value,
            "source": self.source,
            "destination": self.destination,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol.value,
            "length": self.length,
            "info": self.info,
            "decoded": self.decoded
        }


class PacketCapturer:
    """Wireshark-style Packet Capturer"""
    
    def __init__(self, max_packets: int = 10000):
        self.max_packets = max_packets
        self.packets: List[CapturedPacket] = []
        self._running = False
        self._packet_counter = 0
        
        # Filters
        self.filters: Dict[str, Any] = {
            "protocols": [],
            "ports": [],
            "addresses": [],
            "keywords": []
        }
        
        # Statistics
        self._stats = {
            "total_captured": 0,
            "total_bytes": 0,
            "by_protocol": {},
            "by_direction": {"inbound": 0, "outbound": 0, "local": 0}
        }
        
        # Callbacks
        self.on_packet: Optional[Callable] = None
    
    def start(self):
        """Start capturing"""
        self._running = True
        logger.info("Packet capturer started")
    
    def stop(self):
        """Stop capturing"""
        self._running = False
        logger.info("Packet capturer stopped")
    
    def set_filter(self, filter_type: str, value: Any):
        """Set capture filter"""
        if filter_type == "protocol":
            self.filters["protocols"].append(value)
        elif filter_type == "port":
            self.filters["ports"].append(value)
        elif filter_type == "address":
            self.filters["addresses"].append(value)
        elif filter_type == "keyword":
            self.filters["keywords"].append(value)
    
    def clear_filters(self):
        """Clear all filters"""
        self.filters = {
            "protocols": [],
            "ports": [],
            "addresses": [],
            "keywords": []
        }
    
    def capture_packet(
        self,
        direction: PacketDirection,
        source: str,
        destination: str,
        source_port: int = 0,
        destination_port: int = 0,
        protocol: PacketProtocol = PacketProtocol.UNKNOWN,
        payload: Optional[bytes] = None,
        info: str = ""
    ):
        """Capture a packet"""
        if not self._running:
            return
        
        # Apply filters
        if self.filters["protocols"] and protocol.value not in self.filters["protocols"]:
            return
        if self.filters["ports"] and destination_port not in self.filters["ports"]:
            return
        if self.filters["addresses"]:
            if source not in self.filters["addresses"] and destination not in self.filters["addresses"]:
                return
        
        self._packet_counter += 1
        packet = CapturedPacket(
            id=f"pkt-{self._packet_counter:08x}",
            timestamp=datetime.utcnow(),
            direction=direction,
            source=source,
            destination=destination,
            source_port=source_port,
            destination_port=destination_port,
            protocol=protocol,
            length=len(payload) if payload else 0,
            payload=payload,
            info=info,
            hex_data=payload.hex() if payload else None
        )
        
        # Decode packet
        packet.decoded = self._decode_packet(packet)
        
        # Add to capture buffer
        self.packets.append(packet)
        
        # Maintain max size
        if len(self.packets) > self.max_packets:
            self.packets = self.packets[-self.max_packets:]
        
        # Update statistics
        self._stats["total_captured"] += 1
        self._stats["total_bytes"] += packet.length
        self._stats["by_direction"][direction.value] += 1
        
        proto_key = protocol.value
        self._stats["by_protocol"][proto_key] = self._stats["by_protocol"].get(proto_key, 0) + 1
        
        # Callback
        if self.on_packet:
            self.on_packet(packet)
    
    def _decode_packet(self, packet: CapturedPacket) -> Optional[dict]:
        """Decode packet based on protocol"""
        if not packet.payload:
            return None
        
        decoded = {"raw": packet.payload.hex()}
        
        try:
            if packet.protocol == PacketProtocol.MQTT:
                decoded.update(self._decode_mqtt(packet.payload))
            elif packet.protocol == PacketProtocol.MODBUS:
                decoded.update(self._decode_modbus(packet.payload))
            elif packet.protocol == PacketProtocol.COAP:
                decoded.update(self._decode_coap(packet.payload))
            elif packet.protocol == PacketProtocol.OPCUA:
                decoded.update(self._decode_opcua(packet.payload))
            elif packet.protocol == PacketProtocol.BACNET:
                decoded.update(self._decode_bacnet(packet.payload))
            elif packet.protocol in [PacketProtocol.HTTP, PacketProtocol.HTTPS]:
                decoded.update(self._decode_http(packet.payload))
        except Exception as e:
            decoded["error"] = str(e)
        
        return decoded
    
    def _decode_mqtt(self, payload: bytes) -> dict:
        """Decode MQTT packet"""
        if len(payload) < 2:
            return {}
        
        packet_type = payload[0]
        types = {1: "CONNECT", 2: "CONNACK", 3: "PUBLISH", 8: "SUBSCRIBE", 12: "PINGREQ", 14: "DISCONNECT"}
        return {"mqtt_type": types.get(packet_type & 0xF0, "UNKNOWN")}
    
    def _decode_modbus(self, payload: bytes) -> dict:
        """Decode Modbus packet"""
        if len(payload) < 2:
            return {}
        
        func_code = payload[0]
        functions = {
            3: "Read Holding Registers",
            4: "Read Input Registers",
            6: "Write Single Register",
            16: "Write Multiple Registers"
        }
        return {"function_code": functions.get(func_code, f"0x{func_code:02x}")}
    
    def _decode_coap(self, payload: bytes) -> dict:
        """Decode CoAP packet"""
        if len(payload) < 1:
            return {}
        
        code_class = (payload[0] >> 5) & 0x07
        code_detail = payload[0] & 0x1F
        return {"code": f"{code_class}.{code_detail}"}
    
    def _decode_opcua(self, payload: bytes) -> dict:
        """Decode OPC UA packet"""
        # Simplified OPC UA decoding
        return {"length": len(payload)}
    
    def _decode_bacnet(self, payload: bytes) -> dict:
        """Decode BACnet packet"""
        if len(payload) < 2:
            return {}
        
        apdu_type = payload[1]
        services = {8: "Who-Is", 9: "I-Am", 12: "Read Property"}
        return {"service": services.get(apdu_type, f"0x{apdu_type:02x}")}
    
    def _decode_http(self, payload: bytes) -> dict:
        """Decode HTTP packet"""
        try:
            text = payload.decode('utf-8', errors='ignore')
            lines = text.split('\r\n')
            return {
                "method": lines[0].split(' ')[0] if lines else "",
                "path": lines[0].split(' ')[1] if len(lines[0].split(' ')) > 1 else ""
            }
        except:
            return {}
    
    def get_packets(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Get captured packets"""
        packets = self.packets[offset:offset + limit]
        return [p.to_dict() for p in packets]
    
    def get_packet(self, packet_id: str) -> Optional[dict]:
        """Get specific packet"""
        for packet in self.packets:
            if packet.id == packet_id:
                return packet.to_dict()
        return None
    
    def export_packets(self, format: str = "json") -> str:
        """Export captured packets"""
        if format == "json":
            return json.dumps([p.to_dict() for p in self.packets], indent=2)
        elif format == "pcap":
            # Would implement PCAP format
            return json.dumps({"error": "PCAP export not implemented"})
        return json.dumps([p.to_dict() for p in self.packets])
    
    def clear_capture(self):
        """Clear captured packets"""
        self.packets.clear()
        self._packet_counter = 0
        self._stats["total_captured"] = 0
        self._stats["total_bytes"] = 0
        self._stats["by_protocol"] = {}
        self._stats["by_direction"] = {"inbound": 0, "outbound": 0, "local": 0}
    
    def get_stats(self) -> dict:
        """Get capture statistics"""
        return {
            **self._stats,
            "buffer_size": len(self.packets),
            "max_buffer": self.max_packets,
            "filter_active": any(self.filters[k] for k in self.filters)
        }


class PacketFilter:
    """Advanced Packet Filter"""
    
    def __init__(self):
        self.rules: List[dict] = []
    
    def add_rule(self, name: str, condition: dict, action: str = "keep"):
        """Add filter rule"""
        self.rules.append({
            "name": name,
            "condition": condition,
            "action": action  # keep or drop
        })
    
    def match(self, packet: CapturedPacket) -> bool:
        """Check if packet matches any rule"""
        for rule in self.rules:
            if self._match_condition(packet, rule["condition"]):
                return rule["action"] == "keep"
        return True
    
    def _match_condition(self, packet: CapturedPacket, condition: dict) -> bool:
        """Check packet against condition"""
        if "protocol" in condition:
            if packet.protocol.value != condition["protocol"]:
                return False
        
        if "port" in condition:
            if packet.destination_port != condition["port"]:
                return False
        
        if "address" in condition:
            if packet.source != condition["address"] and packet.destination != condition["address"]:
                return False
        
        if "keyword" in condition:
            if condition["keyword"] not in packet.info:
                return False
        
        if "length_min" in condition:
            if packet.length < condition["length_min"]:
                return False
        
        if "length_max" in condition:
            if packet.length > condition["length_max"]:
                return False
        
        return True
    
    def export_rules(self) -> str:
        """Export filter rules"""
        return json.dumps(self.rules, indent=2)


# Factory function
def create_packet_capturer(max_packets: int = 10000) -> PacketCapturer:
    """Create packet capturer"""
    return PacketCapturer(max_packets=max_packets)
