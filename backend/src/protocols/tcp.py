"""
TCP Connection Simulator
TCP server/client simulation with connection pooling
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


class TCPConnectionState(Enum):
    """TCP Connection States"""
    CLOSED = 0
    LISTEN = 1
    SYN_SENT = 2
    SYN_RECEIVED = 3
    ESTABLISHED = 4
    FIN_WAIT_1 = 5
    FIN_WAIT_2 = 6
    CLOSE_WAIT = 7
    CLOSING = 8
    LAST_ACK = 9
    TIME_WAIT = 10


@dataclass
class TCPConnection:
    """TCP Connection"""
    connection_id: str
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    state: TCPConnectionState = TCPConnectionState.CLOSED
    established_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    bytes_sent: int = 0
    bytes_received: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    protocol: str = "raw"
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "connection_id": self.connection_id,
            "local_addr": self.local_addr,
            "local_port": self.local_port,
            "remote_addr": self.remote_addr,
            "remote_port": self.remote_port,
            "state": self.state.name,
            "established_at": self.established_at.isoformat() if self.established_at else None,
            "last_activity": self.last_activity.isoformat(),
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "protocol": self.protocol,
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms
        }


@dataclass
class TCPServerConfig:
    """TCP Server Configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    max_connections: int = 1000
    connection_timeout: int = 300
    keepalive_interval: int = 30
    protocol: str = "raw"
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    message_delimiter: str = "\n"
    max_message_size: int = 65536


class TCPServer:
    """TCP Server Simulator"""
    
    def __init__(self, config: Optional[TCPServerConfig] = None):
        self.config = config or TCPServerConfig()
        self.connections: Dict[str, TCPConnection] = {}
        self.running = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._connection_counter = 0
        
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        self.on_packet: Optional[Callable] = None
        
        # Statistics
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
            "total_messages": 0,
            "connection_errors": 0
        }
    
    async def start(self):
        """Start the TCP server"""
        self.running = True
        
        self._server = await asyncio.start_server(
            self._handle_client,
            self.config.host,
            self.config.port,
            reuse_address=True
        )
        
        logger.info(
            f"TCP Server started on {self.config.host}:{self.config.port} "
            f"(protocol: {self.config.protocol})"
        )
        
        async with self._server:
            await self._server.serve_forever()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        # Close all connections
        for conn in list(self.connections.values()):
            self._close_connection(conn)
        
        if self._server:
            self._server.close()
        
        logger.info("TCP Server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection"""
        addr = writer.get_extra_info('peername')
        self._connection_counter += 1
        
        conn_id = hashlib.md5(f"{addr[0]}:{addr[1]}:{self._connection_counter}".encode()).hexdigest()[:12]
        
        # Check max connections
        if len(self.connections) >= self.config.max_connections:
            logger.warning(f"Max connections reached, rejecting {addr}")
            writer.close()
            await writer.wait_closed()
            return
        
        # Create connection
        conn = TCPConnection(
            connection_id=conn_id,
            local_addr=addr[0],
            local_port=addr[1],
            remote_addr=addr[0],
            remote_port=addr[1],
            state=TCPConnectionState.ESTABLISHED,
            established_at=datetime.utcnow(),
            protocol=self.config.protocol
        )
        self.connections[conn_id] = conn
        self._stats["total_connections"] += 1
        self._stats["active_connections"] += 1
        
        if self.on_connect:
            self.on_connect(conn)
        
        try:
            # Message reading loop
            buffer = b''
            
            while self.running:
                try:
                    # Read data with timeout
                    data = await asyncio.wait_for(
                        reader.read(1024),
                        timeout=self.config.connection_timeout
                    )
                    
                    if not data:
                        break
                    
                    conn.bytes_received += len(data)
                    conn.last_activity = datetime.utcnow()
                    self._stats["total_bytes_received"] += len(data)
                    
                    if self.on_packet:
                        self.on_packet({
                            "connection_id": conn_id,
                            "data": data.hex(),
                            "direction": "inbound"
                        })
                    
                    # Process data based on protocol
                    if self.config.protocol == "raw":
                        buffer += data
                        
                        # Process messages by delimiter
                        delimiter = self.config.message_delimiter.encode()
                        while delimiter in buffer:
                            message, buffer = buffer.split(delimiter, 1)
                            if message:
                                await self._process_message(conn, message)
                    
                    elif self.config.protocol == "json":
                        buffer += data
                        try:
                            messages = buffer.split(b'\x00')
                            for msg in messages[:-1]:
                                if msg:
                                    await self._process_message(conn, msg)
                            buffer = messages[-1]
                        except:
                            pass
                    
                    elif self.config.protocol == "line":
                        buffer += data
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            if line.strip():
                                await self._process_message(conn, line.strip())
                    
                except asyncio.TimeoutError:
                    # Keepalive check
                    if (datetime.utcnow() - conn.last_activity).seconds > self.config.connection_timeout:
                        break
                    continue
                    
        except Exception as e:
            logger.error(f"TCP client error: {e}")
            self._stats["connection_errors"] += 1
        finally:
            self._close_connection(conn)
            writer.close()
            await writer.wait_closed()
    
    async def _process_message(self, conn: TCPConnection, data: bytes):
        """Process received message"""
        conn.messages_received += 1
        self._stats["total_messages"] += 1
        
        # Parse message
        try:
            if self.config.protocol == "json":
                message = json.loads(data.decode())
            else:
                message = data.decode('utf-8', errors='ignore')
        except:
            message = data.hex()
        
        if self.on_message:
            response = await self.on_message(conn, message)
            
            # Send response if any
            if response:
                if isinstance(response, dict):
                    response_data = json.dumps(response).encode()
                else:
                    response_data = str(response).encode()
                
                if self.config.protocol == "raw":
                    response_data += self.config.message_delimiter.encode()
                
                conn.bytes_sent += len(response_data)
                self._stats["total_bytes_sent"] += len(response_data)
                conn.messages_sent += 1
                
                # Simulate latency
                await asyncio.sleep(conn.latency_ms / 1000)
    
    def _close_connection(self, conn: TCPConnection):
        """Close connection"""
        conn.state = TCPConnectionState.CLOSED
        if conn.connection_id in self.connections:
            del self.connections[conn.connection_id]
        
        self._stats["active_connections"] = max(0, self._stats["active_connections"] - 1)
        
        if self.on_disconnect:
            self.on_disconnect(conn)
    
    def send_to_connection(self, connection_id: str, data: Any) -> bool:
        """Send data to specific connection"""
        # This would need the writer reference - simplified
        return False
    
    def broadcast(self, data: Any):
        """Broadcast to all connections"""
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode()
        else:
            data_bytes = str(data).encode()
        
        for conn in self.connections.values():
            conn.bytes_sent += len(data_bytes)
            conn.messages_sent += 1
        
        self._stats["total_bytes_sent"] += len(data_bytes) * len(self.connections)
        self._stats["total_messages"] += len(self.connections)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total": self._stats["total_connections"],
            "active": len(self.connections),
            "by_protocol": {
                "raw": sum(1 for c in self.connections.values() if c.protocol == "raw"),
                "json": sum(1 for c in self.connections.values() if c.protocol == "json"),
            }
        }
    
    def get_all_connections(self) -> List[dict]:
        """Get all connections"""
        return [conn.to_dict() for conn in self.connections.values()]
    
    def close_connection(self, connection_id: str) -> bool:
        """Close specific connection"""
        conn = self.connections.get(connection_id)
        if conn:
            self._close_connection(conn)
            return True
        return False


