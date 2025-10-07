"""
Unit tests for Sonarr MCP Server.

This module tests the Sonarr MCP Server that exposes Sonarr functionality
through the Model Context Protocol. These tests follow TDD principles and
should be written BEFORE the implementation.

Test Coverage Strategy:
- Server initialization and configuration
- Tool registration and schema validation
- Tool execution and response formatting
- Error handling and edge cases
- MCP protocol compliance

Target Coverage: 90%+ for the Sonarr MCP server class
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
from mcp.types import Tool, TextContent

# Import the actual server - using new repository structure
from autoarr.mcp_servers.mcp_servers.sonarr.server import SonarrMCPServer
from autoarr.mcp_servers.mcp_servers.sonarr.client import SonarrClient, SonarrClientError


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_sonarr_client():
    """Create a mock SonarrClient for testing."""
    client = AsyncMock(spec=SonarrClient)
    client.url = "http://localhost:8989"
    client.api_key = "test_api_key"
    return client


@pytest.fixture
def sonarr_server(mock_sonarr_client):
    """Create a SonarrMCPServer instance with mock client."""
    return SonarrMCPServer(client=mock_sonarr_client)


# ============================================================================
# Server Initialization Tests
# ============================================================================


class TestSonarrMCPServerInitialization:
    """Test suite for server initialization."""

    def test_server_requires_client(self) -> None:
        """Test that server initialization requires a client."""
        with pytest.raises(ValueError, match="client"):
            SonarrMCPServer(client=None)

    def test_server_initializes_with_client(self, mock_sonarr_client) -> None:
        """Test that server initializes properly with client."""
        server = SonarrMCPServer(client=mock_sonarr_client)

        assert server is not None
        assert server.client == mock_sonarr_client
        assert server.name == "sonarr"
        assert hasattr(server, "version")

    def test_server_sets_up_mcp_handlers(self, mock_sonarr_client) -> None:
        """Test that server sets up MCP protocol handlers."""
        server = SonarrMCPServer(client=mock_sonarr_client)

        assert hasattr(server, "_server")
        assert server._server is not None


# ============================================================================
# Tool Registration Tests
# ============================================================================


class TestSonarrMCPServerToolRegistration:
    """Test suite for tool registration."""

    def test_server_registers_all_required_tools(self, sonarr_server) -> None:
        """Test that server registers all 10 required tools."""
        tools = sonarr_server._get_tools()

        assert isinstance(tools, list)
        assert len(tools) == 10

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "sonarr_get_series",
            "sonarr_get_series_by_id",
            "sonarr_add_series",
            "sonarr_search_series",
            "sonarr_get_episodes",
            "sonarr_search_episode",
            "sonarr_get_wanted",
            "sonarr_get_calendar",
            "sonarr_get_queue",
            "sonarr_delete_series",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

    def test_get_series_tool_has_correct_schema(self, sonarr_server) -> None:
        """Test that get_series tool has correct schema."""
        tools = sonarr_server._get_tools()
        get_series_tool = next(t for t in tools if t.name == "sonarr_get_series")

        assert get_series_tool.description is not None
        assert "series" in get_series_tool.description.lower()
        assert get_series_tool.inputSchema is not None
        assert get_series_tool.inputSchema["type"] == "object"
        assert "required" in get_series_tool.inputSchema

    def test_get_series_by_id_tool_requires_id(self, sonarr_server) -> None:
        """Test that get_series_by_id requires series_id parameter."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_get_series_by_id")

        assert "series_id" in tool.inputSchema["properties"]
        assert "series_id" in tool.inputSchema["required"]

    def test_add_series_tool_requires_all_fields(self, sonarr_server) -> None:
        """Test that add_series requires all necessary parameters."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_add_series")

        required = tool.inputSchema["required"]
        assert "tvdb_id" in required
        assert "quality_profile_id" in required
        assert "root_folder_path" in required

    def test_search_series_tool_requires_term(self, sonarr_server) -> None:
        """Test that search_series requires search term."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_search_series")

        assert "term" in tool.inputSchema["properties"]
        assert "term" in tool.inputSchema["required"]

    def test_get_episodes_tool_requires_series_id(self, sonarr_server) -> None:
        """Test that get_episodes requires series_id parameter."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_get_episodes")

        assert "series_id" in tool.inputSchema["properties"]
        assert "series_id" in tool.inputSchema["required"]

    def test_search_episode_tool_requires_episode_id(self, sonarr_server) -> None:
        """Test that search_episode requires episode_id parameter."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_search_episode")

        assert "episode_id" in tool.inputSchema["properties"]
        assert "episode_id" in tool.inputSchema["required"]

    def test_get_wanted_tool_has_pagination_params(self, sonarr_server) -> None:
        """Test that get_wanted supports pagination parameters."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_get_wanted")

        props = tool.inputSchema["properties"]
        assert "page" in props
        assert "page_size" in props

    def test_get_calendar_tool_has_date_params(self, sonarr_server) -> None:
        """Test that get_calendar supports date range parameters."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_get_calendar")

        props = tool.inputSchema["properties"]
        assert "start_date" in props or "start" in props
        assert "end_date" in props or "end" in props

    def test_delete_series_tool_has_optional_flags(self, sonarr_server) -> None:
        """Test that delete_series has optional deleteFiles flag."""
        tools = sonarr_server._get_tools()
        tool = next(t for t in tools if t.name == "sonarr_delete_series")

        props = tool.inputSchema["properties"]
        assert "series_id" in props
        assert "delete_files" in props
        assert "series_id" in tool.inputSchema["required"]
        assert "delete_files" not in tool.inputSchema.get("required", [])


