"""
Unit tests for SABnzbd MCP Server.

This module tests the MCP server implementation that exposes SABnzbd functionality
through the Model Context Protocol. These tests verify tool registration, execution,
error handling, and MCP protocol compliance.

Test Coverage Strategy:
- MCP server initialization and lifecycle
- Tool registration and discovery
- Tool execution and parameter validation
- Response formatting and error handling
- MCP protocol compliance
- Integration with SABnzbd client

Target Coverage: 95%+ for the MCP server implementation
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# These imports will fail initially - that's expected in TDD!
# from mcp import Tool, Server
# from mcp_servers.sabnzbd.mcp_server import SABnzbdMCPServer
# from mcp_servers.sabnzbd.client import SABnzbdClient


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
def mock_sabnzbd_client(sabnzbd_url: str, sabnzbd_api_key: str):
    """Create a mock SABnzbd client."""
    client = AsyncMock()
    client.url = sabnzbd_url
    client.api_key = sabnzbd_api_key
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mcp_server(mock_sabnzbd_client):
    """Create an MCP server instance for testing."""
    pytest.skip("SABnzbdMCPServer not yet implemented - TDD red phase")
    # return SABnzbdMCPServer(client=mock_sabnzbd_client)


# ============================================================================
# Server Initialization Tests
# ============================================================================


class TestSABnzbdMCPServerInitialization:
    """Test suite for MCP server initialization."""

    def test_server_requires_client(self) -> None:
        """Test that server initialization requires a SABnzbd client."""
        pytest.skip("Implementation pending - TDD")
        # with pytest.raises(ValueError):
        #     SABnzbdMCPServer(client=None)

    def test_server_initializes_with_client(self, mock_sabnzbd_client) -> None:
        """Test successful server initialization with client."""
        pytest.skip("Implementation pending - TDD")
        # server = SABnzbdMCPServer(client=mock_sabnzbd_client)
        # assert server.client == mock_sabnzbd_client

    def test_server_has_correct_name(self, mcp_server) -> None:
        """Test that server has the correct name."""
        pytest.skip("Implementation pending - TDD")
        # assert mcp_server.name == "sabnzbd"

    def test_server_has_correct_version(self, mcp_server) -> None:
        """Test that server has a version identifier."""
        pytest.skip("Implementation pending - TDD")
        # assert mcp_server.version is not None
        # assert isinstance(mcp_server.version, str)

    @pytest.mark.asyncio
    async def test_server_validates_connection_on_startup(self, mock_sabnzbd_client) -> None:
        """Test that server validates SABnzbd connection on startup."""
        pytest.skip("Implementation pending - TDD")
        # server = SABnzbdMCPServer(client=mock_sabnzbd_client)
        # await server.start()

        # mock_sabnzbd_client.health_check.assert_called_once()


# ============================================================================
# Tool Registration Tests
# ============================================================================


class TestSABnzbdMCPServerToolRegistration:
    """Test suite for tool registration and discovery."""

    def test_server_registers_get_queue_tool(self, mcp_server) -> None:
        """Test that get_queue tool is registered."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # tool_names = [tool.name for tool in tools]
        # assert "sabnzbd_get_queue" in tool_names

    def test_server_registers_get_history_tool(self, mcp_server) -> None:
        """Test that get_history tool is registered."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # tool_names = [tool.name for tool in tools]
        # assert "sabnzbd_get_history" in tool_names

    def test_server_registers_retry_download_tool(self, mcp_server) -> None:
        """Test that retry_download tool is registered."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # tool_names = [tool.name for tool in tools]
        # assert "sabnzbd_retry_download" in tool_names

    def test_server_registers_get_config_tool(self, mcp_server) -> None:
        """Test that get_config tool is registered."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # tool_names = [tool.name for tool in tools]
        # assert "sabnzbd_get_config" in tool_names

    def test_server_registers_set_config_tool(self, mcp_server) -> None:
        """Test that set_config tool is registered."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # tool_names = [tool.name for tool in tools]
        # assert "sabnzbd_set_config" in tool_names

    def test_server_registers_exactly_five_tools(self, mcp_server) -> None:
        """Test that server registers exactly 5 tools as specified."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # assert len(tools) == 5

    def test_all_tools_have_descriptions(self, mcp_server) -> None:
        """Test that all registered tools have descriptions."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # for tool in tools:
        #     assert tool.description is not None
        #     assert len(tool.description) > 0

    def test_all_tools_have_schemas(self, mcp_server) -> None:
        """Test that all registered tools have input schemas."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # for tool in tools:
        #     assert tool.inputSchema is not None


# ============================================================================
# Tool: get_queue Tests
# ============================================================================


class TestSABnzbdMCPServerGetQueueTool:
    """Test suite for the get_queue tool."""

    def test_get_queue_tool_has_correct_schema(self, mcp_server) -> None:
        """Test that get_queue tool has correct input schema."""
        pytest.skip("Implementation pending - TDD")
        # tool = mcp_server.get_tool("sabnzbd_get_queue")
        # schema = tool.inputSchema
        # assert "properties" in schema
        # Optional parameters: start, limit

    @pytest.mark.asyncio
    async def test_get_queue_calls_client_get_queue(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_queue_factory: callable
    ) -> None:
        """Test that get_queue tool calls client.get_queue()."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_queue = sabnzbd_queue_factory(slots=3)
        # mock_sabnzbd_client.get_queue = AsyncMock(return_value=mock_queue)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})

        # Assert
        # mock_sabnzbd_client.get_queue.assert_called_once()
        # assert "queue" in result.content[0].text  # MCP returns text content

    @pytest.mark.asyncio
    async def test_get_queue_passes_parameters_to_client(
        self, mcp_server, mock_sabnzbd_client
    ) -> None:
        """Test that get_queue passes parameters to client."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.get_queue = AsyncMock(return_value={"queue": {"slots": []}})

        # Act
        # await mcp_server.call_tool(
        #     "sabnzbd_get_queue",
        #     {"start": 10, "limit": 20}
        # )

        # Assert
        # mock_sabnzbd_client.get_queue.assert_called_once_with(start=10, limit=20)

    @pytest.mark.asyncio
    async def test_get_queue_formats_response_as_json_string(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_queue_factory: callable
    ) -> None:
        """Test that get_queue returns formatted JSON string."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_queue = sabnzbd_queue_factory(slots=2)
        # mock_sabnzbd_client.get_queue = AsyncMock(return_value=mock_queue)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})

        # Assert
        # assert result.isError is False
        # import json
        # parsed = json.loads(result.content[0].text)
        # assert "queue" in parsed

    @pytest.mark.asyncio
    async def test_get_queue_handles_empty_queue(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_queue_factory: callable
    ) -> None:
        """Test that get_queue handles empty queue correctly."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_queue = sabnzbd_queue_factory(slots=0)
        # mock_sabnzbd_client.get_queue = AsyncMock(return_value=mock_queue)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})

        # Assert
        # assert result.isError is False


# ============================================================================
# Tool: get_history Tests
# ============================================================================


class TestSABnzbdMCPServerGetHistoryTool:
    """Test suite for the get_history tool."""

    def test_get_history_tool_has_correct_schema(self, mcp_server) -> None:
        """Test that get_history tool has correct input schema."""
        pytest.skip("Implementation pending - TDD")
        # tool = mcp_server.get_tool("sabnzbd_get_history")
        # schema = tool.inputSchema
        # assert "properties" in schema
        # Parameters: start, limit, failed_only, category

    @pytest.mark.asyncio
    async def test_get_history_calls_client_get_history(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_history_factory: callable
    ) -> None:
        """Test that get_history tool calls client.get_history()."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_history = sabnzbd_history_factory(entries=5)
        # mock_sabnzbd_client.get_history = AsyncMock(return_value=mock_history)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_history", {})

        # Assert
        # mock_sabnzbd_client.get_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_supports_failed_only_filter(
        self, mcp_server, mock_sabnzbd_client
    ) -> None:
        """Test that get_history supports failed_only parameter."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.get_history = AsyncMock(return_value={"history": {"slots": []}})

        # Act
        # await mcp_server.call_tool(
        #     "sabnzbd_get_history",
        #     {"failed_only": True}
        # )

        # Assert
        # mock_sabnzbd_client.get_history.assert_called_once_with(failed_only=True)

    @pytest.mark.asyncio
    async def test_get_history_supports_category_filter(
        self, mcp_server, mock_sabnzbd_client
    ) -> None:
        """Test that get_history supports category parameter."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.get_history = AsyncMock(return_value={"history": {"slots": []}})

        # Act
        # await mcp_server.call_tool(
        #     "sabnzbd_get_history",
        #     {"category": "tv"}
        # )

        # Assert
        # mock_sabnzbd_client.get_history.assert_called_once_with(category="tv")


