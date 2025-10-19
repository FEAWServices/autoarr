"""
Event Bus Service for AutoArr.

This service provides a publish-subscribe event system with:
- Event publishing and subscription
- Correlation ID tracking for event chains
- Dead letter queue for failed events
- Async event handlers with error handling
- Event filtering and priority-based routing
- Thread-safe operations

The EventBus follows a singleton pattern to ensure a single global event bus
instance across the application.
"""

import asyncio
import inspect
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Event Types and Models
# ============================================================================


class EventType(str, Enum):
    """Types of events that can be published."""

    # Configuration events
    CONFIG_AUDIT_STARTED = "config_audit_started"
    CONFIG_AUDIT_COMPLETED = "config_audit_completed"
    CONFIG_AUDIT_FAILED = "config_audit_failed"
    CONFIG_CHANGED = "config.changed"

    # Download monitoring events
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    DOWNLOAD_PAUSED = "download_paused"
    DOWNLOAD_RESUMED = "download.resumed"
    DOWNLOAD_STATE_CHANGED = "download_state_changed"

    # Recovery events
    RECOVERY_ATTEMPTED = "recovery_attempted"
    RECOVERY_SUCCESS = "recovery_success"
    RECOVERY_FAILED = "recovery_failed"

    # Content request events
    CONTENT_REQUESTED = "content_requested"
    CONTENT_ADDED = "content_added"
    CONTENT_REQUEST_FAILED = "content_request_failed"
    REQUEST_CREATED = "request.created"
    REQUEST_PROCESSED = "request.processed"
    REQUEST_FAILED = "request.failed"

    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class Event(BaseModel):
    """
    Represents an event in the system.

    Events are immutable records of something that happened in the system.
    They include metadata for tracking and correlation.
    """

    event_type: EventType = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for event chains")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source: str = Field(..., description="Source of the event (service/component name)")

    model_config = {"use_enum_values": True}


# Type alias for event handler functions
EventHandler = Callable[[Event], Union[None, asyncio.Future]]


class EventSubscription(BaseModel):
    """
    Represents a subscription to an event type.

    Subscriptions track which handlers are listening to which events,
    along with optional filtering and priority.
    """

    subscription_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = Field(..., description="Event type to subscribe to")
    handler: Any = Field(..., description="Event handler function")
    event_filter: Optional[Callable[[Event], bool]] = Field(
        None, description="Optional filter function"
    )
    priority: int = Field(1, description="Handler priority (higher = executed first)")

    model_config = {"arbitrary_types_allowed": True}


class DeadLetterEntry(BaseModel):
    """
    Represents a failed event delivery in the dead letter queue.

    Failed events are stored here for later analysis or retry.
    """

    event: Event = Field(..., description="The event that failed")
    error: str = Field(..., description="Error message")
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    handler_name: str = Field(..., description="Name of the handler that failed")

    model_config = {"arbitrary_types_allowed": True}


# Alias for backward compatibility with test imports
DeadLetterQueue = DeadLetterEntry


# ============================================================================
# EventBus Class
# ============================================================================


