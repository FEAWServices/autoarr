"""
Unit tests for WebSocket Manager service.

This module tests the WebSocketManager's ability to:
- Manage WebSocket connections
- Broadcast events to connected clients
- Handle subscriptions and event filtering
- Manage reconnections
- Track connection state
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = MagicMock(spec=WebSocket)
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.client_state = MagicMock()
    ws.client_state.name = "CONNECTED"
    return ws


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing integration."""
    mock = MagicMock()
    mock.publish = AsyncMock()
    mock.subscribe = AsyncMock()
    return mock


@pytest.fixture
def ws_manager(mock_event_bus):
    """Create WebSocketManager instance."""
    from autoarr.api.services.websocket_manager import WebSocketManager

    manager = WebSocketManager(event_bus=mock_event_bus)
    return manager


@pytest.fixture
def sample_event():
    """Create a sample WebSocket event."""
    return {
        "type": "request.created",
        "data": {
            "request_id": 123,
            "title": "Inception",
            "status": "pending",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": str(uuid.uuid4()),
    }


# ============================================================================
# Test Classes
# ============================================================================


class TestWebSocketManagerInitialization:
    """Tests for WebSocketManager initialization."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, mock_event_bus) -> None:
        """Test WebSocketManager initialization."""
        # Arrange & Act
        from autoarr.api.services.websocket_manager import WebSocketManager

        manager = WebSocketManager(event_bus=mock_event_bus)

        # Assert
        assert manager.event_bus is not None
        assert manager.connections == {}
        assert manager.subscriptions == {}

    @pytest.mark.asyncio
    async def test_manager_singleton_pattern(self, mock_event_bus) -> None:
        """Test manager uses singleton pattern."""
        # Arrange
        from autoarr.api.services.websocket_manager import get_websocket_manager

        # Act
        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()

        # Assert
        assert manager1 is manager2


class TestConnectionManagement:
    """Tests for WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connect_client(self, ws_manager, mock_websocket) -> None:
        """Test connecting a new client."""
        # Arrange
        connection_id = "test-conn-123"

        # Act
        await ws_manager.connect(connection_id, mock_websocket)

        # Assert
        assert connection_id in ws_manager.connections
        assert ws_manager.connections[connection_id]["websocket"] == mock_websocket
        assert "connected_at" in ws_manager.connections[connection_id]
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_client(self, ws_manager, mock_websocket) -> None:
        """Test disconnecting a client."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)

        # Act
        await ws_manager.disconnect(connection_id)

        # Assert
        assert connection_id not in ws_manager.connections
        assert connection_id not in ws_manager.subscriptions

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(self, ws_manager) -> None:
        """Test disconnecting a client that doesn't exist."""
        # Arrange
        connection_id = "nonexistent"

        # Act & Assert - Should not raise error
        await ws_manager.disconnect(connection_id)

    @pytest.mark.asyncio
    async def test_handle_multiple_connections(self, ws_manager) -> None:
        """Test managing multiple simultaneous connections."""
        # Arrange
        connections = []
        for i in range(10):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            connections.append((f"conn-{i}", ws))

        # Act
        for conn_id, ws in connections:
            await ws_manager.connect(conn_id, ws)

        # Assert
        assert len(ws_manager.connections) == 10
        for conn_id, _ in connections:
            assert conn_id in ws_manager.connections

    @pytest.mark.asyncio
    async def test_connection_state_tracking(self, ws_manager, mock_websocket) -> None:
        """Test tracking connection state."""
        # Arrange
        connection_id = "test-conn-123"

        # Act
        await ws_manager.connect(connection_id, mock_websocket)

        # Assert
        connection = ws_manager.connections[connection_id]
        assert connection["state"] == "connected"
        assert isinstance(connection["connected_at"], datetime)
        assert "last_activity" in connection

    @pytest.mark.asyncio
    async def test_update_last_activity(self, ws_manager, mock_websocket) -> None:
        """Test updating last activity timestamp."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)
        initial_activity = ws_manager.connections[connection_id]["last_activity"]

        # Act
        await asyncio.sleep(0.1)
        await ws_manager.update_activity(connection_id)

        # Assert
        updated_activity = ws_manager.connections[connection_id]["last_activity"]
        assert updated_activity > initial_activity


class TestEventBroadcasting:
    """Tests for event broadcasting to clients."""

    @pytest.mark.asyncio
    async def test_broadcast_to_all_clients(self, ws_manager, sample_event) -> None:
        """Test broadcasting event to all clients."""
        # Arrange
        websockets = []
        for i in range(5):
            ws = MagicMock(spec=WebSocket)
            ws.send_json = AsyncMock()
            ws.client_state.name = "CONNECTED"
            await ws_manager.connect(f"conn-{i}", ws)
            websockets.append(ws)

        # Act
        await ws_manager.broadcast(sample_event)

        # Assert
        for ws in websockets:
            ws.send_json.assert_called_once_with(sample_event)

    @pytest.mark.asyncio
    async def test_broadcast_to_specific_client(
        self, ws_manager, mock_websocket, sample_event
    ) -> None:
        """Test sending event to specific client."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)

        # Also connect another client that should NOT receive the message
        other_ws = MagicMock(spec=WebSocket)
        other_ws.send_json = AsyncMock()
        await ws_manager.connect("other-conn", other_ws)

        # Act
        await ws_manager.send_to_client(connection_id, sample_event)

        # Assert
        mock_websocket.send_json.assert_called_once_with(sample_event)
        other_ws.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_client(self, ws_manager, sample_event) -> None:
        """Test broadcasting when client disconnected during send."""
        # Arrange
        # Create a websocket that raises error on send
        failing_ws = MagicMock(spec=WebSocket)
        failing_ws.send_json = AsyncMock(side_effect=RuntimeError("Connection lost"))
        failing_ws.client_state.name = "DISCONNECTED"

        working_ws = MagicMock(spec=WebSocket)
        working_ws.send_json = AsyncMock()
        working_ws.client_state.name = "CONNECTED"

        await ws_manager.connect("failing-conn", failing_ws)
        await ws_manager.connect("working-conn", working_ws)

        # Act
        await ws_manager.broadcast(sample_event)

        # Assert
        # Failing connection should be removed
        assert "failing-conn" not in ws_manager.connections
        # Working connection should still receive message
        working_ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_event_serialization(self, ws_manager, mock_websocket) -> None:
        """Test event properly serialized to JSON."""
        # Arrange
        await ws_manager.connect("conn-1", mock_websocket)
        event = {
            "type": "request.status_changed",
            "data": {
                "request_id": 123,
                "status": "completed",
                "timestamp": datetime.now(timezone.utc),  # Should be serialized
            },
            "correlation_id": str(uuid.uuid4()),
        }

        # Act
        await ws_manager.broadcast(event)

        # Assert
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]
        # Verify timestamp was converted to ISO format
        assert isinstance(sent_data["data"]["timestamp"], str)

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections(self, ws_manager, sample_event) -> None:
        """Test broadcasting with no connected clients."""
        # Arrange - No connections

        # Act & Assert - Should not raise error
        await ws_manager.broadcast(sample_event)


