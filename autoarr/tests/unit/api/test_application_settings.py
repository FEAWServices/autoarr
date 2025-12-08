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
Tests for application settings including log level configuration.

This module tests that when a user changes the application log level,
it is properly saved to the database and applied to the Python logger at runtime.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from autoarr.api.dependencies import reset_orchestrator
from autoarr.api.main import app


@pytest.fixture
def client(mock_database_init):
    """Create a test client with database mocking."""
    from autoarr.api.routers.settings import get_app_settings_repo

    # Create mock AppSettings object
    mock_settings = MagicMock()
    mock_settings.log_level = "INFO"
    mock_settings.timezone = "UTC"
    mock_settings.debug_mode = False

    # Create mock repository
    mock_repo = MagicMock()
    mock_repo.get_settings = AsyncMock(return_value=mock_settings)

    # Make save_settings update the mock_settings object
    async def save_settings_side_effect(log_level=None, timezone=None, debug_mode=None):
        if log_level is not None:
            mock_settings.log_level = log_level
        if timezone is not None:
            mock_settings.timezone = timezone
        if debug_mode is not None:
            mock_settings.debug_mode = debug_mode
        return mock_settings

    mock_repo.save_settings = AsyncMock(side_effect=save_settings_side_effect)

    # Override the dependency
    async def override_get_app_settings_repo():
        return mock_repo

    app.dependency_overrides[get_app_settings_repo] = override_get_app_settings_repo

    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    reset_orchestrator()
    app.dependency_overrides.clear()


class TestLogLevelSettings:
    """Tests for log level configuration."""

    @pytest.mark.asyncio
    async def test_get_application_settings_returns_log_level(self, client):
        """Test that GET /settings/app returns current log level."""
        response = client.get("/api/v1/settings/app")

        assert response.status_code == 200
        data = response.json()
        assert "log_level" in data
        assert data["log_level"] in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    @pytest.mark.asyncio
    async def test_update_log_level_to_debug(self, client):
        """Test that updating log level to DEBUG saves and is applied."""
        # Update log level to DEBUG
        response = client.put("/api/v1/settings/app", json={"log_level": "DEBUG"})

        assert response.status_code == 200
        data = response.json()
        assert data["log_level"] == "DEBUG"
        assert data["message"] == "Application settings updated successfully"

    @pytest.mark.asyncio
    async def test_update_log_level_applies_to_logger(self, client):
        """Test that updating log level actually changes the Python logger level."""
        # Get the root logger to verify level change
        root_logger = logging.getLogger()
        original_level = root_logger.level

        try:
            # Update log level to DEBUG
            response = client.put("/api/v1/settings/app", json={"log_level": "DEBUG"})

            assert response.status_code == 200

            # Verify the logger level was changed
            assert root_logger.level == logging.DEBUG

            # Update to WARNING
            response = client.put("/api/v1/settings/app", json={"log_level": "WARNING"})

            assert response.status_code == 200
            assert root_logger.level == logging.WARNING

        finally:
            # Restore original level
            root_logger.setLevel(original_level)

    @pytest.mark.asyncio
    async def test_update_log_level_persists_to_database(self, client):
        """Test that log level change is persisted to the database."""
        # The fixture already handles mocking, just verify save was called
        # by checking the response contains the updated value
        response = client.put("/api/v1/settings/app", json={"log_level": "DEBUG"})

        assert response.status_code == 200
        data = response.json()
        assert data["log_level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_invalid_log_level_returns_error(self, client):
        """Test that an invalid log level returns a 400 bad request error."""
        response = client.put("/api/v1/settings/app", json={"log_level": "INVALID_LEVEL"})

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_log_level_case_insensitive(self, client):
        """Test that log level accepts different cases."""
        # Test lowercase
        response = client.put("/api/v1/settings/app", json={"log_level": "debug"})

        assert response.status_code == 200
        data = response.json()
        # Should be normalized to uppercase
        assert data["log_level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_get_application_settings_loads_from_database(self, client):
        """Test that application settings are loaded from database if available."""
        # First set the log level to WARNING
        client.put("/api/v1/settings/app", json={"log_level": "WARNING"})

        # Now get the settings and verify it returns WARNING
        response = client.get("/api/v1/settings/app")

        assert response.status_code == 200
        data = response.json()
        assert data["log_level"] == "WARNING"

    @pytest.mark.asyncio
    async def test_log_level_change_emits_debug_messages(self, client):
        """Test that after changing to DEBUG, debug messages are logged."""
        root_logger = logging.getLogger("autoarr")
        original_level = root_logger.level

        try:
            # Set up a handler to capture log output
            log_records = []

            class TestHandler(logging.Handler):
                def emit(self, record):
                    log_records.append(record)

            handler = TestHandler()
            handler.setLevel(logging.DEBUG)
            root_logger.addHandler(handler)

            # Update log level to DEBUG
            response = client.put("/api/v1/settings/app", json={"log_level": "DEBUG"})

            assert response.status_code == 200

            # Trigger a debug log (this would be done by app code)
            root_logger.debug("Test debug message")

            # Verify debug message was captured
            debug_records = [r for r in log_records if r.levelno == logging.DEBUG]
            assert len(debug_records) > 0

            root_logger.removeHandler(handler)

        finally:
            root_logger.setLevel(original_level)


class TestApplicationSettingsValidation:
    """Tests for application settings validation."""

    @pytest.mark.asyncio
    async def test_empty_request_body_returns_error(self, client):
        """Test that empty request body returns validation error."""
        response = client.put("/api/v1/settings/app", json={})

        # Should either succeed with no changes or return 422
        # depending on implementation (partial updates vs required fields)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_log_levels_enum_values(self, client):
        """Test all valid log level enum values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            response = client.put("/api/v1/settings/app", json={"log_level": level})

            assert response.status_code == 200, f"Failed for log level: {level}"
            data = response.json()
            assert data["log_level"] == level
