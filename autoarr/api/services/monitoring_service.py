"""
Monitoring Service - SABnzbd Queue and Failure Detection.

Polls SABnzbd queue and history to detect failed downloads and wanted items.
Emits events for failures that require recovery actions. Implements
intelligent pattern recognition for failure categorization.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from autoarr.api.database import DownloadMonitoringRepository, Database, get_database
from autoarr.api.services.event_bus import EventBus, EventType, get_event_bus
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)


class FailurePattern:
    """Failure pattern for categorizing download failures."""

    def __init__(self, name: str, patterns: List[str], severity: str):
        """
        Initialize failure pattern.

        Args:
            name: Pattern name
            patterns: List of regex patterns
            severity: Severity level (critical, high, medium, low)
        """
        self.name = name
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.severity = severity

    def matches(self, message: str) -> bool:
        """Check if message matches any pattern."""
        return any(pattern.search(message) for pattern in self.patterns)


# Predefined failure patterns
FAILURE_PATTERNS = [
    FailurePattern(
        "incomplete",
        [r"incomplete", r"missing.*articles?", r"not.*enough.*blocks?"],
        "high",
    ),
    FailurePattern(
        "password_protected",
        [r"password.*required", r"encrypted", r"passworded"],
        "critical",
    ),
    FailurePattern(
        "unpacking_failed",
        [r"unpack.*failed", r"rar.*error", r"extraction.*failed"],
        "medium",
    ),
    FailurePattern(
        "duplicate",
        [r"duplicate", r"already.*exists?"],
        "low",
    ),
    FailurePattern(
        "disk_space",
        [r"disk.*full", r"no.*space", r"insufficient.*space"],
        "critical",
    ),
    FailurePattern(
        "virus_detected",
        [r"virus.*detected", r"malware", r"infected"],
        "critical",
    ),
    FailurePattern(
        "verification_failed",
        [r"verification.*failed", r"par.*check.*failed", r"crc.*error"],
        "high",
    ),
    FailurePattern(
        "propagation_delay",
        [r"propagation", r"not.*available.*yet", r"header.*not.*found"],
        "medium",
    ),
]


class MonitoringService:
    """
    Service for monitoring downloads and detecting failures.

    Polls SABnzbd queue and history at regular intervals, detects failures,
    categorizes them using pattern matching, and emits events for recovery.
    """

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        db: Optional[Database] = None,
        event_bus: Optional[EventBus] = None,
        poll_interval: int = 120,  # 2 minutes
    ):
        """
        Initialize monitoring service.

        Args:
            orchestrator: MCP orchestrator for API calls
            db: Database instance (uses global if not provided)
            event_bus: Event bus instance (uses global if not provided)
            poll_interval: Polling interval in seconds (default: 120)
        """
        self.orchestrator = orchestrator
        self.db = db or get_database()
        self.event_bus = event_bus or get_event_bus()
        self.poll_interval = poll_interval

        # Repository
        self.download_repository = DownloadMonitoringRepository(self.db)

        # Tracking
        self._seen_failures: Set[str] = set()
        self._seen_wanted: Set[str] = set()
        self._running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(f"MonitoringService initialized with {poll_interval}s poll interval")

    async def start(self) -> None:
        """Start the monitoring service."""
        if self._running:
            logger.warning("Monitoring service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())

        await self.event_bus.emit(
            EventType.MONITORING_STARTED,
            {"poll_interval": self.poll_interval, "timestamp": datetime.utcnow().isoformat()},
        )

        logger.info("Monitoring service started")

    async def stop(self) -> None:
        """Stop the monitoring service."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.event_bus.emit(
            EventType.MONITORING_STOPPED,
            {"timestamp": datetime.utcnow().isoformat()},
        )

        logger.info("Monitoring service stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._poll_queue()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await self.event_bus.emit(
                    EventType.SERVICE_ERROR,
                    {
                        "service": "monitoring",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                await asyncio.sleep(self.poll_interval)

    async def _poll_queue(self) -> None:
        """Poll SABnzbd queue and history for failures."""
        try:
            # Check if connected to SABnzbd
            if not await self.orchestrator.is_connected("sabnzbd"):
                logger.warning("SABnzbd not connected, attempting to connect...")
                await self.orchestrator.connect("sabnzbd")

            # Get queue
            queue_data = await self.orchestrator.call_tool(
                "sabnzbd",
                "get_queue",
                {},
            )

            # Get history
            history_data = await self.orchestrator.call_tool(
                "sabnzbd",
                "get_history",
                {"limit": 50},
            )

            # Process queue
            await self._process_queue(queue_data)

            # Process history for failures
            await self._process_history(history_data)

            # Check for wanted items
            await self._check_wanted_items()

            # Emit queue polled event
            await self.event_bus.emit(
                EventType.QUEUE_POLLED,
                {
                    "queue_size": len(queue_data.get("queue", {}).get("slots", [])),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error polling queue: {e}", exc_info=True)
            raise

    async def _process_queue(self, queue_data: Dict[str, Any]) -> None:
        """
        Process queue data.

        Args:
            queue_data: Queue data from SABnzbd
        """
        queue = queue_data.get("queue", {})
        slots = queue.get("slots", [])

        for slot in slots:
            nzo_id = slot.get("nzo_id")
            status = slot.get("status", "").lower()

            # Check for problematic statuses
            if status in ["paused", "failed"]:
                filename = slot.get("filename", "Unknown")
                logger.info(f"Queue item in problematic state: {filename} ({status})")

    async def _process_history(self, history_data: Dict[str, Any]) -> None:
        """
        Process history data and detect failures.

        Args:
            history_data: History data from SABnzbd
        """
        history = history_data.get("history", {})
        slots = history.get("slots", [])

        for slot in slots:
            nzo_id = slot.get("nzo_id")
            status = slot.get("status", "").lower()

            # Only process failures
            if status != "failed":
                continue

            # Skip if already seen
            if nzo_id in self._seen_failures:
                continue

            # Mark as seen
            self._seen_failures.add(nzo_id)

            # Extract failure details
            filename = slot.get("name", "Unknown")
            fail_message = slot.get("fail_message", "Unknown error")
            category = slot.get("category", "")

            # Categorize failure
            failure_category = self._categorize_failure(fail_message)

            # Determine source application from category
            source_application = self._determine_source_application(category)

            # Create or update download monitoring record
            await self.download_repository.create_or_update(
                nzo_id=nzo_id,
                filename=filename,
                source_application=source_application,
                status="failed",
                correlation_id=nzo_id,  # Use nzo_id as initial correlation
                category=category,
                failure_reason=fail_message,
                download_metadata=(
                    f'{{"failure_category": "'
                    f'{failure_category.name if failure_category else "unknown"}"}}'
                ),
            )

            # Emit failure event
            await self.event_bus.emit(
                EventType.DOWNLOAD_FAILED,
                {
                    "nzo_id": nzo_id,
                    "filename": filename,
                    "reason": fail_message,
                    "category": category,
                    "source_application": source_application,
                    "failure_category": failure_category.name if failure_category else "unknown",
                    "severity": failure_category.severity if failure_category else "medium",
                },
                correlation_id=nzo_id,
            )

            logger.info(
                f"Download failed detected: {filename} "
                f"(category: {failure_category.name if failure_category else 'unknown'})"
            )

    def _categorize_failure(self, fail_message: str) -> Optional[FailurePattern]:
        """
        Categorize failure using pattern matching.

        Args:
            fail_message: Failure message from SABnzbd

        Returns:
            Matching FailurePattern or None
        """
        for pattern in FAILURE_PATTERNS:
            if pattern.matches(fail_message):
                return pattern
        return None

    def _determine_source_application(self, category: str) -> str:
        """
        Determine source application from download category.

        Args:
            category: SABnzbd category

        Returns:
            Source application name
        """
        category_lower = category.lower()

        if "tv" in category_lower or "sonarr" in category_lower:
            return "sonarr"
        elif "movie" in category_lower or "radarr" in category_lower:
            return "radarr"
        else:
            return "unknown"

    async def _check_wanted_items(self) -> None:
        """Check Sonarr and Radarr for wanted items."""
        try:
            # Check Sonarr wanted
            if await self.orchestrator.is_connected("sonarr"):
                await self._check_sonarr_wanted()

            # Check Radarr wanted
            if await self.orchestrator.is_connected("radarr"):
                await self._check_radarr_wanted()

        except Exception as e:
            logger.error(f"Error checking wanted items: {e}", exc_info=True)

    async def _check_sonarr_wanted(self) -> None:
        """Check Sonarr for wanted episodes."""
        try:
            # This would call Sonarr's wanted/missing endpoint
            # For now, we'll skip this as it requires Sonarr API implementation
            pass
        except Exception as e:
            logger.error(f"Error checking Sonarr wanted: {e}", exc_info=True)

    async def _check_radarr_wanted(self) -> None:
        """Check Radarr for wanted movies."""
        try:
            # This would call Radarr's wanted/missing endpoint
            # For now, we'll skip this as it requires Radarr API implementation
            pass
        except Exception as e:
            logger.error(f"Error checking Radarr wanted: {e}", exc_info=True)

    async def manual_poll(self) -> Dict[str, Any]:
        """
        Manually trigger a queue poll.

        Returns:
            Poll results
        """
        await self._poll_queue()

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "seen_failures": len(self._seen_failures),
            "seen_wanted": len(self._seen_wanted),
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get monitoring service status.

        Returns:
            Status information
        """
        return {
            "running": self._running,
            "poll_interval": self.poll_interval,
            "seen_failures": len(self._seen_failures),
            "seen_wanted": len(self._seen_wanted),
        }

    def clear_seen_cache(self) -> None:
        """Clear seen failures and wanted items cache (for testing)."""
        self._seen_failures.clear()
        self._seen_wanted.clear()
        logger.info("Cleared seen cache")
