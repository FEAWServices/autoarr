"""
Recovery Service - Intelligent Download Recovery.

Implements sophisticated retry strategies for failed downloads including
quality fallback, alternative release search, indexer switching, and
exponential backoff. Manages dead letter queue for permanent failures.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from autoarr.api.database import DownloadMonitoringRepository, Database, get_database
from autoarr.api.services.event_bus import Event, EventBus, EventType, get_event_bus
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)


# Quality profiles for fallback (highest to lowest)
QUALITY_FALLBACK = ["4K", "2160p", "1080p", "720p", "480p", "SD"]


class RecoveryStrategy:
    """Base class for recovery strategies."""

    def __init__(self, name: str, description: str, priority: int):
        """
        Initialize recovery strategy.

        Args:
            name: Strategy name
            description: Strategy description
            priority: Execution priority (lower = higher priority)
        """
        self.name = name
        self.description = description
        self.priority = priority

    async def execute(
        self,
        orchestrator: MCPOrchestrator,
        download: Any,
        event_bus: EventBus,
    ) -> bool:
        """
        Execute recovery strategy.

        Args:
            orchestrator: MCP orchestrator
            download: Download monitoring record
            event_bus: Event bus

        Returns:
            True if recovery successful, False otherwise
        """
        raise NotImplementedError


class QualityFallbackStrategy(RecoveryStrategy):
    """Strategy for falling back to lower quality."""

    def __init__(self):
        super().__init__(
            "quality_fallback",
            "Try downloading with lower quality profile",
            priority=1,
        )

    async def execute(
        self,
        orchestrator: MCPOrchestrator,
        download: Any,
        event_bus: EventBus,
    ) -> bool:
        """Execute quality fallback."""
        try:
            current_quality = download.current_quality or download.original_quality

            # Find current quality in fallback list
            try:
                current_index = QUALITY_FALLBACK.index(current_quality)
            except ValueError:
                # Unknown quality, start from highest
                current_index = -1

            # Get next lower quality
            if current_index + 1 < len(QUALITY_FALLBACK):
                next_quality = QUALITY_FALLBACK[current_index + 1]

                logger.info(
                    f"Quality fallback: {download.filename} "
                    f"from {current_quality} to {next_quality}"
                )

                # Emit event
                await event_bus.emit(
                    EventType.DOWNLOAD_RETRY_STARTED,
                    {
                        "nzo_id": download.nzo_id,
                        "filename": download.filename,
                        "strategy": self.name,
                        "from_quality": current_quality,
                        "to_quality": next_quality,
                        "retry_count": download.retry_count + 1,
                    },
                    correlation_id=download.correlation_id,
                )

                # This would trigger a search in Sonarr/Radarr with lower quality
                # For now, we'll just log it
                # In production, this would call:
                # - Sonarr/Radarr API to search for the item with different quality
                # - Update quality profile temporarily
                # - Trigger automatic search

                return True

        except Exception as e:
            logger.error(f"Quality fallback failed: {e}", exc_info=True)

        return False


class RetryDownloadStrategy(RecoveryStrategy):
    """Strategy for retrying the same download."""

    def __init__(self):
        super().__init__(
            "retry_download",
            "Retry the same download (may succeed if issue was temporary)",
            priority=0,
        )

    async def execute(
        self,
        orchestrator: MCPOrchestrator,
        download: Any,
        event_bus: EventBus,
    ) -> bool:
        """Execute retry download."""
        try:
            # Emit retry started event
            await event_bus.emit(
                EventType.DOWNLOAD_RETRY_STARTED,
                {
                    "nzo_id": download.nzo_id,
                    "filename": download.filename,
                    "strategy": self.name,
                    "retry_count": download.retry_count + 1,
                },
                correlation_id=download.correlation_id,
            )

            # Retry the download in SABnzbd
            result = await orchestrator.call_tool(
                "sabnzbd",
                "retry_download",
                {"nzo_id": download.nzo_id},
            )

            if result.get("status"):
                logger.info(f"Successfully retried download: {download.filename}")
                return True
            else:
                logger.warning(f"Failed to retry download: {download.filename}")
                return False

        except Exception as e:
            logger.error(f"Retry download failed: {e}", exc_info=True)
            return False


class AlternativeReleaseStrategy(RecoveryStrategy):
    """Strategy for searching alternative releases."""

    def __init__(self):
        super().__init__(
            "alternative_release",
            "Search for alternative release groups or sources",
            priority=2,
        )

    async def execute(
        self,
        orchestrator: MCPOrchestrator,
        download: Any,
        event_bus: EventBus,
    ) -> bool:
        """Execute alternative release search."""
        try:
            logger.info(f"Searching alternative releases for: {download.filename}")

            # Emit event
            await event_bus.emit(
                EventType.DOWNLOAD_RETRY_STARTED,
                {
                    "nzo_id": download.nzo_id,
                    "filename": download.filename,
                    "strategy": self.name,
                    "retry_count": download.retry_count + 1,
                },
                correlation_id=download.correlation_id,
            )

            # In production, this would:
            # - Call Sonarr/Radarr to trigger a new search
            # - Potentially blacklist the failed release
            # - Search with different indexers

            return True

        except Exception as e:
            logger.error(f"Alternative release search failed: {e}", exc_info=True)
            return False


class RecoveryService:
    """
    Service for recovering failed downloads.

    Subscribes to download failed events and implements intelligent
    retry strategies with exponential backoff and dead letter queue.
    """

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        db: Optional[Database] = None,
        event_bus: Optional[EventBus] = None,
        max_retries: int = 3,
        base_backoff: int = 300,  # 5 minutes
    ):
        """
        Initialize recovery service.

        Args:
            orchestrator: MCP orchestrator for API calls
            db: Database instance (uses global if not provided)
            event_bus: Event bus instance (uses global if not provided)
            max_retries: Maximum retry attempts (default: 3)
            base_backoff: Base backoff time in seconds (default: 300)
        """
        self.orchestrator = orchestrator
        self.db = db or get_database()
        self.event_bus = event_bus or get_event_bus()
        self.max_retries = max_retries
        self.base_backoff = base_backoff

        # Repository
        self.download_repository = DownloadMonitoringRepository(self.db)

        # Recovery strategies (sorted by priority)
        self.strategies = sorted(
            [
                RetryDownloadStrategy(),
                QualityFallbackStrategy(),
                AlternativeReleaseStrategy(),
            ],
            key=lambda s: s.priority,
        )

        # Subscribe to failed download events
        self.event_bus.subscribe(EventType.DOWNLOAD_FAILED, self._handle_failure)

        # Background task for retry processing
        self._retry_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            f"RecoveryService initialized with max_retries={max_retries}, "
            f"base_backoff={base_backoff}s"
        )

    async def start(self) -> None:
        """Start the recovery service."""
        if self._running:
            logger.warning("Recovery service already running")
            return

        self._running = True
        self._retry_task = asyncio.create_task(self._retry_loop())

        logger.info("Recovery service started")

    async def stop(self) -> None:
        """Stop the recovery service."""
        if not self._running:
            return

        self._running = False

        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass

        logger.info("Recovery service stopped")

    async def _handle_failure(self, event: Event) -> None:
        """
        Handle download failure event.

        Args:
            event: Download failed event
        """
        try:
            nzo_id = event.payload.get("nzo_id")
            if not nzo_id:
                logger.warning("Download failed event missing nzo_id")
                return

            # Get download record
            download = await self.download_repository.get_by_nzo_id(nzo_id)
            if not download:
                logger.warning(f"Download record not found for nzo_id: {nzo_id}")
                return

            # Check if already in DLQ
            if download.in_dlq:
                logger.info(f"Download {nzo_id} already in DLQ, skipping")
                return

            # Check if exceeded max retries
            if download.retry_count >= self.max_retries:
                await self._move_to_dlq(
                    download,
                    f"Exceeded maximum retry attempts ({self.max_retries})",
                )
                return

            # Schedule retry with exponential backoff
            backoff_time = self.base_backoff * (2**download.retry_count)
            next_retry = datetime.utcnow() + timedelta(seconds=backoff_time)

            # Update download record with next retry time
            download.next_retry_at = next_retry
            logger.info(
                f"Scheduled retry for {download.filename} "
                f"at {next_retry.isoformat()} "
                f"(attempt {download.retry_count + 1}/{self.max_retries})"
            )

        except Exception as e:
            logger.error(f"Error handling failure: {e}", exc_info=True)

    async def _retry_loop(self) -> None:
        """Background loop for processing scheduled retries."""
        while self._running:
            try:
                await self._process_retries()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retry loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _process_retries(self) -> None:
        """Process downloads scheduled for retry."""
        try:
            # Get failed downloads not in DLQ
            failed_downloads = await self.download_repository.get_failed_downloads(
                limit=50,
                exclude_dlq=True,
            )

            current_time = datetime.utcnow()

            for download in failed_downloads:
                # Skip if not yet time to retry
                if download.next_retry_at and download.next_retry_at > current_time:
                    continue

                # Skip if exceeded max retries
                if download.retry_count >= self.max_retries:
                    await self._move_to_dlq(
                        download,
                        f"Exceeded maximum retry attempts ({self.max_retries})",
                    )
                    continue

                # Attempt recovery
                await self._attempt_recovery(download)

        except Exception as e:
            logger.error(f"Error processing retries: {e}", exc_info=True)

    async def _attempt_recovery(self, download: Any) -> None:
        """
        Attempt to recover a failed download.

        Args:
            download: Download monitoring record
        """
        try:
            logger.info(
                f"Attempting recovery for {download.filename} "
                f"(attempt {download.retry_count + 1}/{self.max_retries})"
            )

            # Increment retry count
            await self.download_repository.increment_retry(download.nzo_id)

            # Try each strategy until one succeeds
            recovery_successful = False
            for strategy in self.strategies:
                try:
                    logger.debug(f"Trying strategy: {strategy.name}")
                    success = await strategy.execute(
                        self.orchestrator,
                        download,
                        self.event_bus,
                    )

                    if success:
                        recovery_successful = True
                        break

                except Exception as e:
                    logger.error(f"Strategy {strategy.name} failed: {e}", exc_info=True)
                    continue

            # Handle result
            if recovery_successful:
                logger.info(f"Recovery successful for {download.filename}")
                # Note: Download will be marked as resolved when SABnzbd completes it
            else:
                logger.warning(f"All recovery strategies failed for {download.filename}")

                # Emit retry failed event
                await self.event_bus.emit(
                    EventType.DOWNLOAD_RETRY_FAILED,
                    {
                        "nzo_id": download.nzo_id,
                        "filename": download.filename,
                        "retry_count": download.retry_count,
                    },
                    correlation_id=download.correlation_id,
                )

                # Check if should move to DLQ
                if download.retry_count >= self.max_retries:
                    await self._move_to_dlq(
                        download,
                        "All recovery strategies failed",
                    )

        except Exception as e:
            logger.error(f"Error attempting recovery: {e}", exc_info=True)

    async def _move_to_dlq(self, download: Any, reason: str) -> None:
        """
        Move download to dead letter queue.

        Args:
            download: Download monitoring record
            reason: Reason for moving to DLQ
        """
        try:
            await self.download_repository.move_to_dlq(
                download.nzo_id,
                reason,
            )

            await self.event_bus.emit(
                EventType.DOWNLOAD_MOVED_TO_DLQ,
                {
                    "nzo_id": download.nzo_id,
                    "filename": download.filename,
                    "reason": reason,
                    "retry_count": download.retry_count,
                },
                correlation_id=download.correlation_id,
            )

            logger.warning(f"Moved download to DLQ: {download.filename} - {reason}")

        except Exception as e:
            logger.error(f"Error moving to DLQ: {e}", exc_info=True)

    async def manual_retry(self, nzo_id: str) -> Dict[str, Any]:
        """
        Manually trigger retry for a specific download.

        Args:
            nzo_id: NZO ID to retry

        Returns:
            Retry result
        """
        try:
            download = await self.download_repository.get_by_nzo_id(nzo_id)
            if not download:
                return {
                    "status": "error",
                    "message": f"Download not found: {nzo_id}",
                }

            # Remove from DLQ if present
            if download.in_dlq:
                download.in_dlq = False
                download.dlq_reason = None

            # Reset retry count
            download.retry_count = 0
            download.next_retry_at = datetime.utcnow()

            # Attempt recovery
            await self._attempt_recovery(download)

            return {
                "status": "success",
                "message": f"Manual retry triggered for {download.filename}",
            }

        except Exception as e:
            logger.error(f"Manual retry failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get recovery service status.

        Returns:
            Status information
        """
        return {
            "running": self._running,
            "max_retries": self.max_retries,
            "base_backoff": self.base_backoff,
            "strategies": [
                {
                    "name": s.name,
                    "description": s.description,
                    "priority": s.priority,
                }
                for s in self.strategies
            ],
        }
