"""
Event Bus - Redis/ZeroMQ Integration
Unified event messaging system
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import redis.asyncio as redis
import zmq.asyncio as zmq


class EventType(Enum):
    """Event Types"""
    DATA_CHANGE = "data_change"
    DEVICE_ONLINE = "device_online"
    DEVICE_OFFLINE = "device_offline"
    ALERT = "alert"
    METRIC = "metric"
    COMMAND = "command"
    STATUS = "status"
    PACKET = "packet"


@dataclass
class Event:
    """Event Message"""
    event_type: EventType
    source: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16])
    correlation_id: Optional[str] = None
    priority: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventBusBase:
    """Base Event Bus"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self._running = False
    
    def subscribe(self, event_type: EventType, callback: Callable, priority: int = 0):
        """Subscribe to event type"""
        key = f"{event_type.value}:{priority}"
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)
        
        # Sort by priority (higher first)
        self.subscribers[key].sort(key=lambda x: getattr(x, '__priority__', 0), reverse=True)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from event type"""
        for key in list(self.subscribers.keys()):
            if event_type.value in key:
                if callback in self.subscribers[key]:
                    self.subscribers[key].remove(callback)
    
    async def publish(self, event: Event):
        """Publish event"""
        raise NotImplementedError
    
    async def _notify_subscribers(self, event: Event):
        """Notify all subscribers"""
        for key, callbacks in self.subscribers.items():
            if event.event_type.value in key:
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Subscriber error: {e}")


class RedisEventBus(EventBusBase):
    """Redis-based Event Bus"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        super().__init__()
        self.host = host
        self.port = port
        self.db = db
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._running = False
    
    async def connect(self):
        """Connect to Redis"""
        self._redis = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {self.host}:{self.port}")
        
        # Test connection
        await self._redis.ping()
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("Disconnected from Redis")
    
    async def start(self):
        """Start event bus"""
        self._running = True
        
        # Subscribe to all channels
        if self._pubsub:
            await self._pubsub.subscribe(
                "iot:*",  # Wildcard pattern
                "events:*",
                "alerts:*"
            )
            
            # Start listener
            asyncio.create_task(self._listen_redis())
    
    def stop(self):
        """Stop event bus"""
        self._running = False
    
    async def _listen_redis(self):
        """Listen for Redis messages"""
        try:
            async for message in self._pubsub.listen():
                if not self._running:
                    break
                
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        event = Event(
                            event_type=EventType(data.get("type", "metric")),
                            source=data.get("source", ""),
                            data=data.get("data", {})
                        )
                        await self._notify_subscribers(event)
                    except Exception as e:
                        logger.error(f"Redis message error: {e}")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    async def publish(self, event: Event):
        """Publish event to Redis"""
        if not self._redis:
            return
        
        channel = f"iot:{event.event_type.value}"
        await self._redis.publish(channel, event.to_json())
        
        # Also store in list for persistence
        if event.priority > 0:
            await self._redis.lpush(f"events:{event.event_type.value}", event.to_json())
            # Keep last 1000 events
            await self._redis.ltrim(f"events:{event.event_type.value}", 0, 999)
    
    async def get_events(self, event_type: EventType, limit: int = 100) -> List[Event]:
        """Get recent events"""
        if not self._redis:
            return []
        
        data_list = await self._redis.lrange(f"events:{event_type.value}", 0, limit - 1)
        events = []
        for data_str in data_list:
            try:
                data = json.loads(data_str)
                events.append(Event(
                    event_type=EventType(data["type"]),
                    source=data["source"],
                    data=data["data"]
                ))
            except:
                pass
        
        return events


class ZMQEventBus(EventBusBase):
    """ZeroMQ-based Event Bus"""
    
    def __init__(self, host: str = "*", port: int = 5555):
        super().__init__()
        self.host = host
        self.port = port
        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._running = False
    
    async def connect(self):
        """Create ZMQ socket"""
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PUB)
        self._socket.bind(f"tcp://{self.host}:{self.port}")
        logger.info(f"ZMQ Event Bus bound to {self.host}:{self.port}")
    
    async def disconnect(self):
        """Close ZMQ socket"""
        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()
    
    def start(self):
        """Start event bus"""
        self._running = True
    
    def stop(self):
        """Stop event bus"""
        self._running = False
    
    def publish(self, event: Event):
        """Publish event via ZMQ"""
        if not self._socket:
            return
        
        message = event.to_json()
        try:
            self._socket.send_multipart([
                event.event_type.value.encode(),
                message.encode()
            ])
        except Exception as e:
            logger.error(f"ZMQ publish error: {e}")


class InMemoryEventBus(EventBusBase):
    """In-memory Event Bus (for testing)"""
    
    def __init__(self, max_history: int = 1000):
        super().__init__()
        self._events: List[Event] = []
        self.max_history = max_history
        self._queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self):
        """Start event bus"""
        self._running = True
    
    def stop(self):
        """Stop event bus"""
        self._running = False
    
    async def publish(self, event: Event):
        """Publish event"""
        # Add to history
        self._events.append(event)
        if len(self._events) > self.max_history:
            self._events = self._events[-self.max_history:]
        
        # Notify subscribers
        await self._notify_subscribers(event)
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get event history"""
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]
    
    def get_stats(self) -> dict:
        """Get statistics"""
        return {
            "total_events": len(self._events),
            "subscribers": sum(len(cb) for cb in self.subscribers.values()),
            "queue_size": self._queue.qsize() if hasattr(self._queue, 'qsize') else 0
        }


class EventRouter:
    """Event Router with pattern matching"""
    
    def __init__(self, event_bus: EventBusBase):
        self.event_bus = event_bus
        self._routing_rules: Dict[str, List[str]] = {}
    
    def add_route(self, pattern: str, destination: str):
        """Add routing rule"""
        if pattern not in self._routing_rules:
            self._routing_rules[pattern] = []
        self._routing_rules[pattern].append(destination)
    
    def remove_route(self, pattern: str, destination: str):
        """Remove routing rule"""
        if pattern in self._routing_rules:
            if destination in self._routing_rules[pattern]:
                self._routing_rules[pattern].remove(destination)
    
    async def route(self, event: Event):
        """Route event based on patterns"""
        for pattern, destinations in self._routing_rules.items():
            if self._matches(event, pattern):
                for dest in destinations:
                    logger.debug(f"Routing {event.event_type.value} -> {dest}")
                    # Forward to destination


# Factory functions
def create_redis_event_bus(host: str = "localhost", port: int = 6379) -> RedisEventBus:
    """Create Redis event bus"""
    return RedisEventBus(host=host, port=port)


def create_zmq_event_bus(host: str = "*", port: int = 5555) -> ZMQEventBus:
    """Create ZMQ event bus"""
    return ZMQEventBus(host=host, port=port)


def create_memory_event_bus(max_history: int = 1000) -> InMemoryEventBus:
    """Create in-memory event bus"""
    return InMemoryEventBus(max_history=max_history)
