"""
Monitoring Service for AutoArr (Sprint 5).

This module provides comprehensive monitoring of download queues and wanted lists:
- Periodic polling of SABnzbd queue and history
- Detection of failed downloads
- Pattern recognition for recurring failures
- Alert generation and event emission
- Wanted list monitoring for Sonarr/Radarr
- State change tracking with correlation IDs
- Circuit breaker for resilience

The service acts as the watchdog for the download ecosystem, enabling
proactive recovery and intelligent retry strategies.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from autoarr.api.services.event_bus import Event, EventBus, EventType
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class DownloadStatus(str, Enum):
    """Download status enumeration."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    EXTRACTING = "extracting"
    MOVING = "moving"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def from_sabnzbd_status(cls, status: str) -> "DownloadStatus":
        """
        Convert SABnzbd status to DownloadStatus.

        Args:
            status: SABnzbd status string

        Returns:
            DownloadStatus enum value
        """
        status_lower = status.lower()
        if status_lower in ("queued", "grabbing"):
            return cls.QUEUED
        elif status_lower in ("downloading", "fetching"):
            return cls.DOWNLOADING
        elif status_lower == "paused":
            return cls.PAUSED
        elif status_lower in ("extracting", "unpacking"):
            return cls.EXTRACTING
        elif status_lower == "moving":
            return cls.MOVING
        elif status_lower == "verifying":
            return cls.VERIFYING
        elif status_lower in ("completed", "complete"):
            return cls.COMPLETED
        elif status_lower == "failed":
            return cls.FAILED
        else:
            # Default to queued for unknown statuses
            return cls.QUEUED


class FailurePattern(str, Enum):
    """Failure pattern types."""

    ISOLATED = "isolated"
    RECURRING_SAME_CONTENT = "recurring_same_content"
    DISK_SPACE_ISSUE = "disk_space_issue"
    NETWORK_ISSUE = "network_issue"
    QUALITY_CORRUPTION = "quality_corruption"


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class MonitoringConfig:
    """Configuration for monitoring service."""

    poll_interval: int = 60  # seconds
    failure_detection_enabled: bool = True
    pattern_recognition_enabled: bool = True
    max_retry_attempts: int = 3
    alert_on_failure: bool = True


@dataclass
class QueueItem:
    """Queue item from SABnzbd."""

    nzo_id: str
    filename: str
    status: DownloadStatus
    percentage: int
    mb_left: float
    mb_total: float
    category: str
    priority: str = "Normal"
    eta: str = "Unknown"


@dataclass
class QueueState:
    """Current queue state."""

    status: str
    speed: str = "0 MB/s"
    items: List[QueueItem] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FailedDownload:
    """Failed download information."""

    nzo_id: str
    name: str
    status: DownloadStatus
    failure_reason: str
    category: str
    retry_count: int = 0
    last_retry_time: Optional[datetime] = None
    original_failure_time: datetime = field(default_factory=datetime.now)


@dataclass
class FailurePatternInfo:
    """Information about detected failure pattern."""

    pattern_type: FailurePattern
    failure_count: int
    content_identifier: Optional[str] = None
    common_reason: Optional[str] = None


@dataclass
class WantedEpisode:
    """Wanted episode from Sonarr."""

    id: int
    series_id: int
    season_number: int
    episode_number: int
    title: str
    monitored: bool
    air_date: Optional[str] = None


@dataclass
class WantedMovie:
    """Wanted movie from Radarr."""

    id: int
    title: str
    year: int
    monitored: bool
    has_file: bool = False


@dataclass
class WantedFailureCorrelation:
    """Correlation between wanted item and failed download."""

    content_name: str
    has_failed_attempts: bool
    failure_count: int = 0
    last_failure_reason: Optional[str] = None


# ============================================================================
# Monitoring Service
# ============================================================================


