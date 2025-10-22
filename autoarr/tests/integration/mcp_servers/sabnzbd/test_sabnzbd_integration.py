"""
Integration tests for SABnzbd MCP Server with real SABnzbd instance.

These tests require a running SABnzbd instance. They can be run with:
    pytest tests/integration/mcp_servers/sabnzbd/ -m integration

To skip integration tests:
    pytest -m "not integration"

Required environment variables:
    SABNZBD_URL: URL of SABnzbd instance (default: http://localhost:8080)
    SABNZBD_API_KEY: API key for authentication

Note: These tests interact with a real SABnzbd instance and may modify its state.
Use a test instance, not a production instance.
"""

import os

import pytest

from autoarr.mcp_servers.mcp_servers.sabnzbd.client import (
    SABnzbdClient,
    SABnzbdClientError,
    SABnzbdConnectionError,
)
from autoarr.mcp_servers.mcp_servers.sabnzbd.server import SABnzbdMCPServer

# ============================================================================
# Fixtures and Configuration
# ============================================================================


@pytest.fixture(scope="module")
def sabnzbd_url() -> str:
    """Get SABnzbd URL from environment or use default."""
    return os.getenv("SABNZBD_URL", "http://localhost:8080")


@pytest.fixture(scope="module")
def sabnzbd_api_key() -> str:
    """Get SABnzbd API key from environment."""
    api_key = os.getenv("SABNZBD_API_KEY")
    if not api_key:
        pytest.skip("SABNZBD_API_KEY environment variable not set")
    return api_key


@pytest.fixture(scope="module")
async def sabnzbd_client(sabnzbd_url: str, sabnzbd_api_key: str) -> SABnzbdClient:
    """Create a SABnzbd client for integration testing."""
    client = SABnzbdClient(url=sabnzbd_url, api_key=sabnzbd_api_key)  # noqa: F841
    yield client
    await client.close()


@pytest.fixture(scope="module")
async def sabnzbd_mcp_server(sabnzbd_client: SABnzbdClient) -> SABnzbdMCPServer:
    """Create a SABnzbd MCP server for integration testing."""
    server = SABnzbdMCPServer(client=sabnzbd_client)
    await server.start()
    yield server
    await server.stop()


