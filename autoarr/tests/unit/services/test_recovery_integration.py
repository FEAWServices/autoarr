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
Unit tests for Recovery Service Sonarr/Radarr Integration.

This module tests the enhanced RecoveryService integration with
Sonarr and Radarr search APIs for intelligent quality fallback:
- Finding content by name in Sonarr/Radarr libraries
- Triggering searches with proper content IDs
- Enhanced user notifications for recovery actions
- Quality fallback with automatic release selection
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, call

import pytest

from autoarr.api.services.event_bus import EventBus, EventType
from autoarr.api.services.monitoring_service import DownloadStatus, FailedDownload
from autoarr.api.services.recovery_service import RecoveryConfig, RecoveryService, RetryStrategy
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
def recovery_config():
    """Create recovery service configuration."""
    return RecoveryConfig(
        max_retry_attempts=3,
        immediate_retry_enabled=True,
        exponential_backoff_enabled=True,
        quality_fallback_enabled=True,
        backoff_base_delay=60,
        backoff_max_delay=3600,
        backoff_multiplier=2,
    )


@pytest.fixture
def recovery_service(mock_orchestrator, mock_event_bus, recovery_config):
    """Create a RecoveryService instance with mocked dependencies."""
    service = RecoveryService(
        orchestrator=mock_orchestrator,
        event_bus=mock_event_bus,
        config=recovery_config,
    )
    return service


def create_failed_download(
    nzo_id: str,
    name: str,
    failure_reason: str = "Download failed",
    category: str = "tv",
    retry_count: int = 0,
) -> FailedDownload:
    """Factory to create failed download test data."""
    return FailedDownload(
        nzo_id=nzo_id,
        name=name,
        status=DownloadStatus.FAILED,
        failure_reason=failure_reason,
        category=category,
        retry_count=retry_count,
        last_retry_time=None,
        original_failure_time=datetime.now(),
    )


# ============================================================================
# Tests for Quality Fallback with Sonarr Integration
# ============================================================================


@pytest.mark.asyncio
async def test_quality_fallback_finds_series_and_triggers_search(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test quality fallback finds series in Sonarr and triggers episode search."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Breaking.Bad.S01E01.1080p.BluRay.mkv",
        failure_reason="CRC error",
        category="tv",
        retry_count=1,
    )

    # Mock responses for the integration flow
    # Sonarr provider returns nested data structure
    mock_orchestrator.call_tool.side_effect = [
        # First call: sonarr_get_series
        {
            "success": True,
            "data": {
                "series_count": 2,
                "series": [
                    {"id": 123, "title": "Breaking Bad"},
                    {"id": 456, "title": "Better Call Saul"},
                ],
            },
        },
        # Second call: sonarr_get_episodes
        {
            "success": True,
            "data": {
                "episode_count": 2,
                "episodes": [
                    {"id": 789, "seasonNumber": 1, "episodeNumber": 1, "title": "Pilot"},
                    {"id": 790, "seasonNumber": 1, "episodeNumber": 2},
                ],
            },
        },
        # Third call: sonarr_search_episode
        {"success": True, "data": {"id": 999, "status": "queued"}},
    ]

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.success is True
    assert result.strategy == RetryStrategy.QUALITY_FALLBACK
    assert "Breaking Bad" in result.message or "episode" in result.message.lower()

    # Verify the call sequence
    assert mock_orchestrator.call_tool.call_count == 3

    # First call should get series list
    call1 = mock_orchestrator.call_tool.call_args_list[0]
    assert call1[1]["server"] == "sonarr"
    assert call1[1]["tool"] == "sonarr_get_series"

    # Second call should get episodes
    call2 = mock_orchestrator.call_tool.call_args_list[1]
    assert call2[1]["server"] == "sonarr"
    assert call2[1]["tool"] == "sonarr_get_episodes"
    assert call2[1]["arguments"]["series_id"] == 123

    # Third call should search for episode
    call3 = mock_orchestrator.call_tool.call_args_list[2]
    assert call3[1]["server"] == "sonarr"
    assert call3[1]["tool"] == "sonarr_search_episode"
    assert call3[1]["arguments"]["episode_id"] == 789

    # Verify notifications were sent
    assert mock_event_bus.publish.call_count >= 2  # searching + success


