"""
Health check endpoints.

This module provides health check endpoints for monitoring the overall
system health and individual service health.
"""

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator
from ..models import HealthCheckResponse, ServiceHealth

router = APIRouter()


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
    orch = orchestrator

    services = {}
    all_healthy = True

    # Get list of connected servers
    connected_servers = list(orch._clients.keys())

    if not connected_servers:
        # No servers connected - system is unhealthy
        return HealthCheckResponse(
            status="unhealthy",
            services={},
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    # Check each server
    for server_name in connected_servers:
        start_time = time.time()
        is_healthy = await orch.health_check(server_name)
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Get circuit breaker state
        cb_state = orch.get_circuit_breaker_state(server_name)

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


@router.get("/health/{service}", response_model=ServiceHealth, tags=["health"])
async def service_health(
    service: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> ServiceHealth:
    """
    Individual service health check.

    Check the health of a specific MCP service.

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
    orch = orchestrator

    # Validate service name
    valid_services = ["sabnzbd", "sonarr", "radarr", "plex"]
    if service not in valid_services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service name. Must be one of: {', '.join(valid_services)}",
        )

    # Check if service is connected
    is_connected = await orch.is_connected(service)
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service}' is not connected",
        )

    # Perform health check
    start_time = time.time()
    is_healthy = await orch.health_check(service)
    latency = (time.time() - start_time) * 1000  # Convert to milliseconds

    # Get circuit breaker state
    cb_state = orch.get_circuit_breaker_state(service)

    return ServiceHealth(
        healthy=is_healthy,
        latency_ms=round(latency, 2) if is_healthy else None,
        error=None if is_healthy else "Service health check failed",
        last_check=datetime.utcnow().isoformat() + "Z",
        circuit_breaker_state=cb_state.get("state", "unknown"),
    )


@router.get("/health/circuit-breaker/{service}", tags=["health"])
async def circuit_breaker_status(
    service: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> dict:
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
    orch = orchestrator

    # Validate service name
    valid_services = ["sabnzbd", "sonarr", "radarr", "plex"]
    if service not in valid_services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service name. Must be one of: {', '.join(valid_services)}",
        )

    return orch.get_circuit_breaker_state(service)
