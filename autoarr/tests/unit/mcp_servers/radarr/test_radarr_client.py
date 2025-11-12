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
Unit tests for Radarr API Client.

This module tests the Radarr API client wrapper that handles all HTTP communication
with the Radarr API v3. These tests follow TDD principles and are written BEFORE
the implementation to drive development through the red-green-refactor cycle.

Test Coverage Strategy:
- Connection and authentication (header-based API key)
- All API endpoints (movies, commands, calendar, queue, wanted)
- Error handling and retries
- Response parsing and validation
- Edge cases and boundary conditions

Target Coverage: 90%+ for the Radarr client class
"""

import json

import pytest
from httpx import HTTPError
from pytest_httpx import HTTPXMock

# Import the actual client - using new repository structure
from autoarr.mcp_servers.mcp_servers.radarr.client import (
    RadarrClient,
    RadarrClientError,
    RadarrConnectionError,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def radarr_url() -> str:
    """Return a test Radarr URL."""
    return "http://localhost:7878"


@pytest.fixture
def radarr_api_key() -> str:
    """Return a test API key."""
    return "test_api_key_radarr_12345"


@pytest.fixture
def radarr_client(radarr_url: str, radarr_api_key: str):
    """Create a Radarr client instance for testing."""
    return RadarrClient(url=radarr_url, api_key=radarr_api_key)


# ============================================================================
# Connection and Initialization Tests
# ============================================================================


class TestRadarrClientInitialization:
    """Test suite for client initialization and connection."""

    def test_client_requires_url(self, radarr_api_key: str) -> None:
        """Test that client initialization requires a URL."""
        with pytest.raises(ValueError, match="URL"):
            RadarrClient(url="", api_key=radarr_api_key)

    def test_client_requires_api_key(self, radarr_url: str) -> None:
        """Test that client initialization requires an API key."""
        with pytest.raises(ValueError, match="API key"):
            RadarrClient(url=radarr_url, api_key="")

    def test_client_normalizes_url(self, radarr_api_key: str) -> None:
        """Test that client normalizes URLs (removes trailing slash)."""
        client = RadarrClient(url="http://localhost:7878/", api_key=radarr_api_key)  # noqa: F841
        assert client.url == "http://localhost:7878"

    def test_client_accepts_custom_timeout(self, radarr_url: str, radarr_api_key: str) -> None:
        """Test that client accepts custom timeout values."""
        client = RadarrClient(url=radarr_url, api_key=radarr_api_key, timeout=60.0)  # noqa: F841
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_client_validates_connection_on_create(
        self,
        httpx_mock: HTTPXMock,
        radarr_url: str,
        radarr_api_key: str,
        radarr_system_status_factory: callable,
    ) -> None:
        """Test that client optionally validates connection on initialization."""
        mock_status = radarr_system_status_factory()
        httpx_mock.add_response(url=f"{radarr_url}/api/v3/system/status", json=mock_status)

        client = await RadarrClient.create(  # noqa: F841
            url=radarr_url, api_key=radarr_api_key, validate_connection=True
        )
        assert client is not None

        # Verify API key was in header
        request = httpx_mock.get_request()
        assert request.headers.get("X-Api-Key") == radarr_api_key

    @pytest.mark.asyncio
    async def test_client_health_check_returns_true_when_healthy(
        self,
        httpx_mock: HTTPXMock,
        radarr_client: RadarrClient,
        radarr_system_status_factory: callable,
    ) -> None:
        """Test that health_check returns True when Radarr is accessible."""
        mock_status = radarr_system_status_factory()
        httpx_mock.add_response(json=mock_status)

        is_healthy = await radarr_client.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_client_health_check_returns_false_when_unreachable(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that health_check returns False when Radarr is unreachable."""
        httpx_mock.add_exception(HTTPError("Connection failed"))

        is_healthy = await radarr_client.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_client_context_manager_closes_properly(
        self, radarr_url: str, radarr_api_key: str
    ) -> None:
        """Test that client properly closes when used as context manager."""
        async with RadarrClient(url=radarr_url, api_key=radarr_api_key) as client:
            assert client is not None
        # Client should be closed after exiting context