class EventBus:
    """
    Global event bus for publish-subscribe messaging.

    The EventBus provides:
    - Event publishing with correlation tracking
    - Handler subscription with filtering and priority
    - Dead letter queue for failed deliveries
    - Async/sync handler support
    - Thread-safe operations

    Example:
        ```python
        bus = EventBus()

        # Subscribe to events
        async def my_handler(event: Event):
            print(f"Received: {event.event_type}")

        subscription = bus.subscribe(EventType.DOWNLOAD_COMPLETED, my_handler)

        # Publish events
        event = Event(
            event_type=EventType.DOWNLOAD_COMPLETED,
            data={"nzo_id": "123"},
            source="sabnzbd"
        )
        await bus.publish(event)

        # Unsubscribe
        bus.unsubscribe(subscription)
        ```
    """

    # Dead letter queue size limit
    _DLQ_MAX_SIZE = 100

    # Default handler timeout (seconds)
    _DEFAULT_HANDLER_TIMEOUT = 0.5

    def __init__(self, handler_timeout: float = 0.5):
        """
        Initialize the EventBus.

        Args:
            handler_timeout: Maximum time to wait for each handler (seconds)
        """
        # Store subscriptions by event type
        # Structure: {EventType: [EventSubscription, ...]}
        self._subscriptions: Dict[EventType, List[EventSubscription]] = defaultdict(list)

        # Wildcard subscriptions (subscribe to all events)
        self._wildcard_subscriptions: List[EventSubscription] = []

        # Dead letter queue for failed events
        self._dead_letter_queue: List[DeadLetterEntry] = []

        # Handler timeout
        self._handler_timeout = handler_timeout

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        logger.info(f"EventBus initialized (handler_timeout={handler_timeout}s)")

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
        event_filter: Optional[Callable[[Event], bool]] = None,
        priority: int = 1,
    ) -> EventSubscription:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async or sync function to handle events
            event_filter: Optional filter function to selectively handle events
            priority: Handler priority (higher values execute first)

        Returns:
            EventSubscription object (used for unsubscribing)

        Example:
            ```python
            def tv_only(event: Event) -> bool:
                return event.data.get("category") == "tv"

            bus.subscribe(
                EventType.DOWNLOAD_COMPLETED,
                my_handler,
                event_filter=tv_only,
                priority=10
            )
            ```
        """
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            event_filter=event_filter,
            priority=priority,
        )

        # Add to subscriptions and sort by priority (highest first)
        self._subscriptions[event_type].append(subscription)
        self._subscriptions[event_type].sort(key=lambda s: s.priority, reverse=True)

        logger.debug(
            f"Subscribed handler to {event_type} "
            f"(priority={priority}, filter={event_filter is not None})"
        )

        return subscription

    def subscribe_all(
        self,
        handler: EventHandler,
        event_filter: Optional[Callable[[Event], bool]] = None,
        priority: int = 1,
    ) -> EventSubscription:
        """
        Subscribe a handler to all event types (wildcard subscription).

        Args:
            handler: Async or sync function to handle events
            event_filter: Optional filter function
            priority: Handler priority

        Returns:
            EventSubscription object
        """
        subscription = EventSubscription(
            event_type=EventType.SYSTEM_STARTUP,  # Dummy type for wildcard
            handler=handler,
            event_filter=event_filter,
            priority=priority,
        )

        self._wildcard_subscriptions.append(subscription)
        self._wildcard_subscriptions.sort(key=lambda s: s.priority, reverse=True)

        logger.debug(f"Subscribed wildcard handler (priority={priority})")

        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        """
        Unsubscribe a handler from events.

        Args:
            subscription: The subscription to remove (returned from subscribe())
        """
        # Check wildcard subscriptions first
        if subscription in self._wildcard_subscriptions:
            self._wildcard_subscriptions.remove(subscription)
            logger.debug("Unsubscribed wildcard handler")
            return

        # Check regular subscriptions
        event_type = subscription.event_type
        if event_type in self._subscriptions:
            if subscription in self._subscriptions[event_type]:
                self._subscriptions[event_type].remove(subscription)
                logger.debug(f"Unsubscribed handler from {event_type}")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.

        This method:
        - Auto-generates correlation ID if not present
        - Calls all matching handlers (by type and filter)
        - Handles errors gracefully (failed handlers don't affect others)
        - Stores failed deliveries in dead letter queue
        - Executes handlers in priority order

        Args:
            event: Event to publish

        Example:
            ```python
            event = Event(
                event_type=EventType.DOWNLOAD_FAILED,
                data={"nzo_id": "123", "error": "Connection timeout"},
                correlation_id="workflow-456",
                source="sabnzbd"
            )
            await bus.publish(event)
            ```
        """
        # Auto-generate correlation ID if not present
        if event.correlation_id is None:
            event.correlation_id = str(uuid.uuid4())

        logger.debug(
            f"Publishing event: {event.event_type} "
            f"(correlation_id={event.correlation_id}, source={event.source})"
        )

        # Get handlers for this event type
        handlers_to_call: List[EventSubscription] = []

        # Add wildcard subscriptions
        handlers_to_call.extend(self._wildcard_subscriptions)

        # Add specific subscriptions
        if event.event_type in self._subscriptions:
            handlers_to_call.extend(self._subscriptions[event.event_type])

        # Sort by priority (highest first) - ensure stable sort
        handlers_to_call.sort(key=lambda s: s.priority, reverse=True)

        # Filter based on event_filter functions
        filtered_handlers = []
        for subscription in handlers_to_call:
            if subscription.event_filter is None or subscription.event_filter(event):
                filtered_handlers.append(subscription)

        if not filtered_handlers:
            logger.debug(f"No handlers for event {event.event_type}")
            return

        logger.debug(f"Calling {len(filtered_handlers)} handlers for {event.event_type}")

        # Call all handlers (in order, with error handling)
        for subscription in filtered_handlers:
            try:
                await self._call_handler(subscription.handler, event, timeout=self._handler_timeout)
            except Exception as e:
                # Log error and add to dead letter queue
                handler_name = self._get_handler_name(subscription.handler)
                logger.error(
                    f"Handler {handler_name} failed for event {event.event_type}: {e}",
                    exc_info=True,
                )

                # Add to dead letter queue
                await self._add_to_dead_letter_queue(event, str(e), handler_name)

    async def _call_handler(
        self, handler: EventHandler, event: Event, timeout: float = 30.0
    ) -> None:
        """
        Call an event handler (async or sync) with timeout.

        Args:
            handler: Handler function to call
            event: Event to pass to handler
            timeout: Maximum time to wait for handler (seconds)
        """
        try:
            if inspect.iscoroutinefunction(handler):
                # Async handler with timeout
                await asyncio.wait_for(handler(event), timeout=timeout)
            else:
                # Sync handler - run in executor to avoid blocking (with timeout)
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(loop.run_in_executor(None, handler, event), timeout=timeout)
        except asyncio.TimeoutError:
            # Handler exceeded timeout - raise as regular exception to be caught by publish
            handler_name = self._get_handler_name(handler)
            raise TimeoutError(f"Handler {handler_name} exceeded timeout of {timeout}s")

    def _get_handler_name(self, handler: EventHandler) -> str:
        """Get a readable name for a handler function."""
        if hasattr(handler, "__name__"):
            return handler.__name__
        return str(handler)

    async def _add_to_dead_letter_queue(self, event: Event, error: str, handler_name: str) -> None:
        """
        Add a failed event to the dead letter queue.

        Args:
            event: Event that failed
            error: Error message
            handler_name: Name of the handler that failed
        """
        async with self._lock:
            # Create dead letter entry
            entry = DeadLetterEntry(
                event=event,
                error=error,
                handler_name=handler_name,
            )

            self._dead_letter_queue.append(entry)

            # Enforce size limit (keep most recent entries)
            if len(self._dead_letter_queue) > self._DLQ_MAX_SIZE:
                self._dead_letter_queue = self._dead_letter_queue[-self._DLQ_MAX_SIZE :]

            logger.debug(
                f"Added to dead letter queue: {event.event_type} "
                f"(queue size: {len(self._dead_letter_queue)})"
            )

    def get_dead_letter_queue(self) -> List[DeadLetterEntry]:
        """
        Get all entries in the dead letter queue.

        Returns:
            List of dead letter entries
        """
        return list(self._dead_letter_queue)

    def clear_dead_letter_queue(self) -> None:
        """Clear all entries from the dead letter queue."""
        self._dead_letter_queue.clear()
        logger.info("Cleared dead letter queue")

    async def replay_dead_letter(self, dead_letter: DeadLetterEntry) -> None:
        """
        Replay a failed event from the dead letter queue.

        This re-publishes the event, giving handlers another chance to process it.

        Args:
            dead_letter: Dead letter entry to replay
        """
        logger.info(f"Replaying event from dead letter queue: {dead_letter.event.event_type}")
        await self.publish(dead_letter.event)


# ============================================================================
# Singleton Instance (Optional)
# ============================================================================

# Global event bus instance (optional - tests create their own instances)
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global EventBus instance (singleton pattern).

    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
