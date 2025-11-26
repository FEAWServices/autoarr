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
Tests for health check endpoints.

This module tests the health check API endpoints for overall system health
and individual service health monitoring.
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
    mock._clients = {"sabnzbd": MagicMock(), "sonarr": MagicMock()}
    mock.get_connected_servers = MagicMock(return_value=["sabnzbd", "sonarr"])
    mock.health_check = AsyncMock(return_value=True)
    mock.get_circuit_breaker_state = MagicMock(return_value={"state": "closed", "failure_count": 0})
    mock.is_connected = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def override_orchestrator():
    """Helper to override orchestrator dependency."""

    def _override(mock_orchestrator):
        async def override_func():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_func

    return _override


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    reset_orchestrator()
    # Clear any dependency overrides
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_overall_health_check_healthy(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test overall health check when all services are healthy."""
        override_orchestrator(mock_orchestrator)

        # Make request
        response = client.get("/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "sabnzbd" in data["services"]
        assert "sonarr" in data["services"]
        assert data["services"]["sabnzbd"]["healthy"] is True
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_overall_health_check_degraded(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test overall health check when some services are unhealthy."""

        # Mock one service as unhealthy
        async def health_check_side_effect(server):
            return server == "sabnzbd"

        mock_orchestrator.health_check.side_effect = health_check_side_effect
        override_orchestrator(mock_orchestrator)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["sabnzbd"]["healthy"] is True
        assert data["services"]["sonarr"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_overall_health_check_no_services(self, client, override_orchestrator):
        """Test overall health check when no services are connected (fresh install)."""
        mock_orch = MagicMock()
        mock_orch._clients = {}  # No clients connected
        mock_orch.get_connected_servers = MagicMock(return_value=[])  # No servers

        override_orchestrator(mock_orch)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # Fresh install with no services should be healthy (awaiting configuration)
        assert data["status"] == "healthy"
        assert data["services"] == {}

    @pytest.mark.asyncio
    async def test_service_health_check_success(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test individual service health check for healthy service."""
        override_orchestrator(mock_orchestrator)

        response = client.get("/health/sabnzbd")

        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is True
        assert "latency_ms" in data
        assert data["error"] is None
        assert "last_check" in data
        assert data["circuit_breaker_state"] == "closed"

    @pytest.mark.asyncio
    async def test_service_health_check_invalid_service(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test service health check with invalid service name."""
        override_orchestrator(mock_orchestrator)

        response = client.get("/health/invalid_service")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid service name" in data["detail"]

    @pytest.mark.asyncio
    async def test_service_health_check_not_connected(self, client, override_orchestrator):
        """Test service health check when service is not connected."""
        mock_orch = MagicMock()
        mock_orch._clients = {}  # radarr not in clients = not connected

        override_orchestrator(mock_orch)

        response = client.get("/health/radarr")

        assert response.status_code == 503
        data = response.json()
        assert "not connected" in data["detail"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_status(self, client, mock_orchestrator, override_orchestrator):
        """Test circuit breaker status endpoint."""
        mock_orchestrator.get_circuit_breaker_state.return_value = {
            "state": "open",
            "failure_count": 5,
            "threshold": 5,
            "timeout": 60.0,
        }

        override_orchestrator(mock_orchestrator)

        response = client.get("/health/circuit-breaker/sabnzbd")

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "open"
        assert data["failure_count"] == 5
        assert data["threshold"] == 5

    @pytest.mark.asyncio
    async def test_circuit_breaker_status_invalid_service(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test circuit breaker status with invalid service name."""
        override_orchestrator(mock_orchestrator)

        response = client.get("/health/circuit-breaker/invalid")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid service name" in data["detail"]

    @pytest.mark.asyncio
    async def test_health_check_includes_latency(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test that health check includes latency measurement."""
        override_orchestrator(mock_orchestrator)

        response = client.get("/health/sabnzbd")

        assert response.status_code == 200
        data = response.json()
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], (int, float))
        assert data["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_service(
        self, client, mock_orchestrator, override_orchestrator
    ):
        """Test health check for unhealthy service."""
        mock_orchestrator.health_check = AsyncMock(return_value=False)

        override_orchestrator(mock_orchestrator)

        response = client.get("/health/sabnzbd")

        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is False
        assert data["latency_ms"] is None
        assert data["error"] is not None