# ============================================================================
# Tool: retry_download Tests
# ============================================================================


class TestSABnzbdMCPServerRetryDownloadTool:
    """Test suite for the retry_download tool."""

    def test_retry_download_tool_requires_nzo_id(self, mcp_server) -> None:
        """Test that retry_download requires nzo_id parameter."""
        pytest.skip("Implementation pending - TDD")
        # tool = mcp_server.get_tool("sabnzbd_retry_download")
        # schema = tool.inputSchema
        # assert "nzo_id" in schema["required"]

    @pytest.mark.asyncio
    async def test_retry_download_calls_client_retry(self, mcp_server, mock_sabnzbd_client) -> None:
        """Test that retry_download calls client.retry_download()."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.retry_download = AsyncMock(
        #     return_value={"status": True, "nzo_ids": ["new_id"]}
        # )

        # Act
        # result = await mcp_server.call_tool(
        #     "sabnzbd_retry_download",
        #     {"nzo_id": "failed_nzo_123"}
        # )

        # Assert
        # mock_sabnzbd_client.retry_download.assert_called_once_with(nzo_id="failed_nzo_123")

    @pytest.mark.asyncio
    async def test_retry_download_validates_nzo_id_parameter(self, mcp_server) -> None:
        """Test that retry_download validates nzo_id parameter."""
        pytest.skip("Implementation pending - TDD")
        # Act & Assert
        # result = await mcp_server.call_tool(
        #     "sabnzbd_retry_download",
        #     {"nzo_id": ""}
        # )
        # assert result.isError is True

    @pytest.mark.asyncio
    async def test_retry_download_returns_success_status(
        self, mcp_server, mock_sabnzbd_client
    ) -> None:
        """Test that retry_download returns success status."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.retry_download = AsyncMock(
        #     return_value={"status": True, "nzo_ids": ["new_id"]}
        # )

        # Act
        # result = await mcp_server.call_tool(
        #     "sabnzbd_retry_download",
        #     {"nzo_id": "failed_nzo_123"}
        # )

        # Assert
        # assert result.isError is False
        # import json
        # parsed = json.loads(result.content[0].text)
        # assert parsed["status"] is True


