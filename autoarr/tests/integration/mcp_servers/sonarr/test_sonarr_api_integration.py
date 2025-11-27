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
Integration tests for Sonarr API Client.

This module contains integration tests that validate the Sonarr client's
interaction with the actual Sonarr API (mocked at HTTP layer). These tests
ensure correct API endpoint usage, request/response handling, and error scenarios.

Test Coverage Strategy:
- Full workflow tests (search → add → delete series)
- API endpoint validation
- Request header verification (X-Api-Key)
- Response parsing and data integrity
- Error scenario handling with real API error formats

Target Coverage: 20% of total test suite (integration layer)
"""

import pytest
from pytest_httpx import HTTPXMock

from autoarr.mcp_servers.mcp_servers.sonarr.client import SonarrClient, SonarrClientError

# ============================================================================
# Integration Test Fixtures
# ============================================================================


@pytest.fixture
def sonarr_base_url() -> str:
    """Return integration test Sonarr URL."""
    return "http://localhost:8989"


@pytest.fixture
def sonarr_integration_api_key() -> str:
    """Return integration test API key."""
    return "integration_test_api_key_12345"


@pytest.fixture
async def sonarr_integration_client(
    sonarr_base_url: str, sonarr_integration_api_key: str
) -> SonarrClient:
    """Create Sonarr client for integration testing."""
    client = SonarrClient(
        url=sonarr_base_url, api_key=sonarr_integration_api_key, timeout=30.0
    )  # noqa: F841
    yield client
    await client.close()


# ============================================================================
# Full Workflow Integration Tests
# ============================================================================


class TestSonarrSeriesWorkflow:
    """Integration tests for complete series management workflows."""

    @pytest.mark.asyncio
    async def test_full_series_lifecycle(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_series_factory: callable,
        sonarr_command_factory: callable,
    ) -> None:
        """
        Test complete series lifecycle: search → add → get → delete.

        This integration test validates the full workflow of:
        1. Searching for a series
        2. Adding it to Sonarr
        3. Retrieving it
        4. Deleting it
        """
        # Step 1: Search for series
        search_results = [sonarr_series_factory(series_id=0, title="Breaking Bad", tvdb_id=81189)]
        httpx_mock.add_response(json=search_results)

        results = await sonarr_integration_client.search_series(term="Breaking Bad")

        assert len(results) == 1
        assert results[0]["title"] == "Breaking Bad"
        tvdb_id = results[0]["tvdbId"]

        # Verify search request
        search_request = httpx_mock.get_requests()[0]
        assert "/api/v3/series/lookup" in str(search_request.url)
        assert search_request.headers.get("X-Api-Key") is not None

        # Step 2: Add series
        added_series = sonarr_series_factory(
            series_id=1, title="Breaking Bad", tvdb_id=tvdb_id, path="/tv/Breaking Bad"
        )
        httpx_mock.add_response(status_code=201, json=added_series)

        series_data = {
            "title": "Breaking Bad",
            "tvdbId": tvdb_id,
            "qualityProfileId": 1,
            "rootFolderPath": "/tv",
            "monitored": True,
            "seasonFolder": True,
        }

        new_series = await sonarr_integration_client.add_series(series_data)

        assert new_series["id"] == 1
        assert new_series["title"] == "Breaking Bad"
        series_id = new_series["id"]

        # Verify add request
        add_request = httpx_mock.get_requests()[1]
        assert add_request.method == "POST"
        assert "/api/v3/series" in str(add_request.url)

        # Step 3: Get series details
        httpx_mock.add_response(json=added_series)

        retrieved_series = await sonarr_integration_client.get_series_by_id(series_id)

        assert retrieved_series["id"] == series_id
        assert retrieved_series["title"] == "Breaking Bad"

        # Step 4: Delete series
        httpx_mock.add_response(status_code=200, json={})

        await sonarr_integration_client.delete_series(series_id=series_id, delete_files=True)

        # Verify delete request
        delete_request = httpx_mock.get_requests()[-1]
        assert delete_request.method == "DELETE"
        assert f"/api/v3/series/{series_id}" in str(delete_request.url)
        assert "deleteFiles=true" in str(delete_request.url)

    @pytest.mark.asyncio
    async def test_episode_search_and_monitoring_workflow(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_episode_factory: callable,
        sonarr_command_factory: callable,
        sonarr_queue_factory: callable,
    ) -> None:
        """
        Test episode search and monitoring workflow.

        Validates: Get episodes → Search for missing → Monitor queue
        """
        series_id = 1

        # Step 1: Get episodes for series
        episodes = [
            sonarr_episode_factory(
                episode_id=i,
                series_id=series_id,
                season_number=1,
                episode_number=i,
                has_file=(i <= 3),  # First 3 episodes have files
            )
            for i in range(1, 6)
        ]
        httpx_mock.add_response(json=episodes)

        retrieved_episodes = await sonarr_integration_client.get_episodes(series_id=series_id)

        assert len(retrieved_episodes) == 5
        missing_episodes = [ep for ep in retrieved_episodes if not ep["hasFile"]]
        assert len(missing_episodes) == 2

        # Step 2: Search for missing episode
        episode_to_search = missing_episodes[0]["id"]
        search_command = sonarr_command_factory(
            command_id=100, name="EpisodeSearch", status="queued"
        )
        httpx_mock.add_response(status_code=201, json=search_command)

        command = await sonarr_integration_client.search_episode(episode_to_search)

        assert command["id"] == 100
        assert command["status"] == "queued"
        command_id = command["id"]

        # Step 3: Check command status
        completed_command = sonarr_command_factory(
            command_id=command_id, status="completed", duration="00:01:30"
        )
        httpx_mock.add_response(json=completed_command)

        status = await sonarr_integration_client.get_command(command_id)

        assert status["status"] == "completed"

        # Step 4: Check download queue
        queue = sonarr_queue_factory(records=1)
        httpx_mock.add_response(json=queue)

        download_queue = await sonarr_integration_client.get_queue()

        assert "records" in download_queue
        assert len(download_queue["records"]) >= 0


# ============================================================================
# API Endpoint Integration Tests
# ============================================================================


class TestSonarrAPIEndpoints:
    """Integration tests validating correct API endpoint usage."""

    @pytest.mark.asyncio
    async def test_all_requests_use_api_v3_prefix(
        self, httpx_mock: HTTPXMock, sonarr_integration_client: SonarrClient
    ) -> None:
        """Verify all API requests use /api/v3/ prefix."""
        # Mock various endpoints
        httpx_mock.add_response(json=[])  # series
        httpx_mock.add_response(json=[])  # episodes
        httpx_mock.add_response(json={"page": 1, "records": []})  # queue
        httpx_mock.add_response(json={"version": "3.0.10"})  # status

        await sonarr_integration_client.get_series()
        await sonarr_integration_client.get_episodes(series_id=1)
        await sonarr_integration_client.get_queue()
        await sonarr_integration_client.get_system_status()

        requests = httpx_mock.get_requests()
        for request in requests:
            assert "/api/v3/" in str(request.url)

    @pytest.mark.asyncio
    async def test_all_requests_include_api_key_header(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_integration_api_key: str,
    ) -> None:
        """Verify all requests include X-Api-Key header."""
        httpx_mock.add_response(json=[])
        httpx_mock.add_response(json=[])

        await sonarr_integration_client.get_series()
        await sonarr_integration_client.get_calendar()

        requests = httpx_mock.get_requests()
        for request in requests:
            assert request.headers.get("X-Api-Key") == sonarr_integration_api_key
            # Ensure API key is NOT in URL
            assert sonarr_integration_api_key not in str(request.url)

    @pytest.mark.asyncio
    async def test_post_requests_include_content_type(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_series_factory: callable,
        sonarr_command_factory: callable,
    ) -> None:
        """Verify POST requests include Content-Type: application/json."""
        mock_series = sonarr_series_factory()
        mock_command = sonarr_command_factory()

        httpx_mock.add_response(status_code=201, json=mock_series)
        httpx_mock.add_response(status_code=201, json=mock_command)

        # POST to add series
        await sonarr_integration_client.add_series(
            {"title": "Test", "tvdbId": 12345, "qualityProfileId": 1, "rootFolderPath": "/tv"}
        )

        # POST to execute command
        await sonarr_integration_client.search_episode(episode_id=1)

        requests = httpx_mock.get_requests()
        for request in requests:
            if request.method == "POST":
                assert request.headers.get("Content-Type") == "application/json"


# ============================================================================
# Error Scenario Integration Tests
# ============================================================================


class TestSonarrErrorScenarios:
    """Integration tests for error handling with real API error formats."""

    @pytest.mark.asyncio
    async def test_handles_sonarr_404_error_format(
        self, httpx_mock: HTTPXMock, sonarr_integration_client: SonarrClient
    ) -> None:
        """Test handling of Sonarr's 404 error response format."""
        sonarr_404_response = {
            "message": "Series with id 999 not found",
            "description": "The requested resource could not be found.",
            "statusCode": 404,
        }
        httpx_mock.add_response(status_code=404, json=sonarr_404_response)

        with pytest.raises(SonarrClientError, match="404"):
            await sonarr_integration_client.get_series_by_id(series_id=999)

    @pytest.mark.asyncio
    async def test_handles_sonarr_400_validation_error(
        self, httpx_mock: HTTPXMock, sonarr_integration_client: SonarrClient
    ) -> None:
        """Test handling of Sonarr's 400 validation error format."""
        sonarr_validation_error = {
            "message": "Validation failed",
            "errors": [
                {
                    "propertyName": "rootFolderPath",
                    "errorMessage": "Root folder path is required",
                    "attemptedValue": "",
                }
            ],
        }
        httpx_mock.add_response(status_code=400, json=sonarr_validation_error)

        with pytest.raises(SonarrClientError, match="400"):
            await sonarr_integration_client.add_series(
                {
                    "title": "Test",
                    "tvdbId": 12345,
                    "qualityProfileId": 1,
                    "rootFolderPath": "",  # Invalid
                }
            )

    @pytest.mark.asyncio
    async def test_handles_sonarr_401_unauthorized(
        self, httpx_mock: HTTPXMock, sonarr_base_url: str
    ) -> None:
        """Test handling of 401 Unauthorized with invalid API key."""
        # Create client with invalid API key
        client = SonarrClient(url=sonarr_base_url, api_key="invalid_key")  # noqa: F841

        sonarr_401_response = {"message": "Unauthorized", "statusCode": 401}
        httpx_mock.add_response(status_code=401, json=sonarr_401_response)

        with pytest.raises(SonarrClientError, match="Unauthorized|401"):
            await client.get_series()

        await client.close()

    @pytest.mark.asyncio
    async def test_retries_on_503_service_unavailable(
        self, httpx_mock: HTTPXMock, sonarr_integration_client: SonarrClient
    ) -> None:
        """Test retry logic on 503 Service Unavailable."""
        # First attempt: 503
        httpx_mock.add_response(status_code=503, text="Service Unavailable")
        # Second attempt: Success
        httpx_mock.add_response(json=[])

        result = await sonarr_integration_client.get_series()  # noqa: F841

        assert result == []  # noqa: F841
        assert len(httpx_mock.get_requests()) == 2


