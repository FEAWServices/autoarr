"""
Monitoring API Endpoints.

Provides endpoints for download monitoring, recovery status,
activity logs, and real-time WebSocket updates.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from autoarr.api.services.activity_log import get_activity_log_service
from autoarr.api.services.monitoring_service import MonitoringService
from autoarr.api.services.recovery_service import RecoveryService
from autoarr.api.services.websocket_manager import get_websocket_manager
from autoarr.api.database import DownloadMonitoringRepository, get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# ============================================================================
# Request/Response Models
# ============================================================================


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status."""

    running: bool = Field(..., description="Whether monitoring is running")
    poll_interval: int = Field(..., description="Polling interval in seconds")
    seen_failures: int = Field(..., description="Number of failures tracked")
    seen_wanted: int = Field(..., description="Number of wanted items tracked")


class RecoveryStatusResponse(BaseModel):
    """Response model for recovery service status."""

    running: bool = Field(..., description="Whether recovery is running")
    max_retries: int = Field(..., description="Maximum retry attempts")
    base_backoff: int = Field(..., description="Base backoff time in seconds")
    strategies: list[Dict[str, Any]] = Field(..., description="Available recovery strategies")


class ManualRetryRequest(BaseModel):
    """Request model for manual retry."""

    nzo_id: str = Field(..., description="NZO ID to retry")


class ActivityLogQuery(BaseModel):
    """Query parameters for activity log."""

    event_type: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    download_id: Optional[str] = None
    application: Optional[str] = None
    correlation_id: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


# ============================================================================
# Dependency Injection
# ============================================================================


# These would be properly injected via dependency injection in production
_monitoring_service: Optional[MonitoringService] = None
_recovery_service: Optional[RecoveryService] = None


def get_monitoring_service() -> MonitoringService:
    """Get monitoring service instance."""
    if _monitoring_service is None:
        raise HTTPException(status_code=503, detail="Monitoring service not initialized")
    return _monitoring_service


def get_recovery_service() -> RecoveryService:
    """Get recovery service instance."""
    if _recovery_service is None:
        raise HTTPException(status_code=503, detail="Recovery service not initialized")
    return _recovery_service


# ============================================================================
# Monitoring Endpoints
# ============================================================================


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status() -> Dict[str, Any]:
    """
    Get current monitoring service status.

    Returns status information about the monitoring service including
    polling interval and tracked items.
    """
    try:
        service = get_monitoring_service()
        return service.get_status()
    except HTTPException:
        # Return default status if service not initialized
        return {
            "running": False,
            "poll_interval": 120,
            "seen_failures": 0,
            "seen_wanted": 0,
        }


@router.get("/recovery/status", response_model=RecoveryStatusResponse)
async def get_recovery_status() -> Dict[str, Any]:
    """
    Get current recovery service status.

    Returns information about the recovery service including
    max retries, backoff settings, and available strategies.
    """
    try:
        service = get_recovery_service()
        return service.get_status()
    except HTTPException:
        # Return default status if service not initialized
        return {
            "running": False,
            "max_retries": 3,
            "base_backoff": 300,
            "strategies": [],
        }


