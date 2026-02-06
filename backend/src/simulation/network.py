"""
Network Simulation Module
Topology, latency, and load simulation
"""

import asyncio
import random
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import networkx as nx


class NodeType(Enum):
    """Network Node Types"""
    GATEWAY = "gateway"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    PLC = "plc"
    SERVER = "server"
    CLOUD = "cloud"
    EDGE = "edge"


class LinkType(Enum):
    """Network Link Types"""
    WIRED = "wired"
    WIRELESS = "wireless"
    CELLULAR = "cellular"
    SATELLITE = "satellite"


@dataclass
class NetworkNode:
    """Network Node"""
    id: str
    name: str
    node_type: NodeType
    address: str
    protocols: List[str] = field(default_factory=list)
    properties: Dict = field(default_factory=dict)
    status: str = "online"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "address": self.address,
            "protocols": self.protocols,
            "properties": self.properties,
            "status": self.status
        }


@dataclass
class NetworkLink:
    """Network Link"""
    id: str
    source: str
    target: str
    link_type: LinkType = LinkType.WIRED
    latency_ms: float = 10.0
    jitter_ms: float = 2.0
    packet_loss_percent: float = 0.0
    bandwidth_kbps: float = 1000.0
    status: str = "active"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.link_type.value,
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "packet_loss_percent": self.packet_loss_percent,
            "bandwidth_kbps": self.bandwidth_kbps,
            "status": self.status
        }


