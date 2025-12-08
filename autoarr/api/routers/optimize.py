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
Optimization Assessment API Endpoints.

This module provides API endpoints for assessing service configurations
and providing optimization recommendations.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from autoarr.api.services.tool_providers import (
    PlexToolProvider,
    RadarrToolProvider,
    SABnzbdToolProvider,
    SonarrToolProvider,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class OptimizationCheck(BaseModel):
    """A single optimization check result."""

    id: str = Field(..., description="Unique check identifier")
    category: str = Field(..., description="Check category (performance, security, etc.)")
    status: str = Field(..., description="Check status: critical, warning, recommendation, good")
    title: str = Field(..., description="Short title for the check")
    description: str = Field(..., description="Detailed description of the check")
    recommendation: Optional[str] = Field(None, description="Recommended action to fix")
    current_value: Optional[str] = Field(None, description="Current configuration value")
    optimal_value: Optional[str] = Field(None, description="Optimal/recommended value")
    auto_fix: bool = Field(False, description="Whether this can be auto-fixed")
    fix_action: Optional[str] = Field(None, description="Action to call for auto-fix")
    fix_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for auto-fix")
    min_version: Optional[str] = Field(None, description="Minimum version for this check")


class OptimizationSummary(BaseModel):
    """Summary of optimization check results."""

    total_checks: int = Field(..., description="Total number of checks performed")
    critical: int = Field(0, description="Number of critical issues")
    warnings: int = Field(0, description="Number of warnings")
    recommendations: int = Field(0, description="Number of recommendations")
    good: int = Field(0, description="Number of checks passed")


class ServiceOptimizationResult(BaseModel):
    """Optimization result for a single service."""

    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    overall_status: str = Field(
        ..., description="Overall status: excellent, good, warning, critical"
    )
    overall_score: int = Field(..., description="Overall health score (0-100)")
    summary: OptimizationSummary = Field(..., description="Summary of checks")
    checks: List[OptimizationCheck] = Field(default_factory=list, description="Individual checks")


class AllServicesOptimizationResult(BaseModel):
    """Optimization results for all services."""

    services: List[ServiceOptimizationResult] = Field(
        default_factory=list, description="Results per service"
    )
    overall_score: int = Field(..., description="Combined score across all services")
    overall_status: str = Field(..., description="Combined status")


class ApplyFixRequest(BaseModel):
    """Request to apply an auto-fix."""

    service: str = Field(..., description="Service name")
    check_id: str = Field(..., description="Check ID to fix")
    fix_action: str = Field(..., description="Fix action to apply")
    fix_params: Optional[Dict[str, Any]] = Field(None, description="Fix parameters")


class ApplyFixResponse(BaseModel):
    """Response from applying a fix."""

    success: bool = Field(..., description="Whether fix was applied successfully")
    message: str = Field(..., description="Result message")
    check_id: str = Field(..., description="Check ID that was fixed")


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/assess",
    response_model=AllServicesOptimizationResult,
    summary="Assess all services",
    description="Run optimization assessment on all connected services",
)
async def assess_all_services() -> AllServicesOptimizationResult:
    """
    Assess optimization for all connected services.

    Returns health check results for each service including:
    - SABnzbd configuration optimization
    - (Future) Sonarr configuration
    - (Future) Radarr configuration
    - (Future) Plex configuration
    """
    services: List[ServiceOptimizationResult] = []

    # Define all service providers and their assessment tools
    service_configs = [
        ("sabnzbd", SABnzbdToolProvider, "sabnzbd_assess_optimization"),
        ("sonarr", SonarrToolProvider, "sonarr_assess_optimization"),
        ("radarr", RadarrToolProvider, "radarr_assess_optimization"),
        ("plex", PlexToolProvider, "plex_assess_optimization"),
    ]

    # Assess each service
    for service_name, provider_class, assessment_tool in service_configs:
        try:
            provider = provider_class()
            if await provider.is_available():
                result = await provider.execute(assessment_tool, {})
                if result.success and result.data:
                    data = result.data
                    services.append(
                        ServiceOptimizationResult(
                            service=data.get("service", service_name),
                            version=data.get("version"),
                            overall_status=data.get("overall_status", "unknown"),
                            overall_score=data.get("overall_score", 0),
                            summary=OptimizationSummary(**data.get("summary", {})),
                            checks=[OptimizationCheck(**c) for c in data.get("checks", [])],
                        )
                    )
                else:
                    # Assessment failed but service is connected
                    services.append(
                        ServiceOptimizationResult(
                            service=service_name,
                            version=None,
                            overall_status="error",
                            overall_score=0,
                            summary=OptimizationSummary(total_checks=0),
                            checks=[
                                OptimizationCheck(
                                    id="assessment_error",
                                    category="system",
                                    status="warning",
                                    title="Assessment Error",
                                    description=result.error or "Unknown error during assessment",
                                    auto_fix=False,
                                )
                            ],
                        )
                    )
            else:
                # Service not connected - add placeholder
                services.append(
                    ServiceOptimizationResult(
                        service=service_name,
                        version=None,
                        overall_status="not_connected",
                        overall_score=0,
                        summary=OptimizationSummary(total_checks=0),
                        checks=[],
                    )
                )
        except Exception as e:
            logger.error(f"Failed to assess {service_name}: {e}")
            services.append(
                ServiceOptimizationResult(
                    service=service_name,
                    version=None,
                    overall_status="error",
                    overall_score=0,
                    summary=OptimizationSummary(total_checks=0),
                    checks=[
                        OptimizationCheck(
                            id="assessment_error",
                            category="system",
                            status="critical",
                            title="Assessment Failed",
                            description=str(e),
                            auto_fix=False,
                        )
                    ],
                )
            )

    # Calculate overall score
    connected_services = [s for s in services if s.overall_status not in ["not_connected", "error"]]
    if connected_services:
        overall_score = round(
            sum(s.overall_score for s in connected_services) / len(connected_services)
        )
    else:
        overall_score = 0

    # Determine overall status
    statuses = [
        s.overall_status for s in services if s.overall_status not in ["not_connected", "error"]
    ]
    if "critical" in statuses:
        overall_status = "critical"
    elif "warning" in statuses:
        overall_status = "warning"
    elif statuses:
        overall_status = "good"
    else:
        overall_status = "not_connected"

    return AllServicesOptimizationResult(
        services=services,
        overall_score=overall_score,
        overall_status=overall_status,
    )


