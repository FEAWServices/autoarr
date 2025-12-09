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
Health check endpoints.

This module provides health check endpoints for monitoring the overall
system health and individual service health.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator
from ..models import HealthCheckResponse, ServiceHealth

router = APIRouter()
logger = logging.getLogger(__name__)

# Global warmup state
_warmup_complete = False
_warmup_timestamp: str | None = None

# LLM health cache (avoid hitting OpenRouter API on every request)
_llm_health_cache: Dict[str, Any] | None = None
_llm_health_cache_time: float = 0
_LLM_HEALTH_CACHE_TTL = 60  # Cache for 60 seconds


@router.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> HealthCheckResponse:
    """
    Overall system health check.

    This endpoint checks the health of all connected MCP servers and returns
    an overall system status.

    Returns:
        HealthCheckResponse: Overall system health status

    Example:
        ```
        GET /health
        {
            "status": "healthy",
            "services": {
                "sabnzbd": {
                    "healthy": true,
                    "latency_ms": 45.2,
                    "error": null,
                    "last_check": "2025-01-15T10:30:00Z",
                    "circuit_breaker_state": "closed"
                }
            },
            "timestamp": "2025-01-15T10:30:00Z"
        }
        ```
    """
    services = {}
    all_healthy = True

    # Get list of connected servers
    connected_servers = orchestrator.get_connected_servers()

    if not connected_servers:
        # No servers connected yet - system is healthy but awaiting configuration
        # This is the expected state on fresh install
        return HealthCheckResponse(
            status="healthy",
            services={},
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    # Check each server
    for server_name in connected_servers:
        start_time = time.time()
        is_healthy = await orchestrator.health_check(server_name)
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Get circuit breaker state
        cb_state = orchestrator.get_circuit_breaker_state(server_name)

        services[server_name] = ServiceHealth(
            healthy=is_healthy,
            latency_ms=round(latency, 2) if is_healthy else None,
            error=None if is_healthy else "Service unhealthy",
            last_check=datetime.utcnow().isoformat() + "Z",
            circuit_breaker_state=cb_state.get("state", "unknown"),
        )

        if not is_healthy:
            all_healthy = False

    # Determine overall status
    if all_healthy:
        overall_status = "healthy"
    elif any(s.healthy for s in services.values()):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthCheckResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/health/database", tags=["health"])
async def database_health() -> Dict[str, Any]:
    """
    Database health check.

    Check if the database is configured and accessible.

    Returns:
        dict: Database health status

    Example:
        ```
        GET /health/database
        {
            "status": "healthy",
            "configured": true,
            "type": "sqlite",
            "message": "Database connection successful"
        }
        ```
    """
    from ..config import get_settings
    from ..database import get_database

    settings = get_settings()

    if not settings.database_url:
        return {
            "status": "unconfigured",
            "configured": False,
            "type": None,
            "message": "DATABASE_URL not configured. Settings will not persist.",
        }

    try:
        db = get_database()
        # Try to get a session to verify connection
        async with db.session() as session:
            # Execute a simple query to verify connectivity
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))

        # Determine database type from URL
        db_type = "unknown"
        if "sqlite" in settings.database_url:
            db_type = "sqlite"
        elif "postgresql" in settings.database_url:
            db_type = "postgresql"
        elif "mysql" in settings.database_url:
            db_type = "mysql"

        return {
            "status": "healthy",
            "configured": True,
            "type": db_type,
            "message": "Database connection successful",
        }
    except RuntimeError as e:
        return {
            "status": "error",
            "configured": True,
            "type": None,
            "message": f"Database not initialized: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "configured": True,
            "type": None,
            "message": f"Database connection failed: {str(e)}",
        }


