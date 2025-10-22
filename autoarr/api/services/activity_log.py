"""
Activity Log Service (Sprint 6).

This module provides comprehensive activity logging functionality with:
- Activity creation with metadata and correlation tracking
- Rich filtering by service, type, severity, date range
- Pagination support for efficient data retrieval
- Statistics aggregation and trend analysis
- Integration with EventBus for automatic activity logging
- Cleanup utilities for retention management

The service acts as a central activity tracking system for all AutoArr operations.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from autoarr.api.database import ActivityLog as ActivityLogModel
from autoarr.api.database import ActivityLogRepository

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class ActivityType(str, Enum):
    """Activity event types."""

    # Download events
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    DOWNLOAD_PAUSED = "download_paused"
    DOWNLOAD_RESUMED = "download_resumed"

    # Recovery events
    RECOVERY_ATTEMPTED = "recovery_attempted"
    RECOVERY_SUCCESS = "recovery_success"
    RECOVERY_FAILED = "recovery_failed"
    RECOVERY_CANCELLED = "recovery_cancelled"

    # Configuration events
    CONFIG_AUDIT_STARTED = "config_audit_started"
    CONFIG_AUDIT_COMPLETED = "config_audit_completed"
    CONFIG_APPLIED = "config_applied"
    CONFIG_ERROR = "config_error"

    # Request events
    REQUEST_RECEIVED = "request_received"
    REQUEST_PROCESSED = "request_processed"
    REQUEST_FAILED = "request_failed"

    # System events
    SYSTEM_INFO = "system_info"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_ERROR = "system_error"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"


class ActivitySeverity(str, Enum):
    """Activity severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class ActivityLog:
    """Activity log data model."""

    id: int
    service: str
    activity_type: ActivityType
    severity: ActivitySeverity
    message: str
    correlation_id: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    created_at: datetime
    user_id: Optional[str] = None

    @classmethod
    def from_db_model(cls, db_model: ActivityLogModel) -> "ActivityLog":
        """Create ActivityLog from database model."""
        return cls(
            id=db_model.id,
            service=db_model.service,
            activity_type=ActivityType(db_model.event_type),
            severity=ActivitySeverity(db_model.severity),
            message=db_model.message,
            correlation_id=db_model.correlation_id,
            metadata=db_model.event_metadata or {},
            timestamp=db_model.timestamp,
            created_at=db_model.created_at,
            user_id=db_model.user_id,
        )


@dataclass
class ActivityFilter:
    """Filter criteria for activity queries."""

    service: Optional[str] = None
    services: Optional[List[str]] = None
    activity_type: Optional[ActivityType] = None
    activity_types: Optional[List[ActivityType]] = None
    severity: Optional[ActivitySeverity] = None
    severities: Optional[List[ActivitySeverity]] = None
    min_severity: Optional[ActivitySeverity] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    correlation_id: Optional[str] = None
    search_query: Optional[str] = None


@dataclass
class ActivityStatistics:
    """Activity statistics aggregation."""

    total_count: int
    by_type: Dict[ActivityType, int]
    by_service: Dict[str, int]
    by_severity: Dict[ActivitySeverity, int]


@dataclass
class PaginatedResult:
    """Paginated activity results."""

    items: List[ActivityLog]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ============================================================================
# Activity Log Service
# ============================================================================


