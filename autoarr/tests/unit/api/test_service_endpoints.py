"""
Tests for service-specific endpoints.

This module tests the service-specific API endpoints for Downloads (SABnzbd),
Shows (Sonarr), Movies (Radarr), and Media (Plex).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from autoarr.api.main import app
from autoarr.api.dependencies import reset_orchestrator


@pytest.fixture
def client(mock_database_init):
    """Create a test client with database mocking."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    mock = MagicMock()
    mock.call_tool = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    reset_orchestrator()
    # Clear any dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def override_orchestrator():
    """Helper to override orchestrator dependency."""
    from autoarr.api.dependencies import get_orchestrator

    def _override(mock_orchestrator):
        async def override_func():
            yield mock_orchestrator

        app.dependency_overrides[get_orchestrator] = override_func

    return _override


class TestDownloadsEndpoints:
    """Test Downloads (SABnzbd) endpoints."""

    @pytest.mark.asyncio
    async def test_get_download_queue(self, client, mock_orchestrator, override_orchestrator):
        """Test getting download queue."""
        mock_orchestrator.call_tool.return_value = {
            "queue": [],
            "speed": "0 MB/s",
            "paused": False,
        }

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/downloads/queue")

        assert response.status_code == 200
        data = response.json()
        assert "queue" in data

    @pytest.mark.asyncio
    async def test_retry_download(self, client, mock_orchestrator, override_orchestrator):
        """Test retrying a download."""
        mock_orchestrator.call_tool.return_value = {"success": True}

        override_orchestrator(mock_orchestrator)

        response = client.post("/api/v1/downloads/retry/SABnzbd_nzo_abc123")

        assert response.status_code == 200
        mock_orchestrator.call_tool.assert_called_once()


class TestShowsEndpoints:
    """Test Shows (Sonarr) endpoints."""

    @pytest.mark.asyncio
    async def test_list_shows(self, client, mock_orchestrator, override_orchestrator):
        """Test listing all shows."""
        mock_orchestrator.call_tool.return_value = [
            {"id": 1, "title": "Breaking Bad"},
            {"id": 2, "title": "The Wire"},
        ]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/shows/")

        assert response.status_code == 200
        data = response.json()
        assert "series" in data
        assert data["total"] == 2
        mock_orchestrator.call_tool.assert_called_once_with("sonarr", "get_series", {})

    @pytest.mark.asyncio
    async def test_search_shows(self, client, mock_orchestrator, override_orchestrator):
        """Test searching for shows."""
        mock_orchestrator.call_tool.return_value = [{"title": "Breaking Bad", "tvdbId": 81189}]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/shows/search/breaking%20bad")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        mock_orchestrator.call_tool.assert_called_once_with(
            "sonarr", "search_series", {"query": "breaking bad"}
        )

    @pytest.mark.asyncio
    async def test_add_show(self, client, mock_orchestrator, override_orchestrator):
        """Test adding a new show."""
        mock_orchestrator.call_tool.return_value = {"id": 123, "title": "Breaking Bad"}

        override_orchestrator(mock_orchestrator)

        response = client.post(
            "/api/v1/shows/",
            json={
                "title": "Breaking Bad",
                "tvdb_id": 81189,
                "quality_profile_id": 1,
                "root_folder_path": "/tv",
                "monitored": True,
                "season_folder": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123
        # Verify call_tool was called with correct parameters
        mock_orchestrator.call_tool.assert_called_once()
        call_args = mock_orchestrator.call_tool.call_args
        assert call_args[0][0] == "sonarr"
        assert call_args[0][1] == "add_series"

    @pytest.mark.asyncio
    async def test_delete_show(self, client, mock_orchestrator, override_orchestrator):
        """Test deleting a show."""
        mock_orchestrator.call_tool.return_value = {"success": True}

        override_orchestrator(mock_orchestrator)

        response = client.delete("/api/v1/shows/123?delete_files=true")

        assert response.status_code == 200
        mock_orchestrator.call_tool.assert_called_once_with(
            "sonarr", "delete_series", {"series_id": 123, "delete_files": True}
        )


class TestMoviesEndpoints:
    """Test Movies (Radarr) endpoints."""

    @pytest.mark.asyncio
    async def test_list_movies(self, client, mock_orchestrator, override_orchestrator):
        """Test listing all movies."""
        mock_orchestrator.call_tool.return_value = [
            {"id": 1, "title": "The Matrix"},
            {"id": 2, "title": "Inception"},
        ]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/movies/")

        assert response.status_code == 200
        data = response.json()
        assert "movies" in data
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_search_movies(self, client, mock_orchestrator, override_orchestrator):
        """Test searching for movies."""
        mock_orchestrator.call_tool.return_value = [{"title": "The Matrix", "tmdbId": 603}]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/movies/search/matrix")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_add_movie(self, client, mock_orchestrator, override_orchestrator):
        """Test adding a new movie."""
        mock_orchestrator.call_tool.return_value = {"id": 123, "title": "The Matrix"}

        override_orchestrator(mock_orchestrator)

        response = client.post(
            "/api/v1/movies/",
            json={
                "title": "The Matrix",
                "tmdb_id": 603,
                "quality_profile_id": 1,
                "root_folder_path": "/movies",
                "monitored": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123

    @pytest.mark.asyncio
    async def test_delete_movie(self, client, mock_orchestrator, override_orchestrator):
        """Test deleting a movie."""
        mock_orchestrator.call_tool.return_value = {"success": True}

        override_orchestrator(mock_orchestrator)

        response = client.delete("/api/v1/movies/123?delete_files=true")

        assert response.status_code == 200
        mock_orchestrator.call_tool.assert_called_once()


class TestMediaEndpoints:
    """Test Media (Plex) endpoints."""

    @pytest.mark.asyncio
    async def test_list_libraries(self, client, mock_orchestrator, override_orchestrator):
        """Test listing Plex libraries."""
        mock_orchestrator.call_tool.return_value = [
            {"key": "1", "title": "Movies", "type": "movie"},
            {"key": "2", "title": "TV Shows", "type": "show"},
        ]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/media/libraries")

        assert response.status_code == 200
        data = response.json()
        assert "libraries" in data
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_recently_added(self, client, mock_orchestrator, override_orchestrator):
        """Test getting recently added media."""
        mock_orchestrator.call_tool.return_value = [{"rating_key": "123", "title": "The Matrix"}]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/media/recently-added?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_scan_library(self, client, mock_orchestrator, override_orchestrator):
        """Test scanning a library."""
        mock_orchestrator.call_tool.return_value = {"success": True}

        override_orchestrator(mock_orchestrator)

        response = client.post(
            "/api/v1/media/scan",
            json={"library_key": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_search_media(self, client, mock_orchestrator, override_orchestrator):
        """Test searching for media."""
        mock_orchestrator.call_tool.return_value = [{"rating_key": "123", "title": "The Matrix"}]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/media/search?query=matrix")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_sessions(self, client, mock_orchestrator, override_orchestrator):
        """Test getting active sessions."""
        mock_orchestrator.call_tool.return_value = [
            {"user": "John", "title": "The Matrix", "state": "playing"}
        ]

        override_orchestrator(mock_orchestrator)

        response = client.get("/api/v1/media/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data


class TestRootEndpoints:
    """Test root API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data

    def test_ping_endpoint(self, client):
        """Test ping endpoint."""
        response = client.get("/ping")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
