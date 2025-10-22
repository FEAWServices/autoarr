"""
Unit tests for Plex API Client.

This module tests the Plex API client wrapper that handles all HTTP communication
with the Plex Media Server API. These tests follow TDD principles and should be written BEFORE
the implementation.

Test Coverage Strategy:
- Connection and authentication
- All API endpoints (libraries, sessions, search, history, etc.)
- Error handling and retries
- XML and JSON response parsing
- Edge cases and boundary conditions

Target Coverage: 90%+ for the Plex client class
"""

import pytest
from httpx import HTTPError
from pytest_httpx import HTTPXMock

# Import the actual client
from autoarr.mcp_servers.mcp_servers.plex.client import (
    PlexClient,
    PlexClientError,
    PlexConnectionError,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def plex_url() -> str:
    """Return a test Plex URL."""
    return "http://localhost:32400"


@pytest.fixture
def plex_token() -> str:
    """Return a test Plex token."""
    return "test_plex_token_12345"


@pytest.fixture
def plex_client(plex_url: str, plex_token: str):
    """Create a Plex client instance for testing."""
    return PlexClient(url=plex_url, token=plex_token)


# ============================================================================
# Connection and Initialization Tests
# ============================================================================


class TestPlexClientInitialization:
    """Test suite for client initialization and connection."""

    def test_client_requires_url(self, plex_token: str) -> None:
        """Test that client initialization requires a URL."""
        with pytest.raises((ValueError, TypeError)):
            PlexClient(url="", token=plex_token)

    def test_client_requires_token(self, plex_url: str) -> None:
        """Test that client initialization requires a token."""
        with pytest.raises(ValueError):
            PlexClient(url=plex_url, token="")

    def test_client_normalizes_url(self, plex_token: str) -> None:
        """Test that client normalizes URLs (removes trailing slash)."""
        client = PlexClient(url="http://localhost:32400/", token=plex_token)  # noqa: F841
        assert client.url == "http://localhost:32400"

    def test_client_accepts_custom_timeout(self, plex_url: str, plex_token: str) -> None:
        """Test that client accepts custom timeout values."""
        client = PlexClient(url=plex_url, token=plex_token, timeout=60.0)  # noqa: F841
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_client_validates_connection_on_init(
        self,
        httpx_mock: HTTPXMock,
        plex_url: str,
        plex_token: str,
        plex_server_identity_factory: callable,
    ) -> None:
        """Test that client optionally validates connection on initialization."""
        identity = plex_server_identity_factory()
        httpx_mock.add_response(
            url=f"{plex_url}/",
            json=identity,
        )
        client = await PlexClient.create(
            url=plex_url, token=plex_token, validate_connection=True
        )  # noqa: F841
        assert client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_client_validation_fails_gracefully(
        self, httpx_mock: HTTPXMock, plex_url: str, plex_token: str
    ) -> None:
        """Test that connection validation handles failures gracefully."""
        httpx_mock.add_response(status_code=500)

        with pytest.raises(PlexConnectionError):
            await PlexClient.create(url=plex_url, token=plex_token, validate_connection=True)


# ============================================================================
# System Operations Tests
# ============================================================================


class TestPlexClientSystemOperations:
    """Test suite for system-related operations."""

    @pytest.mark.asyncio
    async def test_get_server_identity_returns_data(
        self, httpx_mock: HTTPXMock, plex_client, plex_server_identity_factory: callable
    ) -> None:
        """Test that get_server_identity returns server information."""
        identity = plex_server_identity_factory(
            version="1.40.0.7998",
            platform="Linux",
            machine_identifier="test123",
        )
        httpx_mock.add_response(json=identity)

        result = await plex_client.get_server_identity()  # noqa: F841

        assert "machineIdentifier" in result
        assert result["version"] == "1.40.0.7998"
        assert result["platform"] == "Linux"

    @pytest.mark.asyncio
    async def test_health_check_returns_true_on_success(
        self, httpx_mock: HTTPXMock, plex_client, plex_server_identity_factory: callable
    ) -> None:
        """Test that health_check returns True when server is healthy."""
        identity = plex_server_identity_factory()
        httpx_mock.add_response(json=identity)

        is_healthy = await plex_client.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_failure(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that health_check returns False when server is unreachable."""
        httpx_mock.add_response(status_code=500)

        is_healthy = await plex_client.health_check()

        assert is_healthy is False


# ============================================================================
# Library Operations Tests
# ============================================================================


class TestPlexClientLibraryOperations:
    """Test suite for library-related operations."""

    @pytest.mark.asyncio
    async def test_get_libraries_returns_library_list(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that get_libraries returns list of libraries."""
        libraries = [
            plex_library_factory(library_id="1", title="Movies", library_type="movie"),
            plex_library_factory(library_id="2", title="TV Shows", library_type="show"),
        ]
        httpx_mock.add_response(json={"MediaContainer": {"Directory": libraries}})

        result = await plex_client.get_libraries()  # noqa: F841

        assert len(result) == 2
        assert result[0]["title"] == "Movies"
        assert result[1]["title"] == "TV Shows"

    @pytest.mark.asyncio
    async def test_get_libraries_handles_single_library(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that get_libraries handles single library correctly."""
        library = plex_library_factory(library_id="1", title="Movies")
        httpx_mock.add_response(json={"MediaContainer": {"Directory": library}})

        result = await plex_client.get_libraries()  # noqa: F841

        assert len(result) == 1
        assert result[0]["title"] == "Movies"

    @pytest.mark.asyncio
    async def test_get_libraries_handles_empty_response(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that get_libraries handles empty library list."""
        httpx_mock.add_response(json={"MediaContainer": {}})

        result = await plex_client.get_libraries()  # noqa: F841

        assert result == []  # noqa: F841

    @pytest.mark.asyncio
    async def test_get_library_items_returns_media_items(
        self, httpx_mock: HTTPXMock, plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that get_library_items returns items from a library."""
        items = [
            plex_media_item_factory(title="Movie 1"),
            plex_media_item_factory(title="Movie 2"),
            plex_media_item_factory(title="Movie 3"),
        ]
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": items}})

        result = await plex_client.get_library_items("1")  # noqa: F841

        assert len(result) == 3
        assert result[0]["title"] == "Movie 1"

    @pytest.mark.asyncio
    async def test_get_library_items_supports_pagination(
        self, httpx_mock: HTTPXMock, plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that get_library_items supports limit and offset."""
        items = [plex_media_item_factory(title=f"Movie {i}") for i in range(5)]
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": items}})

        result = await plex_client.get_library_items("1", limit=5, offset=10)  # noqa: F841

        request = httpx_mock.get_request()
        assert "X-Plex-Container-Size=5" in str(request.url)
        assert "X-Plex-Container-Start=10" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_recently_added_returns_recent_content(
        self, httpx_mock: HTTPXMock, plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that get_recently_added returns recently added items."""
        items = [plex_media_item_factory(title=f"Recent {i}") for i in range(5)]
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": items}})

        result = await plex_client.get_recently_added(limit=5)  # noqa: F841

        assert len(result) == 5
        assert result[0]["title"] == "Recent 0"

    @pytest.mark.asyncio
    async def test_get_on_deck_returns_continue_watching(
        self, httpx_mock: HTTPXMock, plex_client, plex_media_item_factory: callable
    ) -> None:
        """Test that get_on_deck returns On Deck items."""
        items = [plex_media_item_factory(title=f"On Deck {i}") for i in range(3)]
        httpx_mock.add_response(json={"MediaContainer": {"Video": items}})

        result = await plex_client.get_on_deck(limit=3)  # noqa: F841

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_refresh_library_sends_refresh_command(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that refresh_library triggers library scan."""
        httpx_mock.add_response(status_code=200, json={})

        result = await plex_client.refresh_library("1")  # noqa: F841

        request = httpx_mock.get_request()
        assert "/library/sections/1/refresh" in str(request.url)
        assert result["success"] is True
        assert result["library_id"] == "1"


# ============================================================================
# Session and Playback Operations Tests
# ============================================================================


class TestPlexClientSessionOperations:
    """Test suite for session and playback operations."""

    @pytest.mark.asyncio
    async def test_get_sessions_returns_active_sessions(
        self, httpx_mock: HTTPXMock, plex_client, plex_session_factory: callable
    ) -> None:
        """Test that get_sessions returns currently playing sessions."""
        sessions = [
            plex_session_factory(user="User1", title="Movie 1"),
            plex_session_factory(user="User2", title="Movie 2"),
        ]
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": sessions}})

        result = await plex_client.get_sessions()  # noqa: F841

        assert len(result) == 2
        assert result[0]["User"]["title"] == "User1"

    @pytest.mark.asyncio
    async def test_get_sessions_handles_empty_sessions(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that get_sessions handles no active sessions."""
        httpx_mock.add_response(json={"MediaContainer": {}})

        result = await plex_client.get_sessions()  # noqa: F841

        assert result == []  # noqa: F841

    @pytest.mark.asyncio
    async def test_get_history_returns_watch_history(
        self, httpx_mock: HTTPXMock, plex_client, plex_history_factory: callable
    ) -> None:
        """Test that get_history returns watch history."""
        history = plex_history_factory(records=10)
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": history}})

        result = await plex_client.get_history(limit=10)  # noqa: F841

        assert len(result) == 10
        assert "viewedAt" in result[0]

    @pytest.mark.asyncio
    async def test_get_history_supports_pagination(
        self, httpx_mock: HTTPXMock, plex_client, plex_history_factory: callable
    ) -> None:
        """Test that get_history supports limit and offset."""
        history = plex_history_factory(records=5)
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": history}})

        result = await plex_client.get_history(limit=5, offset=10)  # noqa: F841

        request = httpx_mock.get_request()
        assert "X-Plex-Container-Size=5" in str(request.url)
        assert "X-Plex-Container-Start=10" in str(request.url)


# ============================================================================
# Search Operations Tests
# ============================================================================


class TestPlexClientSearchOperations:
    """Test suite for search operations."""

    @pytest.mark.asyncio
    async def test_search_returns_results(
        self, httpx_mock: HTTPXMock, plex_client, plex_search_results_factory: callable
    ) -> None:
        """Test that search returns search results."""
        results = plex_search_results_factory(count=5, query="matrix")
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": results}})

        result = await plex_client.search("matrix")  # noqa: F841

        assert len(result) == 5
        assert "matrix" in result[0]["summary"].lower()

    @pytest.mark.asyncio
    async def test_search_supports_limit(
        self, httpx_mock: HTTPXMock, plex_client, plex_search_results_factory: callable
    ) -> None:
        """Test that search supports limit parameter."""
        results = plex_search_results_factory(count=3)
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": results}})

        result = await plex_client.search("test", limit=3)  # noqa: F841

        request = httpx_mock.get_request()
        assert "limit=3" in str(request.url)

    @pytest.mark.asyncio
    async def test_search_supports_section_filter(
        self, httpx_mock: HTTPXMock, plex_client, plex_search_results_factory: callable
    ) -> None:
        """Test that search can filter by section ID."""
        results = plex_search_results_factory(count=2)
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": results}})

        result = await plex_client.search("test", section_id="1")  # noqa: F841

        request = httpx_mock.get_request()
        assert "sectionId=1" in str(request.url)

    @pytest.mark.asyncio
    async def test_search_handles_no_results(self, httpx_mock: HTTPXMock, plex_client) -> None:
        """Test that search handles empty results."""
        httpx_mock.add_response(json={"MediaContainer": {}})

        result = await plex_client.search("nonexistent")  # noqa: F841

        assert result == []  # noqa: F841


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestPlexClientErrorHandling:
    """Test suite for error handling and retries."""

    @pytest.mark.asyncio
    async def test_client_handles_401_unauthorized(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that client handles 401 unauthorized errors."""
        httpx_mock.add_response(status_code=401)

        with pytest.raises(PlexClientError) as exc_info:
            await plex_client.get_libraries()

        assert "Unauthorized" in str(exc_info.value)
        assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_handles_404_not_found(self, httpx_mock: HTTPXMock, plex_client) -> None:
        """Test that client handles 404 not found errors."""
        httpx_mock.add_response(status_code=404)

        with pytest.raises(PlexClientError) as exc_info:
            await plex_client.get_library_items("999")

        assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_retries_on_503_service_unavailable(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that client retries on 503 errors."""
        # First two requests fail, third succeeds
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(status_code=503)
        libraries = [plex_library_factory()]
        httpx_mock.add_response(json={"MediaContainer": {"Directory": libraries}})

        result = await plex_client.get_libraries()  # noqa: F841

        assert len(result) == 1
        assert len(httpx_mock.get_requests()) == 3

    @pytest.mark.asyncio
    async def test_client_fails_after_max_retries(self, httpx_mock: HTTPXMock, plex_client) -> None:
        """Test that client fails after max retries."""
        # All requests fail
        for _ in range(3):
            httpx_mock.add_response(status_code=503)

        with pytest.raises(PlexClientError) as exc_info:
            await plex_client.get_libraries()

        assert "503" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_handles_500_server_error(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that client handles 500 server errors."""
        httpx_mock.add_response(status_code=500)

        with pytest.raises(PlexClientError) as exc_info:
            await plex_client.get_libraries()

        assert "Server error" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_handles_connection_errors(
        self, httpx_mock: HTTPXMock, plex_client
    ) -> None:
        """Test that client handles network connection errors."""
        httpx_mock.add_exception(HTTPError("Connection refused"))

        with pytest.raises(PlexConnectionError) as exc_info:
            await plex_client.get_libraries()

        assert "Connection failed" in str(exc_info.value)


# ============================================================================
# Response Parsing Tests
# ============================================================================


class TestPlexClientResponseParsing:
    """Test suite for response parsing (XML and JSON)."""

    @pytest.mark.asyncio
    async def test_client_parses_json_response(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that client correctly parses JSON responses."""
        libraries = [plex_library_factory()]
        httpx_mock.add_response(
            json={"MediaContainer": {"Directory": libraries}},
            headers={"content-type": "application/json"},
        )

        result = await plex_client.get_libraries()  # noqa: F841

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_client_parses_xml_response(self, httpx_mock: HTTPXMock, plex_client) -> None:
        """Test that client correctly parses XML responses."""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
<MediaContainer size="1">
    <Directory key="1" title="Movies" type="movie" />
</MediaContainer>"""
        httpx_mock.add_response(
            text=xml_response,
            headers={"content-type": "application/xml"},
        )

        result = await plex_client.get_libraries()  # noqa: F841

        assert len(result) == 1
        assert result[0]["title"] == "Movies"

    @pytest.mark.asyncio
    async def test_client_handles_empty_response(self, httpx_mock: HTTPXMock, plex_client) -> None:
        """Test that client handles empty responses."""
        httpx_mock.add_response(text="", status_code=200)

        result = await plex_client.get_libraries()  # noqa: F841

        # Should return empty dict or list depending on endpoint
        assert result in [[], {}]

    @pytest.mark.asyncio
    async def test_client_handles_invalid_json(self, httpx_mock: HTTPXMock, plex_client) -> None:
        """Test that client handles invalid JSON responses."""
        httpx_mock.add_response(
            text="invalid json{",
            headers={"content-type": "application/json"},
        )

        with pytest.raises(PlexClientError) as exc_info:
            await plex_client.get_libraries()

        assert "Invalid response" in str(exc_info.value)


# ============================================================================
# Request Building Tests
# ============================================================================


class TestPlexClientRequestBuilding:
    """Test suite for request building and headers."""

    @pytest.mark.asyncio
    async def test_client_sends_auth_token_header(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that client includes X-Plex-Token in headers."""
        libraries = [plex_library_factory()]
        httpx_mock.add_response(json={"MediaContainer": {"Directory": libraries}})

        await plex_client.get_libraries()

        request = httpx_mock.get_request()
        assert "X-Plex-Token" in request.headers
        assert request.headers["X-Plex-Token"] == "test_plex_token_12345"

    @pytest.mark.asyncio
    async def test_client_sends_accept_json_header(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that client includes Accept header."""
        libraries = [plex_library_factory()]
        httpx_mock.add_response(json={"MediaContainer": {"Directory": libraries}})

        await plex_client.get_libraries()

        request = httpx_mock.get_request()
        assert "Accept" in request.headers
        assert "application/json" in request.headers["Accept"]

    @pytest.mark.asyncio
    async def test_client_builds_url_correctly(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that client builds URLs correctly."""
        libraries = [plex_library_factory()]
        httpx_mock.add_response(json={"MediaContainer": {"Directory": libraries}})

        await plex_client.get_libraries()

        request = httpx_mock.get_request()
        assert str(request.url).startswith("http://localhost:32400/")
        assert "library/sections" in str(request.url)

    @pytest.mark.asyncio
    async def test_client_converts_boolean_params(
        self, httpx_mock: HTTPXMock, plex_url: str, plex_token: str
    ) -> None:
        """Test that client converts boolean parameters to integers."""
        client = PlexClient(url=plex_url, token=plex_token)  # noqa: F841
        httpx_mock.add_response(json={})

        # Call a method that would use boolean params (using internal _request)
        await client._request("GET", "test", test_bool=True)

        request = httpx_mock.get_request()
        assert "test_bool=1" in str(request.url)

    @pytest.mark.asyncio
    async def test_client_filters_none_params(
        self, httpx_mock: HTTPXMock, plex_client, plex_library_factory: callable
    ) -> None:
        """Test that client filters out None parameters."""
        libraries = [plex_library_factory()]
        httpx_mock.add_response(json={"MediaContainer": {"Metadata": libraries}})

        await plex_client.get_library_items("1", limit=None, offset=None)

        request = httpx_mock.get_request()
        # Should not have limit or offset in URL
        assert "X-Plex-Container-Size" not in str(request.url)
        assert "X-Plex-Container-Start" not in str(request.url)


# ============================================================================
# Async Context Manager Tests
# ============================================================================


class TestPlexClientContextManager:
    """Test suite for async context manager support."""

    @pytest.mark.asyncio
    async def test_client_supports_async_context_manager(
        self, httpx_mock: HTTPXMock, plex_url: str, plex_token: str, plex_library_factory: callable
    ) -> None:
        """Test that client can be used as async context manager."""
        libraries = [plex_library_factory()]
        httpx_mock.add_response(json={"MediaContainer": {"Directory": libraries}})

        async with PlexClient(url=plex_url, token=plex_token) as client:
            result = await client.get_libraries()  # noqa: F841
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_client_closes_on_context_exit(self, plex_url: str, plex_token: str) -> None:
        """Test that client closes HTTP client on context exit."""
        client = PlexClient(url=plex_url, token=plex_token)  # noqa: F841

        async with client:
            # Initialize the client
            _ = client._get_client()

        # After context exit, client should be None
        assert client._client is None

    @pytest.mark.asyncio
    async def test_client_close_method(self, plex_url: str, plex_token: str) -> None:
        """Test that close method properly cleans up."""
        client = PlexClient(url=plex_url, token=plex_token)  # noqa: F841
        _ = client._get_client()

        await client.close()

        assert client._client is None
