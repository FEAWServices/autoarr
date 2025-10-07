"""
Root conftest.py for pytest configuration and shared fixtures.

This file provides global test configuration and fixtures used across all test modules.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator

# IMPORTANT: Add paths BEFORE any other imports to ensure modules can be found
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "mcp_servers") not in sys.path:
    sys.path.insert(0, str(root_dir / "mcp_servers"))

import pytest
from httpx import AsyncClient, Response
from pytest_httpx import HTTPXMock


# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture
def load_test_data(test_data_dir: Path) -> callable:
    """
    Factory fixture to load test data from JSON files.

    Usage:
        data = load_test_data("sabnzbd_queue_response.json")
    """

    def _load(filename: str) -> Dict[str, Any]:
        filepath = test_data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Test data file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    return _load


@pytest.fixture
def mock_httpx_response() -> callable:
    """
    Factory fixture to create mock httpx Response objects.

    Usage:
        response = mock_httpx_response(200, {"key": "value"})
    """

    def _create_response(
        status_code: int,
        json_data: Dict[str, Any] | None = None,
        text: str | None = None,
    ) -> Response:
        """Create a mock Response object."""
        content = text.encode() if text else json.dumps(json_data or {}).encode()
        return Response(
            status_code=status_code,
            content=content,
            headers={"content-type": "application/json"},
        )

    return _create_response


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for integration tests."""
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def httpx_mock(httpx_mock: HTTPXMock) -> HTTPXMock:
    """Provide HTTPXMock fixture from pytest-httpx."""
    return httpx_mock


# Pytest hook to configure paths before collection
def pytest_configure(config):
    """Configure pytest before collection starts."""
    # Paths should already be set from module-level code above
    pass


# Import fixture factories from tests/fixtures/
pytest_plugins = ["tests.fixtures.api_fixtures", "tests.fixtures.mcp_orchestrator_fixtures"]
