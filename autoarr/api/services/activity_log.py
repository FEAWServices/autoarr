"""
Activity Log Service.

Comprehensive logging service that tracks all monitoring, recovery, and system actions.
Provides query capabilities with filtering, pagination, and retention management.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from autoarr.api.database import ActivityLogRepository, Database, get_database
from autoarr.api.services.event_bus import Event, EventBus, EventType, get_event_bus

logger = logging.getLogger(__name__)


class ActivityLogService:
    """
    Service for managing activity logs.

    Subscribes to all events from the event bus and persists them to database
    for auditing, debugging, and analytics. Provides comprehensive query
    capabilities with filtering and pagination.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        event_bus: Optional[EventBus] = None,
        retention_days: int = 90,
    ):
        """
        Initialize activity log service.

        Args:
            db: Database instance (uses global if not provided)
            event_bus: Event bus instance (uses global if not provided)
            retention_days: Number of days to retain logs (default: 90)
        """
        self.db = db or get_database()
        self.event_bus = event_bus or get_event_bus()
        self.retention_days = retention_days

        # Repository
        self.repository = ActivityLogRepository(self.db)

        # Subscribe to all events
        self.event_bus.subscribe_all(self._handle_event)

        logger.info(f"ActivityLogService initialized with {retention_days} days retention")

    async def _handle_event(self, event: Event) -> None:
        """
        Handle event from event bus and persist to database.

        Args:
            event: Event to log
        """
        try:
            # Extract download ID from payload if present
            download_id = event.payload.get("nzo_id")

            # Extract application from payload if present
            application = event.payload.get("application") or event.payload.get(
                "source_application"
            )

            # Determine action from event type and payload
            action = self._determine_action(event)

            # Determine status from payload or event type
            status = self._determine_status(event)

            # Create log entry
            await self.repository.create_log(
                event_type=event.event_type.value,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                action=action,
                source="event_bus",
                status=status,
                details=json.dumps(event.payload),
                error_message=event.payload.get("error_message") or event.payload.get("reason"),
                download_id=download_id,
                application=application,
            )

            logger.debug(f"Logged event: {event.event_type.value} - {action}")

        except Exception as e:
            logger.error(f"Failed to log event {event.event_type.value}: {e}", exc_info=True)

    def _determine_action(self, event: Event) -> str:
        """
        Determine action description from event.

        Args:
            event: Event to analyze

        Returns:
            Action description
        """
        # Map event types to actions
        action_map = {
            EventType.DOWNLOAD_FAILED: "Download failed",
            EventType.DOWNLOAD_RECOVERED: "Download recovered successfully",
            EventType.DOWNLOAD_RETRY_STARTED: "Download retry started",
            EventType.DOWNLOAD_RETRY_FAILED: "Download retry failed",
            EventType.DOWNLOAD_MOVED_TO_DLQ: "Download moved to dead letter queue",
            EventType.QUEUE_POLLED: "Queue polled",
            EventType.QUEUE_STATE_CHANGED: "Queue state changed",
            EventType.WANTED_ITEM_DETECTED: "Wanted item detected",
            EventType.WANTED_ITEM_RESOLVED: "Wanted item resolved",
            EventType.CONFIG_APPLIED: "Configuration applied",
            EventType.CONFIG_VALIDATION_FAILED: "Configuration validation failed",
            EventType.AUDIT_STARTED: "Audit started",
            EventType.AUDIT_COMPLETED: "Audit completed",
            EventType.AUDIT_FAILED: "Audit failed",
            EventType.MONITORING_STARTED: "Monitoring started",
            EventType.MONITORING_STOPPED: "Monitoring stopped",
            EventType.SERVICE_ERROR: "Service error occurred",
        }

        base_action = action_map.get(event.event_type, "Unknown action")

        # Add details from payload if available
        if "filename" in event.payload:
            base_action += f": {event.payload['filename']}"
        elif "title" in event.payload:
            base_action += f": {event.payload['title']}"

        return base_action

    def _determine_status(self, event: Event) -> str:
        """
        Determine status from event.

        Args:
            event: Event to analyze

        Returns:
            Status string
        """
        # Check payload for explicit status
        if "status" in event.payload:
            return event.payload["status"]

        # Determine from event type
        if "failed" in event.event_type.value or "error" in event.event_type.value:
            return "failed"
        elif "recovered" in event.event_type.value or "resolved" in event.event_type.value:
            return "success"
        elif "started" in event.event_type.value:
            return "in_progress"
        elif "completed" in event.event_type.value:
            return "success"
        else:
            return "info"

    async def create_manual_log(
        self,
        action: str,
        source: str,
        status: str,
        details: Dict[str, Any],
        correlation_id: Optional[str] = None,
        error_message: Optional[str] = None,
        download_id: Optional[str] = None,
        application: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a manual activity log entry (not from event bus).

        Args:
            action: Action description
            source: Source of the action
            status: Status of the action
            details: Action details
            correlation_id: Optional correlation ID
            error_message: Optional error message
            download_id: Optional related download ID
            application: Optional related application

        Returns:
            Created log entry as dictionary
        """
        import uuid

        log = await self.repository.create_log(
            event_type="manual",
            correlation_id=correlation_id or str(uuid.uuid4()),
            action=action,
            source=source,
            status=status,
            details=json.dumps(details),
            error_message=error_message,
            download_id=download_id,
            application=application,
        )

        return self._log_to_dict(log)

    async def query_logs(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        download_id: Optional[str] = None,
        application: Optional[str] = None,
        correlation_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Query activity logs with filtering and pagination.

        Args:
            event_type: Filter by event type
            source: Filter by source
            status: Filter by status
            download_id: Filter by download ID
            application: Filter by application
            correlation_id: Filter by correlation ID
            page: Page number (1-indexed)
            page_size: Number of results per page

        Returns:
            Dictionary with logs and pagination info
        """
        offset = (page - 1) * page_size

        logs = await self.repository.get_logs(
            event_type=event_type,
            source=source,
            status=status,
            download_id=download_id,
            application=application,
            correlation_id=correlation_id,
            limit=page_size,
            offset=offset,
        )

        # Get total count for pagination
        total = await self.repository.count_logs(
            event_type=event_type,
            source=source,
            status=status,
        )

        return {
            "logs": [self._log_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def get_download_timeline(
        self,
        download_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get complete timeline of events for a download.

        Args:
            download_id: Download ID
            limit: Maximum number of events

        Returns:
            List of log entries in chronological order
        """
        logs = await self.repository.get_logs(
            download_id=download_id,
            limit=limit,
            offset=0,
        )

        # Reverse to get chronological order
        return [self._log_to_dict(log) for log in reversed(logs)]

    async def get_correlation_timeline(
        self,
        correlation_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get complete timeline of events for a correlation ID.

        Args:
            correlation_id: Correlation ID
            limit: Maximum number of events

        Returns:
            List of log entries in chronological order
        """
        logs = await self.repository.get_logs(
            correlation_id=correlation_id,
            limit=limit,
            offset=0,
        )

        # Reverse to get chronological order
        return [self._log_to_dict(log) for log in reversed(logs)]

    async def get_recent_errors(
        self,
        limit: int = 50,
        application: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent error logs.

        Args:
            limit: Maximum number of errors to return
            application: Optional filter by application

        Returns:
            List of error log entries
        """
        logs = await self.repository.get_logs(
            status="failed",
            application=application,
            limit=limit,
            offset=0,
        )

        return [self._log_to_dict(log) for log in logs]

    async def cleanup_old_logs(self) -> int:
        """
        Delete activity logs older than retention period.

        Returns:
            Number of logs deleted
        """
        deleted = await self.repository.delete_old_logs(self.retention_days)
        logger.info(
            f"Cleaned up {deleted} old activity logs (retention: {self.retention_days} days)"
        )
        return deleted

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get activity log statistics.

        Returns:
            Dictionary with statistics
        """
        total = await self.repository.count_logs()
        failed = await self.repository.count_logs(status="failed")
        success = await self.repository.count_logs(status="success")
        in_progress = await self.repository.count_logs(status="in_progress")

        return {
            "total_logs": total,
            "failed": failed,
            "success": success,
            "in_progress": in_progress,
            "retention_days": self.retention_days,
        }

    def _log_to_dict(self, log: Any) -> Dict[str, Any]:
        """
        Convert database log model to dictionary.

        Args:
            log: ActivityLog database model

        Returns:
            Dictionary representation
        """
        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type,
            "correlation_id": log.correlation_id,
            "causation_id": log.causation_id,
            "action": log.action,
            "source": log.source,
            "status": log.status,
            "details": json.loads(log.details) if log.details else {},
            "error_message": log.error_message,
            "download_id": log.download_id,
            "application": log.application,
        }


# ============================================================================
# Global Activity Log Service Instance
# ============================================================================

_activity_log_service: Optional[ActivityLogService] = None


def get_activity_log_service() -> ActivityLogService:
    """
    Get the global activity log service instance.

    Returns:
        ActivityLogService: Global service instance
    """
    global _activity_log_service
    if _activity_log_service is None:
        _activity_log_service = ActivityLogService()
    return _activity_log_service


def init_activity_log_service(
    db: Optional[Database] = None,
    event_bus: Optional[EventBus] = None,
    retention_days: int = 90,
) -> ActivityLogService:
    """
    Initialize the global activity log service.

    Args:
        db: Database instance
        event_bus: Event bus instance
        retention_days: Log retention in days

    Returns:
        ActivityLogService: Initialized service
    """
    global _activity_log_service
    _activity_log_service = ActivityLogService(
        db=db,
        event_bus=event_bus,
        retention_days=retention_days,
    )
    return _activity_log_service


def reset_activity_log_service() -> None:
    """Reset the global activity log service (for testing)."""
    global _activity_log_service
    _activity_log_service = None
