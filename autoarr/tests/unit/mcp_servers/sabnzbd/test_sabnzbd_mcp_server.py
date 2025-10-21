"""
Unit tests for SABnzbd MCP Server.

This module tests the SABnzbd MCP server that exposes SABnzbd operations as MCP tools.
These tests follow TDD principles and ensure the MCP server correctly translates tool calls
to SABnzbd API operations.

Test Coverage Strategy:
- MCP server initialization and setup
- Tool registration and listing
- Tool execution for each MCP tool
- Input validation and error handling
- Response formatting
- Integration with SABnzbd client

Target Coverage: 100% for the SABnzbd MCP server class
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from autoarr.mcp_servers.mcp_servers.sabnzbd.client import (
    SABnzbdClient,
    SABnzbdClientError,
    SABnzbdConnectionError,
)

# Import the actual MCP server and client
from autoarr.mcp_servers.mcp_servers.sabnzbd.server import SABnzbdMCPServer

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_sabnzbd_client():
    """Create a mock SABnzbd client for testing."""
    client = Mock(spec=SABnzbdClient)  # noqa: F841
    client.url = "http://localhost:8080"
    client.api_key = "test_api_key"

    # Mock all client methods as AsyncMock
    client.get_queue = AsyncMock()
    client.get_history = AsyncMock()
    client.retry_download = AsyncMock()
    client.get_config = AsyncMock()
    client.set_config = AsyncMock()
    client.get_version = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    client.close = AsyncMock()

    return client


@pytest.fixture
def sabnzbd_mcp_server(mock_sabnzbd_client):
    """Create a SABnzbd MCP server instance for testing."""
    return SABnzbdMCPServer(client=mock_sabnzbd_client)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestSABnzbdMCPServerInitialization:
    """Test suite for MCP server initialization."""

    def test_server_requires_client(self) -> None:
        """Test that server initialization requires a client."""
        with pytest.raises(ValueError, match="client"):
            SABnzbdMCPServer(client=None)

    def test_server_initializes_with_valid_client(self, mock_sabnzbd_client) -> None:
        """Test that server initializes correctly with a valid client."""
        server = SABnzbdMCPServer(client=mock_sabnzbd_client)

        assert server.client == mock_sabnzbd_client  # noqa: F841
        assert server.name == "sabnzbd"
        assert server.version == "0.1.0"

    def test_server_creates_mcp_server_instance(self, sabnzbd_mcp_server) -> None:
        """Test that server creates an MCP Server instance."""
        assert sabnzbd_mcp_server._server is not None

    @pytest.mark.asyncio
    async def test_server_start_validates_connection(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that server.start() validates connection to SABnzbd."""
        mock_sabnzbd_client.health_check.return_value = True

        await sabnzbd_mcp_server.start()

        mock_sabnzbd_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_start_fails_if_unhealthy(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that server.start() fails if SABnzbd is unreachable."""
        mock_sabnzbd_client.health_check.return_value = False

        with pytest.raises(SABnzbdClientError, match="Failed to connect"):
            await sabnzbd_mcp_server.start()

    @pytest.mark.asyncio
    async def test_server_stop_closes_client(self, mock_sabnzbd_client, sabnzbd_mcp_server) -> None:
        """Test that server.stop() closes the client connection."""
        await sabnzbd_mcp_server.stop()

        mock_sabnzbd_client.close.assert_called_once()


# ============================================================================
# Tool Registration Tests
# ============================================================================


class TestSABnzbdMCPServerToolRegistration:
    """Test suite for tool registration and listing."""

    def test_list_tools_returns_all_tools(self, sabnzbd_mcp_server) -> None:
        """Test that list_tools returns all available tools."""
        tools = sabnzbd_mcp_server.list_tools()

        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]

        assert "sabnzbd_get_queue" in tool_names
        assert "sabnzbd_get_history" in tool_names
        assert "sabnzbd_retry_download" in tool_names
        assert "sabnzbd_get_config" in tool_names
        assert "sabnzbd_set_config" in tool_names

    def test_get_queue_tool_has_correct_schema(self, sabnzbd_mcp_server) -> None:
        """Test that get_queue tool has correct input schema."""
        tool = sabnzbd_mcp_server.get_tool("sabnzbd_get_queue")

        assert tool is not None
        assert tool.name == "sabnzbd_get_queue"
        assert "queue" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "start" in schema["properties"]
        assert "limit" in schema["properties"]
        assert schema["required"] == []

    def test_get_history_tool_has_correct_schema(self, sabnzbd_mcp_server) -> None:
        """Test that get_history tool has correct input schema."""
        tool = sabnzbd_mcp_server.get_tool("sabnzbd_get_history")

        assert tool is not None
        assert tool.name == "sabnzbd_get_history"
        assert "history" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert "start" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "failed_only" in schema["properties"]
        assert "category" in schema["properties"]

    def test_retry_download_tool_has_correct_schema(self, sabnzbd_mcp_server) -> None:
        """Test that retry_download tool has correct input schema."""
        tool = sabnzbd_mcp_server.get_tool("sabnzbd_retry_download")

        assert tool is not None
        assert tool.name == "sabnzbd_retry_download"
        assert "retry" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert "nzo_id" in schema["properties"]
        assert schema["required"] == ["nzo_id"]

    def test_get_config_tool_has_correct_schema(self, sabnzbd_mcp_server) -> None:
        """Test that get_config tool has correct input schema."""
        tool = sabnzbd_mcp_server.get_tool("sabnzbd_get_config")

        assert tool is not None
        assert tool.name == "sabnzbd_get_config"
        assert "config" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert "section" in schema["properties"]
        assert schema["required"] == []

    def test_set_config_tool_has_correct_schema(self, sabnzbd_mcp_server) -> None:
        """Test that set_config tool has correct input schema."""
        tool = sabnzbd_mcp_server.get_tool("sabnzbd_set_config")

        assert tool is not None
        assert tool.name == "sabnzbd_set_config"
        assert "config" in tool.description.lower()

        # Check input schema
        schema = tool.inputSchema
        assert "section" in schema["properties"]
        assert "keyword" in schema["properties"]
        assert "value" in schema["properties"]
        assert schema["required"] == ["section", "keyword", "value"]

    def test_get_tool_returns_none_for_unknown_tool(self, sabnzbd_mcp_server) -> None:
        """Test that get_tool returns None for unknown tool names."""
        tool = sabnzbd_mcp_server.get_tool("unknown_tool")

        assert tool is None


# ============================================================================
# Tool Execution Tests - Get Queue
# ============================================================================


class TestSABnzbdMCPServerGetQueue:
    """Test suite for get_queue tool execution."""

    @pytest.mark.asyncio
    async def test_get_queue_with_default_params(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_queue_factory
    ) -> None:
        """Test get_queue with default parameters."""
        mock_queue = sabnzbd_queue_factory(slots=2)
        mock_sabnzbd_client.get_queue.return_value = mock_queue

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        # Verify client was called correctly
        mock_sabnzbd_client.get_queue.assert_called_once_with(start=0, limit=None)

        # Verify result format
        assert not result.isError
        assert len(result.content) == 1

        # Parse JSON response
        response_data = json.loads(result.content[0].text)
        assert "queue" in response_data
        assert response_data["queue"]["noofslots"] == 2

    @pytest.mark.asyncio
    async def test_get_queue_with_pagination(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_queue_factory
    ) -> None:
        """Test get_queue with pagination parameters."""
        mock_queue = sabnzbd_queue_factory(slots=1)
        mock_sabnzbd_client.get_queue.return_value = mock_queue

        await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {"start": 10, "limit": 20})

        mock_sabnzbd_client.get_queue.assert_called_once_with(start=10, limit=20)

    @pytest.mark.asyncio
    async def test_get_queue_validates_start_parameter(self, sabnzbd_mcp_server) -> None:
        """Test that get_queue validates start parameter."""
        result = await sabnzbd_mcp_server.call_tool(
            "sabnzbd_get_queue", {"start": -1}
        )  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data
        assert "start" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_get_queue_validates_limit_parameter(self, sabnzbd_mcp_server) -> None:
        """Test that get_queue validates limit parameter."""
        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {"limit": 0})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data
        assert "limit" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_get_queue_handles_client_error(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that get_queue handles SABnzbd client errors."""
        mock_sabnzbd_client.get_queue.side_effect = SABnzbdClientError("Connection failed")

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data
        assert "Connection failed" in response_data["error"]


# ============================================================================
# Tool Execution Tests - Get History
# ============================================================================


class TestSABnzbdMCPServerGetHistory:
    """Test suite for get_history tool execution."""

    @pytest.mark.asyncio
    async def test_get_history_with_default_params(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_history_factory
    ) -> None:
        """Test get_history with default parameters."""
        mock_history = sabnzbd_history_factory(entries=3, failed=1)
        mock_sabnzbd_client.get_history.return_value = mock_history

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_history", {})  # noqa: F841

        # Verify client was called correctly
        mock_sabnzbd_client.get_history.assert_called_once_with(
            start=0, limit=None, failed_only=False, category=None
        )

        # Verify result format
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert "history" in response_data

    @pytest.mark.asyncio
    async def test_get_history_with_all_params(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_history_factory
    ) -> None:
        """Test get_history with all parameters."""
        mock_history = sabnzbd_history_factory(entries=2, failed=2)
        mock_sabnzbd_client.get_history.return_value = mock_history

        await sabnzbd_mcp_server.call_tool(
            "sabnzbd_get_history", {"start": 5, "limit": 10, "failed_only": True, "category": "tv"}
        )

        mock_sabnzbd_client.get_history.assert_called_once_with(
            start=5, limit=10, failed_only=True, category="tv"
        )

    @pytest.mark.asyncio
    async def test_get_history_validates_start_parameter(self, sabnzbd_mcp_server) -> None:
        """Test that get_history validates start parameter."""
        result = await sabnzbd_mcp_server.call_tool(
            "sabnzbd_get_history", {"start": -5}
        )  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_get_history_validates_failed_only_parameter(self, sabnzbd_mcp_server) -> None:
        """Test that get_history validates failed_only parameter."""
        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_get_history", {"failed_only": "not_a_boolean"}
        )

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data


