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
Configuration Audit API endpoints.

This module provides REST API endpoints for configuration auditing, recommendations,
and applying configuration changes following TDD principles.
"""

import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models_config import (
    ApplyConfigRequest,
    ApplyConfigResponse,
    AuditHistoryResponse,
    ConfigAuditRequest,
    ConfigAuditResponse,
    DetailedRecommendation,
    RecommendationsListResponse,
)
from ..services.config_manager import ConfigurationManager, get_config_manager_instance

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_config_manager() -> AsyncGenerator[ConfigurationManager, None]:
    """
    Dependency to get ConfigurationManager instance.

    Yields:
        ConfigurationManager instance
    """
    yield get_config_manager_instance()


# ============================================================================
# Configuration Audit Endpoints
# ============================================================================


@router.post("/audit", response_model=ConfigAuditResponse, status_code=status.HTTP_200_OK)
async def trigger_config_audit(
    request: ConfigAuditRequest,
    config_manager: ConfigurationManager = Depends(get_config_manager),
) -> ConfigAuditResponse:
    """
    Trigger configuration audit for one or more services.

    This endpoint analyzes the current configuration of specified services
    and generates recommendations for improvements based on best practices.

    Args:
        request: Configuration audit request
        config_manager: Configuration manager dependency

    Returns:
        ConfigAuditResponse: Audit results with recommendations

    Raises:
        HTTPException: If validation fails or audit encounters an error

    Example:
        ```
        POST /api/v1/config/audit
        {
            "services": ["sabnzbd", "sonarr"],
            "include_web_search": true
        }
        ```

    Rate Limit:
        10 audits per hour per service
    """
    try:
        # Validate that at least one service is specified
        if not request.services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one service must be specified",
            )

        # Perform the audit
        result = await config_manager.audit_configuration(  # noqa: F841
            services=request.services,
            include_web_search=request.include_web_search,
        )

        return ConfigAuditResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error during configuration audit: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the configuration audit",
        )


@router.get(
    "/recommendations",
    response_model=RecommendationsListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_recommendations(
    service: Optional[str] = Query(None, description="Filter by service name"),
    priority: Optional[str] = Query(None, description="Filter by priority (high, medium, low)"),
    category: Optional[str] = Query(
        None, description="Filter by category (performance, security, best_practices)"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    config_manager: ConfigurationManager = Depends(get_config_manager),
) -> RecommendationsListResponse:
    """
    List all recommendations from latest audit with optional filtering.

    This endpoint retrieves configuration recommendations with support for
    filtering by service, priority, and category, as well as pagination.

    Args:
        service: Optional service name filter
        priority: Optional priority filter
        category: Optional category filter
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
        config_manager: Configuration manager dependency

    Returns:
        RecommendationsListResponse: List of recommendations with pagination

    Example:
        ```
        GET /api/v1/config/recommendations?service=sabnzbd&priority=high&page=1&page_size=10
        ```

    Rate Limit:
        50 recommendations queries per hour
    """
    try:
        result = await config_manager.get_recommendations(  # noqa: F841
            service=service,
            priority=priority,
            category=category,
            page=page,
            page_size=page_size,
        )

        return RecommendationsListResponse(**result)

    except Exception as e:
        logger.error(f"Error retrieving recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving recommendations",
        )


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=DetailedRecommendation,
    status_code=status.HTTP_200_OK,
)
async def get_recommendation_detail(
    recommendation_id: int,
    config_manager: ConfigurationManager = Depends(get_config_manager),
) -> DetailedRecommendation:
    """
    Get detailed information about a specific recommendation.

    This endpoint retrieves comprehensive details about a recommendation,
    including explanation and reference documentation.

    Args:
        recommendation_id: Recommendation ID
        config_manager: Configuration manager dependency

    Returns:
        DetailedRecommendation: Detailed recommendation information

    Raises:
        HTTPException: If recommendation not found

    Example:
        ```
        GET /api/v1/config/recommendations/1
        ```

    Rate Limit:
        50 recommendations queries per hour
    """
    try:
        result = await config_manager.get_recommendation_by_id(recommendation_id)  # noqa: F841

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation with ID {recommendation_id} not found",
            )

        return DetailedRecommendation(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recommendation {recommendation_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the recommendation",
        )


@router.post("/apply", response_model=ApplyConfigResponse, status_code=status.HTTP_200_OK)
async def apply_config_changes(
    request: ApplyConfigRequest,
    config_manager: ConfigurationManager = Depends(get_config_manager),
) -> ApplyConfigResponse:
    """
    Apply recommended configuration changes.

    This endpoint applies one or more configuration recommendations to their
    respective services. Supports dry-run mode for testing.

    Args:
        request: Apply configuration request
        config_manager: Configuration manager dependency

    Returns:
        ApplyConfigResponse: Results for each recommendation

    Raises:
        HTTPException: If validation fails

    Example:
        ```
        POST /api/v1/config/apply
        {
            "recommendation_ids": [1, 2, 3],
            "dry_run": false
        }
        ```

    Rate Limit:
        20 apply operations per hour
    """
    try:
        # Validate that at least one recommendation is specified
        if not request.recommendation_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one recommendation ID must be specified",
            )

        # Apply the recommendations
        result = await config_manager.apply_recommendations(  # noqa: F841
            recommendation_ids=request.recommendation_ids,
            dry_run=request.dry_run,
        )

        return ApplyConfigResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error applying configuration changes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while applying configuration changes",
        )


@router.get(
    "/audit/history",
    response_model=AuditHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_audit_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    config_manager: ConfigurationManager = Depends(get_config_manager),
) -> AuditHistoryResponse:
    """
    View audit history with timestamps and pagination.

    This endpoint retrieves the history of all configuration audits,
    showing when audits were performed and their results.

    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
        config_manager: Configuration manager dependency

    Returns:
        AuditHistoryResponse: List of audit history items with pagination

    Example:
        ```
        GET /api/v1/config/audit/history?page=1&page_size=10
        ```

    Rate Limit:
        50 recommendations queries per hour
    """
    try:
        result = await config_manager.get_audit_history(  # noqa: F841
            page=page,
            page_size=page_size,
        )

        return AuditHistoryResponse(**result)

    except Exception as e:
        logger.error(f"Error retrieving audit history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving audit history",
        )
