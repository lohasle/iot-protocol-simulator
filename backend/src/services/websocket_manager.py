"""
WebSocket connection manager for real-time communication
"""

from typing import Set
from loguru import logger
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: dict[str, Set[WebSocket]] = {
            "metrics": set(),
            "packets": set(),
            "alerts": set(),
            "devices": set(),
        }
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for subscribers in self.subscriptions.values():
            subscribers.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_message(self, message: str, websocket: WebSocket):
        """Send message to single connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast(self, message: str, channel: Optional[str] = None):
        """Broadcast message to all connections or channel subscribers"""
        if channel and channel in self.subscriptions:
            targets = self.subscriptions[channel]
        else:
            targets = self.active_connections
        
        for connection in targets:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")
    
    async def handle_message(self, websocket: WebSocket, data: str) -> Optional[str]:
        """Handle incoming WebSocket message"""
        try:
            import json
            message = json.loads(data)
            
            if message["type"] == "subscribe":
                channels = message.get("channels", [])
                for channel in channels:
                    if channel in self.subscriptions:
                        self.subscriptions[channel].add(websocket)
                logger.info(f"Subscribed to channels: {channels}")
                return json.dumps({"type": "subscribed", "channels": channels})
            
            elif message["type"] == "unsubscribe":
                channels = message.get("channels", [])
                for channel in channels:
                    if channel in self.subscriptions:
                        self.subscriptions[channel].discard(websocket)
                return json.dumps({"type": "unsubscribed", "channels": channels})
            
            elif message["type"] == "ping":
                return json.dumps({"type": "pong"})
            
            else:
                logger.info(f"Unknown message type: {message['type']}")
                return None
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message")
            return json.dumps({"type": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            return json.dumps({"type": "error", "message": str(e)})
    
    async def start(self):
        """Start the connection manager"""
        logger.info("WebSocket connection manager started")
    
    async def stop(self):
        """Stop and cleanup connections"""
        for connection in list(self.active_connections):
            await connection.close()
        self.active_connections.clear()
        logger.info("WebSocket connection manager stopped")


# Global connection manager instance
ws_manager = ConnectionManager()
