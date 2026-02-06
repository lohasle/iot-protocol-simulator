"""
Traffic Replayer
Record and replay network traffic
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger


class ReplayMode(Enum):
    """Replay Modes"""
    NORMAL = "normal"
    FAST = "fast"
    SLOW = "slow"
    LOOP = "loop"
    STEP = "step"


@dataclass
class RecordedPacket:
    """Recorded Packet"""
    id: str
    timestamp: datetime
    sequence: int
    source: str
    destination: str
    protocol: str
    payload: bytes
    metadata: Dict = field(default_factory=dict)


@dataclass
class RecordingSession:
    """Recording Session"""
    id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime]
    packets: List[RecordedPacket]
    protocols: List[str]
    statistics: Dict = field(default_factory=dict)


class TrafficRecorder:
    """Record Network Traffic"""
    
    def __init__(self):
        self.current_session: Optional[RecordingSession] = None
        self.sessions: Dict[str, RecordingSession] = {}
        self._recording = False
        self._sequence = 0
    
    def start_recording(self, name: str = None):
        """Start a new recording session"""
        session_id = hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        self.current_session = RecordingSession(
            id=session_id,
            name=name or f"Recording-{session_id}",
            start_time=datetime.utcnow(),
            end_time=None,
            packets=[],
            protocols=[],
            statistics={}
        )
        self._recording = True
        self._sequence = 0
        logger.info(f"Started recording session: {self.current_session.name}")
    
    def stop_recording(self):
        """Stop current recording session"""
        if self.current_session:
            self.current_session.end_time = datetime.utcnow()
            self.current_session.statistics = self._calculate_stats()
            self.sessions[self.current_session.id] = self.current_session
            
            count = len(self.current_session.packets)
            logger.info(f"Stopped recording: {count} packets recorded")
            
            self.current_session = None
        
        self._recording = False
    
    def record_packet(
        self,
        source: str,
        destination: str,
        protocol: str,
        payload: bytes,
        metadata: Dict = None
    ):
        """Record a packet"""
        if not self._recording or not self.current_session:
            return
        
        self._sequence += 1
        
        packet = RecordedPacket(
            id=f"rec-{self._sequence:08x}",
            timestamp=datetime.utcnow(),
            sequence=self._sequence,
            source=source,
            destination=destination,
            protocol=protocol,
            payload=payload,
            metadata=metadata or {}
        )
        
        self.current_session.packets.append(packet)
        
        # Track protocols
        if protocol not in self.current_session.protocols:
            self.current_session.protocols.append(protocol)
    
    def _calculate_stats(self) -> dict:
        """Calculate session statistics"""
        if not self.current_session:
            return {}
        
        packets = self.current_session.packets
        if not packets:
            return {}
        
        return {
            "total_packets": len(packets),
            "total_bytes": sum(len(p.payload) for p in packets),
            "duration_seconds": (packets[-1].timestamp - packets[0].timestamp).total_seconds(),
            "packets_per_second": len(packets) / max(1, (packets[-1].timestamp - packets[0].timestamp).total_seconds()),
            "protocols": list(set(p.protocol for p in packets)),
            "sources": list(set(p.source for p in packets)),
            "destinations": list(set(p.destination for p in packets))
        }
    
    def get_sessions(self) -> List[dict]:
        """Get all recording sessions"""
        return [
            {
                "id": s.id,
                "name": s.name,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "packet_count": len(s.packets),
                "protocols": s.protocols,
                "statistics": s.statistics
            }
            for s in self.sessions.values()
        ]
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get specific session"""
        session = self.sessions.get(session_id)
        if session:
            return {
                "id": session.id,
                "name": session.name,
                "packets": [self._packet_to_dict(p) for p in session.packets],
                "statistics": session.statistics
            }
        return None
    
    def _packet_to_dict(self, packet: RecordedPacket) -> dict:
        """Convert packet to dictionary"""
        return {
            "id": packet.id,
            "timestamp": packet.timestamp.isoformat(),
            "sequence": packet.sequence,
            "source": packet.source,
            "destination": packet.destination,
            "protocol": packet.protocol,
            "length": len(packet.payload),
            "hex": packet.payload.hex() if packet.payload else None
        }
    
    def delete_session(self, session_id: str):
        """Delete a recording session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def export_session(self, session_id: str, format: str = "json") -> str:
        """Export session"""
        session = self.sessions.get(session_id)
        if not session:
            return json.dumps({"error": "Session not found"})
        
        data = {
            "id": session.id,
            "name": session.name,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "packets": [self._packet_to_dict(p) for p in session.packets],
            "statistics": session.statistics
        }
        
        if format == "json":
            return json.dumps(data, indent=2)
        
        return json.dumps(data)


class TrafficReplayer:
    """Replay Recorded Traffic"""
    
    def __init__(self, recorder: TrafficRecorder = None):
        self.recorder = recorder or TrafficRecorder()
        self._replaying = False
        self._current_packet = 0
        self._replay_session: Optional[RecordingSession] = None
        self._task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_packet: Optional[callable] = None
        self.on_complete: Optional[callable] = None
    
    def load_session(self, session_id: str) -> bool:
        """Load session for replay"""
        session = self.recorder.sessions.get(session_id)
        if session:
            self._replay_session = session
            return True
        return False
    
    def start_replay(
        self,
        mode: ReplayMode = ReplayMode.NORMAL,
        speed: float = 1.0,
        loop: bool = False
    ):
        """Start replaying traffic"""
        if not self._replay_session:
            logger.error("No session loaded")
            return
        
        self._replaying = True
        self._current_packet = 0
        self._task = asyncio.create_task(
            self._replay_loop(mode, speed, loop)
        )
        logger.info(f"Started replay: {self._replay_session.name}")
    
    def stop_replay(self):
        """Stop replaying"""
        self._replaying = False
        if self._task:
            self._task.cancel()
        logger.info("Replay stopped")
    
    def pause_replay(self):
        """Pause replay"""
        self._replaying = False
    
    def resume_replay(self, mode: ReplayMode = ReplayMode.NORMAL, speed: float = 1.0):
        """Resume replay"""
        if self._replay_session and self._current_packet < len(self._replay_session.packets):
            self._replaying = True
            self._task = asyncio.create_task(
                self._replay_loop(mode, speed, False)
            )
    
    async def _replay_loop(
        self,
        mode: ReplayMode,
        speed: float,
        loop: bool
    ):
        """Replay loop"""
        packets = self._replay_session.packets
        
        while self._replaying and self._current_packet < len(packets):
            packet = packets[self._current_packet]
            
            # Calculate delay
            if self._current_packet > 0:
                prev_time = packets[self._current_packet - 1].timestamp
                delay = (packet.timestamp - prev_time).total_seconds() / speed
            
            # Handle mode
            if mode == ReplayMode.SLOW:
                await asyncio.sleep(delay * 2)
            elif mode == ReplayMode.FAST:
                await asyncio.sleep(delay * 0.5)
            elif mode == ReplayMode.NORMAL:
                await asyncio.sleep(delay)
            
            # Send packet
            if self.on_packet:
                await self.on_packet(packet)
            
            self._current_packet += 1
        
        # Check for loop
        if loop and self._replaying:
            self._current_packet = 0
            await self._replay_loop(mode, speed, loop)
        else:
            self._replaying = False
            if self.on_complete:
                await self.on_complete()
    
    def get_replay_status(self) -> dict:
        """Get replay status"""
        total = len(self._replay_session.packets) if self._replay_session else 0
        return {
            "replaying": self._replaying,
            "session_name": self._replay_session.name if self._replay_session else None,
            "current_packet": self._current_packet,
            "total_packets": total,
            "progress": self._current_packet / total * 100 if total > 0 else 0
        }


# Factory functions
def create_traffic_recorder() -> TrafficRecorder:
    """Create traffic recorder"""
    return TrafficRecorder()


def create_traffic_replayer(recorder: TrafficRecorder = None) -> TrafficReplayer:
    """Create traffic replayer"""
    return TrafficReplayer(recorder)