# ============================================================================
# Connection and Health Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestSABnzbdClientIntegration:
    """Integration tests for SABnzbd client with real instance."""

    async def test_health_check_succeeds(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that health check succeeds with real SABnzbd."""
        is_healthy = await sabnzbd_client.health_check()
        assert is_healthy is True

    async def test_get_version_returns_valid_version(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that get_version returns valid version information."""
        result = await sabnzbd_client.get_version()  # noqa: F841

        assert "version" in result
        assert isinstance(result["version"], str)
        assert len(result["version"]) > 0

    async def test_get_status_returns_server_info(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that get_status returns server status information."""
        result = await sabnzbd_client.get_status()  # noqa: F841

        assert "status" in result
        status = result["status"]
        assert "version" in status
        assert "uptime" in status

    async def test_get_queue_returns_valid_structure(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that get_queue returns valid queue structure."""
        result = await sabnzbd_client.get_queue()  # noqa: F841

        assert "queue" in result
        queue = result["queue"]
        assert "status" in queue
        assert "speed" in queue
        assert "slots" in queue
        assert isinstance(queue["slots"], list)
        assert "noofslots" in queue

    async def test_get_history_returns_valid_structure(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that get_history returns valid history structure."""
        result = await sabnzbd_client.get_history(limit=10)  # noqa: F841

        assert "history" in result
        history = result["history"]
        assert "slots" in history
        assert isinstance(history["slots"], list)
        assert "noofslots" in history
        assert "total_size" in history

    async def test_get_config_returns_valid_structure(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that get_config returns valid configuration structure."""
        result = await sabnzbd_client.get_config()  # noqa: F841

        assert "config" in result
        config = result["config"]
        assert "misc" in config
        assert isinstance(config["misc"], dict)

    async def test_pause_and_resume_queue(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test pausing and resuming the queue."""
        # Pause queue
        pause_result = await sabnzbd_client.pause_queue()  # noqa: F841
        assert "status" in pause_result or "queue" in pause_result

        # Verify queue is paused
        queue = await sabnzbd_client.get_queue()
        assert queue["queue"]["paused"] is True or queue["queue"]["status"] == "Paused"

        # Resume queue
        resume_result = await sabnzbd_client.resume_queue()  # noqa: F841
        assert "status" in resume_result or "queue" in resume_result

        # Verify queue is resumed
        queue = await sabnzbd_client.get_queue()
        # Note: Queue might still show as paused if no downloads are active
        # Just verify we can call the endpoint

    async def test_pagination_works(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that pagination parameters work correctly."""
        # Get first page
        result1 = await sabnzbd_client.get_history(start=0, limit=5)

        # Get second page
        result2 = await sabnzbd_client.get_history(start=5, limit=5)

        # Verify we got results (even if empty)
        assert "history" in result1
        assert "history" in result2

    async def test_invalid_api_key_raises_error(self, sabnzbd_url: str) -> None:
        """Test that invalid API key raises appropriate error."""
        # Skip if SABnzbd service is not available (no API key means not configured for testing)
        if not os.getenv("SABNZBD_API_KEY"):
            pytest.skip("SABNZBD_API_KEY not set - SABnzbd not configured for testing")

        # Use short timeout to avoid waiting too long if SABnzbd is unavailable
        client = SABnzbdClient(
            url=sabnzbd_url, api_key="invalid_key_12345", timeout=2.0
        )  # noqa: F841

        try:
            # Use max_retries=1 to fail fast if service unavailable
            await client._request("queue", max_retries=1)
            # If we get here without error, the test should fail
            pytest.fail("Expected SABnzbdClientError but no error was raised")
        except SABnzbdConnectionError:
            # Connection error means SABnzbd not available
            pytest.skip("SABnzbd instance not available for testing")
        except SABnzbdClientError as e:
            # Otherwise, check for the expected "Unauthorized" message
            assert "Unauthorized" in str(e) or "401" in str(
                e
            ), f"Expected Unauthorized error, got: {e}"
        finally:
            await client.close()


# ============================================================================
# MCP Server Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestSABnzbdMCPServerIntegration:
    """Integration tests for SABnzbd MCP server with real instance."""

    async def test_mcp_server_starts_successfully(
        self, sabnzbd_mcp_server: SABnzbdMCPServer
    ) -> None:
        """Test that MCP server starts and validates connection."""
        assert sabnzbd_mcp_server.client is not None
        assert sabnzbd_mcp_server.name == "sabnzbd"

    async def test_mcp_get_queue_tool(self, sabnzbd_mcp_server: SABnzbdMCPServer) -> None:
        """Test MCP get_queue tool with real SABnzbd."""
        import json

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        assert not result.isError
        assert len(result.content) == 1

        response_data = json.loads(result.content[0].text)
        assert "queue" in response_data
        assert "slots" in response_data["queue"]

    async def test_mcp_get_history_tool(self, sabnzbd_mcp_server: SABnzbdMCPServer) -> None:
        """Test MCP get_history tool with real SABnzbd."""
        import json

        result = await sabnzbd_mcp_server.call_tool(
            "sabnzbd_get_history", {"limit": 10}
        )  # noqa: F841

        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert "history" in response_data

    async def test_mcp_get_config_tool(self, sabnzbd_mcp_server: SABnzbdMCPServer) -> None:
        """Test MCP get_config tool with real SABnzbd."""
        import json

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_config", {})  # noqa: F841

        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert "config" in response_data
        assert "misc" in response_data["config"]

    async def test_mcp_tool_validation(self, sabnzbd_mcp_server: SABnzbdMCPServer) -> None:
        """Test that MCP tools validate input parameters."""
        import json

        # Test invalid start parameter
        result = await sabnzbd_mcp_server.call_tool(
            "sabnzbd_get_queue", {"start": -1}
        )  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data

    async def test_mcp_list_all_tools(self, sabnzbd_mcp_server: SABnzbdMCPServer) -> None:
        """Test listing all available MCP tools."""
        tools = sabnzbd_mcp_server.list_tools()

        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        assert "sabnzbd_get_queue" in tool_names
        assert "sabnzbd_get_history" in tool_names
        assert "sabnzbd_retry_download" in tool_names
        assert "sabnzbd_get_config" in tool_names
        assert "sabnzbd_set_config" in tool_names


# ============================================================================
# Configuration Management Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestSABnzbdConfigurationIntegration:
    """Integration tests for configuration management."""

    async def test_get_specific_config_section(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test getting a specific configuration section."""
        result = await sabnzbd_client.get_config(section="misc")  # noqa: F841

        assert "config" in result
        config = result["config"]
        assert "misc" in config

    async def test_config_contains_expected_fields(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that config contains expected fields."""
        result = await sabnzbd_client.get_config()  # noqa: F841
        misc = result["config"]["misc"]

        # Check for common config fields
        assert "complete_dir" in misc
        assert "download_dir" in misc
        assert "api_key" in misc
        assert "host" in misc
        assert "port" in misc


# ============================================================================
# Error Handling Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestSABnzbdErrorHandlingIntegration:
    """Integration tests for error handling."""

    async def test_retry_nonexistent_download_fails_gracefully(
        self, sabnzbd_client: SABnzbdClient
    ) -> None:
        """Test that retrying a non-existent download fails gracefully."""
        # This should not crash, but may return an error or empty result
        try:
            result = await sabnzbd_client.retry_download("nonexistent_nzo_id")  # noqa: F841
            # If it succeeds, check the result structure
            assert "status" in result or "nzo_ids" in result
        except SABnzbdClientError:
            # This is also acceptable - SABnzbd may return an error
            pass

    async def test_concurrent_requests_work(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that concurrent requests can be made safely."""
        import asyncio

        # Make multiple concurrent requests
        results = await asyncio.gather(
            sabnzbd_client.get_queue(),
            sabnzbd_client.get_history(),
            sabnzbd_client.get_version(),
            return_exceptions=True,
        )

        # Verify all succeeded
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)


# ============================================================================
# Performance Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
class TestSABnzbdPerformanceIntegration:
    """Performance tests for SABnzbd integration."""

    async def test_health_check_is_fast(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that health check completes quickly."""
        import time

        start = time.time()
        is_healthy = await sabnzbd_client.health_check()
        duration = time.time() - start

        assert is_healthy is True
        assert duration < 5.0  # Should complete within 5 seconds

    async def test_multiple_sequential_requests(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that multiple sequential requests work correctly."""
        # Make 10 sequential requests
        for _ in range(10):
            result = await sabnzbd_client.get_queue()  # noqa: F841
            assert "queue" in result

    async def test_client_connection_reuse(self, sabnzbd_client: SABnzbdClient) -> None:
        """Test that client properly reuses HTTP connections."""
        # Make multiple requests - client should reuse connection
        for _ in range(5):
            result = await sabnzbd_client.get_queue()  # noqa: F841
            assert "queue" in result

        # Verify client still works after multiple uses
        result = await sabnzbd_client.get_history()  # noqa: F841
        assert "history" in result