class TestSubscriptionManagement:
    """Tests for event subscription and filtering."""

    @pytest.mark.asyncio
    async def test_subscribe_to_event_type(self, ws_manager, mock_websocket) -> None:
        """Test subscribing to specific event type."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)

        # Act
        await ws_manager.subscribe(connection_id, "request.status")

        # Assert
        assert connection_id in ws_manager.subscriptions
        assert "request.status" in ws_manager.subscriptions[connection_id]

    @pytest.mark.asyncio
    async def test_subscribe_to_multiple_event_types(self, ws_manager, mock_websocket) -> None:
        """Test subscribing to multiple event types."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)

        # Act
        await ws_manager.subscribe(connection_id, "request.status")
        await ws_manager.subscribe(connection_id, "download.progress")
        await ws_manager.subscribe(connection_id, "system.notification")

        # Assert
        subscriptions = ws_manager.subscriptions[connection_id]
        assert len(subscriptions) == 3
        assert "request.status" in subscriptions
        assert "download.progress" in subscriptions
        assert "system.notification" in subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_from_event_type(self, ws_manager, mock_websocket) -> None:
        """Test unsubscribing from event type."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)
        await ws_manager.subscribe(connection_id, "request.status")

        # Act
        await ws_manager.unsubscribe(connection_id, "request.status")

        # Assert
        subscriptions = ws_manager.subscriptions.get(connection_id, set())
        assert "request.status" not in subscriptions

    @pytest.mark.asyncio
    async def test_filter_events_by_subscription(self, ws_manager) -> None:
        """Test event filtering based on subscriptions."""
        # Arrange
        # Client 1: subscribed to request.* only
        ws1 = MagicMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws1.client_state.name = "CONNECTED"
        await ws_manager.connect("conn-1", ws1)
        await ws_manager.subscribe("conn-1", "request.*")

        # Client 2: subscribed to all events
        ws2 = MagicMock(spec=WebSocket)
        ws2.send_json = AsyncMock()
        ws2.client_state.name = "CONNECTED"
        await ws_manager.connect("conn-2", ws2)
        await ws_manager.subscribe("conn-2", "*")

        # Act
        await ws_manager.broadcast({"type": "request.created", "data": {}})
        await ws_manager.broadcast({"type": "download.progress", "data": {}})

        # Assert
        # ws1 should receive only request.created (1 call)
        assert ws1.send_json.call_count == 1
        # ws2 should receive both events (2 calls)
        assert ws2.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self, ws_manager, mock_websocket) -> None:
        """Test wildcard subscription (all events)."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)
        await ws_manager.subscribe(connection_id, "*")

        # Act
        events = [
            {"type": "request.created", "data": {}},
            {"type": "download.progress", "data": {}},
            {"type": "system.notification", "data": {}},
        ]
        for event in events:
            await ws_manager.broadcast(event)

        # Assert
        # All events should be sent
        assert mock_websocket.send_json.call_count == 3

    @pytest.mark.asyncio
    async def test_pattern_matching_subscription(self, ws_manager, mock_websocket) -> None:
        """Test pattern matching in subscriptions."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)
        await ws_manager.subscribe(connection_id, "request.*")

        # Act
        await ws_manager.broadcast({"type": "request.created", "data": {}})
        await ws_manager.broadcast({"type": "request.status_changed", "data": {}})
        await ws_manager.broadcast({"type": "download.progress", "data": {}})

        # Assert
        # Should receive 2 request.* events, not the download event
        assert mock_websocket.send_json.call_count == 2


class TestReconnectionHandling:
    """Tests for client reconnection handling."""

    @pytest.mark.asyncio
    async def test_handle_client_reconnect(self, ws_manager) -> None:
        """Test handling client reconnection."""
        # Arrange
        connection_id = "test-conn-123"
        old_ws = MagicMock(spec=WebSocket)
        old_ws.accept = AsyncMock()
        old_ws.close = AsyncMock()

        new_ws = MagicMock(spec=WebSocket)
        new_ws.accept = AsyncMock()

        # Act
        await ws_manager.connect(connection_id, old_ws)
        await ws_manager.disconnect(connection_id)
        await ws_manager.connect(connection_id, new_ws)

        # Assert
        assert connection_id in ws_manager.connections
        assert ws_manager.connections[connection_id]["websocket"] == new_ws

    @pytest.mark.asyncio
    async def test_connection_timeout_cleanup(self, ws_manager, mock_websocket) -> None:
        """Test connection timeout handling."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)

        # Manually set last_activity to simulate timeout
        from datetime import timedelta

        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        ws_manager.connections[connection_id]["last_activity"] = old_time

        # Act
        await ws_manager.cleanup_inactive_connections(timeout_minutes=5)

        # Assert
        assert connection_id not in ws_manager.connections


