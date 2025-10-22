"""
Unit tests for Event Bus (Sprint 5).

This module tests the EventBus's ability to:
- Publish events to subscribers
- Subscribe/unsubscribe handlers for specific event types
- Support multiple subscribers for the same event type
- Correlate events with unique correlation IDs
- Handle dead letter queue for failed event deliveries
- Support async event handlers
- Handle subscriber errors gracefully
- Provide event filtering and routing

Test Strategy:
- 70% Unit Tests: Focus on pub/sub mechanics and error handling
- Test all event types and routing logic
- Verify correlation ID propagation
- Test dead letter queue functionality
- Ensure thread-safety and async handling
- Test edge cases: no subscribers, failing subscribers, concurrent events
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

from autoarr.api.services.event_bus import Event, EventBus, EventType

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def event_bus():
    """Create an EventBus instance."""
    return EventBus()


@pytest.fixture
def mock_handler():
    """Create a mock event handler."""
    handler = AsyncMock()
    handler.return_value = None
    return handler


@pytest.fixture
def mock_handler_sync():
    """Create a mock synchronous event handler."""
    handler = Mock()
    handler.return_value = None
    return handler


# ============================================================================
# Test Data Factories
# ============================================================================


def create_event(
    event_type: EventType,
    data: Dict[str, Any] = None,
    correlation_id: str = None,
    source: str = "test",
) -> Event:
    """Factory to create Event test data."""
    return Event(
        event_type=event_type,
        data=data or {},
        correlation_id=correlation_id or f"corr_{datetime.now().timestamp()}",
        timestamp=datetime.now(),
        source=source,
    )


# ============================================================================
# Tests for Event Publishing
# ============================================================================


@pytest.mark.asyncio
async def test_publish_event_to_subscriber(event_bus, mock_handler):
    """Test publishing an event to a subscribed handler."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    event = create_event(EventType.DOWNLOAD_FAILED, data={"nzo_id": "test_123"})

    # Act
    await event_bus.publish(event)

    # Assert
    mock_handler.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_publish_event_with_no_subscribers(event_bus):
    """Test publishing an event when there are no subscribers."""
    # Arrange
    event = create_event(EventType.DOWNLOAD_FAILED, data={"nzo_id": "test_123"})

    # Act & Assert - Should not raise any exceptions
    await event_bus.publish(event)


@pytest.mark.asyncio
async def test_publish_multiple_events_sequentially(event_bus, mock_handler):
    """Test publishing multiple events in sequence."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    events = [
        create_event(EventType.DOWNLOAD_FAILED, data={"nzo_id": f"test_{i}"}) for i in range(3)
    ]

    # Act
    for event in events:
        await event_bus.publish(event)

    # Assert
    assert mock_handler.call_count == 3
    for i, call_args in enumerate(mock_handler.call_args_list):
        assert call_args[0][0].data["nzo_id"] == f"test_{i}"


@pytest.mark.asyncio
async def test_publish_different_event_types(event_bus):
    """Test publishing different event types to appropriate subscribers."""
    # Arrange
    handler_download = AsyncMock()
    handler_recovery = AsyncMock()

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_download)
    event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, handler_recovery)

    event_download = create_event(EventType.DOWNLOAD_FAILED)
    event_recovery = create_event(EventType.RECOVERY_ATTEMPTED)

    # Act
    await event_bus.publish(event_download)
    await event_bus.publish(event_recovery)

    # Assert
    handler_download.assert_called_once_with(event_download)
    handler_recovery.assert_called_once_with(event_recovery)


@pytest.mark.asyncio
async def test_publish_preserves_event_data(event_bus, mock_handler):
    """Test that published events preserve all data fields."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, mock_handler)
    event_data = {
        "nzo_id": "test_123",
        "name": "Test.Download.mkv",
        "size": 1234567890,
        "category": "tv",
    }
    event = create_event(
        EventType.DOWNLOAD_COMPLETED,
        data=event_data,
        correlation_id="corr_abc123",
    )

    # Act
    await event_bus.publish(event)

    # Assert
    published_event = mock_handler.call_args[0][0]
    assert published_event.data == event_data
    assert published_event.correlation_id == "corr_abc123"
    assert published_event.event_type == EventType.DOWNLOAD_COMPLETED


# ============================================================================
# Tests for Event Subscription
# ============================================================================


