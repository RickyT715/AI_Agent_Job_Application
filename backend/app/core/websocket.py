"""WebSocket connection manager for real-time agent status updates."""

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        self._active_connections: list[WebSocket] = []

    @property
    def active_count(self) -> int:
        """Number of active connections."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active: {self.active_count}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Active: {self.active_count}")

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected clients."""
        text = json.dumps(message)
        disconnected: list[WebSocket] = []

        for connection in self._active_connections:
            try:
                await connection.send_text(text)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send a JSON message to a specific client."""
        await websocket.send_text(json.dumps(message))


# Singleton instance
manager = ConnectionManager()
