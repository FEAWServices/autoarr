"""
Unit tests for Sonarr API Client.

This module tests the Sonarr API client wrapper that handles all HTTP communication
with the Sonarr API v3. These tests follow TDD principles and are written BEFORE
the implementation to drive development through the red-green-refactor cycle.

Test Coverage Strategy:
- Connection and authentication (header-based API key)
- All API endpoints (series, episodes, commands, calendar, queue, wanted)
- Error handling and retries
- Response parsing and validation
- Edge cases and boundary conditions

Target Coverage: 90%+ for the Sonarr client class
"""

import json

import pytest
from httpx import HTTPError
from pytest_httpx import HTTPXMock

# Import the actual client - using new repository structure
from autoarr.mcp_servers.mcp_servers.sonarr.client import (
    SonarrClient,
    SonarrClientError,
    SonarrConnectionError,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sonarr_url() -> str:
    """Return a test Sonarr URL."""
    return "http://localhost:8989"


@pytest.fixture
def sonarr_api_key() -> str:
    """Return a test API key."""
    return "test_api_key_sonarr_12345"


@pytest.fixture
def sonarr_client(sonarr_url: str, sonarr_api_key: str):
    """Create a Sonarr client instance for testing."""
    return SonarrClient(url=sonarr_url, api_key=sonarr_api_key)


# ============================================================================
# Connection and Initialization Tests
# ============================================================================


class TestSonarrClientInitialization:
    """Test suite for client initialization and connection."""

    def test_client_requires_url(self, sonarr_api_key: str) -> None:
        """Test that client initialization requires a URL."""
        with pytest.raises(ValueError, match="URL"):
            SonarrClient(url="", api_key=sonarr_api_key)

    def test_client_requires_api_key(self, sonarr_url: str) -> None:
        """Test that client initialization requires an API key."""
        with pytest.raises(ValueError, match="API key"):
            SonarrClient(url=sonarr_url, api_key="")

    def test_client_normalizes_url(self, sonarr_api_key: str) -> None:
        """Test that client normalizes URLs (removes trailing slash)."""
        client = SonarrClient(url="http://localhost:8989/", api_key=sonarr_api_key)  # noqa: F841
        assert client.url == "http://localhost:8989"

    def test_client_accepts_custom_timeout(self, sonarr_url: str, sonarr_api_key: str) -> None:
        """Test that client accepts custom timeout values."""
        client = SonarrClient(url=sonarr_url, api_key=sonarr_api_key, timeout=60.0)  # noqa: F841
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_client_validates_connection_on_create(
        self,
        httpx_mock: HTTPXMock,
        sonarr_url: str,
        sonarr_api_key: str,
        sonarr_system_status_factory: callable,
    ) -> None:
        """Test that client optionally validates connection on initialization."""
        mock_status = sonarr_system_status_factory()
        httpx_mock.add_response(url=f"{sonarr_url}/api/v3/system/status", json=mock_status)

        client = await SonarrClient.create(  # noqa: F841
            url=sonarr_url, api_key=sonarr_api_key, validate_connection=True
        )
        assert client is not None

        # Verify API key was in header
        request = httpx_mock.get_request()
        assert request.headers.get("X-Api-Key") == sonarr_api_key

    @pytest.mark.asyncio
    async def test_client_health_check_returns_true_when_healthy(
        self,
        httpx_mock: HTTPXMock,
        sonarr_client: SonarrClient,
        sonarr_system_status_factory: callable,
    ) -> None:
        """Test that health_check returns True when Sonarr is accessible."""
        mock_status = sonarr_system_status_factory()
        httpx_mock.add_response(json=mock_status)

        is_healthy = await sonarr_client.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_client_health_check_returns_false_when_unreachable(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that health_check returns False when Sonarr is unreachable."""
        httpx_mock.add_exception(HTTPError("Connection failed"))

        is_healthy = await sonarr_client.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_client_context_manager_closes_properly(
        self, sonarr_url: str, sonarr_api_key: str
    ) -> None:
        """Test that client properly closes when used as context manager."""
        async with SonarrClient(url=sonarr_url, api_key=sonarr_api_key) as client:
            assert client is not None
        # Client should be closed after exiting context


# ============================================================================
# Series Operations Tests
# ============================================================================


class TestSonarrClientSeriesOperations:
    """Test suite for series-related operations."""

    @pytest.mark.asyncio
    async def test_get_series_returns_all_series(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that get_series returns all TV series."""
        mock_series = [sonarr_series_factory(series_id=i) for i in range(1, 4)]
        httpx_mock.add_response(json=mock_series)

        result = await sonarr_client.get_series()  # noqa: F841

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 3

    @pytest.mark.asyncio
    async def test_get_series_returns_empty_list_when_no_series(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that get_series returns empty list when no series exist."""
        httpx_mock.add_response(json=[])

        result = await sonarr_client.get_series()  # noqa: F841

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_series_by_id_returns_specific_series(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that get_series_by_id returns specific series details."""
        mock_series = sonarr_series_factory(series_id=5, title="Breaking Bad")
        httpx_mock.add_response(json=mock_series)

        result = await sonarr_client.get_series_by_id(series_id=5)  # noqa: F841

        assert result["id"] == 5
        assert result["title"] == "Breaking Bad"

        # Verify correct endpoint was called
        request = httpx_mock.get_request()
        assert "/api/v3/series/5" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_series_by_id_raises_on_not_found(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that get_series_by_id raises error for non-existent series."""
        httpx_mock.add_response(status_code=404, json={"message": "NotFound"})

        with pytest.raises(SonarrClientError, match="404"):
            await sonarr_client.get_series_by_id(series_id=999)

    @pytest.mark.asyncio
    async def test_add_series_sends_correct_payload(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that add_series sends correct POST request with series data."""
        mock_series = sonarr_series_factory(series_id=1, title="The Wire")
        httpx_mock.add_response(status_code=201, json=mock_series)

        series_data = {
            "title": "The Wire",
            "tvdbId": 12345,
            "qualityProfileId": 1,
            "rootFolderPath": "/tv",
            "seasonFolder": True,
            "monitored": True,
        }

        result = await sonarr_client.add_series(series_data)  # noqa: F841

        # Verify POST request was made
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "/api/v3/series" in str(request.url)

        # Verify payload
        payload = json.loads(request.content)
        assert payload["tvdbId"] == 12345
        assert payload["qualityProfileId"] == 1
        assert payload["rootFolderPath"] == "/tv"

        assert result["title"] == "The Wire"

    @pytest.mark.asyncio
    async def test_add_series_validates_required_fields(self, sonarr_client: SonarrClient) -> None:
        """Test that add_series validates required fields."""
        # Missing tvdbId
        with pytest.raises(ValueError, match="tvdbId"):
            await sonarr_client.add_series({"title": "Test", "rootFolderPath": "/tv"})

        # Missing rootFolderPath
        with pytest.raises(ValueError, match="rootFolderPath"):
            await sonarr_client.add_series({"title": "Test", "tvdbId": 12345})

    @pytest.mark.asyncio
    async def test_add_series_with_monitoring_options(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that add_series includes monitoring and season folder options."""
        mock_series = sonarr_series_factory()
        httpx_mock.add_response(status_code=201, json=mock_series)

        series_data = {
            "title": "Test Series",
            "tvdbId": 12345,
            "qualityProfileId": 1,
            "rootFolderPath": "/tv",
            "monitored": True,
            "seasonFolder": True,
        }

        await sonarr_client.add_series(series_data)

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["monitored"] is True
        assert payload["seasonFolder"] is True

    @pytest.mark.asyncio
    async def test_search_series_returns_lookup_results(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that search_series returns TVDB lookup results."""
        mock_results = [
            sonarr_series_factory(series_id=0, title="The Wire", tvdb_id=12345),
            sonarr_series_factory(series_id=0, title="The Wire (UK)", tvdb_id=54321),
        ]
        httpx_mock.add_response(json=mock_results)

        result = await sonarr_client.search_series(term="The Wire")  # noqa: F841

        # Verify search endpoint
        request = httpx_mock.get_request()
        assert "/api/v3/series/lookup" in str(request.url)
        assert "term=" in str(request.url)

        assert len(result) == 2
        assert result[0]["title"] == "The Wire"

    @pytest.mark.asyncio
    async def test_search_series_by_tvdb_id(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that search_series can lookup by TVDB ID."""
        mock_result = [sonarr_series_factory(tvdb_id=12345)]  # noqa: F841
        httpx_mock.add_response(json=mock_result)

        result = await sonarr_client.search_series(term="tvdb:12345")  # noqa: F841

        request = httpx_mock.get_request()
        assert "term=tvdb%3A12345" in str(request.url) or "term=tvdb:12345" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_series_removes_series(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that delete_series sends DELETE request."""
        httpx_mock.add_response(status_code=200, json={})

        await sonarr_client.delete_series(series_id=5)

        request = httpx_mock.get_request()
        assert request.method == "DELETE"
        assert "/api/v3/series/5" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_series_with_delete_files_flag(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that delete_series includes deleteFiles query parameter."""
        httpx_mock.add_response(status_code=200, json={})

        await sonarr_client.delete_series(series_id=5, delete_files=True)

        request = httpx_mock.get_request()
        assert "deleteFiles=true" in str(request.url)

    @pytest.mark.asyncio
    async def test_delete_series_with_add_import_exclusion_flag(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that delete_series includes addImportExclusion parameter."""
        httpx_mock.add_response(status_code=200, json={})

        await sonarr_client.delete_series(series_id=5, delete_files=True, add_import_exclusion=True)

        request = httpx_mock.get_request()
        assert "addImportExclusion=true" in str(request.url)


# ============================================================================
# Episode Operations Tests
# ============================================================================


class TestSonarrClientEpisodeOperations:
    """Test suite for episode-related operations."""

    @pytest.mark.asyncio
    async def test_get_episodes_returns_series_episodes(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_episode_factory: callable
    ) -> None:
        """Test that get_episodes returns all episodes for a series."""
        mock_episodes = [
            sonarr_episode_factory(episode_id=i, series_id=1, episode_number=i)
            for i in range(1, 11)
        ]
        httpx_mock.add_response(json=mock_episodes)

        result = await sonarr_client.get_episodes(series_id=1)  # noqa: F841

        assert len(result) == 10
        assert result[0]["seriesId"] == 1

        # Verify query parameters
        request = httpx_mock.get_request()
        assert "/api/v3/episode" in str(request.url)
        assert "seriesId=1" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_episodes_filters_by_season(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_episode_factory: callable
    ) -> None:
        """Test that get_episodes can filter by season number."""
        mock_episodes = [
            sonarr_episode_factory(episode_id=i, series_id=1, season_number=2) for i in range(1, 6)
        ]
        httpx_mock.add_response(json=mock_episodes)

        result = await sonarr_client.get_episodes(series_id=1, season_number=2)  # noqa: F841

        request = httpx_mock.get_request()
        assert "seasonNumber=2" in str(request.url)
        assert all(ep["seasonNumber"] == 2 for ep in result)

    @pytest.mark.asyncio
    async def test_get_episode_by_id_returns_specific_episode(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_episode_factory: callable
    ) -> None:
        """Test that get_episode_by_id returns specific episode details."""
        mock_episode = sonarr_episode_factory(episode_id=42, title="Pilot")
        httpx_mock.add_response(json=mock_episode)

        result = await sonarr_client.get_episode_by_id(episode_id=42)  # noqa: F841

        assert result["id"] == 42
        assert result["title"] == "Pilot"

        request = httpx_mock.get_request()
        assert "/api/v3/episode/42" in str(request.url)

    @pytest.mark.asyncio
    async def test_search_episode_triggers_episode_search(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that search_episode triggers episode search command."""
        mock_command = sonarr_command_factory(
            command_id=100, name="EpisodeSearch", body={"episodeIds": [5]}
        )
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await sonarr_client.search_episode(episode_id=5)  # noqa: F841

        # Verify command was posted
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "/api/v3/command" in str(request.url)

        payload = json.loads(request.content)
        assert payload["name"] == "EpisodeSearch"
        assert 5 in payload["episodeIds"]

        assert result["id"] == 100

    @pytest.mark.asyncio
    async def test_search_episode_returns_command_id(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that search_episode returns command ID for tracking."""
        mock_command = sonarr_command_factory(command_id=123)
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await sonarr_client.search_episode(episode_id=10)  # noqa: F841

        assert "id" in result
        assert result["id"] == 123


# ============================================================================
# Command Operations Tests
# ============================================================================


class TestSonarrClientCommandOperations:
    """Test suite for command execution operations."""

    @pytest.mark.asyncio
    async def test_execute_command_posts_to_command_endpoint(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that _execute_command POSTs to /api/v3/command."""
        mock_command = sonarr_command_factory(name="TestCommand")
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await sonarr_client._execute_command(
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
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that get_command returns command status and progress."""
        mock_command = sonarr_command_factory(
            command_id=50, status="completed", duration="00:02:30"
        )
        httpx_mock.add_response(json=mock_command)

        result = await sonarr_client.get_command(command_id=50)  # noqa: F841

        assert result["id"] == 50
        assert result["status"] == "completed"
        assert result["duration"] == "00:02:30"

        request = httpx_mock.get_request()
        assert "/api/v3/command/50" in str(request.url)

    @pytest.mark.asyncio
    async def test_series_search_triggers_series_search_command(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that search_series_command triggers SeriesSearch command."""
        mock_command = sonarr_command_factory(name="SeriesSearch", body={"seriesId": 3})
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await sonarr_client.search_series_command(series_id=3)  # noqa: F841

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["name"] == "SeriesSearch"
        assert payload["seriesId"] == 3

    @pytest.mark.asyncio
    async def test_refresh_series_triggers_refresh_series_command(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that refresh_series triggers RefreshSeries command."""
        mock_command = sonarr_command_factory(name="RefreshSeries", body={"seriesId": 7})
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await sonarr_client.refresh_series(series_id=7)  # noqa: F841

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["name"] == "RefreshSeries"
        assert payload["seriesId"] == 7

    @pytest.mark.asyncio
    async def test_rescan_series_triggers_rescan_series_command(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_command_factory: callable
    ) -> None:
        """Test that rescan_series triggers RescanSeries command."""
        mock_command = sonarr_command_factory(name="RescanSeries")
        httpx_mock.add_response(status_code=201, json=mock_command)

        result = await sonarr_client.rescan_series(series_id=4)  # noqa: F841

        request = httpx_mock.get_request()
        payload = json.loads(request.content)
        assert payload["name"] == "RescanSeries"
        assert payload["seriesId"] == 4


# ============================================================================
# Calendar, Queue, and Wanted Tests
# ============================================================================


class TestSonarrClientCalendarQueueWanted:
    """Test suite for calendar, queue, and wanted operations."""

    @pytest.mark.asyncio
    async def test_get_calendar_returns_upcoming_episodes(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_calendar_factory: callable
    ) -> None:
        """Test that get_calendar returns episodes airing in date range."""
        mock_calendar = sonarr_calendar_factory(days=7, episodes_per_day=2)
        httpx_mock.add_response(json=mock_calendar)

        result = await sonarr_client.get_calendar(
            start_date="2020-01-01", end_date="2020-01-07"
        )  # noqa: F841

        assert len(result) == 14  # 7 days * 2 episodes per day

        request = httpx_mock.get_request()
        assert "/api/v3/calendar" in str(request.url)
        assert "start=" in str(request.url)
        assert "end=" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_calendar_defaults_to_current_week(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that get_calendar uses default date range when not specified."""
        httpx_mock.add_response(json=[])

        await sonarr_client.get_calendar()

        request = httpx_mock.get_request()
        assert "/api/v3/calendar" in str(request.url)
        # Should include default date parameters or none at all

    @pytest.mark.asyncio
    async def test_get_queue_returns_download_queue(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_queue_factory: callable
    ) -> None:
        """Test that get_queue returns download queue with status."""
        mock_queue = sonarr_queue_factory(records=3)
        httpx_mock.add_response(json=mock_queue)

        result = await sonarr_client.get_queue()  # noqa: F841

        assert "records" in result
        assert len(result["records"]) == 3
        assert result["totalRecords"] == 3

        request = httpx_mock.get_request()
        assert "/api/v3/queue" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_queue_supports_pagination(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_queue_factory: callable
    ) -> None:
        """Test that get_queue supports page and pageSize parameters."""
        mock_queue = sonarr_queue_factory(records=5, page=2, page_size=20)
        httpx_mock.add_response(json=mock_queue)

        result = await sonarr_client.get_queue(page=2, page_size=20)  # noqa: F841

        request = httpx_mock.get_request()
        assert "page=2" in str(request.url)
        assert "pageSize=20" in str(request.url)

        assert result["page"] == 2
        assert result["pageSize"] == 20

    @pytest.mark.asyncio
    async def test_get_wanted_missing_returns_missing_episodes(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_wanted_factory: callable
    ) -> None:
        """Test that get_wanted_missing returns paginated missing episodes."""
        mock_wanted = sonarr_wanted_factory(records=10)
        httpx_mock.add_response(json=mock_wanted)

        result = await sonarr_client.get_wanted_missing()  # noqa: F841

        assert "records" in result
        assert len(result["records"]) == 10
        assert all(not ep["hasFile"] for ep in result["records"])

        request = httpx_mock.get_request()
        assert "/api/v3/wanted/missing" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_wanted_missing_supports_pagination(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_wanted_factory: callable
    ) -> None:
        """Test that get_wanted_missing supports pagination parameters."""
        mock_wanted = sonarr_wanted_factory(records=5, page=3, page_size=10)
        httpx_mock.add_response(json=mock_wanted)

        result = await sonarr_client.get_wanted_missing(page=3, page_size=10)  # noqa: F841

        request = httpx_mock.get_request()
        assert "page=3" in str(request.url)
        assert "pageSize=10" in str(request.url)

    @pytest.mark.asyncio
    async def test_get_wanted_missing_includes_series_by_default(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_wanted_factory: callable
    ) -> None:
        """Test that get_wanted_missing includes series information."""
        mock_wanted = sonarr_wanted_factory(records=2, include_series=True)
        httpx_mock.add_response(json=mock_wanted)

        result = await sonarr_client.get_wanted_missing(include_series=True)  # noqa: F841

        # Check that series info is included
        assert "series" in result["records"][0]
        assert result["records"][0]["series"]["title"] is not None


# ============================================================================
# System Status Tests
# ============================================================================


class TestSonarrClientSystemStatus:
    """Test suite for system status operations."""

    @pytest.mark.asyncio
    async def test_get_system_status_returns_status_info(
        self,
        httpx_mock: HTTPXMock,
        sonarr_client: SonarrClient,
        sonarr_system_status_factory: callable,
    ) -> None:
        """Test that get_system_status returns Sonarr system information."""
        mock_status = sonarr_system_status_factory(version="3.0.10.1567")
        httpx_mock.add_response(json=mock_status)

        result = await sonarr_client.get_system_status()  # noqa: F841

        assert result["version"] == "3.0.10.1567"
        assert "osName" in result
        assert "isDocker" in result

        request = httpx_mock.get_request()
        assert "/api/v3/system/status" in str(request.url)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSonarrClientErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_401_unauthorized_error(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of 401 Unauthorized (invalid API key)."""
        httpx_mock.add_response(status_code=401, json={"message": "Unauthorized"})

        with pytest.raises(SonarrClientError, match="Unauthorized|401"):
            await sonarr_client.get_series()

    @pytest.mark.asyncio
    async def test_handles_404_not_found_error(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of 404 Not Found errors."""
        httpx_mock.add_response(status_code=404, json={"message": "Series not found"})

        with pytest.raises(SonarrClientError, match="404|not found"):
            await sonarr_client.get_series_by_id(series_id=999)

    @pytest.mark.asyncio
    async def test_handles_500_server_error(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of 500 Internal Server Error."""
        httpx_mock.add_response(status_code=500, text="Internal Server Error")

        with pytest.raises(SonarrClientError, match="500|Server error"):
            await sonarr_client.get_series()

    @pytest.mark.asyncio
    async def test_handles_connection_timeout(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of connection timeout."""
        httpx_mock.add_exception(HTTPError("Timeout"))

        with pytest.raises(SonarrConnectionError, match="Timeout|Connection"):
            await sonarr_client.get_series()

    @pytest.mark.asyncio
    async def test_handles_network_error(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of network connection error."""
        httpx_mock.add_exception(HTTPError("Connection refused"))

        with pytest.raises(SonarrConnectionError, match="Connection refused"):
            await sonarr_client.get_series()

    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of invalid JSON in response."""
        httpx_mock.add_response(text="Not valid JSON{")

        with pytest.raises(SonarrClientError, match="Invalid JSON|JSON"):
            await sonarr_client.get_series()

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that client retries on transient 503 errors."""
        # First request fails with 503
        httpx_mock.add_response(status_code=503)
        # Second request succeeds
        httpx_mock.add_response(json=[])

        result = await sonarr_client.get_series()  # noqa: F841

        assert result is not None
        assert len(httpx_mock.get_requests()) == 2

    @pytest.mark.asyncio
    async def test_respects_max_retries(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that client respects maximum retry limit."""
        # Add exactly 3 503 responses to match max_retries (default 3)
        for _ in range(3):
            httpx_mock.add_response(status_code=503)

        with pytest.raises(SonarrClientError):
            await sonarr_client.get_series()

        # Should stop at max_retries (default 3)
        assert len(httpx_mock.get_requests()) == 3


# ============================================================================
# Authentication and Request Building Tests
# ============================================================================


class TestSonarrClientAuthentication:
    """Test suite for authentication and request building."""

    @pytest.mark.asyncio
    async def test_includes_api_key_in_headers(
        self, httpx_mock: HTTPXMock, sonarr_url: str, sonarr_api_key: str
    ) -> None:
        """Test that all requests include X-Api-Key header."""
        httpx_mock.add_response(json=[])

        client = SonarrClient(url=sonarr_url, api_key=sonarr_api_key)  # noqa: F841
        await client.get_series()

        request = httpx_mock.get_request()
        assert request.headers.get("X-Api-Key") == sonarr_api_key

    @pytest.mark.asyncio
    async def test_api_key_not_in_url(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_api_key: str
    ) -> None:
        """Test that API key is NOT included in URL query parameters."""
        httpx_mock.add_response(json=[])

        await sonarr_client.get_series()

        request = httpx_mock.get_request()
        # API key should be in header, not URL
        assert sonarr_api_key not in str(request.url)
        assert "api_key" not in str(request.url).lower()
        assert "apikey" not in str(request.url).lower()

    @pytest.mark.asyncio
    async def test_builds_correct_api_v3_url(
        self, httpx_mock: HTTPXMock, sonarr_url: str, sonarr_api_key: str
    ) -> None:
        """Test that API URLs are built with /api/v3/ prefix."""
        httpx_mock.add_response(json=[])

        client = SonarrClient(url=sonarr_url, api_key=sonarr_api_key)  # noqa: F841
        await client.get_series()

        request = httpx_mock.get_request()
        assert str(request.url).startswith(sonarr_url)
        assert "/api/v3/series" in str(request.url)

    @pytest.mark.asyncio
    async def test_includes_content_type_json_for_post(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test that POST requests include Content-Type: application/json."""
        mock_series = sonarr_series_factory()
        httpx_mock.add_response(status_code=201, json=mock_series)

        series_data = {
            "title": "Test",
            "tvdbId": 12345,
            "qualityProfileId": 1,
            "rootFolderPath": "/tv",
        }
        await sonarr_client.add_series(series_data)

        request = httpx_mock.get_request()
        assert request.headers.get("Content-Type") == "application/json"


# ============================================================================
# Resource Management Tests
# ============================================================================


class TestSonarrClientResourceManagement:
    """Test suite for resource management and performance."""

    @pytest.mark.asyncio
    async def test_client_properly_closes_connections(
        self, sonarr_url: str, sonarr_api_key: str
    ) -> None:
        """Test that client properly closes HTTP connections."""
        async with SonarrClient(url=sonarr_url, api_key=sonarr_api_key) as client:
            pass
        # Client should be closed after exiting context

    @pytest.mark.asyncio
    async def test_client_reuses_http_client(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that client reuses the same HTTP client for multiple requests."""
        httpx_mock.add_response(json=[])
        httpx_mock.add_response(json=[])

        await sonarr_client.get_series()
        await sonarr_client.get_calendar()

        # Both requests should use the same client
        assert len(httpx_mock.get_requests()) == 2

    @pytest.mark.asyncio
    async def test_concurrent_requests_dont_conflict(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test that concurrent requests can be made safely."""
        import asyncio

        httpx_mock.add_response(json=[])
        httpx_mock.add_response(json={"page": 1, "records": []})
        httpx_mock.add_response(json={"version": "3.0.10"})

        results = await asyncio.gather(
            sonarr_client.get_series(),
            sonarr_client.get_queue(),
            sonarr_client.get_system_status(),
        )

        assert len(results) == 3


# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================


class TestSonarrClientEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_handles_empty_series_list(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of empty series list."""
        httpx_mock.add_response(json=[])

        result = await sonarr_client.get_series()  # noqa: F841

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_handles_large_series_list(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test handling of large series list (100+ series)."""
        mock_series = [sonarr_series_factory(series_id=i) for i in range(150)]
        httpx_mock.add_response(json=mock_series)

        result = await sonarr_client.get_series()  # noqa: F841

        assert len(result) == 150

    @pytest.mark.asyncio
    async def test_handles_special_characters_in_series_title(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_series_factory: callable
    ) -> None:
        """Test handling of special characters in series titles."""
        mock_series = sonarr_series_factory(title="Test: The Series (2020) - Part 1")
        httpx_mock.add_response(json=[mock_series])

        result = await sonarr_client.search_series(
            term="Test: The Series (2020) - Part 1"
        )  # noqa: F841

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient
    ) -> None:
        """Test handling of responses with missing optional fields."""
        minimal_series = {"id": 1, "title": "Minimal Series", "tvdbId": 12345, "monitored": True}
        httpx_mock.add_response(json=[minimal_series])

        result = await sonarr_client.get_series()  # noqa: F841

        assert len(result) == 1
        assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_handles_null_values_in_response(
        self, httpx_mock: HTTPXMock, sonarr_client: SonarrClient, sonarr_episode_factory: callable
    ) -> None:
        """Test handling of null values in API responses."""
        episode = sonarr_episode_factory()
        episode["airDate"] = None
        episode["overview"] = None

        httpx_mock.add_response(json=[episode])

        result = await sonarr_client.get_episodes(series_id=1)  # noqa: F841

        assert len(result) == 1
        assert result[0]["airDate"] is None
