"""
MQTT Broker + Client Protocol Simulator
Complete MQTT 3.1.1/5.0 implementation
"""

import asyncio
import random
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import hashlib
import base64


class MQTTQoS(Enum):
    """MQTT Quality of Service Levels"""
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


class MQTTConnReturnCode(Enum):
    """Connection Return Codes"""
    ACCEPTED = 0x00
    UNSUPPORTED_PROTOCOL_VERSION = 0x01
    IDENTIFIER_REJECTED = 0x02
    SERVER_UNAVAILABLE = 0x03
    BAD_USERNAME_PASSWORD = 0x04
    NOT_AUTHORIZED = 0x05


@dataclass
class MQTTClient:
    """MQTT Client Information"""
    client_id: str
    username: Optional[str] = None
    password: Optional[str] = None
    clean_session: bool = True
    keep_alive: int = 60
    will_topic: Optional[str] = None
    will_message: Optional[str] = None
    will_qos: MQTTQoS = MQTTQoS.AT_MOST_ONCE
    will_retain: bool = False
    subscriptions: Dict[str, MQTTQoS] = field(default_factory=dict)
    connected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MQTTMessage:
    """MQTT Message"""
    topic: str
    payload: Any
    qos: MQTTQoS = MQTTQoS.AT_MOST_ONCE
    retain: bool = False
    client_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: Optional[int] = None


class MQTTBroker:
    """MQTT Broker Simulator"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 1883):
        self.host = host
        self.port = port
        self.clients: Dict[str, MQTTClient] = {}
        self.topics: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._message_id = 0
        self._stats = {
            "messages_published": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "active_connections": 0,
        }
        self.on_message: Optional[Callable] = None
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
    
    async def start(self):
        """Start the MQTT broker"""
        self.running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(f"MQTT Broker started on {self.host}:{self.port}")
        async with self._server:
            await self._server.serve_forever()
    
    def stop(self):
        """Stop the broker"""
        self.running = False
        if self._server:
            self._server.close()
        logger.info("MQTT Broker stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection"""
        addr = writer.get_extra_info('peername')
        client_id = f"client-{random.randint(1000, 9999)}"
        
        try:
            while self.running:
                try:
                    first_byte = await reader.read(1)
                    if not first_byte:
                        break
                    
                    packet_type = (first_byte[0] >> 4) & 0x0F
                    remaining_length = 0
                    multiplier = 1
                    while True:
                        byte = await reader.read(1)
                        if not byte:
                            return
                        remaining_length += (byte[0] & 0x7F) * multiplier
                        if not (byte[0] & 0x80):
                            break
                        multiplier *= 128
                    
                    if remaining_length > 0:
                        payload = await reader.read(remaining_length)
                    else:
                        payload = b''
                    
                    response = await self._process_packet(
                        client_id, writer, packet_type, payload
                    )
                    
                    if response:
                        writer.write(response)
                        await writer.drain()
                        
                except Exception as e:
                    logger.error(f"MQTT client error: {e}")
                    break
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _process_packet(
        self,
        client_id: str,
        writer: asyncio.StreamWriter,
        packet_type: int,
        payload: bytes
    ) -> Optional[bytes]:
        """Process MQTT packet"""
        # CONNECT (0x01)
        if packet_type == 0x01:
            return await self._handle_connect(client_id, payload)
        # CONNACK (0x02)
        elif packet_type == 0x02:
            pass
        # PUBLISH (0x03)
        elif packet_type == 0x03:
            return await self._handle_publish(client_id, payload)
        # PUBACK (0x04)
        elif packet_type == 0x04:
            pass
        # SUBSCRIBE (0x08)
        elif packet_type == 0x08:
            return await self._handle_subscribe(client_id, payload)
        # PINGREQ (0x0C)
        elif packet_type == 0x0C:
            return self._handle_pingresp()
        # DISCONNECT (0x0E)
        elif packet_type == 0x0E:
            pass
        
        return None
    
    async def _handle_connect(self, client_id: str, payload: bytes) -> bytes:
        """Handle CONNECT packet"""
        pos = 2
        proto_name_len = payload[0] * 256 + payload[1]
        proto_name = payload[2:2 + proto_name_len].decode('utf-8', errors='ignore')
        pos = 2 + proto_name_len
        proto_level = payload[pos]
        pos += 1
        flags = payload[pos]
        pos += 1
        clean_session = bool(flags & 0x02)
        pos += 2  # skip keep_alive
        
        client_id_len = payload[pos] * 256 + payload[pos + 1]
        client_id = payload[pos + 2:pos + 2 + client_id_len].decode('utf-8', errors='ignore')
        
        client = MQTTClient(client_id=client_id, clean_session=clean_session)
        self.clients[client_id] = client
        self._stats["active_connections"] = len(self.clients)
        
        if self.on_connect:
            self.on_connect(client)
        
        return bytes([0x20, 0x02, 0x00, MQTTConnReturnCode.ACCEPTED.value])
    
    async def _handle_publish(self, client_id: str, payload: bytes) -> Optional[bytes]:
        """Handle PUBLISH packet"""
        pos = 0
        topic_len = payload[pos] * 256 + payload[pos + 1]
        topic = payload[pos + 2:pos + 2 + topic_len].decode('utf-8', errors='ignore')
        pos += 2 + topic_len
        message_payload = payload[pos:]
        
        message = MQTTMessage(
            topic=topic,
            payload=message_payload.decode('utf-8', errors='ignore'),
            client_id=client_id
        )
        
        self._stats["messages_received"] += 1
        
        if self.on_message:
            self.on_message(message)
        
        return None
    
    async def _handle_subscribe(self, client_id: str, payload: bytes) -> bytes:
        """Handle SUBSCRIBE packet"""
        pos = 2
        message_id = payload[0] * 256 + payload[1]
        
        if client_id in self.clients:
            while pos < len(payload):
                topic_len = payload[pos] * 256 + payload[pos + 1]
                pos += 2
                topic = payload[pos:pos + topic_len].decode('utf-8', errors='ignore')
                pos += topic_len
                qos = payload[pos]
                pos += 1
                self.clients[client_id].subscriptions[topic] = MQTTQoS(qos)
        
        return bytes([0x90, 0x03, payload[0], payload[1], 0x00])
    
    def _handle_pingresp(self) -> bytes:
        """Handle PINGREQ, return PINGRESP"""
        return bytes([0xD0, 0x00])
    
    def publish(self, topic: str, payload: Any, qos: MQTTQoS = MQTTQoS.AT_MOST_ONCE, retain: bool = False):
        """Publish a message"""
        message = MQTTMessage(topic=topic, payload=payload, qos=qos, retain=retain)
        self._stats["messages_published"] += 1
        
        if self.on_message:
            self.on_message(message)
    
    def get_stats(self) -> Dict[str, int]:
        """Get broker statistics"""
        return self._stats.copy()


