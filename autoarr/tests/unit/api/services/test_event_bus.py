"""
Unit tests for Event Bus.

Tests pub/sub pattern, event correlation, error handling, and history tracking.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from autoarr.api.services.event_bus import (
    Event,
    EventBus,
    EventType,
    get_event_bus,
    reset_event_bus,
)


@pytest.fixture
def event_bus():
    """Create a fresh event bus for each test."""
    bus = EventBus(max_history_size=100)
    yield bus
    # Cleanup
    bus.clear_history()


@pytest.fixture(autouse=True)
def reset_global_bus():
    """Reset global event bus after each test."""
    yield
    reset_event_bus()


class TestEventCreation:
    """Test event creation and serialization."""

    def test_event_creation_with_defaults(self):
        """Test creating an event with default values."""
        event = Event(
            event_type=EventType.DOWNLOAD_FAILED,
            payload={"nzo_id": "test123", "reason": "incomplete"},
        )

        assert event.event_type == EventType.DOWNLOAD_FAILED
        assert event.payload["nzo_id"] == "test123"
        assert event.correlation_id is not None
        assert event.causation_id is None
        assert event.timestamp > 0
        assert isinstance(event.metadata, dict)

    def test_event_creation_with_correlation(self):
        """Test creating an event with correlation IDs."""
        event = Event(
            event_type=EventType.DOWNLOAD_RETRY_STARTED,
            payload={"nzo_id": "test123"},
            correlation_id="correlation-123",
            causation_id="event-456",
        )

        assert event.correlation_id == "correlation-123"
        assert event.causation_id == "event-456"

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        event = Event(
            event_type=EventType.CONFIG_APPLIED,
            payload={"application": "sabnzbd", "changes": 5},
            correlation_id="test-correlation",
            metadata={"user": "admin"},
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "config.applied"
        assert event_dict["payload"]["application"] == "sabnzbd"
        assert event_dict["correlation_id"] == "test-correlation"
        assert "timestamp_iso" in event_dict
        assert event_dict["metadata"]["user"] == "admin"

    def test_event_repr(self):
        """Test event string representation."""
        event = Event(
            event_type=EventType.DOWNLOAD_FAILED,
            payload={"nzo_id": "test123", "reason": "incomplete"},
        )

        repr_str = repr(event)

        assert "download.failed" in repr_str
        assert "correlation_id" in repr_str
        assert "nzo_id" in repr_str


class TestEventBusSubscription:
    """Test event subscription and unsubscription."""

    @pytest.mark.asyncio
    async def test_subscribe_to_event(self, event_bus):
        """Test subscribing to a specific event type."""
        callback_called = False

        async def callback(event: Event):
            nonlocal callback_called
            callback_called = True

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback)

        await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
        )

        # Give callback time to execute
        await asyncio.sleep(0.01)

        assert callback_called

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus):
        """Test multiple subscribers receiving the same event."""
        call_count = 0

        async def callback1(event: Event):
            nonlocal call_count
            call_count += 1

        async def callback2(event: Event):
            nonlocal call_count
            call_count += 1

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback1)
        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback2)

        await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
        )

        await asyncio.sleep(0.01)

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_unsubscribe_from_event(self, event_bus):
        """Test unsubscribing from an event type."""
        callback_called = False

        async def callback(event: Event):
            nonlocal callback_called
            callback_called = True

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback)
        event_bus.unsubscribe(EventType.DOWNLOAD_FAILED, callback)

        await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
        )

        await asyncio.sleep(0.01)

        assert not callback_called

    @pytest.mark.asyncio
    async def test_subscribe_all_wildcard(self, event_bus):
        """Test wildcard subscription to all event types."""
        received_events = []

        async def callback(event: Event):
            received_events.append(event.event_type)

        event_bus.subscribe_all(callback)

        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.CONFIG_APPLIED, {})
        await event_bus.emit(EventType.AUDIT_COMPLETED, {})

        await asyncio.sleep(0.01)

        assert len(received_events) == 3
        assert EventType.DOWNLOAD_FAILED in received_events
        assert EventType.CONFIG_APPLIED in received_events
        assert EventType.AUDIT_COMPLETED in received_events

    @pytest.mark.asyncio
    async def test_subscriber_not_called_for_different_event(self, event_bus):
        """Test that subscribers only receive events they subscribed to."""
        callback_called = False

        async def callback(event: Event):
            nonlocal callback_called
            callback_called = True

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback)

        await event_bus.emit(
            EventType.CONFIG_APPLIED,
            {"application": "sabnzbd"},
        )

        await asyncio.sleep(0.01)

        assert not callback_called


class TestEventEmission:
    """Test event emission and delivery."""

    @pytest.mark.asyncio
    async def test_emit_returns_event(self, event_bus):
        """Test that emit returns the created event."""
        event = await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
        )

        assert isinstance(event, Event)
        assert event.event_type == EventType.DOWNLOAD_FAILED
        assert event.payload["nzo_id"] == "test123"

    @pytest.mark.asyncio
    async def test_emit_generates_correlation_id(self, event_bus):
        """Test that correlation ID is generated if not provided."""
        event = await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
        )

        assert event.correlation_id is not None
        assert len(event.correlation_id) > 0

    @pytest.mark.asyncio
    async def test_emit_with_custom_correlation_id(self, event_bus):
        """Test emitting event with custom correlation ID."""
        event = await event_bus.emit(
            EventType.DOWNLOAD_RETRY_STARTED,
            {"nzo_id": "test123"},
            correlation_id="custom-correlation-id",
        )

        assert event.correlation_id == "custom-correlation-id"

    @pytest.mark.asyncio
    async def test_emit_with_causation_id(self, event_bus):
        """Test emitting event with causation ID."""
        first_event = await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
        )

        second_event = await event_bus.emit(
            EventType.DOWNLOAD_RETRY_STARTED,
            {"nzo_id": "test123"},
            correlation_id=first_event.correlation_id,
            causation_id=first_event.correlation_id,
        )

        assert second_event.causation_id == first_event.correlation_id

    @pytest.mark.asyncio
    async def test_emit_with_metadata(self, event_bus):
        """Test emitting event with custom metadata."""
        event = await event_bus.emit(
            EventType.CONFIG_APPLIED,
            {"application": "sabnzbd"},
            metadata={"user": "admin", "source": "api"},
        )

        assert event.metadata["user"] == "admin"
        assert event.metadata["source"] == "api"

    @pytest.mark.asyncio
    async def test_emit_updates_stats(self, event_bus):
        """Test that emitting events updates statistics."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.CONFIG_APPLIED, {})

        stats = event_bus.get_stats()

        assert stats["total_events"] == 3
        assert stats["events_by_type"]["download.failed"] == 2
        assert stats["events_by_type"]["config.applied"] == 1