# ============================================================================
# Data Integrity Integration Tests
# ============================================================================


class TestSonarrDataIntegrity:
    """Integration tests validating data integrity and parsing."""

    @pytest.mark.asyncio
    async def test_preserves_complex_series_structure(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_series_factory: callable,
    ) -> None:
        """Test that complex series data structures are preserved."""
        complex_series = sonarr_series_factory(series_id=1, title="Complex Series", season_count=5)
        httpx_mock.add_response(json=[complex_series])

        result = await sonarr_integration_client.get_series()  # noqa: F841

        assert len(result) == 1
        series = result[0]

        # Verify nested structures
        assert "seasons" in series
        assert len(series["seasons"]) == 6  # 5 seasons + specials
        assert "images" in series
        assert "statistics" in series
        assert series["statistics"]["seasonCount"] == 5

    @pytest.mark.asyncio
    async def test_handles_pagination_correctly(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_wanted_factory: callable,
    ) -> None:
        """Test correct handling of paginated responses."""
        # Page 1
        page1 = sonarr_wanted_factory(records=10, page=1, page_size=10)
        httpx_mock.add_response(json=page1)

        # Page 2
        page2 = sonarr_wanted_factory(records=5, page=2, page_size=10)
        httpx_mock.add_response(json=page2)

        result1 = await sonarr_integration_client.get_wanted_missing(page=1, page_size=10)
        result2 = await sonarr_integration_client.get_wanted_missing(page=2, page_size=10)

        assert result1["page"] == 1
        assert len(result1["records"]) == 10
        assert result2["page"] == 2
        assert len(result2["records"]) == 5

    @pytest.mark.asyncio
    async def test_handles_unicode_and_special_characters(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_series_factory: callable,
    ) -> None:
        """Test handling of Unicode and special characters in data."""
        series_with_unicode = sonarr_series_factory(
            series_id=1, title="Café: L'Été (2020) – Part 1 & 2"
        )
        httpx_mock.add_response(json=[series_with_unicode])

        result = await sonarr_integration_client.search_series(term="Café: L'Été")  # noqa: F841

        assert len(result) == 1
        assert result[0]["title"] == "Café: L'Été (2020) – Part 1 & 2"