# ============================================================================
# Tool Execution Tests - Retry Download
# ============================================================================


class TestSABnzbdMCPServerRetryDownload:
    """Test suite for retry_download tool execution."""

    @pytest.mark.asyncio
    async def test_retry_download_with_valid_nzo_id(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_nzo_action_factory
    ) -> None:
        """Test retry_download with valid NZO ID."""
        mock_action = sabnzbd_nzo_action_factory(success=True, nzo_ids=["new_nzo_123"])
        mock_sabnzbd_client.retry_download.return_value = mock_action

        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_retry_download", {"nzo_id": "failed_nzo_456"}
        )

        # Verify client was called correctly
        mock_sabnzbd_client.retry_download.assert_called_once_with(nzo_id="failed_nzo_456")

        # Verify result format
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert response_data["status"] is True

    @pytest.mark.asyncio
    async def test_retry_download_requires_nzo_id(self, sabnzbd_mcp_server) -> None:
        """Test that retry_download requires nzo_id parameter."""
        result = await sabnzbd_mcp_server.call_tool("sabnzbd_retry_download", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data
        assert "nzo_id" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_retry_download_validates_nzo_id(self, sabnzbd_mcp_server) -> None:
        """Test that retry_download validates nzo_id parameter."""
        result = await sabnzbd_mcp_server.call_tool(
            "sabnzbd_retry_download", {"nzo_id": ""}
        )  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_retry_download_handles_client_error(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that retry_download handles SABnzbd client errors."""
        mock_sabnzbd_client.retry_download.side_effect = SABnzbdClientError("Download not found")

        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_retry_download", {"nzo_id": "invalid_nzo"}
        )

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "Download not found" in response_data["error"]


# ============================================================================
# Tool Execution Tests - Get Config
# ============================================================================


class TestSABnzbdMCPServerGetConfig:
    """Test suite for get_config tool execution."""

    @pytest.mark.asyncio
    async def test_get_config_without_section(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_config_factory
    ) -> None:
        """Test get_config without section parameter (returns all config)."""
        mock_config = sabnzbd_config_factory()
        mock_sabnzbd_client.get_config.return_value = mock_config

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_config", {})  # noqa: F841

        # Verify client was called correctly
        mock_sabnzbd_client.get_config.assert_called_once_with(section=None)

        # Verify result format
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert "config" in response_data
        assert "misc" in response_data["config"]

    @pytest.mark.asyncio
    async def test_get_config_with_section(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_config_factory
    ) -> None:
        """Test get_config with specific section parameter."""
        mock_config = sabnzbd_config_factory()
        mock_sabnzbd_client.get_config.return_value = mock_config

        await sabnzbd_mcp_server.call_tool("sabnzbd_get_config", {"section": "misc"})

        mock_sabnzbd_client.get_config.assert_called_once_with(section="misc")

    @pytest.mark.asyncio
    async def test_get_config_handles_client_error(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that get_config handles SABnzbd client errors."""
        mock_sabnzbd_client.get_config.side_effect = SABnzbdClientError("Access denied")

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_config", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "Access denied" in response_data["error"]


# ============================================================================
# Tool Execution Tests - Set Config
# ============================================================================


class TestSABnzbdMCPServerSetConfig:
    """Test suite for set_config tool execution."""

    @pytest.mark.asyncio
    async def test_set_config_with_valid_params(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test set_config with valid parameters."""
        mock_sabnzbd_client.set_config.return_value = {"status": True}

        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_set_config", {"section": "misc", "keyword": "cache_limit", "value": "1000M"}
        )

        # Verify client was called correctly
        mock_sabnzbd_client.set_config.assert_called_once_with(
            section="misc", keyword="cache_limit", value="1000M"
        )

        # Verify result format
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert response_data["status"] is True

    @pytest.mark.asyncio
    async def test_set_config_requires_section(self, sabnzbd_mcp_server) -> None:
        """Test that set_config requires section parameter."""
        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_set_config", {"keyword": "key", "value": "val"}
        )

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data
        assert "section" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_set_config_requires_keyword(self, sabnzbd_mcp_server) -> None:
        """Test that set_config requires keyword parameter."""
        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_set_config", {"section": "misc", "value": "val"}
        )

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "keyword" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_set_config_requires_value(self, sabnzbd_mcp_server) -> None:
        """Test that set_config requires value parameter."""
        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_set_config", {"section": "misc", "keyword": "key"}
        )

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "value" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_set_config_validates_empty_section(self, sabnzbd_mcp_server) -> None:
        """Test that set_config validates empty section."""
        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_set_config", {"section": "", "keyword": "key", "value": "val"}
        )

        assert result.isError

    @pytest.mark.asyncio
    async def test_set_config_handles_client_error(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that set_config handles SABnzbd client errors."""
        mock_sabnzbd_client.set_config.side_effect = SABnzbdClientError("Invalid setting")

        result = await sabnzbd_mcp_server.call_tool(  # noqa: F841
            "sabnzbd_set_config", {"section": "misc", "keyword": "invalid", "value": "val"}
        )

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "Invalid setting" in response_data["error"]


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSABnzbdMCPServerErrorHandling:
    """Test suite for error handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, sabnzbd_mcp_server) -> None:
        """Test that calling an unknown tool returns an error."""
        result = await sabnzbd_mcp_server.call_tool("unknown_tool", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "Unknown tool" in response_data["error"]

    @pytest.mark.asyncio
    async def test_handles_unexpected_exceptions(
        self, mock_sabnzbd_client, sabnzbd_mcp_server
    ) -> None:
        """Test that server handles unexpected exceptions gracefully."""
        mock_sabnzbd_client.get_queue.side_effect = Exception("Unexpected error")

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "Unexpected error" in response_data["error"]

    @pytest.mark.asyncio
    async def test_handles_connection_errors(self, mock_sabnzbd_client, sabnzbd_mcp_server) -> None:
        """Test that server handles connection errors."""
        mock_sabnzbd_client.get_queue.side_effect = SABnzbdConnectionError("Connection timeout")

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "Connection timeout" in response_data["error"]


# ============================================================================
# Response Formatting Tests
# ============================================================================


class TestSABnzbdMCPServerResponseFormatting:
    """Test suite for response formatting."""

    @pytest.mark.asyncio
    async def test_success_response_format(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_queue_factory
    ) -> None:
        """Test that successful responses are formatted correctly."""
        mock_queue = sabnzbd_queue_factory(slots=1)
        mock_sabnzbd_client.get_queue.return_value = mock_queue

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        # Check TextContent format
        assert len(result.content) == 1
        assert result.content[0].type == "text"

        # Check JSON is valid and pretty-printed
        response_text = result.content[0].text
        response_data = json.loads(response_text)
        assert response_data is not None

        # Verify indentation (pretty-print)
        assert "\n" in response_text

    @pytest.mark.asyncio
    async def test_error_response_format(self, mock_sabnzbd_client, sabnzbd_mcp_server) -> None:
        """Test that error responses are formatted correctly."""
        mock_sabnzbd_client.get_queue.side_effect = SABnzbdClientError("Test error")

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841

        # Check TextContent format
        assert len(result.content) == 1
        assert result.content[0].type == "text"

        # Check error structure
        response_data = json.loads(result.content[0].text)
        assert "error" in response_data
        assert "success" in response_data
        assert response_data["success"] is False
        assert response_data["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_response_includes_full_data(
        self, mock_sabnzbd_client, sabnzbd_mcp_server, sabnzbd_queue_factory
    ) -> None:
        """Test that responses include full data from SABnzbd."""
        mock_queue = sabnzbd_queue_factory(slots=3, paused=True)
        mock_sabnzbd_client.get_queue.return_value = mock_queue

        result = await sabnzbd_mcp_server.call_tool("sabnzbd_get_queue", {})  # noqa: F841
        response_data = json.loads(result.content[0].text)

        # Verify all queue data is included
        assert "queue" in response_data
        assert response_data["queue"]["noofslots"] == 3
        assert response_data["queue"]["paused"] is True
        assert len(response_data["queue"]["slots"]) == 3
