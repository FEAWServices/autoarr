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
Tests for FastAPI dependency injection.

This module tests the dependency injection functions for the orchestrator
and configuration management.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.api.config import Settings
from autoarr.api.dependencies import (
    get_orchestrator,
    get_orchestrator_config,
    reset_orchestrator,
    shutdown_orchestrator,
)
from autoarr.shared.core.config import MCPOrchestratorConfig, ServerConfig


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        # SABnzbd settings
        sabnzbd_url="http://test-sabnzbd:8080",
        sabnzbd_api_key="test-sabnzbd-key",
        sabnzbd_enabled=True,
        sabnzbd_timeout=30.0,
        # Sonarr settings
        sonarr_url="http://test-sonarr:8989",
        sonarr_api_key="test-sonarr-key",
        sonarr_enabled=True,
        sonarr_timeout=30.0,
        # Radarr settings
        radarr_url="http://test-radarr:7878",
        radarr_api_key="test-radarr-key",
        radarr_enabled=True,
        radarr_timeout=30.0,
        # Plex settings
        plex_url="http://test-plex:32400",
        plex_token="test-plex-token",
        plex_enabled=True,
        plex_timeout=30.0,
        # Orchestrator settings
        max_concurrent_requests=10,
        default_tool_timeout=30.0,
        max_retries=3,
        auto_reconnect=True,
        keepalive_interval=30.0,
        health_check_interval=60,
        health_check_failure_threshold=3,
        circuit_breaker_threshold=5,
        circuit_breaker_timeout=60.0,
        circuit_breaker_success_threshold=3,
        max_parallel_calls=10,
        parallel_timeout=None,
    )


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up orchestrator after each test."""
    yield
    reset_orchestrator()
    # Clear the LRU cache on get_orchestrator_config
    get_orchestrator_config.cache_clear()


class TestGetOrchestratorConfig:
    """Test orchestrator configuration creation."""

    def test_creates_config_from_settings(self, test_settings):
        """Test that config is created from settings."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert isinstance(config, MCPOrchestratorConfig)
            assert config.max_concurrent_requests == 10
            assert config.default_tool_timeout == 30.0
            assert config.max_retries == 3
            assert config.auto_reconnect is True

    def test_creates_sabnzbd_server_config(self, test_settings):
        """Test that SABnzbd server config is created."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.sabnzbd is not None
            assert isinstance(config.sabnzbd, ServerConfig)
            assert config.sabnzbd.name == "sabnzbd"
            assert config.sabnzbd.url == "http://test-sabnzbd:8080"
            assert config.sabnzbd.api_key == "test-sabnzbd-key"
            assert config.sabnzbd.enabled is True
            assert config.sabnzbd.timeout == 30.0

    def test_creates_sonarr_server_config(self, test_settings):
        """Test that Sonarr server config is created."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.sonarr is not None
            assert isinstance(config.sonarr, ServerConfig)
            assert config.sonarr.name == "sonarr"
            assert config.sonarr.url == "http://test-sonarr:8989"
            assert config.sonarr.api_key == "test-sonarr-key"
            assert config.sonarr.enabled is True

    def test_creates_radarr_server_config(self, test_settings):
        """Test that Radarr server config is created."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.radarr is not None
            assert isinstance(config.radarr, ServerConfig)
            assert config.radarr.name == "radarr"
            assert config.radarr.url == "http://test-radarr:7878"
            assert config.radarr.api_key == "test-radarr-key"
            assert config.radarr.enabled is True

    def test_creates_plex_server_config(self, test_settings):
        """Test that Plex server config is created."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.plex is not None
            assert isinstance(config.plex, ServerConfig)
            assert config.plex.name == "plex"
            assert config.plex.url == "http://test-plex:32400"
            assert config.plex.api_key == "test-plex-token"
            assert config.plex.enabled is True

    def test_skips_disabled_server(self):
        """Test that disabled servers are not configured."""
        settings = Settings(
            sabnzbd_enabled=False,
            sabnzbd_api_key="",
            sonarr_enabled=True,
            sonarr_api_key="test-key",
        )

        with patch("autoarr.api.dependencies.get_settings", return_value=settings):
            config = get_orchestrator_config(None)

            assert config.sabnzbd is None
            assert config.sonarr is not None

    def test_skips_server_without_api_key(self):
        """Test that servers without API keys are not configured."""
        settings = Settings(
            sabnzbd_enabled=True,
            sabnzbd_api_key="",  # Empty API key
            sonarr_enabled=True,
            sonarr_api_key="test-key",
        )

        with patch("autoarr.api.dependencies.get_settings", return_value=settings):
            config = get_orchestrator_config(None)

            assert config.sabnzbd is None
            assert config.sonarr is not None

    def test_uses_default_settings_when_none_provided(self):
        """Test that default settings are used when None is provided."""
        config = get_orchestrator_config(None)

        assert isinstance(config, MCPOrchestratorConfig)

    def test_config_is_cached(self, test_settings):
        """Test that config is cached using lru_cache."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config1 = get_orchestrator_config(None)
            config2 = get_orchestrator_config(None)

            # Should be the same instance due to caching
            assert config1 is config2

    def test_circuit_breaker_settings(self, test_settings):
        """Test that circuit breaker settings are configured."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.circuit_breaker_threshold == 5
            assert config.circuit_breaker_timeout == 60.0
            assert config.circuit_breaker_success_threshold == 3

    def test_parallel_call_settings(self, test_settings):
        """Test that parallel call settings are configured."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.max_parallel_calls == 10  # noqa: F841
            assert config.parallel_timeout is None

    def test_health_check_settings(self, test_settings):
        """Test that health check settings are configured."""
        with patch("autoarr.api.dependencies.get_settings", return_value=test_settings):
            config = get_orchestrator_config(None)

            assert config.health_check_interval == 60
            assert config.health_check_failure_threshold == 3
            assert config.keepalive_interval == 30.0


class TestGetOrchestrator:
    """Test orchestrator dependency injection."""

    @pytest.mark.asyncio
    async def test_creates_orchestrator_on_first_call(self):
        """Test that orchestrator is created on first call."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock()
            mock_orch_class.return_value = mock_orch

            # Get orchestrator
            async for orch in get_orchestrator():
                assert orch is mock_orch

            # Verify orchestrator was created and connected
            mock_orch_class.assert_called_once()
            mock_orch.connect_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_same_orchestrator_on_subsequent_calls(self):
        """Test that same orchestrator instance is returned."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock()
            mock_orch_class.return_value = mock_orch

            # Get orchestrator twice
            async for orch1 in get_orchestrator():
                first_orch = orch1

            async for orch2 in get_orchestrator():
                second_orch = orch2

            # Should be the same instance
            assert first_orch is second_orch

            # Orchestrator should only be created once
            assert mock_orch_class.call_count == 1
            # Connect should only be called once
            assert mock_orch.connect_all.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_connection_failure_gracefully(self):
        """Test that connection failures are handled gracefully."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock(side_effect=Exception("Connection failed"))
            mock_orch_class.return_value = mock_orch

            # Get orchestrator - should not raise even if connect fails
            async for orch in get_orchestrator():
                assert orch is mock_orch

            # Connect was attempted
            mock_orch.connect_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_orchestrator_config(self, test_settings):
        """Test that orchestrator is created with correct config."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock()
            mock_orch_class.return_value = mock_orch

            with patch("autoarr.api.dependencies.get_orchestrator_config") as mock_get_config:
                mock_config = MagicMock()
                mock_get_config.return_value = mock_config

                async for orch in get_orchestrator():
                    pass

                # Verify config was retrieved and used
                mock_get_config.assert_called_once()
                mock_orch_class.assert_called_once_with(mock_config)


class TestShutdownOrchestrator:
    """Test orchestrator shutdown."""

    @pytest.mark.asyncio
    async def test_shuts_down_orchestrator_gracefully(self):
        """Test graceful orchestrator shutdown."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock()
            mock_orch.shutdown = AsyncMock()
            mock_orch_class.return_value = mock_orch

            # Create orchestrator
            async for _ in get_orchestrator():
                pass

            # Shutdown
            await shutdown_orchestrator()

            # Verify graceful shutdown was called
            mock_orch.shutdown.assert_called_once_with(graceful=True, timeout=10.0)

    @pytest.mark.asyncio
    async def test_forces_shutdown_on_graceful_failure(self):
        """Test that force shutdown is attempted if graceful fails."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock()
            # First call (graceful) fails, second call (force) succeeds
            mock_orch.shutdown = AsyncMock(side_effect=[Exception("Graceful failed"), None])
            mock_orch_class.return_value = mock_orch

            # Create orchestrator
            async for _ in get_orchestrator():
                pass

            # Shutdown
            await shutdown_orchestrator()

            # Verify shutdown was called twice
            assert mock_orch.shutdown.call_count == 2
            # First call was graceful
            assert mock_orch.shutdown.call_args_list[0][1] == {"graceful": True, "timeout": 10.0}
            # Second call was force
            assert mock_orch.shutdown.call_args_list[1][1] == {"force": True}

    @pytest.mark.asyncio
    async def test_handles_shutdown_when_no_orchestrator(self):
        """Test shutdown when orchestrator was never created."""
        # Don't create orchestrator, just try to shut down
        await shutdown_orchestrator()
        # Should not raise an exception

    @pytest.mark.asyncio
    async def test_handles_force_shutdown_failure(self):
        """Test that force shutdown failures are handled."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch = MagicMock()
            mock_orch.connect_all = AsyncMock()
            # Both calls fail
            mock_orch.shutdown = AsyncMock(side_effect=Exception("Shutdown failed"))
            mock_orch_class.return_value = mock_orch

            # Create orchestrator
            async for _ in get_orchestrator():
                pass

            # Shutdown should not raise even if both attempts fail
            await shutdown_orchestrator()

    @pytest.mark.asyncio
    async def test_resets_orchestrator_after_shutdown(self):
        """Test that orchestrator is reset after shutdown."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch1 = MagicMock()
            mock_orch1.connect_all = AsyncMock()
            mock_orch1.shutdown = AsyncMock()

            mock_orch2 = MagicMock()
            mock_orch2.connect_all = AsyncMock()

            mock_orch_class.side_effect = [mock_orch1, mock_orch2]

            # Create orchestrator
            async for orch1 in get_orchestrator():
                first_orch = orch1

            # Shutdown
            await shutdown_orchestrator()

            # Create new orchestrator
            async for orch2 in get_orchestrator():
                second_orch = orch2

            # Should be different instances
            assert first_orch is not second_orch


class TestResetOrchestrator:
    """Test orchestrator reset."""

    def test_resets_orchestrator_instance(self):
        """Test that reset clears the orchestrator instance."""
        # This is primarily used for testing
        reset_orchestrator()
        # Should not raise

    @pytest.mark.asyncio
    async def test_forces_new_orchestrator_after_reset(self):
        """Test that new orchestrator is created after reset."""
        with patch("autoarr.api.dependencies.MCPOrchestrator") as mock_orch_class:
            mock_orch1 = MagicMock()
            mock_orch1.connect_all = AsyncMock()

            mock_orch2 = MagicMock()
            mock_orch2.connect_all = AsyncMock()

            mock_orch_class.side_effect = [mock_orch1, mock_orch2]

            # Create first orchestrator
            async for orch1 in get_orchestrator():
                first_orch = orch1

            # Reset
            reset_orchestrator()

            # Create second orchestrator
            async for orch2 in get_orchestrator():
                second_orch = orch2

            # Should be different instances
            assert first_orch is not second_orch
            assert mock_orch_class.call_count == 2