@pytest.mark.asyncio
async def test_quality_fallback_finds_movie_and_triggers_search(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test quality fallback finds movie in Radarr and triggers movie search."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "The.Matrix.1999.1080p.BluRay.mkv",
        failure_reason="PAR2 repair failed",
        category="movies",
        retry_count=1,
    )

    # Mock responses
    # Radarr provider returns nested data structure
    mock_orchestrator.call_tool.side_effect = [
        # First call: radarr_get_movies
        {
            "success": True,
            "data": {
                "movie_count": 2,
                "movies": [
                    {"id": 123, "title": "The Matrix", "year": 1999},
                    {"id": 456, "title": "The Matrix Reloaded", "year": 2003},
                ],
            },
        },
        # Second call: radarr_search_movie
        {"success": True, "data": {"id": 999, "status": "queued"}},
    ]

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.success is True
    assert result.strategy == RetryStrategy.QUALITY_FALLBACK

    # Verify the call sequence
    assert mock_orchestrator.call_tool.call_count == 2

    # First call should get movie list
    call1 = mock_orchestrator.call_tool.call_args_list[0]
    assert call1[1]["server"] == "radarr"
    assert call1[1]["tool"] == "radarr_get_movies"

    # Second call should search for movie
    call2 = mock_orchestrator.call_tool.call_args_list[1]
    assert call2[1]["server"] == "radarr"
    assert call2[1]["tool"] == "radarr_search_movie"
    assert call2[1]["arguments"]["movie_id"] == 123

    # Verify notifications
    assert mock_event_bus.publish.call_count >= 2


@pytest.mark.asyncio
async def test_quality_fallback_handles_series_not_found(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test quality fallback falls back to exponential backoff when series not found."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Unknown.Show.S01E01.1080p.mkv",
        failure_reason="CRC error",
        category="tv",
        retry_count=1,
    )

    # Mock responses
    # Sonarr provider returns nested data structure
    mock_orchestrator.call_tool.side_effect = [
        # First call: sonarr_get_series (no matching series)
        {
            "success": True,
            "data": {"series_count": 1, "series": [{"id": 123, "title": "Some Other Show"}]},
        },
        # Fallback to SABnzbd retry (exponential backoff)
        {"status": True},
    ]

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should fall back to exponential backoff
    assert result.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
    assert mock_orchestrator.call_tool.call_count == 2

    # Verify failure notification was sent
    failure_events = [
        call_args[0][0]
        for call_args in mock_event_bus.publish.call_args_list
        if call_args[0][0].event_type == EventType.RECOVERY_FAILED
    ]
    assert len(failure_events) >= 1
    assert "could not find" in failure_events[0].data["message"].lower()


@pytest.mark.asyncio
async def test_quality_fallback_handles_episode_not_found(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test quality fallback handles missing episode gracefully."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Breaking.Bad.S99E99.1080p.mkv",
        failure_reason="CRC error",
        category="tv",
        retry_count=1,
    )

    # Mock responses
    # Sonarr provider returns nested data structure
    mock_orchestrator.call_tool.side_effect = [
        # First call: sonarr_get_series (series found)
        {
            "success": True,
            "data": {"series_count": 1, "series": [{"id": 123, "title": "Breaking Bad"}]},
        },
        # Second call: sonarr_get_episodes (no matching episode)
        {
            "success": True,
            "data": {
                "episode_count": 1,
                "episodes": [{"id": 789, "seasonNumber": 1, "episodeNumber": 1}],
            },
        },
        # Fallback to SABnzbd retry
        {"status": True},
    ]

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
    assert mock_orchestrator.call_tool.call_count == 3


