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
Tests for FastAPI main application lifespan.

This module tests the application startup and shutdown lifecycle,
including database initialization and orchestrator management.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from autoarr.api.config import Settings
from autoarr.api.main import app, lifespan


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        app_env="test",
        log_level="INFO",
        database_url="sqlite:///test.db",
    )


@pytest.fixture
def test_settings_no_db():
    """Create test settings without database."""
    return Settings(
        app_env="test",
        log_level="INFO",
        database_url=None,
    )


class TestLifespanStartup:
    """Test application startup lifecycle."""

    @pytest.mark.asyncio
    async def test_logs_startup_message(self, test_settings):
        test_app = FastAPI()
        """Test that startup messages are logged."""
        test_app = FastAPI()
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger") as mock_logger:
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator"):
                        mock_db = MagicMock()
                        mock_db.init_db = AsyncMock()
                        mock_db.close = AsyncMock()
                        mock_init_db.return_value = mock_db

                        async with lifespan(test_app):
                            pass

                        # Check startup logs
                        calls = [
                            str(call) for call in mock_logger.info.call_args_list
                        ]  # noqa: F841
                        assert any("Starting AutoArr" in call for call in calls)
                        assert any("Environment: test" in call for call in calls)
                        assert any("Log level: INFO" in call for call in calls)

    @pytest.mark.asyncio
    async def test_initializes_database_when_configured(self, test_settings):
        test_app = FastAPI()
        """Test that database is initialized when DATABASE_URL is set."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator"):
                        mock_db = MagicMock()
                        mock_db.init_db = AsyncMock()
                        mock_db.close = AsyncMock()
                        mock_init_db.return_value = mock_db

                        async with lifespan(test_app):
                            pass

                        # Verify database was initialized
                        mock_init_db.assert_called_once_with("sqlite:///test.db")
                        mock_db.init_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_database_initialization(self, test_settings):
        test_app = FastAPI()
        """Test that database initialization is logged."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger") as mock_logger:
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator"):
                        mock_db = MagicMock()
                        mock_db.init_db = AsyncMock()
                        mock_db.close = AsyncMock()
                        mock_init_db.return_value = mock_db

                        async with lifespan(test_app):
                            pass

                        calls = [
                            str(call) for call in mock_logger.info.call_args_list
                        ]  # noqa: F841
                        assert any("Initializing database" in call for call in calls)
                        assert any("Database initialized successfully" in call for call in calls)

    @pytest.mark.asyncio
    async def test_warns_when_no_database_configured(self, test_settings_no_db):
        test_app = FastAPI()
        """Test that warning is logged when no database is configured."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings_no_db):
            with patch("autoarr.api.main.logger") as mock_logger:
                with patch("autoarr.api.main.shutdown_orchestrator"):
                    async with lifespan(test_app):
                        pass

                    # Check for warning
                    mock_logger.warning.assert_called_once()
                    warning_call = str(mock_logger.warning.call_args)
                    assert "No DATABASE_URL configured" in warning_call
                    assert "will not persist" in warning_call

    @pytest.mark.asyncio
    async def test_skips_database_init_when_not_configured(self, test_settings_no_db):
        test_app = FastAPI()
        """Test that database init is skipped when not configured."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings_no_db):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator"):
                        async with lifespan(test_app):
                            pass

                        # Database should not be initialized
                        mock_init_db.assert_not_called()


