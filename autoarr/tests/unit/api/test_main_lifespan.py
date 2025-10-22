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
            with patch("autoarr.api.main.logger") as mock_logger:
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
    async def test_exception_during_startup_doesnt_prevent_shutdown(self, test_settings):
        test_app = FastAPI()
        """Test that shutdown still happens if startup has issues."""
        with patch("autoarr.api.main.get_settings", return_value=test_settings):
            with patch("autoarr.api.main.logger"):
                with patch("autoarr.api.main.init_database") as mock_init_db:
                    with patch("autoarr.api.main.shutdown_orchestrator") as mock_shutdown:
                        mock_db = MagicMock()
                        mock_db.init_db = AsyncMock(side_effect=Exception("Init failed"))
                        mock_init_db.return_value = mock_db

                        # Should not raise, startup error is caught
                        async with lifespan(test_app):
                            pass

                        # Shutdown should still be called
                        mock_shutdown.assert_called_once()


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
        """Test that root endpoint exists."""
        routes = [route.path for route in app.routes]
        assert "/" in routes

    def test_ping_endpoint_exists(self):
        """Test that ping endpoint exists."""
        routes = [route.path for route in app.routes]
        assert "/ping" in routes
