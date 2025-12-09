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
from typing import Any, Dict, List, Optional

from .event_bus import Event, EventBus, EventSubscription, EventType

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
        self._subscriptions: List[EventSubscription] = []
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
        event_types = [
            EventType.CONFIG_AUDIT_STARTED,
            EventType.CONFIG_AUDIT_COMPLETED,
            EventType.CONFIG_AUDIT_FAILED,
            EventType.DOWNLOAD_STARTED,
            EventType.DOWNLOAD_COMPLETED,
            EventType.DOWNLOAD_FAILED,
            EventType.DOWNLOAD_PAUSED,
            EventType.DOWNLOAD_RESUMED,
            EventType.DOWNLOAD_STATE_CHANGED,
            EventType.RECOVERY_ATTEMPTED,
            EventType.RECOVERY_SUCCESS,
            EventType.RECOVERY_FAILED,
            EventType.CONTENT_REQUESTED,
            EventType.CONTENT_ADDED,
            EventType.CONTENT_REQUEST_FAILED,
            EventType.REQUEST_CREATED,
            EventType.REQUEST_PROCESSED,
            EventType.REQUEST_FAILED,
        ]

        for event_type in event_types:
            subscription = self.event_bus.subscribe(event_type, self._handle_event_sync)
            self._subscriptions.append(subscription)
            logger.debug(f"Subscribed to event type: {event_type}")

        logger.info(f"WebSocket bridge started, monitoring {len(event_types)} event types")

    async def stop(self) -> None:
        """
        Stop the WebSocket bridge.

        Unsubscribes from all event bus topics and cancels pending tasks.
        """
        if not self._running:
            return

        logger.info("Stopping WebSocket event bridge...")
        self._running = False

        # Unsubscribe from all event types
        for subscription in self._subscriptions:
            try:
                self.event_bus.unsubscribe(subscription)
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")

        self._subscriptions.clear()

        # Cancel all pending tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("WebSocket bridge stopped")

    def _handle_event_sync(self, event: Event) -> None:
        """
        Sync wrapper for handling events from the event bus.

        Creates an async task to handle the event without blocking.

        Args:
            event: Event from the event bus
        """
        if not self._running:
            return

        # Schedule the async handler as a task
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._handle_event_async(event))
            self._tasks.append(task)
            # Clean up completed tasks
            self._tasks = [t for t in self._tasks if not t.done()]
        except RuntimeError:
            # No running event loop - this shouldn't happen in normal operation
            logger.warning("No running event loop for WebSocket bridge event handling")

    async def _handle_event_async(self, event: Event) -> None:
        """
        Handle an event from the event bus asynchronously.

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
                f"Broadcasted event {event.event_type} (correlation_id: {event.correlation_id})"
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


def set_websocket_bridge(bridge: Optional[WebSocketBridge]) -> None:
    """
    Set the global WebSocket bridge instance.

    Args:
        bridge: WebSocket bridge instance (or None to clear)
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
