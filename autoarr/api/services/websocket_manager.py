"""
WebSocket Manager - Real-time Event Broadcasting.

Manages WebSocket connections and broadcasts events from the event bus
to connected clients for real-time updates.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from autoarr.api.services.event_bus import Event, EventBus, get_event_bus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and event broadcasting.

    Subscribes to all events from the event bus and broadcasts them
    to all connected WebSocket clients.
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize WebSocket manager.

        Args:
            event_bus: Event bus instance (uses global if not provided)
        """
        self.event_bus = event_bus or get_event_bus()

        # Active WebSocket connections
        self._connections: Set[WebSocket] = set()

        # Subscribe to all events
        self.event_bus.subscribe_all(self._broadcast_event)

        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection to accept
        """
        await websocket.accept()
        self._connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self._connections)}")

        # Send welcome message
        await self._send_to_client(
            websocket,
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to AutoArr monitoring service",
            },
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        self._connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self._connections)}")

    async def _broadcast_event(self, event: Event) -> None:
        """
        Broadcast event to all connected clients.

        Args:
            event: Event to broadcast
        """
        if not self._connections:
            return

        # Convert event to WebSocket message
        message = {
            "type": "event",
            "data": event.to_dict(),
        }

        # Send to all clients (collect disconnected ones)
        disconnected = []

        for connection in self._connections:
            try:
                await self._send_to_client(connection, message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def _send_to_client(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """
        Send message to a specific client.

        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket client: {e}")
            raise

    async def send_status(self, status: Dict[str, Any]) -> None:
        """
        Broadcast status update to all clients.

        Args:
            status: Status information to broadcast
        """
        message = {
            "type": "status",
            "data": status,
        }

        for connection in list(self._connections):
            try:
                await self._send_to_client(connection, message)
            except Exception:
                self.disconnect(connection)

    def get_connection_count(self) -> int:
        """
        Get number of active connections.

        Returns:
            Number of active WebSocket connections
        """
        return len(self._connections)

    def get_status(self) -> Dict[str, Any]:
        """
        Get WebSocket manager status.

        Returns:
            Status information
        """
        return {
            "active_connections": len(self._connections),
        }


# ============================================================================
# Global WebSocket Manager Instance
# ============================================================================

_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.

    Returns:
        WebSocketManager: Global manager instance
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def reset_websocket_manager() -> None:
    """Reset the global WebSocket manager (for testing)."""
    global _websocket_manager
    _websocket_manager = None