class TestErrorHandling:
    """Tests for error handling in WebSocket operations."""

    @pytest.mark.asyncio
    async def test_handle_websocket_send_error(self, ws_manager, sample_event) -> None:
        """Test handling WebSocket send errors."""
        # Arrange
        ws = MagicMock(spec=WebSocket)
        ws.send_json = AsyncMock(side_effect=RuntimeError("Send failed"))
        ws.client_state.name = "CONNECTED"
        await ws_manager.connect("conn-1", ws)

        # Act
        await ws_manager.broadcast(sample_event)

        # Assert
        # Connection should be removed after send failure
        assert "conn-1" not in ws_manager.connections

    @pytest.mark.asyncio
    async def test_handle_malformed_message(self, ws_manager, mock_websocket) -> None:
        """Test handling malformed incoming message."""
        # Arrange
        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, mock_websocket)

        # Act
        result = await ws_manager.handle_message(connection_id, "invalid json {")

        # Assert
        assert result["error"] is not None
        # Connection should still be active
        assert connection_id in ws_manager.connections

    @pytest.mark.asyncio
    async def test_handle_connection_closed_abruptly(self, ws_manager) -> None:
        """Test handling abrupt connection closure."""
        # Arrange
        ws = MagicMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock(side_effect=RuntimeError("Connection closed"))
        ws.client_state.name = "DISCONNECTED"

        connection_id = "test-conn-123"
        await ws_manager.connect(connection_id, ws)

        # Act
        await ws_manager.broadcast({"type": "test", "data": {}})

        # Assert
        # Should handle gracefully and remove connection
        assert connection_id not in ws_manager.connections


