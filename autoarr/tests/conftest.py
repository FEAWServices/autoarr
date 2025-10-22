"""
Root conftest.py for pytest configuration and shared fixtures.

This file provides global test configuration and fixtures used across all test modules.
"""

import json
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict

# IMPORTANT: Add paths BEFORE any other imports to ensure modules can be found
# Note: With the new repository structure, autoarr is a package and should be
# importable directly. The root directory should be in sys.path.
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from httpx import AsyncClient, Response
from pytest_httpx import HTTPXMock

# Configure pytest-asyncio
# Note: With asyncio_mode = "auto" in pyproject.toml, pytest-asyncio handles event loops automatically.  # noqa: E501
# Custom event_loop fixture removed as it's deprecated and unnecessary with auto mode.


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


@pytest.fixture(autouse=True)
def configure_httpx_mock_defaults(request):
    """
    Configure default options for pytest-httpx globally.

    pytest-httpx 0.32.0+ changed behavior to not reuse matched responses by default.
    We enable can_send_already_matched_responses=True to maintain backward compatibility
    with our existing tests that expect responses to be reusable.
    """
    # Apply the marker to all tests unless they override it
    if "httpx_mock" not in [marker.name for marker in request.node.iter_markers()]:
        request.node.add_marker(
            pytest.mark.httpx_mock(can_send_already_matched_responses=True)
        )


@pytest.fixture
def httpx_mock(httpx_mock: HTTPXMock) -> HTTPXMock:
    """Provide HTTPXMock fixture from pytest-httpx."""
    return httpx_mock


# Pytest hook to configure paths before collection
def pytest_configure(config):
    """Configure pytest before collection starts."""
    # Paths should already be set from module-level code above


# Import fixture factories from tests/fixtures/
pytest_plugins = [
    "autoarr.tests.fixtures.api_fixtures",
    "autoarr.tests.fixtures.mcp_orchestrator_fixtures",
]
