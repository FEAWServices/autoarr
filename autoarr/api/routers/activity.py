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
Activity log API endpoints.

This module provides endpoints for retrieving and managing activity logs,
including paginated listing, filtering, statistics, and cleanup.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from autoarr.api.database import ActivityLogRepository, get_database
from autoarr.api.services.activity_log import (
    ActivityFilter,
    ActivityLog,
    ActivityLogService,
    ActivitySeverity,
    ActivityStatistics,
    ActivityType,
    PaginatedResult,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for API
# ============================================================================


class ActivityLogResponse(BaseModel):
    """Activity log response model."""

    id: int
    service: str
    activity_type: str
    severity: str
    message: str
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    created_at: datetime
    user_id: Optional[str] = None

    @classmethod
    def from_activity_log(cls, activity: ActivityLog) -> "ActivityLogResponse":
        """Create response from ActivityLog instance."""
        return cls(
            id=activity.id,
            service=activity.service,
            activity_type=activity.activity_type.value,
            severity=activity.severity.value,
            message=activity.message,
            correlation_id=activity.correlation_id,
            metadata=activity.metadata,
            timestamp=activity.timestamp,
            created_at=activity.created_at,
            user_id=activity.user_id,
        )


class PaginatedActivityResponse(BaseModel):
    """Paginated activity list response."""

    items: List[ActivityLogResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ActivityStatisticsResponse(BaseModel):
    """Activity statistics response."""

    total_count: int
    by_type: Dict[str, int]
    by_service: Dict[str, int]
    by_severity: Dict[str, int]


class ActivityTrendResponse(BaseModel):
    """Activity trend response."""

    trend: Dict[str, int]  # Date string -> count


class CleanupResponse(BaseModel):
    """Cleanup operation response."""

    deleted_count: int
    message: str


# ============================================================================
# Dependencies
# ============================================================================


async def get_activity_service() -> ActivityLogService:
    """Get ActivityLogService instance."""
    db = get_database()
    repository = ActivityLogRepository(db)
    return ActivityLogService(repository)


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "",
    response_model=PaginatedActivityResponse,
    summary="Get paginated activity logs",
    description="Retrieve activity logs with pagination and optional filtering.",
)
async def get_activities(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    search: Optional[str] = Query(None, description="Search in message text"),
    order_by: str = Query("timestamp", description="Field to order by"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Order direction"),
    activity_service: ActivityLogService = Depends(get_activity_service),
) -> PaginatedActivityResponse:
    """
    Get paginated activity logs with optional filters.

    Returns a paginated list of activity logs that can be filtered by
    service, type, severity, date range, and correlation ID.
    """
    try:
        # Build filter
        activity_filter = ActivityFilter(
            service=service,
            activity_type=ActivityType(activity_type) if activity_type else None,
            severity=ActivitySeverity(severity) if severity else None,
            start_date=start_date,
            end_date=end_date,
            correlation_id=correlation_id,
            search_query=search,
        )

        # Get paginated results
        result: PaginatedResult = await activity_service.get_activities_paginated(
            page=page,
            page_size=page_size,
            filter=activity_filter,
            order_by=order_by,
            order=order,
        )

        return PaginatedActivityResponse(
            items=[ActivityLogResponse.from_activity_log(item) for item in result.items],
            page=result.page,
            page_size=result.page_size,
            total_items=result.total_items,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_previous=result.has_previous,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter value: {e}",
        )
    except Exception as e:
        logger.error(f"Failed to get activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity logs",
        )


@router.get(
    "/{activity_id}",
    response_model=ActivityLogResponse,
    summary="Get activity by ID",
    description="Retrieve a single activity log entry by its ID.",
)
async def get_activity_by_id(
    activity_id: int,
    activity_service: ActivityLogService = Depends(get_activity_service),
) -> ActivityLogResponse:
    """Get a specific activity log entry by ID."""
    activity = await activity_service.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    return ActivityLogResponse.from_activity_log(activity)


@router.get(
    "/workflow/{correlation_id}",
    response_model=List[ActivityLogResponse],
    summary="Get workflow activities",
    description="Get all activities for a workflow by correlation ID.",
)
async def get_workflow_activities(
    correlation_id: str,
    activity_service: ActivityLogService = Depends(get_activity_service),
) -> List[ActivityLogResponse]:
    """
    Get all activities for a specific workflow.

    Activities are returned in chronological order to show workflow progression.
    """
    activities = await activity_service.get_workflow_by_correlation_id(correlation_id)
    return [ActivityLogResponse.from_activity_log(a) for a in activities]


@router.get(
    "/stats",
    response_model=ActivityStatisticsResponse,
    summary="Get activity statistics",
    description="Get aggregated activity statistics.",
)
async def get_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    activity_service: ActivityLogService = Depends(get_activity_service),
) -> ActivityStatisticsResponse:
    """Get activity statistics with optional date range filter."""
    try:
        stats: ActivityStatistics = await activity_service.get_statistics(
            start_date=start_date,
            end_date=end_date,
        )
        return ActivityStatisticsResponse(
            total_count=stats.total_count,
            by_type={k.value: v for k, v in stats.by_type.items()},
            by_service=stats.by_service,
            by_severity={k.value: v for k, v in stats.by_severity.items()},
        )
    except Exception as e:
        logger.error(f"Failed to get activity statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity statistics",
        )


@router.get(
    "/trend",
    response_model=ActivityTrendResponse,
    summary="Get activity trend",
    description="Get activity counts over time.",
)
async def get_activity_trend(
    days: int = Query(7, ge=1, le=90, description="Number of days"),
    service: Optional[str] = Query(None, description="Filter by service"),
    activity_type: Optional[str] = Query(None, description="Filter by type"),
    activity_service: ActivityLogService = Depends(get_activity_service),
) -> ActivityTrendResponse:
    """Get activity trend over the specified number of days."""
    try:
        event_type = ActivityType(activity_type) if activity_type else None
        trend = await activity_service.get_activity_trend(
            days=days,
            event_type=event_type,
            service=service,
        )
        return ActivityTrendResponse(trend=trend)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid activity type: {e}",
        )
    except Exception as e:
        logger.error(f"Failed to get activity trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity trend",
        )


@router.delete(
    "/cleanup",
    response_model=CleanupResponse,
    summary="Cleanup old activities",
    description="Delete activities older than the specified retention period.",
)
async def cleanup_old_activities(
    retention_days: int = Query(30, ge=1, le=365, description="Retention period in days"),
    activity_service: ActivityLogService = Depends(get_activity_service),
) -> CleanupResponse:
    """Delete activity logs older than the retention period."""
    try:
        deleted_count = await activity_service.cleanup_by_retention_policy(retention_days)
        return CleanupResponse(
            deleted_count=deleted_count,
            message=f"Deleted {deleted_count} activities older than {retention_days} days",
        )
    except Exception as e:
        logger.error(f"Failed to cleanup activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old activities",
        )


@router.get(
    "/types",
    response_model=List[str],
    summary="Get available activity types",
    description="Get list of all available activity types.",
)
async def get_activity_types() -> List[str]:
    """Get all available activity types."""
    return [t.value for t in ActivityType]


@router.get(
    "/severities",
    response_model=List[str],
    summary="Get available severity levels",
    description="Get list of all available severity levels.",
)
async def get_severity_levels() -> List[str]:
    """Get all available severity levels."""
    return [s.value for s in ActivitySeverity]