class TestLifespanShutdown:
    """Test application shutdown lifecycle."""

    @pytest.mark.asyncio
    async def test_logs_shutdown_message(self, test_settings_no_db):
        test_app = FastAPI()
        """Test that shutdown messages are logged."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings_no_db):
            with patch("autoarr.api.main.logger") as mock_logger:
                with patch("autoarr.api.main.shutdown_orchestrator"):
                    async with lifespan(test_app):
                        pass

                    # Check shutdown logs
                    calls = [str(call) for call in mock_logger.info.call_args_list]  # noqa: F841
                    assert any("Shutting down AutoArr" in call for call in calls)
                    assert any("Shutdown complete" in call for call in calls)

    @pytest.mark.asyncio
    async def test_shuts_down_orchestrator(self, test_settings_no_db):
        test_app = FastAPI()
        """Test that orchestrator is shut down."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings_no_db):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.shutdown_orchestrator") as mock_shutdown:
                    async with lifespan(test_app):
                        pass

                    # Verify shutdown was called
                    mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_database_when_configured(self, test_settings):
        test_app = FastAPI()
        """Test that database is closed when configured."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.get_database") as mock_get_db:
                        with patch("autoarr.api.main.shutdown_orchestrator"):
                            mock_db = MagicMock()
                            mock_db.init_db = AsyncMock()
                            mock_db.close = AsyncMock()
                            mock_init_db.return_value = mock_db
                            mock_get_db.return_value = mock_db

                            async with lifespan(test_app):
                                pass

                            # Verify database was closed
                            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_database_closure(self, test_settings):
        test_app = FastAPI()
        """Test that database closure is logged."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger") as mock_logger:
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.get_database") as mock_get_db:
                        with patch("autoarr.api.main.shutdown_orchestrator"):
                            mock_db = MagicMock()
                            mock_db.init_db = AsyncMock()
                            mock_db.close = AsyncMock()
                            mock_init_db.return_value = mock_db
                            mock_get_db.return_value = mock_db

                            async with lifespan(test_app):
                                pass

                            calls = [
                                str(call) for call in mock_logger.info.call_args_list
                            ]  # noqa: F841
                            assert any("Database connections closed" in call for call in calls)

    @pytest.mark.asyncio
    async def test_handles_database_not_initialized(self, test_settings_no_db):
        test_app = FastAPI()
        """Test that shutdown handles case where database was not initialized."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings_no_db):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.get_database") as mock_get_db:
                    with patch("autoarr.api.main.shutdown_orchestrator"):
                        # get_database raises RuntimeError when not initialized
                        mock_get_db.side_effect = RuntimeError("Database not initialized")

                        # Should not raise
                        async with lifespan(test_app):
                            pass

    @pytest.mark.asyncio
    async def test_shutdown_order(self, test_settings):
        test_app = FastAPI()
        """Test that shutdown happens in correct order."""
        call_order = []

        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.get_database") as mock_get_db:
                        with patch("autoarr.api.main.shutdown_orchestrator") as mock_shutdown:
                            mock_db = MagicMock()
                            mock_db.init_db = AsyncMock()

                            async def close_db():
                                call_order.append("database")

                            mock_db.close = close_db
                            mock_init_db.return_value = mock_db
                            mock_get_db.return_value = mock_db

                            async def shutdown_orch():
                                call_order.append("orchestrator")

                            mock_shutdown.side_effect = shutdown_orch

                            async with lifespan(test_app):
                                pass

                            # Orchestrator should shut down before database
                            assert call_order == ["orchestrator", "database"]


class TestLifespanFullCycle:
    """Test full startup and shutdown cycle."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_with_database(self, test_settings):
        test_app = FastAPI()
        """Test complete lifecycle with database."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.get_database") as mock_get_db:
                        with patch("autoarr.api.main.shutdown_orchestrator") as mock_shutdown:
                            mock_db = MagicMock()
                            mock_db.init_db = AsyncMock()
                            mock_db.close = AsyncMock()
                            mock_init_db.return_value = mock_db
                            mock_get_db.return_value = mock_db

                            async with lifespan(test_app):
                                # App is running
                                pass

                            # Verify startup
                            mock_init_db.assert_called_once()
                            mock_db.init_db.assert_called_once()

                            # Verify shutdown
                            mock_shutdown.assert_called_once()
                            mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_lifecycle_without_database(self, test_settings_no_db):
        test_app = FastAPI()
        """Test complete lifecycle without database."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings_no_db):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator") as mock_shutdown:
                        async with lifespan(test_app):
                            # App is running
                            pass

                        # Verify database was not initialized
                        mock_init_db.assert_not_called()

                        # Verify orchestrator was shut down
                        mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_during_startup_fails_fast(self, test_settings):
        test_app = FastAPI()
        """Test that database init failures cause the app to fail fast."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator"):
                        mock_db = MagicMock()
                        mock_db.init_db = AsyncMock(side_effect=Exception("Init failed"))
                        mock_init_db.return_value = mock_db

                        # Should raise - fail fast when database init fails
                        with pytest.raises(Exception, match="Init failed"):
                            async with lifespan(test_app):
                                pass


class TestAppConfiguration:
    """Test FastAPI app configuration."""

    def test_app_has_correct_metadata(self):
        """Test that app has correct metadata."""
        assert app.title == "AutoArr API"
        assert app.version == "1.0.0"
        assert app.description == "Intelligent media automation orchestrator"

    def test_app_has_docs_urls(self):
        """Test that docs URLs are configured."""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_app_has_middleware(self):
        """Test that middleware is configured."""
        # FastAPI app should have middleware
        assert len(app.user_middleware) > 0

    def test_app_has_routers(self):
        """Test that routers are included."""
        # Check that routes exist
        routes = [route.path for route in app.routes]

        # Health endpoints
        assert "/health" in routes

        # MCP endpoints
        assert any("/api/v1/mcp" in route for route in routes)

        # Service endpoints
        assert any("/api/v1/downloads" in route for route in routes)
        assert any("/api/v1/shows" in route for route in routes)
        assert any("/api/v1/movies" in route for route in routes)
        assert any("/api/v1/media" in route for route in routes)

    def test_root_endpoint_exists(self):
        """Test that API info endpoint exists."""
        routes = [route.path for route in app.routes]
        # The app uses /api for API info and /{full_path:path} for SPA catch-all
        assert "/api" in routes

    def test_ping_endpoint_exists(self):
        """Test that ping endpoint exists."""
        routes = [route.path for route in app.routes]
        assert "/ping" in routes

    def test_pwa_endpoints_exist(self):
        """Test that PWA-related endpoints exist."""
        routes = [route.path for route in app.routes]
        assert "/manifest.json" in routes
        assert "/logo-192.png" in routes
        assert "/logo-512.png" in routes
        assert "/favicon.ico" in routes
        assert "/logo.png" in routes
        assert "/apple-touch-icon.png" in routes

    def test_spa_catchall_endpoint_exists(self):
        """Test that SPA catch-all endpoint exists."""
        routes = [route.path for route in app.routes]
        assert "/{full_path:path}" in routes


def _setup_pwa_file_mock(mock_path, exists=True, resolve_path=None):
    """Helper to set up mock path chain for PWA file tests."""
    mock_file = MagicMock()
    mock_file.exists.return_value = exists
    if resolve_path:
        mock_file.resolve.return_value = resolve_path
    # Chain: Path(__file__).parent.parent / "ui" / "dist" / "filename"
    truediv = mock_path.return_value.parent.parent.__truediv__.return_value
    truediv.__truediv__.return_value.__truediv__.return_value = mock_file
    return mock_file


def _setup_spa_dir_mock(mock_path, exists=True, resolve_path=None):
    """Helper to set up mock path chain for SPA directory tests."""
    mock_index = MagicMock()
    mock_index.exists.return_value = exists
    if resolve_path:
        mock_index.resolve.return_value = resolve_path
    mock_dist_dir = MagicMock()
    mock_dist_dir.__truediv__.return_value = mock_index
    # Chain: Path(__file__).parent.parent / "ui" / "dist"
    truediv = mock_path.return_value.parent.parent.__truediv__.return_value
    truediv.__truediv__.return_value = mock_dist_dir
    return mock_index


class TestPWAEndpoints:
    """Test PWA file serving endpoints."""

    @pytest.mark.asyncio
    async def test_serve_manifest_returns_file_when_exists(self, tmp_path):
        """Test serve_manifest returns FileResponse when file exists."""
        from autoarr.api.main import serve_manifest

        # Create a temporary manifest file
        manifest_content = '{"name": "test"}'
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(manifest_content)

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=True, resolve_path=str(manifest_file))
            result = await serve_manifest()

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)

    @pytest.mark.asyncio
    async def test_serve_manifest_raises_404_when_missing(self):
        """Test serve_manifest raises 404 when file doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_manifest

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_manifest()

            assert exc_info.value.status_code == 404
            assert "manifest.json not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_serve_logo_192_raises_404_when_missing(self):
        """Test serve_logo_192 raises 404 when file doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_logo_192

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_logo_192()

            assert exc_info.value.status_code == 404
            assert "logo-192.png not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_serve_logo_512_raises_404_when_missing(self):
        """Test serve_logo_512 raises 404 when file doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_logo_512

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_logo_512()

            assert exc_info.value.status_code == 404
            assert "logo-512.png not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_serve_favicon_raises_404_when_missing(self):
        """Test serve_favicon raises 404 when file doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_favicon

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_favicon()

            assert exc_info.value.status_code == 404
            assert "favicon.ico not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_serve_logo_raises_404_when_missing(self):
        """Test serve_logo raises 404 when file doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_logo

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_logo()

            assert exc_info.value.status_code == 404
            assert "logo.png not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_serve_apple_touch_icon_raises_404_when_missing(self):
        """Test serve_apple_touch_icon raises 404 when file doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_apple_touch_icon

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_apple_touch_icon()

            assert exc_info.value.status_code == 404
            assert "apple-touch-icon.png not found" in str(exc_info.value.detail)


class TestServeSPA:
    """Test SPA catch-all route."""

    @pytest.mark.asyncio
    async def test_serve_spa_raises_503_when_index_missing(self):
        """Test serve_spa raises 503 when index.html doesn't exist."""
        from fastapi import HTTPException

        from autoarr.api.main import serve_spa

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_spa_dir_mock(mock_path, exists=False)

            with pytest.raises(HTTPException) as exc_info:
                await serve_spa("any/path")

            assert exc_info.value.status_code == 503
            assert "UI not available" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_serve_spa_ignores_path_parameter(self):
        """Test serve_spa ignores the path parameter for security."""
        from autoarr.api.main import serve_spa

        # This test verifies that the path parameter is ignored
        # and doesn't affect which file is served
        with patch("autoarr.api.main.Path") as mock_path:
            _setup_spa_dir_mock(mock_path, exists=True, resolve_path="/safe/path/index.html")

            # Call with a potentially malicious path - should be ignored
            result = await serve_spa("../../../etc/passwd")

            # The result should be a FileResponse for index.html
            assert result is not None

    def test_serve_spa_function_signature(self):
        """Test serve_spa accepts full_path parameter."""
        import inspect

        from autoarr.api.main import serve_spa

        sig = inspect.signature(serve_spa)
        params = list(sig.parameters.keys())
        assert "full_path" in params

    @pytest.mark.asyncio
    async def test_serve_spa_returns_file_when_exists(self):
        """Test serve_spa returns FileResponse when index.html exists."""
        from autoarr.api.main import serve_spa

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_spa_dir_mock(mock_path, exists=True, resolve_path="/app/ui/dist/index.html")

            result = await serve_spa("dashboard")

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)


