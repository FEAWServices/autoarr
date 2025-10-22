"""
Unit tests for Activity Log Service (Sprint 6).

This module tests the ActivityLog service's ability to:
- Create and store activity events with metadata
- Filter activities by service, type, severity, date range
- Support pagination for activity lists
- Aggregate statistics (counts by type, service, time period)
- Track correlation IDs for related activities
- Index by timestamp for efficient queries
- Handle concurrent activity logging
- Provide activity search and retrieval

Test Strategy:
- 70% Unit Tests: Focus on CRUD operations and filtering
- Test all filter combinations and edge cases
- Verify pagination logic and performance
- Test statistics aggregation accuracy
- Ensure proper indexing and query optimization
- Test concurrent writes and reads
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock

import pytest

from autoarr.api.database import ActivityLogRepository, Database
from autoarr.api.services.activity_log import (
    ActivityFilter,
    ActivityLog,
    ActivityLogService,
    ActivitySeverity,
    ActivityStatistics,
    ActivityType,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_database():
    """Create a mock database."""
    db = Mock(spec=Database)
    db.session = AsyncMock()
    return db


@pytest.fixture
def mock_activity_repo():
    """Create a mock activity log repository."""
    repo = Mock(spec=ActivityLogRepository)
    repo.create_activity = AsyncMock()
    repo.get_activities = AsyncMock()
    repo.get_activity_by_id = AsyncMock()
    repo.count_activities = AsyncMock()
    repo.get_statistics = AsyncMock()
    repo.delete_old_activities = AsyncMock()
    return repo


@pytest.fixture
def activity_log_service(mock_activity_repo):
    """Create an ActivityLogService instance with mocked dependencies."""
    service = ActivityLogService(repository=mock_activity_repo)
    return service


# ============================================================================
# Test Data Factories
# ============================================================================


def create_activity(
    activity_id: int = 1,
    service: str = "monitoring_service",
    activity_type: ActivityType = ActivityType.DOWNLOAD_FAILED,
    severity: ActivitySeverity = ActivitySeverity.WARNING,
    message: str = "Download failed",
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> ActivityLog:
    """Factory to create ActivityLog test data."""
    return ActivityLog(
        id=activity_id,
        service=service,
        activity_type=activity_type,
        severity=severity,
        message=message,
        correlation_id=correlation_id or f"corr_{activity_id}",
        metadata=metadata or {},
        timestamp=timestamp or datetime.now(),
        created_at=timestamp or datetime.now(),
    )


def create_activity_filter(
    service: Optional[str] = None,
    activity_type: Optional[ActivityType] = None,
    severity: Optional[ActivitySeverity] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    correlation_id: Optional[str] = None,
    search_query: Optional[str] = None,
) -> ActivityFilter:
    """Factory to create ActivityFilter test data."""
    return ActivityFilter(
        service=service,
        activity_type=activity_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        correlation_id=correlation_id,
        search_query=search_query,
    )


# ============================================================================
# Tests for Activity Creation
# ============================================================================


@pytest.mark.asyncio
async def test_create_activity_success(activity_log_service, mock_activity_repo):
    """Test successful creation of an activity log entry."""
    # Arrange
    mock_activity = create_activity(1, "monitoring_service", ActivityType.DOWNLOAD_FAILED)
    mock_activity_repo.create_activity.return_value = mock_activity

    # Act
    activity = await activity_log_service.create_activity(
        service="monitoring_service",
        activity_type=ActivityType.DOWNLOAD_FAILED,
        severity=ActivitySeverity.WARNING,
        message="Download failed",
        correlation_id="corr_123",
        metadata={"nzo_id": "test_123"},
    )

    # Assert
    assert activity is not None
    assert activity.service == "monitoring_service"
    assert activity.activity_type == ActivityType.DOWNLOAD_FAILED
    mock_activity_repo.create_activity.assert_called_once()


@pytest.mark.asyncio
async def test_create_activity_with_metadata(activity_log_service, mock_activity_repo):
    """Test creating activity with detailed metadata."""
    # Arrange
    metadata = {
        "nzo_id": "test_123",
        "filename": "Test.Show.S01E01.mkv",
        "failure_reason": "CRC error",
        "category": "tv",
        "size": 1234567890,
    }
    mock_activity_repo.create_activity.return_value = create_activity(metadata=metadata)

    # Act
    activity = await activity_log_service.create_activity(
        service="monitoring_service",
        activity_type=ActivityType.DOWNLOAD_FAILED,
        severity=ActivitySeverity.ERROR,
        message="Download failed with CRC error",
        metadata=metadata,
    )

    # Assert
    assert activity.metadata == metadata
    assert activity.metadata["nzo_id"] == "test_123"


@pytest.mark.asyncio
async def test_create_activity_auto_timestamp(activity_log_service, mock_activity_repo):
    """Test that activity creation auto-generates timestamp."""
    # Arrange
    before_time = datetime.now()
    mock_activity_repo.create_activity.return_value = create_activity()

    # Act
    activity = await activity_log_service.create_activity(
        service="test_service",
        activity_type=ActivityType.SYSTEM_INFO,
        severity=ActivitySeverity.INFO,
        message="Test activity",
    )
    after_time = datetime.now()

    # Assert
    assert activity.timestamp is not None
    assert before_time <= activity.timestamp <= after_time


@pytest.mark.asyncio
async def test_create_activity_with_correlation_id(activity_log_service, mock_activity_repo):
    """Test creating activity with correlation ID for tracking."""
    # Arrange
    correlation_id = "workflow_abc123"
    mock_activity_repo.create_activity.return_value = create_activity(correlation_id=correlation_id)

    # Act
    activity = await activity_log_service.create_activity(
        service="recovery_service",
        activity_type=ActivityType.RECOVERY_ATTEMPTED,
        severity=ActivitySeverity.INFO,
        message="Retry attempted",
        correlation_id=correlation_id,
    )

    # Assert
    assert activity.correlation_id == correlation_id


@pytest.mark.asyncio
async def test_create_activity_different_severities(activity_log_service, mock_activity_repo):
    """Test creating activities with different severity levels."""
    # Test all severity levels
    severities = [
        ActivitySeverity.INFO,
        ActivitySeverity.WARNING,
        ActivitySeverity.ERROR,
        ActivitySeverity.CRITICAL,
    ]

    for severity in severities:
        # Arrange
        mock_activity_repo.create_activity.return_value = create_activity(severity=severity)

        # Act
        activity = await activity_log_service.create_activity(
            service="test_service",
            activity_type=ActivityType.SYSTEM_INFO,
            severity=severity,
            message=f"Test {severity.value}",
        )

        # Assert
        assert activity.severity == severity


# ============================================================================
# Tests for Activity Retrieval
# ============================================================================


@pytest.mark.asyncio
async def test_get_activities_all(activity_log_service, mock_activity_repo):
    """Test retrieving all activities without filters."""
    # Arrange
    mock_activities = [
        create_activity(1, "service_a", ActivityType.DOWNLOAD_COMPLETED),
        create_activity(2, "service_b", ActivityType.RECOVERY_ATTEMPTED),
        create_activity(3, "service_a", ActivityType.DOWNLOAD_FAILED),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    # Act
    activities = await activity_log_service.get_activities()

    # Assert
    assert len(activities) == 3
    mock_activity_repo.get_activities.assert_called_once()


@pytest.mark.asyncio
async def test_get_activity_by_id(activity_log_service, mock_activity_repo):
    """Test retrieving a specific activity by ID."""
    # Arrange
    activity_id = 123
    mock_activity = create_activity(activity_id, "monitoring_service")
    mock_activity_repo.get_activity_by_id.return_value = mock_activity

    # Act
    activity = await activity_log_service.get_activity_by_id(activity_id)

    # Assert
    assert activity is not None
    assert activity.id == activity_id
    mock_activity_repo.get_activity_by_id.assert_called_once_with(activity_id)


@pytest.mark.asyncio
async def test_get_nonexistent_activity(activity_log_service, mock_activity_repo):
    """Test retrieving a non-existent activity returns None."""
    # Arrange
    mock_activity_repo.get_activity_by_id.return_value = None

    # Act
    activity = await activity_log_service.get_activity_by_id(99999)

    # Assert
    assert activity is None


# ============================================================================
# Tests for Filtering by Service
# ============================================================================


@pytest.mark.asyncio
async def test_filter_activities_by_service(activity_log_service, mock_activity_repo):
    """Test filtering activities by specific service."""
    # Arrange
    mock_activities = [
        create_activity(1, "monitoring_service"),
        create_activity(2, "monitoring_service"),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(service="monitoring_service")

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2
    assert all(a.service == "monitoring_service" for a in activities)


@pytest.mark.asyncio
async def test_filter_by_multiple_services(activity_log_service, mock_activity_repo):
    """Test filtering activities by multiple services."""
    # Arrange
    mock_activities = [
        create_activity(1, "monitoring_service"),
        create_activity(2, "recovery_service"),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = ActivityFilter(services=["monitoring_service", "recovery_service"])

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2


# ============================================================================
# Tests for Filtering by Activity Type
# ============================================================================


@pytest.mark.asyncio
async def test_filter_activities_by_type(activity_log_service, mock_activity_repo):
    """Test filtering activities by activity type."""
    # Arrange
    mock_activities = [
        create_activity(1, activity_type=ActivityType.DOWNLOAD_FAILED),
        create_activity(2, activity_type=ActivityType.DOWNLOAD_FAILED),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(activity_type=ActivityType.DOWNLOAD_FAILED)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2
    assert all(a.activity_type == ActivityType.DOWNLOAD_FAILED for a in activities)


@pytest.mark.asyncio
async def test_filter_by_multiple_activity_types(activity_log_service, mock_activity_repo):
    """Test filtering by multiple activity types."""
    # Arrange
    mock_activities = [
        create_activity(1, activity_type=ActivityType.DOWNLOAD_FAILED),
        create_activity(2, activity_type=ActivityType.RECOVERY_ATTEMPTED),
        create_activity(3, activity_type=ActivityType.RECOVERY_SUCCESS),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = ActivityFilter(
        activity_types=[
            ActivityType.DOWNLOAD_FAILED,
            ActivityType.RECOVERY_ATTEMPTED,
            ActivityType.RECOVERY_SUCCESS,
        ]
    )

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 3


# ============================================================================
# Tests for Filtering by Severity
# ============================================================================


@pytest.mark.asyncio
async def test_filter_activities_by_severity(activity_log_service, mock_activity_repo):
    """Test filtering activities by severity level."""
    # Arrange
    mock_activities = [
        create_activity(1, severity=ActivitySeverity.ERROR),
        create_activity(2, severity=ActivitySeverity.ERROR),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(severity=ActivitySeverity.ERROR)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2
    assert all(a.severity == ActivitySeverity.ERROR for a in activities)


@pytest.mark.asyncio
async def test_filter_by_minimum_severity(activity_log_service, mock_activity_repo):
    """Test filtering by minimum severity level (e.g., WARNING and above)."""
    # Arrange - Return WARNING, ERROR, CRITICAL (not INFO)
    mock_activities = [
        create_activity(1, severity=ActivitySeverity.WARNING),
        create_activity(2, severity=ActivitySeverity.ERROR),
        create_activity(3, severity=ActivitySeverity.CRITICAL),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = ActivityFilter(min_severity=ActivitySeverity.WARNING)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 3
    assert all(
        a.severity in [ActivitySeverity.WARNING, ActivitySeverity.ERROR, ActivitySeverity.CRITICAL]
        for a in activities
    )


# ============================================================================
# Tests for Date Range Filtering
# ============================================================================


@pytest.mark.asyncio
async def test_filter_activities_by_date_range(activity_log_service, mock_activity_repo):
    """Test filtering activities by date range."""
    # Arrange
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    mock_activities = [
        create_activity(1, timestamp=datetime.now() - timedelta(days=5)),
        create_activity(2, timestamp=datetime.now() - timedelta(days=3)),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(start_date=start_date, end_date=end_date)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2
    assert all(start_date <= a.timestamp <= end_date for a in activities)


@pytest.mark.asyncio
async def test_filter_activities_after_date(activity_log_service, mock_activity_repo):
    """Test filtering activities after a specific date."""
    # Arrange
    cutoff_date = datetime.now() - timedelta(days=1)
    mock_activities = [
        create_activity(1, timestamp=datetime.now()),
        create_activity(2, timestamp=datetime.now() - timedelta(hours=12)),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(start_date=cutoff_date)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2
    assert all(a.timestamp >= cutoff_date for a in activities)


@pytest.mark.asyncio
async def test_filter_activities_before_date(activity_log_service, mock_activity_repo):
    """Test filtering activities before a specific date."""
    # Arrange
    cutoff_date = datetime.now() - timedelta(days=1)
    mock_activities = [
        create_activity(1, timestamp=datetime.now() - timedelta(days=5)),
        create_activity(2, timestamp=datetime.now() - timedelta(days=3)),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(end_date=cutoff_date)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 2
    assert all(a.timestamp <= cutoff_date for a in activities)


# ============================================================================
# Tests for Correlation ID Filtering
# ============================================================================


@pytest.mark.asyncio
async def test_filter_activities_by_correlation_id(activity_log_service, mock_activity_repo):
    """Test filtering activities by correlation ID to track related events."""
    # Arrange
    correlation_id = "workflow_abc123"
    mock_activities = [
        create_activity(
            1, correlation_id=correlation_id, activity_type=ActivityType.DOWNLOAD_FAILED
        ),
        create_activity(
            2, correlation_id=correlation_id, activity_type=ActivityType.RECOVERY_ATTEMPTED
        ),
        create_activity(
            3, correlation_id=correlation_id, activity_type=ActivityType.RECOVERY_SUCCESS
        ),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(correlation_id=correlation_id)

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) == 3
    assert all(a.correlation_id == correlation_id for a in activities)


@pytest.mark.asyncio
async def test_get_activity_workflow_by_correlation_id(activity_log_service, mock_activity_repo):
    """Test retrieving complete workflow using correlation ID."""
    # Arrange
    correlation_id = "workflow_123"
    mock_activities = [
        create_activity(
            1,
            correlation_id=correlation_id,
            activity_type=ActivityType.DOWNLOAD_FAILED,
            timestamp=datetime.now() - timedelta(minutes=10),
        ),
        create_activity(
            2,
            correlation_id=correlation_id,
            activity_type=ActivityType.RECOVERY_ATTEMPTED,
            timestamp=datetime.now() - timedelta(minutes=5),
        ),
        create_activity(
            3,
            correlation_id=correlation_id,
            activity_type=ActivityType.RECOVERY_SUCCESS,
            timestamp=datetime.now(),
        ),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    # Act
    workflow = await activity_log_service.get_workflow_by_correlation_id(correlation_id)

    # Assert
    assert len(workflow) == 3
    # Should be ordered by timestamp
    assert workflow[0].activity_type == ActivityType.DOWNLOAD_FAILED
    assert workflow[1].activity_type == ActivityType.RECOVERY_ATTEMPTED
    assert workflow[2].activity_type == ActivityType.RECOVERY_SUCCESS


# ============================================================================
# Tests for Search Query
# ============================================================================


@pytest.mark.asyncio
async def test_search_activities_by_message(activity_log_service, mock_activity_repo):
    """Test searching activities by message content."""
    # Arrange
    mock_activities = [
        create_activity(1, message="Download failed: CRC error"),
        create_activity(2, message="Download failed: Disk full"),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(search_query="CRC error")

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) >= 1
    assert any("CRC error" in a.message for a in activities)


@pytest.mark.asyncio
async def test_search_activities_by_metadata(activity_log_service, mock_activity_repo):
    """Test searching activities by metadata content."""
    # Arrange
    mock_activities = [
        create_activity(1, metadata={"filename": "Breaking.Bad.S01E01.mkv"}),
    ]
    mock_activity_repo.get_activities.return_value = mock_activities

    activity_filter = create_activity_filter(search_query="Breaking.Bad")

    # Act
    activities = await activity_log_service.get_activities(filter=activity_filter)

    # Assert
    assert len(activities) >= 1


# ============================================================================
# Tests for Pagination
# ============================================================================


@pytest.mark.asyncio
async def test_paginate_activities(activity_log_service, mock_activity_repo):
    """Test paginating activity results."""
    # Arrange - First page
    page_1_activities = [create_activity(i) for i in range(1, 21)]  # 20 items
    mock_activity_repo.get_activities.return_value = page_1_activities
    mock_activity_repo.count_activities.return_value = 50  # Total count

    # Act
    result = await activity_log_service.get_activities_paginated(page=1, page_size=20)  # noqa: F841

    # Assert
    assert len(result.items) == 20
    assert result.page == 1
    assert result.page_size == 20
    assert result.total_items == 50
    assert result.total_pages == 3


@pytest.mark.asyncio
async def test_paginate_activities_second_page(activity_log_service, mock_activity_repo):
    """Test retrieving second page of paginated results."""
    # Arrange - Second page
    page_2_activities = [create_activity(i) for i in range(21, 41)]
    mock_activity_repo.get_activities.return_value = page_2_activities
    mock_activity_repo.count_activities.return_value = 50

    # Act
    result = await activity_log_service.get_activities_paginated(page=2, page_size=20)  # noqa: F841

    # Assert
    assert len(result.items) == 20
    assert result.page == 2
    assert result.has_next is True
    assert result.has_previous is True


@pytest.mark.asyncio
async def test_paginate_activities_last_page(activity_log_service, mock_activity_repo):
    """Test retrieving last page with partial results."""
    # Arrange - Last page with only 10 items
    page_3_activities = [create_activity(i) for i in range(41, 51)]
    mock_activity_repo.get_activities.return_value = page_3_activities
    mock_activity_repo.count_activities.return_value = 50

    # Act
    result = await activity_log_service.get_activities_paginated(page=3, page_size=20)  # noqa: F841

    # Assert
    assert len(result.items) == 10
    assert result.page == 3
    assert result.has_next is False
    assert result.has_previous is True


@pytest.mark.asyncio
async def test_pagination_with_filters(activity_log_service, mock_activity_repo):
    """Test pagination combined with filters."""
    # Arrange
    filtered_activities = [
        create_activity(i, severity=ActivitySeverity.ERROR) for i in range(1, 11)
    ]
    mock_activity_repo.get_activities.return_value = filtered_activities
    mock_activity_repo.count_activities.return_value = 10

    activity_filter = create_activity_filter(severity=ActivitySeverity.ERROR)

    # Act
    result = await activity_log_service.get_activities_paginated(  # noqa: F841
        filter=activity_filter, page=1, page_size=10
    )

    # Assert
    assert len(result.items) == 10
    assert all(a.severity == ActivitySeverity.ERROR for a in result.items)


# ============================================================================
# Tests for Statistics Aggregation
# ============================================================================


@pytest.mark.asyncio
async def test_get_activity_statistics(activity_log_service, mock_activity_repo):
    """Test retrieving activity statistics."""
    # Arrange
    mock_stats = ActivityStatistics(
        total_count=100,
        by_type={
            ActivityType.DOWNLOAD_FAILED: 30,
            ActivityType.RECOVERY_ATTEMPTED: 25,
            ActivityType.RECOVERY_SUCCESS: 20,
            ActivityType.DOWNLOAD_COMPLETED: 25,
        },
        by_service={
            "monitoring_service": 50,
            "recovery_service": 50,
        },
        by_severity={
            ActivitySeverity.INFO: 50,
            ActivitySeverity.WARNING: 30,
            ActivitySeverity.ERROR: 15,
            ActivitySeverity.CRITICAL: 5,
        },
    )
    mock_activity_repo.get_statistics.return_value = mock_stats

    # Act
    stats = await activity_log_service.get_statistics()

    # Assert
    assert stats.total_count == 100
    assert stats.by_type[ActivityType.DOWNLOAD_FAILED] == 30
    assert stats.by_service["monitoring_service"] == 50


@pytest.mark.asyncio
async def test_get_statistics_for_date_range(activity_log_service, mock_activity_repo):
    """Test statistics for a specific date range."""
    # Arrange
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    mock_stats = ActivityStatistics(
        total_count=50,
        by_type={ActivityType.DOWNLOAD_FAILED: 20},
        by_service={"monitoring_service": 50},
        by_severity={ActivitySeverity.ERROR: 20},
    )
    mock_activity_repo.get_statistics.return_value = mock_stats

    # Act
    stats = await activity_log_service.get_statistics(start_date=start_date, end_date=end_date)

    # Assert
    assert stats.total_count == 50


@pytest.mark.asyncio
async def test_get_statistics_by_service(activity_log_service, mock_activity_repo):
    """Test statistics breakdown by service."""
    # Arrange
    mock_stats = ActivityStatistics(
        total_count=100,
        by_service={
            "monitoring_service": 40,
            "recovery_service": 35,
            "request_handler": 25,
        },
        by_type={},
        by_severity={},
    )
    mock_activity_repo.get_statistics.return_value = mock_stats

    # Act
    stats = await activity_log_service.get_statistics()

    # Assert
    assert len(stats.by_service) == 3
    assert stats.by_service["monitoring_service"] == 40
    assert stats.by_service["recovery_service"] == 35


@pytest.mark.asyncio
async def test_get_statistics_by_severity(activity_log_service, mock_activity_repo):
    """Test statistics breakdown by severity."""
    # Arrange
    mock_stats = ActivityStatistics(
        total_count=100,
        by_severity={
            ActivitySeverity.INFO: 60,
            ActivitySeverity.WARNING: 25,
            ActivitySeverity.ERROR: 10,
            ActivitySeverity.CRITICAL: 5,
        },
        by_type={},
        by_service={},
    )
    mock_activity_repo.get_statistics.return_value = mock_stats

    # Act
    stats = await activity_log_service.get_statistics()

    # Assert
    assert stats.by_severity[ActivitySeverity.INFO] == 60
    assert stats.by_severity[ActivitySeverity.CRITICAL] == 5


@pytest.mark.asyncio
async def test_get_activity_trend_over_time(activity_log_service, mock_activity_repo):
    """Test getting activity trends over time periods."""
    # Arrange
    mock_trend = {
        "2024-01-01": 50,
        "2024-01-02": 45,
        "2024-01-03": 60,
        "2024-01-04": 55,
    }
    mock_activity_repo.get_trend.return_value = mock_trend

    # Act
    trend = await activity_log_service.get_activity_trend(days=7)

    # Assert
    assert len(trend) >= 4
    assert "2024-01-01" in trend


# ============================================================================
# Tests for Database Model
# ============================================================================


@pytest.mark.asyncio
async def test_activity_model_fields(activity_log_service):
    """Test that activity model has all required fields."""
    # Create activity instance
    activity = create_activity(
        activity_id=1,
        service="test_service",
        activity_type=ActivityType.SYSTEM_INFO,
        severity=ActivitySeverity.INFO,
        message="Test message",
        correlation_id="corr_123",
        metadata={"key": "value"},
    )

    # Assert all fields present
    assert hasattr(activity, "id")
    assert hasattr(activity, "service")
    assert hasattr(activity, "activity_type")
    assert hasattr(activity, "severity")
    assert hasattr(activity, "message")
    assert hasattr(activity, "correlation_id")
    assert hasattr(activity, "metadata")
    assert hasattr(activity, "timestamp")
    assert hasattr(activity, "created_at")


# ============================================================================
# Tests for Concurrent Operations
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_reads_and_writes(activity_log_service, mock_activity_repo):
    """Test concurrent read and write operations."""
    # Arrange
    mock_activity_repo.create_activity.return_value = create_activity()
    mock_activity_repo.get_activities.return_value = [create_activity()]

    # Act - Mix reads and writes
    tasks = []
    for i in range(5):
        tasks.append(
            activity_log_service.create_activity(
                service="test",
                activity_type=ActivityType.SYSTEM_INFO,
                severity=ActivitySeverity.INFO,
                message=f"Write {i}",
            )
        )
        tasks.append(activity_log_service.get_activities())

    results = await asyncio.gather(*tasks)

    # Assert - All operations complete successfully
    assert len(results) == 10


# ============================================================================
# Tests for Activity Cleanup
# ============================================================================


@pytest.mark.asyncio
async def test_delete_old_activities(activity_log_service, mock_activity_repo):
    """Test deletion of old activities."""
    # Arrange
    cutoff_date = datetime.now() - timedelta(days=90)
    mock_activity_repo.delete_old_activities.return_value = 50  # 50 deleted

    # Act
    deleted_count = await activity_log_service.delete_old_activities(cutoff_date)

    # Assert
    assert deleted_count == 50
    mock_activity_repo.delete_old_activities.assert_called_once_with(cutoff_date)


@pytest.mark.asyncio
async def test_cleanup_by_retention_policy(activity_log_service, mock_activity_repo):
    """Test cleanup based on retention policy (e.g., keep 90 days)."""
    # Arrange
    retention_days = 90
    mock_activity_repo.delete_old_activities.return_value = 100

    # Act
    deleted_count = await activity_log_service.cleanup_by_retention_policy(retention_days)

    # Assert
    assert deleted_count == 100


# ============================================================================
# Tests for Performance
# ============================================================================


@pytest.mark.asyncio
async def test_query_performance_with_large_dataset(activity_log_service, mock_activity_repo):
    """Test query performance with large number of activities."""
    # Arrange - Large dataset
    mock_activities = [create_activity(i) for i in range(1000)]
    mock_activity_repo.get_activities.return_value = mock_activities

    # Act
    start_time = datetime.now()
    activities = await activity_log_service.get_activities()
    duration = (datetime.now() - start_time).total_seconds()

    # Assert
    assert len(activities) == 1000
    assert duration < 1.0  # Should be fast with proper indexing


@pytest.mark.asyncio
async def test_pagination_performance(activity_log_service, mock_activity_repo):
    """Test that pagination improves performance for large datasets."""
    # Arrange
    mock_activity_repo.get_activities.return_value = [create_activity(i) for i in range(20)]
    mock_activity_repo.count_activities.return_value = 10000

    # Act
    start_time = datetime.now()
    result = await activity_log_service.get_activities_paginated(page=1, page_size=20)  # noqa: F841
    duration = (datetime.now() - start_time).total_seconds()

    # Assert - Should only load page size, not all 10000
    assert len(result.items) == 20
    assert duration < 0.5  # Fast because of pagination


# ============================================================================
# Tests for Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_handle_database_error_on_create(activity_log_service, mock_activity_repo):
    """Test handling of database errors during activity creation."""
    # Arrange
    mock_activity_repo.create_activity.side_effect = Exception("Database error")

    # Act & Assert - Should handle gracefully
    with pytest.raises(Exception):
        await activity_log_service.create_activity(
            service="test",
            activity_type=ActivityType.SYSTEM_INFO,
            severity=ActivitySeverity.INFO,
            message="Test",
        )


@pytest.mark.asyncio
async def test_handle_invalid_filter_parameters(activity_log_service, mock_activity_repo):
    """Test handling of invalid filter parameters."""
    # Arrange - Invalid date range (end before start)
    activity_filter = create_activity_filter(
        start_date=datetime.now(),
        end_date=datetime.now() - timedelta(days=1),
    )

    # Act & Assert - Should either validate or handle gracefully
    # Implementation may raise ValueError or return empty results
    result = await activity_log_service.get_activities(filter=activity_filter)  # noqa: F841
    assert isinstance(result, list)  # Should return list, possibly empty