class NetworkTopology:
    """Network Topology Simulator"""
    
    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.links: Dict[str, NetworkLink] = {}
        self.graph = nx.Graph()
        self._running = False
        
        # Initialize default topology
        self._init_default_topology()
    
    def _init_default_topology(self):
        """Initialize default network topology"""
        # Create gateway
        self.add_node(NetworkNode(
            id="gateway-1",
            name="Main Gateway",
            node_type=NodeType.GATEWAY,
            address="192.168.1.1",
            protocols=["mqtt", "tcp", "modbus"]
        ))
        
        # Create cloud server
        self.add_node(NetworkNode(
            id="cloud-1",
            name="Cloud Server",
            node_type=NodeType.CLOUD,
            address="cloud.iot-platform.com",
            protocols=["mqtt", "https", "opcua"]
        ))
        
        # Create edge node
        self.add_node(NetworkNode(
            id="edge-1",
            name="Edge Node",
            node_type=NodeType.EDGE,
            address="192.168.1.100",
            protocols=["mqtt", "bacnet"]
        ))
        
        # Create sensors
        for i in range(10):
            self.add_node(NetworkNode(
                id=f"sensor-{i+1}",
                name=f"Temperature Sensor {i+1}",
                node_type=NodeType.SENSOR,
                address=f"192.168.1.{10+i}",
                protocols=["mqtt", "coap"]
            ))
        
        # Create PLCs
        for i in range(3):
            self.add_node(NetworkNode(
                id=f"plc-{i+1}",
                name=f"PLC {i+1}",
                node_type=NodeType.PLC,
                address=f"192.168.2.{10+i}",
                protocols=["modbus", "opcua"]
            ))
        
        # Create links
        self.add_link(NetworkLink(id="link-gw-cloud", source="gateway-1", target="cloud-1", 
                                   latency_ms=50, link_type=LinkType.CELLULAR))
        self.add_link(NetworkLink(id="link-gw-edge", source="gateway-1", target="edge-1",
                                   latency_ms=5))
        self.add_link(NetworkLink(id="link-edge-plc1", source="edge-1", target="plc-1",
                                   latency_ms=2))
        
        # Connect sensors to gateway
        for i in range(10):
            self.add_link(NetworkLink(
                id=f"link-sensor-{i+1}",
                source=f"sensor-{i+1}",
                target="gateway-1",
                latency_ms=random.uniform(1, 10),
                jitter_ms=random.uniform(0.5, 3),
                packet_loss_percent=random.uniform(0, 1),
                link_type=LinkType.WIRELESS if random.random() > 0.5 else LinkType.WIRED
            ))
    
    def add_node(self, node: NetworkNode):
        """Add node to topology"""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.to_dict())
        logger.info(f"Added node: {node.name}")
    
    def remove_node(self, node_id: str):
        """Remove node from topology"""
        if node_id in self.nodes:
            # Remove connected links
            for link_id in list(self.links.keys()):
                if self.links[link_id].source == node_id or self.links[link_id].target == node_id:
                    del self.links[link_id]
            
            del self.nodes[node_id]
            self.graph.remove_node(node_id)
    
    def add_link(self, link: NetworkLink):
        """Add link to topology"""
        self.links[link.id] = link
        self.graph.add_edge(link.source, link.target, **link.to_dict())
    
    def remove_link(self, link_id: str):
        """Remove link from topology"""
        if link_id in self.links:
            link = self.links[link_id]
            self.graph.remove_edge(link.source, link.target)
            del self.links[link_id]
    
    def get_path(self, source: str, target: str) -> List[str]:
        """Get shortest path between nodes"""
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return []
    
    def get_latency(self, source: str, target: str) -> float:
        """Calculate latency between nodes"""
        path = self.get_path(source, target)
        if not path:
            return float('inf')
        
        total_latency = 0
        for i in range(len(path) - 1):
            for link in self.links.values():
                if (link.source == path[i] and link.target == path[i + 1]) or \
                   (link.source == path[i + 1] and link.target == path[i]):
                    total_latency += link.latency_ms
                    break
        
        return total_latency
    
    def update_link_latency(self, link_id: str, latency_ms: float):
        """Update link latency"""
        if link_id in self.links:
            self.links[link_id].latency_ms = latency_ms
    
    def set_link_packet_loss(self, link_id: str, loss_percent: float):
        """Set packet loss on link"""
        if link_id in self.links:
            self.links[link_id].packet_loss_percent = loss_percent
    
    def get_topology_stats(self) -> dict:
        """Get topology statistics"""
        return {
            "nodes": len(self.nodes),
            "links": len(self.links),
            "gateways": sum(1 for n in self.nodes.values() if n.node_type == NodeType.GATEWAY),
            "sensors": sum(1 for n in self.nodes.values() if n.node_type == NodeType.SENSOR),
            "plcs": sum(1 for n in self.nodes.values() if n.node_type == NodeType.PLC),
            "edge_nodes": sum(1 for n in self.nodes.values() if n.node_type == NodeType.EDGE),
            "cloud_nodes": sum(1 for n in self.nodes.values() if n.node_type == NodeType.CLOUD),
            "connected": nx.is_connected(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values()) / len(self.graph.nodes()) if self.graph.nodes() else 0
        }
    
    def export_topology(self) -> dict:
        """Export topology as dictionary"""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "links": [l.to_dict() for l in self.links.values()]
        }


class LatencySimulator:
    """Latency and Packet Loss Simulator"""
    
    def __init__(self, base_latency: float = 10.0, base_jitter: float = 2.0):
        self.base_latency = base_latency
        self.base_jitter = base_jitter
        self._running = False
        
        # Dynamic latency profiles
        self.profiles = {
            "normal": {"latency": 10.0, "jitter": 2.0, "loss": 0.0},
            "congested": {"latency": 100.0, "jitter": 20.0, "loss": 2.0},
            "poor": {"latency": 500.0, "jitter": 100.0, "loss": 5.0},
            "excellent": {"latency": 2.0, "jitter": 0.5, "loss": 0.0}
        }
        
        self._current_profile = "normal"
    
    def set_profile(self, profile: str):
        """Set latency profile"""
        if profile in self.profiles:
            self._current_profile = profile
    
    def get_latency(self) -> float:
        """Get simulated latency with jitter"""
        profile = self.profiles[self._current_profile]
        latency = profile["latency"] + random.gauss(0, profile["jitter"])
        return max(0, latency)
    
    def should_drop_packet(self) -> bool:
        """Determine if packet should be dropped"""
        profile = self.profiles[self._current_profile]
        return random.random() < (profile["loss"] / 100)