class TestEventHistory:
    """Test event history tracking."""

    @pytest.mark.asyncio
    async def test_event_added_to_history(self, event_bus):
        """Test that emitted events are added to history."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {"nzo_id": "test123"})

        history = event_bus.get_history()

        assert len(history) == 1
        assert history[0].event_type == EventType.DOWNLOAD_FAILED

    @pytest.mark.asyncio
    async def test_history_limit(self, event_bus):
        """Test that history respects maximum size."""
        small_bus = EventBus(max_history_size=5)

        for i in range(10):
            await small_bus.emit(EventType.DOWNLOAD_FAILED, {"index": i})

        history = small_bus.get_history()

        assert len(history) <= 5

    @pytest.mark.asyncio
    async def test_get_history_filtered_by_type(self, event_bus):
        """Test filtering history by event type."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {"nzo_id": "1"})
        await event_bus.emit(EventType.CONFIG_APPLIED, {"app": "sabnzbd"})
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {"nzo_id": "2"})

        history = event_bus.get_history(event_type=EventType.DOWNLOAD_FAILED)

        assert len(history) == 2
        assert all(e.event_type == EventType.DOWNLOAD_FAILED for e in history)

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self, event_bus):
        """Test limiting history results."""
        for i in range(10):
            await event_bus.emit(EventType.DOWNLOAD_FAILED, {"index": i})

        history = event_bus.get_history(limit=3)

        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_history_returns_most_recent_first(self, event_bus):
        """Test that history is returned in reverse chronological order."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {"index": 0})
        await asyncio.sleep(0.01)
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {"index": 1})
        await asyncio.sleep(0.01)
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {"index": 2})

        history = event_bus.get_history()

        assert history[0].payload["index"] == 2
        assert history[1].payload["index"] == 1
        assert history[2].payload["index"] == 0

    @pytest.mark.asyncio
    async def test_clear_history(self, event_bus):
        """Test clearing event history."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.CONFIG_APPLIED, {})

        event_bus.clear_history()

        history = event_bus.get_history()
        assert len(history) == 0


class TestCorrelationTracking:
    """Test event correlation tracking."""

    @pytest.mark.asyncio
    async def test_correlation_tracking(self, event_bus):
        """Test tracking events by correlation ID."""
        correlation_id = "test-correlation-123"

        await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123"},
            correlation_id=correlation_id,
        )
        await event_bus.emit(
            EventType.DOWNLOAD_RETRY_STARTED,
            {"nzo_id": "test123"},
            correlation_id=correlation_id,
        )

        correlated = event_bus.get_correlated_events(correlation_id)

        assert len(correlated) == 2
        assert all(e.correlation_id == correlation_id for e in correlated)

    @pytest.mark.asyncio
    async def test_get_history_by_correlation_id(self, event_bus):
        """Test getting history filtered by correlation ID."""
        correlation_id = "test-correlation-123"

        await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {},
            correlation_id=correlation_id,
        )
        await event_bus.emit(EventType.CONFIG_APPLIED, {})  # Different correlation
        await event_bus.emit(
            EventType.DOWNLOAD_RETRY_STARTED,
            {},
            correlation_id=correlation_id,
        )

        history = event_bus.get_history(correlation_id=correlation_id)

        assert len(history) == 2
        assert all(e.correlation_id == correlation_id for e in history)

    @pytest.mark.asyncio
    async def test_empty_correlation_tracking(self, event_bus):
        """Test getting correlated events for unknown correlation ID."""
        correlated = event_bus.get_correlated_events("unknown-correlation")

        assert len(correlated) == 0