# ============================================================================
# Performance and Concurrency Integration Tests
# ============================================================================


class TestSonarrPerformance:
    """Integration tests for performance and concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_perform_correctly(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_series_factory: callable,
        sonarr_queue_factory: callable,
    ) -> None:
        """Test that concurrent requests complete successfully."""
        import asyncio

        # Mock responses for concurrent requests
        httpx_mock.add_response(json=[sonarr_series_factory()])
        httpx_mock.add_response(json=[])
        httpx_mock.add_response(json=sonarr_queue_factory())
        httpx_mock.add_response(json={"version": "3.0.10"})

        # Execute concurrent requests
        results = await asyncio.gather(
            sonarr_integration_client.get_series(),
            sonarr_integration_client.get_calendar(),
            sonarr_integration_client.get_queue(),
            sonarr_integration_client.get_system_status(),
        )

        assert len(results) == 4
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_handles_large_response_sets(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_series_factory: callable,
    ) -> None:
        """Test handling of large response sets (100+ items)."""
        large_series_list = [
            sonarr_series_factory(series_id=i, title=f"Series {i}") for i in range(1, 151)
        ]
        httpx_mock.add_response(json=large_series_list)

        result = await sonarr_integration_client.get_series()  # noqa: F841

        assert len(result) == 150
        assert result[0]["id"] == 1
        assert result[149]["id"] == 150


# ============================================================================
# Calendar and Queue Integration Tests
# ============================================================================


class TestSonarrCalendarAndQueue:
    """Integration tests for calendar and queue operations."""

    @pytest.mark.asyncio
    async def test_calendar_date_range_filtering(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_calendar_factory: callable,
    ) -> None:
        """Test calendar with specific date ranges."""
        start_date = "2020-01-01"
        end_date = "2020-01-07"

        calendar_data = sonarr_calendar_factory(days=7, episodes_per_day=2, start_date=start_date)
        httpx_mock.add_response(json=calendar_data)

        result = await sonarr_integration_client.get_calendar(  # noqa: F841
            start_date=start_date, end_date=end_date
        )

        assert len(result) == 14
        # Verify date filtering in request
        request = httpx_mock.get_requests()[0]
        assert "start=" in str(request.url)
        assert "end=" in str(request.url)

    @pytest.mark.asyncio
    async def test_queue_status_monitoring(
        self,
        httpx_mock: HTTPXMock,
        sonarr_integration_client: SonarrClient,
        sonarr_queue_factory: callable,
    ) -> None:
        """Test monitoring download queue status."""
        queue_with_downloads = sonarr_queue_factory(records=3)
        httpx_mock.add_response(json=queue_with_downloads)

        queue = await sonarr_integration_client.get_queue()

        assert "records" in queue
        assert queue["totalRecords"] == 3
        assert all("status" in record for record in queue["records"])
        assert all("timeleft" in record for record in queue["records"])