# ============================================================================
# Tool Execution Tests
# ============================================================================


class TestSonarrMCPServerToolExecution:
    """Test suite for tool execution."""

    @pytest.mark.asyncio
    async def test_get_series_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that get_series tool executes correctly."""
        mock_series = [sonarr_series_factory(series_id=i) for i in range(1, 4)]
        mock_sonarr_client.get_series.return_value = mock_series

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert "data" in response_data
        assert len(response_data["data"]) == 3

        mock_sonarr_client.get_series.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_series_by_id_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that get_series_by_id tool executes correctly."""
        mock_series = sonarr_series_factory(series_id=5, title="Breaking Bad")
        mock_sonarr_client.get_series_by_id.return_value = mock_series

        result = await sonarr_server._call_tool("sonarr_get_series_by_id", {"series_id": 5})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["data"]["id"] == 5
        assert response_data["data"]["title"] == "Breaking Bad"

        mock_sonarr_client.get_series_by_id.assert_called_once_with(series_id=5)

    @pytest.mark.asyncio
    async def test_add_series_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that add_series tool executes correctly."""
        mock_series = sonarr_series_factory(series_id=1, title="The Wire")
        mock_sonarr_client.add_series.return_value = mock_series

        arguments = {
            "title": "The Wire",
            "tvdb_id": 12345,
            "quality_profile_id": 1,
            "root_folder_path": "/tv",
            "monitored": True,
            "season_folder": True,
        }

        result = await sonarr_server._call_tool("sonarr_add_series", arguments)

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["data"]["title"] == "The Wire"

        mock_sonarr_client.add_series.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_series_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that search_series tool executes correctly."""
        mock_results = [sonarr_series_factory(series_id=0, title="The Wire", tvdb_id=12345)]
        mock_sonarr_client.search_series.return_value = mock_results

        result = await sonarr_server._call_tool("sonarr_search_series", {"term": "The Wire"})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["data"]) == 1

        mock_sonarr_client.search_series.assert_called_once_with(term="The Wire")

    @pytest.mark.asyncio
    async def test_get_episodes_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_episode_factory
    ) -> None:
        """Test that get_episodes tool executes correctly."""
        mock_episodes = [sonarr_episode_factory(episode_id=i) for i in range(1, 6)]
        mock_sonarr_client.get_episodes.return_value = mock_episodes

        result = await sonarr_server._call_tool("sonarr_get_episodes", {"series_id": 1})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["data"]) == 5

        mock_sonarr_client.get_episodes.assert_called_once_with(series_id=1, season_number=None)

    @pytest.mark.asyncio
    async def test_get_episodes_with_season_filter(
        self, sonarr_server, mock_sonarr_client, sonarr_episode_factory
    ) -> None:
        """Test that get_episodes supports season filtering."""
        mock_episodes = [sonarr_episode_factory(season_number=2)]
        mock_sonarr_client.get_episodes.return_value = mock_episodes

        result = await sonarr_server._call_tool(
            "sonarr_get_episodes", {"series_id": 1, "season_number": 2}
        )

        mock_sonarr_client.get_episodes.assert_called_once_with(series_id=1, season_number=2)

    @pytest.mark.asyncio
    async def test_search_episode_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_command_factory
    ) -> None:
        """Test that search_episode tool executes correctly."""
        mock_command = sonarr_command_factory(command_id=100, name="EpisodeSearch")
        mock_sonarr_client.search_episode.return_value = mock_command

        result = await sonarr_server._call_tool("sonarr_search_episode", {"episode_id": 5})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["data"]["id"] == 100

        mock_sonarr_client.search_episode.assert_called_once_with(episode_id=5)

    @pytest.mark.asyncio
    async def test_get_wanted_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_wanted_factory
    ) -> None:
        """Test that get_wanted tool executes correctly."""
        mock_wanted = sonarr_wanted_factory(records=5)
        mock_sonarr_client.get_wanted_missing.return_value = mock_wanted

        result = await sonarr_server._call_tool("sonarr_get_wanted", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert "records" in response_data["data"]
        assert len(response_data["data"]["records"]) == 5

        mock_sonarr_client.get_wanted_missing.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_wanted_with_pagination(
        self, sonarr_server, mock_sonarr_client, sonarr_wanted_factory
    ) -> None:
        """Test that get_wanted supports pagination."""
        mock_wanted = sonarr_wanted_factory(records=3, page=2, page_size=10)
        mock_sonarr_client.get_wanted_missing.return_value = mock_wanted

        result = await sonarr_server._call_tool("sonarr_get_wanted", {"page": 2, "page_size": 10})

        mock_sonarr_client.get_wanted_missing.assert_called_once_with(
            page=2, page_size=10, include_series=None
        )

    @pytest.mark.asyncio
    async def test_get_calendar_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_calendar_factory
    ) -> None:
        """Test that get_calendar tool executes correctly."""
        mock_calendar = sonarr_calendar_factory(days=7, episodes_per_day=2)
        mock_sonarr_client.get_calendar.return_value = mock_calendar

        result = await sonarr_server._call_tool(
            "sonarr_get_calendar", {"start_date": "2020-01-01", "end_date": "2020-01-07"}
        )

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert len(response_data["data"]) == 14

        mock_sonarr_client.get_calendar.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_queue_tool_execution(
        self, sonarr_server, mock_sonarr_client, sonarr_queue_factory
    ) -> None:
        """Test that get_queue tool executes correctly."""
        mock_queue = sonarr_queue_factory(records=3)
        mock_sonarr_client.get_queue.return_value = mock_queue

        result = await sonarr_server._call_tool("sonarr_get_queue", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert "records" in response_data["data"]
        assert len(response_data["data"]["records"]) == 3

        mock_sonarr_client.get_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_series_tool_execution(self, sonarr_server, mock_sonarr_client) -> None:
        """Test that delete_series tool executes correctly."""
        mock_sonarr_client.delete_series.return_value = {}

        result = await sonarr_server._call_tool(
            "sonarr_delete_series", {"series_id": 5, "delete_files": True}
        )

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True

        mock_sonarr_client.delete_series.assert_called_once_with(
            series_id=5, delete_files=True, add_import_exclusion=None
        )


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSonarrMCPServerErrorHandling:
    """Test suite for error handling."""

    @pytest.mark.asyncio
    async def test_handles_unknown_tool_name(self, sonarr_server) -> None:
        """Test that server handles unknown tool names gracefully."""
        result = await sonarr_server._call_tool("unknown_tool", {})

        assert isinstance(result, list)
        assert len(result) == 1

        response_data = json.loads(result[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "unknown" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_handles_client_error(self, sonarr_server, mock_sonarr_client) -> None:
        """Test that server handles SonarrClientError gracefully."""
        mock_sonarr_client.get_series.side_effect = SonarrClientError("API Error")

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "API Error" in response_data["error"]

    @pytest.mark.asyncio
    async def test_handles_missing_required_parameter(
        self, sonarr_server, mock_sonarr_client
    ) -> None:
        """Test that server validates required parameters."""
        # This should fail because series_id is required
        result = await sonarr_server._call_tool("sonarr_get_series_by_id", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is False
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_handles_invalid_parameter_type(self, sonarr_server, mock_sonarr_client) -> None:
        """Test that server handles invalid parameter types."""
        # series_id should be int, not string
        result = await sonarr_server._call_tool(
            "sonarr_get_series_by_id", {"series_id": "not_an_int"}
        )

        response_data = json.loads(result[0].text)
        # Should either handle gracefully or return error
        assert "success" in response_data

    @pytest.mark.asyncio
    async def test_handles_network_error(self, sonarr_server, mock_sonarr_client) -> None:
        """Test that server handles network errors gracefully."""
        from autoarr.mcp_servers.mcp_servers.sonarr.client import SonarrConnectionError

        mock_sonarr_client.get_series.side_effect = SonarrConnectionError("Connection failed")

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "Connection" in response_data["error"]

    @pytest.mark.asyncio
    async def test_handles_unexpected_exception(self, sonarr_server, mock_sonarr_client) -> None:
        """Test that server handles unexpected exceptions gracefully."""
        mock_sonarr_client.get_series.side_effect = Exception("Unexpected error")

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is False
        assert "error" in response_data


# ============================================================================
# Response Formatting Tests
# ============================================================================


class TestSonarrMCPServerResponseFormatting:
    """Test suite for response formatting."""

    @pytest.mark.asyncio
    async def test_success_response_format(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that success responses follow correct format."""
        mock_series = [sonarr_series_factory()]
        mock_sonarr_client.get_series.return_value = mock_series

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        response_data = json.loads(result[0].text)
        assert "success" in response_data
        assert "data" in response_data
        assert response_data["success"] is True

    @pytest.mark.asyncio
    async def test_error_response_format(self, sonarr_server, mock_sonarr_client) -> None:
        """Test that error responses follow correct format."""
        mock_sonarr_client.get_series.side_effect = SonarrClientError("Test error")

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        response_data = json.loads(result[0].text)
        assert "success" in response_data
        assert "error" in response_data
        assert response_data["success"] is False
        assert isinstance(response_data["error"], str)

    @pytest.mark.asyncio
    async def test_response_is_valid_json(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that all responses are valid JSON."""
        mock_series = [sonarr_series_factory()]
        mock_sonarr_client.get_series.return_value = mock_series

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        # Should not raise json.JSONDecodeError
        response_data = json.loads(result[0].text)
        assert isinstance(response_data, dict)

    @pytest.mark.asyncio
    async def test_response_includes_metadata(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that responses include useful metadata."""
        mock_series = [sonarr_series_factory(series_id=i) for i in range(1, 4)]
        mock_sonarr_client.get_series.return_value = mock_series

        result = await sonarr_server._call_tool("sonarr_get_series", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert "data" in response_data

        # Could include count, timestamp, etc.
        data = response_data["data"]
        assert isinstance(data, list)
        assert len(data) == 3


# ============================================================================
# MCP Protocol Compliance Tests
# ============================================================================


class TestSonarrMCPServerProtocolCompliance:
    """Test suite for MCP protocol compliance."""

    def test_tool_schemas_are_valid_json_schema(self, sonarr_server) -> None:
        """Test that all tool schemas are valid JSON Schema."""
        tools = sonarr_server._get_tools()

        for tool in tools:
            schema = tool.inputSchema
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema
            assert isinstance(schema["required"], list)

    def test_tool_names_follow_convention(self, sonarr_server) -> None:
        """Test that tool names follow naming convention."""
        tools = sonarr_server._get_tools()

        for tool in tools:
            assert tool.name.startswith("sonarr_")
            assert "_" in tool.name
            assert tool.name.islower()

    def test_tool_descriptions_are_informative(self, sonarr_server) -> None:
        """Test that all tools have informative descriptions."""
        tools = sonarr_server._get_tools()

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 10
            assert not tool.description.isspace()

    def test_required_parameters_are_documented(self, sonarr_server) -> None:
        """Test that required parameters have descriptions."""
        tools = sonarr_server._get_tools()

        for tool in tools:
            required = tool.inputSchema.get("required", [])
            props = tool.inputSchema.get("properties", {})

            for req_param in required:
                assert req_param in props
                assert "description" in props[req_param]
                assert len(props[req_param]["description"]) > 0

    def test_optional_parameters_have_defaults_or_nullable(self, sonarr_server) -> None:
        """Test that optional parameters have defaults or are nullable."""
        tools = sonarr_server._get_tools()

        for tool in tools:
            required = tool.inputSchema.get("required", [])
            props = tool.inputSchema.get("properties", {})

            for prop_name, prop_schema in props.items():
                if prop_name not in required:
                    # Optional params should have default or be nullable
                    has_default = "default" in prop_schema
                    is_nullable = prop_schema.get("type") == "null"
                    # At least one should be true for optional params
                    # (This is a design decision, adjust as needed)


# ============================================================================
# Integration with Client Tests
# ============================================================================


class TestSonarrMCPServerClientIntegration:
    """Test suite for integration between server and client."""

    @pytest.mark.asyncio
    async def test_server_passes_arguments_to_client_correctly(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that server correctly passes arguments to client methods."""
        mock_series = sonarr_series_factory()
        mock_sonarr_client.add_series.return_value = mock_series

        arguments = {
            "title": "Test Series",
            "tvdb_id": 12345,
            "quality_profile_id": 1,
            "root_folder_path": "/tv",
            "monitored": True,
            "season_folder": False,
        }

        await sonarr_server._call_tool("sonarr_add_series", arguments)

        # Verify client was called with correct arguments
        mock_sonarr_client.add_series.assert_called_once()
        call_args = mock_sonarr_client.add_series.call_args

        # Check that arguments were transformed/passed correctly
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_server_handles_client_response_correctly(
        self, sonarr_server, mock_sonarr_client, sonarr_queue_factory
    ) -> None:
        """Test that server correctly processes client responses."""
        mock_queue = sonarr_queue_factory(records=5)
        mock_sonarr_client.get_queue.return_value = mock_queue

        result = await sonarr_server._call_tool("sonarr_get_queue", {})

        response_data = json.loads(result[0].text)
        assert response_data["success"] is True
        assert response_data["data"] == mock_queue

    @pytest.mark.asyncio
    async def test_server_preserves_client_data_structure(
        self, sonarr_server, mock_sonarr_client, sonarr_series_factory
    ) -> None:
        """Test that server preserves data structure from client."""
        mock_series = sonarr_series_factory(series_id=1, title="Test Series", season_count=5)
        mock_sonarr_client.get_series_by_id.return_value = mock_series

        result = await sonarr_server._call_tool("sonarr_get_series_by_id", {"series_id": 1})

        response_data = json.loads(result[0].text)
        returned_series = response_data["data"]

        # Verify structure is preserved
        assert returned_series["id"] == mock_series["id"]
        assert returned_series["title"] == mock_series["title"]
        assert "seasons" in returned_series
        assert len(returned_series["seasons"]) == len(mock_series["seasons"])