class LoadGenerator:
    """High-scale IoT Device Load Generator"""
    
    def __init__(self, max_devices: int = 1000):
        self.max_devices = max_devices
        self.devices: Dict[str, dict] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Device templates
        self.templates = {
            "sensor": {
                "protocols": ["mqtt", "coap"],
                "data_rate": 1.0,  # messages per second
                "data_size": 100
            },
            "actuator": {
                "protocols": ["mqtt", "tcp"],
                "data_rate": 0.1,
                "data_size": 50
            },
            "plc": {
                "protocols": ["modbus", "opcua"],
                "data_rate": 10.0,
                "data_size": 500
            },
            "gateway": {
                "protocols": ["mqtt", "tcp", "bacnet"],
                "data_rate": 100.0,
                "data_size": 1000
            }
        }
    
    def create_devices(self, count: int, device_type: str = "sensor"):
        """Create simulated devices"""
        template = self.templates.get(device_type, self.templates["sensor"])
        
        for i in range(min(count, self.max_devices - len(self.devices))):
            device_id = f"device-{device_type[:3]}-{i+1:04d}"
            self.devices[device_id] = {
                "id": device_id,
                "type": device_type,
                "address": f"192.168.{i // 256}.{i % 256}",
                "protocols": template["protocols"],
                "data_rate": template["data_rate"],
                "data_size": template["data_size"],
                "messages_sent": 0,
                "messages_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0,
                "status": "online"
            }
        
        logger.info(f"Created {count} {device_type} devices (total: {len(self.devices)})")
    
    def start(self, interval: float = 0.1):
        """Start load generation"""
        self._running = True
        self._task = asyncio.create_task(self._generate_load(interval))
    
    def stop(self):
        """Stop load generation"""
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def _generate_load(self, interval: float):
        """Generate simulated traffic"""
        while self._running:
            try:
                # Random device traffic
                device_count = min(len(self.devices), 100)  # Sample 100 devices per interval
                sample_devices = random.sample(list(self.devices.keys()), device_count)
                
                for device_id in sample_devices:
                    device = self.devices[device_id]
                    
                    # Simulate message based on data rate
                    if random.random() < device["data_rate"] * interval:
                        message_size = random.randint(
                            device["data_size"] // 2, 
                            device["data_size"] * 2
                        )
                        
                        device["messages_sent"] += 1
                        device["bytes_sent"] += message_size
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
    
    def get_stats(self) -> dict:
        """Get load statistics"""
        total_sent = sum(d["messages_sent"] for d in self.devices.values())
        total_bytes = sum(d["bytes_sent"] for d in self.devices.values())
        
        return {
            "total_devices": len(self.devices),
            "online_devices": sum(1 for d in self.devices.values() if d["status"] == "online"),
            "total_messages_sent": total_sent,
            "total_bytes_sent": total_bytes,
            "avg_messages_per_device": total_sent / len(self.devices) if self.devices else 0,
            "by_type": {
                dtype: {
                    "count": sum(1 for d in self.devices.values() if d["type"] == dtype),
                    "messages": sum(d["messages_sent"] for d in self.devices.values() if d["type"] == dtype)
                }
                for dtype in self.templates.keys()
            }
        }
    
    def get_device(self, device_id: str) -> Optional[dict]:
        """Get device info"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[dict]:
        """Get all devices"""
        return list(self.devices.values())


# Factory functions
def create_network_topology() -> NetworkTopology:
    """Create network topology"""
    return NetworkTopology()


def create_latency_simulator(base_latency: float = 10.0) -> LatencySimulator:
    """Create latency simulator"""
    return LatencySimulator(base_latency=base_latency)


def create_load_generator(max_devices: int = 1000) -> LoadGenerator:
    """Create load generator"""
    return LoadGenerator(max_devices=max_devices)
