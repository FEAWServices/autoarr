"""
Unit tests for Radarr MCP Server.

This module tests the MCP server implementation for Radarr, which exposes
Radarr functionality through the Model Context Protocol. Tests follow TDD
principles and verify tool registration, request handling, and error management.

Test Coverage Strategy:
- Tool registration and list_tools functionality
- Tool execution for all Radarr operations
- Input validation and parameter handling
- Error response formatting
- MCP protocol compliance
- Integration with RadarrClient

Target Coverage: 90%+ for the RadarrMCPServer class
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest
from mcp.types import TextContent, Tool

# Import the actual server - using new repository structure
from autoarr.mcp_servers.mcp_servers.radarr.client import (
    RadarrClient, RadarrClientError, RadarrConnectionError)
from autoarr.mcp_servers.mcp_servers.radarr.server import RadarrMCPServer

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_radarr_client() -> Mock:
    """Create a mock RadarrClient for testing."""
    client = Mock(spec=RadarrClient)  # noqa: F841
    client.health_check = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def radarr_mcp_server(mock_radarr_client: Mock) -> RadarrMCPServer:
    """Create a RadarrMCPServer instance with mocked client."""
    return RadarrMCPServer(client=mock_radarr_client)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestRadarrMCPServerInitialization:
    """Test suite for MCP server initialization."""

    def test_server_requires_client(self) -> None:
        """Test that server initialization requires a client."""
        with pytest.raises(ValueError, match="client"):
            RadarrMCPServer(client=None)

    def test_server_initializes_with_valid_client(self, mock_radarr_client: Mock) -> None:
        """Test that server initializes properly with valid client."""
        server = RadarrMCPServer(client=mock_radarr_client)
        assert server.client == mock_radarr_client  # noqa: F841
        assert server.name == "radarr"
        assert server.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_server_start_validates_connection(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that server start validates connection to Radarr."""
        radarr_mcp_server.client.health_check = AsyncMock(return_value=True)

        await radarr_mcp_server.start()

        radarr_mcp_server.client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_start_raises_on_connection_failure(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that server start raises error if connection fails."""
        radarr_mcp_server.client.health_check = AsyncMock(return_value=False)

        with pytest.raises(Exception):
            await radarr_mcp_server.start()

    @pytest.mark.asyncio
    async def test_server_stop_closes_client(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that server stop closes the client connection."""
        await radarr_mcp_server.stop()

        radarr_mcp_server.client.close.assert_called_once()


# ============================================================================
# Tool Registration Tests
# ============================================================================


class TestRadarrMCPServerToolRegistration:
    """Test suite for MCP tool registration."""

    def test_list_tools_returns_all_radarr_tools(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that list_tools returns all available Radarr tools."""
        tools = radarr_mcp_server.list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Verify all expected tools are present
        tool_names = [tool.name for tool in tools]
        assert "radarr_get_movies" in tool_names
        assert "radarr_get_movie_by_id" in tool_names
        assert "radarr_add_movie" in tool_names
        assert "radarr_delete_movie" in tool_names
        assert "radarr_search_movie_lookup" in tool_names
        assert "radarr_search_movie" in tool_names
        assert "radarr_get_queue" in tool_names
        assert "radarr_get_calendar" in tool_names
        assert "radarr_get_wanted" in tool_names

    def test_tools_have_proper_schemas(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that all tools have proper JSON schemas."""
        tools = radarr_mcp_server.list_tools()

        for tool in tools:
            assert isinstance(tool, Tool)
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema

    def test_get_tool_by_name_returns_correct_tool(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that get_tool retrieves specific tool by name."""
        tool = radarr_mcp_server.get_tool("radarr_get_movies")

        assert tool is not None
        assert tool.name == "radarr_get_movies"
        assert "movies" in tool.description.lower()

    def test_get_tool_returns_none_for_unknown_tool(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that get_tool returns None for non-existent tool."""
        tool = radarr_mcp_server.get_tool("unknown_tool")

        assert tool is None


# ============================================================================
# Movie Operations Tool Tests
# ============================================================================


class TestRadarrMCPServerMovieOperations:
    """Test suite for movie management tools."""

    @pytest.mark.asyncio
    async def test_get_movies_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_movie_factory: callable
    ) -> None:
        """Test that get_movies tool calls client correctly."""
        mock_movies = [radarr_movie_factory(movie_id=i) for i in range(3)]
        radarr_mcp_server.client.get_movies = AsyncMock(return_value=mock_movies)

        result = await radarr_mcp_server.call_tool("radarr_get_movies", {})  # noqa: F841

        radarr_mcp_server.client.get_movies.assert_called_once()
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True
        assert len(response_data["data"]) == 3

    @pytest.mark.asyncio
    async def test_get_movies_tool_supports_pagination(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that get_movies tool supports pagination parameters."""
        radarr_mcp_server.client.get_movies = AsyncMock(return_value=[])

        await radarr_mcp_server.call_tool("radarr_get_movies", {"limit": 10, "page": 2})

        radarr_mcp_server.client.get_movies.assert_called_once_with(limit=10, page=2)

    @pytest.mark.asyncio
    async def test_get_movie_by_id_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_movie_factory: callable
    ) -> None:
        """Test that get_movie_by_id tool calls client correctly."""
        mock_movie = radarr_movie_factory(movie_id=5, title="The Matrix")
        radarr_mcp_server.client.get_movie_by_id = AsyncMock(return_value=mock_movie)

        result = await radarr_mcp_server.call_tool(
            "radarr_get_movie_by_id", {"movie_id": 5}
        )  # noqa: F841

        radarr_mcp_server.client.get_movie_by_id.assert_called_once_with(movie_id=5)
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert response_data["data"]["id"] == 5
        assert response_data["data"]["title"] == "The Matrix"

    @pytest.mark.asyncio
    async def test_get_movie_by_id_validates_movie_id(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that get_movie_by_id validates movie_id parameter."""
        result = await radarr_mcp_server.call_tool("radarr_get_movie_by_id", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "movie_id" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_add_movie_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_movie_factory: callable
    ) -> None:
        """Test that add_movie tool calls client correctly."""
        mock_movie = radarr_movie_factory(movie_id=1, title="Inception")
        radarr_mcp_server.client.add_movie = AsyncMock(return_value=mock_movie)

        arguments = {
            "title": "Inception",
            "tmdb_id": 27205,
            "quality_profile_id": 1,
            "root_folder_path": "/movies",
            "monitored": True,
            "minimum_availability": "released",
        }

        await radarr_mcp_server.call_tool("radarr_add_movie", arguments)

        radarr_mcp_server.client.add_movie.assert_called_once()
        call_args = radarr_mcp_server.client.add_movie.call_args[0][0]
        assert call_args["tmdbId"] == 27205
        assert call_args["qualityProfileId"] == 1
        assert call_args["rootFolderPath"] == "/movies"

    @pytest.mark.asyncio
    async def test_search_movie_lookup_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_movie_factory: callable
    ) -> None:
        """Test that search_movie_lookup tool calls client correctly."""
        mock_results = [radarr_movie_factory(title="The Matrix")]
        radarr_mcp_server.client.search_movie_lookup = AsyncMock(return_value=mock_results)

        result = await radarr_mcp_server.call_tool(  # noqa: F841
            "radarr_search_movie_lookup", {"term": "The Matrix"}
        )

        radarr_mcp_server.client.search_movie_lookup.assert_called_once_with(term="The Matrix")
        assert not result.isError

    @pytest.mark.asyncio
    async def test_search_movie_lookup_validates_term(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that search_movie_lookup validates term parameter."""
        result = await radarr_mcp_server.call_tool(
            "radarr_search_movie_lookup", {"term": ""}
        )  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "term" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_movie_tool_calls_client(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that delete_movie tool calls client correctly."""
        radarr_mcp_server.client.delete_movie = AsyncMock(return_value={})

        result = await radarr_mcp_server.call_tool(  # noqa: F841
            "radarr_delete_movie", {"movie_id": 5, "delete_files": True}
        )

        radarr_mcp_server.client.delete_movie.assert_called_once_with(
            movie_id=5, delete_files=True, add_import_exclusion=None
        )
        assert not result.isError


# ============================================================================
# Command Operations Tool Tests
# ============================================================================


class TestRadarrMCPServerCommandOperations:
    """Test suite for command execution tools."""

    @pytest.mark.asyncio
    async def test_search_movie_tool_triggers_search(
        self, radarr_mcp_server: RadarrMCPServer, radarr_command_factory: callable
    ) -> None:
        """Test that search_movie tool triggers movie search command."""
        mock_command = radarr_command_factory(command_id=123, name="MoviesSearch")
        radarr_mcp_server.client.search_movie = AsyncMock(return_value=mock_command)

        result = await radarr_mcp_server.call_tool(
            "radarr_search_movie", {"movie_id": 5}
        )  # noqa: F841

        radarr_mcp_server.client.search_movie.assert_called_once_with(movie_id=5)
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert response_data["data"]["id"] == 123

    @pytest.mark.asyncio
    async def test_search_movie_validates_movie_id(
        self, radarr_mcp_server: RadarrMCPServer
    ) -> None:
        """Test that search_movie validates movie_id parameter."""
        result = await radarr_mcp_server.call_tool("radarr_search_movie", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "movie_id" in response_data["error"].lower()


# ============================================================================
# Calendar, Queue, and Wanted Tool Tests
# ============================================================================


class TestRadarrMCPServerCalendarQueueWanted:
    """Test suite for calendar, queue, and wanted tools."""

    @pytest.mark.asyncio
    async def test_get_calendar_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_calendar_factory: callable
    ) -> None:
        """Test that get_calendar tool calls client correctly."""
        mock_calendar = radarr_calendar_factory(days=7, movies_per_day=2)
        radarr_mcp_server.client.get_calendar = AsyncMock(return_value=mock_calendar)

        result = await radarr_mcp_server.call_tool(  # noqa: F841
            "radarr_get_calendar", {"start_date": "2020-01-01", "end_date": "2020-01-07"}
        )

        radarr_mcp_server.client.get_calendar.assert_called_once_with(
            start_date="2020-01-01", end_date="2020-01-07"
        )
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_queue_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_queue_factory: callable
    ) -> None:
        """Test that get_queue tool calls client correctly."""
        mock_queue = radarr_queue_factory(records=3)
        radarr_mcp_server.client.get_queue = AsyncMock(return_value=mock_queue)

        result = await radarr_mcp_server.call_tool("radarr_get_queue", {})  # noqa: F841

        radarr_mcp_server.client.get_queue.assert_called_once()
        assert not result.isError
        response_data = json.loads(result.content[0].text)
        assert len(response_data["data"]["records"]) == 3

    @pytest.mark.asyncio
    async def test_get_queue_supports_pagination(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that get_queue supports pagination parameters."""
        radarr_mcp_server.client.get_queue = AsyncMock(return_value={"records": []})

        await radarr_mcp_server.call_tool("radarr_get_queue", {"page": 2, "page_size": 20})

        radarr_mcp_server.client.get_queue.assert_called_once_with(page=2, page_size=20)

    @pytest.mark.asyncio
    async def test_get_wanted_tool_calls_client(
        self, radarr_mcp_server: RadarrMCPServer, radarr_wanted_factory: callable
    ) -> None:
        """Test that get_wanted tool calls client correctly."""
        mock_wanted = radarr_wanted_factory(records=5)
        radarr_mcp_server.client.get_wanted_missing = AsyncMock(return_value=mock_wanted)

        result = await radarr_mcp_server.call_tool("radarr_get_wanted", {})  # noqa: F841

        radarr_mcp_server.client.get_wanted_missing.assert_called_once()
        assert not result.isError


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestRadarrMCPServerErrorHandling:
    """Test suite for error handling in MCP tools."""

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that server handles RadarrConnectionError properly."""
        radarr_mcp_server.client.get_movies = AsyncMock(
            side_effect=RadarrConnectionError("Connection failed")
        )

        result = await radarr_mcp_server.call_tool("radarr_get_movies", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "connection error" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_handles_client_error(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that server handles RadarrClientError properly."""
        radarr_mcp_server.client.get_movie_by_id = AsyncMock(
            side_effect=RadarrClientError("Movie not found (404)")
        )

        result = await radarr_mcp_server.call_tool(
            "radarr_get_movie_by_id", {"movie_id": 999}
        )  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "404" in response_data["error"]

    @pytest.mark.asyncio
    async def test_handles_validation_error(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that server handles ValueError from validation properly."""
        result = await radarr_mcp_server.call_tool("radarr_get_movie_by_id", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "validation error" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_handles_unknown_tool(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that server handles unknown tool gracefully."""
        result = await radarr_mcp_server.call_tool("unknown_tool", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "unknown tool" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that server handles unexpected errors gracefully."""
        radarr_mcp_server.client.get_movies = AsyncMock(side_effect=Exception("Unexpected error"))

        result = await radarr_mcp_server.call_tool("radarr_get_movies", {})  # noqa: F841

        assert result.isError
        response_data = json.loads(result.content[0].text)
        assert "unexpected error" in response_data["error"].lower()


# ============================================================================
# Response Format Tests
# ============================================================================


class TestRadarrMCPServerResponseFormat:
    """Test suite for MCP response formatting."""

    @pytest.mark.asyncio
    async def test_successful_response_format(
        self, radarr_mcp_server: RadarrMCPServer, radarr_movie_factory: callable
    ) -> None:
        """Test that successful responses follow correct format."""
        mock_movie = radarr_movie_factory()
        radarr_mcp_server.client.get_movie_by_id = AsyncMock(return_value=mock_movie)

        result = await radarr_mcp_server.call_tool(
            "radarr_get_movie_by_id", {"movie_id": 1}
        )  # noqa: F841

        assert isinstance(result.content, list)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)

        response_data = json.loads(result.content[0].text)
        assert "success" in response_data
        assert "data" in response_data
        assert response_data["success"] is True

    @pytest.mark.asyncio
    async def test_error_response_format(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that error responses follow correct format."""
        radarr_mcp_server.client.get_movies = AsyncMock(
            side_effect=RadarrClientError("Error occurred")
        )

        result = await radarr_mcp_server.call_tool("radarr_get_movies", {})  # noqa: F841

        assert isinstance(result.content, list)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)

        response_data = json.loads(result.content[0].text)
        assert "success" in response_data
        assert "error" in response_data
        assert response_data["success"] is False

    @pytest.mark.asyncio
    async def test_response_is_valid_json(self, radarr_mcp_server: RadarrMCPServer) -> None:
        """Test that all responses are valid JSON."""
        radarr_mcp_server.client.get_movies = AsyncMock(return_value=[])

        result = await radarr_mcp_server.call_tool("radarr_get_movies", {})  # noqa: F841

        # Should not raise JSONDecodeError
        response_data = json.loads(result.content[0].text)
        assert isinstance(response_data, dict)
