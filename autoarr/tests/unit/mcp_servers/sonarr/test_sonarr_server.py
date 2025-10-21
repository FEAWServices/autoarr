"""
Unit tests for Sonarr MCP Server.

This module tests the Sonarr MCP server implementation that exposes Sonarr
operations as MCP tools. These tests follow TDD principles and verify:

- Tool registration and schema validation
- Tool execution and argument handling
- Error handling and edge cases
- Response formatting and serialization

Test Coverage Strategy:
- All MCP tools (sonarr_get_series, sonarr_add_series, etc.)
- Input validation for all tool arguments
- Error handling for client failures
- Edge cases and boundary conditions

Target Coverage: 95%+ for the Sonarr MCP server class
"""

import json
from unittest.mock import AsyncMock

import pytest
from mcp.types import TextContent

# Import the actual MCP server and client
from autoarr.mcp_servers.mcp_servers.sonarr.client import (
    SonarrClient, SonarrClientError, SonarrConnectionError)
from autoarr.mcp_servers.mcp_servers.sonarr.server import SonarrMCPServer

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_sonarr_client():
    """Create a mock Sonarr client for testing."""
    client = AsyncMock(spec=SonarrClient)  # noqa: F841
    client.url = "http://localhost:8989"
    client.api_key = "test_api_key_sonarr"
    client.timeout = 30.0
    client.health_check = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def sonarr_mcp_server(mock_sonarr_client):
    """Create a Sonarr MCP server instance for testing."""
    return SonarrMCPServer(client=mock_sonarr_client)


@pytest.fixture
def sonarr_series_data():
    """Sample series data for testing."""
    return {
        "id": 1,
        "title": "Breaking Bad",
        "tvdbId": 81189,
        "status": "ended",
        "overview": "A chemistry teacher starts making meth",
        "network": "AMC",
        "monitored": True,
        "qualityProfileId": 1,
        "path": "/tv/Breaking Bad",
    }


@pytest.fixture
def sonarr_episode_data():
    """Sample episode data for testing."""
    return {
        "id": 1,
        "seriesId": 1,
        "tvdbId": 349232,
        "seasonNumber": 1,
        "episodeNumber": 1,
        "title": "Pilot",
        "airDate": "2008-01-20",
        "hasFile": False,
        "monitored": True,
    }


# ============================================================================
# Initialization and Setup Tests
# ============================================================================


class TestSonarrMCPServerInitialization:
    """Test suite for MCP server initialization."""

    def test_server_requires_client(self) -> None:
        """Test that server initialization requires a client."""
        with pytest.raises(ValueError, match="client"):
            SonarrMCPServer(client=None)

    def test_server_initializes_with_client(self, mock_sonarr_client) -> None:
        """Test that server initializes correctly with a client."""
        server = SonarrMCPServer(client=mock_sonarr_client)

        assert server.client == mock_sonarr_client  # noqa: F841
        assert server.name == "sonarr"
        assert server.version == "0.1.0"

    def test_server_has_correct_name_and_version(self, sonarr_mcp_server) -> None:
        """Test that server has correct metadata."""
        assert sonarr_mcp_server.name == "sonarr"
        assert sonarr_mcp_server.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_server_start_validates_connection(self, mock_sonarr_client) -> None:
        """Test that server start validates connection to Sonarr."""
        mock_sonarr_client.health_check.return_value = True
        server = SonarrMCPServer(client=mock_sonarr_client)

        await server.start()

        mock_sonarr_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_start_raises_on_connection_failure(self, mock_sonarr_client) -> None:
        """Test that server start raises error when connection fails."""
        mock_sonarr_client.health_check.return_value = False
        server = SonarrMCPServer(client=mock_sonarr_client)

        with pytest.raises(SonarrClientError, match="Failed to connect"):
            await server.start()

    @pytest.mark.asyncio
    async def test_server_stop_closes_client(self, mock_sonarr_client) -> None:
        """Test that server stop closes the client connection."""
        server = SonarrMCPServer(client=mock_sonarr_client)

        await server.stop()

        mock_sonarr_client.close.assert_called_once()


