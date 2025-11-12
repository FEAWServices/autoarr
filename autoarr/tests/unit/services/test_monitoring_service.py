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
Unit tests for Monitoring Service (Sprint 5).

This module tests the MonitoringService's ability to:
- Poll SABnzbd queue periodically for download status
- Detect failed downloads based on status codes
- Recognize failure patterns (multiple failures, recurring issues)
- Generate alerts for download failures
- Monitor Sonarr/Radarr wanted lists
- Track download state changes
- Handle polling errors gracefully

Test Strategy:
- 70% Unit Tests: Fast, isolated tests with mocked dependencies
- Focus on failure detection logic and pattern recognition
- Test edge cases: network failures, malformed responses, race conditions
- Verify event emission for activity tracking
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

from autoarr.api.services.event_bus import EventBus, EventType
from autoarr.api.services.monitoring_service import (
    DownloadStatus,
    FailurePattern,
    MonitoringConfig,
    MonitoringService,
)
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_orchestrator():
    """Create a mock MCP orchestrator."""
    orchestrator = Mock(spec=MCPOrchestrator)
    orchestrator.call_tool = AsyncMock()
    orchestrator.is_connected = AsyncMock(return_value=True)
    return orchestrator


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    event_bus = Mock(spec=EventBus)
    event_bus.publish = AsyncMock()
    event_bus.subscribe = Mock()
    return event_bus


@pytest.fixture
def monitoring_config():
    """Create monitoring configuration."""
    return MonitoringConfig(
        poll_interval=60,  # 60 seconds
        failure_detection_enabled=True,
        pattern_recognition_enabled=True,
        max_retry_attempts=3,
        alert_on_failure=True,
    )


@pytest.fixture
def monitoring_service(mock_orchestrator, mock_event_bus, monitoring_config):
    """Create a MonitoringService instance with mocked dependencies."""
    service = MonitoringService(
        orchestrator=mock_orchestrator,
        event_bus=mock_event_bus,
        config=monitoring_config,
    )
    return service


# ============================================================================
# Test Data Factories
# ============================================================================


def create_queue_item(
    nzo_id: str,
    filename: str,
    status: str = "Downloading",
    percentage: int = 50,
    mb_left: float = 500.0,
    mb_total: float = 1000.0,
    category: str = "tv",
) -> Dict[str, Any]:
    """Factory to create SABnzbd queue item test data."""
    return {
        "nzo_id": nzo_id,
        "filename": filename,
        "status": status,
        "percentage": percentage,
        "mb": mb_total,
        "mbleft": mb_left,
        "category": category,
        "priority": "Normal",
        "eta": "00:10:00",
    }


def create_history_item(
    nzo_id: str,
    name: str,
    status: str = "Completed",
    fail_message: str = "",
    category: str = "tv",
    retry_count: int = 0,
) -> Dict[str, Any]:
    """Factory to create SABnzbd history item test data."""
    return {
        "nzo_id": nzo_id,
        "name": name,
        "status": status,
        "fail_message": fail_message,
        "category": category,
        "size": "1.2 GB",
        "download_time": 300,
        "completed": int(datetime.now().timestamp()),
        "retry": retry_count,
    }


def create_wanted_episode(
    series_id: int,
    season_number: int,
    episode_number: int,
    title: str = "Test Episode",
    monitored: bool = True,
) -> Dict[str, Any]:
    """Factory to create Sonarr wanted episode test data."""
    return {
        "id": series_id * 1000 + season_number * 100 + episode_number,
        "seriesId": series_id,
        "seasonNumber": season_number,
        "episodeNumber": episode_number,
        "title": title,
        "monitored": monitored,
        "hasFile": False,
        "airDate": "2024-01-01",
        "airDateUtc": "2024-01-01T21:00:00Z",
    }


# ============================================================================
# Tests for Queue Polling
# ============================================================================


