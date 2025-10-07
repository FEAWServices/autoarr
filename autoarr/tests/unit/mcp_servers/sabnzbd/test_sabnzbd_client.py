"""
Unit tests for SABnzbd API Client.

This module tests the SABnzbd API client wrapper that handles all HTTP communication
with the SABnzbd API. These tests follow TDD principles and should be written BEFORE
the implementation.

Test Coverage Strategy:
- Connection and authentication
- All API endpoints (queue, history, config, actions)
- Error handling and retries
- Response parsing and validation
- Edge cases and boundary conditions

Target Coverage: 95%+ for the SABnzbd client class
"""

import json
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import AsyncClient, HTTPError, HTTPStatusError, Response
from pytest_httpx import HTTPXMock

# Import the actual client - using new repository structure
from autoarr.mcp_servers.mcp_servers.sabnzbd.client import (
    SABnzbdClient,
    SABnzbdClientError,
    SABnzbdConnectionError,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sabnzbd_url() -> str:
    """Return a test SABnzbd URL."""
    return "http://localhost:8080"


@pytest.fixture
def sabnzbd_api_key() -> str:
    """Return a test API key."""
    return "test_api_key_12345"


@pytest.fixture
def sabnzbd_client(sabnzbd_url: str, sabnzbd_api_key: str):
    """Create a SABnzbd client instance for testing."""
    return SABnzbdClient(url=sabnzbd_url, api_key=sabnzbd_api_key)


# ============================================================================
# Connection and Initialization Tests
# ============================================================================


class TestSABnzbdClientInitialization:
    """Test suite for client initialization and connection."""

    def test_client_requires_url(self, sabnzbd_api_key: str) -> None:
        """Test that client initialization requires a URL."""
        with pytest.raises((ValueError, TypeError)):
            SABnzbdClient(url="", api_key=sabnzbd_api_key)

    def test_client_requires_api_key(self, sabnzbd_url: str) -> None:
        """Test that client initialization requires an API key."""
        with pytest.raises(ValueError):
            SABnzbdClient(url=sabnzbd_url, api_key="")

    def test_client_normalizes_url(self, sabnzbd_api_key: str) -> None:
        """Test that client normalizes URLs (removes trailing slash)."""
        client = SABnzbdClient(url="http://localhost:8080/", api_key=sabnzbd_api_key)
        assert client.url == "http://localhost:8080"

    def test_client_accepts_custom_timeout(self, sabnzbd_url: str, sabnzbd_api_key: str) -> None:
        """Test that client accepts custom timeout values."""
        client = SABnzbdClient(url=sabnzbd_url, api_key=sabnzbd_api_key, timeout=60.0)
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_client_validates_connection_on_init(
        self, httpx_mock: HTTPXMock, sabnzbd_url: str, sabnzbd_api_key: str
    ) -> None:
        """Test that client optionally validates connection on initialization."""
        httpx_mock.add_response(
            url=f"{sabnzbd_url}/api?mode=version&output=json&apikey={sabnzbd_api_key}",
            json={"version": "4.1.0"},
        )
        client = await SABnzbdClient.create(
            url=sabnzbd_url, api_key=sabnzbd_api_key, validate_connection=True
        )
        assert client is not None


# ============================================================================
# Queue Operations Tests
# ============================================================================


class TestSABnzbdClientQueue:
    """Test suite for queue-related operations."""

    @pytest.mark.asyncio
    async def test_get_queue_returns_queue_data(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_queue_factory: callable
    ) -> None:
        """Test that get_queue returns valid queue data."""
        mock_queue = sabnzbd_queue_factory(slots=3)
        httpx_mock.add_response(json=mock_queue)

        result = await sabnzbd_client.get_queue()

        assert "queue" in result
        assert result["queue"]["noofslots"] == 3
        assert len(result["queue"]["slots"]) == 3

    @pytest.mark.asyncio
    async def test_get_queue_handles_empty_queue(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_queue_factory: callable
    ) -> None:
        """Test that get_queue handles empty queue correctly."""
        mock_queue = sabnzbd_queue_factory(slots=0)
        httpx_mock.add_response(json=mock_queue)

        result = await sabnzbd_client.get_queue()

        assert result["queue"]["noofslots"] == 0
        assert result["queue"]["slots"] == []

    @pytest.mark.asyncio
    async def test_get_queue_includes_pagination_params(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that get_queue supports start and limit parameters."""
        httpx_mock.add_response(json={"queue": {"slots": []}})

        await sabnzbd_client.get_queue(start=10, limit=20)

        request = httpx_mock.get_request()
        assert "start=10" in str(request.url)
        assert "limit=20" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_queue_with_nzo_ids_filter(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that get_queue can filter by specific NZO IDs."""
        httpx_mock.add_response(json={"queue": {"slots": []}})

        await sabnzbd_client.get_queue(nzo_ids=["id1", "id2"])

        request = httpx_mock.get_request()
        assert "nzo_ids=" in str(request.url)

    @pytest.mark.asyncio
    async def test_pause_queue_sends_correct_command(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that pause_queue sends the correct API command."""
        httpx_mock.add_response(json={"status": True})

        result = await sabnzbd_client.pause_queue()

        request = httpx_mock.get_request()
        assert "mode=pause" in str(request.url)
        assert result["status"] is True

    @pytest.mark.asyncio
    async def test_resume_queue_sends_correct_command(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that resume_queue sends the correct API command."""
        httpx_mock.add_response(json={"status": True})

        result = await sabnzbd_client.resume_queue()

        request = httpx_mock.get_request()
        assert "mode=resume" in str(request.url)


# ============================================================================
# History Operations Tests
# ============================================================================


class TestSABnzbdClientHistory:
    """Test suite for history-related operations."""

    @pytest.mark.asyncio
    async def test_get_history_returns_history_data(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_history_factory: callable
    ) -> None:
        """Test that get_history returns valid history data."""
        mock_history = sabnzbd_history_factory(entries=5, failed=2)
        httpx_mock.add_response(json=mock_history)

        result = await sabnzbd_client.get_history()

        assert "history" in result
        assert result["history"]["noofslots"] == 5

    @pytest.mark.asyncio
    async def test_get_history_supports_pagination(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that get_history supports start and limit parameters."""
        httpx_mock.add_response(json={"history": {"slots": []}})

        await sabnzbd_client.get_history(start=0, limit=50)

        request = httpx_mock.get_request()
        assert "start=0" in str(request.url)
        assert "limit=50" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_history_filters_by_failed_only(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that get_history can filter to show only failed downloads."""
        httpx_mock.add_response(json={"history": {"slots": []}})

        await sabnzbd_client.get_history(failed_only=True)

        request = httpx_mock.get_request()
        assert "failed_only=1" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_history_filters_by_category(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that get_history can filter by category."""
        httpx_mock.add_response(json={"history": {"slots": []}})

        await sabnzbd_client.get_history(category="tv")

        request = httpx_mock.get_request()
        assert "category=tv" in str(request.url)


# ============================================================================
# Download Management Tests
# ============================================================================


class TestSABnzbdClientDownloadManagement:
    """Test suite for download management operations."""

    @pytest.mark.asyncio
    async def test_retry_download_by_nzo_id(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test retrying a failed download by NZO ID."""
        httpx_mock.add_response(json={"status": True, "nzo_ids": ["new_id"]})

        result = await sabnzbd_client.retry_download(nzo_id="failed_nzo_123")

        request = httpx_mock.get_request()
        assert "mode=retry" in str(request.url)
        assert "value=failed_nzo_123" in str(request.url)
        assert result["status"] is True

    @pytest.mark.asyncio
    async def test_retry_download_validates_nzo_id(self, sabnzbd_client) -> None:
        """Test that retry_download validates NZO ID parameter."""
        with pytest.raises(ValueError, match="nzo_id"):
            await sabnzbd_client.retry_download(nzo_id="")

    @pytest.mark.asyncio
    async def test_delete_download_by_nzo_id(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test deleting a download by NZO ID."""
        httpx_mock.add_response(json={"status": True})

        result = await sabnzbd_client.delete_download(nzo_id="nzo_123", delete_files=True)

        request = httpx_mock.get_request()
        assert "mode=queue" in str(request.url)
        assert "name=delete" in str(request.url)
        assert "value=nzo_123" in str(request.url)
        assert "del_files=1" in str(request.url)

    @pytest.mark.asyncio
    async def test_pause_download_by_nzo_id(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test pausing a specific download."""
        httpx_mock.add_response(json={"status": True})

        result = await sabnzbd_client.pause_download(nzo_id="nzo_123")

        request = httpx_mock.get_request()
        assert "mode=queue" in str(request.url)
        assert "name=pause" in str(request.url)
        assert "value=nzo_123" in str(request.url)

    @pytest.mark.asyncio
    async def test_resume_download_by_nzo_id(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test resuming a paused download."""
        httpx_mock.add_response(json={"status": True})

        result = await sabnzbd_client.resume_download(nzo_id="nzo_123")

        request = httpx_mock.get_request()
        assert "mode=queue" in str(request.url)
        assert "name=resume" in str(request.url)


# ============================================================================
# Configuration Tests
# ============================================================================


class TestSABnzbdClientConfiguration:
    """Test suite for configuration operations."""

    @pytest.mark.asyncio
    async def test_get_config_returns_full_config(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_config_factory: callable
    ) -> None:
        """Test that get_config returns complete configuration."""
        mock_config = sabnzbd_config_factory()
        httpx_mock.add_response(json=mock_config)

        result = await sabnzbd_client.get_config()

        assert "config" in result
        assert "misc" in result["config"]
        assert "servers" in result["config"]
        assert "categories" in result["config"]

    @pytest.mark.asyncio
    async def test_get_config_section_returns_specific_section(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_config_factory: callable
    ) -> None:
        """Test that get_config can retrieve specific config sections."""
        mock_config = sabnzbd_config_factory()
        httpx_mock.add_response(json=mock_config)

        result = await sabnzbd_client.get_config(section="misc")

        assert "misc" in result["config"]

    @pytest.mark.asyncio
    async def test_set_config_updates_single_value(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test updating a single configuration value."""
        httpx_mock.add_response(json={"status": True})

        result = await sabnzbd_client.set_config(
            section="misc", keyword="cache_limit", value="1000M"
        )

        request = httpx_mock.get_request()
        assert "mode=set_config" in str(request.url)
        assert "section=misc" in str(request.url)
        assert "keyword=cache_limit" in str(request.url)
        assert "value=1000M" in str(request.url)

    @pytest.mark.asyncio
    async def test_set_config_validates_parameters(self, sabnzbd_client) -> None:
        """Test that set_config validates required parameters."""
        with pytest.raises(ValueError):
            await sabnzbd_client.set_config(section="", keyword="key", value="val")

    @pytest.mark.asyncio
    async def test_set_config_batch_updates_multiple_values(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test batch updating multiple configuration values."""
        httpx_mock.add_response(json={"status": True})

        config_updates = {
            "misc.cache_limit": "1000M",
            "misc.refresh_rate": 2,
        }
        result = await sabnzbd_client.set_config_batch(config_updates)

        assert result["status"] is True


# ============================================================================
# Status and Information Tests
# ============================================================================


class TestSABnzbdClientStatus:
    """Test suite for status and information operations."""

    @pytest.mark.asyncio
    async def test_get_version_returns_version_info(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that get_version returns SABnzbd version."""
        httpx_mock.add_response(json={"version": "4.1.0"})

        result = await sabnzbd_client.get_version()

        assert result["version"] == "4.1.0"

    @pytest.mark.asyncio
    async def test_get_status_returns_server_status(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_status_factory: callable
    ) -> None:
        """Test that get_status returns complete server status."""
        mock_status = sabnzbd_status_factory()
        httpx_mock.add_response(json=mock_status)

        result = await sabnzbd_client.get_status()

        assert "status" in result
        assert "version" in result["status"]
        assert "uptime" in result["status"]

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that health_check returns True when SABnzbd is accessible."""
        httpx_mock.add_response(json={"version": "4.1.0"})

        is_healthy = await sabnzbd_client.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_unreachable(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that health_check returns False when SABnzbd is unreachable."""
        httpx_mock.add_exception(HTTPError("Connection failed"))

        is_healthy = await sabnzbd_client.health_check()

        assert is_healthy is False


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSABnzbdClientErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_401_unauthorized_error(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test handling of 401 Unauthorized (invalid API key)."""
        httpx_mock.add_response(status_code=401, json={"error": "Unauthorized"})

        with pytest.raises(SABnzbdClientError, match="Unauthorized"):
            await sabnzbd_client.get_queue()

    @pytest.mark.asyncio
    async def test_handles_500_server_error(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test handling of 500 Internal Server Error."""
        httpx_mock.add_response(status_code=500, text="Internal Server Error")

        with pytest.raises(SABnzbdClientError, match="Server error"):
            await sabnzbd_client.get_queue()

    @pytest.mark.asyncio
    async def test_handles_connection_timeout(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test handling of connection timeout."""
        httpx_mock.add_exception(HTTPError("Timeout"))

        with pytest.raises(SABnzbdConnectionError, match="Timeout"):
            await sabnzbd_client.get_queue()

    @pytest.mark.asyncio
    async def test_handles_network_error(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test handling of network connection error."""
        httpx_mock.add_exception(HTTPError("Connection refused"))

        with pytest.raises(SABnzbdConnectionError, match="Connection refused"):
            await sabnzbd_client.get_queue()

    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test handling of invalid JSON in response."""
        httpx_mock.add_response(text="Not valid JSON{")

        with pytest.raises(SABnzbdClientError, match="Invalid JSON"):
            await sabnzbd_client.get_queue()

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test that client retries on transient errors."""
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(json={"queue": {"slots": []}})

        result = await sabnzbd_client.get_queue()

        assert result is not None
        assert len(httpx_mock.get_requests()) == 2  # Two attempts

    @pytest.mark.asyncio
    async def test_respects_max_retries(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test that client respects max retry limit."""
        for _ in range(5):
            httpx_mock.add_response(status_code=503)

        with pytest.raises(SABnzbdClientError):
            await sabnzbd_client.get_queue()
        assert len(httpx_mock.get_requests()) == 3  # Max 3 attempts


# ============================================================================
# URL Building and Request Tests
# ============================================================================


class TestSABnzbdClientRequestBuilding:
    """Test suite for URL building and request formatting."""

    @pytest.mark.asyncio
    async def test_builds_correct_api_url(
        self, httpx_mock: HTTPXMock, sabnzbd_url: str, sabnzbd_api_key: str
    ) -> None:
        """Test that API URLs are built correctly."""
        httpx_mock.add_response(json={"queue": {"slots": []}})

        client = SABnzbdClient(url=sabnzbd_url, api_key=sabnzbd_api_key)
        await client.get_queue()

        request = httpx_mock.get_request()
        assert str(request.url).startswith(sabnzbd_url)
        assert f"apikey={sabnzbd_api_key}" in str(request.url)
        assert "output=json" in str(request.url)

    @pytest.mark.asyncio
    async def test_includes_api_key_in_all_requests(
        self, httpx_mock: HTTPXMock, sabnzbd_client, sabnzbd_api_key: str
    ) -> None:
        """Test that all requests include the API key."""
        httpx_mock.add_response(json={})

        await sabnzbd_client.get_queue()

        request = httpx_mock.get_request()
        assert f"apikey={sabnzbd_api_key}" in str(request.url)

    @pytest.mark.asyncio
    async def test_encodes_url_parameters_correctly(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that URL parameters are properly encoded."""
        httpx_mock.add_response(json={})

        await sabnzbd_client.set_config(
            section="misc", keyword="test key", value="test value with spaces"
        )

        request = httpx_mock.get_request()
        assert "test+key" in str(request.url) or "test%20key" in str(request.url)


# ============================================================================
# Performance and Resource Management Tests
# ============================================================================


class TestSABnzbdClientResourceManagement:
    """Test suite for resource management and performance."""

    @pytest.mark.asyncio
    async def test_client_properly_closes_connections(self, sabnzbd_client) -> None:
        """Test that client properly closes HTTP connections."""
        async with sabnzbd_client:
            # Client should manage its own AsyncClient
            pass

    @pytest.mark.asyncio
    async def test_client_reuses_http_client(self, httpx_mock: HTTPXMock, sabnzbd_client) -> None:
        """Test that client reuses the same HTTP client for multiple requests."""
        httpx_mock.add_response(json={"queue": {"slots": []}})
        httpx_mock.add_response(json={"history": {"slots": []}})

        await sabnzbd_client.get_queue()
        await sabnzbd_client.get_history()

    @pytest.mark.asyncio
    async def test_concurrent_requests_dont_conflict(
        self, httpx_mock: HTTPXMock, sabnzbd_client
    ) -> None:
        """Test that concurrent requests can be made safely."""
        import asyncio

        httpx_mock.add_response(json={"queue": {"slots": []}})
        httpx_mock.add_response(json={"history": {"slots": []}})
        httpx_mock.add_response(json={"config": {}})

        results = await asyncio.gather(
            sabnzbd_client.get_queue(),
            sabnzbd_client.get_history(),
            sabnzbd_client.get_config(),
        )

        assert len(results) == 3