# ============================================================================
# Tool Registration Tests
# ============================================================================


class TestSonarrMCPServerToolRegistration:
    """Test suite for MCP tool registration."""

    def test_list_tools_returns_all_tools(self, sonarr_mcp_server) -> None:
        """Test that list_tools returns all available Sonarr tools."""
        tools = sonarr_mcp_server.list_tools()

        # Should have 10 tools
        assert len(tools) == 10

        tool_names = [tool.name for tool in tools]
        assert "sonarr_get_series" in tool_names
        assert "sonarr_get_series_by_id" in tool_names
        assert "sonarr_add_series" in tool_names
        assert "sonarr_search_series" in tool_names
        assert "sonarr_get_episodes" in tool_names
        assert "sonarr_search_episode" in tool_names
        assert "sonarr_get_wanted" in tool_names
        assert "sonarr_get_calendar" in tool_names
        assert "sonarr_get_queue" in tool_names
        assert "sonarr_delete_series" in tool_names

    def test_get_tool_returns_correct_tool(self, sonarr_mcp_server) -> None:
        """Test that get_tool returns the correct tool by name."""
        tool = sonarr_mcp_server.get_tool("sonarr_get_series")

        assert tool is not None
        assert tool.name == "sonarr_get_series"
        assert "TV series" in tool.description

    def test_get_tool_returns_none_for_unknown_tool(self, sonarr_mcp_server) -> None:
        """Test that get_tool returns None for unknown tools."""
        tool = sonarr_mcp_server.get_tool("nonexistent_tool")

        assert tool is None

    def test_tools_have_valid_schemas(self, sonarr_mcp_server) -> None:
        """Test that all tools have valid input schemas."""
        tools = sonarr_mcp_server.list_tools()

        for tool in tools:
            assert hasattr(tool, "inputSchema")
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema
            assert "required" in tool.inputSchema


# ============================================================================
# Series Operations Tests
# ============================================================================