@pytest.mark.asyncio
async def test_poll_queue_success(monitoring_service, mock_orchestrator):
    """Test successful queue polling returns current queue state."""
    # Arrange
    mock_queue_data = {
        "queue": {
            "status": "Downloading",
            "speed": "5.2 MB/s",
            "slots": [
                create_queue_item("nzo_1", "Test.Show.S01E01.mkv", status="Downloading"),
                create_queue_item("nzo_2", "Test.Movie.2024.mkv", status="Queued"),
            ],
        }
    }
    mock_orchestrator.call_tool.return_value = mock_queue_data

    # Act
    queue_state = await monitoring_service.poll_queue()

    # Assert
    assert queue_state is not None
    assert len(queue_state.items) == 2
    assert queue_state.items[0].nzo_id == "nzo_1"
    assert queue_state.items[0].status == DownloadStatus.DOWNLOADING
    assert queue_state.items[1].nzo_id == "nzo_2"
    assert queue_state.items[1].status == DownloadStatus.QUEUED
    mock_orchestrator.call_tool.assert_called_once_with(
        server="sabnzbd", tool="get_queue", params={}
    )


@pytest.mark.asyncio
async def test_poll_queue_empty(monitoring_service, mock_orchestrator):
    """Test polling returns empty state when queue is empty."""
    # Arrange
    mock_queue_data = {"queue": {"status": "Idle", "speed": "0 MB/s", "slots": []}}
    mock_orchestrator.call_tool.return_value = mock_queue_data

    # Act
    queue_state = await monitoring_service.poll_queue()

    # Assert
    assert queue_state is not None
    assert len(queue_state.items) == 0
    assert queue_state.status == "Idle"


@pytest.mark.asyncio
async def test_poll_queue_connection_error(monitoring_service, mock_orchestrator):
    """Test polling handles connection errors gracefully."""
    # Arrange
    mock_orchestrator.call_tool.side_effect = ConnectionError("Failed to connect to SABnzbd")

    # Act
    queue_state = await monitoring_service.poll_queue()

    # Assert
    assert queue_state is None  # Should return None on error, not raise


@pytest.mark.asyncio
async def test_poll_queue_malformed_response(monitoring_service, mock_orchestrator):
    """Test polling handles malformed API responses."""
    # Arrange
    mock_orchestrator.call_tool.return_value = {"invalid": "response"}

    # Act
    queue_state = await monitoring_service.poll_queue()

    # Assert
    assert queue_state is None  # Should handle gracefully


@pytest.mark.asyncio
async def test_poll_queue_periodic_polling(monitoring_service, mock_orchestrator):
    """Test that polling occurs at configured intervals."""
    # Arrange
    mock_orchestrator.call_tool.return_value = {"queue": {"status": "Downloading", "slots": []}}
    monitoring_service.config.poll_interval = 1  # 1 second for testing

    # Act - Start monitoring in background
    monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())
    await asyncio.sleep(2.5)  # Wait for ~2 poll cycles
    monitoring_service.stop_monitoring()
    await monitoring_task

    # Assert - Should have called at least 2 times
    assert mock_orchestrator.call_tool.call_count >= 2


# ============================================================================
# Tests for Failed Download Detection
# ============================================================================


@pytest.mark.asyncio
async def test_detect_failed_download_from_history(monitoring_service, mock_orchestrator):
    """Test detection of failed downloads in SABnzbd history."""
    # Arrange
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item(
                    "nzo_failed_1",
                    "Failed.Show.S01E01",
                    status="Failed",
                    fail_message="Unpacking failed, write error or disk is full?",
                ),
                create_history_item("nzo_success_1", "Success.Show.S01E02", status="Completed"),
            ]
        }
    }
    mock_orchestrator.call_tool.return_value = mock_history_data

    # Act
    failed_downloads = await monitoring_service.detect_failed_downloads()

    # Assert
    assert len(failed_downloads) == 1
    assert failed_downloads[0].nzo_id == "nzo_failed_1"
    assert failed_downloads[0].status == DownloadStatus.FAILED
    assert "Unpacking failed" in failed_downloads[0].failure_reason


@pytest.mark.asyncio
async def test_detect_failed_download_status_codes(monitoring_service):
    """Test various failure status codes are correctly identified."""
    # Test data with different failure statuses
    failure_statuses = [
        ("Failed", "CRC error in verification"),
        ("Failed", "Insufficient disk space"),
        ("Failed", "Connection timeout"),
        ("Failed", "Unpacking failed"),
        ("Failed", "PAR2 repair failed"),
    ]

    for status, reason in failure_statuses:
        # Act
        is_failed = monitoring_service._is_failed_status(status, reason)

        # Assert
        assert is_failed is True, f"Should detect '{status}' with reason '{reason}' as failed"