# ============================================================================
# Tool: get_config Tests
# ============================================================================


class TestSABnzbdMCPServerGetConfigTool:
    """Test suite for the get_config tool."""

    def test_get_config_tool_has_optional_section_param(self, mcp_server) -> None:
        """Test that get_config has optional section parameter."""
        pytest.skip("Implementation pending - TDD")
        # tool = mcp_server.get_tool("sabnzbd_get_config")
        # schema = tool.inputSchema
        # assert "section" in schema.get("properties", {})

    @pytest.mark.asyncio
    async def test_get_config_calls_client_get_config(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_config_factory: callable
    ) -> None:
        """Test that get_config calls client.get_config()."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_config = sabnzbd_config_factory()
        # mock_sabnzbd_client.get_config = AsyncMock(return_value=mock_config)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_config", {})

        # Assert
        # mock_sabnzbd_client.get_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_config_supports_section_filter(
        self, mcp_server, mock_sabnzbd_client
    ) -> None:
        """Test that get_config supports section parameter."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.get_config = AsyncMock(return_value={"config": {"misc": {}}})

        # Act
        # await mcp_server.call_tool(
        #     "sabnzbd_get_config",
        #     {"section": "misc"}
        # )

        # Assert
        # mock_sabnzbd_client.get_config.assert_called_once_with(section="misc")

    @pytest.mark.asyncio
    async def test_get_config_returns_complete_config(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_config_factory: callable
    ) -> None:
        """Test that get_config returns complete configuration."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_config = sabnzbd_config_factory()
        # mock_sabnzbd_client.get_config = AsyncMock(return_value=mock_config)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_config", {})

        # Assert
        # import json
        # parsed = json.loads(result.content[0].text)
        # assert "config" in parsed


# ============================================================================
# Tool: set_config Tests
# ============================================================================


class TestSABnzbdMCPServerSetConfigTool:
    """Test suite for the set_config tool."""

    def test_set_config_tool_requires_parameters(self, mcp_server) -> None:
        """Test that set_config requires section, keyword, and value."""
        pytest.skip("Implementation pending - TDD")
        # tool = mcp_server.get_tool("sabnzbd_set_config")
        # schema = tool.inputSchema
        # required = schema.get("required", [])
        # assert "section" in required
        # assert "keyword" in required
        # assert "value" in required

    @pytest.mark.asyncio
    async def test_set_config_calls_client_set_config(
        self, mcp_server, mock_sabnzbd_client
    ) -> None:
        """Test that set_config calls client.set_config()."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.set_config = AsyncMock(return_value={"status": True})

        # Act
        # await mcp_server.call_tool(
        #     "sabnzbd_set_config",
        #     {"section": "misc", "keyword": "cache_limit", "value": "1000M"}
        # )

        # Assert
        # mock_sabnzbd_client.set_config.assert_called_once_with(
        #     section="misc",
        #     keyword="cache_limit",
        #     value="1000M"
        # )

    @pytest.mark.asyncio
    async def test_set_config_validates_required_parameters(self, mcp_server) -> None:
        """Test that set_config validates required parameters."""
        pytest.skip("Implementation pending - TDD")
        # Act & Assert: Missing value
        # result = await mcp_server.call_tool(
        #     "sabnzbd_set_config",
        #     {"section": "misc", "keyword": "cache_limit"}
        # )
        # assert result.isError is True

    @pytest.mark.asyncio
    async def test_set_config_returns_success_status(self, mcp_server, mock_sabnzbd_client) -> None:
        """Test that set_config returns success status."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_sabnzbd_client.set_config = AsyncMock(return_value={"status": True})

        # Act
        # result = await mcp_server.call_tool(
        #     "sabnzbd_set_config",
        #     {"section": "misc", "keyword": "cache_limit", "value": "1000M"}
        # )

        # Assert
        # assert result.isError is False


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSABnzbdMCPServerErrorHandling:
    """Test suite for error handling in MCP server."""

    @pytest.mark.asyncio
    async def test_handles_client_error_gracefully(self, mcp_server, mock_sabnzbd_client) -> None:
        """Test that server handles client errors gracefully."""
        pytest.skip("Implementation pending - TDD")
        # from mcp_servers.sabnzbd.client import SABnzbdClientError

        # Arrange
        # mock_sabnzbd_client.get_queue = AsyncMock(
        #     side_effect=SABnzbdClientError("Connection failed")
        # )

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})

        # Assert
        # assert result.isError is True
        # assert "Connection failed" in result.content[0].text

    @pytest.mark.asyncio
    async def test_handles_invalid_tool_name(self, mcp_server) -> None:
        """Test that server handles invalid tool names."""
        pytest.skip("Implementation pending - TDD")
        # Act
        # result = await mcp_server.call_tool("invalid_tool", {})

        # Assert
        # assert result.isError is True

    @pytest.mark.asyncio
    async def test_handles_invalid_parameters(self, mcp_server) -> None:
        """Test that server validates tool parameters."""
        pytest.skip("Implementation pending - TDD")
        # Act: Pass wrong type for parameter
        # result = await mcp_server.call_tool(
        #     "sabnzbd_get_queue",
        #     {"start": "not_a_number"}
        # )

        # Assert
        # assert result.isError is True

    @pytest.mark.asyncio
    async def test_handles_missing_required_parameters(self, mcp_server) -> None:
        """Test that server validates required parameters."""
        pytest.skip("Implementation pending - TDD")
        # Act: Missing required nzo_id
        # result = await mcp_server.call_tool("sabnzbd_retry_download", {})

        # Assert
        # assert result.isError is True

    @pytest.mark.asyncio
    async def test_error_responses_include_details(self, mcp_server, mock_sabnzbd_client) -> None:
        """Test that error responses include helpful details."""
        pytest.skip("Implementation pending - TDD")
        # from mcp_servers.sabnzbd.client import SABnzbdClientError

        # Arrange
        # error_message = "Unauthorized: Invalid API key"
        # mock_sabnzbd_client.get_queue = AsyncMock(
        #     side_effect=SABnzbdClientError(error_message)
        # )

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})

        # Assert
        # assert result.isError is True
        # assert error_message in result.content[0].text


# ============================================================================
# MCP Protocol Compliance Tests
# ============================================================================


class TestSABnzbdMCPServerProtocolCompliance:
    """Test suite for MCP protocol compliance."""

    @pytest.mark.asyncio
    async def test_server_implements_list_tools(self, mcp_server) -> None:
        """Test that server implements list_tools protocol method."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # assert isinstance(tools, list)
        # assert all(isinstance(tool, Tool) for tool in tools)

    @pytest.mark.asyncio
    async def test_server_implements_call_tool(self, mcp_server) -> None:
        """Test that server implements call_tool protocol method."""
        pytest.skip("Implementation pending - TDD")
        # from mcp import CallToolResult

        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})
        # assert isinstance(result, CallToolResult)

    def test_tool_schemas_follow_json_schema_spec(self, mcp_server) -> None:
        """Test that all tool schemas follow JSON Schema specification."""
        pytest.skip("Implementation pending - TDD")
        # tools = mcp_server.list_tools()
        # for tool in tools:
        #     schema = tool.inputSchema
        #     assert "type" in schema
        #     assert schema["type"] == "object"
        #     if "properties" in schema:
        #         assert isinstance(schema["properties"], dict)

    @pytest.mark.asyncio
    async def test_tool_responses_follow_mcp_format(
        self, mcp_server, mock_sabnzbd_client, sabnzbd_queue_factory: callable
    ) -> None:
        """Test that tool responses follow MCP format."""
        pytest.skip("Implementation pending - TDD")
        # Arrange
        # mock_queue = sabnzbd_queue_factory(slots=1)
        # mock_sabnzbd_client.get_queue = AsyncMock(return_value=mock_queue)

        # Act
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})

        # Assert: MCP format requirements
        # assert hasattr(result, "content")
        # assert hasattr(result, "isError")
        # assert isinstance(result.content, list)


