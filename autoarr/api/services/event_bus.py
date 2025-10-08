"""
Event Bus - Central event-driven architecture backbone.

This module provides a robust in-memory event bus with pub/sub pattern,
enabling decoupled communication between services. Supports event correlation,
history tracking, and multiple subscriber patterns.
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standardized event types emitted by the system."""

    # Download monitoring events
    DOWNLOAD_FAILED = "download.failed"
    DOWNLOAD_RECOVERED = "download.recovered"
    DOWNLOAD_RETRY_STARTED = "download.retry_started"
    DOWNLOAD_RETRY_FAILED = "download.retry_failed"
    DOWNLOAD_MOVED_TO_DLQ = "download.moved_to_dlq"

    # Queue monitoring events
    QUEUE_POLLED = "queue.polled"
    QUEUE_STATE_CHANGED = "queue.state_changed"

    # Wanted list events
    WANTED_ITEM_DETECTED = "wanted.item_detected"
    WANTED_ITEM_RESOLVED = "wanted.item_resolved"

    # Configuration events
    CONFIG_APPLIED = "config.applied"
    CONFIG_VALIDATION_FAILED = "config.validation_failed"

    # Audit events
    AUDIT_STARTED = "audit.started"
    AUDIT_COMPLETED = "audit.completed"
    AUDIT_FAILED = "audit.failed"

    # System events
    MONITORING_STARTED = "monitoring.started"
    MONITORING_STOPPED = "monitoring.stopped"
    SERVICE_ERROR = "service.error"


@dataclass
class Event:
    """
    Event data structure with metadata.

    All events include correlation IDs for tracking flows across services,
    timestamps for ordering, and flexible payload for event-specific data.
    """

    event_type: EventType
    payload: Dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    causation_id: Optional[str] = None  # ID of event that caused this event
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """String representation for logging."""
        return (
            f"Event(type={self.event_type.value}, "
            f"correlation_id={self.correlation_id[:8]}..., "
            f"payload_keys={list(self.payload.keys())})"
        )


class EventBus:
    """
    In-memory event bus with pub/sub pattern.

    Features:
    - Async event emission and handling
    - Multiple subscribers per event type
    - Event history for debugging
    - Correlation ID tracking for distributed tracing
    - Error isolation (one subscriber failure doesn't affect others)
    - Wildcard subscriptions
    """

    def __init__(self, max_history_size: int = 1000):
        """
        Initialize event bus.

        Args:
            max_history_size: Maximum number of events to keep in history
        """
        self.max_history_size = max_history_size

        # Subscribers: event_type -> set of async callbacks
        self._subscribers: Dict[str, Set[Callable]] = defaultdict(set)

        # Event history for debugging and replay
        self._event_history: List[Event] = []

        # Correlation tracking: correlation_id -> list of events
        self._correlation_tracker: Dict[str, List[Event]] = defaultdict(list)

        # Statistics
        self._stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "subscriber_errors": 0,
        }

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        logger.info("EventBus initialized")

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], Any],
    ) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event is emitted
                     Signature: async def callback(event: Event) -> None
        """
        self._subscribers[event_type.value].add(callback)
        logger.info(f"Subscribed to {event_type.value}: {callback.__name__}")

    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], Any],
    ) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if callback in self._subscribers[event_type.value]:
            self._subscribers[event_type.value].remove(callback)
            logger.info(f"Unsubscribed from {event_type.value}: {callback.__name__}")

    def subscribe_all(self, callback: Callable[[Event], Any]) -> None:
        """
        Subscribe to all event types (wildcard subscription).

        Args:
            callback: Async function to call for any event
        """
        self._subscribers["*"].add(callback)
        logger.info(f"Subscribed to ALL events: {callback.__name__}")

    async def emit(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Emit an event to all subscribers.

        Args:
            event_type: Type of event
            payload: Event data
            correlation_id: Optional correlation ID (generated if not provided)
            causation_id: Optional ID of event that caused this one
            metadata: Optional additional metadata

        Returns:
            The emitted Event object
        """
        # Create event
        event = Event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id or str(uuid.uuid4()),
            causation_id=causation_id,
            metadata=metadata or {},
        )

        # Add to history
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self.max_history_size:
                self._event_history.pop(0)

            # Track correlation
            self._correlation_tracker[event.correlation_id].append(event)

            # Update stats
            self._stats["total_events"] += 1
            self._stats["events_by_type"][event_type.value] += 1

        logger.debug(f"Emitting event: {event}")

        # Get subscribers for this event type and wildcard subscribers
        subscribers = set(self._subscribers[event_type.value])
        subscribers.update(self._subscribers.get("*", set()))

        # Notify all subscribers (async and error-isolated)
        tasks = []
        for callback in subscribers:
            tasks.append(self._safe_callback(callback, event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return event

    async def _safe_callback(self, callback: Callable, event: Event) -> None:
        """
        Execute callback with error handling.

        Args:
            callback: Function to call
            event: Event to pass to callback
        """
        try:
            result = callback(event)
            # Handle both sync and async callbacks
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            self._stats["subscriber_errors"] += 1
            logger.error(
                f"Error in event subscriber {callback.__name__} "
                f"for event {event.event_type.value}: {e}",
                exc_info=True,
            )

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type (None for all)
            correlation_id: Filter by correlation ID
            limit: Maximum number of events to return

        Returns:
            List of events, most recent first
        """
        if correlation_id:
            events = self._correlation_tracker.get(correlation_id, [])
        else:
            events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return list(reversed(events[-limit:]))

    def get_correlated_events(self, correlation_id: str) -> List[Event]:
        """
        Get all events for a specific correlation ID.

        Args:
            correlation_id: Correlation ID to search for

        Returns:
            List of events with this correlation ID, in chronological order
        """
        return self._correlation_tracker.get(correlation_id, [])

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary containing stats
        """
        return {
            "total_events": self._stats["total_events"],
            "events_by_type": dict(self._stats["events_by_type"]),
            "subscriber_errors": self._stats["subscriber_errors"],
            "active_subscribers": {
                event_type: len(callbacks) for event_type, callbacks in self._subscribers.items()
            },
            "history_size": len(self._event_history),
            "tracked_correlations": len(self._correlation_tracker),
        }

    def clear_history(self) -> None:
        """Clear event history (for testing)."""
        self._event_history.clear()
        self._correlation_tracker.clear()
        logger.info("Event history cleared")

    def reset_stats(self) -> None:
        """Reset statistics (for testing)."""
        self._stats = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "subscriber_errors": 0,
        }
        logger.info("Event bus stats reset")


# ============================================================================
# Global Event Bus Instance
# ============================================================================

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Returns:
        EventBus: Global event bus
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (for testing)."""
    global _event_bus
    _event_bus = None