class ActivityLogService:
    """
    Service for managing activity logs.

    Provides comprehensive activity tracking, filtering, pagination,
    and statistics aggregation.
    """

    def __init__(self, repository: ActivityLogRepository):
        """
        Initialize service.

        Args:
            repository: Activity log repository instance
        """
        self.repository = repository

    async def create_activity(
        self,
        service: str,
        activity_type: ActivityType,
        severity: ActivitySeverity,
        message: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> ActivityLog:
        """
        Create a new activity log entry.

        Args:
            service: Service name
            activity_type: Type of activity
            severity: Severity level
            message: Human-readable message
            correlation_id: Optional correlation ID
            metadata: Optional metadata dictionary
            user_id: Optional user ID
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Created ActivityLog
        """
        db_activity = await self.repository.create_activity(
            service=service,
            event_type=activity_type.value,
            severity=severity.value,
            message=message,
            correlation_id=correlation_id,
            metadata=metadata,
            user_id=user_id,
            timestamp=timestamp,
        )
        # Handle both database models and service models (for testing)
        if isinstance(db_activity, ActivityLog):
            return db_activity
        return ActivityLog.from_db_model(db_activity)

    async def get_activity_by_id(self, activity_id: int) -> Optional[ActivityLog]:
        """
        Get a specific activity by ID.

        Args:
            activity_id: Activity ID

        Returns:
            ActivityLog if found, None otherwise
        """
        db_activity = await self.repository.get_activity_by_id(activity_id)
        if db_activity:
            # Handle both database models and service models (for testing)
            if isinstance(db_activity, ActivityLog):
                return db_activity
            return ActivityLog.from_db_model(db_activity)
        return None

    async def get_activities(
        self,
        filter: Optional[ActivityFilter] = None,
        order_by: str = "timestamp",
        order: str = "desc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ActivityLog]:
        """
        Get activities with optional filters.

        Args:
            filter: Optional filter criteria
            order_by: Field to order by (default: timestamp)
            order: Order direction (asc/desc)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of ActivityLog instances
        """
        # Build filter parameters
        filter_params = self._build_filter_params(filter)

        db_activities = await self.repository.get_activities(
            **filter_params,
            order_by=order_by,
            order=order,
            limit=limit,
            offset=offset,
        )

        # Handle both database models and service models (for testing)
        return [
            (
                db_activity
                if isinstance(db_activity, ActivityLog)
                else ActivityLog.from_db_model(db_activity)
            )
            for db_activity in db_activities
        ]

    async def get_workflow_by_correlation_id(self, correlation_id: str) -> List[ActivityLog]:
        """
        Get all activities for a workflow using correlation ID.

        Activities are returned ordered by timestamp ascending to show
        the workflow progression.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of ActivityLog instances in chronological order
        """
        db_activities = await self.repository.get_activities(
            correlation_id=correlation_id,
            order_by="timestamp",
            order="asc",
        )
        # Handle both database models and service models (for testing)
        return [
            (
                db_activity
                if isinstance(db_activity, ActivityLog)
                else ActivityLog.from_db_model(db_activity)
            )
            for db_activity in db_activities
        ]

    async def get_activities_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filter: Optional[ActivityFilter] = None,
        order_by: str = "timestamp",
        order: str = "desc",
    ) -> PaginatedResult:
        """
        Get paginated activities with optional filters.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filter: Optional filter criteria
            order_by: Field to order by
            order: Order direction (asc/desc)

        Returns:
            PaginatedResult with items and pagination metadata
        """
        # Build filter parameters
        filter_params = self._build_filter_params(filter)

        # Get total count
        total_items = await self.repository.count_activities(**filter_params)

        # Calculate pagination
        total_pages = (total_items + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # Get items
        db_activities = await self.repository.get_activities(
            **filter_params,
            order_by=order_by,
            order=order,
            limit=page_size,
            offset=offset,
        )

        # Handle both database models and service models (for testing)
        items = [
            (
                db_activity
                if isinstance(db_activity, ActivityLog)
                else ActivityLog.from_db_model(db_activity)
            )
            for db_activity in db_activities
        ]

        return PaginatedResult(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ActivityStatistics:
        """
        Get activity statistics with aggregations.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            ActivityStatistics with aggregated data
        """
        stats_result = await self.repository.get_statistics(  # noqa: F841
            start_date=start_date,
            end_date=end_date,
        )

        # Handle both dict (from repository) and ActivityStatistics (from tests)
        if isinstance(stats_result, ActivityStatistics):
            return stats_result

        # Convert string keys to enums
        by_type = {ActivityType(k): v for k, v in stats_result.get("by_type", {}).items()}
        by_severity = {
            ActivitySeverity(k): v for k, v in stats_result.get("by_severity", {}).items()
        }

        return ActivityStatistics(
            total_count=stats_result.get("total_count", 0),
            by_type=by_type,
            by_service=stats_result.get("by_service", {}),
            by_severity=by_severity,
        )

    async def get_activity_trend(
        self,
        days: int = 7,
        event_type: Optional[ActivityType] = None,
        service: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get activity trend over time.

        Args:
            days: Number of days to include
            event_type: Optional event type filter
            service: Optional service filter

        Returns:
            Dictionary mapping dates (YYYY-MM-DD) to counts
        """
        result = await self.repository.get_trend(
            days=days,
            event_type=event_type.value if event_type else None,
            service=service,
        )
        return dict(result)  # Explicitly cast to dict

    async def delete_old_activities(self, cutoff_date: datetime) -> int:
        """
        Delete activities older than cutoff date.

        Args:
            cutoff_date: Delete activities before this date

        Returns:
            Number of activities deleted
        """
        count = await self.repository.delete_old_activities(cutoff_date)
        return int(count)  # Explicitly cast to int

    async def cleanup_by_retention_policy(self, retention_days: int) -> int:
        """
        Cleanup activities based on retention policy.

        Args:
            retention_days: Number of days to retain

        Returns:
            Number of activities deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return await self.delete_old_activities(cutoff_date)

    def _build_filter_params(self, filter: Optional[ActivityFilter]) -> Dict[str, Any]:
        """
        Build filter parameters for repository queries.

        Args:
            filter: Optional filter criteria

        Returns:
            Dictionary of filter parameters
        """
        if not filter:
            return {}

        params: Dict[str, Any] = {}

        if filter.service:
            params["service"] = filter.service
        if filter.services:
            params["services"] = filter.services
        if filter.activity_type:
            params["event_type"] = filter.activity_type.value
        if filter.activity_types:
            params["event_types"] = [at.value for at in filter.activity_types]
        if filter.severity:
            params["severity"] = filter.severity.value
        if filter.severities:
            params["severities"] = [s.value for s in filter.severities]
        if filter.min_severity:
            params["min_severity"] = filter.min_severity.value
        if filter.start_date:
            params["start_date"] = filter.start_date
        if filter.end_date:
            params["end_date"] = filter.end_date
        if filter.correlation_id:
            params["correlation_id"] = filter.correlation_id
        if filter.search_query:
            params["search_query"] = filter.search_query

        return params