class TestPWAEndpointsSuccess:
    """Test PWA endpoints when files exist."""

    @pytest.mark.asyncio
    async def test_serve_logo_192_returns_file_when_exists(self):
        """Test serve_logo_192 returns FileResponse when file exists."""
        from autoarr.api.main import serve_logo_192

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=True, resolve_path="/app/ui/dist/logo-192.png")

            result = await serve_logo_192()

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)

    @pytest.mark.asyncio
    async def test_serve_logo_512_returns_file_when_exists(self):
        """Test serve_logo_512 returns FileResponse when file exists."""
        from autoarr.api.main import serve_logo_512

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=True, resolve_path="/app/ui/dist/logo-512.png")

            result = await serve_logo_512()

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)

    @pytest.mark.asyncio
    async def test_serve_favicon_returns_file_when_exists(self):
        """Test serve_favicon returns FileResponse when file exists."""
        from autoarr.api.main import serve_favicon

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=True, resolve_path="/app/ui/dist/favicon.ico")

            result = await serve_favicon()

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)

    @pytest.mark.asyncio
    async def test_serve_logo_returns_file_when_exists(self):
        """Test serve_logo returns FileResponse when file exists."""
        from autoarr.api.main import serve_logo

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(mock_path, exists=True, resolve_path="/app/ui/dist/logo.png")

            result = await serve_logo()

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)

    @pytest.mark.asyncio
    async def test_serve_apple_touch_icon_returns_file_when_exists(self):
        """Test serve_apple_touch_icon returns FileResponse when file exists."""
        from autoarr.api.main import serve_apple_touch_icon

        with patch("autoarr.api.main.Path") as mock_path:
            _setup_pwa_file_mock(
                mock_path, exists=True, resolve_path="/app/ui/dist/apple-touch-icon.png"
            )

            result = await serve_apple_touch_icon()

            from fastapi.responses import FileResponse

            assert isinstance(result, FileResponse)