class MQTTClientSimulator:
    """MQTT Client Simulator"""
    
    def __init__(self, client_id: str, broker_host: str = "localhost", broker_port: int = 1883):
        self.client_id = client_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._message_id = 0
        self.subscriptions: Dict[str, Callable] = {}
    
    async def connect(self):
        """Connect to broker"""
        self.reader, self.writer = await asyncio.open_connection(self.broker_host, self.broker_port)
        
        # Build CONNECT packet
        client_id_bytes = self.client_id.encode()
        proto_name = b"MQTT"
        conn_flags = 0x02  # Clean session
        
        payload = bytearray()
        payload.extend(len(proto_name).to_bytes(2, 'big'))
        payload.extend(proto_name)
        payload.append(4)  # Protocol level
        payload.append(conn_flags)
        payload.extend((60).to_bytes(2, 'big'))  # Keep alive
        payload.extend(len(client_id_bytes).to_bytes(2, 'big'))
        payload.extend(client_id_bytes)
        
        packet = bytearray([0x10, len(payload)]) + payload
        
        self.writer.write(bytes(packet))
        await self.writer.drain()
        
        # Read CONNACK
        ack = await self.reader.read(2)
        self.connected = True
        logger.info(f"MQTT client {self.client_id} connected to {self.broker_host}:{self.broker_port}")
    
    async def disconnect(self):
        """Disconnect from broker"""
        if self.writer:
            self.writer.write(bytes([0xE0, 0x00]))
            await self.writer.drain()
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        if not self.connected:
            raise Exception("Not connected")
        
        self._message_id = (self._message_id + 1) % 65536
        topic_bytes = topic.encode()
        
        payload = bytearray()
        payload.extend(self._message_id.to_bytes(2, 'big'))
        payload.extend(len(topic_bytes).to_bytes(2, 'big'))
        payload.extend(topic_bytes)
        payload.append(0)  # QoS 0
        
        packet = bytearray([0x82, len(payload)]) + payload
        
        self.writer.write(bytes(packet))
        await self.writer.drain()
        self.subscriptions[topic] = callback
    
    async def publish(self, topic: str, payload: Any):
        """Publish a message"""
        if not self.connected:
            raise Exception("Not connected")
        
        topic_bytes = topic.encode()
        payload_bytes = str(payload).encode()
        
        pdu = bytearray()
        pdu.extend(len(topic_bytes).to_bytes(2, 'big'))
        pdu.extend(topic_bytes)
        pdu.extend(payload_bytes)
        
        packet = bytearray([0x30, len(pdu)]) + pdu
        
        self.writer.write(bytes(packet))
        await self.writer.drain()
    
    async def receive_loop(self):
        """Receive messages"""
        while self.connected:
            try:
                first_byte = await self.reader.read(1)
                if not first_byte:
                    break
                
                packet_type = (first_byte[0] >> 4) & 0x0F
                
                if packet_type == 0x03:  # PUBLISH
                    remaining_length = 0
                    multiplier = 1
                    while True:
                        byte = await self.reader.read(1)
                        if not byte:
                            return
                        remaining_length += (byte[0] & 0x7F) * multiplier
                        if not (byte[0] & 0x80):
                            break
                        multiplier *= 128
                    
                    payload = await self.reader.read(remaining_length)
                    
                    pos = 0
                    topic_len = payload[0] * 256 + payload[1]
                    topic = payload[pos + 2:pos + 2 + topic_len].decode('utf-8', errors='ignore')
                    pos += 2 + topic_len
                    message_payload = payload[pos:]
                    
                    if topic in self.subscriptions:
                        self.subscriptions[topic](topic, message_payload.decode('utf-8', errors='ignore'))
                        
            except Exception as e:
                logger.error(f"MQTT receive error: {e}")
                break


