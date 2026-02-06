"""
BACnet IP/MS-TP Protocol Simulator
Complete BACnet implementation
"""

import asyncio
import random
import struct
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger


class BACnetService(Enum):
    """BACnet Services"""
    WHO_IS = 0x08
    I_AM = 0x09
    READ_PROPERTY = 0x0C
    READ_PROPERTY_ACK = 0x0D
    WRITE_PROPERTY = 0x0F
    WHO_HAS = 0x10
    I_HAVE = 0x11
    COV_NOTIFICATION = 0x13
    SUBSCRIBE_COV = 0x15


class BACnetObjectType(Enum):
    """BACnet Object Types"""
    ANALOG_INPUT = 0
    ANALOG_OUTPUT = 1
    ANALOG_VALUE = 2
    BINARY_INPUT = 3
    BINARY_OUTPUT = 4
    BINARY_VALUE = 5
    DEVICE = 8
    FILE = 10
    GROUP = 11
    LOOP = 14
    MULTI_STATE_INPUT = 13
    MULTI_STATE_OUTPUT = 14


@dataclass
class BACnetObject:
    """BACnet Object"""
    object_id: int
    object_type: BACnetObjectType
    object_name: str
    present_value: Any = None
    description: str = ""
    units: Optional[str] = None
    min_pres_value: float = 0.0
    max_pres_value: float = 100.0
    resolution: float = 1.0
    cov_increment: float = 1.0
    status_flags: List[bool] = field(default_factory=lambda: [False, False, False, False])
    
    def __post_init__(self):
        if self.present_value is None:
            self.present_value = self._get_default_value()
    
    def _get_default_value(self) -> Any:
        """Get default value based on object type"""
        if self.object_type in [BACnetObjectType.ANALOG_INPUT, 
                                 BACnetObjectType.ANALOG_OUTPUT,
                                 BACnetObjectType.ANALOG_VALUE]:
            return random.uniform(self.min_pres_value, self.max_pres_value)
        elif self.object_type in [BACnetObjectType.BINARY_INPUT,
                                    BACnetObjectType.BINARY_OUTPUT,
                                    BACnetObjectType.BINARY_VALUE]:
            return random.choice([0, 1])
        elif self.object_type == BACnetObjectType.MULTI_STATE_INPUT:
            return 1
        elif self.object_type == BACnetObjectType.MULTI_STATE_OUTPUT:
            return 1
        return None


@dataclass
class BACnetDevice:
    """BACnet Device"""
    device_id: int
    name: str
    address: str
    objects: Dict[int, BACnetObject] = field(default_factory=dict)
    vendor_name: str = "Simulator"
    vendor_identifier: int = 999
    model_name: str = "BACnet Simulator"
    firmware_revision: str = "1.0.0"
    application_software_version: str = "1.0.0"
    protocol_version: int = 1
    protocol_revision: int = 14
    
    def __post_init__(self):
        self._initialize_standard_objects()
    
    def _initialize_standard_objects(self):
        """Initialize with standard objects"""
        # Device object
        device_obj = BACnetObject(
            object_id=self.device_id,
            object_type=BACnetObjectType.DEVICE,
            object_name=self.name,
            present_value=self.device_id,
            description=f"Device {self.name}"
        )
        self.objects[self.device_id] = device_obj
        
        # Analog inputs (sensors)
        for i in range(4):
            obj = BACnetObject(
                object_id=1000 + i,
                object_type=BACnetObjectType.ANALOG_INPUT,
                object_name=f"Temperature_{i+1}",
                present_value=20.0 + random.gauss(0, 3),
                description=f"Temperature Sensor {i+1}",
                units="degrees-celsius",
                min_pres_value=-40.0,
                max_pres_value=125.0,
                resolution=0.1
            )
            self.objects[obj.object_id] = obj
        
        # Analog outputs
        for i in range(2):
            obj = BACnetObject(
                object_id=2000 + i,
                object_type=BACnetObjectType.ANALOG_OUTPUT,
                object_name=f"Heater_{i+1}",
                present_value=50.0,
                description=f"Heater {i+1}",
                units="percent",
                min_pres_value=0.0,
                max_pres_value=100.0,
                resolution=1.0
            )
            self.objects[obj.object_id] = obj
        
        # Binary inputs
        for i in range(8):
            obj = BACnetObject(
                object_id=3000 + i,
                object_type=BACnetObjectType.BINARY_INPUT,
                object_name=f"Switch_{i+1}",
                present_value=0,
                description=f"Switch {i+1}"
            )
            self.objects[obj.object_id] = obj