class TestPerformance:
    """Tests for WebSocket manager performance."""

    @pytest.mark.asyncio
    async def test_broadcast_performance(self, ws_manager, sample_event) -> None:
        """Test broadcast performance with many clients."""
        import time

        # Arrange - Create 100 mock connections
        for i in range(100):
            ws = MagicMock(spec=WebSocket)
            ws.send_json = AsyncMock()
            ws.client_state.name = "CONNECTED"
            await ws_manager.connect(f"conn-{i}", ws)

        # Act
        start_time = time.time()
        await ws_manager.broadcast(sample_event)
        elapsed_time = time.time() - start_time

        # Assert
        # Should complete in < 100ms
        assert elapsed_time < 0.1
        assert len(ws_manager.connections) == 100

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, ws_manager, sample_event) -> None:
        """Test concurrent connect/disconnect/broadcast."""

        # Arrange
        async def connect_client(i):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            ws.client_state.name = "CONNECTED"
            await ws_manager.connect(f"conn-{i}", ws)

        async def disconnect_client(i):
            await ws_manager.disconnect(f"conn-{i}")

        async def broadcast_event():
            await ws_manager.broadcast(sample_event)

        # Act - Run concurrent operations
        tasks = []
        for i in range(10):
            tasks.append(connect_client(i))
            tasks.append(broadcast_event())
            if i % 2 == 0:
                tasks.append(disconnect_client(i))

        await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - No race conditions, state is consistent
        assert isinstance(ws_manager.connections, dict)


class TestConnectionStatistics:
    """Tests for connection statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_connection_count(self, ws_manager) -> None:
        """Test getting active connection count."""
        # Arrange
        for i in range(5):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            await ws_manager.connect(f"conn-{i}", ws)

        # Act
        count = ws_manager.get_connection_count()

        # Assert
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_connection_stats(self, ws_manager) -> None:
        """Test getting detailed connection statistics."""
        # Arrange
        for i in range(3):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            await ws_manager.connect(f"conn-{i}", ws)
            await ws_manager.subscribe(f"conn-{i}", "request.*")

        # Act
        stats = ws_manager.get_stats()

        # Assert
        assert stats["total_connections"] == 3
        assert stats["total_subscriptions"] >= 3
        assert "uptime" in stats

    @pytest.mark.asyncio
    async def test_list_active_connections(self, ws_manager) -> None:
        """Test listing active connections."""
        # Arrange
        for i in range(3):
            ws = MagicMock(spec=WebSocket)
            ws.accept = AsyncMock()
            await ws_manager.connect(f"conn-{i}", ws)

        # Act
        connections = ws_manager.list_connections()

        # Assert
        assert len(connections) == 3
        assert all("connection_id" in conn for conn in connections)
        assert all("connected_at" in conn for conn in connections)