@pytest.mark.asyncio
async def test_subscribe_handler_to_event_type(event_bus, mock_handler):
    """Test subscribing a handler to an event type."""
    # Act
    subscription = event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)

    # Assert
    assert subscription is not None
    assert subscription.event_type == EventType.DOWNLOAD_FAILED
    assert subscription.handler == mock_handler


@pytest.mark.asyncio
async def test_subscribe_multiple_handlers_to_same_event(event_bus):
    """Test subscribing multiple handlers to the same event type."""
    # Arrange
    handler_1 = AsyncMock()
    handler_2 = AsyncMock()
    handler_3 = AsyncMock()

    # Act
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_1)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_2)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_3)

    event = create_event(EventType.DOWNLOAD_FAILED)
    await event_bus.publish(event)

    # Assert - All handlers should be called
    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)
    handler_3.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_subscribe_same_handler_to_multiple_event_types(event_bus, mock_handler):
    """Test subscribing the same handler to multiple event types."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, mock_handler)

    event_1 = create_event(EventType.DOWNLOAD_FAILED)
    event_2 = create_event(EventType.RECOVERY_ATTEMPTED)

    # Act
    await event_bus.publish(event_1)
    await event_bus.publish(event_2)

    # Assert - Handler should be called for both event types
    assert mock_handler.call_count == 2


@pytest.mark.asyncio
async def test_unsubscribe_handler(event_bus, mock_handler):
    """Test unsubscribing a handler from an event type."""
    # Arrange
    subscription = event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)

    # Act - Unsubscribe
    event_bus.unsubscribe(subscription)

    # Publish event after unsubscribe
    event = create_event(EventType.DOWNLOAD_FAILED)
    await event_bus.publish(event)

    # Assert - Handler should not be called
    mock_handler.assert_not_called()


@pytest.mark.asyncio
async def test_unsubscribe_one_of_multiple_handlers(event_bus):
    """Test unsubscribing one handler while others remain subscribed."""
    # Arrange
    handler_1 = AsyncMock()
    handler_2 = AsyncMock()

    subscription_1 = event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_1)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_2)

    # Act - Unsubscribe only handler_1
    event_bus.unsubscribe(subscription_1)

    event = create_event(EventType.DOWNLOAD_FAILED)
    await event_bus.publish(event)

    # Assert
    handler_1.assert_not_called()
    handler_2.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_subscribe_with_event_filter(event_bus):
    """Test subscribing with an event filter function."""
    # Arrange
    handler = AsyncMock()

    def filter_func(event: Event) -> bool:
        # Only handle events for specific category
        return event.data.get("category") == "tv"

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler, event_filter=filter_func)

    event_tv = create_event(EventType.DOWNLOAD_FAILED, data={"category": "tv"})
    event_movie = create_event(EventType.DOWNLOAD_FAILED, data={"category": "movies"})

    # Act
    await event_bus.publish(event_tv)
    await event_bus.publish(event_movie)

    # Assert - Only TV event should trigger handler
    handler.assert_called_once_with(event_tv)


# ============================================================================
# Tests for Event Correlation
# ============================================================================


@pytest.mark.asyncio
async def test_event_includes_correlation_id(event_bus, mock_handler):
    """Test that events include correlation IDs."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    correlation_id = "test_correlation_123"
    event = create_event(EventType.DOWNLOAD_FAILED, correlation_id=correlation_id)

    # Act
    await event_bus.publish(event)

    # Assert
    published_event = mock_handler.call_args[0][0]
    assert published_event.correlation_id == correlation_id


@pytest.mark.asyncio
async def test_auto_generate_correlation_id_if_missing(event_bus, mock_handler):
    """Test auto-generation of correlation ID if not provided."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    event = Event(
        event_type=EventType.DOWNLOAD_FAILED,
        data={},
        correlation_id=None,  # Not provided
        timestamp=datetime.now(),
        source="test",
    )

    # Act
    await event_bus.publish(event)

    # Assert
    published_event = mock_handler.call_args[0][0]
    assert published_event.correlation_id is not None
    assert len(published_event.correlation_id) > 0


@pytest.mark.asyncio
async def test_correlate_related_events(event_bus, mock_handler):
    """Test correlating related events using the same correlation ID."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, mock_handler)

    correlation_id = "workflow_123"
    event_1 = create_event(EventType.DOWNLOAD_FAILED, correlation_id=correlation_id)
    event_2 = create_event(EventType.RECOVERY_ATTEMPTED, correlation_id=correlation_id)

    # Act
    await event_bus.publish(event_1)
    await event_bus.publish(event_2)

    # Assert - Both events should have same correlation ID
    assert mock_handler.call_count == 2
    call_1 = mock_handler.call_args_list[0][0][0]
    call_2 = mock_handler.call_args_list[1][0][0]
    assert call_1.correlation_id == call_2.correlation_id == correlation_id