@router.post("/retry/{nzo_id}")
async def manual_retry(nzo_id: str) -> Dict[str, Any]:
    """
    Manually trigger retry for a failed download.

    Resets retry count and immediately attempts recovery
    for the specified download.

    Args:
        nzo_id: NZO ID of the download to retry

    Returns:
        Result of the retry attempt
    """
    try:
        service = get_recovery_service()
        result = await service.manual_retry(nzo_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Manual retry failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failed")
async def get_failed_downloads(
    limit: int = Query(50, ge=1, le=100),
    exclude_dlq: bool = Query(True),
) -> Dict[str, Any]:
    """
    Get list of failed downloads.

    Returns downloads that have failed and may need retry or manual intervention.

    Args:
        limit: Maximum number of results to return
        exclude_dlq: Whether to exclude downloads in dead letter queue

    Returns:
        List of failed downloads
    """
    try:
        db = get_database()
        repo = DownloadMonitoringRepository(db)

        downloads = await repo.get_failed_downloads(
            limit=limit,
            exclude_dlq=exclude_dlq,
        )

        return {
            "downloads": [
                {
                    "nzo_id": d.nzo_id,
                    "filename": d.filename,
                    "source_application": d.source_application,
                    "status": d.status,
                    "failure_reason": d.failure_reason,
                    "retry_count": d.retry_count,
                    "max_retries": d.max_retries,
                    "created_at": d.created_at.isoformat(),
                    "last_retry_at": d.last_retry_at.isoformat() if d.last_retry_at else None,
                }
                for d in downloads
            ],
            "total": len(downloads),
        }
    except Exception as e:
        logger.error(f"Failed to get failed downloads: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dlq")
async def get_dlq_entries(
    limit: int = Query(50, ge=1, le=100),
) -> Dict[str, Any]:
    """
    Get downloads in dead letter queue.

    Returns downloads that have failed all recovery attempts and
    require manual intervention.

    Args:
        limit: Maximum number of results to return

    Returns:
        List of downloads in DLQ
    """
    try:
        db = get_database()
        repo = DownloadMonitoringRepository(db)

        downloads = await repo.get_dlq_entries(limit=limit)

        return {
            "downloads": [
                {
                    "nzo_id": d.nzo_id,
                    "filename": d.filename,
                    "source_application": d.source_application,
                    "failure_reason": d.failure_reason,
                    "dlq_reason": d.dlq_reason,
                    "retry_count": d.retry_count,
                    "created_at": d.created_at.isoformat(),
                    "dlq_timestamp": d.dlq_timestamp.isoformat() if d.dlq_timestamp else None,
                }
                for d in downloads
            ],
            "total": len(downloads),
        }
    except Exception as e:
        logger.error(f"Failed to get DLQ entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Activity Log Endpoints
# ============================================================================


@router.get("/activity")
async def get_activity_logs(
    event_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    download_id: Optional[str] = Query(None),
    application: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> Dict[str, Any]:
    """
    Query activity logs with filtering and pagination.

    Returns activity logs matching the specified filters,
    ordered by timestamp descending (most recent first).

    Args:
        event_type: Filter by event type
        source: Filter by source
        status: Filter by status
        download_id: Filter by download ID
        application: Filter by application
        correlation_id: Filter by correlation ID
        page: Page number (1-indexed)
        page_size: Results per page

    Returns:
        Paginated activity logs
    """
    try:
        service = get_activity_log_service()

        result = await service.query_logs(
            event_type=event_type,
            source=source,
            status=status,
            download_id=download_id,
            application=application,
            correlation_id=correlation_id,
            page=page,
            page_size=page_size,
        )

        return result
    except Exception as e:
        logger.error(f"Failed to query activity logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity/download/{download_id}")
async def get_download_timeline(
    download_id: str,
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Get complete timeline of events for a download.

    Returns all activity log entries related to a specific download,
    ordered chronologically.

    Args:
        download_id: Download ID (NZO ID)
        limit: Maximum number of events to return

    Returns:
        Download event timeline
    """
    try:
        service = get_activity_log_service()

        timeline = await service.get_download_timeline(
            download_id=download_id,
            limit=limit,
        )

        return {
            "download_id": download_id,
            "events": timeline,
            "total": len(timeline),
        }
    except Exception as e:
        logger.error(f"Failed to get download timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity/correlation/{correlation_id}")
async def get_correlation_timeline(
    correlation_id: str,
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Get complete timeline of events for a correlation ID.

    Returns all activity log entries with the same correlation ID,
    showing the complete flow of events.

    Args:
        correlation_id: Correlation ID
        limit: Maximum number of events to return

    Returns:
        Correlation event timeline
    """
    try:
        service = get_activity_log_service()

        timeline = await service.get_correlation_timeline(
            correlation_id=correlation_id,
            limit=limit,
        )

        return {
            "correlation_id": correlation_id,
            "events": timeline,
            "total": len(timeline),
        }
    except Exception as e:
        logger.error(f"Failed to get correlation timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity/stats")
async def get_activity_stats() -> Dict[str, Any]:
    """
    Get activity log statistics.

    Returns overall statistics about activity logs including
    total counts, success/failure rates, etc.

    Returns:
        Activity log statistics
    """
    try:
        service = get_activity_log_service()
        return await service.get_stats()
    except Exception as e:
        logger.error(f"Failed to get activity stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    Clients can connect to this endpoint to receive real-time updates
    about download failures, recoveries, and system events.

    Events are sent as JSON messages with the following structure:
    {
        "type": "event",
        "data": {
            "event_type": "download.failed",
            "payload": {...},
            "correlation_id": "...",
            "timestamp": "..."
        }
    }
    """
    manager = get_websocket_manager()

    await manager.connect(websocket)

    try:
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            data = await websocket.receive_text()

            # Handle ping
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
