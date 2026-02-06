"""
Simulation engine for generating IoT traffic
"""

import asyncio
import random
import json
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
from src.models.schemas import Packet, Metric, Alert, ProtocolType, AlertType
from src.services.websocket_manager import ws_manager


class SimulationEngine:
    """Engine for simulating IoT traffic and devices"""
    
    def __init__(self):
        self.is_running = False
        self._tasks: List[asyncio.Task] = []
        self._devices: Dict[str, dict] = {}
        self._packets: List[Packet] = []
        self._metrics: Dict[str, float] = {
            "active_devices": 24,
            "msg_rate": 1200,
            "throughput": 256.5,
            "load": 34,
        }
    
    def start(self):
        """Start the simulation engine"""
        if self.is_running:
            logger.warning("Simulation engine already running")
            return
        
        self.is_running = True
        logger.info("Simulation engine started")
        
        # Create background tasks
        self._tasks = [
            asyncio.create_task(self._generate_packets_loop()),
            asyncio.create_task(self._update_metrics_loop()),
            asyncio.create_task(self._generate_alerts_loop()),
            asyncio.create_task(self._device_heartbeat_loop()),
        ]
        
        # Initialize sample devices
        self._initialize_sample_devices()
    
    def stop(self):
        """Stop the simulation engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        self._tasks.clear()
        logger.info("Simulation engine stopped")
    
    def _initialize_sample_devices(self):
        """Initialize sample IoT devices"""
        device_types = [
            ("PLC-001", "plc", ["modbus", "bacnet"]),
            ("Sensor-001", "sensor", ["mqtt", "coap"]),
            ("Actuator-001", "actuator", ["modbus", "opcua"]),
            ("Gateway-001", "gateway", ["mqtt", "tcp"]),
            ("Server-001", "server", ["opcua"]),
        ]
        
        for i, (name, dtype, protocols) in enumerate(device_types):
            device_id = f"device-{i+1}"
            self._devices[device_id] = {
                "id": device_id,
                "name": name,
                "type": dtype,
                "ip": f"192.168.1.{10+i}",
                "protocols": protocols,
                "status": "online",
            }
    
    async def _generate_packets_loop(self):
        """Generate random IoT packets"""
        while self.is_running:
            try:
                if random.random() > 0.3:
                    packet = self._generate_random_packet()
                    self._packets.append(packet)
                    
                    # Keep only last 1000 packets
                    if len(self._packets) > 1000:
                        self._packets = self._packets[-999:]
                    
                    # Broadcast to subscribers
                    message = json.dumps({
                        "type": "packet",
                        "payload": packet.dict(),
                    })
                    await ws_manager.broadcast(message, "packets")
                
                await asyncio.sleep(1.0 / max(self._metrics["msg_rate"] / 60, 1))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Packet generation error: {e}")
    
    def _generate_random_packet(self) -> Packet:
        """Generate a random IoT packet"""
        protocols = list(ProtocolType)
        sources = [f"192.168.1.{random.randint(10, 99)}" for _ in range(5)]
        destinations = ["192.168.1.100", "cloud.iot.com", "192.168.2.1"]
        
        protocol = random.choice(protocols)
        
        packet_info = {
            ProtocolType.MODBUS: [
                "Read Holding Registers (FC03)",
                "Write Single Register (FC06)",
                "Read Input Registers (FC04)",
            ],
            ProtocolType.MQTT: [
                "PUBLISH /sensors/temp",
                "CONNECT Protocol",
                "PINGREQ",
            ],
            ProtocolType.OPCUA: [
                "Publish Request",
                "Data Change Notification",
                "Browse Request",
            ],
            ProtocolType.BACnet: [
                "Who-Is Request",
                "I-Am Response",
                "Read Property",
            ],
            ProtocolType.COAP: [
                "GET /status",
                "POST /control",
                "PUT /config",
            ],
        }
        
        return Packet(
            source=random.choice(sources),
            destination=random.choice(destinations),
            protocol=protocol,
            length=random.randint(50, 500),
            info=random.choice(packet_info.get(protocol, ["Unknown"])),
        )
    
    async def _update_metrics_loop(self):
        """Update simulation metrics"""
        while self.is_running:
            try:
                # Update metrics with random variation
                self._metrics["active_devices"] = max(0, self._metrics["active_devices"] + random.randint(-1, 1))
                self._metrics["msg_rate"] = max(100, self._metrics["msg_rate"] + random.randint(-100, 100))
                self._metrics["throughput"] = max(0, self._metrics["throughput"] + random.uniform(-20, 20))
                self._metrics["load"] = max(5, min(95, self._metrics["load"] + random.randint(-5, 5)))
                
                # Create metric updates
                for name, value in self._metrics.items():
                    metric = Metric(
                        name=name,
                        value=value,
                        unit="msg/s" if name == "msg_rate" else ("%" if name == "load" else "KB/s"),
                    )
                    message = json.dumps({
                        "type": "metric",
                        "metric": name,
                        "value": value,
                    })
                    await ws_manager.broadcast(message, "metrics")
                
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
    
    async def _generate_alerts_loop(self):
        """Generate random alerts"""
        alert_titles = [
            ("温度过高", AlertType.WARNING),
            ("连接不稳定", AlertType.WARNING),
            ("设备上线", AlertType.SUCCESS),
            ("内存使用率高", AlertType.CRITICAL),
            ("网络延迟增加", AlertType.INFO),
        ]
        
        alert_descs = [
            "设备温度超过安全阈值",
            "检测到异常丢包率",
            "设备已重新连接网络",
            "CPU 使用率超过 80%",
            "响应时间增加 50ms",
        ]
        
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Generate alert every 30 seconds
                
                if random.random() > 0.7:
                    title, alert_type = random.choice(alert_titles)
                    description = random.choice(alert_descs)
                    
                    alert = Alert(
                        type=alert_type,
                        title=title,
                        description=description,
                    )
                    
                    message = json.dumps({
                        "type": "alert",
                        "payload": alert.dict(),
                    })
                    await ws_manager.broadcast(message, "alerts")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert generation error: {e}")
    
    async def _device_heartbeat_loop(self):
        """Update device status periodically"""
        while self.is_running:
            try:
                for device_id in list(self._devices.keys()):
                    if random.random() > 0.95:
                        device = self._devices[device_id]
                        device["status"] = "offline" if device["status"] == "online" else "online"
                        
                        message = json.dumps({
                            "type": "device_status",
                            "device": device,
                        })
                        await ws_manager.broadcast(message, "devices")
                
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Device heartbeat error: {e}")
    
    def get_devices(self) -> List[dict]:
        """Get all devices"""
        return list(self._devices.values())
    
    def get_packets(self, limit: int = 100) -> List[Packet]:
        """Get recent packets"""
        return self._packets[-limit:]
    
    def get_metrics(self) -> Dict[str, float]:
        """Get current metrics"""
        return self._metrics.copy()
    
    def clear_packets(self):
        """Clear packet history"""
        self._packets.clear()


# Global simulation engine instance
simulation_engine = SimulationEngine()