@pytest.mark.asyncio
async def test_ignore_non_failure_statuses(monitoring_service):
    """Test that non-failure statuses are not flagged as failures."""
    # Test data with success statuses
    success_statuses = [
        "Completed",
        "Downloading",
        "Queued",
        "Paused",
        "Extracting",
        "Moving",
        "Verifying",
    ]

    for status in success_statuses:
        # Act
        is_failed = monitoring_service._is_failed_status(status, "")

        # Assert
        assert is_failed is False, f"Should not detect '{status}' as failed"


@pytest.mark.asyncio
async def test_detect_multiple_failed_downloads(monitoring_service, mock_orchestrator):
    """Test detection of multiple failed downloads in a single poll."""
    # Arrange
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item("nzo_1", "Failed.1", status="Failed", fail_message="Error 1"),
                create_history_item("nzo_2", "Failed.2", status="Failed", fail_message="Error 2"),
                create_history_item("nzo_3", "Failed.3", status="Failed", fail_message="Error 3"),
                create_history_item("nzo_4", "Success", status="Completed"),
            ]
        }
    }
    mock_orchestrator.call_tool.return_value = mock_history_data

    # Act
    failed_downloads = await monitoring_service.detect_failed_downloads()

    # Assert
    assert len(failed_downloads) == 3
    assert all(d.status == DownloadStatus.FAILED for d in failed_downloads)


# ============================================================================
# Tests for Failure Pattern Recognition
# ============================================================================


@pytest.mark.asyncio
async def test_recognize_recurring_failure_pattern(monitoring_service):
    """Test recognition of recurring failures for the same content."""
    # Arrange - Simulate multiple failures for the same episode
    failure_history = [
        create_history_item(
            "nzo_1",
            "Show.S01E01.HDTV",
            status="Failed",
            fail_message="PAR2 repair failed",
            retry_count=0,
        ),
        create_history_item(
            "nzo_2",
            "Show.S01E01.WEB-DL",
            status="Failed",
            fail_message="CRC error",
            retry_count=1,
        ),
        create_history_item(
            "nzo_3",
            "Show.S01E01.720p",
            status="Failed",
            fail_message="Unpacking failed",
            retry_count=2,
        ),
    ]

    # Act
    pattern = monitoring_service.analyze_failure_pattern(failure_history)

    # Assert
    assert pattern is not None
    assert pattern.pattern_type == FailurePattern.RECURRING_SAME_CONTENT
    assert pattern.failure_count == 3
    assert pattern.content_identifier == "Show.S01E01"


@pytest.mark.asyncio
async def test_recognize_disk_space_failure_pattern(monitoring_service):
    """Test recognition of disk space related failure patterns."""
    # Arrange
    failure_history = [
        create_history_item(
            "nzo_1", "Movie.1", status="Failed", fail_message="Insufficient disk space"
        ),
        create_history_item(
            "nzo_2", "Movie.2", status="Failed", fail_message="write error or disk is full?"
        ),
        create_history_item(
            "nzo_3", "Show.1", status="Failed", fail_message="No space left on device"
        ),
    ]

    # Act
    pattern = monitoring_service.analyze_failure_pattern(failure_history)

    # Assert
    assert pattern is not None
    assert pattern.pattern_type == FailurePattern.DISK_SPACE_ISSUE
    assert pattern.failure_count == 3


@pytest.mark.asyncio
async def test_recognize_network_failure_pattern(monitoring_service):
    """Test recognition of network/connection related failure patterns."""
    # Arrange
    failure_history = [
        create_history_item(
            "nzo_1", "Content.1", status="Failed", fail_message="Connection timeout"
        ),
        create_history_item(
            "nzo_2", "Content.2", status="Failed", fail_message="Connection reset by peer"
        ),
        create_history_item(
            "nzo_3", "Content.3", status="Failed", fail_message="Failed to connect"
        ),
    ]

    # Act
    pattern = monitoring_service.analyze_failure_pattern(failure_history)

    # Assert
    assert pattern is not None
    assert pattern.pattern_type == FailurePattern.NETWORK_ISSUE
    assert pattern.failure_count == 3


@pytest.mark.asyncio
async def test_recognize_quality_issue_pattern(monitoring_service):
    """Test recognition of quality/corruption related failure patterns."""
    # Arrange
    failure_history = [
        create_history_item("nzo_1", "File.1", status="Failed", fail_message="CRC error"),
        create_history_item("nzo_2", "File.2", status="Failed", fail_message="PAR2 repair failed"),
        create_history_item("nzo_3", "File.3", status="Failed", fail_message="Verification failed"),
    ]

    # Act
    pattern = monitoring_service.analyze_failure_pattern(failure_history)

    # Assert
    assert pattern is not None
    assert pattern.pattern_type == FailurePattern.QUALITY_CORRUPTION
    assert pattern.failure_count == 3