@router.get("/health/circuit-breaker/{service}", tags=["health"])
async def circuit_breaker_status(
    service: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get circuit breaker status for a service.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, or plex)

    Returns:
        dict: Circuit breaker state information

    Example:
        ```
        GET /health/circuit-breaker/sabnzbd
        {
            "state": "closed",
            "failure_count": 0,
            "success_count": 0,
            "threshold": 5,
            "timeout": 60.0
        }
        ```
    """
    # Validate service name
    valid_services = ["sabnzbd", "sonarr", "radarr", "plex"]
    if service not in valid_services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service name. Must be one of: {', '.join(valid_services)}",
        )

    result: Dict[str, Any] = orchestrator.get_circuit_breaker_state(service)
    return result


# ============================================================================
# Warmup Endpoints
# ============================================================================


async def perform_warmup() -> Dict[str, Any]:
    """
    Perform application warmup to preload caches and initialize resources.

    This is called automatically on startup and can be triggered manually.

    Returns:
        dict: Warmup results with timing information
    """
    global _warmup_complete, _warmup_timestamp

    start_time = time.time()
    results: Dict[str, Any] = {
        "tasks": {},
        "errors": [],
    }

    # Task 1: Warm up database connection pool
    try:
        task_start = time.time()
        from ..database import get_database

        db = get_database()
        async with db.session() as session:
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
        results["tasks"]["database"] = {
            "status": "ok",
            "duration_ms": round((time.time() - task_start) * 1000, 2),
        }
        logger.info("Warmup: Database connection pool initialized")
    except Exception as e:
        results["tasks"]["database"] = {"status": "error", "error": str(e)}
        results["errors"].append(f"database: {e}")
        logger.warning(f"Warmup: Database warmup failed: {e}")

    # Task 2: Preload onboarding state (frequently accessed on startup)
    try:
        task_start = time.time()
        from ..database import OnboardingStateRepository, get_database

        db = get_database()
        repo = OnboardingStateRepository(db)
        await repo.get_or_create_state()
        results["tasks"]["onboarding_state"] = {
            "status": "ok",
            "duration_ms": round((time.time() - task_start) * 1000, 2),
        }
        logger.info("Warmup: Onboarding state loaded")
    except Exception as e:
        results["tasks"]["onboarding_state"] = {"status": "skipped", "error": str(e)}
        logger.debug(f"Warmup: Onboarding state skipped: {e}")

    # Task 3: Preload LLM settings (if configured)
    try:
        task_start = time.time()
        from ..database import LLMSettingsRepository, get_database

        db = get_database()
        llm_repo = LLMSettingsRepository(db)
        await llm_repo.get_settings()
        results["tasks"]["llm_settings"] = {
            "status": "ok",
            "duration_ms": round((time.time() - task_start) * 1000, 2),
        }
        logger.info("Warmup: LLM settings loaded")
    except Exception as e:
        results["tasks"]["llm_settings"] = {"status": "skipped", "error": str(e)}
        logger.debug(f"Warmup: LLM settings skipped: {e}")

    # Task 4: Initialize Python module imports (reduces first-request latency)
    try:
        task_start = time.time()
        # Import heavy modules that are commonly used
        import json  # noqa: F401

        from pydantic import BaseModel  # noqa: F401

        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider  # noqa: F401
        from autoarr.shared.llm.provider_factory import LLMProviderFactory  # noqa: F401

        # Initialize provider factory
        LLMProviderFactory.initialize()

        results["tasks"]["module_imports"] = {
            "status": "ok",
            "duration_ms": round((time.time() - task_start) * 1000, 2),
        }
        logger.info("Warmup: Module imports completed")
    except Exception as e:
        results["tasks"]["module_imports"] = {"status": "error", "error": str(e)}
        results["errors"].append(f"module_imports: {e}")

    # Task 5: Preload service settings
    try:
        task_start = time.time()
        from ..database import SettingsRepository, get_database

        db = get_database()
        settings_repo = SettingsRepository(db)
        await settings_repo.get_all_service_settings()
        results["tasks"]["service_settings"] = {
            "status": "ok",
            "duration_ms": round((time.time() - task_start) * 1000, 2),
        }
        logger.info("Warmup: Service settings loaded")
    except Exception as e:
        results["tasks"]["service_settings"] = {"status": "skipped", "error": str(e)}
        logger.debug(f"Warmup: Service settings skipped: {e}")

    # Calculate totals
    total_duration = time.time() - start_time
    results["total_duration_ms"] = round(total_duration * 1000, 2)
    results["success"] = len(results["errors"]) == 0
    results["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Mark warmup as complete
    _warmup_complete = True
    _warmup_timestamp = results["timestamp"]

    logger.info(f"Warmup completed in {results['total_duration_ms']}ms")

    return results


@router.get("/health/ready", tags=["health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.

    Returns 200 only when the application is fully warmed up and ready
    to serve requests. Use this for load balancer health checks.

    Returns:
        dict: Readiness status

    Example:
        ```
        GET /health/ready
        {
            "ready": true,
            "warmup_complete": true,
            "warmup_timestamp": "2025-01-15T10:30:00Z"
        }
        ```
    """
    if not _warmup_complete:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application is still warming up",
        )

    return {
        "ready": True,
        "warmup_complete": _warmup_complete,
        "warmup_timestamp": _warmup_timestamp,
    }