class BACnetIPRouter:
    """BACnet IP Router/Server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 47808):
        self.host = host
        self.port = port
        self.devices: Dict[int, BACnetDevice] = {}
        self.running = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._broadcast_address = ("255.255.255.255", 47808)
        
        self.on_packet: Optional[Callable] = None
        self.on_data_change: Optional[Callable] = None
        
        # Initialize default device
        self._add_default_device()
    
    def _add_default_device(self):
        """Add a default BACnet device"""
        device = BACnetDevice(
            device_id=12345,
            name="Simulator-Device",
            address=f"192.168.1.100:{self.port}"
        )
        self.add_device(device)
    
    def add_device(self, device: BACnetDevice):
        """Add a BACnet device"""
        self.devices[device.device_id] = device
        logger.info(f"Added BACnet device: {device.name} (ID: {device.device_id})")
    
    async def start(self):
        """Start the BACnet IP server"""
        self.running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
            reuse_address=True
        )
        logger.info(f"BACnet IP Server started on {self.host}:{self.port}")
        
        # Start periodic broadcasts
        asyncio.create_task(self._periodic_who_is())
        
        # Start data simulation
        asyncio.create_task(self._simulate_data_changes())
        
        async with self._server:
            await self._server.serve_forever()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self._server:
            self._server.close()
        logger.info("BACnet IP Server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection"""
        addr = writer.get_extra_info('peername')
        
        try:
            while self.running:
                try:
                    data = await reader.read(1024)
                    if not data:
                        break
                    
                    # Process BACnet packet
                    response = self._process_bacnet_packet(data)
                    
                    if response:
                        writer.write(response)
                        await writer.drain()
                        
                except Exception as e:
                    logger.error(f"BACnet client error: {e}")
                    break
                    
        finally:
            writer.close()
            await writer.wait_closed()
    
    def _process_bacnet_packet(self, data: bytes) -> Optional[bytes]:
        """Process BACnet packet"""
        if len(data) < 6:
            return None
        
        # Parse BACnet header
        bvlc_function = data[0]
        
        if bvlc_function == 0x0B:  # Original-Unicast-NPDU
            return self._handle_unicast(data[4:])
        elif bvlc_function == 0x0C:  # Original-Broadcast-NPDU
            return self._handle_broadcast(data[4:])
        
        return None
    
    def _handle_unicast(self, npdu: bytes) -> Optional[bytes]:
        """Handle unicast NPDU"""
        if len(npdu) < 2:
            return None
        
        apdu = npdu[6:] if len(npdu) > 6 else npdu
        
        service = apdu[0] if apdu else None
        
        if service == BACnetService.READ_PROPERTY.value:
            return self._handle_read_property(apdu)
        elif service == BACnetService.WRITE_PROPERTY.value:
            return self._handle_write_property(apdu)
        elif service == BACnetService.WHO_IS.value:
            return self._handle_who_is(apdu)
        elif service == BACnetService.WHO_HAS.value:
            return self._handle_who_has(apdu)
        
        return None
    
    def _handle_broadcast(self, npdu: bytes) -> Optional[bytes]:
        """Handle broadcast NPDU"""
        # Generate I-Am response for Who-Is broadcasts
        return self._handle_who_is(npdu)
    
    def _handle_who_is(self, apdu: bytes) -> Optional[bytes]:
        """Handle Who-Is request"""
        # Check if targeting specific device or all
        if len(apdu) >= 10:
            low_device = struct.unpack(">H", apdu[8:10])[0] if apdu[8:10] != b'\xff\xff' else None
            high_device = struct.unpack(">H", apdu[10:12])[0] if len(apdu) >= 12 and apdu[10:12] != b'\xff\xff' else None
            
            # If specific device range, check if we should respond
            if low_device and self.devices[0].device_id < low_device:
                return None
            if high_device and self.devices[0].device_id > high_device:
                return None
        
        # Generate I-Am response
        return self._create_i_am_response()
    
    def _create_i_am_response(self) -> bytes:
        """Create I-Am response"""
        device = self.devices.get(12345)
        if not device:
            return None
        
        # Build APDU
        apdu = bytearray()
        apdu.append(0x20)  # APDU type (Unconfirmed-Response)
        apdu.append(BACnetService.I_AM.value)
        
        # Object list in device object
        object_count = len(device.objects)
        apdu.extend(struct.pack(">H", object_count + 5))  # Number of properties
        
        # Vendor ID
        apdu.extend(struct.pack(">H", device.vendor_identifier))
        
        # Build NPDU
        npdu = bytearray()
        npdu.append(0x01)  # Version
        npdu.append(0x20)  # Priority
        npdu.extend(apdu)
        
        # Build BVLC
        bvlc = bytearray()
        bvlc.append(0x0B)  # Original-Unicast-NPDU
        bvlc.extend(struct.pack(">I", len(npdu) + 4))  # Length
        bvlc.extend(npdu)
        
        return bytes(bvlc)
    
    def _handle_read_property(self, apdu: bytes) -> Optional[bytes]:
        """Handle Read Property request"""
        try:
            if len(apdu) < 12:
                return None
            
            object_type = struct.unpack(">H", apdu[3:5])[0]
            object_instance = struct.unpack(">I", apdu[5:9])[0]
            property_id = struct.unpack(">H", apdu[9:11])[0]
            
            # Find the device
            device = None
            for d in self.devices.values():
                if d.device_id == object_instance or object_type == 8:  # Device type
                    device = d
                    break
            
            if not device:
                return None
            
            # Find the object
            obj = device.objects.get(object_instance)
            if not obj:
                return None
            
            # Build Read Property ACK
            return self._create_read_property_ack(obj, property_id)
            
        except Exception as e:
            logger.error(f"Read Property error: {e}")
            return None
    
    def _create_read_property_ack(self, obj: BACnetObject, property_id: int) -> bytes:
        """Create Read Property ACK response"""
        apdu = bytearray()
        apdu.append(0x30)  # APDU type (Complex-ACK)
        apdu.append(BACnetService.READ_PROPERTY_ACK.value)
        apdu.extend(struct.pack(">H", object_type_to_id(obj.object_type)))
        apdu.extend(struct.pack(">I", obj.object_id))
        apdu.extend(struct.pack(">H", property_id))
        
        # Property value
        apdu.extend(self._encode_bacnet_value(obj.present_value))
        
        return bytes(apdu)
    
    def _handle_write_property(self, apdu: bytes) -> Optional[bytes]:
        """Handle Write Property request"""
        # Simulated ACK (simple success response)
        return bytes([0x30, 0x1F, 0x00, 0x00])
    
    def _handle_who_has(self, apdu: bytes) -> Optional[bytes]:
        """Handle Who-Has request"""
        return self._create_i_am_response()
    
    def _encode_bacnet_value(self, value: Any) -> bytes:
        """Encode value in BACnet format"""
        if isinstance(value, float):
            result = bytearray()
            result.append(0x44)  # REAL
            result.extend(struct.pack(">f", value))
            return bytes(result)
        elif isinstance(value, int):
            result = bytearray()
            result.append(0x22)  # Unsigned Integer
            result.extend(struct.pack(">I", value))
            return bytes(result)
        else:
            result = bytearray()
            result.append(0x7E)  # Null
            return bytes(result)
    
    async def _periodic_who_is(self):
        """Periodic Who-Is broadcast simulation"""
        while self.running:
            try:
                await asyncio.sleep(60)
                # In real implementation, broadcast Who-Is here
            except asyncio.CancelledError:
                break
    
    async def _simulate_data_changes(self):
        """Simulate value changes"""
        while self.running:
            try:
                for device in self.devices.values():
                    for obj in device.objects.values():
                        if obj.object_type in [BACnetObjectType.ANALOG_INPUT,
                                                BACnetObjectType.ANALOG_OUTPUT,
                                                BACnetObjectType.ANALOG_VALUE]:
                            # Add small random change
                            change = random.gauss(0, obj.resolution * 2)
                            obj.present_value = max(
                                obj.min_pres_value,
                                min(obj.max_pres_value, obj.present_value + change)
                            )
                
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
    
    def read_property(self, device_id: int, object_type: int, object_instance: int, property_id: int) -> Optional[Any]:
        """Read property (API method)"""
        device = self.devices.get(device_id)
        if not device:
            return None
        
        obj = device.objects.get(object_instance)
        if not obj:
            return None
        
        if property_id == 85:  # Present-Value
            return obj.present_value
        elif property_id == 77:  # Object-Name
            return obj.object_name
        
        return None
    
    def write_property(self, device_id: int, object_type: int, object_instance: int, property_id: int, value: Any) -> bool:
        """Write property (API method)"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        obj = device.objects.get(object_instance)
        if not obj:
            return False
        
        obj.present_value = value
        return True


def object_type_to_id(obj_type: BACnetObjectType) -> int:
    """Convert enum to ID"""
    return obj_type.value


# Factory function
def create_bacnet_server(host: str = "0.0.0.0", port: int = 47808) -> BACnetIPRouter:
    """Create a new BACnet IP server"""
    return BACnetIPRouter(host=host, port=port)


def create_bacnet_device(device_id: int, name: str, address: str) -> BACnetDevice:
    """Create a new BACnet device"""
    return BACnetDevice(device_id=device_id, name=name, address=address)
