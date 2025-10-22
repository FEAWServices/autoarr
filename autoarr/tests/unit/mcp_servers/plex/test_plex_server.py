"""
Unit tests for Plex MCP Server.

This module tests the MCP server implementation for Plex, including tool
registration, tool execution, and error handling. These tests follow TDD
principles and should be written BEFORE the implementation.

Test Coverage Strategy:
- MCP server initialization
- Tool registration and listing
- Tool execution for all Plex operations
- Error handling and validation
- Response formatting

Target Coverage: 90%+ for the Plex MCP server class
"""

import json
from unittest.mock import AsyncMock

import pytest

# Import the MCP server and client
from autoarr.mcp_servers.mcp_servers.plex.client import (
    PlexClient,
    PlexClientError,
    PlexConnectionError,
)
from autoarr.mcp_servers.mcp_servers.plex.server import PlexMCPServer

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_plex_client():
    """Create a mock Plex client for testing."""
    client = AsyncMock(spec=PlexClient)  # noqa: F841
    client.health_check = AsyncMock(return_value=True)
    client.get_libraries = AsyncMock(return_value=[])
    client.get_library_items = AsyncMock(return_value=[])
    client.get_recently_added = AsyncMock(return_value=[])
    client.get_on_deck = AsyncMock(return_value=[])
    client.get_sessions = AsyncMock(return_value=[])
    client.search = AsyncMock(return_value=[])
    client.refresh_library = AsyncMock(return_value={"success": True})
    client.get_history = AsyncMock(return_value=[])
    client.close = AsyncMock()
    return client


@pytest.fixture
def plex_server(mock_plex_client):
    """Create a Plex MCP server instance for testing."""
    return PlexMCPServer(client=mock_plex_client)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestPlexMCPServerInitialization:
    """Test suite for MCP server initialization."""

    def test_server_requires_client(self) -> None:
        """Test that server initialization requires a client."""
        with pytest.raises(ValueError):
            PlexMCPServer(client=None)

    def test_server_initializes_with_client(self, mock_plex_client) -> None:
        """Test that server initializes correctly with a client."""
        server = PlexMCPServer(client=mock_plex_client)

        assert server.client == mock_plex_client  # noqa: F841
        assert server.name == "plex"
        assert server.version == "0.1.0"

    def test_server_has_internal_mcp_server(self, plex_server) -> None:
        """Test that server creates an internal MCP Server instance."""
        assert plex_server._server is not None


# ============================================================================
# Tool Registration Tests
# ============================================================================


class TestPlexMCPServerToolRegistration:
    """Test suite for tool registration and listing."""

    def test_server_lists_all_tools(self, plex_server) -> None:
        """Test that server lists all available tools."""
        tools = plex_server.list_tools()

        tool_names = [tool.name for tool in tools]

        assert "plex_get_libraries" in tool_names
        assert "plex_get_library_items" in tool_names
        assert "plex_get_recently_added" in tool_names
        assert "plex_get_on_deck" in tool_names
        assert "plex_get_sessions" in tool_names
        assert "plex_search" in tool_names
        assert "plex_refresh_library" in tool_names
        assert "plex_get_history" in tool_names

    def test_all_tools_have_descriptions(self, plex_server) -> None:
        """Test that all tools have descriptions."""
        tools = plex_server.list_tools()

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0

    def test_all_tools_have_input_schemas(self, plex_server) -> None:
        """Test that all tools have valid input schemas."""
        tools = plex_server.list_tools()

        for tool in tools:
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    def test_get_tool_by_name(self, plex_server) -> None:
        """Test that get_tool retrieves a specific tool."""
        tool = plex_server.get_tool("plex_get_libraries")

        assert tool is not None
        assert tool.name == "plex_get_libraries"

    def test_get_tool_returns_none_for_invalid_name(self, plex_server) -> None:
        """Test that get_tool returns None for invalid tool name."""
        tool = plex_server.get_tool("nonexistent_tool")

        assert tool is None


# ============================================================================
# Tool Execution Tests - Get Libraries
# ============================================================================


