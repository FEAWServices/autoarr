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

from __future__ import annotations

"""
FastAPI dependency injection functions.

This module provides dependency injection for the FastAPI Gateway,
managing the MCP Orchestrator lifecycle and providing it to endpoints.
"""

import logging
from typing import Any, AsyncGenerator, Dict, Optional

from autoarr.shared.core.config import MCPOrchestratorConfig, ServerConfig
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


async def get_db_service_settings() -> Dict[str, Dict[str, Any]]:
    """
    Fetch service settings from the database.

    Returns a dict keyed by service name with url, api_key, enabled, timeout.
    Returns empty dict if database not available.
    """
    try:
        from .database import SettingsRepository, get_database

        db = get_database()
        repo = SettingsRepository(db)
        # Returns dict[str, ServiceSettings] - already keyed by service name
        all_settings = await repo.get_all_service_settings()

        result: Dict[str, Dict[str, Any]] = {}
        for service_name, service_setting in all_settings.items():
            result[service_name] = {
                "url": service_setting.url,
                "api_key": service_setting.api_key_or_token,
                "enabled": service_setting.enabled,
                "timeout": service_setting.timeout or 30.0,
            }
        return result
    except Exception as e:
        logger.debug(f"Could not load database service settings: {e}")
        return {}


def get_orchestrator_config(
    settings: Optional[Settings] = None,
    db_settings: Optional[Dict[str, Dict[str, Any]]] = None,
) -> MCPOrchestratorConfig:
    """
    Create MCP Orchestrator configuration from application settings.

    Settings priority: Database settings > Environment variables > Defaults.

    Args:
        settings: Application settings (will use get_settings() if not provided)
        db_settings: Database service settings (optional, from get_db_service_settings())

    Returns:
        MCPOrchestratorConfig: Orchestrator configuration
    """
    if settings is None:
        settings = get_settings()

    if db_settings is None:
        db_settings = {}

    # Helper to get service config with database settings taking priority
    def get_service_config(
        service_name: str,
        env_url: str,
        env_api_key: str,
        env_enabled: bool,
        env_timeout: float,
    ) -> Optional[ServerConfig]:
        """Get service config, preferring database settings over env vars."""
        db_svc = db_settings.get(service_name, {})

        # Database settings take priority if enabled and has API key
        if db_svc.get("enabled") and db_svc.get("api_key"):
            return ServerConfig(
                name=service_name,
                url=db_svc.get("url", env_url),
                api_key=db_svc.get("api_key", ""),
                enabled=True,
                timeout=db_svc.get("timeout", env_timeout),
            )

        # Fall back to env vars if configured
        if env_enabled and env_api_key:
            return ServerConfig(
                name=service_name,
                url=env_url,
                api_key=env_api_key,
                enabled=env_enabled,
                timeout=env_timeout,
            )

        return None

    # Create server configurations with database priority
    sabnzbd_config = get_service_config(
        "sabnzbd",
        settings.sabnzbd_url,
        settings.sabnzbd_api_key,
        settings.sabnzbd_enabled,
        settings.sabnzbd_timeout,
    )

    sonarr_config = get_service_config(
        "sonarr",
        settings.sonarr_url,
        settings.sonarr_api_key,
        settings.sonarr_enabled,
        settings.sonarr_timeout,
    )

    radarr_config = get_service_config(
        "radarr",
        settings.radarr_url,
        settings.radarr_api_key,
        settings.radarr_enabled,
        settings.radarr_timeout,
    )

    plex_config = get_service_config(
        "plex",
        settings.plex_url,
        settings.plex_token,
        settings.plex_enabled,
        settings.plex_timeout,
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
        # Fetch database settings (priority over env vars)
        db_settings = await get_db_service_settings()
        config = get_orchestrator_config(db_settings=db_settings)
        _orchestrator = MCPOrchestrator(config)

        # Log which services are being configured
        services_to_connect = []
        if config.sabnzbd:
            services_to_connect.append("sabnzbd")
        if config.sonarr:
            services_to_connect.append("sonarr")
        if config.radarr:
            services_to_connect.append("radarr")
        if config.plex:
            services_to_connect.append("plex")

        if services_to_connect:
            logger.info(f"Configuring MCP servers: {', '.join(services_to_connect)}")

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