# ============================================================================
# Lifecycle and State Management Tests
# ============================================================================


class TestSABnzbdMCPServerLifecycle:
    """Test suite for server lifecycle and state management."""

    @pytest.mark.asyncio
    async def test_server_start_initializes_client(self, mock_sabnzbd_client) -> None:
        """Test that server.start() initializes the client."""
        pytest.skip("Implementation pending - TDD")
        # server = SABnzbdMCPServer(client=mock_sabnzbd_client)
        # await server.start()

        # Verify client health check was called
        # mock_sabnzbd_client.health_check.assert_called()

    @pytest.mark.asyncio
    async def test_server_stop_cleans_up_resources(self, mcp_server) -> None:
        """Test that server.stop() cleans up resources."""
        pytest.skip("Implementation pending - TDD")
        # await mcp_server.start()
        # await mcp_server.stop()

        # Verify cleanup occurred (client closed, etc.)

    @pytest.mark.asyncio
    async def test_server_handles_restart(self, mcp_server, mock_sabnzbd_client) -> None:
        """Test that server can be stopped and restarted."""
        pytest.skip("Implementation pending - TDD")
        # await mcp_server.start()
        # await mcp_server.stop()
        # await mcp_server.start()

        # Verify server is functional after restart
        # mock_sabnzbd_client.get_queue = AsyncMock(return_value={"queue": {"slots": []}})
        # result = await mcp_server.call_tool("sabnzbd_get_queue", {})
        # assert result.isError is False
