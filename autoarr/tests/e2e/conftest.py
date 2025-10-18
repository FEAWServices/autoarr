"""
E2E test fixtures and configuration.

This module provides fixtures for E2E tests including:
- Docker compose test environment setup
- Database fixtures with test data seeding
- MCP server mock fixtures
- API client fixtures
- WebSocket client fixtures
- Cleanup fixtures
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator

import pytest
import websockets
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from autoarr.api.config import Settings, get_settings
from autoarr.api.database import Database
from autoarr.api.main import app
from autoarr.api.models import Base


# ============================================================================
# Test Settings Fixture
# ============================================================================


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Create test settings with isolated test database.

    Returns:
        Settings: Test configuration
    """
    return Settings(
        app_env="testing",
        log_level="DEBUG",
        database_url="sqlite+aiosqlite:///:memory:",
        # Test service URLs (can be mocked)
        sabnzbd_url="http://localhost:18080",
        sabnzbd_api_key="test_sabnzbd_key",
        sonarr_url="http://localhost:18989",
        sonarr_api_key="test_sonarr_key",
        radarr_url="http://localhost:17878",
        radarr_api_key="test_radarr_key",
        plex_url="http://localhost:32400",
        plex_token="test_plex_token",
        # Security
        secret_key="test_secret_key_for_e2e_tests",
        cors_origins=["http://localhost:3000", "http://localhost:5173"],
        # Timeouts (shorter for tests)
        sabnzbd_timeout=5.0,
        sonarr_timeout=5.0,
        radarr_timeout=5.0,
        plex_timeout=5.0,
    )


@pytest.fixture(scope="session", autouse=True)
def override_get_settings(test_settings: Settings):
    """Override get_settings dependency for all E2E tests."""
    from autoarr.api import config

    original = config.get_settings
    config.get_settings = lambda: test_settings

    yield

    config.get_settings = original


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
async def test_database(test_settings: Settings) -> AsyncGenerator[Database, None]:
    """
    Create test database instance.

    Yields:
        Database: Test database instance
    """
    db = Database(test_settings.database_url)
    await db.init_db()
    yield db
    await db.close()


@pytest.fixture
async def db_session(test_database: Database) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for a test.

    Yields:
        AsyncSession: Database session
    """
    async with test_database.get_session() as session:
        yield session
        await session.rollback()  # Rollback after each test


@pytest.fixture
async def seed_test_data(db_session: AsyncSession) -> None:
    """
    Seed database with test data for E2E tests.

    This fixture populates the database with:
    - Sample best practices
    - Sample configuration audits
    - Sample activity logs
    - Sample settings
    """
    from autoarr.api.models import BestPractice, ConfigAudit, ActivityLog, Setting

    # Seed best practices
    best_practices = [
        BestPractice(
            id="sabnzbd_01",
            service="sabnzbd",
            category="performance",
            name="article_cache",
            description="Article cache should be at least 500MB",
            check_type="threshold",
            threshold_value=500,
            severity="warning",
            recommendation="Increase article cache to at least 500MB for better performance",
        ),
        BestPractice(
            id="sonarr_01",
            service="sonarr",
            category="quality",
            name="quality_profile",
            description="Should have at least one quality profile configured",
            check_type="exists",
            severity="error",
            recommendation="Configure at least one quality profile",
        ),
        BestPractice(
            id="radarr_01",
            service="radarr",
            category="quality",
            name="quality_profile",
            description="Should have at least one quality profile configured",
            check_type="exists",
            severity="error",
            recommendation="Configure at least one quality profile",
        ),
    ]

    for bp in best_practices:
        db_session.add(bp)

    # Seed settings
    settings = [
        Setting(key="notifications_enabled", value="true"),
        Setting(key="auto_retry_enabled", value="true"),
        Setting(key="max_retry_attempts", value="3"),
    ]

    for setting in settings:
        db_session.add(setting)

    await db_session.commit()


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
async def api_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """
    Create API client for testing.

    Yields:
        AsyncClient: HTTP client configured for testing
    """
    # Use TestClient for E2E tests to test the real app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # Convert synchronous TestClient to async wrapper
        async_client = AsyncClient(app=app, base_url="http://testserver")
        yield async_client
        await async_client.aclose()


@pytest.fixture
async def authenticated_client(
    api_client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create authenticated API client with auth headers.

    Yields:
        AsyncClient: Authenticated HTTP client
    """
    # TODO: Implement authentication when auth is added
    # For now, return the regular client
    yield api_client


# ============================================================================
# WebSocket Fixtures
# ============================================================================