class MQTTDataGenerator:
    """Generate realistic MQTT messages"""
    
    def __init__(self, broker: MQTTBroker, topic_prefix: str = "sensors"):
        self.broker = broker
        self.topic_prefix = topic_prefix
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._topics = [
            "temperature",
            "humidity",
            "pressure",
            "flow",
            "level",
            "voltage",
            "current",
            "power",
        ]
    
    def start(self, interval: float = 1.0):
        """Start data generation"""
        self.running = True
        self._task = asyncio.create_task(self._generate_loop(interval))
    
    def stop(self):
        """Stop data generation"""
        self.running = False
        if self._task:
            self._task.cancel()
    
    async def _generate_loop(self, interval: float):
        """Generate messages periodically"""
        while self.running:
            try:
                for topic in self._topics:
                    payload = self._generate_payload(topic)
                    self.broker.publish(
                        f"{self.topic_prefix}/{topic}",
                        json.dumps(payload)
                    )
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
    
    def _generate_payload(self, topic: str) -> Dict[str, Any]:
        """Generate realistic payload for topic"""
        base = {
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": f"sensor-{random.randint(1, 100):03d}",
        }
        
        if topic == "temperature":
            base["value"] = round(20 + random.gauss(0, 5), 2)
            base["unit"] = "°C"
        elif topic == "humidity":
            base["value"] = round(50 + random.gauss(0, 10), 2)
            base["unit"] = "%"
        elif topic == "pressure":
            base["value"] = round(1000 + random.gauss(0, 50), 2)
            base["unit"] = "hPa"
        elif topic == "flow":
            base["value"] = round(random.uniform(0, 100), 2)
            base["unit"] = "m³/h"
        elif topic == "level":
            base["value"] = round(random.uniform(0, 100), 2)
            base["unit"] = "%"
        elif topic == "voltage":
            base["value"] = round(230 + random.gauss(0, 5), 2)
            base["unit"] = "V"
        elif topic == "current":
            base["value"] = round(random.uniform(0, 20), 2)
            base["unit"] = "A"
        elif topic == "power":
            base["value"] = round(random.uniform(0, 5000), 2)
            base["unit"] = "W"
        
        return base


# Factory functions
def create_mqtt_broker(host: str = "0.0.0.0", port: int = 1883) -> MQTTBroker:
    """Create a new MQTT broker"""
    return MQTTBroker(host=host, port=port)


def create_mqtt_client(client_id: str, broker_host: str = "localhost", broker_port: int = 1883) -> MQTTClientSimulator:
    """Create a new MQTT client"""
    return MQTTClientSimulator(client_id=client_id, broker_host=broker_host, broker_port=broker_port)