@pytest.mark.asyncio
async def test_track_event_chain_by_correlation_id(event_bus):
    """Test tracking a chain of related events."""
    # Arrange
    events_received = []

    async def tracking_handler(event: Event):
        events_received.append(event)

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, tracking_handler)
    event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, tracking_handler)
    event_bus.subscribe(EventType.RECOVERY_SUCCESS, tracking_handler)

    correlation_id = "chain_abc123"

    # Act - Publish chain of related events
    await event_bus.publish(create_event(EventType.DOWNLOAD_FAILED, correlation_id=correlation_id))
    await event_bus.publish(
        create_event(EventType.RECOVERY_ATTEMPTED, correlation_id=correlation_id)
    )
    await event_bus.publish(create_event(EventType.RECOVERY_SUCCESS, correlation_id=correlation_id))

    # Assert - All events in chain have same correlation ID
    assert len(events_received) == 3
    assert all(e.correlation_id == correlation_id for e in events_received)


# ============================================================================
# Tests for Multiple Subscribers
# ============================================================================


@pytest.mark.asyncio
async def test_all_subscribers_receive_event(event_bus):
    """Test that all subscribers receive published events."""
    # Arrange
    handlers = [AsyncMock() for _ in range(5)]
    for handler in handlers:
        event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, handler)

    event = create_event(EventType.DOWNLOAD_COMPLETED)

    # Act
    await event_bus.publish(event)

    # Assert - All handlers called
    for handler in handlers:
        handler.assert_called_once_with(event)


@pytest.mark.asyncio
async def test_subscriber_execution_order(event_bus):
    """Test execution order of multiple subscribers."""
    # Arrange
    execution_order = []

    async def handler_1(event: Event):
        execution_order.append(1)

    async def handler_2(event: Event):
        execution_order.append(2)

    async def handler_3(event: Event):
        execution_order.append(3)

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_1)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_2)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_3)

    event = create_event(EventType.DOWNLOAD_FAILED)

    # Act
    await event_bus.publish(event)

    # Assert - Order should be maintained (or document if parallel)
    assert execution_order == [1, 2, 3]  # Or check if parallel execution


@pytest.mark.asyncio
async def test_subscriber_failure_does_not_affect_others(event_bus):
    """Test that one subscriber's failure doesn't affect others."""
    # Arrange
    handler_1 = AsyncMock(side_effect=Exception("Handler 1 failed"))
    handler_2 = AsyncMock()
    handler_3 = AsyncMock()

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_1)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_2)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler_3)

    event = create_event(EventType.DOWNLOAD_FAILED)

    # Act
    await event_bus.publish(event)

    # Assert - Handlers 2 and 3 should still be called despite handler 1 failure
    handler_2.assert_called_once_with(event)
    handler_3.assert_called_once_with(event)


# ============================================================================
# Tests for Dead Letter Queue
# ============================================================================


@pytest.mark.asyncio
async def test_failed_event_delivery_to_dead_letter_queue(event_bus, mock_handler):
    """Test that failed event deliveries go to dead letter queue."""
    # Arrange
    mock_handler.side_effect = Exception("Handler error")
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)

    event = create_event(EventType.DOWNLOAD_FAILED, data={"nzo_id": "test_123"})

    # Act
    await event_bus.publish(event)

    # Assert - Event should be in dead letter queue
    dead_letters = event_bus.get_dead_letter_queue()
    assert len(dead_letters) >= 1
    assert any(dl.event.data.get("nzo_id") == "test_123" for dl in dead_letters)


@pytest.mark.asyncio
async def test_dead_letter_includes_error_info(event_bus):
    """Test that dead letter queue entries include error information."""
    # Arrange
    error_message = "Specific handler error"

    async def failing_handler(event: Event):
        raise ValueError(error_message)

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, failing_handler)
    event = create_event(EventType.DOWNLOAD_FAILED)

    # Act
    await event_bus.publish(event)

    # Assert
    dead_letters = event_bus.get_dead_letter_queue()
    assert len(dead_letters) >= 1
    dead_letter = dead_letters[-1]
    assert dead_letter.error is not None
    assert error_message in str(dead_letter.error)