class TestPlexMCPServerGetLibraries:
    """Test suite for plex_get_libraries tool."""

    @pytest.mark.asyncio
    async def test_get_libraries_returns_success(
        self, plex_server, mock_plex_client, plex_library_factory: callable
    ) -> None:
        """Test that plex_get_libraries returns library list."""
        libraries = [
            plex_library_factory(library_id="1", title="Movies"),
            plex_library_factory(library_id="2", title="TV Shows"),
        ]
        mock_plex_client.get_libraries.return_value = libraries

        result = await plex_server.call_tool("plex_get_libraries", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_libraries_handles_empty_list(self, plex_server, mock_plex_client) -> None:
        """Test that plex_get_libraries handles empty library list."""
        mock_plex_client.get_libraries.return_value = []

        result = await plex_server.call_tool("plex_get_libraries", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert data["data"] == []


# ============================================================================
# Tool Execution Tests - Get Library Items
# ============================================================================


class TestPlexMCPServerGetLibraryItems:
    """Test suite for plex_get_library_items tool."""

    @pytest.mark.asyncio
    async def test_get_library_items_returns_items(
        self, plex_server, mock_plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that plex_get_library_items returns media items."""
        items = [
            plex_media_item_factory(title="Movie 1"),
            plex_media_item_factory(title="Movie 2"),
        ]
        mock_plex_client.get_library_items.return_value = items

        result = await plex_server.call_tool(
            "plex_get_library_items", {"library_id": "1"}
        )  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_library_items_requires_library_id(self, plex_server) -> None:
        """Test that plex_get_library_items requires library_id."""
        result = await plex_server.call_tool("plex_get_library_items", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "library_id" in data["error"]

    @pytest.mark.asyncio
    async def test_get_library_items_validates_library_id(self, plex_server) -> None:
        """Test that plex_get_library_items validates library_id."""
        result = await plex_server.call_tool(
            "plex_get_library_items", {"library_id": ""}
        )  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_get_library_items_supports_pagination(
        self, plex_server, mock_plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that plex_get_library_items supports pagination."""
        items = [plex_media_item_factory(title=f"Movie {i}") for i in range(5)]
        mock_plex_client.get_library_items.return_value = items

        result = await plex_server.call_tool(  # noqa: F841
            "plex_get_library_items", {"library_id": "1", "limit": 5, "offset": 10}
        )

        mock_plex_client.get_library_items.assert_called_once_with(
            library_id="1", limit=5, offset=10
        )


# ============================================================================
# Tool Execution Tests - Recently Added
# ============================================================================


class TestPlexMCPServerGetRecentlyAdded:
    """Test suite for plex_get_recently_added tool."""

    @pytest.mark.asyncio
    async def test_get_recently_added_returns_items(
        self, plex_server, mock_plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that plex_get_recently_added returns recent items."""
        items = [plex_media_item_factory(title=f"Recent {i}") for i in range(10)]
        mock_plex_client.get_recently_added.return_value = items

        result = await plex_server.call_tool("plex_get_recently_added", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 10

    @pytest.mark.asyncio
    async def test_get_recently_added_supports_limit(
        self, plex_server, mock_plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that plex_get_recently_added supports limit parameter."""
        items = [plex_media_item_factory(title=f"Recent {i}") for i in range(5)]
        mock_plex_client.get_recently_added.return_value = items

        result = await plex_server.call_tool("plex_get_recently_added", {"limit": 5})  # noqa: F841

        mock_plex_client.get_recently_added.assert_called_once_with(limit=5)


# ============================================================================
# Tool Execution Tests - On Deck
# ============================================================================


class TestPlexMCPServerGetOnDeck:
    """Test suite for plex_get_on_deck tool."""

    @pytest.mark.asyncio
    async def test_get_on_deck_returns_items(
        self, plex_server, mock_plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that plex_get_on_deck returns On Deck items."""
        items = [plex_media_item_factory(title=f"On Deck {i}") for i in range(3)]
        mock_plex_client.get_on_deck.return_value = items

        result = await plex_server.call_tool("plex_get_on_deck", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 3


# ============================================================================
# Tool Execution Tests - Sessions
# ============================================================================


class TestPlexMCPServerGetSessions:
    """Test suite for plex_get_sessions tool."""

    @pytest.mark.asyncio
    async def test_get_sessions_returns_active_sessions(
        self, plex_server, mock_plex_client, plex_session_factory: callable
    ) -> None:
        """Test that plex_get_sessions returns active sessions."""
        sessions = [
            plex_session_factory(user="User1"),
            plex_session_factory(user="User2"),
        ]
        mock_plex_client.get_sessions.return_value = sessions

        result = await plex_server.call_tool("plex_get_sessions", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_sessions_handles_no_sessions(self, plex_server, mock_plex_client) -> None:
        """Test that plex_get_sessions handles no active sessions."""
        mock_plex_client.get_sessions.return_value = []

        result = await plex_server.call_tool("plex_get_sessions", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert data["data"] == []


# ============================================================================
# Tool Execution Tests - Search
# ============================================================================


class TestPlexMCPServerSearch:
    """Test suite for plex_search tool."""

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, plex_server, mock_plex_client, plex_search_results_factory: callable
    ) -> None:
        """Test that plex_search returns search results."""
        results = plex_search_results_factory(count=5, query="matrix")
        mock_plex_client.search.return_value = results

        result = await plex_server.call_tool("plex_search", {"query": "matrix"})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 5

    @pytest.mark.asyncio
    async def test_search_requires_query(self, plex_server) -> None:
        """Test that plex_search requires query parameter."""
        result = await plex_server.call_tool("plex_search", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "query" in data["error"]

    @pytest.mark.asyncio
    async def test_search_validates_query(self, plex_server) -> None:
        """Test that plex_search validates query parameter."""
        result = await plex_server.call_tool("plex_search", {"query": ""})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_search_supports_limit(
        self, plex_server, mock_plex_client, plex_search_results_factory: callable
    ) -> None:
        """Test that plex_search supports limit parameter."""
        results = plex_search_results_factory(count=3)
        mock_plex_client.search.return_value = results

        result = await plex_server.call_tool(
            "plex_search", {"query": "test", "limit": 3}
        )  # noqa: F841

        mock_plex_client.search.assert_called_once_with(query="test", limit=3, section_id=None)

    @pytest.mark.asyncio
    async def test_search_supports_section_filter(
        self, plex_server, mock_plex_client, plex_search_results_factory: callable
    ) -> None:
        """Test that plex_search supports section_id parameter."""
        results = plex_search_results_factory(count=2)
        mock_plex_client.search.return_value = results

        result = await plex_server.call_tool(
            "plex_search", {"query": "test", "section_id": "1"}
        )  # noqa: F841

        mock_plex_client.search.assert_called_once_with(query="test", limit=None, section_id="1")


# ============================================================================
# Tool Execution Tests - Refresh Library
# ============================================================================


class TestPlexMCPServerRefreshLibrary:
    """Test suite for plex_refresh_library tool."""

    @pytest.mark.asyncio
    async def test_refresh_library_triggers_scan(self, plex_server, mock_plex_client) -> None:
        """Test that plex_refresh_library triggers library scan."""
        mock_plex_client.refresh_library.return_value = {"success": True, "library_id": "1"}

        result = await plex_server.call_tool(
            "plex_refresh_library", {"library_id": "1"}
        )  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        mock_plex_client.refresh_library.assert_called_once_with(library_id="1")

    @pytest.mark.asyncio
    async def test_refresh_library_requires_library_id(self, plex_server) -> None:
        """Test that plex_refresh_library requires library_id."""
        result = await plex_server.call_tool("plex_refresh_library", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "library_id" in data["error"]


# ============================================================================
# Tool Execution Tests - History
# ============================================================================


class TestPlexMCPServerGetHistory:
    """Test suite for plex_get_history tool."""

    @pytest.mark.asyncio
    async def test_get_history_returns_watch_history(
        self, plex_server, mock_plex_client, plex_history_factory: callable
    ) -> None:
        """Test that plex_get_history returns watch history."""
        history = plex_history_factory(records=10)
        mock_plex_client.get_history.return_value = history

        result = await plex_server.call_tool("plex_get_history", {})  # noqa: F841

        assert not result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is True
        assert len(data["data"]) == 10

    @pytest.mark.asyncio
    async def test_get_history_supports_pagination(
        self, plex_server, mock_plex_client, plex_history_factory: callable
    ) -> None:
        """Test that plex_get_history supports pagination."""
        history = plex_history_factory(records=5)
        mock_plex_client.get_history.return_value = history

        result = await plex_server.call_tool(
            "plex_get_history", {"limit": 5, "offset": 10}
        )  # noqa: F841

        mock_plex_client.get_history.assert_called_once_with(limit=5, offset=10)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestPlexMCPServerErrorHandling:
    """Test suite for error handling."""

    @pytest.mark.asyncio
    async def test_server_handles_unknown_tool(self, plex_server) -> None:
        """Test that server handles unknown tool names."""
        result = await plex_server.call_tool("unknown_tool", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_server_handles_connection_errors(self, plex_server, mock_plex_client) -> None:
        """Test that server handles Plex connection errors."""
        mock_plex_client.get_libraries.side_effect = PlexConnectionError("Connection refused")

        result = await plex_server.call_tool("plex_get_libraries", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "Connection error" in data["error"]

    @pytest.mark.asyncio
    async def test_server_handles_client_errors(self, plex_server, mock_plex_client) -> None:
        """Test that server handles Plex client errors."""
        mock_plex_client.get_libraries.side_effect = PlexClientError("Unauthorized: Invalid token")

        result = await plex_server.call_tool("plex_get_libraries", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "Unauthorized" in data["error"]

    @pytest.mark.asyncio
    async def test_server_handles_unexpected_errors(self, plex_server, mock_plex_client) -> None:
        """Test that server handles unexpected errors gracefully."""
        mock_plex_client.get_libraries.side_effect = Exception("Unexpected error")

        result = await plex_server.call_tool("plex_get_libraries", {})  # noqa: F841

        assert result.isError
        content = result.content[0].text
        data = json.loads(content)
        assert data["success"] is False
        assert "Unexpected error" in data["error"]


# ============================================================================
# Server Lifecycle Tests
# ============================================================================


class TestPlexMCPServerLifecycle:
    """Test suite for server lifecycle operations."""

    @pytest.mark.asyncio
    async def test_server_start_validates_connection(self, plex_server, mock_plex_client) -> None:
        """Test that server start validates Plex connection."""
        mock_plex_client.health_check.return_value = True

        await plex_server.start()

        mock_plex_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_start_fails_on_unhealthy_connection(
        self, plex_server, mock_plex_client
    ) -> None:
        """Test that server start fails if Plex is unhealthy."""
        mock_plex_client.health_check.return_value = False

        with pytest.raises(PlexClientError):
            await plex_server.start()

    @pytest.mark.asyncio
    async def test_server_stop_closes_client(self, plex_server, mock_plex_client) -> None:
        """Test that server stop closes the Plex client."""
        await plex_server.stop()

        mock_plex_client.close.assert_called_once()