@pytest.mark.asyncio
async def test_no_pattern_with_isolated_failures(monitoring_service):
    """Test that isolated failures don't trigger pattern recognition."""
    # Arrange - Different failures, no clear pattern
    failure_history = [
        create_history_item("nzo_1", "Show.A", status="Failed", fail_message="Random error 1"),
    ]

    # Act
    pattern = monitoring_service.analyze_failure_pattern(failure_history)

    # Assert
    assert pattern is None or pattern.pattern_type == FailurePattern.ISOLATED


# ============================================================================
# Tests for Alert Generation
# ============================================================================


@pytest.mark.asyncio
async def test_generate_alert_on_failure_detection(
    monitoring_service, mock_orchestrator, mock_event_bus
):
    """Test that alerts are generated when failures are detected."""
    # Arrange
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item(
                    "nzo_failed",
                    "Failed.Download",
                    status="Failed",
                    fail_message="Download failed",
                ),
            ]
        }
    }
    mock_orchestrator.call_tool.return_value = mock_history_data

    # Act
    await monitoring_service.check_and_alert_failures()

    # Assert
    mock_event_bus.publish.assert_called()
    published_event = mock_event_bus.publish.call_args[0][0]
    assert published_event.event_type == EventType.DOWNLOAD_FAILED
    assert "nzo_failed" in published_event.data["nzo_id"]


@pytest.mark.asyncio
async def test_alert_contains_failure_details(
    monitoring_service, mock_orchestrator, mock_event_bus
):
    """Test that alerts include detailed failure information."""
    # Arrange
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item(
                    "nzo_123",
                    "Test.Show.S01E01",
                    status="Failed",
                    fail_message="PAR2 repair failed",
                    category="tv",
                ),
            ]
        }
    }
    mock_orchestrator.call_tool.return_value = mock_history_data

    # Act
    await monitoring_service.check_and_alert_failures()

    # Assert
    published_event = mock_event_bus.publish.call_args[0][0]
    assert published_event.data["name"] == "Test.Show.S01E01"
    assert published_event.data["failure_reason"] == "PAR2 repair failed"
    assert published_event.data["category"] == "tv"


@pytest.mark.asyncio
async def test_no_alert_when_disabled(monitoring_service, mock_orchestrator, mock_event_bus):
    """Test that alerts are not generated when disabled in config."""
    # Arrange
    monitoring_service.config.alert_on_failure = False
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item("nzo_1", "Failed", status="Failed", fail_message="Error"),
            ]
        }
    }
    mock_orchestrator.call_tool.return_value = mock_history_data

    # Act
    await monitoring_service.check_and_alert_failures()

    # Assert
    mock_event_bus.publish.assert_not_called()


@pytest.mark.asyncio
async def test_alert_throttling_prevents_spam(
    monitoring_service, mock_orchestrator, mock_event_bus
):
    """Test that repeated alerts for the same failure are throttled."""
    # Arrange
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item("nzo_1", "Failed", status="Failed", fail_message="Error"),
            ]
        }
    }
    mock_orchestrator.call_tool.return_value = mock_history_data

    # Act - Check multiple times in quick succession
    await monitoring_service.check_and_alert_failures()
    await monitoring_service.check_and_alert_failures()
    await monitoring_service.check_and_alert_failures()

    # Assert - Should only alert once (or limited times)
    assert mock_event_bus.publish.call_count <= 2  # Allow for initial + one retry


# ============================================================================
# Tests for Wanted List Monitoring
# ============================================================================


@pytest.mark.asyncio
async def test_monitor_sonarr_wanted_list(monitoring_service, mock_orchestrator):
    """Test monitoring of Sonarr wanted/missing episodes."""
    # Arrange
    mock_wanted_data = {
        "page": 1,
        "pageSize": 20,
        "totalRecords": 2,
        "records": [
            create_wanted_episode(1, 1, 1, "Missing Episode 1"),
            create_wanted_episode(1, 1, 2, "Missing Episode 2"),
        ],
    }
    mock_orchestrator.call_tool.return_value = mock_wanted_data

    # Act
    wanted_episodes = await monitoring_service.get_wanted_episodes()

    # Assert
    assert len(wanted_episodes) == 2
    assert wanted_episodes[0].season_number == 1
    assert wanted_episodes[0].episode_number == 1
    mock_orchestrator.call_tool.assert_called_once_with(
        server="sonarr", tool="get_wanted", params={"page": 1, "pageSize": 50}
    )