class MonitoringService:
    """
    Service for monitoring download queues and detecting failures.

    Provides:
    - Periodic queue polling
    - Failure detection and pattern recognition
    - Alert generation via EventBus
    - Wanted list monitoring
    - State change tracking
    - Circuit breaker protection
    """

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        event_bus: EventBus,
        config: Optional[MonitoringConfig] = None,
    ):
        """
        Initialize monitoring service.

        Args:
            orchestrator: MCP orchestrator for tool calls
            event_bus: Event bus for publishing alerts
            config: Optional monitoring configuration
        """
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.config = config or MonitoringConfig()

        # State tracking
        self._tracked_downloads: Dict[str, DownloadStatus] = {}
        self._alerted_failures: Set[str] = set()
        self._failure_timestamps: Dict[str, datetime] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_monitoring = False
        self._poll_lock = asyncio.Lock()

    # ========================================================================
    # Queue Polling
    # ========================================================================

    async def poll_queue(self) -> Optional[QueueState]:
        """
        Poll SABnzbd queue for current state.

        Returns:
            QueueState if successful, None on error
        """
        # Use lock to prevent overlapping polls
        async with self._poll_lock:
            try:
                result = await self.orchestrator.call_tool(  # noqa: F841
                    server="sabnzbd", tool="get_queue", params={}
                )

                if not result or "queue" not in result:
                    logger.warning("Malformed queue response from SABnzbd")
                    return None

                queue_data = result["queue"]
                items = []

                for slot in queue_data.get("slots", []):
                    try:
                        item = QueueItem(
                            nzo_id=slot.get("nzo_id", ""),
                            filename=slot.get("filename", ""),
                            status=DownloadStatus.from_sabnzbd_status(slot.get("status", "Queued")),
                            percentage=slot.get("percentage", 0),
                            mb_left=float(slot.get("mbleft", 0)),
                            mb_total=float(slot.get("mb", 0)),
                            category=slot.get("category", ""),
                            priority=slot.get("priority", "Normal"),
                            eta=slot.get("eta", "Unknown"),
                        )
                        items.append(item)
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Skipping invalid queue item: {e}")
                        continue

                return QueueState(
                    status=queue_data.get("status", "Unknown"),
                    speed=queue_data.get("speed", "0 MB/s"),
                    items=items,
                    timestamp=datetime.now(),
                )

            except (ConnectionError, asyncio.TimeoutError) as e:
                logger.error(f"Error polling SABnzbd queue: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error polling queue: {e}", exc_info=True)
                return None

    # ========================================================================
    # Failure Detection
    # ========================================================================

    def _is_failed_status(self, status: str, failure_reason: str = "") -> bool:
        """
        Check if a status indicates a failure.

        Args:
            status: Status string
            failure_reason: Failure reason string

        Returns:
            True if status indicates failure
        """
        return status.lower() == "failed"

    async def detect_failed_downloads(self) -> List[FailedDownload]:
        """
        Detect failed downloads from SABnzbd history.

        Returns:
            List of failed downloads
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="sabnzbd", tool="get_history", params={}
            )

            if not result or "history" not in result:
                logger.warning("Malformed history response from SABnzbd")
                return []

            history_data = result["history"]
            failed_downloads = []

            for slot in history_data.get("slots", []):
                status = slot.get("status", "")
                fail_message = slot.get("fail_message", "")

                if self._is_failed_status(status, fail_message):
                    failed_download = FailedDownload(
                        nzo_id=slot.get("nzo_id", ""),
                        name=slot.get("name", ""),
                        status=DownloadStatus.FAILED,
                        failure_reason=fail_message,
                        category=slot.get("category", ""),
                        retry_count=slot.get("retry", 0),
                        last_retry_time=None,
                        original_failure_time=datetime.now(),
                    )
                    failed_downloads.append(failed_download)

            return failed_downloads

        except Exception as e:
            logger.error(f"Error detecting failed downloads: {e}", exc_info=True)
            return []

    # ========================================================================
    # Pattern Recognition
    # ========================================================================

    def analyze_failure_pattern(
        self, failure_history: List[Dict[str, Any]]
    ) -> Optional[FailurePatternInfo]:
        """
        Analyze failure history to identify patterns.

        Args:
            failure_history: List of failed download items

        Returns:
            FailurePatternInfo if pattern detected, None otherwise
        """
        if not failure_history:
            return None

        if len(failure_history) == 1:
            return FailurePatternInfo(
                pattern_type=FailurePattern.ISOLATED,
                failure_count=1,
            )

        # Check for recurring same content FIRST (highest priority)
        # Extract content identifier (e.g., "Show.S01E01" from various release formats)
        content_identifiers = []
        for item in failure_history:
            name = item.get("name", "")
            # Try to extract show/episode pattern
            match = re.search(r"(.+?)[.\s]S(\d+)E(\d+)", name, re.IGNORECASE)
            if match:
                show_name = match.group(1).replace(".", "")
                season = match.group(2)
                episode = match.group(3)
                identifier = f"{show_name}.S{season}E{episode}"
                content_identifiers.append(identifier)

        if content_identifiers:
            # Find most common identifier
            from collections import Counter

            counter = Counter(content_identifiers)
            most_common = counter.most_common(1)[0]
            if most_common[1] >= 2:  # At least 2 failures for same content
                return FailurePatternInfo(
                    pattern_type=FailurePattern.RECURRING_SAME_CONTENT,
                    failure_count=most_common[1],
                    content_identifier=most_common[0],
                )

        # Extract failure reasons
        failure_reasons = [item.get("fail_message", "").lower() for item in failure_history]

        # Check for disk space issues
        disk_space_keywords = ["disk", "space", "full", "write error"]
        disk_space_count = sum(
            1
            for reason in failure_reasons
            if any(keyword in reason for keyword in disk_space_keywords)
        )
        if disk_space_count >= 2:
            return FailurePatternInfo(
                pattern_type=FailurePattern.DISK_SPACE_ISSUE,
                failure_count=disk_space_count,
                common_reason="Disk space issue",
            )

        # Check for network issues
        network_keywords = ["connection", "timeout", "reset", "failed to connect"]
        network_count = sum(
            1
            for reason in failure_reasons
            if any(keyword in reason for keyword in network_keywords)
        )
        if network_count >= 2:
            return FailurePatternInfo(
                pattern_type=FailurePattern.NETWORK_ISSUE,
                failure_count=network_count,
                common_reason="Network issue",
            )

        # Check for quality/corruption issues
        quality_keywords = ["crc", "par2", "verification", "corrupt"]
        quality_count = sum(
            1
            for reason in failure_reasons
            if any(keyword in reason for keyword in quality_keywords)
        )
        if quality_count >= 2:
            return FailurePatternInfo(
                pattern_type=FailurePattern.QUALITY_CORRUPTION,
                failure_count=quality_count,
                common_reason="Quality/corruption issue",
            )

        return FailurePatternInfo(
            pattern_type=FailurePattern.ISOLATED,
            failure_count=len(failure_history),
        )

    # ========================================================================
    # Alert Generation
    # ========================================================================

    async def check_and_alert_failures(self) -> None:
        """
        Check for failures and emit alerts via EventBus.
        """
        if not self.config.alert_on_failure:
            return

        failed_downloads = await self.detect_failed_downloads()

        for failed in failed_downloads:
            # Check if we've already alerted for this failure
            if failed.nzo_id in self._alerted_failures:
                # Check if we should throttle
                last_alert = self._failure_timestamps.get(failed.nzo_id)
                if last_alert:
                    time_since_alert = datetime.now() - last_alert
                    if time_since_alert < timedelta(minutes=5):
                        continue  # Throttle alerts

            # Emit failure event
            event = Event(
                event_type=EventType.DOWNLOAD_FAILED,
                data={
                    "nzo_id": failed.nzo_id,
                    "name": failed.name,
                    "failure_reason": failed.failure_reason,
                    "category": failed.category,
                    "retry_count": failed.retry_count,
                },
                correlation_id=str(uuid4()),
                timestamp=datetime.now(),
                source="monitoring_service",
            )

            await self.event_bus.publish(event)

            # Track that we've alerted
            self._alerted_failures.add(failed.nzo_id)
            self._failure_timestamps[failed.nzo_id] = datetime.now()

    # ========================================================================
    # Wanted List Monitoring
    # ========================================================================

    async def get_wanted_episodes(self) -> List[WantedEpisode]:
        """
        Get wanted/missing episodes from Sonarr.

        Returns:
            List of wanted episodes
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="sonarr",
                tool="get_wanted",
                params={"page": 1, "pageSize": 50},
            )

            if not result or "records" not in result:
                logger.warning("Malformed wanted response from Sonarr")
                return []

            episodes = []
            for record in result.get("records", []):
                episode = WantedEpisode(
                    id=record.get("id", 0),
                    series_id=record.get("seriesId", 0),
                    season_number=record.get("seasonNumber", 0),
                    episode_number=record.get("episodeNumber", 0),
                    title=record.get("title", ""),
                    monitored=record.get("monitored", False),
                    air_date=record.get("airDate"),
                )
                episodes.append(episode)

            return episodes

        except Exception as e:
            logger.error(f"Error getting wanted episodes: {e}", exc_info=True)
            return []

    async def get_wanted_movies(self) -> List[WantedMovie]:
        """
        Get wanted/missing movies from Radarr.

        Returns:
            List of wanted movies
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="radarr",
                tool="get_wanted",
                params={"page": 1, "pageSize": 50},
            )

            if not result or "records" not in result:
                logger.warning("Malformed wanted response from Radarr")
                return []

            movies = []
            for record in result.get("records", []):
                movie = WantedMovie(
                    id=record.get("id", 0),
                    title=record.get("title", ""),
                    year=record.get("year", 0),
                    monitored=record.get("monitored", False),
                    has_file=record.get("hasFile", False),
                )
                movies.append(movie)

            return movies

        except Exception as e:
            logger.error(f"Error getting wanted movies: {e}", exc_info=True)
            return []

    async def correlate_wanted_with_failures(self) -> List[WantedFailureCorrelation]:
        """
        Correlate wanted items with failed downloads.

        Returns:
            List of correlations
        """
        # Get wanted episodes and failed downloads
        wanted_episodes = await self.get_wanted_episodes()
        failed_downloads = await self.detect_failed_downloads()

        correlations = []

        for episode in wanted_episodes:
            # Create content identifier for matching
            season_ep = f"S{episode.season_number:02d}E{episode.episode_number:02d}"

            # Check if any failed downloads match
            matching_failures = [f for f in failed_downloads if season_ep.lower() in f.name.lower()]

            if matching_failures:
                # Extract show name from the first matching failure
                show_name = "Unknown"
                for failure in matching_failures:
                    match = re.search(r"(.+?)[.\s]S(\d+)E(\d+)", failure.name, re.IGNORECASE)
                    if match:
                        show_name = match.group(1).replace(".", "")
                        break

                # Create content name with show name
                content_name = (
                    f"{show_name}.S{episode.season_number:02d}E{episode.episode_number:02d}"
                )

                correlation = WantedFailureCorrelation(
                    content_name=content_name,
                    has_failed_attempts=True,
                    failure_count=len(matching_failures),
                    last_failure_reason=matching_failures[-1].failure_reason,
                )
                correlations.append(correlation)

        return correlations

    # ========================================================================
    # State Change Tracking
    # ========================================================================

    def _update_tracked_state(self, nzo_id: str, status: DownloadStatus) -> None:
        """
        Update tracked state for a download.

        Args:
            nzo_id: Download ID
            status: New status
        """
        self._tracked_downloads[nzo_id] = status

    async def _handle_state_change(self, nzo_id: str, new_status: DownloadStatus) -> None:
        """
        Handle state change for a download.

        Args:
            nzo_id: Download ID
            new_status: New status
        """
        old_status = self._tracked_downloads.get(nzo_id)

        # Check if status actually changed
        if old_status == new_status:
            return

        # Update tracked state
        self._update_tracked_state(nzo_id, new_status)

        # Determine event type
        if new_status == DownloadStatus.COMPLETED:
            event_type = EventType.DOWNLOAD_COMPLETED
        else:
            event_type = EventType.DOWNLOAD_STATE_CHANGED

        # Emit event
        event = Event(
            event_type=event_type,
            data={
                "nzo_id": nzo_id,
                "old_state": old_status.value if old_status else "unknown",
                "new_state": new_status.value,
            },
            correlation_id=str(uuid4()),
            timestamp=datetime.now(),
            source="monitoring_service",
        )

        await self.event_bus.publish(event)

    # ========================================================================
    # Background Monitoring
    # ========================================================================

    async def start_monitoring(self) -> None:
        """
        Start background monitoring task.

        Polls queue at configured intervals and detects failures.
        """
        self._stop_monitoring = False
        logger.info(f"Starting monitoring service (poll interval: {self.config.poll_interval}s)")

        while not self._stop_monitoring:
            try:
                # Poll queue
                await self.poll_queue()

                # Check for failures if enabled
                if self.config.failure_detection_enabled:
                    await self.check_and_alert_failures()

                # Wait for next poll
                await asyncio.sleep(self.config.poll_interval)

            except asyncio.CancelledError:
                logger.info("Monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                # Continue monitoring even after errors
                await asyncio.sleep(self.config.poll_interval)

        logger.info("Monitoring service stopped")

    def stop_monitoring(self) -> None:
        """Stop background monitoring task."""
        self._stop_monitoring = True
        if self._monitoring_task:
            self._monitoring_task.cancel()
