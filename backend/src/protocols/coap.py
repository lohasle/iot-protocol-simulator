"""
CoAP (Constrained Application Protocol) Server Simulator
RFC 7252 implementation
"""

import asyncio
import random
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import struct


class CoAPCode(Enum):
    """CoAP Response Codes"""
    EMPTY = 0.00
    GET = 1.00
    POST = 2.00
    PUT = 3.00
    DELETE = 4.00
    CREATED = 2.01
    DELETED = 2.02
    VALID = 2.03
    CHANGED = 2.04
    CONTENT = 2.05
    BAD_REQUEST = 4.00
    UNAUTHORIZED = 4.01
    BAD_OPTION = 4.02
    FORBIDDEN = 4.03
    NOT_FOUND = 4.04
    METHOD_NOT_ALLOWED = 4.05
    PRECONDITION_FAILED = 4.12
    UNSUPPORTED_CONTENT_FORMAT = 4.15


class CoAPContentFormat(Enum):
    """CoAP Content Formats"""
    TEXT_PLAIN = 0
    APPLICATION_LINK_FORMAT = 40
    APPLICATION_JSON = 50
    APPLICATION_OCTET_STREAM = 41
    APPLICATION_XML = 41


class CoAPOption(Enum):
    """CoAP Options"""
    IF_MATCH = 1
    URI_HOST = 3
    ETAG = 4
    IF_NONE_MATCH = 5
    OBSERVE = 6
    URI_PORT = 7
    LOCATION_PATH = 8
    URI_PATH = 11
    CONTENT_FORMAT = 12
    MAX_AGE = 14
    URI_QUERY = 15
    ACCEPT = 17
    LOCATION_QUERY = 20


@dataclass
class CoAPResource:
    """CoAP Resource"""
    path: str
    resource_type: str = "sensor"
    content_type: CoAPContentFormat = CoAPAPPLICATION_JSON
    observable: bool = False
    value: Any = None
    max_age: int = 60
    etag: Optional[bytes] = None
    observers: List[Any] = field(default_factory=list)
    
    def __post_init__(self):
        if self.etag is None:
            self.etag = bytes([random.randint(0, 255) for _ in range(4)])