@router.get("/health/live", tags=["health"])
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.

    Returns 200 if the application is running (even if not fully ready).
    Use this to detect if the application is stuck and needs restart.

    Returns:
        dict: Liveness status

    Example:
        ```
        GET /health/live
        {
            "alive": true,
            "timestamp": "2025-01-15T10:30:00Z"
        }
        ```
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/health/warmup", tags=["health"])
async def trigger_warmup() -> Dict[str, Any]:
    """
    Manually trigger application warmup.

    This can be called to refresh caches or after configuration changes.

    Returns:
        dict: Warmup results

    Example:
        ```
        POST /health/warmup
        {
            "success": true,
            "total_duration_ms": 45.2,
            "tasks": {
                "database": {"status": "ok", "duration_ms": 12.3},
                "onboarding_state": {"status": "ok", "duration_ms": 8.1},
                ...
            }
        }
        ```
    """
    return await perform_warmup()


@router.get("/health/llm", tags=["health"])
async def llm_health() -> Dict[str, Any]:
    """
    LLM/AI service health check.

    Check if the LLM provider (OpenRouter) is configured and accessible.
    Results are cached for 60 seconds to avoid excessive API calls.

    Returns:
        dict: LLM health status

    Example:
        ```
        GET /health/llm
        {
            "healthy": true,
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "latency_ms": 234.5,
            "error": null,
            "cached": false
        }
        ```
    """
    global _llm_health_cache, _llm_health_cache_time

    # Return cached result if still valid
    if _llm_health_cache and (time.time() - _llm_health_cache_time) < _LLM_HEALTH_CACHE_TTL:
        return {**_llm_health_cache, "cached": True}

    from ..database import LLMSettingsRepository, get_database

    result: Dict[str, Any]

    try:
        db = get_database()
        llm_repo = LLMSettingsRepository(db)
        settings = await llm_repo.get_settings()

        if not settings or not settings.api_key:
            result = {
                "healthy": False,
                "provider": None,
                "model": None,
                "latency_ms": None,
                "error": "LLM not configured",
            }
            _llm_health_cache = result
            _llm_health_cache_time = time.time()
            return {**result, "cached": False}

        # Test connection to OpenRouter
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        start_time = time.time()
        provider = OpenRouterProvider({"api_key": settings.api_key})
        is_available = await provider.is_available()
        latency = (time.time() - start_time) * 1000

        if is_available:
            result = {
                "healthy": True,
                "provider": settings.provider or "openrouter",
                "model": settings.selected_model,
                "latency_ms": round(latency, 2),
                "error": None,
            }
        else:
            result = {
                "healthy": False,
                "provider": settings.provider or "openrouter",
                "model": settings.selected_model,
                "latency_ms": round(latency, 2),
                "error": "Failed to connect to OpenRouter",
            }

        _llm_health_cache = result
        _llm_health_cache_time = time.time()
        return {**result, "cached": False}

    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")
        result = {
            "healthy": False,
            "provider": None,
            "model": None,
            "latency_ms": None,
            "error": str(e),
        }
        _llm_health_cache = result
        _llm_health_cache_time = time.time()
        return {**result, "cached": False}


async def _get_service_config_from_db(service: str) -> tuple[str | None, str | None, bool]:
    """Get service configuration from database."""
    from ..database import SettingsRepository, get_database

    try:
        db = get_database()
        repo = SettingsRepository(db)
        db_settings = await repo.get_service_settings(service)
        if db_settings and db_settings.enabled and db_settings.api_key_or_token:
            return db_settings.url, db_settings.api_key_or_token, True
    except Exception:
        pass
    return None, None, False