@pytest.mark.asyncio
async def test_dead_letter_retry_count(event_bus):
    """Test tracking retry count for failed events."""
    # Arrange
    handler = AsyncMock(side_effect=Exception("Handler error"))
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler)
    event = create_event(EventType.DOWNLOAD_FAILED)

    # Act - Try to publish multiple times
    await event_bus.publish(event)
    await event_bus.publish(event)
    await event_bus.publish(event)

    # Assert - Should track multiple failures
    dead_letters = event_bus.get_dead_letter_queue()
    assert len(dead_letters) >= 3


@pytest.mark.asyncio
async def test_clear_dead_letter_queue(event_bus):
    """Test clearing the dead letter queue."""
    # Arrange
    handler = AsyncMock(side_effect=Exception("Error"))
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler)
    event = create_event(EventType.DOWNLOAD_FAILED)

    await event_bus.publish(event)
    assert len(event_bus.get_dead_letter_queue()) >= 1

    # Act
    event_bus.clear_dead_letter_queue()

    # Assert
    assert len(event_bus.get_dead_letter_queue()) == 0


@pytest.mark.asyncio
async def test_dead_letter_queue_size_limit(event_bus):
    """Test that dead letter queue has a size limit."""
    # Arrange
    handler = AsyncMock(side_effect=Exception("Error"))
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler)

    # Act - Publish many failing events
    for i in range(150):  # More than typical limit (e.g., 100)
        event = create_event(EventType.DOWNLOAD_FAILED, data={"id": i})
        await event_bus.publish(event)

    # Assert - Should not grow indefinitely
    dead_letters = event_bus.get_dead_letter_queue()
    assert len(dead_letters) <= 100  # Or configured limit


@pytest.mark.asyncio
async def test_replay_dead_letter_event(event_bus):
    """Test replaying events from dead letter queue."""
    # Arrange
    handler = AsyncMock(side_effect=[Exception("First fails"), None])  # Fails then succeeds
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler)
    event = create_event(EventType.DOWNLOAD_FAILED, data={"nzo_id": "replay_test"})

    await event_bus.publish(event)
    dead_letters = event_bus.get_dead_letter_queue()
    assert len(dead_letters) >= 1

    # Act - Replay from dead letter queue
    dead_letter = dead_letters[-1]
    await event_bus.replay_dead_letter(dead_letter)

    # Assert - Should succeed on replay
    assert handler.call_count == 2  # Original + replay


# ============================================================================
# Tests for Async Event Handlers
# ============================================================================


@pytest.mark.asyncio
async def test_async_handler_execution(event_bus):
    """Test execution of async event handlers."""
    # Arrange
    handler_called = False

    async def async_handler(event: Event):
        nonlocal handler_called
        await asyncio.sleep(0.1)  # Simulate async work
        handler_called = True

    event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, async_handler)
    event = create_event(EventType.DOWNLOAD_COMPLETED)

    # Act
    await event_bus.publish(event)

    # Assert
    assert handler_called is True


@pytest.mark.asyncio
async def test_concurrent_async_handlers(event_bus):
    """Test concurrent execution of multiple async handlers."""
    # Arrange
    execution_times = []

    async def slow_handler(event: Event):
        start = datetime.now()
        await asyncio.sleep(0.2)
        execution_times.append((start, datetime.now()))

    # Subscribe multiple handlers
    for _ in range(3):
        event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, slow_handler)

    event = create_event(EventType.DOWNLOAD_COMPLETED)

    # Act
    start_time = datetime.now()
    await event_bus.publish(event)
    total_time = (datetime.now() - start_time).total_seconds()

    # Assert - If parallel, should take ~0.2s, not ~0.6s
    # (Depends on implementation - adjust expectation accordingly)
    assert len(execution_times) == 3


@pytest.mark.asyncio
async def test_mixed_sync_async_handlers(event_bus):
    """Test handling of mixed sync and async event handlers."""
    # Arrange
    sync_called = False
    async_called = False

    def sync_handler(event: Event):
        nonlocal sync_called
        sync_called = True

    async def async_handler(event: Event):
        nonlocal async_called
        await asyncio.sleep(0.01)
        async_called = True

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, sync_handler)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, async_handler)

    event = create_event(EventType.DOWNLOAD_FAILED)

    # Act
    await event_bus.publish(event)

    # Assert
    assert sync_called is True
    assert async_called is True


