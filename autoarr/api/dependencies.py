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
FastAPI dependency injection functions.

This module provides dependency injection for the FastAPI Gateway,
managing the MCP Orchestrator lifecycle and providing it to endpoints.
"""

import logging
from typing import AsyncGenerator, Optional

from autoarr.shared.core.config import MCPOrchestratorConfig, ServerConfig
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


def get_orchestrator_config(settings: Optional[Settings] = None) -> MCPOrchestratorConfig:
    """
    Create MCP Orchestrator configuration from application settings.

    Note: No caching here since Settings objects are not hashable.
    The get_settings() function already implements caching.

    Args:
        settings: Application settings (will use get_settings() if not provided)

    Returns:
        MCPOrchestratorConfig: Orchestrator configuration
    """
    if settings is None:
        settings = get_settings()

    # Create server configurations
    sabnzbd_config = None
    if settings.sabnzbd_enabled and settings.sabnzbd_api_key:
        sabnzbd_config = ServerConfig(
            name="sabnzbd",
            url=settings.sabnzbd_url,
            api_key=settings.sabnzbd_api_key,
            enabled=settings.sabnzbd_enabled,
            timeout=settings.sabnzbd_timeout,
        )

    sonarr_config = None
    if settings.sonarr_enabled and settings.sonarr_api_key:
        sonarr_config = ServerConfig(
            name="sonarr",
            url=settings.sonarr_url,
            api_key=settings.sonarr_api_key,
            enabled=settings.sonarr_enabled,
            timeout=settings.sonarr_timeout,
        )

    radarr_config = None
    if settings.radarr_enabled and settings.radarr_api_key:
        radarr_config = ServerConfig(
            name="radarr",
            url=settings.radarr_url,
            api_key=settings.radarr_api_key,
            enabled=settings.radarr_enabled,
            timeout=settings.radarr_timeout,
        )

    plex_config = None
    if settings.plex_enabled and settings.plex_token:
        plex_config = ServerConfig(
            name="plex",
            url=settings.plex_url,
            api_key=settings.plex_token,
            enabled=settings.plex_enabled,
            timeout=settings.plex_timeout,
        )

    # Create orchestrator configuration
    return MCPOrchestratorConfig(
        sabnzbd=sabnzbd_config,
        sonarr=sonarr_config,
        radarr=radarr_config,
        plex=plex_config,
        max_concurrent_requests=settings.max_concurrent_requests,
        default_tool_timeout=settings.default_tool_timeout,
        max_retries=settings.max_retries,
        auto_reconnect=settings.auto_reconnect,
        keepalive_interval=settings.keepalive_interval,
        health_check_interval=settings.health_check_interval,
        health_check_failure_threshold=settings.health_check_failure_threshold,
        circuit_breaker_threshold=settings.circuit_breaker_threshold,
        circuit_breaker_timeout=settings.circuit_breaker_timeout,
        circuit_breaker_success_threshold=settings.circuit_breaker_success_threshold,
        max_parallel_calls=settings.max_parallel_calls,
        parallel_timeout=settings.parallel_timeout,
    )


# Global orchestrator instance (singleton)
_orchestrator: MCPOrchestrator | None = None


async def get_orchestrator() -> AsyncGenerator[MCPOrchestrator, None]:
    """
    Get or create MCP Orchestrator instance.

    This is a FastAPI dependency that provides the orchestrator to endpoints.
    It manages the orchestrator lifecycle and ensures proper cleanup.

    Yields:
        MCPOrchestrator: The orchestrator instance
    """
    global _orchestrator

    # Create orchestrator if it doesn't exist
    if _orchestrator is None:
        config = get_orchestrator_config()
        _orchestrator = MCPOrchestrator(config)

        # Connect to all enabled servers
        try:
            await _orchestrator.connect_all()
            logger.info("Successfully connected to MCP servers")
        except Exception as e:
            # Log error but continue - individual endpoints will handle connection errors
            logger.error(f"Failed to connect to some MCP servers during startup: {e}")
            logger.warning(
                "Orchestrator initialized but some services may be unavailable. "
                "Individual endpoints will report connection errors."
            )

    yield _orchestrator


async def shutdown_orchestrator() -> None:
    """
    Shutdown the orchestrator on application shutdown.

    This should be called during FastAPI app shutdown to properly
    disconnect from all MCP servers.
    """
    global _orchestrator

    if _orchestrator is not None:
        try:
            await _orchestrator.shutdown(graceful=True, timeout=10.0)
        except Exception:
            # Force shutdown on error
            try:
                await _orchestrator.shutdown(force=True)
            except Exception:
                pass
        finally:
            _orchestrator = None


def reset_orchestrator() -> None:
    """
    Reset the orchestrator instance.

    This is primarily used for testing to ensure a clean state.
    """
    global _orchestrator
    _orchestrator = None