@router.get(
    "/assess/{service}",
    response_model=ServiceOptimizationResult,
    summary="Assess single service",
    description="Run optimization assessment on a specific service",
)
async def assess_service(service: str) -> ServiceOptimizationResult:
    """
    Assess optimization for a specific service.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, plex)
    """
    # Map service names to providers and assessment tools
    service_map = {
        "sabnzbd": (SABnzbdToolProvider, "sabnzbd_assess_optimization"),
        "sonarr": (SonarrToolProvider, "sonarr_assess_optimization"),
        "radarr": (RadarrToolProvider, "radarr_assess_optimization"),
        "plex": (PlexToolProvider, "plex_assess_optimization"),
    }

    service_lower = service.lower()
    if service_lower not in service_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not supported. Available: {', '.join(service_map.keys())}",
        )

    provider_class, assessment_tool = service_map[service_lower]

    try:
        provider = provider_class()
        if not await provider.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{service.capitalize()} is not connected. Please configure it in Settings.",
            )

        result = await provider.execute(assessment_tool, {})
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Assessment failed",
            )

        data = result.data
        return ServiceOptimizationResult(
            service=data.get("service", service_lower),
            version=data.get("version"),
            overall_status=data.get("overall_status", "unknown"),
            overall_score=data.get("overall_score", 0),
            summary=OptimizationSummary(**data.get("summary", {})),
            checks=[OptimizationCheck(**c) for c in data.get("checks", [])],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{service} assessment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/fix",
    response_model=ApplyFixResponse,
    summary="Apply auto-fix",
    description="Apply an automatic fix for an optimization issue",
)
async def apply_fix(request: ApplyFixRequest) -> ApplyFixResponse:
    """
    Apply an automatic fix for an optimization issue.

    This endpoint executes the fix_action specified in the optimization check.
    """
    # Map service names to providers
    service_map = {
        "sabnzbd": SABnzbdToolProvider,
        "sonarr": SonarrToolProvider,
        "radarr": RadarrToolProvider,
        "plex": PlexToolProvider,
    }

    service_lower = request.service.lower()
    if service_lower not in service_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{request.service}' not supported. "
            f"Available: {', '.join(service_map.keys())}",
        )

    provider_class = service_map[service_lower]

    try:
        provider = provider_class()
        if not await provider.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{request.service.capitalize()} is not connected",
            )

        # Execute the fix action
        result = await provider.execute(
            request.fix_action,
            request.fix_params or {},
        )

        if result.success:
            return ApplyFixResponse(
                success=True,
                message=f"Successfully applied fix: {request.fix_action}",
                check_id=request.check_id,
            )
        else:
            return ApplyFixResponse(
                success=False,
                message=result.error or "Fix failed",
                check_id=request.check_id,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply fix: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