@pytest.mark.asyncio
async def test_quality_fallback_emits_detailed_notifications(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test that quality fallback emits detailed user notifications."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Test.Show.S01E01.1080p.mkv",
        failure_reason="CRC error",
        category="tv",
        retry_count=1,
    )

    # Mock successful flow
    # Sonarr provider returns nested data structure
    mock_orchestrator.call_tool.side_effect = [
        {"success": True, "data": {"series_count": 1, "series": [{"id": 1, "title": "Test Show"}]}},
        {
            "success": True,
            "data": {
                "episode_count": 1,
                "episodes": [{"id": 10, "seasonNumber": 1, "episodeNumber": 1}],
            },
        },
        {"success": True, "data": {"id": 999}},
    ]

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert - Check notifications
    events = [call_args[0][0] for call_args in mock_event_bus.publish.call_args_list]

    # Should have: searching notification, success notification, and recovery attempted
    assert len(events) >= 2

    # Find the quality fallback notifications
    qf_events = [e for e in events if "quality_fallback" in e.source]
    assert len(qf_events) >= 2

    # First should be "searching"
    searching_event = qf_events[0]
    assert searching_event.data["status"] == "searching"
    assert "episode" in searching_event.data["content_description"].lower()
    assert "1080p" == searching_event.data["current_quality"]

    # Last should be "success"
    success_event = qf_events[-1]
    assert success_event.data["status"] == "success"


# ============================================================================
# Tests for Enhanced Immediate Retry Notifications
# ============================================================================


@pytest.mark.asyncio
async def test_immediate_retry_emits_notifications(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test immediate retry emits start and success notifications."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Test.mkv",
        failure_reason="connection reset",
        retry_count=0,
    )

    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert
    events = [call_args[0][0] for call_args in mock_event_bus.publish.call_args_list]

    # Should have start and success notifications
    immediate_events = [e for e in events if "immediate" in e.source]
    assert len(immediate_events) >= 2

    # Check notification content
    assert immediate_events[0].data["status"] == "starting"
    assert immediate_events[1].data["status"] == "success"
    assert immediate_events[0].data["attempt_number"] == 1


# ============================================================================
# Tests for Enhanced Exponential Backoff Notifications
# ============================================================================


@pytest.mark.asyncio
async def test_exponential_backoff_emits_notifications_with_delay(
    recovery_service, mock_orchestrator, mock_event_bus
):
    """Test exponential backoff emits notifications with delay information."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Test.mkv",
        failure_reason="disk full",
        retry_count=2,
    )

    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert
    events = [call_args[0][0] for call_args in mock_event_bus.publish.call_args_list]

    # Find backoff notifications
    backoff_events = [e for e in events if "exponential_backof" in e.source]
    assert len(backoff_events) >= 2

    # Check delay is included
    assert backoff_events[0].data["delay_seconds"] > 0
    assert backoff_events[0].data["status"] == "starting"


# ============================================================================
# Tests for Content Matching
# ============================================================================


@pytest.mark.asyncio
async def test_find_series_normalizes_names_correctly(recovery_service, mock_orchestrator):
    """Test series name normalization handles dots, underscores, and case."""
    # Arrange
    # Sonarr provider returns nested data structure
    mock_orchestrator.call_tool.return_value = {
        "success": True,
        "data": {
            "series_count": 2,
            "series": [
                {"id": 1, "title": "The Walking Dead"},
                {"id": 2, "title": "Breaking Bad"},
            ],
        },
    }

    # Act - Test various name formats
    test_cases = [
        "The.Walking.Dead",
        "the walking dead",
        "The_Walking_Dead",
        "walking dead",  # partial match
    ]

    for name in test_cases:
        result = await recovery_service._find_series_id(name)
        # All should match series ID 1
        assert result == 1


@pytest.mark.asyncio
async def test_find_movie_matches_with_year_tolerance(recovery_service, mock_orchestrator):
    """Test movie matching allows 1-year tolerance in year matching."""
    # Arrange
    # Radarr provider returns nested data structure
    mock_orchestrator.call_tool.return_value = {
        "success": True,
        "data": {
            "movie_count": 2,
            "movies": [
                {"id": 1, "title": "The Matrix", "year": 1999},
                {"id": 2, "title": "The Matrix Reloaded", "year": 2003},
            ],
        },
    }

    # Act - Test year tolerance
    # Should match with exact year
    result1 = await recovery_service._find_movie_id("The Matrix", 1999)
    assert result1 == 1

    # Should match with year off by 1
    result2 = await recovery_service._find_movie_id("The Matrix", 2000)
    assert result2 == 1

    result3 = await recovery_service._find_movie_id("The Matrix", 1998)
    assert result3 == 1

    # Should NOT match with year off by 2+
    result4 = await recovery_service._find_movie_id("The Matrix", 2001)
    assert result4 is None