class TestErrorHandling:
    """Test error handling in event subscribers."""

    @pytest.mark.asyncio
    async def test_subscriber_error_isolated(self, event_bus):
        """Test that one subscriber's error doesn't affect others."""
        successful_calls = 0

        async def failing_callback(event: Event):
            raise ValueError("Subscriber error")

        async def successful_callback(event: Event):
            nonlocal successful_calls
            successful_calls += 1

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, failing_callback)
        event_bus.subscribe(EventType.DOWNLOAD_FAILED, successful_callback)

        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})

        await asyncio.sleep(0.01)

        assert successful_calls == 1

    @pytest.mark.asyncio
    async def test_subscriber_error_tracked_in_stats(self, event_bus):
        """Test that subscriber errors are tracked in statistics."""

        async def failing_callback(event: Event):
            raise ValueError("Test error")

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, failing_callback)

        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})

        await asyncio.sleep(0.01)

        stats = event_bus.get_stats()
        assert stats["subscriber_errors"] > 0

    @pytest.mark.asyncio
    async def test_sync_callback_supported(self, event_bus):
        """Test that synchronous callbacks are supported."""
        callback_called = False

        def sync_callback(event: Event):
            nonlocal callback_called
            callback_called = True

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, sync_callback)

        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})

        await asyncio.sleep(0.01)

        assert callback_called


class TestStatistics:
    """Test event bus statistics."""

    @pytest.mark.asyncio
    async def test_stats_initialization(self, event_bus):
        """Test that stats are properly initialized."""
        stats = event_bus.get_stats()

        assert stats["total_events"] == 0
        assert isinstance(stats["events_by_type"], dict)
        assert stats["subscriber_errors"] == 0

    @pytest.mark.asyncio
    async def test_stats_track_events_by_type(self, event_bus):
        """Test that statistics track events by type."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.CONFIG_APPLIED, {})
        await event_bus.emit(EventType.AUDIT_COMPLETED, {})

        stats = event_bus.get_stats()

        assert stats["events_by_type"]["download.failed"] == 2
        assert stats["events_by_type"]["config.applied"] == 1
        assert stats["events_by_type"]["audit.completed"] == 1

    @pytest.mark.asyncio
    async def test_stats_track_active_subscribers(self, event_bus):
        """Test that stats track active subscribers."""

        async def callback1(event: Event):
            pass

        async def callback2(event: Event):
            pass

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback1)
        event_bus.subscribe(EventType.DOWNLOAD_FAILED, callback2)
        event_bus.subscribe(EventType.CONFIG_APPLIED, callback1)

        stats = event_bus.get_stats()

        assert stats["active_subscribers"]["download.failed"] == 2
        assert stats["active_subscribers"]["config.applied"] == 1

    @pytest.mark.asyncio
    async def test_reset_stats(self, event_bus):
        """Test resetting statistics."""
        await event_bus.emit(EventType.DOWNLOAD_FAILED, {})
        await event_bus.emit(EventType.CONFIG_APPLIED, {})

        event_bus.reset_stats()

        stats = event_bus.get_stats()
        assert stats["total_events"] == 0
        assert len(stats["events_by_type"]) == 0


class TestGlobalEventBus:
    """Test global event bus singleton."""

    def test_get_event_bus_singleton(self):
        """Test that get_event_bus returns singleton instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_reset_event_bus(self):
        """Test resetting global event bus."""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()

        assert bus1 is not bus2


class TestEventFlows:
    """Test complete event flows (integration-style)."""

    @pytest.mark.asyncio
    async def test_download_failure_recovery_flow(self, event_bus):
        """Test complete download failure and recovery event flow."""
        events_received = []

        async def event_logger(event: Event):
            events_received.append(event.event_type)

        event_bus.subscribe_all(event_logger)

        correlation_id = "download-123"

        # Simulate download failure flow
        failure_event = await event_bus.emit(
            EventType.DOWNLOAD_FAILED,
            {"nzo_id": "test123", "reason": "incomplete"},
            correlation_id=correlation_id,
        )

        await event_bus.emit(
            EventType.DOWNLOAD_RETRY_STARTED,
            {"nzo_id": "test123", "attempt": 1},
            correlation_id=correlation_id,
            causation_id=failure_event.correlation_id,
        )

        await event_bus.emit(
            EventType.DOWNLOAD_RECOVERED,
            {"nzo_id": "test123"},
            correlation_id=correlation_id,
        )

        await asyncio.sleep(0.01)

        # Verify flow
        assert EventType.DOWNLOAD_FAILED in events_received
        assert EventType.DOWNLOAD_RETRY_STARTED in events_received
        assert EventType.DOWNLOAD_RECOVERED in events_received

        # Verify correlation
        correlated = event_bus.get_correlated_events(correlation_id)
        assert len(correlated) == 3