@pytest.fixture
async def websocket_client(test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    Create WebSocket client for testing real-time events.

    Yields:
        WebSocket client connection
    """
    # Note: WebSocket endpoint needs to be implemented in main.py
    # For now, this is a placeholder for future WebSocket testing
    ws_url = "ws://testserver/ws"

    try:
        async with websockets.connect(ws_url) as websocket:
            yield websocket
    except Exception as e:
        # If WebSocket not implemented yet, yield None
        pytest.skip(f"WebSocket not available: {e}")


# ============================================================================
# MCP Server Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_sabnzbd_responses() -> Dict[str, Any]:
    """
    Mock responses from SABnzbd MCP server.

    Returns:
        Dict: Mock response data
    """
    return {
        "queue": {
            "status": "active",
            "speed": "10 MB/s",
            "size_left": "1.5 GB",
            "items": [
                {
                    "nzo_id": "SABnzbd_nzo_test123",
                    "filename": "Test.Show.S01E01.1080p.WEB.H264",
                    "status": "Downloading",
                    "percentage": 45,
                    "size": "1.2 GB",
                }
            ],
        },
        "history": {
            "items": [
                {
                    "nzo_id": "SABnzbd_nzo_failed123",
                    "name": "Failed.Download.S01E01",
                    "status": "Failed",
                    "fail_message": "Incomplete download",
                }
            ]
        },
        "config": {
            "misc": {"cache_limit": "200M", "download_dir": "/downloads"},
            "servers": [{"host": "news.example.com", "port": 563, "ssl": True}],
        },
    }


@pytest.fixture
def mock_sonarr_responses() -> Dict[str, Any]:
    """
    Mock responses from Sonarr MCP server.

    Returns:
        Dict: Mock response data
    """
    return {
        "series": [
            {
                "id": 1,
                "title": "Test Show",
                "year": 2024,
                "status": "continuing",
                "tvdbId": 123456,
                "qualityProfileId": 1,
            }
        ],
        "quality_profiles": [
            {"id": 1, "name": "HD-1080p", "cutoff": {"id": 9, "name": "HDTV-1080p"}}
        ],
        "wanted": {
            "page": 1,
            "pageSize": 10,
            "totalRecords": 1,
            "records": [
                {
                    "seriesId": 1,
                    "episodeFileId": 0,
                    "seasonNumber": 1,
                    "episodeNumber": 1,
                    "title": "Pilot",
                }
            ],
        },
    }


@pytest.fixture
def mock_radarr_responses() -> Dict[str, Any]:
    """
    Mock responses from Radarr MCP server.

    Returns:
        Dict: Mock response data
    """
    return {
        "movies": [
            {
                "id": 1,
                "title": "Test Movie",
                "year": 2024,
                "tmdbId": 123456,
                "qualityProfileId": 1,
                "hasFile": True,
            }
        ],
        "quality_profiles": [
            {"id": 1, "name": "HD-1080p", "cutoff": {"id": 7, "name": "Bluray-1080p"}}
        ],
        "wanted": {
            "page": 1,
            "pageSize": 10,
            "totalRecords": 1,
            "records": [
                {
                    "title": "Missing Movie",
                    "year": 2024,
                    "hasFile": False,
                }
            ],
        },
    }


@pytest.fixture
def mock_plex_responses() -> Dict[str, Any]:
    """
    Mock responses from Plex MCP server.

    Returns:
        Dict: Mock response data
    """
    return {
        "libraries": [
            {"key": "1", "title": "Movies", "type": "movie"},
            {"key": "2", "title": "TV Shows", "type": "show"},
        ],
        "recently_added": {
            "size": 2,
            "Metadata": [
                {"title": "Test Movie", "type": "movie", "addedAt": 1699564800},
                {"title": "Test Show", "type": "show", "addedAt": 1699478400},
            ],
        },
    }


# ============================================================================
# Docker Compose Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    """
    Return path to Docker Compose file for E2E tests.

    Returns:
        Path: Docker compose file path
    """
    return Path(__file__).parent.parent.parent.parent / "docker" / "docker-compose.test.yml"


@pytest.fixture(scope="session", autouse=False)
def docker_services(docker_compose_file: Path) -> Generator[None, None, None]:
    """
    Start Docker Compose services for E2E tests.

    This fixture is not autouse - only use it for tests that require
    real Docker services.

    Yields:
        None
    """
    if not docker_compose_file.exists():
        pytest.skip(f"Docker Compose file not found: {docker_compose_file}")

    import subprocess

    # Start services
    subprocess.run(
        ["docker-compose", "-f", str(docker_compose_file), "up", "-d"],
        check=True,
    )

    # Wait for services to be ready
    time.sleep(5)

    yield

    # Cleanup: stop services
    subprocess.run(
        ["docker-compose", "-f", str(docker_compose_file), "down"],
        check=False,
    )


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup resources after each test."""
    yield
    # Cleanup code here if needed
    await asyncio.sleep(0.1)  # Allow pending tasks to complete


# ============================================================================
# Helper Fixtures
# ============================================================================


@pytest.fixture
def event_correlation_id() -> str:
    """Generate unique correlation ID for event tracking."""
    import uuid

    return str(uuid.uuid4())


@pytest.fixture
async def wait_for_event():
    """
    Helper fixture to wait for async events.

    Returns:
        Callable that waits for a condition to be true
    """

    async def _wait(condition, timeout: float = 5.0, interval: float = 0.1):
        """
        Wait for condition to be true.

        Args:
            condition: Callable that returns bool
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds

        Raises:
            TimeoutError: If condition not met within timeout
        """
        elapsed = 0.0
        while elapsed < timeout:
            if await condition() if asyncio.iscoroutinefunction(condition) else condition():
                return
            await asyncio.sleep(interval)
            elapsed += interval
        raise TimeoutError(f"Condition not met within {timeout} seconds")

    return _wait