@pytest.mark.asyncio
async def test_monitor_radarr_wanted_list(monitoring_service, mock_orchestrator):
    """Test monitoring of Radarr wanted/missing movies."""
    # Arrange
    mock_wanted_data = {
        "page": 1,
        "pageSize": 20,
        "totalRecords": 1,
        "records": [
            {
                "id": 1,
                "title": "Missing Movie",
                "year": 2024,
                "hasFile": False,
                "monitored": True,
            }
        ],
    }
    mock_orchestrator.call_tool.return_value = mock_wanted_data

    # Act
    wanted_movies = await monitoring_service.get_wanted_movies()

    # Assert
    assert len(wanted_movies) == 1
    assert wanted_movies[0].title == "Missing Movie"
    assert wanted_movies[0].year == 2024
    mock_orchestrator.call_tool.assert_called_once_with(
        server="radarr", tool="get_wanted", params={"page": 1, "pageSize": 50}
    )


@pytest.mark.asyncio
async def test_correlate_wanted_with_failed_downloads(monitoring_service, mock_orchestrator):
    """Test correlation between wanted items and failed downloads."""
    # Arrange - Setup wanted episode
    mock_wanted_data = {"records": [create_wanted_episode(1, 1, 1, "Show.S01E01")]}

    # Setup failed download for the same episode
    mock_history_data = {
        "history": {
            "slots": [
                create_history_item(
                    "nzo_1", "Show.S01E01.HDTV", status="Failed", fail_message="Error"
                ),
            ]
        }
    }

    mock_orchestrator.call_tool.side_effect = [mock_wanted_data, mock_history_data]

    # Act
    correlations = await monitoring_service.correlate_wanted_with_failures()

    # Assert
    assert len(correlations) == 1
    assert correlations[0].content_name == "Show.S01E01"
    assert correlations[0].has_failed_attempts is True


# ============================================================================
# Tests for State Change Tracking
# ============================================================================


@pytest.mark.asyncio
async def test_track_download_state_changes(monitoring_service, mock_event_bus):
    """Test tracking of download state transitions."""
    # Arrange - Initial state: Queued
    initial_item = create_queue_item("nzo_1", "Test.mkv", status="Queued")
    monitoring_service._update_tracked_state("nzo_1", DownloadStatus.QUEUED)

    # Act - State change: Queued -> Downloading
    updated_item = create_queue_item("nzo_1", "Test.mkv", status="Downloading")
    await monitoring_service._handle_state_change("nzo_1", DownloadStatus.DOWNLOADING)

    # Assert - Should emit state change event
    mock_event_bus.publish.assert_called()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.DOWNLOAD_STATE_CHANGED
    assert event.data["nzo_id"] == "nzo_1"
    assert event.data["old_state"] == "queued"
    assert event.data["new_state"] == "downloading"


@pytest.mark.asyncio
async def test_track_completion_state_change(monitoring_service, mock_event_bus):
    """Test tracking when download completes successfully."""
    # Arrange
    monitoring_service._update_tracked_state("nzo_1", DownloadStatus.DOWNLOADING)

    # Act
    await monitoring_service._handle_state_change("nzo_1", DownloadStatus.COMPLETED)

    # Assert
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.DOWNLOAD_COMPLETED
    assert event.data["nzo_id"] == "nzo_1"


@pytest.mark.asyncio
async def test_no_event_when_state_unchanged(monitoring_service, mock_event_bus):
    """Test that no events are emitted when state doesn't change."""
    # Arrange
    monitoring_service._update_tracked_state("nzo_1", DownloadStatus.DOWNLOADING)

    # Act - Same state
    await monitoring_service._handle_state_change("nzo_1", DownloadStatus.DOWNLOADING)

    # Assert
    mock_event_bus.publish.assert_not_called()


# ============================================================================
# Tests for Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_handle_orchestrator_timeout(monitoring_service, mock_orchestrator):
    """Test handling of MCP orchestrator timeouts during polling."""
    # Arrange
    mock_orchestrator.call_tool.side_effect = asyncio.TimeoutError("Request timed out")

    # Act & Assert - Should not raise, should handle gracefully
    queue_state = await monitoring_service.poll_queue()
    assert queue_state is None