def _get_service_config_from_env(service: str) -> tuple[str | None, str | None, bool]:
    """Get service configuration from environment variables."""
    from ..config import get_settings

    settings = get_settings()
    config_map = {
        "sabnzbd": (
            settings.sabnzbd_url,
            settings.sabnzbd_api_key,
            settings.sabnzbd_enabled and bool(settings.sabnzbd_api_key),
        ),
        "sonarr": (
            settings.sonarr_url,
            settings.sonarr_api_key,
            settings.sonarr_enabled and bool(settings.sonarr_api_key),
        ),
        "radarr": (
            settings.radarr_url,
            settings.radarr_api_key,
            settings.radarr_enabled and bool(settings.radarr_api_key),
        ),
        "plex": (
            settings.plex_url,
            settings.plex_token,
            settings.plex_enabled and bool(settings.plex_token),
        ),
    }
    return config_map.get(service, (None, None, False))


async def _check_service_health(
    service: str, service_url: str, service_api_key: str
) -> tuple[bool, int]:
    """Perform HTTP health check for a service. Returns (is_healthy, status_code)."""
    import httpx

    async with httpx.AsyncClient(timeout=10.0) as client:
        base_url = service_url.rstrip("/")

        if service == "sabnzbd":
            url = f"{base_url}/api?mode=version&apikey={service_api_key}&output=json"
            response = await client.get(url)
        elif service in ["sonarr", "radarr"]:
            url = f"{base_url}/api/v3/system/status"
            response = await client.get(url, headers={"X-Api-Key": service_api_key})
        elif service == "plex":
            url = f"{base_url}/identity"
            response = await client.get(url, headers={"X-Plex-Token": service_api_key})
        else:
            return False, 0

        return response.status_code == 200, response.status_code


# NOTE: This dynamic route MUST come AFTER all specific /health/* routes
# to prevent FastAPI from matching "ready", "live", "database", etc. as service names
@router.get("/health/{service}", response_model=ServiceHealth, tags=["health"])
async def service_health(
    service: str,
) -> ServiceHealth:
    """
    Individual service health check.

    Check the health of a specific MCP service using direct HTTP calls.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, or plex)

    Returns:
        ServiceHealth: Service health status

    Raises:
        HTTPException: If service name is invalid or service is not connected

    Example:
        ```
        GET /health/sabnzbd
        {
            "healthy": true,
            "latency_ms": 45.2,
            "error": null,
            "last_check": "2025-01-15T10:30:00Z",
            "circuit_breaker_state": "closed"
        }
        ```
    """
    valid_services = ["sabnzbd", "sonarr", "radarr", "plex"]
    if service not in valid_services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service name. Must be one of: {', '.join(valid_services)}",
        )

    # Try database first, then fall back to environment
    service_url, service_api_key, service_enabled = await _get_service_config_from_db(service)
    if not service_enabled:
        service_url, service_api_key, service_enabled = _get_service_config_from_env(service)

    if not service_enabled or not service_api_key:
        return ServiceHealth(
            healthy=False,
            latency_ms=None,
            error="Service not configured",
            last_check=datetime.utcnow().isoformat() + "Z",
            circuit_breaker_state="unconfigured",
        )

    assert service_url is not None
    assert service_api_key is not None

    start_time = time.time()
    try:
        is_healthy, _ = await _check_service_health(service, service_url, service_api_key)
        latency = (time.time() - start_time) * 1000

        return ServiceHealth(
            healthy=is_healthy,
            latency_ms=round(latency, 2) if is_healthy else None,
            error=None if is_healthy else "Service health check failed",
            last_check=datetime.utcnow().isoformat() + "Z",
            circuit_breaker_state="closed" if is_healthy else "open",
        )
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return ServiceHealth(
            healthy=False,
            latency_ms=round(latency, 2),
            error=str(e),
            last_check=datetime.utcnow().isoformat() + "Z",
            circuit_breaker_state="open",
        )