class CoAPServer:
    """CoAP Server Simulator"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5683):
        self.host = host
        self.port = port
        self.resources: Dict[str, CoAPResource] = {}
        self.running = False
        self._server: Optional[asyncio.DatagramProtocol] = None
        
        self.on_request: Optional[Callable] = None
        self.on_observation: Optional[Callable] = None
        
        # Initialize default resources
        self._initialize_resources()
    
    def _initialize_resources(self):
        """Initialize default CoAP resources"""
        # Core resources
        self.add_resource(CoAPResource(path="/", resource_type="core"))
        self.add_resource(CoAPResource(path="/.well-known/core", resource_type="core"))
        
        # Sensor resources
        self.add_resource(CoAPResource(path="/temperature", resource_type="sensor", observable=True, value=20.0))
        self.add_resource(CoAPResource(path="/humidity", resource_type="sensor", observable=True, value=50.0))
        self.add_resource(CoAPResource(path="/pressure", resource_type="sensor", observable=True, value=1013.25))
        self.add_resource(CoAPResource(path="/light", resource_type="sensor", observable=True, value=500))
        self.add_resource(CoAPResource(path="/motion", resource_type="actuator", value=False))
        
        # Device resources
        self.add_resource(CoAPResource(path="/device/info", resource_type="device", value={"name": "IoT-Device", "version": "1.0.0"}))
        self.add_resource(CoAPResource(path="/device/status", resource_type="device", observable=True, value={"state": "running"}))
        
        # Control resources
        self.add_resource(CoAPResource(path="/control/led", resource_type="actuator", value={"state": "off"}))
        self.add_resource(CoAPResource(path="/control/relay", resource_type="actuator", value={"state": "off"}))
    
    def add_resource(self, resource: CoAPResource):
        """Add a CoAP resource"""
        self.resources[resource.path] = resource
        logger.info(f"Added CoAP resource: {resource.path}")
    
    async def start(self):
        """Start the CoAP server"""
        self.running = True
        
        loop = asyncio.get_event_loop()
        self._server = await loop.create_datagram_endpoint(
            lambda: self._CoAPProtocol(),
            local_addr=(self.host, self.port)
        )
        logger.info(f"CoAP Server started on {self.host}:{self.port}")
        
        # Start value simulation
        asyncio.create_task(self._simulate_values())
        
        # Start observation notifications
        asyncio.create_task(self._notify_observers())
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self._server:
            self._server.close()
        logger.info("CoAP Server stopped")
    
    class _CoAPProtocol(asyncio.DatagramProtocol):
        """CoAP UDP Protocol"""
        
        def __init__(self):
            super().__init__()
            self.server: Optional[CoAPServer] = None
        
        def connection_made(self, transport):
            self.transport = transport
        
        def datagram_received(self, data: bytes, addr):
            if self.server:
                response = self.server._process_request(data, addr)
                if response:
                    self.transport.sendto(response, addr)
        
        def error_received(self, exc):
            logger.error(f"CoAP error: {exc}")
        
        def connection_lost(self, exc):
            pass
    
    def _process_request(self, data: bytes, addr) -> Optional[bytes]:
        """Process CoAP request"""
        try:
            if len(data) < 4:
                return None
            
            # Parse CoAP header
            version = (data[0] >> 6) & 0x03
            token_length = data[0] & 0x0F
            code_class = (data[1] >> 5) & 0x07
            code_detail = data[1] & 0x1F
            message_id = struct.unpack(">H", data[2:4])[0]
            
            code = CoAPCode(code_class * 100 + code_detail)
            token = data[4:4 + token_length] if token_length > 0 else b''
            
            # Parse options
            options, payload = self._parse_options(data[4 + token_length:])
            
            # Get URI path
            uri_path = self._get_option_value(options, CoAPOption.URI_PATH)
            
            # Process request
            return self._handle_request(code, uri_path, options, payload, message_id, token, addr)
            
        except Exception as e:
            logger.error(f"CoAP processing error: {e}")
            return self._create_response(CoAPCode.BAD_REQUEST, message_id, token, b"Bad Request")
    
    def _parse_options(self, data: bytes) -> tuple:
        """Parse CoAP options"""
        options = []
        pos = 0
        
        while pos < len(data) and data[pos] != 0xFF:
            option_delta = (data[pos] >> 4) & 0x0F
            option_length = data[pos] & 0x0F
            pos += 1
            
            # Decode extended delta/length
            if option_delta == 13:
                option_delta = data[pos] + 13
                pos += 1
            elif option_delta == 14:
                option_delta = data[pos] * 256 + data[pos + 1] + 269
                pos += 2
            
            if option_length == 13:
                option_length = data[pos] + 13
                pos += 1
            elif option_length == 14:
                option_length = data[pos] * 256 + data[pos + 1] + 269
                pos += 2
            
            # Get option value
            value = data[pos:pos + option_length]
            options.append((option_delta, value))
            pos += option_length
        
        # Payload (if 0xFF present)
        payload = b''
        if pos < len(data) and data[pos] == 0xFF:
            payload = data[pos + 1:]
        
        return options, payload
    
    def _get_option_value(self, options: list, option_type: CoAPOption) -> Optional[List[bytes]]:
        """Get option value by type"""
        values = []
        current_type = 0
        
        for delta, value in options:
            current_type += delta
            if current_type == option_type.value:
                values.append(value)
        
        return values if values else None
    
    def _handle_request(
        self,
        code: CoAPCode,
        uri_path: Optional[List[bytes]],
        options: list,
        payload: bytes,
        message_id: int,
        token: bytes,
        addr
    ) -> Optional[bytes]:
        """Handle CoAP request"""
        # Build path
        path = '/'.join([v.decode() for v in uri_path or []])
        if not path:
            path = '/'
        
        # Handle by method
        if code == CoAPCode.GET:
            return self._handle_get(path, options, message_id, token, addr)
        elif code == CoAPCode.POST:
            return self._handle_post(path, payload, options, message_id, token, addr)
        elif code == CoAPCode.PUT:
            return self._handle_put(path, payload, options, message_id, token, addr)
        elif code == CoAPCode.DELETE:
            return self._handle_delete(path, message_id, token, addr)
        
        return self._create_response(CoAPCode.METHOD_NOT_ALLOWED, message_id, token, b"Method Not Allowed")
    
    def _handle_get(
        self,
        path: str,
        options: list,
        message_id: int,
        token: bytes,
        addr
    ) -> bytes:
        """Handle GET request"""
        resource = self.resources.get(path)
        
        if not resource:
            return self._create_response(CoAPCode.NOT_FOUND, message_id, token, b"Not Found")
        
        # Check if observing
        observe_options = self._get_option_value(options, CoAPOption.OBSERVE)
        is_observing = observe_options and observe_options[0][0] == 0
        
        if is_observing:
            # Add to observers (simplified)
            resource.observers.append((token, addr))
            if self.on_observation:
                self.on_observation({"path": path, "token": token.hex()})
        
        # Generate response
        content_type = resource.content_format.value
        payload = self._serialize_value(resource.value, resource.content_format)
        
        options = [(CoAPOption.CONTENT_FORMAT.value, struct.pack(">H", content_format))]
        if resource.etag:
            options.append((CoAPOption.ETAG.value, resource.etag))
        
        return self._create_response(CoAPCode.CONTENT, message_id, token, payload, options)
    
    def _handle_post(
        self,
        path: str,
        payload: bytes,
        options: list,
        message_id: int,
        token: bytes,
        addr
    ) -> bytes:
        """Handle POST request"""
        # Check if creating new resource
        if path.endswith('/') or path not in self.resources:
            # Create new resource
            new_path = path.rstrip('/') + '/' + str(random.randint(100, 999))
            
            content_format = self._get_option_value(options, CoAPOption.CONTENT_FORMAT)
            if content_format:
                cf = int.from_bytes(content_format[0], 'big')
            else:
                cf = CoAPContentFormat.APPLICATION_JSON.value
            
            new_resource = CoAPResource(
                path=new_path,
                resource_type="user",
                content_format=CoAPContentFormat(cf),
                value=self._deserialize_value(payload, CoAPContentFormat(cf))
            )
            self.resources[new_path] = new_resource
            
            # Return Created with Location
            location = self._get_option_value(options, CoAPOption.LOCATION_PATH)
            location_path = '/'.join([v.decode() for v in location or []])
            
            options = [(CoAPOption.LOCATION_PATH.value, new_path.encode())]
            return self._create_response(CoAPCode.CREATED, message_id, token, b"", options)
        
        # Otherwise, update existing resource
        return self._handle_put(path, payload, options, message_id, token, addr)
    
    def _handle_put(
        self,
        path: str,
        payload: bytes,
        options: list,
        message_id: int,
        token: bytes,
        addr
    ) -> bytes:
        """Handle PUT request"""
        resource = self.resources.get(path)
        
        if not resource:
            return self._create_response(CoAPCode.NOT_FOUND, message_id, token, b"Not Found")
        
        # Update value
        content_format = self._get_option_value(options, CoAPOption.CONTENT_FORMAT)
        if content_format:
            cf = int.from_bytes(content_format[0], 'big')
        else:
            cf = resource.content_format.value
        
        resource.value = self._deserialize_value(payload, CoAPContentFormat(cf))
        
        return self._create_response(CoAPCode.CHANGED, message_id, token, b"Changed")
    
    def _handle_delete(self, path: str, message_id: int, token: bytes, addr) -> bytes:
        """Handle DELETE request"""
        if path in self.resources:
            del self.resources[path]
            return self._create_response(CoAPCode.DELETED, message_id, token, b"Deleted")
        
        return self._create_response(CoAPCode.NOT_FOUND, message_id, token, b"Not Found")
    
    def _create_response(
        self,
        code: CoAPCode,
        message_id: int,
        token: bytes,
        payload: bytes = b'',
        options: list = None
    ) -> bytes:
        """Create CoAP response"""
        # Build options delta
        options_data = bytearray()
        last_option = 0
        
        for option_type, value in options or []:
            option_delta = option_type - last_option
            if option_delta >= 13:
                options_data.append(13 << 4 | (option_delta - 13))
            else:
                options_data.append(option_delta << 4)
            
            if len(value) >= 13:
                options_data.extend([13, len(value) - 13])
            else:
                options_data.append(len(value))
            
            options_data.extend(value)
            last_option = option_type
        
        # Build header
        header = bytearray()
        header.append(0x40 | len(token))  # Version 1, token length
        header.append(code.value)
        header.extend(struct.pack(">H", message_id))
        header.extend(token)
        header.extend(options_data)
        
        # Payload marker
        if payload:
            header.append(0xFF)
            header.extend(payload)
        
        return bytes(header)
    
    def _serialize_value(self, value: Any, content_format: CoAPContentFormat) -> bytes:
        """Serialize value based on content format"""
        if isinstance(value, (dict, list)):
            if content_format == CoAPContentFormat.APPLICATION_JSON:
                return json.dumps(value).encode()
            else:
                return str(value).encode()
        elif isinstance(value, (int, float)):
            return str(value).encode()
        elif isinstance(value, bool):
            return b"true" if value else b"false"
        else:
            return str(value).encode()
    
    def _deserialize_value(self, payload: bytes, content_format: CoAPContentFormat) -> Any:
        """Deserialize value from payload"""
        try:
            if content_format == CoAPContentFormat.APPLICATION_JSON:
                return json.loads(payload.decode())
            elif content_format == CoAPContentFormat.TEXT_PLAIN:
                text = payload.decode().strip()
                if text.lower() == 'true':
                    return True
                elif text.lower() == 'false':
                    return False
                try:
                    if '.' in text:
                        return float(text)
                    return int(text)
                except:
                    return text
            else:
                return payload.decode().strip()
        except:
            return payload
    
    async def _simulate_values(self):
        """Simulate sensor value changes"""
        while self.running:
            try:
                for path, resource in self.resources.items():
                    if resource.resource_type == "sensor":
                        resource.value = self._generate_realistic_value(path, resource.value)
                
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
    
    def _generate_realistic_value(self, path: str, current: Any) -> Any:
        """Generate realistic sensor value"""
        path_lower = path.lower()
        
        if "temperature" in path_lower:
            return round((current or 20) + random.gauss(0, 0.5), 2)
        elif "humidity" in path_lower:
            return round(max(0, min(100, (current or 50) + random.gauss(0, 2))), 2)
        elif "pressure" in path_lower:
            return round((current or 1013) + random.gauss(0, 1), 2)
        elif "light" in path_lower:
            return round(max(0, (current or 500) + random.gauss(0, 50)), 0)
        elif "motion" in path_lower:
            return random.random() > 0.9
        
        return current
    
    async def _notify_observers(self):
        """Notify observers of resource changes"""
        while self.running:
            try:
                for path, resource in self.resources.items():
                    if resource.observers and resource.observable:
                        payload = self._serialize_value(resource.value, resource.content_format)
                        
                        for token, addr in list(resource.observers):
                            response = self._create_response(
                                CoAPCode.CONTENT,
                                random.randint(1, 65535),
                                token,
                                payload,
                                [(CoAPOption.CONTENT_FORMAT.value, struct.pack(">H", resource.content_format.value))]
                            )
                            # Would send to addr here
                
                await asyncio.sleep(resource.max_age if hasattr(resource, 'max_age') else 30)
            except asyncio.CancelledError:
                break
    
    def get_resources(self) -> Dict[str, Dict]:
        """Get all resources"""
        return {
            path: {
                "path": path,
                "resource_type": res.resource_type,
                "observable": res.observable,
                "value": res.value
            }
            for path, res in self.resources.items()
        }


class CoAPClient:
    """CoAP Client Simulator"""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 5683):
        self.server_host = server_host
        self.server_port = server_port
        self.message_id = 0
        self.token = bytes([random.randint(0, 255) for _ in range(4)])
        self._transport = None
    
    async def get(self, path: str) -> Optional[dict]:
        """GET request"""
        return {"code": 2.05, "payload": {"value": random.uniform(0, 100)}}
    
    async def put(self, path: str, value: Any) -> bool:
        """PUT request"""
        logger.info(f"PUT {path} = {value}")
        return True
    
    async def post(self, path: str, value: Any) -> bool:
        """POST request"""
        logger.info(f"POST {path} = {value}")
        return True
    
    async def delete(self, path: str) -> bool:
        """DELETE request"""
        logger.info(f"DELETE {path}")
        return True


# Factory function
def create_coap_server(host: str = "0.0.0.0", port: int = 5683) -> CoAPServer:
    """Create a new CoAP server"""
    return CoAPServer(host=host, port=port)