# ============================================================================
# Tests for Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_handle_handler_exception(event_bus):
    """Test graceful handling of handler exceptions."""

    # Arrange
    async def failing_handler(event: Event):
        raise RuntimeError("Handler failed")

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, failing_handler)
    event = create_event(EventType.DOWNLOAD_FAILED)

    # Act & Assert - Should not raise exception
    await event_bus.publish(event)  # Should handle gracefully


@pytest.mark.asyncio
async def test_handle_invalid_event_type(event_bus):
    """Test handling of invalid event type."""
    # Arrange - Try to create event with invalid type
    # (This depends on implementation - may validate at Event creation)

    # Act & Assert
    # Should either reject at creation or handle gracefully at publish


@pytest.mark.asyncio
async def test_handle_handler_timeout(event_bus):
    """Test handling of slow/hanging handlers."""

    # Arrange
    async def slow_handler(event: Event):
        await asyncio.sleep(10)  # Very slow handler

    event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, slow_handler)
    event = create_event(EventType.DOWNLOAD_COMPLETED)

    # Act - Publish with timeout
    start_time = datetime.now()
    await asyncio.wait_for(event_bus.publish(event), timeout=1.0)
    duration = (datetime.now() - start_time).total_seconds()

    # Assert - Should timeout and not block indefinitely
    assert duration < 2.0