class TCPClient:
    """TCP Client Simulator"""
    
    def __init__(self, host: str, port: int, protocol: str = "raw"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.connected = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
    
    async def connect(self, timeout: float = 10.0) -> bool:
        """Connect to server"""
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=timeout
            )
            self.connected = True
            logger.info(f"TCP client connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"TCP connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False
    
    async def send(self, data: Any, delimiter: str = "\n") -> bool:
        """Send data"""
        if not self.connected:
            return False
        
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            
            data = str(data)
            if self.protocol == "raw":
                data += delimiter
            
            self.writer.write(data.encode())
            await self.writer.drain()
            
            self.messages_sent += 1
            self.bytes_sent += len(data.encode())
            return True
        except Exception as e:
            logger.error(f"TCP send failed: {e}")
            return False
    
    async def receive(self, timeout: float = 5.0) -> Optional[str]:
        """Receive data"""
        if not self.connected:
            return None
        
        try:
            data = await asyncio.wait_for(
                self.reader.read(1024),
                timeout=timeout
            )
            
            if data:
                self.bytes_received += len(data)
                self.messages_received += 1
                return data.decode('utf-8', errors='ignore')
            return None
        except asyncio.TimeoutError:
            return None
    
    async def send_and_receive(self, data: Any, timeout: float = 5.0) -> Optional[str]:
        """Send and receive"""
        await self.send(data)
        return await self.receive(timeout)


class TCPConnectionPool:
    """TCP Connection Pool for simulating many devices"""
    
    def __init__(self, server_host: str, server_port: int, max_connections: int = 1000):
        self.server_host = server_host
        self.server_port = server_port
        self.max_connections = max_connections
        self.clients: List[TCPClient] = []
        self.running = False
    
    async def connect_all(self, protocol: str = "raw"):
        """Connect all clients"""
        self.running = True
        
        for i in range(self.max_connections):
            client = TCPClient(self.server_host, self.server_port, protocol)
            success = await client.connect()
            
            if success:
                self.clients.append(client)
            
            # Stagger connections
            await asyncio.sleep(0.001)
        
        logger.info(f"Connected {len(self.clients)} clients to {self.server_host}:{self.server_port}")
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        self.running = False
        
        for client in self.clients:
            await client.disconnect()
        
        self.clients.clear()
    
    async def broadcast(self, data: Any):
        """Broadcast to all clients"""
        for client in self.clients:
            await client.send(data)
    
    async def simulate_traffic(self, interval: float = 1.0):
        """Simulate traffic from all clients"""
        while self.running:
            for client in self.clients:
                if random.random() > 0.5:
                    message = {"device_id": hash(id(client)), "value": random.uniform(0, 100)}
                    await client.send(message)
            
            await asyncio.sleep(interval)
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        total_sent = sum(c.bytes_sent for c in self.clients)
        total_received = sum(c.bytes_received for c in self.clients)
        
        return {
            "connected_clients": len(self.clients),
            "total_bytes_sent": total_sent,
            "total_bytes_received": total_received,
            "avg_bytes_per_client": total_sent / len(self.clients) if self.clients else 0
        }


# Factory functions
def create_tcp_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    protocol: str = "raw"
) -> TCPServer:
    """Create a new TCP server"""
    config = TCPServerConfig(host=host, port=port, protocol=protocol)
    return TCPServer(config)


def create_tcp_client(host: str, port: int, protocol: str = "raw") -> TCPClient:
    """Create a new TCP client"""
    return TCPClient(host=host, port=port, protocol=protocol)
