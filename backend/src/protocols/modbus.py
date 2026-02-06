"""
Modbus TCP/RTU Protocol Simulator
Complete implementation of Modbus protocol stack
"""

import asyncio
import struct
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import random


class ModbusFunctionCode(Enum):
    """Modbus Function Codes"""
    # Read Functions
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    
    # Write Single Functions
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    
    # Write Multiple Functions
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10
    
    # Diagnostics
    DIAGNOSTICS = 0x08
    
    # Other
    REPORT_SLAVE_ID = 0x11
    READ_FILE_RECORD = 0x14
    WRITE_FILE_RECORD = 0x15
    MASK_WRITE_REGISTER = 0x16
    READ_WRITE_MULTIPLE = 0x17
    READ_FIFO_QUEUE = 0x18


class ModbusException(Exception):
    """Modbus Exception"""
    def __init__(self, function_code: int, exception_code: int):
        self.function_code = function_code
        self.exception_code = exception_code
        self.message = self._get_exception_message()
        super().__init__(self.message)
    
    def _get_exception_message(self) -> str:
        messages = {
            0x01: "Illegal Function",
            0x02: "Illegal Data Address",
            0x03: "Illegal Data Value",
            0x04: "Slave Device Failure",
            0x05: "Acknowledge",
            0x06: "Slave Device Busy",
            0x07: "Negative Acknowledge",
            0x08: "Memory Parity Error",
            0x0A: "Gateway Path Unavailable",
            0x0B: "Gateway Target Failed",
        }
        return messages.get(self.exception_code, f"Unknown Exception {self.exception_code}")


@dataclass
class ModbusDevice:
    """Simulated Modbus Device"""
    unit_id: int
    name: str
    coils: Dict[int, bool] = field(default_factory=dict)
    discrete_inputs: Dict[int, bool] = field(default_factory=dict)
    holding_registers: Dict[int, int] = field(default_factory=dict)
    input_registers: Dict[int, int] = field(default_factory=dict)
    
    def __post_init__(self):
        # Initialize with some default values
        for i in range(100):
            self.holding_registers[i] = random.randint(0, 65535)
            self.input_registers[i] = random.randint(0, 65535)
            self.coils[i] = random.choice([True, False])
            self.discrete_inputs[i] = random.choice([True, False])


