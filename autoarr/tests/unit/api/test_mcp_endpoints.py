"""
Tests for MCP proxy endpoints.

This module tests the MCP proxy API endpoints for calling tools,
batch operations, and tool discovery.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from autoarr.api.dependencies import get_orchestrator, reset_orchestrator
from autoarr.api.main import app


@pytest.fixture
def client(mock_database_init):
    """Create a test client with database mocking."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    mock = MagicMock()
    mock.call_tool = AsyncMock()
    mock.call_tools_parallel = AsyncMock()
    mock.list_tools = AsyncMock()
    mock.list_all_tools = AsyncMock()
    mock.get_stats = MagicMock()
    return mock


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    reset_orchestrator()
    # Clear dependency overrides after each test
    app.dependency_overrides.clear()


class TestMCPEndpoints:
    """Test MCP proxy endpoints."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self, client, mock_orchestrator):
        """Test successful tool call."""
        mock_orchestrator.call_tool.return_value = {
            "data": {"queue": []},
            "metadata": {
                "server": "sabnzbd",
                "tool": "get_queue",
                "duration": 0.123,
            },
        }

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/call",
            json={
                "server": "sabnzbd",
                "tool": "get_queue",
                "params": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data
        assert data["error"] is None

    @pytest.mark.asyncio
    async def test_call_tool_with_timeout(self, client, mock_orchestrator):
        """Test tool call with custom timeout."""
        mock_orchestrator.call_tool.return_value = {"result": "ok"}

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/call",
            json={
                "server": "sabnzbd",
                "tool": "get_queue",
                "params": {},
                "timeout": 60.0,
            },
        )

        assert response.status_code == 200
        # Verify timeout was passed to call_tool
        mock_orchestrator.call_tool.assert_called_once()
        call_args = mock_orchestrator.call_tool.call_args
        assert call_args.kwargs.get("timeout") == 60.0

    @pytest.mark.asyncio
    async def test_call_tool_error(self, client, mock_orchestrator):
        """Test tool call that fails."""
        mock_orchestrator.call_tool.side_effect = Exception("Tool execution failed")

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/call",
            json={
                "server": "sabnzbd",
                "tool": "get_queue",
                "params": {},
            },
        )

        assert response.status_code == 200  # Still returns 200, error in body
        data = response.json()
        assert data["success"] is False
        assert data["error"] is not None
        assert "Tool execution failed" in data["error"]

    @pytest.mark.asyncio
    async def test_batch_tool_call_success(self, client, mock_orchestrator):
        """Test successful batch tool call."""
        mock_orchestrator.call_tools_parallel.return_value = [
            {"success": True, "data": {"queue": []}, "error": None},
            {"success": True, "data": {"series": []}, "error": None},
        ]

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/batch",
            json={
                "calls": [
                    {"server": "sabnzbd", "tool": "get_queue", "params": {}},
                    {"server": "sonarr", "tool": "get_series", "params": {}},
                ],
                "return_partial": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["success"] is True
        assert data[1]["success"] is True

    @pytest.mark.asyncio
    async def test_batch_tool_call_with_failures(self, client, mock_orchestrator):
        """Test batch tool call with some failures."""
        mock_orchestrator.call_tools_parallel.return_value = [
            {"success": True, "data": {"queue": []}, "error": None},
            {"success": False, "data": None, "error": "Connection failed"},
        ]

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/batch",
            json={
                "calls": [
                    {"server": "sabnzbd", "tool": "get_queue", "params": {}},
                    {"server": "sonarr", "tool": "get_series", "params": {}},
                ],
                "return_partial": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["success"] is True
        assert data[1]["success"] is False
        assert data[1]["error"] is not None

    @pytest.mark.asyncio
    async def test_list_all_tools(self, client, mock_orchestrator):
        """Test listing all available tools."""
        mock_orchestrator.list_all_tools.return_value = {
            "sabnzbd": ["get_queue", "get_history", "retry_download"],
            "sonarr": ["get_series", "search_series"],
        }

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.get("/api/v1/mcp/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "sabnzbd" in data["tools"]
        assert "sonarr" in data["tools"]
        assert len(data["tools"]["sabnzbd"]) == 3

    @pytest.mark.asyncio
    async def test_list_server_tools(self, client, mock_orchestrator):
        """Test listing tools for specific server."""
        mock_orchestrator.list_tools.return_value = [
            "get_queue",
            "get_history",
            "retry_download",
        ]

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.get("/api/v1/mcp/tools/sabnzbd")

        assert response.status_code == 200
        data = response.json()
        assert data["server"] == "sabnzbd"
        assert "tools" in data
        assert len(data["tools"]) == 3

    @pytest.mark.asyncio
    async def test_get_stats(self, client, mock_orchestrator):
        """Test getting orchestrator statistics."""
        mock_orchestrator.get_stats.return_value = {
            "total_calls": 150,
            "total_health_checks": 45,
            "calls_per_server": {
                "sabnzbd": 50,
                "sonarr": 60,
                "radarr": 40,
            },
        }

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.get("/api/v1/mcp/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 150
        assert data["total_health_checks"] == 45
        assert "calls_per_server" in data

    @pytest.mark.asyncio
    async def test_call_tool_with_params(self, client, mock_orchestrator):
        """Test tool call with parameters."""
        mock_orchestrator.call_tool.return_value = {"result": "success"}

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/call",
            json={
                "server": "sabnzbd",
                "tool": "retry_download",
                "params": {"nzo_id": "SABnzbd_nzo_abc123"},
            },
        )

        assert response.status_code == 200
        # Verify params were passed correctly
        mock_orchestrator.call_tool.assert_called_once()
        call_args = mock_orchestrator.call_tool.call_args
        assert call_args.kwargs.get("params") == {"nzo_id": "SABnzbd_nzo_abc123"}

    @pytest.mark.asyncio
    async def test_call_tool_raw_data_response(self, client, mock_orchestrator):
        """Test tool call with raw data response (no metadata)."""
        mock_orchestrator.call_tool.return_value = {"queue": []}

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/call",
            json={
                "server": "sabnzbd",
                "tool": "get_queue",
                "params": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_batch_call_empty_list(self, client, mock_orchestrator):
        """Test batch call with empty call list."""
        mock_orchestrator.call_tools_parallel.return_value = []

        async def override_get_orchestrator():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_get_orchestrator

        response = client.post(
            "/api/v1/mcp/batch",
            json={
                "calls": [],
                "return_partial": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []
