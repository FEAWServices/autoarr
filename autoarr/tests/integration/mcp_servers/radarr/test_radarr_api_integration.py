"""
Integration tests for Radarr API Client.

This module contains integration tests that validate the Radarr client's
interaction with the actual Radarr API (mocked at HTTP layer). These tests
ensure correct API endpoint usage, request/response handling, and error scenarios.

Test Coverage Strategy:
- Full workflow tests (search → add → delete movies)
- API endpoint validation
- Request header verification (X-Api-Key)
- Response parsing and data integrity
- Error scenario handling with real API error formats

Target Coverage: 20% of total test suite (integration layer)
"""

import json

import pytest
from pytest_httpx import HTTPXMock

from autoarr.mcp_servers.mcp_servers.radarr.client import (RadarrClient,
                                                           RadarrClientError)

# ============================================================================
# Integration Test Fixtures
# ============================================================================


@pytest.fixture
def radarr_base_url() -> str:
    """Return integration test Radarr URL."""
    return "http://localhost:7878"


@pytest.fixture
def radarr_integration_api_key() -> str:
    """Return integration test API key."""
    return "integration_test_radarr_api_key_12345"


@pytest.fixture
async def radarr_integration_client(
    radarr_base_url: str, radarr_integration_api_key: str
) -> RadarrClient:
    """Create Radarr client for integration testing."""
    client = RadarrClient(
        url=radarr_base_url, api_key=radarr_integration_api_key, timeout=30.0
    )  # noqa: F841
    yield client
    await client.close()


# ============================================================================
# Full Workflow Integration Tests
# ============================================================================


class TestRadarrMovieWorkflow:
    """Integration tests for complete movie management workflows."""

    @pytest.mark.asyncio
    async def test_full_movie_lifecycle(
        self,
        httpx_mock: HTTPXMock,
        radarr_integration_client: RadarrClient,
        radarr_movie_factory: callable,
        radarr_command_factory: callable,
    ) -> None:
        """
        Test complete movie lifecycle: search → add → get → delete.

        This integration test validates the full workflow of:
        1. Searching for a movie
        2. Adding it to Radarr
        3. Retrieving it
        4. Deleting it
        """
        # Step 1: Search for movie
        search_results = [radarr_movie_factory(movie_id=0, title="The Matrix", tmdb_id=603)]
        httpx_mock.add_response(json=search_results)

        results = await radarr_integration_client.search_movie_lookup(term="The Matrix")

        assert len(results) == 1
        assert results[0]["title"] == "The Matrix"
        tmdb_id = results[0]["tmdbId"]

        # Verify search request
        search_request = httpx_mock.get_requests()[0]
        assert "/api/v3/movie/lookup" in str(search_request.url)
        assert search_request.headers.get("X-Api-Key") is not None

        # Step 2: Add movie
        added_movie = radarr_movie_factory(
            movie_id=1, title="The Matrix", tmdb_id=tmdb_id, path="/movies/The Matrix (1999)"
        )
        httpx_mock.add_response(status_code=201, json=added_movie)

        movie_data = {
            "title": "The Matrix",
            "tmdbId": tmdb_id,
            "qualityProfileId": 1,
            "rootFolderPath": "/movies",
            "monitored": True,
            "minimumAvailability": "released",
        }

        new_movie = await radarr_integration_client.add_movie(movie_data)

        assert new_movie["id"] == 1
        assert new_movie["title"] == "The Matrix"
        movie_id = new_movie["id"]

        # Verify add request
        add_request = httpx_mock.get_requests()[1]
        assert add_request.method == "POST"
        assert "/api/v3/movie" in str(add_request.url)

        # Step 3: Get movie details
        httpx_mock.add_response(json=added_movie)

        retrieved_movie = await radarr_integration_client.get_movie_by_id(movie_id)

        assert retrieved_movie["id"] == movie_id
        assert retrieved_movie["title"] == "The Matrix"

        # Step 4: Delete movie
        httpx_mock.add_response(status_code=200, json={})

        await radarr_integration_client.delete_movie(movie_id=movie_id, delete_files=True)

        # Verify delete request
        delete_request = httpx_mock.get_requests()[-1]
        assert delete_request.method == "DELETE"
        assert f"/api/v3/movie/{movie_id}" in str(delete_request.url)
        assert "deleteFiles=true" in str(delete_request.url)

    @pytest.mark.asyncio
    async def test_movie_search_and_monitoring_workflow(
        self,
        httpx_mock: HTTPXMock,
        radarr_integration_client: RadarrClient,
        radarr_movie_factory: callable,
        radarr_command_factory: callable,
    ) -> None:
        """
        Test movie search command workflow.

        This validates:
        1. Getting a movie
        2. Triggering a search for the movie
        3. Monitoring command status
        """
        # Step 1: Get movie
        mock_movie = radarr_movie_factory(movie_id=5, title="Inception", has_file=False)
        httpx_mock.add_response(json=mock_movie)

        movie = await radarr_integration_client.get_movie_by_id(movie_id=5)

        assert movie["id"] == 5
        assert movie["hasFile"] is False

        # Step 2: Trigger movie search
        search_command = radarr_command_factory(
            command_id=100, name="MoviesSearch", status="queued", body={"movieIds": [5]}
        )
        httpx_mock.add_response(status_code=201, json=search_command)

        command_result = await radarr_integration_client.search_movie(movie_id=5)  # noqa: F841

        assert command_result["id"] == 100
        assert command_result["name"] == "MoviesSearch"
        command_id = command_result["id"]

        # Verify command request
        command_request = httpx_mock.get_requests()[-1]
        assert command_request.method == "POST"
        assert "/api/v3/command" in str(command_request.url)
        payload = json.loads(command_request.content)
        assert payload["name"] == "MoviesSearch"
        assert 5 in payload["movieIds"]

        # Step 3: Check command status
        completed_command = radarr_command_factory(
            command_id=100, name="MoviesSearch", status="completed", duration="00:01:30"
        )
        httpx_mock.add_response(json=completed_command)

        status = await radarr_integration_client.get_command(command_id=command_id)

        assert status["id"] == command_id
        assert status["status"] == "completed"


class TestRadarrCalendarAndQueue:
    """Integration tests for calendar and queue operations."""

    @pytest.mark.asyncio
    async def test_calendar_upcoming_releases(
        self,
        httpx_mock: HTTPXMock,
        radarr_integration_client: RadarrClient,
        radarr_calendar_factory: callable,
    ) -> None:
        """Test retrieving upcoming movie releases from calendar."""
        # Mock calendar with 7 days of releases
        start_date = "2025-01-01"
        end_date = "2025-01-07"
        mock_calendar = radarr_calendar_factory(days=7, movies_per_day=2)
        httpx_mock.add_response(json=mock_calendar)

        calendar = await radarr_integration_client.get_calendar(
            start_date=start_date, end_date=end_date
        )

        assert len(calendar) == 14  # 7 days * 2 movies per day

        # Verify calendar request
        calendar_request = httpx_mock.get_requests()[0]
        assert "/api/v3/calendar" in str(calendar_request.url)
        assert f"start={start_date}" in str(calendar_request.url)
        assert f"end={end_date}" in str(calendar_request.url)

    @pytest.mark.asyncio
    async def test_download_queue_management(
        self,
        httpx_mock: HTTPXMock,
        radarr_integration_client: RadarrClient,
        radarr_queue_factory: callable,
    ) -> None:
        """Test retrieving and paginating download queue."""
        # Mock queue with 5 downloading movies
        mock_queue = radarr_queue_factory(records=5, page=1, page_size=20)
        httpx_mock.add_response(json=mock_queue)

        queue = await radarr_integration_client.get_queue(page=1, page_size=20)

        assert "records" in queue
        assert len(queue["records"]) == 5
        assert queue["totalRecords"] == 5
        assert queue["page"] == 1

        # Verify queue request
        queue_request = httpx_mock.get_requests()[0]
        assert "/api/v3/queue" in str(queue_request.url)
        assert "page=1" in str(queue_request.url)
        assert "pageSize=20" in str(queue_request.url)


class TestRadarrErrorScenarios:
    """Integration tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_unauthorized_api_key_error(
        self, httpx_mock: HTTPXMock, radarr_base_url: str
    ) -> None:
        """Test handling of 401 Unauthorized error (invalid API key)."""
        httpx_mock.add_response(
            status_code=401, json={"error": "Unauthorized", "message": "Invalid API Key"}
        )

        client = RadarrClient(url=radarr_base_url, api_key="invalid_key")  # noqa: F841

        with pytest.raises(RadarrClientError, match="401|Unauthorized"):
            await client.get_movies()

    @pytest.mark.asyncio
    async def test_movie_not_found_error(
        self, httpx_mock: HTTPXMock, radarr_integration_client: RadarrClient
    ) -> None:
        """Test handling of 404 Not Found error."""
        httpx_mock.add_response(
            status_code=404, json={"error": "NotFound", "message": "Movie not found"}
        )

        with pytest.raises(RadarrClientError, match="404"):
            await radarr_integration_client.get_movie_by_id(movie_id=99999)

    @pytest.mark.asyncio
    async def test_server_error_with_retry(
        self, httpx_mock: HTTPXMock, radarr_integration_client: RadarrClient
    ) -> None:
        """Test that 503 server errors trigger retries."""
        # First request fails with 503
        httpx_mock.add_response(status_code=503, text="Service Unavailable")
        # Second request succeeds
        httpx_mock.add_response(json=[])

        result = await radarr_integration_client.get_movies()  # noqa: F841

        # Should succeed after retry
        assert result is not None
        assert len(httpx_mock.get_requests()) == 2


class TestRadarrDataIntegrity:
    """Integration tests for data parsing and integrity."""

    @pytest.mark.asyncio
    async def test_movie_response_parsing(
        self,
        httpx_mock: HTTPXMock,
        radarr_integration_client: RadarrClient,
        radarr_movie_factory: callable,
    ) -> None:
        """Test that movie response data is parsed correctly."""
        mock_movie = radarr_movie_factory(
            movie_id=1,
            title="Test Movie",
            year=2020,
            tmdb_id=12345,
            has_file=True,
            monitored=True,
        )
        httpx_mock.add_response(json=mock_movie)

        movie = await radarr_integration_client.get_movie_by_id(movie_id=1)

        # Verify all key fields are present
        assert movie["id"] == 1
        assert movie["title"] == "Test Movie"
        assert movie["year"] == 2020
        assert movie["tmdbId"] == 12345
        assert movie["hasFile"] is True
        assert movie["monitored"] is True

    @pytest.mark.asyncio
    async def test_wanted_missing_movies_response(
        self,
        httpx_mock: HTTPXMock,
        radarr_integration_client: RadarrClient,
        radarr_wanted_factory: callable,
    ) -> None:
        """Test that wanted/missing movies response is parsed correctly."""
        mock_wanted = radarr_wanted_factory(records=10, page=1, page_size=20)
        httpx_mock.add_response(json=mock_wanted)

        wanted = await radarr_integration_client.get_wanted_missing(page=1, page_size=20)

        assert "records" in wanted
        assert len(wanted["records"]) == 10
        assert all(not movie["hasFile"] for movie in wanted["records"])
        assert wanted["page"] == 1
        assert wanted["totalRecords"] == 10