class ModbusTCPServer:
    """Modbus TCP Server Simulator"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 502):
        self.host = host
        self.port = port
        self.devices: Dict[int, ModbusDevice] = {}
        self.running = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._transaction_id = 0
        self.on_packet: Optional[Callable] = None
        self.on_data_change: Optional[Callable] = None
    
    def add_device(self, device: ModbusDevice):
        """Add a simulated device"""
        self.devices[device.unit_id] = device
        logger.info(f"Added Modbus device: {device.name} (ID: {device.unit_id})")
    
    async def start(self):
        """Start the Modbus TCP server"""
        self.running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(f"Modbus TCP server started on {self.host}:{self.port}")
        
        async with self._server:
            await self._server.serve_forever()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self._server:
            self._server.close()
        logger.info("Modbus TCP server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection"""
        addr = writer.get_extra_info('peername')
        logger.debug(f"New Modbus client connection from {addr}")
        
        try:
            while self.running:
                try:
                    # Read MBAP header (7 bytes)
                    header = await reader.read(7)
                    if not header:
                        break
                    
                    # Parse MBAP
                    transaction_id = struct.unpack(">H", header[0:2])[0]
                    protocol_id = struct.unpack(">H", header[2:4])[0]
                    length = struct.unpack(">H", header[4:6])[0]
                    unit_id = header[6]
                    
                    # Read PDU
                    pdu_length = length - 1
                    pdu = await reader.read(pdu_length)
                    
                    # Process request
                    response = await self._process_request(unit_id, pdu)
                    
                    # Send response
                    if response:
                        response_pdu = response
                        response_length = len(response_pdu) + 1
                        response_header = struct.pack(
                            ">HHHB",
                            transaction_id,
                            protocol_id,
                            response_length,
                            unit_id
                        )
                        writer.write(response_header + response_pdu)
                        await writer.drain()
                        
                except Exception as e:
                    logger.error(f"Error handling client: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _process_request(self, unit_id: int, pdu: bytes) -> Optional[bytes]:
        """Process Modbus request and generate response"""
        if not pdu:
            return None
        
        function_code = pdu[0]
        
        # Get device
        device = self.devices.get(unit_id)
        if not device:
            # Return exception for unknown device
            return bytes([0x80 | function_code, 0x0B])
        
        try:
            if function_code == ModbusFunctionCode.READ_COILS.value:
                return self._read_coils(device, pdu)
            elif function_code == ModbusFunctionCode.READ_DISCRETE_INPUTS.value:
                return self._read_discrete_inputs(device, pdu)
            elif function_code == ModbusFunctionCode.READ_HOLDING_REGISTERS.value:
                return self._read_holding_registers(device, pdu)
            elif function_code == ModbusFunctionCode.READ_INPUT_REGISTERS.value:
                return self._read_input_registers(device, pdu)
            elif function_code == ModbusFunctionCode.WRITE_SINGLE_COIL.value:
                return self._write_single_coil(device, pdu)
            elif function_code == ModbusFunctionCode.WRITE_SINGLE_REGISTER.value:
                return self._write_single_register(device, pdu)
            elif function_code == ModbusFunctionCode.WRITE_MULTIPLE_COILS.value:
                return self._write_multiple_coils(device, pdu)
            elif function_code == ModbusFunctionCode.WRITE_MULTIPLE_REGISTERS.value:
                return self._write_multiple_registers(device, pdu)
            elif function_code == ModbusFunctionCode.DIAGNOSTICS.value:
                return self._diagnostics(device, pdu)
            else:
                return bytes([0x80 | function_code, 0x01])
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return bytes([0x80 | function_code, 0x04])
    
    def _read_coils(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Read Coils (FC01)"""
        start_addr, quantity = struct.unpack(">HH", pdu[1:5])
        byte_count = (quantity + 7) // 8
        
        coils = []
        for i in range(start_addr, start_addr + quantity):
            coils.append(device.coils.get(i, False))
        
        # Pack into bytes
        response = bytearray([0x01, byte_count])
        for i in range(byte_count):
            byte_val = 0
            for bit in range(8):
                idx = i * 8 + bit
                if idx < len(coils) and coils[idx]:
                    byte_val |= (1 << bit)
            response.append(byte_val)
        
        return bytes(response)
    
    def _read_discrete_inputs(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Read Discrete Inputs (FC02)"""
        start_addr, quantity = struct.unpack(">HH", pdu[1:5])
        byte_count = (quantity + 7) // 8
        
        response = bytearray([0x02, byte_count])
        for i in range(byte_count):
            byte_val = 0
            for bit in range(8):
                idx = i * 8 + bit
                if device.discrete_inputs.get(start_addr + idx, False):
                    byte_val |= (1 << bit)
            response.append(byte_val)
        
        return bytes(response)
    
    def _read_holding_registers(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Read Holding Registers (FC03)"""
        start_addr, quantity = struct.unpack(">HH", pdu[1:5])
        byte_count = quantity * 2
        
        response = bytearray([0x03, byte_count])
        for i in range(start_addr, start_addr + quantity):
            value = device.holding_registers.get(i, 0)
            response.extend(struct.pack(">H", value))
        
        return bytes(response)
    
    def _read_input_registers(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Read Input Registers (FC04)"""
        start_addr, quantity = struct.unpack(">HH", pdu[1:5])
        byte_count = quantity * 2
        
        response = bytearray([0x04, byte_count])
        for i in range(start_addr, start_addr + quantity):
            value = device.input_registers.get(i, 0)
            response.extend(struct.pack(">H", value))
        
        return bytes(response)
    
    def _write_single_coil(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Write Single Coil (FC05)"""
        addr, value = struct.unpack(">HH", pdu[1:5])
        coil_value = value == 0xFF00
        
        device.coils[addr] = coil_value
        
        if self.on_data_change:
            self.on_data_change({
                "device": device.name,
                "type": "coil",
                "address": addr,
                "value": coil_value,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return pdu  # Echo back
    
    def _write_single_register(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Write Single Register (FC06)"""
        addr, value = struct.unpack(">HH", pdu[1:5])
        
        device.holding_registers[addr] = value
        
        if self.on_data_change:
            self.on_data_change({
                "device": device.name,
                "type": "register",
                "address": addr,
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return pdu  # Echo back
    
    def _write_multiple_coils(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Write Multiple Coils (FC15)"""
        start_addr = struct.unpack(">H", pdu[1:3])[0]
        quantity = struct.unpack(">H", pdu[3:5])[0]
        byte_count = pdu[5]
        
        for i in range(quantity):
            byte_idx = 5 + 1 + i // 8
            bit_idx = i % 8
            if pdu[byte_idx] & (1 << bit_idx):
                device.coils[start_addr + i] = True
            else:
                device.coils[start_addr + i] = False
        
        return pdu[:5]  # Return function code, start addr, quantity
    
    def _write_multiple_registers(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Write Multiple Registers (FC16)"""
        start_addr = struct.unpack(">H", pdu[1:3])[0]
        quantity = struct.unpack(">H", pdu[3:5])[0]
        
        for i in range(quantity):
            addr = start_addr + i
            value = struct.unpack(">H", pdu[6 + i * 2:8 + i * 2])[0]
            device.holding_registers[addr] = value
        
        return pdu[:5]  # Return function code, start addr, quantity
    
    def _diagnostics(self, device: ModbusDevice, pdu: bytes) -> bytes:
        """Diagnostics (FC08)"""
        sub_func = struct.unpack(">H", pdu[1:3])[0]
        data = pdu[3:]
        
        # Return echo for sub-function 00 (Echo)
        if sub_func == 0x0000:
            return bytes([0x08, 0x00, 0x00, 0x00]) + data
        
        return bytes([0x08, 0x00, 0x00, 0x00])


class ModbusRTUServer:
    """Modbus RTU Server Simulator"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.devices: Dict[int, ModbusDevice] = {}
        self.running = False
    
    def add_device(self, device: ModbusDevice):
        """Add a simulated device"""
        self.devices[device.unit_id] = device
    
    async def start(self):
        """Start RTU simulation"""
        self.running = True
        logger.info(f"Modbus RTU simulator started on {self.port} @ {self.baudrate}bps")
    
    def stop(self):
        """Stop the simulator"""
        self.running = False


class ModbusClient:
    """Modbus TCP Client Simulator"""
    
    def __init__(self, host: str = "localhost", port: int = 502):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.transaction_id = 0
    
    async def connect(self):
        """Connect to Modbus server"""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logger.info(f"Connected to Modbus server at {self.host}:{self.port}")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
    
    async def read_holding_registers(self, unit_id: int, start_addr: int, quantity: int) -> List[int]:
        """Read Holding Registers (FC03)"""
        self.transaction_id += 1
        
        # Build request
        pdu = bytes([
            0x03,  # Function code
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (quantity >> 8) & 0xFF,
            quantity & 0xFF
        ])
        
        response = await self._send_request(unit_id, pdu)
        
        # Parse response
        byte_count = response[1]
        values = []
        for i in range(byte_count // 2):
            value = struct.unpack(">H", response[2 + i * 2:4 + i * 2])[0]
            values.append(value)
        
        return values
    
    async def write_single_register(self, unit_id: int, addr: int, value: int):
        """Write Single Register (FC06)"""
        self.transaction_id += 1
        
        pdu = bytes([
            0x06,  # Function code
            (addr >> 8) & 0xFF,
            addr & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF
        ])
        
        response = await self._send_request(unit_id, pdu)
        return response
    
    async def _send_request(self, unit_id: int, pdu: bytes) -> bytes:
        """Send request and receive response"""
        transaction_id = self.transaction_id
        
        # Build MBAP
        length = len(pdu) + 1
        mbap = struct.pack(">HHHB", transaction_id, 0, length, unit_id)
        
        # Send
        self.writer.write(mbap + pdu)
        await self.writer.drain()
        
        # Receive header
        header = await self.reader.read(7)
        _, _, resp_length, _ = struct.unpack(">HHHB", header)
        
        # Receive PDU
        response = await self.reader.read(resp_length - 1)
        
        return response


class ModbusDataGenerator:
    """Generate realistic Modbus data"""
    
    def __init__(self, device: ModbusDevice, update_interval: float = 1.0):
        self.device = device
        self.update_interval = update_interval
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    def start(self):
        """Start data generation"""
        self.running = True
        self._task = asyncio.create_task(self._generate_loop())
    
    def stop(self):
        """Stop data generation"""
        self.running = False
        if self._task:
            self._task.cancel()
    
    async def _generate_loop(self):
        """Generate data periodically"""
        while self.running:
            try:
                # Update registers with realistic values
                for addr in list(self.device.holding_registers.keys())[:10]:
                    # Simulate temperature (0-100°C)
                    if addr < 4:
                        self.device.holding_registers[addr] = int(
                            20 + random.gauss(0, 5) + 10 * random.random()
                        )
                    # Simulate pressure (0-10 bar)
                    elif addr < 8:
                        self.device.holding_registers[addr] = int(
                            random.uniform(0, 10) * 100
                        )
                    # Simulate flow rate (0-100 m³/h)
                    else:
                        self.device.holding_registers[addr] = int(
                            random.uniform(0, 100) * 10
                        )
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break


# Factory functions
def create_modbus_device(
    unit_id: int,
    name: str,
    num_registers: int = 100,
    num_coils: int = 100
) -> ModbusDevice:
    """Create a new Modbus device"""
    return ModbusDevice(
        unit_id=unit_id,
        name=name,
        holding_registers={i: random.randint(0, 65535) for i in range(num_registers)},
        input_registers={i: random.randint(0, 65535) for i in range(num_registers)},
        coils={i: random.choice([True, False]) for i in range(num_coils)},
        discrete_inputs={i: random.choice([True, False]) for i in range(num_coils)}
    )


def create_modbus_server(host: str = "0.0.0.0", port: int = 502) -> ModbusTCPServer:
    """Create a new Modbus TCP server"""
    return ModbusTCPServer(host=host, port=port)
