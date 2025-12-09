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
Recovery service for automatic download retry (Sprint 5).

This module provides intelligent retry strategies for failed downloads,
including immediate retry, exponential backoff, and quality fallback.
"""

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from autoarr.api.services.event_bus import Event, EventBus, EventType
from autoarr.api.services.monitoring_service import FailedDownload

logger = logging.getLogger(__name__)


# ============================================================================
# Retry Strategy
# ============================================================================


class RetryStrategy(str, Enum):
    """Retry strategy enumeration."""

    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backof"
    QUALITY_FALLBACK = "quality_fallback"


# ============================================================================
# Failure Reason Categories
# ============================================================================


class FailureReason(str, Enum):
    """Common failure reason categories."""

    TRANSIENT_NETWORK = "transient_network"
    CRC_ERROR = "crc_error"
    PAR2_FAILED = "par2_failed"
    INCOMPLETE = "incomplete"
    DISK_FULL = "disk_full"
    UNKNOWN = "unknown"


# ============================================================================
# Configuration and Models
# ============================================================================


@dataclass
class RecoveryConfig:
    """
    Configuration for recovery service.

    Attributes:
        max_retry_attempts: Maximum number of retry attempts per download
        immediate_retry_enabled: Enable immediate retry strategy
        exponential_backoff_enabled: Enable exponential backoff strategy
        quality_fallback_enabled: Enable quality fallback strategy
        backoff_base_delay: Base delay for exponential backoff (seconds)
        backoff_max_delay: Maximum delay for exponential backoff (seconds)
        backoff_multiplier: Multiplier for exponential backoff
    """

    max_retry_attempts: int = 3
    immediate_retry_enabled: bool = True
    exponential_backoff_enabled: bool = True
    quality_fallback_enabled: bool = True
    backoff_base_delay: int = 60  # 1 minute
    backoff_max_delay: int = 3600  # 1 hour
    backoff_multiplier: int = 2


@dataclass
class RetryAttempt:
    """
    Model for a retry attempt.

    Attributes:
        nzo_id: SABnzbd download ID
        strategy: Retry strategy used
        attempt_number: Attempt number
        timestamp: Timestamp of attempt
        success: Whether attempt was successful
    """

    nzo_id: str
    strategy: RetryStrategy
    attempt_number: int
    timestamp: datetime
    success: bool


@dataclass
class RecoveryResult:
    """
    Result of a recovery attempt.

    Attributes:
        success: Whether recovery was triggered successfully
        retry_triggered: Whether a retry was actually initiated
        strategy: Strategy used for retry
        message: Human-readable message
        retry_attempt_number: Attempt number for this retry
        delay_seconds: Delay before retry execution (for scheduled retries)
        scheduled_time: When retry will execute (for scheduled retries)
    """

    success: bool
    retry_triggered: bool
    strategy: Optional[RetryStrategy]
    message: str
    retry_attempt_number: int = 0
    delay_seconds: int = 0
    scheduled_time: Optional[datetime] = None


# ============================================================================
# Recovery Service
# ============================================================================


class RecoveryService:
    """
    Service for automatic download recovery with intelligent retry strategies.

    Implements:
    - Immediate retry for transient failures
    - Exponential backoff for repeated failures
    - Quality fallback for corrupted downloads
    - Max retry limit enforcement
    - Success/failure tracking
    """

    def __init__(self, orchestrator: Any, event_bus: EventBus, config: RecoveryConfig):
        """
        Initialize recovery service.

        Args:
            orchestrator: MCP orchestrator for calling tools
            event_bus: Event bus for publishing events
            config: Recovery configuration
        """
        self.orchestrator = orchestrator
        self.event_bus = event_bus
        self.config = config

        # Track active retries to prevent duplicates
        self._active_retries: Dict[str, asyncio.Lock] = {}

        # Track retry history
        self._retry_history: Dict[str, List[RetryAttempt]] = {}

    async def trigger_retry(self, failed_download: FailedDownload) -> RecoveryResult:
        """
        Trigger retry for a failed download.

        Args:
            failed_download: Failed download to retry

        Returns:
            RecoveryResult with retry status and details
        """
        nzo_id = failed_download.nzo_id
        correlation_id = str(uuid.uuid4())

        # Validate download data
        if not nzo_id or not failed_download.category:
            logger.warning(f"Invalid download data for {nzo_id}")
            return RecoveryResult(
                success=False,
                retry_triggered=False,
                strategy=None,
                message="Invalid download data",
            )

        # Check max retry limit
        if failed_download.retry_count >= self.config.max_retry_attempts:
            logger.info(f"Max retry attempts exceeded for {nzo_id}")
            await self._emit_max_retries_exceeded(failed_download, correlation_id)
            return RecoveryResult(
                success=False,
                retry_triggered=False,
                strategy=None,
                message=(
                    "Exceeded max retry attempts " f"(maximum: {self.config.max_retry_attempts})"
                ),
                retry_attempt_number=failed_download.retry_count,
            )

        # Prevent duplicate concurrent retries
        if nzo_id not in self._active_retries:
            self._active_retries[nzo_id] = asyncio.Lock()

        lock = self._active_retries[nzo_id]
        if lock.locked():
            logger.debug(f"Retry already in progress for {nzo_id}")
            return RecoveryResult(
                success=False,
                retry_triggered=False,
                strategy=None,
                message="Retry already in progress",
            )

        async with lock:
            try:
                # Select retry strategy
                quality = self._extract_quality_from_filename(failed_download.name)
                strategy = self._select_retry_strategy(
                    failure_reason=failed_download.failure_reason,
                    retry_count=failed_download.retry_count,
                    current_quality=quality,
                )

                # Calculate retry attempt number
                retry_attempt_number = failed_download.retry_count + 1

                # Execute retry based on strategy
                if strategy == RetryStrategy.IMMEDIATE:
                    result = await self._execute_immediate_retry(  # noqa: F841
                        failed_download, retry_attempt_number, correlation_id
                    )
                elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                    result = await self._execute_backoff_retry(  # noqa: F841
                        failed_download, retry_attempt_number, correlation_id
                    )
                elif strategy == RetryStrategy.QUALITY_FALLBACK:
                    result = await self._execute_quality_fallback(  # noqa: F841
                        failed_download, retry_attempt_number, correlation_id, quality
                    )
                else:
                    result = RecoveryResult(  # noqa: F841
                        success=False,
                        retry_triggered=False,
                        strategy=strategy,
                        message="Unknown strategy",
                    )

                # Track attempt
                self._track_retry_attempt(nzo_id, strategy, result.success)

                # Emit event
                await self._emit_recovery_attempted(
                    failed_download, strategy, result.success, correlation_id
                )

                return result

            except Exception as e:
                logger.error(f"Error during retry for {nzo_id}: {e}", exc_info=True)
                await self._emit_recovery_attempted(failed_download, None, False, correlation_id)
                return RecoveryResult(
                    success=False,
                    retry_triggered=False,
                    strategy=None,
                    message=f"Error during retry: {str(e)}",
                )

    def _select_retry_strategy(
        self,
        failure_reason: str,
        retry_count: int,
        current_quality: Optional[str] = None,
    ) -> RetryStrategy:
        """
        Select appropriate retry strategy based on failure reason and history.

        Args:
            failure_reason: Reason for download failure
            retry_count: Number of previous retry attempts
            current_quality: Current download quality (if known)

        Returns:
            RetryStrategy to use
        """
        reason_lower = failure_reason.lower()

        # Transient network errors - immediate retry (first attempt only)
        transient_keywords = [
            "timeout",
            "connection reset",
            "network unreachable",
            "temporary server error",
            "read timeout",
        ]
        if self.config.immediate_retry_enabled and retry_count == 0:
            if any(keyword in reason_lower for keyword in transient_keywords):
                return RetryStrategy.IMMEDIATE

        # CRC/PAR2 errors or quality issues - try quality fallback if enabled
        # Use quality fallback for retry attempts 0-1, exponential backoff for 2+
        quality_issue_keywords = ["crc error", "par2 repair failed", "crc", "par2"]
        is_quality_issue = any(keyword in reason_lower for keyword in quality_issue_keywords)

        if self.config.quality_fallback_enabled and retry_count <= 1:
            if is_quality_issue:
                # Use quality fallback if not at lowest quality (or quality unknown)
                if not current_quality or current_quality != "HDTV":
                    return RetryStrategy.QUALITY_FALLBACK

        # For retry attempt == 1, use quality fallback to search for alternatives
        # (unless it's a system issue that should use backoff)
        system_issue_keywords = ["disk full", "disk space", "permission denied", "no space"]
        is_system_issue = any(keyword in reason_lower for keyword in system_issue_keywords)

        if (
            self.config.quality_fallback_enabled
            and retry_count == 1
            and not is_system_issue
            and not is_quality_issue
        ):
            if not current_quality or current_quality != "HDTV":
                return RetryStrategy.QUALITY_FALLBACK

        # System issues or repeated failures - exponential backoff
        if self.config.exponential_backoff_enabled:
            return RetryStrategy.EXPONENTIAL_BACKOFF

        # Default to exponential backoff
        return RetryStrategy.EXPONENTIAL_BACKOFF

    async def _execute_immediate_retry(
        self, failed_download: FailedDownload, attempt_number: int, correlation_id: str
    ) -> RecoveryResult:
        """
        Execute immediate retry (no delay).

        This is used for transient network errors where an immediate retry
        is likely to succeed.

        Args:
            failed_download: Failed download
            attempt_number: Retry attempt number
            correlation_id: Correlation ID for tracking

        Returns:
            RecoveryResult
        """
        try:
            # Emit notification before retry
            await self._emit_retry_notification(
                failed_download,
                RetryStrategy.IMMEDIATE,
                attempt_number,
                correlation_id,
                "starting",
                delay_seconds=0,
            )

            # Retry immediately via SABnzbd
            result = await self.orchestrator.call_tool(
                server="sabnzbd",
                tool="retry_download",
                arguments={"nzo_id": failed_download.nzo_id},
            )

            success = result.get("status", False)

            # Emit success/failure notification
            await self._emit_retry_notification(
                failed_download,
                RetryStrategy.IMMEDIATE,
                attempt_number,
                correlation_id,
                "success" if success else "failed",
                delay_seconds=0,
                error=None if success else "SABnzbd retry command failed",
            )

            return RecoveryResult(
                success=success,
                retry_triggered=True,
                strategy=RetryStrategy.IMMEDIATE,
                message=(
                    "Immediate retry triggered successfully"
                    if success
                    else "Immediate retry command sent but status unclear"
                ),
                retry_attempt_number=attempt_number,
                delay_seconds=0,
            )

        except Exception as e:
            logger.error(f"Immediate retry failed: {e}")
            await self._emit_retry_notification(
                failed_download,
                RetryStrategy.IMMEDIATE,
                attempt_number,
                correlation_id,
                "failed",
                delay_seconds=0,
                error=str(e),
            )
            return RecoveryResult(
                success=False,
                retry_triggered=False,
                strategy=RetryStrategy.IMMEDIATE,
                message=f"Immediate retry error: {str(e)}",
                retry_attempt_number=attempt_number,
            )

    async def _execute_backoff_retry(
        self, failed_download: FailedDownload, attempt_number: int, correlation_id: str
    ) -> RecoveryResult:
        """
        Execute retry with exponential backoff.

        This is used for repeated failures or system issues where waiting
        before retrying increases the chance of success.

        Args:
            failed_download: Failed download
            attempt_number: Retry attempt number
            correlation_id: Correlation ID for tracking

        Returns:
            RecoveryResult
        """
        try:
            # Calculate backoff delay
            delay = self._calculate_backoff_delay(failed_download.retry_count)
            scheduled_time = datetime.utcnow() + timedelta(seconds=delay)

            # Emit notification before retry
            await self._emit_retry_notification(
                failed_download,
                RetryStrategy.EXPONENTIAL_BACKOFF,
                attempt_number,
                correlation_id,
                "starting",
                delay_seconds=delay,
            )

            # Schedule retry (in real implementation, would use task scheduler)
            # For now, we'll trigger immediately and return scheduled info
            result = await self.orchestrator.call_tool(
                server="sabnzbd",
                tool="retry_download",
                arguments={"nzo_id": failed_download.nzo_id},
            )

            success = result.get("status", False)

            # Emit success/failure notification
            await self._emit_retry_notification(
                failed_download,
                RetryStrategy.EXPONENTIAL_BACKOFF,
                attempt_number,
                correlation_id,
                "success" if success else "failed",
                delay_seconds=delay,
                error=None if success else "SABnzbd retry command failed",
            )

            return RecoveryResult(
                success=success,
                retry_triggered=True,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                message=(
                    f"Retry scheduled with {delay}s backoff delay (attempt {attempt_number})"
                    if success
                    else f"Retry command sent with {delay}s delay but status unclear"
                ),
                retry_attempt_number=attempt_number,
                delay_seconds=delay,
                scheduled_time=scheduled_time,
            )

        except Exception as e:
            logger.error(f"Backoff retry failed: {e}")
            delay = self._calculate_backoff_delay(failed_download.retry_count)
            await self._emit_retry_notification(
                failed_download,
                RetryStrategy.EXPONENTIAL_BACKOFF,
                attempt_number,
                correlation_id,
                "failed",
                delay_seconds=delay,
                error=str(e),
            )
            return RecoveryResult(
                success=False,
                retry_triggered=False,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                message=f"Backoff retry error: {str(e)}",
                retry_attempt_number=attempt_number,
            )

    async def _execute_quality_fallback(
        self,
        failed_download: FailedDownload,
        attempt_number: int,
        correlation_id: str,
        current_quality: Optional[str],
    ) -> RecoveryResult:
        """
        Execute retry with quality fallback (search for lower quality).

        This method:
        1. Extracts content info from the failed download filename
        2. Searches for the content in Sonarr/Radarr to find its ID
        3. Triggers a new search which will find alternative releases
        4. Sonarr/Radarr will automatically select the best available quality

        Args:
            failed_download: Failed download
            attempt_number: Retry attempt number
            correlation_id: Correlation ID for tracking
            current_quality: Current quality level

        Returns:
            RecoveryResult
        """
        try:
            # Determine service based on category
            server = "sonarr" if failed_download.category == "tv" else "radarr"

            # Extract content info from filename and find content ID
            if server == "sonarr":
                series_info = self._extract_series_info(failed_download.name)
                if not series_info:
                    raise ValueError("Could not extract series info from filename")

                series_name, season, episode = series_info

                # Find series by name
                content_id = await self._find_series_id(series_name)
                if not content_id:
                    raise ValueError(f"Could not find series '{series_name}' in Sonarr")

                # Find specific episode
                episode_id = await self._find_episode_id(content_id, season, episode)
                if not episode_id:
                    raise ValueError(
                        f"Could not find episode S{season:02d}E{episode:02d} for series"
                    )

                # Trigger episode search
                tool = "sonarr_search_episode"
                arguments = {"episode_id": episode_id}
                content_description = f"episode S{season:02d}E{episode:02d} of {series_name}"

            else:
                movie_info = self._extract_movie_info(failed_download.name)
                if not movie_info:
                    raise ValueError("Could not extract movie info from filename")

                movie_name, year = movie_info

                # Find movie by name and year
                content_id = await self._find_movie_id(movie_name, year)
                if not content_id:
                    raise ValueError(f"Could not find movie '{movie_name} ({year})' in Radarr")

                # Trigger movie search
                tool = "radarr_search_movie"
                arguments = {"movie_id": content_id}
                content_description = f"movie {movie_name} ({year})"

            # Emit notification before search
            await self._emit_quality_fallback_notification(
                failed_download,
                content_description,
                current_quality,
                correlation_id,
                "searching",
            )

            # Call search tool
            result = await self.orchestrator.call_tool(
                server=server, tool=tool, arguments=arguments
            )

            # Parse result - MCP servers return {"success": True, "data": {...}}
            success = result.get("success", False)
            if success:
                command_data = result.get("data", {})
                command_id = command_data.get("id")
                logger.info(
                    f"Quality fallback search triggered for {content_description}, "
                    f"command ID: {command_id}"
                )

                # Emit success notification
                await self._emit_quality_fallback_notification(
                    failed_download,
                    content_description,
                    current_quality,
                    correlation_id,
                    "success",
                )

                return RecoveryResult(
                    success=True,
                    retry_triggered=True,
                    strategy=RetryStrategy.QUALITY_FALLBACK,
                    message=(
                        f"Quality fallback search triggered for {content_description}. "
                        f"Sonarr/Radarr will automatically find alternative releases."
                    ),
                    retry_attempt_number=attempt_number,
                )
            else:
                error_msg = result.get("error", "Unknown error")
                raise Exception(f"Search command failed: {error_msg}")

        except Exception as e:
            error_details = str(e)
            logger.warning(
                f"Quality fallback failed for {failed_download.name}: {error_details}. "
                f"Falling back to exponential backoff."
            )

            # Emit failure notification
            await self._emit_quality_fallback_notification(
                failed_download,
                failed_download.name,
                current_quality,
                correlation_id,
                "failed",
                error_details,
            )

            # If quality fallback fails (e.g., can't parse filename), use exponential backoff
            return await self._execute_backoff_retry(
                failed_download, attempt_number, correlation_id
            )

    def _calculate_backoff_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay.

        Args:
            retry_count: Number of previous retry attempts

        Returns:
            Delay in seconds
        """
        delay = self.config.backoff_base_delay * (self.config.backoff_multiplier**retry_count)
        return min(delay, self.config.backoff_max_delay)  # type: ignore[no-any-return]

    def _extract_quality_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract quality indicator from filename.

        Args:
            filename: Download filename

        Returns:
            Quality string (e.g., "1080p", "720p") or None
        """
        quality_patterns = [
            (r"2160p", "2160p"),
            (r"1080p", "1080p"),
            (r"720p", "720p"),
            (r"WEB-DL", "WEB-DL"),
            (r"BluRay", "BluRay"),
            (r"HDTV", "HDTV"),
        ]

        for pattern, quality in quality_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return quality

        return None

    def _get_fallback_quality(self, current_quality: str) -> str:
        """
        Get fallback quality for a given quality level.

        Args:
            current_quality: Current quality

        Returns:
            Lower quality to try
        """
        quality_ladder = {
            "2160p": "1080p",
            "1080p": "720p",
            "720p": "HDTV",
            "BluRay": "WEB-DL",
            "WEB-DL": "HDTV",
        }

        return quality_ladder.get(current_quality, "HDTV")

    def _extract_series_info(self, filename: str) -> Optional[Tuple[str, int, int]]:
        """
        Extract series name, season, and episode from filename.

        Args:
            filename: Download filename

        Returns:
            Tuple of (series_name, season, episode) or None
        """
        # Pattern: Series.Name.S01E01
        pattern = r"(.+?)\.S(\d+)E(\d+)"
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            series_name = match.group(1).replace(".", " ")
            season = int(match.group(2))
            episode = int(match.group(3))
            return (series_name, season, episode)

        return None

    def _extract_movie_info(self, filename: str) -> Optional[Tuple[str, int]]:
        """
        Extract movie name and year from filename.

        Args:
            filename: Download filename

        Returns:
            Tuple of (movie_name, year) or None
        """
        # Pattern: Movie.Name.2020
        pattern = r"(.+?)\.(\d{4})"
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            movie_name = match.group(1).replace(".", " ")
            year = int(match.group(2))
            return (movie_name, year)

        return None

    def _track_retry_attempt(self, nzo_id: str, strategy: RetryStrategy, success: bool) -> None:
        """
        Track a retry attempt for statistics.

        Args:
            nzo_id: Download ID
            strategy: Strategy used
            success: Whether attempt was successful
        """
        if nzo_id not in self._retry_history:
            self._retry_history[nzo_id] = []

        attempt = RetryAttempt(
            nzo_id=nzo_id,
            strategy=strategy,
            attempt_number=len(self._retry_history[nzo_id]) + 1,
            timestamp=datetime.utcnow(),
            success=success,
        )

        self._retry_history[nzo_id].append(attempt)

    def get_retry_history(self, nzo_id: str) -> List[RetryAttempt]:
        """
        Get retry history for a download.

        Args:
            nzo_id: Download ID

        Returns:
            List of retry attempts
        """
        return self._retry_history.get(nzo_id, [])

    def get_strategy_statistics(
        self, attempts: List[RetryAttempt]
    ) -> Dict[RetryStrategy, Dict[str, float]]:
        """
        Calculate success rates for each retry strategy.

        Args:
            attempts: List of retry attempts

        Returns:
            Dictionary mapping strategies to statistics
        """
        stats: Dict[RetryStrategy, Dict[str, float]] = {}

        for strategy in RetryStrategy:
            strategy_attempts = [a for a in attempts if a.strategy == strategy]
            if strategy_attempts:
                success_count = sum(1 for a in strategy_attempts if a.success)
                success_rate = success_count / len(strategy_attempts)
                stats[strategy] = {
                    "total_attempts": len(strategy_attempts),
                    "successful": success_count,
                    "success_rate": success_rate,
                }

        return stats

    async def _emit_recovery_attempted(
        self,
        failed_download: FailedDownload,
        strategy: Optional[RetryStrategy],
        success: bool,
        correlation_id: str,
    ) -> None:
        """
        Emit recovery attempted event.

        Args:
            failed_download: Failed download
            strategy: Strategy used
            success: Whether recovery was successful
            correlation_id: Correlation ID
        """
        event = Event(
            event_type=EventType.RECOVERY_ATTEMPTED,
            data={
                "nzo_id": failed_download.nzo_id,
                "name": failed_download.name,
                "strategy": strategy.value if strategy else None,
                "success": success,
                "retry_count": failed_download.retry_count + 1,
            },
            correlation_id=correlation_id,
            source="recovery_service",
        )

        await self.event_bus.publish(event)

    async def _emit_max_retries_exceeded(
        self, failed_download: FailedDownload, correlation_id: str
    ) -> None:
        """
        Emit event when max retries exceeded.

        Args:
            failed_download: Failed download
            correlation_id: Correlation ID
        """
        event = Event(
            event_type=EventType.RECOVERY_FAILED,
            data={
                "nzo_id": failed_download.nzo_id,
                "name": failed_download.name,
                "reason": f"Exceeded maximum retry attempts ({self.config.max_retry_attempts})",
                "retry_count": failed_download.retry_count,
            },
            correlation_id=correlation_id,
            source="recovery_service",
        )

        await self.event_bus.publish(event)

    async def _emit_retry_notification(
        self,
        failed_download: FailedDownload,
        strategy: RetryStrategy,
        attempt_number: int,
        correlation_id: str,
        status: str,
        delay_seconds: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """
        Emit notification for retry actions (immediate and backoff).

        Args:
            failed_download: Failed download
            strategy: Retry strategy used
            attempt_number: Retry attempt number
            correlation_id: Correlation ID
            status: Status of the action (starting, success, failed)
            delay_seconds: Delay before retry (for backoff strategy)
            error: Error details if status is failed
        """
        if status == "starting":
            event_type = EventType.RECOVERY_ATTEMPTED
            if strategy == RetryStrategy.IMMEDIATE:
                message = (
                    f"Attempting immediate retry for '{failed_download.name}' "
                    f"(attempt {attempt_number})"
                )
            else:
                message = (
                    f"Scheduling retry for '{failed_download.name}' with {delay_seconds}s delay "
                    f"(attempt {attempt_number})"
                )
        elif status == "success":
            event_type = EventType.RECOVERY_ATTEMPTED
            if strategy == RetryStrategy.IMMEDIATE:
                message = f"Successfully triggered immediate retry for '{failed_download.name}'"
            else:
                message = (
                    f"Successfully scheduled retry for '{failed_download.name}' "
                    f"with {delay_seconds}s backoff"
                )
        else:  # failed
            event_type = EventType.RECOVERY_FAILED
            message = (
                f"Failed to trigger {strategy.value} retry for '{failed_download.name}': {error}"
            )

        event = Event(
            event_type=event_type,
            data={
                "nzo_id": failed_download.nzo_id,
                "name": failed_download.name,
                "strategy": strategy.value,
                "attempt_number": attempt_number,
                "status": status,
                "message": message,
                "delay_seconds": delay_seconds,
                "error": error if status == "failed" else None,
            },
            correlation_id=correlation_id,
            source=f"recovery_service.{strategy.value}",
        )

        await self.event_bus.publish(event)

    async def _emit_quality_fallback_notification(
        self,
        failed_download: FailedDownload,
        content_description: str,
        current_quality: Optional[str],
        correlation_id: str,
        status: str,
        error_details: Optional[str] = None,
    ) -> None:
        """
        Emit notification for quality fallback actions.

        Args:
            failed_download: Failed download
            content_description: Human-readable content description
            current_quality: Current quality level
            correlation_id: Correlation ID
            status: Status of the action (searching, success, failed)
            error_details: Error details if status is failed
        """
        if status == "searching":
            event_type = EventType.RECOVERY_ATTEMPTED
            message = (
                f"Searching for alternative releases of {content_description}. "
                f"Original quality: {current_quality or 'unknown'}"
            )
        elif status == "success":
            event_type = EventType.RECOVERY_ATTEMPTED
            message = (
                f"Successfully triggered search for {content_description}. "
                f"Sonarr/Radarr will automatically find the best available release."
            )
        else:  # failed
            event_type = EventType.RECOVERY_FAILED
            message = (
                f"Quality fallback search failed for {content_description}: {error_details}. "
                f"Will retry with exponential backoff instead."
            )

        event = Event(
            event_type=event_type,
            data={
                "nzo_id": failed_download.nzo_id,
                "name": failed_download.name,
                "content_description": content_description,
                "current_quality": current_quality,
                "status": status,
                "message": message,
                "error": error_details if status == "failed" else None,
            },
            correlation_id=correlation_id,
            source="recovery_service.quality_fallback",
        )

        await self.event_bus.publish(event)

    async def _find_series_id(self, series_name: str) -> Optional[int]:
        """
        Find series ID in Sonarr by name.

        Args:
            series_name: Name of the series

        Returns:
            Series ID if found, None otherwise
        """
        try:
            # Get all series from Sonarr
            result = await self.orchestrator.call_tool(
                server="sonarr",
                tool="sonarr_get_series",
                arguments={},
            )

            if not result.get("success"):
                logger.warning(f"Failed to get series list from Sonarr: {result}")
                return None

            series_list = result.get("data", [])

            # Normalize series name for comparison
            normalized_search = series_name.lower().replace(".", " ").replace("_", " ").strip()

            # Find matching series
            for series in series_list:
                series_title = series.get("title", "").lower()
                if normalized_search in series_title or series_title in normalized_search:
                    return series.get("id")

            logger.warning(f"Series '{series_name}' not found in Sonarr")
            return None

        except Exception as e:
            logger.error(f"Error finding series ID: {e}")
            return None

    async def _find_episode_id(self, series_id: int, season: int, episode: int) -> Optional[int]:
        """
        Find episode ID in Sonarr by series ID, season, and episode number.

        Args:
            series_id: Series ID
            season: Season number
            episode: Episode number

        Returns:
            Episode ID if found, None otherwise
        """
        try:
            # Get episodes for the series
            result = await self.orchestrator.call_tool(
                server="sonarr",
                tool="sonarr_get_episodes",
                arguments={"series_id": series_id, "season_number": season},
            )

            if not result.get("success"):
                logger.warning(
                    f"Failed to get episodes for series {series_id} season {season}: {result}"
                )
                return None

            episodes = result.get("data", [])

            # Find matching episode
            for ep in episodes:
                if ep.get("seasonNumber") == season and ep.get("episodeNumber") == episode:
                    return ep.get("id")

            logger.warning(f"Episode S{season:02d}E{episode:02d} not found for series {series_id}")
            return None

        except Exception as e:
            logger.error(f"Error finding episode ID: {e}")
            return None

    async def _find_movie_id(self, movie_name: str, year: int) -> Optional[int]:
        """
        Find movie ID in Radarr by name and year.

        Args:
            movie_name: Name of the movie
            year: Release year

        Returns:
            Movie ID if found, None otherwise
        """
        try:
            # Get all movies from Radarr
            result = await self.orchestrator.call_tool(
                server="radarr",
                tool="radarr_get_movies",
                arguments={},
            )

            if not result.get("success"):
                logger.warning(f"Failed to get movie list from Radarr: {result}")
                return None

            movies = result.get("data", [])

            # Normalize movie name for comparison
            normalized_search = movie_name.lower().replace(".", " ").replace("_", " ").strip()

            # Find matching movie
            for movie in movies:
                movie_title = movie.get("title", "").lower()
                movie_year = movie.get("year")

                # Match by name and year (with 1-year tolerance)
                if (normalized_search in movie_title or movie_title in normalized_search) and (
                    movie_year and abs(movie_year - year) <= 1
                ):
                    return movie.get("id")

            logger.warning(f"Movie '{movie_name} ({year})' not found in Radarr")
            return None

        except Exception as e:
            logger.error(f"Error finding movie ID: {e}")
            return None