# ============================================================================
# Movie Operations Tests
# ============================================================================


class TestRadarrClientMovieOperations:
    """Test suite for movie-related operations."""

    @pytest.mark.asyncio
    async def test_get_movies_returns_all_movies(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that get_movies returns all movies."""
        mock_movies = [radarr_movie_factory(movie_id=i) for i in range(1, 4)]
        httpx_mock.add_response(json=mock_movies)

        result = await radarr_client.get_movies()  # noqa: F841

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 3

    @pytest.mark.asyncio
    async def test_get_movies_returns_empty_list_when_no_movies(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that get_movies returns empty list when no movies exist."""
        httpx_mock.add_response(json=[])

        result = await radarr_client.get_movies()  # noqa: F841

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_movie_by_id_returns_specific_movie(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that get_movie_by_id returns specific movie details."""
        mock_movie = radarr_movie_factory(movie_id=5, title="The Matrix")
        httpx_mock.add_response(json=mock_movie)

        result = await radarr_client.get_movie_by_id(movie_id=5)  # noqa: F841

        assert result["id"] == 5
        assert result["title"] == "The Matrix"

        # Verify correct endpoint was called
        request = httpx_mock.get_request()
        assert "/api/v3/movie/5" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_movie_by_id_raises_on_not_found(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that get_movie_by_id raises error for non-existent movie."""
        httpx_mock.add_response(status_code=404, json={"message": "NotFound"})

        with pytest.raises(RadarrClientError, match="404"):
            await radarr_client.get_movie_by_id(movie_id=999)

    @pytest.mark.asyncio
    async def test_add_movie_sends_correct_payload(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that add_movie sends correct POST request with movie data."""
        mock_movie = radarr_movie_factory(movie_id=1, title="Inception")
        httpx_mock.add_response(status_code=201, json=mock_movie)

        movie_data = {
            "title": "Inception",
            "tmdbId": 27205,
            "qualityProfileId": 1,
            "rootFolderPath": "/movies",
            "monitored": True,
            "minimumAvailability": "released",
        }

        result = await radarr_client.add_movie(movie_data)  # noqa: F841

        # Verify POST request was made
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "/api/v3/movie" in str(request.url)

        # Verify payload
        payload = json.loads(request.content)
        assert payload["tmdbId"] == 27205
        assert payload["qualityProfileId"] == 1
        assert payload["rootFolderPath"] == "/movies"

        assert result["title"] == "Inception"

    @pytest.mark.asyncio
    async def test_add_movie_validates_required_fields(self, radarr_client: RadarrClient) -> None:
        """Test that add_movie validates required fields."""
        # Missing tmdbId
        with pytest.raises(ValueError, match="tmdbId"):
            await radarr_client.add_movie({"title": "Test", "rootFolderPath": "/movies"})

        # Missing rootFolderPath
        with pytest.raises(ValueError, match="rootFolderPath"):
            await radarr_client.add_movie({"title": "Test", "tmdbId": 12345})

    @pytest.mark.asyncio
    async def test_add_movie_with_monitoring_options(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that add_movie includes monitoring and availability options."""
        mock_movie = radarr_movie_factory()
        httpx_mock.add_response(status_code=201, json=mock_movie)

        movie_data = {
            "title": "Test Movie",
            "tmdbId": 12345,
            "qualityProfileId": 1,
            "rootFolderPath": "/movies",
            "monitored": True,
            "minimumAvailability": "inCinemas",
        }

        await radarr_client.add_movie(movie_data)

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["monitored"] is True
        assert payload["minimumAvailability"] == "inCinemas"

    @pytest.mark.asyncio
    async def test_search_movie_lookup_returns_lookup_results(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that search_movie_lookup returns TMDb lookup results."""
        mock_results = [
            radarr_movie_factory(movie_id=0, title="The Matrix", tmdb_id=603),
            radarr_movie_factory(movie_id=0, title="The Matrix Reloaded", tmdb_id=604),
        ]
        httpx_mock.add_response(json=mock_results)

        result = await radarr_client.search_movie_lookup(term="The Matrix")  # noqa: F841

        # Verify search endpoint
        request = httpx_mock.get_request()
        assert "/api/v3/movie/lookup" in str(request.url)
        assert "term=" in str(request.url)

        assert len(result) == 2
        assert result[0]["title"] == "The Matrix"

    @pytest.mark.asyncio
    async def test_search_movie_lookup_by_tmdb_id(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that search_movie_lookup can lookup by TMDb ID."""
        mock_result = [radarr_movie_factory(tmdb_id=603)]  # noqa: F841
        httpx_mock.add_response(json=mock_result)

        result = await radarr_client.search_movie_lookup(term="tmdb:603")  # noqa: F841

        request = httpx_mock.get_request()
        assert "term=tmdb%3A603" in str(request.url) or "term=tmdb:603" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_movie_removes_movie(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that delete_movie sends DELETE request."""
        httpx_mock.add_response(status_code=200, json={})

        await radarr_client.delete_movie(movie_id=5)

        request = httpx_mock.get_request()
        assert request.method == "DELETE"
        assert "/api/v3/movie/5" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_movie_with_delete_files_flag(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that delete_movie includes deleteFiles query parameter."""
        httpx_mock.add_response(status_code=200, json={})

        await radarr_client.delete_movie(movie_id=5, delete_files=True)

        request = httpx_mock.get_request()
        assert "deleteFiles=true" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_movie_with_add_import_exclusion_flag(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that delete_movie includes addImportExclusion parameter."""
        httpx_mock.add_response(status_code=200, json={})

        await radarr_client.delete_movie(movie_id=5, delete_files=True, add_import_exclusion=True)

        request = httpx_mock.get_request()
        assert "addImportExclusion=true" in str(request.url)


# ============================================================================
# Command Operations Tests
# ============================================================================


class TestRadarrClientCommandOperations:
    """Test suite for command execution operations."""

    @pytest.mark.asyncio
    async def test_execute_command_posts_to_command_endpoint(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_command_factory: callable
    ) -> None:
        """Test that _execute_command POSTs to /api/v3/command."""
        mock_command = radarr_command_factory(name="TestCommand")
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await radarr_client._execute_command(
            "TestCommand", {"param": "value"}
        )  # noqa: F841

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "/api/v3/command" in str(request.url)

        payload = json.loads(request.content)
        assert payload["name"] == "TestCommand"
        assert payload["param"] == "value"

    @pytest.mark.asyncio
    async def test_get_command_status_returns_command_info(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_command_factory: callable
    ) -> None:
        """Test that get_command returns command status and progress."""
        mock_command = radarr_command_factory(
            command_id=50, status="completed", duration="00:02:30"
        )
        httpx_mock.add_response(json=mock_command)

        result = await radarr_client.get_command(command_id=50)  # noqa: F841

        assert result["id"] == 50
        assert result["status"] == "completed"
        assert result["duration"] == "00:02:30"

        request = httpx_mock.get_request()
        assert "/api/v3/command/50" in str(request.url)

    @pytest.mark.asyncio
    async def test_search_movie_triggers_movie_search_command(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_command_factory: callable
    ) -> None:
        """Test that search_movie triggers MoviesSearch command."""
        mock_command = radarr_command_factory(name="MoviesSearch", body={"movieIds": [3]})
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await radarr_client.search_movie(movie_id=3)  # noqa: F841

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["name"] == "MoviesSearch"
        assert 3 in payload["movieIds"]

    @pytest.mark.asyncio
    async def test_search_movie_returns_command_id(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_command_factory: callable
    ) -> None:
        """Test that search_movie returns command ID for tracking."""
        mock_command = radarr_command_factory(command_id=123)
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await radarr_client.search_movie(movie_id=10)  # noqa: F841

        assert "id" in result
        assert result["id"] == 123

    @pytest.mark.asyncio
    async def test_refresh_movie_triggers_refresh_movie_command(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_command_factory: callable
    ) -> None:
        """Test that refresh_movie triggers RefreshMovie command."""
        mock_command = radarr_command_factory(name="RefreshMovie", body={"movieId": 7})
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await radarr_client.refresh_movie(movie_id=7)  # noqa: F841

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["name"] == "RefreshMovie"
        assert payload["movieId"] == 7

    @pytest.mark.asyncio
    async def test_rescan_movie_triggers_rescan_movie_command(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_command_factory: callable
    ) -> None:
        """Test that rescan_movie triggers RescanMovie command."""
        mock_command = radarr_command_factory(name="RescanMovie")
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await radarr_client.rescan_movie(movie_id=4)  # noqa: F841

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["name"] == "RescanMovie"
        assert payload["movieId"] == 4


# ============================================================================
# Calendar, Queue, and Wanted Tests
# ============================================================================


class TestRadarrClientCalendarQueueWanted:
    """Test suite for calendar, queue, and wanted operations."""

    @pytest.mark.asyncio
    async def test_get_calendar_returns_upcoming_releases(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_calendar_factory: callable
    ) -> None:
        """Test that get_calendar returns movies releasing in date range."""
        mock_calendar = radarr_calendar_factory(days=7, movies_per_day=2)
        httpx_mock.add_response(json=mock_calendar)

        result = await radarr_client.get_calendar(
            start_date="2020-01-01", end_date="2020-01-07"
        )  # noqa: F841

        assert len(result) == 14  # 7 days * 2 movies per day

        request = httpx_mock.get_request()
        assert "/api/v3/calendar" in str(request.url)
        assert "start=" in str(request.url)
        assert "end=" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_calendar_defaults_to_current_week(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that get_calendar uses default date range when not specified."""
        httpx_mock.add_response(json=[])

        await radarr_client.get_calendar()

        request = httpx_mock.get_request()
        assert "/api/v3/calendar" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_queue_returns_download_queue(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_queue_factory: callable
    ) -> None:
        """Test that get_queue returns download queue with status."""
        mock_queue = radarr_queue_factory(records=3)
        httpx_mock.add_response(json=mock_queue)

        result = await radarr_client.get_queue()  # noqa: F841

        assert "records" in result
        assert len(result["records"]) == 3
        assert result["totalRecords"] == 3

        request = httpx_mock.get_request()
        assert "/api/v3/queue" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_queue_supports_pagination(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_queue_factory: callable
    ) -> None:
        """Test that get_queue supports page and pageSize parameters."""
        mock_queue = radarr_queue_factory(records=5, page=2, page_size=20)
        httpx_mock.add_response(json=mock_queue)

        result = await radarr_client.get_queue(page=2, page_size=20)  # noqa: F841

        request = httpx_mock.get_request()
        assert "page=2" in str(request.url)
        assert "pageSize=20" in str(request.url)

        assert result["page"] == 2
        assert result["pageSize"] == 20

    @pytest.mark.asyncio
    async def test_get_wanted_missing_returns_missing_movies(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_wanted_factory: callable
    ) -> None:
        """Test that get_wanted_missing returns paginated missing movies."""
        mock_wanted = radarr_wanted_factory(records=10)
        httpx_mock.add_response(json=mock_wanted)

        result = await radarr_client.get_wanted_missing()  # noqa: F841

        assert "records" in result
        assert len(result["records"]) == 10
        assert all(not movie["hasFile"] for movie in result["records"])

        request = httpx_mock.get_request()
        assert "/api/v3/wanted/missing" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_wanted_missing_supports_pagination(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_wanted_factory: callable
    ) -> None:
        """Test that get_wanted_missing supports pagination parameters."""
        mock_wanted = radarr_wanted_factory(records=5, page=3, page_size=10)
        httpx_mock.add_response(json=mock_wanted)

        result = await radarr_client.get_wanted_missing(page=3, page_size=10)  # noqa: F841

        request = httpx_mock.get_request()
        assert "page=3" in str(request.url)
        assert "pageSize=10" in str(request.url)


# ============================================================================
# System Status Tests
# ============================================================================


class TestRadarrClientSystemStatus:
    """Test suite for system status operations."""

    @pytest.mark.asyncio
    async def test_get_system_status_returns_status_info(
        self,
        httpx_mock: HTTPXMock,
        radarr_client: RadarrClient,
        radarr_system_status_factory: callable,
    ) -> None:
        """Test that get_system_status returns Radarr system information."""
        mock_status = radarr_system_status_factory(version="4.5.0.7244")
        httpx_mock.add_response(json=mock_status)

        result = await radarr_client.get_system_status()  # noqa: F841

        assert result["version"] == "4.5.0.7244"
        assert "osName" in result
        assert "isDocker" in result

        request = httpx_mock.get_request()
        assert "/api/v3/system/status" in str(request.url)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestRadarrClientErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_401_unauthorized_error(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of 401 Unauthorized (invalid API key)."""
        httpx_mock.add_response(status_code=401, json={"message": "Unauthorized"})

        with pytest.raises(RadarrClientError, match="Unauthorized|401"):
            await radarr_client.get_movies()

    @pytest.mark.asyncio
    async def test_handles_404_not_found_error(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of 404 Not Found errors."""
        httpx_mock.add_response(status_code=404, json={"message": "Movie not found"})

        with pytest.raises(RadarrClientError, match="404|not found"):
            await radarr_client.get_movie_by_id(movie_id=999)

    @pytest.mark.asyncio
    async def test_handles_500_server_error(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of 500 Internal Server Error."""
        httpx_mock.add_response(status_code=500, text="Internal Server Error")

        with pytest.raises(RadarrClientError, match="500|Server error"):
            await radarr_client.get_movies()

    @pytest.mark.asyncio
    async def test_handles_connection_timeout(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of connection timeout."""
        httpx_mock.add_exception(HTTPError("Timeout"))

        with pytest.raises(RadarrConnectionError, match="Timeout|Connection"):
            await radarr_client.get_movies()

    @pytest.mark.asyncio
    async def test_handles_network_error(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of network connection error."""
        httpx_mock.add_exception(HTTPError("Connection refused"))

        with pytest.raises(RadarrConnectionError, match="Connection refused"):
            await radarr_client.get_movies()

    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of invalid JSON in response."""
        httpx_mock.add_response(text="Not valid JSON{")

        with pytest.raises(RadarrClientError, match="Invalid JSON|JSON"):
            await radarr_client.get_movies()

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that client retries on transient 503 errors."""
        # First request fails with 503
        httpx_mock.add_response(status_code=503)
        # Second request succeeds
        httpx_mock.add_response(json=[])

        result = await radarr_client.get_movies()  # noqa: F841

        assert result is not None
        assert len(httpx_mock.get_requests()) == 2

    @pytest.mark.asyncio
    async def test_respects_max_retries(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that client respects maximum retry limit."""
        # Add exactly 3 503 responses to match max_retries (default 3)
        for _ in range(3):
            httpx_mock.add_response(status_code=503)

        with pytest.raises(RadarrClientError):
            await radarr_client.get_movies()

        # Should stop at max_retries (default 3)
        assert len(httpx_mock.get_requests()) == 3


# ============================================================================
# Authentication and Request Building Tests
# ============================================================================


class TestRadarrClientAuthentication:
    """Test suite for authentication and request building."""

    @pytest.mark.asyncio
    async def test_includes_api_key_in_headers(
        self, httpx_mock: HTTPXMock, radarr_url: str, radarr_api_key: str
    ) -> None:
        """Test that all requests include X-Api-Key header."""
        httpx_mock.add_response(json=[])

        client = RadarrClient(url=radarr_url, api_key=radarr_api_key)  # noqa: F841
        await client.get_movies()

        request = httpx_mock.get_request()
        assert request.headers.get("X-Api-Key") == radarr_api_key

    @pytest.mark.asyncio
    async def test_api_key_not_in_url(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_api_key: str
    ) -> None:
        """Test that API key is NOT included in URL query parameters."""
        httpx_mock.add_response(json=[])

        await radarr_client.get_movies()

        request = httpx_mock.get_request()
        # API key should be in header, not URL
        assert radarr_api_key not in str(request.url)
        assert "api_key" not in str(request.url).lower()
        assert "apikey" not in str(request.url).lower()

    @pytest.mark.asyncio
    async def test_builds_correct_api_v3_url(
        self, httpx_mock: HTTPXMock, radarr_url: str, radarr_api_key: str
    ) -> None:
        """Test that API URLs are built with /api/v3/ prefix."""
        httpx_mock.add_response(json=[])

        client = RadarrClient(url=radarr_url, api_key=radarr_api_key)  # noqa: F841
        await client.get_movies()

        request = httpx_mock.get_request()
        assert str(request.url).startswith(radarr_url)
        assert "/api/v3/movie" in str(request.url)

    @pytest.mark.asyncio
    async def test_includes_content_type_json_for_post(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test that POST requests include Content-Type: application/json."""
        mock_movie = radarr_movie_factory()
        httpx_mock.add_response(status_code=201, json=mock_movie)

        movie_data = {
            "title": "Test",
            "tmdbId": 12345,
            "qualityProfileId": 1,
            "rootFolderPath": "/movies",
        }
        await radarr_client.add_movie(movie_data)

        request = httpx_mock.get_request()
        assert request.headers.get("Content-Type") == "application/json"


# ============================================================================
# Resource Management Tests
# ============================================================================


class TestRadarrClientResourceManagement:
    """Test suite for resource management and performance."""

    @pytest.mark.asyncio
    async def test_client_properly_closes_connections(
        self, radarr_url: str, radarr_api_key: str
    ) -> None:
        """Test that client properly closes HTTP connections."""
        async with RadarrClient(url=radarr_url, api_key=radarr_api_key) as client:
            pass
        # Client should be closed after exiting context

    @pytest.mark.asyncio
    async def test_client_reuses_http_client(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that client reuses the same HTTP client for multiple requests."""
        httpx_mock.add_response(json=[])
        httpx_mock.add_response(json=[])

        await radarr_client.get_movies()
        await radarr_client.get_calendar()

        # Both requests should use the same client
        assert len(httpx_mock.get_requests()) == 2

    @pytest.mark.asyncio
    async def test_concurrent_requests_dont_conflict(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test that concurrent requests can be made safely."""
        import asyncio

        httpx_mock.add_response(json=[])
        httpx_mock.add_response(json={"page": 1, "records": []})
        httpx_mock.add_response(json={"version": "4.5.0"})

        results = await asyncio.gather(
            radarr_client.get_movies(),
            radarr_client.get_queue(),
            radarr_client.get_system_status(),
        )

        assert len(results) == 3


# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================


class TestRadarrClientEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_handles_empty_movie_list(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of empty movie list."""
        httpx_mock.add_response(json=[])

        result = await radarr_client.get_movies()  # noqa: F841

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_handles_large_movie_list(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test handling of large movie list (100+ movies)."""
        mock_movies = [radarr_movie_factory(movie_id=i) for i in range(150)]
        httpx_mock.add_response(json=mock_movies)

        result = await radarr_client.get_movies()  # noqa: F841

        assert len(result) == 150

    @pytest.mark.asyncio
    async def test_handles_special_characters_in_movie_title(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test handling of special characters in movie titles."""
        mock_movie = radarr_movie_factory(title="Test: The Movie (2020) - Part 1")
        httpx_mock.add_response(json=[mock_movie])

        result = await radarr_client.search_movie_lookup(
            term="Test: The Movie (2020) - Part 1"
        )  # noqa: F841

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient
    ) -> None:
        """Test handling of responses with missing optional fields."""
        minimal_movie = {"id": 1, "title": "Minimal Movie", "tmdbId": 12345, "monitored": True}
        httpx_mock.add_response(json=[minimal_movie])

        result = await radarr_client.get_movies()  # noqa: F841

        assert len(result) == 1
        assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_handles_null_values_in_response(
        self, httpx_mock: HTTPXMock, radarr_client: RadarrClient, radarr_movie_factory: callable
    ) -> None:
        """Test handling of null values in API responses."""
        movie = radarr_movie_factory()
        movie["inCinemas"] = None
        movie["overview"] = None

        httpx_mock.add_response(json=[movie])

        result = await radarr_client.get_movies()  # noqa: F841

        assert len(result) == 1
        assert result[0]["inCinemas"] is None