class TestSonarrMCPServerSeriesOperations:
    """Test suite for series-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_series_calls_client_correctly(
        self, sonarr_mcp_server, mock_sonarr_client, sonarr_series_data
    ) -> None:
        """Test that sonarr_get_series calls the client correctly."""
        mock_sonarr_client.get_series.return_value = [sonarr_series_data]

        result = await sonarr_mcp_server.call_tool("sonarr_get_series", {})  # noqa: F841

        mock_sonarr_client.get_series.assert_called_once_with(limit=None, page=None)
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_series_with_pagination(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test sonarr_get_series with pagination parameters."""
        mock_sonarr_client.get_series.return_value = []

        await sonarr_mcp_server.call_tool("sonarr_get_series", {"limit": 10, "page": 2})

        mock_sonarr_client.get_series.assert_called_once_with(limit=10, page=2)

    @pytest.mark.asyncio
    async def test_get_series_by_id_returns_series(
        self, sonarr_mcp_server, mock_sonarr_client, sonarr_series_data
    ) -> None:
        """Test that sonarr_get_series_by_id returns series data."""
        mock_sonarr_client.get_series_by_id.return_value = sonarr_series_data

        result = await sonarr_mcp_server.call_tool(
            "sonarr_get_series_by_id", {"series_id": 1}
        )  # noqa: F841

        mock_sonarr_client.get_series_by_id.assert_called_once_with(series_id=1)
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_series_by_id_validates_series_id(self, sonarr_mcp_server) -> None:
        """Test that sonarr_get_series_by_id validates series_id."""
        result = await sonarr_mcp_server.call_tool("sonarr_get_series_by_id", {})  # noqa: F841

        assert result.isError
        # Parse the error response
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "series_id is required" in error_data["error"]

    @pytest.mark.asyncio
    async def test_add_series_sends_correct_data(
        self, sonarr_mcp_server, mock_sonarr_client, sonarr_series_data
    ) -> None:
        """Test that sonarr_add_series sends correct data to client."""
        mock_sonarr_client.add_series.return_value = sonarr_series_data

        arguments = {
            "title": "Breaking Bad",
            "tvdb_id": 81189,
            "quality_profile_id": 1,
            "root_folder_path": "/tv",
            "monitored": True,
            "season_folder": True,
        }

        result = await sonarr_mcp_server.call_tool("sonarr_add_series", arguments)  # noqa: F841

        # Verify the call
        mock_sonarr_client.add_series.assert_called_once()
        call_args = mock_sonarr_client.add_series.call_args[0][0]

        assert call_args["title"] == "Breaking Bad"
        assert call_args["tvdbId"] == 81189
        assert call_args["qualityProfileId"] == 1
        assert call_args["rootFolderPath"] == "/tv"
        assert call_args["monitored"] is True
        assert call_args["seasonFolder"] is True
        assert not result.isError

    @pytest.mark.asyncio
    async def test_search_series_validates_term(self, sonarr_mcp_server) -> None:
        """Test that sonarr_search_series validates search term."""
        # Empty term
        result = await sonarr_mcp_server.call_tool(
            "sonarr_search_series", {"term": ""}
        )  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "non-empty string" in error_data["error"]

    @pytest.mark.asyncio
    async def test_search_series_calls_client(
        self, sonarr_mcp_server, mock_sonarr_client, sonarr_series_data
    ) -> None:
        """Test that sonarr_search_series calls client correctly."""
        mock_sonarr_client.search_series.return_value = [sonarr_series_data]

        result = await sonarr_mcp_server.call_tool(
            "sonarr_search_series", {"term": "Breaking Bad"}
        )  # noqa: F841

        mock_sonarr_client.search_series.assert_called_once_with(term="Breaking Bad")
        assert not result.isError

    @pytest.mark.asyncio
    async def test_delete_series_validates_series_id(self, sonarr_mcp_server) -> None:
        """Test that sonarr_delete_series validates series_id."""
        result = await sonarr_mcp_server.call_tool("sonarr_delete_series", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "series_id is required" in error_data["error"]

    @pytest.mark.asyncio
    async def test_delete_series_with_files(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test that sonarr_delete_series handles delete_files parameter."""
        mock_sonarr_client.delete_series.return_value = {}

        await sonarr_mcp_server.call_tool(
            "sonarr_delete_series",
            {"series_id": 1, "delete_files": True, "add_import_exclusion": True},
        )

        mock_sonarr_client.delete_series.assert_called_once_with(
            series_id=1, delete_files=True, add_import_exclusion=True
        )


# ============================================================================
# Episode Operations Tests
# ============================================================================


class TestSonarrMCPServerEpisodeOperations:
    """Test suite for episode-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_episodes_requires_series_id(self, sonarr_mcp_server) -> None:
        """Test that sonarr_get_episodes requires series_id."""
        result = await sonarr_mcp_server.call_tool("sonarr_get_episodes", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "series_id is required" in error_data["error"]

    @pytest.mark.asyncio
    async def test_get_episodes_calls_client(
        self, sonarr_mcp_server, mock_sonarr_client, sonarr_episode_data
    ) -> None:
        """Test that sonarr_get_episodes calls client correctly."""
        mock_sonarr_client.get_episodes.return_value = [sonarr_episode_data]

        result = await sonarr_mcp_server.call_tool(
            "sonarr_get_episodes", {"series_id": 1}
        )  # noqa: F841

        mock_sonarr_client.get_episodes.assert_called_once_with(series_id=1, season_number=None)
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_episodes_with_season_filter(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test sonarr_get_episodes with season number filter."""
        mock_sonarr_client.get_episodes.return_value = []

        await sonarr_mcp_server.call_tool(
            "sonarr_get_episodes", {"series_id": 1, "season_number": 2}
        )

        mock_sonarr_client.get_episodes.assert_called_once_with(series_id=1, season_number=2)

    @pytest.mark.asyncio
    async def test_search_episode_requires_episode_id(self, sonarr_mcp_server) -> None:
        """Test that sonarr_search_episode requires episode_id."""
        result = await sonarr_mcp_server.call_tool("sonarr_search_episode", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "episode_id is required" in error_data["error"]

    @pytest.mark.asyncio
    async def test_search_episode_triggers_search(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test that sonarr_search_episode triggers episode search."""
        mock_sonarr_client.search_episode.return_value = {
            "id": 100,
            "name": "EpisodeSearch",
            "status": "queued",
        }

        result = await sonarr_mcp_server.call_tool(
            "sonarr_search_episode", {"episode_id": 42}
        )  # noqa: F841

        mock_sonarr_client.search_episode.assert_called_once_with(episode_id=42)
        assert not result.isError


# ============================================================================
# Queue, Calendar, and Wanted Tests
# ============================================================================


class TestSonarrMCPServerQueueCalendarWanted:
    """Test suite for queue, calendar, and wanted operations."""

    @pytest.mark.asyncio
    async def test_get_queue_returns_queue_data(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test that sonarr_get_queue returns queue data."""
        mock_queue = {
            "page": 1,
            "pageSize": 20,
            "totalRecords": 3,
            "records": [],
        }
        mock_sonarr_client.get_queue.return_value = mock_queue

        result = await sonarr_mcp_server.call_tool("sonarr_get_queue", {})  # noqa: F841

        mock_sonarr_client.get_queue.assert_called_once_with(page=None, page_size=None)
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_queue_with_pagination(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test sonarr_get_queue with pagination parameters."""
        mock_sonarr_client.get_queue.return_value = {"page": 2, "records": []}

        await sonarr_mcp_server.call_tool("sonarr_get_queue", {"page": 2, "page_size": 50})

        mock_sonarr_client.get_queue.assert_called_once_with(page=2, page_size=50)

    @pytest.mark.asyncio
    async def test_get_calendar_returns_upcoming_episodes(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test that sonarr_get_calendar returns upcoming episodes."""
        mock_sonarr_client.get_calendar.return_value = []

        result = await sonarr_mcp_server.call_tool("sonarr_get_calendar", {})  # noqa: F841

        mock_sonarr_client.get_calendar.assert_called_once_with(start_date=None, end_date=None)
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_calendar_with_date_range(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test sonarr_get_calendar with date range."""
        mock_sonarr_client.get_calendar.return_value = []

        await sonarr_mcp_server.call_tool(
            "sonarr_get_calendar",
            {"start_date": "2024-01-01", "end_date": "2024-01-07"},
        )

        mock_sonarr_client.get_calendar.assert_called_once_with(
            start_date="2024-01-01", end_date="2024-01-07"
        )

    @pytest.mark.asyncio
    async def test_get_wanted_returns_missing_episodes(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test that sonarr_get_wanted returns missing episodes."""
        mock_wanted = {
            "page": 1,
            "pageSize": 20,
            "totalRecords": 10,
            "records": [],
        }
        mock_sonarr_client.get_wanted_missing.return_value = mock_wanted

        result = await sonarr_mcp_server.call_tool("sonarr_get_wanted", {})  # noqa: F841

        mock_sonarr_client.get_wanted_missing.assert_called_once_with(
            page=None, page_size=None, include_series=None
        )
        assert not result.isError

    @pytest.mark.asyncio
    async def test_get_wanted_with_options(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test sonarr_get_wanted with pagination and include_series."""
        mock_sonarr_client.get_wanted_missing.return_value = {"records": []}

        await sonarr_mcp_server.call_tool(
            "sonarr_get_wanted",
            {"page": 3, "page_size": 25, "include_series": True},
        )

        mock_sonarr_client.get_wanted_missing.assert_called_once_with(
            page=3, page_size=25, include_series=True
        )


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSonarrMCPServerErrorHandling:
    """Test suite for error handling in MCP server."""

    @pytest.mark.asyncio
    async def test_handles_unknown_tool(self, sonarr_mcp_server) -> None:
        """Test handling of unknown tool names."""
        result = await sonarr_mcp_server.call_tool("unknown_tool", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "Unknown tool" in error_data["error"]

    @pytest.mark.asyncio
    async def test_handles_client_error(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test handling of SonarrClientError."""
        mock_sonarr_client.get_series.side_effect = SonarrClientError("Server error: 500")

        result = await sonarr_mcp_server.call_tool("sonarr_get_series", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "Server error" in error_data["error"]

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test handling of SonarrConnectionError."""
        mock_sonarr_client.get_series.side_effect = SonarrConnectionError("Connection refused")

        result = await sonarr_mcp_server.call_tool("sonarr_get_series", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "Connection error" in error_data["error"]

    @pytest.mark.asyncio
    async def test_handles_validation_error(self, sonarr_mcp_server) -> None:
        """Test handling of validation errors."""
        # Try to add series without required fields
        result = await sonarr_mcp_server.call_tool("sonarr_add_series", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "Validation error" in error_data["error"] or "error" in error_data

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test handling of unexpected errors."""
        mock_sonarr_client.get_series.side_effect = RuntimeError("Unexpected error")

        result = await sonarr_mcp_server.call_tool("sonarr_get_series", {})  # noqa: F841

        assert result.isError
        error_text = result.content[0].text
        error_data = json.loads(error_text)
        assert "Unexpected error" in error_data["error"]


# ============================================================================
# Response Formatting Tests
# ============================================================================


class TestSonarrMCPServerResponseFormatting:
    """Test suite for response formatting."""

    @pytest.mark.asyncio
    async def test_successful_response_format(
        self, sonarr_mcp_server, mock_sonarr_client, sonarr_series_data
    ) -> None:
        """Test that successful responses are properly formatted."""
        mock_sonarr_client.get_series.return_value = [sonarr_series_data]

        result = await sonarr_mcp_server.call_tool("sonarr_get_series", {})  # noqa: F841

        assert not result.isError
        assert isinstance(result.content, list)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)

        # Parse response
        response_text = result.content[0].text
        response_data = json.loads(response_text)

        assert "success" in response_data
        assert response_data["success"] is True
        assert "data" in response_data
        assert isinstance(response_data["data"], list)
        assert len(response_data["data"]) == 1
        assert response_data["data"][0]["title"] == "Breaking Bad"

    @pytest.mark.asyncio
    async def test_error_response_format(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test that error responses are properly formatted."""
        mock_sonarr_client.get_series.side_effect = SonarrClientError("Test error")

        result = await sonarr_mcp_server.call_tool("sonarr_get_series", {})  # noqa: F841

        assert result.isError
        assert isinstance(result.content, list)
        assert len(result.content) == 1

        # Parse error response
        error_text = result.content[0].text
        error_data = json.loads(error_text)

        assert "success" in error_data
        assert error_data["success"] is False
        assert "error" in error_data
        assert "Test error" in error_data["error"]

    @pytest.mark.asyncio
    async def test_delete_series_empty_response_handling(
        self, sonarr_mcp_server, mock_sonarr_client
    ) -> None:
        """Test that delete_series handles empty response correctly."""
        mock_sonarr_client.delete_series.return_value = {}

        result = await sonarr_mcp_server.call_tool(
            "sonarr_delete_series", {"series_id": 1}
        )  # noqa: F841

        assert not result.isError
        response_text = result.content[0].text
        response_data = json.loads(response_text)

        # Should return success with deleted indicator
        assert response_data["success"] is True
        assert "deleted" in response_data["data"]
        assert response_data["data"]["deleted"] is True


# ============================================================================
# Integration-like Tests
# ============================================================================


class TestSonarrMCPServerIntegration:
    """Test suite for integration-like scenarios."""

    @pytest.mark.asyncio
    async def test_complete_series_workflow(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test a complete workflow: search, add, get episodes, search episode."""
        # Step 1: Search for a series
        mock_sonarr_client.search_series.return_value = [
            {
                "title": "Breaking Bad",
                "tvdbId": 81189,
                "year": 2008,
            }
        ]

        search_result = await sonarr_mcp_server.call_tool(  # noqa: F841
            "sonarr_search_series", {"term": "Breaking Bad"}
        )
        assert not search_result.isError

        # Step 2: Add the series
        mock_sonarr_client.add_series.return_value = {
            "id": 1,
            "title": "Breaking Bad",
            "tvdbId": 81189,
        }

        add_result = await sonarr_mcp_server.call_tool(  # noqa: F841
            "sonarr_add_series",
            {
                "tvdb_id": 81189,
                "quality_profile_id": 1,
                "root_folder_path": "/tv",
            },
        )
        assert not add_result.isError

        # Step 3: Get episodes
        mock_sonarr_client.get_episodes.return_value = [
            {
                "id": 1,
                "seriesId": 1,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "Pilot",
                "hasFile": False,
            }
        ]

        episodes_result = await sonarr_mcp_server.call_tool(
            "sonarr_get_episodes", {"series_id": 1}
        )  # noqa: F841
        assert not episodes_result.isError

        # Step 4: Search for episode
        mock_sonarr_client.search_episode.return_value = {
            "id": 100,
            "name": "EpisodeSearch",
        }

        search_ep_result = await sonarr_mcp_server.call_tool(  # noqa: F841
            "sonarr_search_episode", {"episode_id": 1}
        )
        assert not search_ep_result.isError

    @pytest.mark.asyncio
    async def test_all_tools_are_callable(self, sonarr_mcp_server, mock_sonarr_client) -> None:
        """Test that all registered tools can be called without crashing."""
        # Setup mock returns
        mock_sonarr_client.get_series.return_value = []
        mock_sonarr_client.get_series_by_id.return_value = {"id": 1}
        mock_sonarr_client.search_series.return_value = []
        mock_sonarr_client.add_series.return_value = {"id": 1}
        mock_sonarr_client.get_episodes.return_value = []
        mock_sonarr_client.search_episode.return_value = {"id": 100}
        mock_sonarr_client.get_queue.return_value = {"records": []}
        mock_sonarr_client.get_calendar.return_value = []
        mock_sonarr_client.get_wanted_missing.return_value = {"records": []}
        mock_sonarr_client.delete_series.return_value = {}

        tools = sonarr_mcp_server.list_tools()

        for tool in tools:
            # Create minimal valid arguments
            args = {}
            if "series_id" in tool.inputSchema.get("required", []):
                args["series_id"] = 1
            if "episode_id" in tool.inputSchema.get("required", []):
                args["episode_id"] = 1
            if "term" in tool.inputSchema.get("required", []):
                args["term"] = "test"
            if "tvdb_id" in tool.inputSchema.get("required", []):
                args["tvdb_id"] = 12345
            if "quality_profile_id" in tool.inputSchema.get("required", []):
                args["quality_profile_id"] = 1
            if "root_folder_path" in tool.inputSchema.get("required", []):
                args["root_folder_path"] = "/tv"

            # Call the tool
            result = await sonarr_mcp_server.call_tool(tool.name, args)  # noqa: F841

            # Should not crash (may error if args are invalid, but shouldn't crash)
            assert result is not None
            assert hasattr(result, "content")