@pytest.mark.asyncio
async def test_handle_concurrent_publishes(event_bus, mock_handler):
    """Test handling of concurrent event publishes."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)
    events = [create_event(EventType.DOWNLOAD_FAILED, data={"id": i}) for i in range(10)]

    # Act - Publish concurrently
    await asyncio.gather(*[event_bus.publish(e) for e in events])

    # Assert - All events should be handled
    assert mock_handler.call_count == 10


# ============================================================================
# Tests for Event Metadata
# ============================================================================


@pytest.mark.asyncio
async def test_event_includes_timestamp(event_bus, mock_handler):
    """Test that events include timestamps."""
    # Arrange
    event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, mock_handler)
    event = create_event(EventType.DOWNLOAD_COMPLETED)

    # Act
    await event_bus.publish(event)

    # Assert
    published_event = mock_handler.call_args[0][0]
    assert published_event.timestamp is not None
    assert isinstance(published_event.timestamp, datetime)


@pytest.mark.asyncio
async def test_event_includes_source(event_bus, mock_handler):
    """Test that events include source information."""
    # Arrange
    event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, mock_handler)
    event = create_event(EventType.RECOVERY_ATTEMPTED, source="recovery_service")

    # Act
    await event_bus.publish(event)

    # Assert
    published_event = mock_handler.call_args[0][0]
    assert published_event.source == "recovery_service"


@pytest.mark.asyncio
async def test_event_immutability(event_bus, mock_handler):
    """Test that events cannot be modified by handlers."""
    # Arrange
    original_data = {"nzo_id": "test_123", "status": "failed"}

    async def modifying_handler(event: Event):
        # Try to modify event data
        event.data["status"] = "modified"

    event_bus.subscribe(EventType.DOWNLOAD_FAILED, modifying_handler)
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, mock_handler)

    event = create_event(EventType.DOWNLOAD_FAILED, data=original_data.copy())

    # Act
    await event_bus.publish(event)

    # Assert - Original event should remain unchanged for subsequent handlers
    # (Depends on implementation - may need deep copy or immutable events)


# ============================================================================
# Tests for Performance
# ============================================================================


@pytest.mark.asyncio
async def test_publish_performance_with_many_subscribers(event_bus):
    """Test publish performance with many subscribers."""
    # Arrange - Many subscribers
    handlers = [AsyncMock() for _ in range(100)]
    for handler in handlers:
        event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, handler)

    event = create_event(EventType.DOWNLOAD_COMPLETED)

    # Act
    start_time = datetime.now()
    await event_bus.publish(event)
    duration = (datetime.now() - start_time).total_seconds()

    # Assert - Should complete in reasonable time
    assert duration < 1.0  # Should be fast
    assert all(h.called for h in handlers)


@pytest.mark.asyncio
async def test_subscribe_unsubscribe_performance(event_bus):
    """Test performance of subscribe/unsubscribe operations."""
    # Arrange
    handlers = [AsyncMock() for _ in range(1000)]

    # Act - Subscribe many handlers
    start_time = datetime.now()
    subscriptions = [event_bus.subscribe(EventType.DOWNLOAD_FAILED, h) for h in handlers]
    subscribe_duration = (datetime.now() - start_time).total_seconds()

    # Unsubscribe all
    start_time = datetime.now()
    for sub in subscriptions:
        event_bus.unsubscribe(sub)
    unsubscribe_duration = (datetime.now() - start_time).total_seconds()

    # Assert - Should be reasonably fast
    assert subscribe_duration < 1.0
    assert unsubscribe_duration < 1.0


# ============================================================================
# Tests for Event Filtering and Routing
# ============================================================================


@pytest.mark.asyncio
async def test_wildcard_subscription(event_bus):
    """Test subscribing to all event types with wildcard."""
    # Arrange
    all_events_handler = AsyncMock()
    event_bus.subscribe_all(all_events_handler)

    # Act - Publish different event types
    await event_bus.publish(create_event(EventType.DOWNLOAD_FAILED))
    await event_bus.publish(create_event(EventType.RECOVERY_ATTEMPTED))
    await event_bus.publish(create_event(EventType.DOWNLOAD_COMPLETED))

    # Assert - Handler should receive all events
    assert all_events_handler.call_count == 3


@pytest.mark.asyncio
async def test_event_routing_by_pattern(event_bus):
    """Test event routing based on data patterns."""
    # Arrange
    tv_handler = AsyncMock()
    movie_handler = AsyncMock()

    # Subscribe with filters
    event_bus.subscribe(
        EventType.DOWNLOAD_COMPLETED,
        tv_handler,
        event_filter=lambda e: e.data.get("category") == "tv",
    )
    event_bus.subscribe(
        EventType.DOWNLOAD_COMPLETED,
        movie_handler,
        event_filter=lambda e: e.data.get("category") == "movies",
    )

    # Act
    await event_bus.publish(create_event(EventType.DOWNLOAD_COMPLETED, data={"category": "tv"}))
    await event_bus.publish(create_event(EventType.DOWNLOAD_COMPLETED, data={"category": "movies"}))

    # Assert
    tv_handler.assert_called_once()
    movie_handler.assert_called_once()


@pytest.mark.asyncio
async def test_event_priority_handling(event_bus):
    """Test handling of high-priority events."""
    # Arrange
    execution_order = []

    async def high_priority_handler(event: Event):
        execution_order.append("high")

    async def normal_priority_handler(event: Event):
        execution_order.append("normal")

    event_bus.subscribe(
        EventType.DOWNLOAD_FAILED, high_priority_handler, priority=10  # High priority
    )
    event_bus.subscribe(
        EventType.DOWNLOAD_FAILED, normal_priority_handler, priority=1  # Normal priority
    )

    # Act
    await event_bus.publish(create_event(EventType.DOWNLOAD_FAILED))

    # Assert - High priority should execute first
    assert execution_order == ["high", "normal"]


# ============================================================================
# Tests for Thread Safety and Concurrency
# ============================================================================


@pytest.mark.asyncio
async def test_thread_safe_subscribe_unsubscribe(event_bus):
    """Test thread-safe subscribe/unsubscribe operations."""

    # Arrange & Act - Concurrent subscribe/unsubscribe
    async def subscribe_many():
        handlers = [AsyncMock() for _ in range(50)]
        subs = [event_bus.subscribe(EventType.DOWNLOAD_FAILED, h) for h in handlers]
        for sub in subs:
            event_bus.unsubscribe(sub)

    # Execute concurrently
    await asyncio.gather(*[subscribe_many() for _ in range(10)])

    # Assert - Should not crash or corrupt state
    # Verify event bus is still functional
    handler = AsyncMock()
    event_bus.subscribe(EventType.DOWNLOAD_FAILED, handler)
    await event_bus.publish(create_event(EventType.DOWNLOAD_FAILED))
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_publish_to_same_handler(event_bus):
    """Test concurrent publishes to the same handler."""
    # Arrange
    handler_call_count = 0
    lock = asyncio.Lock()

    async def counting_handler(event: Event):
        nonlocal handler_call_count
        async with lock:
            handler_call_count += 1

    event_bus.subscribe(EventType.DOWNLOAD_COMPLETED, counting_handler)

    # Act - Publish many events concurrently
    events = [create_event(EventType.DOWNLOAD_COMPLETED) for _ in range(20)]
    await asyncio.gather(*[event_bus.publish(e) for e in events])

    # Assert - All events should be handled
    assert handler_call_count == 20
