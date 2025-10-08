"""
Tests for Content Integration Service.

This module tests the content integration service including:
- Movie addition to Radarr
- TV series addition to Sonarr
- Error handling
- Service availability checks
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.api.services.content_integration import (
    ContentAlreadyExistsError,
    ContentIntegrationError,
    ContentIntegrationService,
    ServiceUnavailableError,
)


@pytest.fixture
def mock_orchestrator():
    """Create a mock MCP orchestrator."""
    orchestrator = MagicMock()
    orchestrator.call_tool = AsyncMock()
    return orchestrator


@pytest.fixture
def integration_service(mock_orchestrator):
    """Create a content integration service with mocked orchestrator."""
    return ContentIntegrationService(mock_orchestrator)


@pytest.mark.asyncio
class TestAddMovieToRadarr:
    """Test adding movies to Radarr."""

    async def test_add_movie_success(self, integration_service, mock_orchestrator):
        """Test successfully adding a movie."""
        # Mock lookup response
        mock_orchestrator.call_tool.side_effect = [
            {"title": "Dune", "tmdbId": 438631},  # lookup
            {"movies": []},  # get_movies (check existing)
            {"id": 123, "title": "Dune"},  # add_movie
        ]

        result = await integration_service.add_movie_to_radarr(
            tmdb_id=438631,
            quality_profile_id=1,
            root_folder="/movies",
            title="Dune",
            year=2021,
        )

        assert result["id"] == 123
        assert result["title"] == "Dune"
        assert mock_orchestrator.call_tool.call_count == 3

    async def test_add_movie_already_exists(self, integration_service, mock_orchestrator):
        """Test adding a movie that already exists."""
        # Mock responses
        mock_orchestrator.call_tool.side_effect = [
            {"title": "Dune", "tmdbId": 438631},  # lookup
            {"movies": [{"tmdbId": 438631, "title": "Dune"}]},  # get_movies (exists)
        ]

        with pytest.raises(ContentAlreadyExistsError, match="already exists"):
            await integration_service.add_movie_to_radarr(
                tmdb_id=438631,
                quality_profile_id=1,
                root_folder="/movies",
            )

    async def test_add_movie_not_found_in_tmdb(self, integration_service, mock_orchestrator):
        """Test adding a movie not found in TMDB."""
        # Mock lookup returning None
        mock_orchestrator.call_tool.return_value = None

        with pytest.raises(ContentIntegrationError, match="not found in TMDB"):
            await integration_service.add_movie_to_radarr(
                tmdb_id=999999,
                quality_profile_id=1,
                root_folder="/movies",
            )

    async def test_add_movie_radarr_unavailable(self, integration_service, mock_orchestrator):
        """Test when Radarr service is unavailable."""
        # Mock connection error
        mock_orchestrator.call_tool.side_effect = Exception("Connection refused")

        with pytest.raises(ServiceUnavailableError, match="unavailable"):
            await integration_service.add_movie_to_radarr(
                tmdb_id=438631,
                quality_profile_id=1,
                root_folder="/movies",
            )

    async def test_add_movie_with_search(self, integration_service, mock_orchestrator):
        """Test adding movie with search enabled."""
        mock_orchestrator.call_tool.side_effect = [
            {"title": "Dune", "tmdbId": 438631},
            {"movies": []},
            {"id": 123, "title": "Dune"},
        ]

        await integration_service.add_movie_to_radarr(
            tmdb_id=438631,
            quality_profile_id=1,
            root_folder="/movies",
            search_now=True,
        )

        # Verify search_for_movie param was passed
        calls = mock_orchestrator.call_tool.call_args_list
        add_call = calls[2]
        assert add_call[1]["params"]["search_for_movie"] is True


@pytest.mark.asyncio
class TestAddSeriesToSonarr:
    """Test adding TV series to Sonarr."""

    async def test_add_series_success(self, integration_service, mock_orchestrator):
        """Test successfully adding a series."""
        # Mock responses
        mock_orchestrator.call_tool.side_effect = [
            {"series": [{"title": "Breaking Bad", "tvdbId": 81189}]},  # lookup
            {"series": []},  # get_series (check existing)
            {"id": 456, "title": "Breaking Bad"},  # add_series
        ]

        result = await integration_service.add_series_to_sonarr(
            tvdb_id=81189,
            quality_profile_id=1,
            root_folder="/tv",
            title="Breaking Bad",
        )

        assert result["id"] == 456
        assert result["title"] == "Breaking Bad"
        assert mock_orchestrator.call_tool.call_count == 3

    async def test_add_series_already_exists(self, integration_service, mock_orchestrator):
        """Test adding a series that already exists."""
        mock_orchestrator.call_tool.side_effect = [
            {"series": [{"title": "Breaking Bad", "tvdbId": 81189}]},  # lookup
            {"series": [{"tvdbId": 81189, "title": "Breaking Bad"}]},  # get_series (exists)
        ]

        with pytest.raises(ContentAlreadyExistsError, match="already exists"):
            await integration_service.add_series_to_sonarr(
                tvdb_id=81189,
                quality_profile_id=1,
                root_folder="/tv",
            )

    async def test_add_series_not_found_in_tvdb(self, integration_service, mock_orchestrator):
        """Test adding a series not found in TVDB."""
        # Mock lookup returning empty
        mock_orchestrator.call_tool.return_value = {"series": []}

        with pytest.raises(ContentIntegrationError, match="not found in TVDB"):
            await integration_service.add_series_to_sonarr(
                tvdb_id=999999,
                quality_profile_id=1,
                root_folder="/tv",
            )

    async def test_add_series_sonarr_unavailable(self, integration_service, mock_orchestrator):
        """Test when Sonarr service is unavailable."""
        mock_orchestrator.call_tool.side_effect = Exception("Service unavailable")

        with pytest.raises(ServiceUnavailableError, match="unavailable"):
            await integration_service.add_series_to_sonarr(
                tvdb_id=81189,
                quality_profile_id=1,
                root_folder="/tv",
            )

    async def test_add_series_with_season_folders(self, integration_service, mock_orchestrator):
        """Test adding series with season folders enabled."""
        mock_orchestrator.call_tool.side_effect = [
            {"series": [{"title": "Breaking Bad", "tvdbId": 81189}]},
            {"series": []},
            {"id": 456, "title": "Breaking Bad"},
        ]

        await integration_service.add_series_to_sonarr(
            tvdb_id=81189,
            quality_profile_id=1,
            root_folder="/tv",
            season_folder=True,
        )

        # Verify season_folder param was passed
        calls = mock_orchestrator.call_tool.call_args_list
        add_call = calls[2]
        assert add_call[1]["params"]["season_folder"] is True


@pytest.mark.asyncio
class TestQualityProfiles:
    """Test quality profile retrieval."""

    async def test_get_radarr_quality_profiles_success(
        self, integration_service, mock_orchestrator
    ):
        """Test successfully getting Radarr quality profiles."""
        mock_profiles = {"profiles": [{"id": 1, "name": "HD-1080p"}, {"id": 2, "name": "4K"}]}
        mock_orchestrator.call_tool.return_value = mock_profiles

        result = await integration_service.get_radarr_quality_profiles()

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "HD-1080p"

    async def test_get_radarr_quality_profiles_service_unavailable(
        self, integration_service, mock_orchestrator
    ):
        """Test when Radarr is unavailable."""
        mock_orchestrator.call_tool.side_effect = Exception("Connection error")

        with pytest.raises(ServiceUnavailableError):
            await integration_service.get_radarr_quality_profiles()

    async def test_get_sonarr_quality_profiles_success(
        self, integration_service, mock_orchestrator
    ):
        """Test successfully getting Sonarr quality profiles."""
        mock_profiles = {"profiles": [{"id": 1, "name": "HD-1080p"}, {"id": 2, "name": "4K"}]}
        mock_orchestrator.call_tool.return_value = mock_profiles

        result = await integration_service.get_sonarr_quality_profiles()

        assert len(result) == 2
        assert result[0]["id"] == 1

    async def test_get_sonarr_quality_profiles_service_unavailable(
        self, integration_service, mock_orchestrator
    ):
        """Test when Sonarr is unavailable."""
        mock_orchestrator.call_tool.side_effect = Exception("unavailable")

        with pytest.raises(ServiceUnavailableError):
            await integration_service.get_sonarr_quality_profiles()


@pytest.mark.asyncio
class TestRootFolders:
    """Test root folder retrieval."""

    async def test_get_radarr_root_folders_success(self, integration_service, mock_orchestrator):
        """Test successfully getting Radarr root folders."""
        mock_folders = {"folders": [{"path": "/movies", "freeSpace": 1000000}]}
        mock_orchestrator.call_tool.return_value = mock_folders

        result = await integration_service.get_radarr_root_folders()

        assert len(result) == 1
        assert result[0]["path"] == "/movies"

    async def test_get_radarr_root_folders_service_unavailable(
        self, integration_service, mock_orchestrator
    ):
        """Test when Radarr is unavailable."""
        mock_orchestrator.call_tool.side_effect = Exception("connection failed")

        with pytest.raises(ServiceUnavailableError):
            await integration_service.get_radarr_root_folders()

    async def test_get_sonarr_root_folders_success(self, integration_service, mock_orchestrator):
        """Test successfully getting Sonarr root folders."""
        mock_folders = {"folders": [{"path": "/tv", "freeSpace": 2000000}]}
        mock_orchestrator.call_tool.return_value = mock_folders

        result = await integration_service.get_sonarr_root_folders()

        assert len(result) == 1
        assert result[0]["path"] == "/tv"

    async def test_get_sonarr_root_folders_service_unavailable(
        self, integration_service, mock_orchestrator
    ):
        """Test when Sonarr is unavailable."""
        mock_orchestrator.call_tool.side_effect = Exception("Service is unavailable")

        with pytest.raises(ServiceUnavailableError):
            await integration_service.get_sonarr_root_folders()
