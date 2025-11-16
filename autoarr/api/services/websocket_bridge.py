# Copyright (C) 2025 AutoArr Contributors
#
# This file is part of AutoArr.
#
# AutoArr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AutoArr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
WebSocket Event Bus Bridge Service.

This service bridges the event bus with WebSocket connections, enabling
real-time event delivery to connected clients.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Set

from .event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class WebSocketBridge:
    """
    Bridges event bus events to WebSocket connections.

    Subscribes to event bus topics and broadcasts events to WebSocket clients
    with support for filtering by correlation ID and event type.
    """

    def __init__(self, event_bus: EventBus, connection_manager: Any):
        """
        Initialize WebSocket bridge.

        Args:
            event_bus: Event bus instance to subscribe to
            connection_manager: WebSocket connection manager for broadcasting
        """
        self.event_bus = event_bus
        self.connection_manager = connection_manager
        self.subscribed_topics: Set[str] = set()
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """
        Start the WebSocket bridge.

        Subscribes to all relevant event bus topics and begins
        forwarding events to WebSocket clients.
        """
        if self._running:
            logger.warning("WebSocket bridge already running")
            return

        logger.info("Starting WebSocket event bridge...")
        self._running = True

        # Subscribe to all important event types
        topics = [
            "config.audit.started",
            "config.audit.completed",
            "config.audit.failed",
            "download.failed",
            "download.retry.started",
            "download.retry.succeeded",
            "download.retry.failed",
            "content.request.created",
            "content.request.classified",
            "content.request.added",
            "content.request.completed",
            "content.request.failed",
            "activity.created",
        ]

        for topic in topics:
            await self.event_bus.subscribe(topic, self._handle_event)
            self.subscribed_topics.add(topic)
            logger.debug(f"Subscribed to event topic: {topic}")

        logger.info(f"WebSocket bridge started, monitoring {len(topics)} event types")

    async def stop(self) -> None:
        """
        Stop the WebSocket bridge.

        Unsubscribes from all event bus topics and cancels pending tasks.
        """
        if not self._running:
            return

        logger.info("Stopping WebSocket event bridge...")
        self._running = False

        # Unsubscribe from all topics
        for topic in self.subscribed_topics:
            try:
                await self.event_bus.unsubscribe(topic, self._handle_event)
            except Exception as e:
                logger.error(f"Error unsubscribing from {topic}: {e}")

        self.subscribed_topics.clear()

        # Cancel all pending tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("WebSocket bridge stopped")

    async def _handle_event(self, event: Event) -> None:
        """
        Handle an event from the event bus.

        Transforms the event into a WebSocket-friendly format and broadcasts
        it to all connected clients.

        Args:
            event: Event from the event bus
        """
        if not self._running:
            return

        try:
            # Transform event to WebSocket message format
            message = self._event_to_websocket_message(event)

            # Broadcast to all connected clients
            await self.connection_manager.broadcast(message)

            logger.debug(
                f"Broadcasted event {event.event_type} "
                f"(correlation_id: {event.correlation_id})"
            )

        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}", exc_info=True)

    def _event_to_websocket_message(self, event: Event) -> Dict[str, Any]:
        """
        Transform an event bus event into a WebSocket message.

        Args:
            event: Event from the event bus

        Returns:
            WebSocket message dictionary
        """
        return {
            "type": "event",
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data,
            "metadata": {
                "source": event.source,
                "user_id": event.user_id,
            },
        }

    async def broadcast_custom_message(
        self, message_type: str, data: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> None:
        """
        Broadcast a custom message to all WebSocket clients.

        Useful for system messages or notifications that don't originate
        from the event bus.

        Args:
            message_type: Type of message
            data: Message data
            correlation_id: Optional correlation ID for tracking
        """
        message = {
            "type": message_type,
            "correlation_id": correlation_id,
            "data": data,
        }

        await self.connection_manager.broadcast(message)
        logger.debug(f"Broadcasted custom message: {message_type}")


# Global bridge instance (initialized on startup)
_bridge_instance: Optional[WebSocketBridge] = None


def get_websocket_bridge() -> Optional[WebSocketBridge]:
    """
    Get the global WebSocket bridge instance.

    Returns:
        WebSocket bridge instance or None if not initialized
    """
    return _bridge_instance


def set_websocket_bridge(bridge: WebSocketBridge) -> None:
    """
    Set the global WebSocket bridge instance.

    Args:
        bridge: WebSocket bridge instance
    """
    global _bridge_instance
    _bridge_instance = bridge


async def initialize_websocket_bridge(
    event_bus: EventBus, connection_manager: Any
) -> WebSocketBridge:
    """
    Initialize and start the WebSocket bridge.

    Args:
        event_bus: Event bus instance
        connection_manager: WebSocket connection manager

    Returns:
        Initialized and started WebSocket bridge
    """
    bridge = WebSocketBridge(event_bus, connection_manager)
    await bridge.start()
    set_websocket_bridge(bridge)
    logger.info("WebSocket bridge initialized and started")
    return bridge


async def shutdown_websocket_bridge() -> None:
    """Shutdown the WebSocket bridge."""
    bridge = get_websocket_bridge()
    if bridge:
        await bridge.stop()
        set_websocket_bridge(None)
        logger.info("WebSocket bridge shutdown complete")