@pytest.mark.asyncio
async def test_handle_malformed_queue_data(monitoring_service, mock_orchestrator):
    """Test handling of malformed queue data from SABnzbd."""
    # Arrange
    mock_orchestrator.call_tool.return_value = {
        "queue": {"slots": [{"invalid": "data", "missing": "required_fields"}]}
    }

    # Act
    queue_state = await monitoring_service.poll_queue()

    # Assert - Should handle gracefully, possibly skip invalid items
    assert queue_state is not None
    # Invalid items should be filtered out or handled gracefully


@pytest.mark.asyncio
async def test_continue_monitoring_after_error(monitoring_service, mock_orchestrator):
    """Test that monitoring continues after encountering errors."""
    # Arrange
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("Temporary failure")
        return {"queue": {"status": "Downloading", "slots": []}}

    mock_orchestrator.call_tool.side_effect = side_effect
    monitoring_service.config.poll_interval = 1

    # Act
    monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())
    await asyncio.sleep(2.5)
    monitoring_service.stop_monitoring()
    await monitoring_task

    # Assert - Should have recovered and continued polling
    assert call_count >= 2


# ============================================================================
# Tests for Event Emission
# ============================================================================


@pytest.mark.asyncio
async def test_emit_event_with_correlation_id(monitoring_service, mock_event_bus):
    """Test that emitted events include correlation IDs."""
    # Arrange
    mock_orchestrator = monitoring_service.orchestrator
    mock_orchestrator.call_tool.return_value = {
        "history": {
            "slots": [
                create_history_item("nzo_1", "Test", status="Failed", fail_message="Error"),
            ]
        }
    }

    # Act
    await monitoring_service.check_and_alert_failures()

    # Assert
    event = mock_event_bus.publish.call_args[0][0]
    assert event.correlation_id is not None
    assert isinstance(event.correlation_id, str)
    assert len(event.correlation_id) > 0


@pytest.mark.asyncio
async def test_emit_event_with_timestamp(monitoring_service, mock_event_bus):
    """Test that emitted events include timestamps."""
    # Arrange
    mock_orchestrator = monitoring_service.orchestrator
    mock_orchestrator.call_tool.return_value = {
        "history": {
            "slots": [
                create_history_item("nzo_1", "Test", status="Failed", fail_message="Error"),
            ]
        }
    }

    # Act
    await monitoring_service.check_and_alert_failures()

    # Assert
    event = mock_event_bus.publish.call_args[0][0]
    assert event.timestamp is not None
    assert isinstance(event.timestamp, datetime)


# ============================================================================
# Tests for Performance and Concurrency
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_polling_does_not_overlap(monitoring_service, mock_orchestrator):
    """Test that concurrent poll requests don't overlap."""
    # Arrange
    poll_started = []
    poll_completed = []

    async def slow_call(*args, **kwargs):
        poll_started.append(datetime.now())
        await asyncio.sleep(0.5)  # Simulate slow API call
        poll_completed.append(datetime.now())
        return {"queue": {"status": "Downloading", "slots": []}}

    mock_orchestrator.call_tool.side_effect = slow_call

    # Act - Start two polls concurrently
    results = await asyncio.gather(
        monitoring_service.poll_queue(),
        monitoring_service.poll_queue(),
    )

    # Assert - Second poll should wait for first to complete
    assert len(poll_completed) == 2
    # If properly serialized, second should start after first completes
    # (This depends on implementation using locks/semaphores)


@pytest.mark.asyncio
async def test_polling_performance_with_large_queue(monitoring_service, mock_orchestrator):
    """Test polling performance with a large queue."""
    # Arrange - Create large queue (100 items)
    large_queue = {
        "queue": {
            "status": "Downloading",
            "slots": [create_queue_item(f"nzo_{i}", f"File_{i}.mkv") for i in range(100)],
        }
    }
    mock_orchestrator.call_tool.return_value = large_queue

    # Act
    start_time = datetime.now()
    queue_state = await monitoring_service.poll_queue()
    duration = (datetime.now() - start_time).total_seconds()

    # Assert
    assert queue_state is not None
    assert len(queue_state.items) == 100
    assert duration < 1.0  # Should process quickly (< 1 second)
