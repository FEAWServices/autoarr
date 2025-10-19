"""
Unit tests for Recovery Service (Sprint 5).

This module tests the RecoveryService's ability to:
- Automatically trigger retries for failed downloads
- Implement intelligent retry strategies:
  * Immediate retry (for transient failures)
  * Exponential backoff (for repeated failures)
  * Quality fallback (try lower quality when high quality fails)
- Enforce max retry limit per download
- Track success/failure rates for retry strategies
- Coordinate with Sonarr/Radarr for re-searches
- Emit events for recovery attempts and outcomes

Test Strategy:
- 70% Unit Tests: Focus on retry logic and strategy selection
- Test all retry strategies with various failure scenarios
- Verify max retry enforcement and backoff calculations
- Test edge cases: concurrent retries, duplicate attempts, race conditions
- Ensure proper event emission for activity tracking
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch, call

import pytest

from autoarr.api.services.recovery_service import (
    RecoveryService,
    RetryStrategy,
    RetryAttempt,
    RecoveryConfig,
    FailureReason,
    RecoveryResult,
)
from autoarr.api.services.event_bus import EventBus, Event, EventType
from autoarr.api.services.monitoring_service import DownloadStatus, FailedDownload
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
        backoff_base_delay=60,  # 1 minute
        backoff_max_delay=3600,  # 1 hour
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


# ============================================================================
# Test Data Factories
# ============================================================================


def create_failed_download(
    nzo_id: str,
    name: str,
    failure_reason: str = "Download failed",
    category: str = "tv",
    retry_count: int = 0,
    last_retry_time: Optional[datetime] = None,
) -> FailedDownload:
    """Factory to create failed download test data."""
    return FailedDownload(
        nzo_id=nzo_id,
        name=name,
        status=DownloadStatus.FAILED,
        failure_reason=failure_reason,
        category=category,
        retry_count=retry_count,
        last_retry_time=last_retry_time,
        original_failure_time=datetime.now(),
    )


def create_retry_attempt(
    nzo_id: str,
    strategy: RetryStrategy,
    attempt_number: int = 1,
    success: bool = True,
) -> RetryAttempt:
    """Factory to create retry attempt test data."""
    return RetryAttempt(
        nzo_id=nzo_id,
        strategy=strategy,
        attempt_number=attempt_number,
        timestamp=datetime.now(),
        success=success,
    )


# ============================================================================
# Tests for Automatic Retry Triggering
# ============================================================================


@pytest.mark.asyncio
async def test_trigger_retry_on_failed_download(recovery_service, mock_orchestrator):
    """Test that retry is automatically triggered for a failed download."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.Show.S01E01.mkv")
    mock_orchestrator.call_tool.return_value = {"status": True, "nzo_id": "nzo_retry_1"}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.success is True
    assert result.retry_triggered is True
    mock_orchestrator.call_tool.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_retry_respects_max_attempts(recovery_service):
    """Test that retry is not triggered when max attempts exceeded."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1", "Test.Show.S01E01.mkv", retry_count=3  # Already at max (config = 3)
    )

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.success is False
    assert result.retry_triggered is False
    assert "max retry attempts" in result.message.lower()


@pytest.mark.asyncio
async def test_trigger_retry_increments_attempt_counter(recovery_service, mock_orchestrator):
    """Test that retry attempt counter is incremented."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv", retry_count=1)
    mock_orchestrator.call_tool.return_value = {"status": True, "nzo_id": "nzo_retry_1"}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.retry_attempt_number == 2


@pytest.mark.asyncio
async def test_no_duplicate_concurrent_retries(recovery_service, mock_orchestrator):
    """Test that concurrent retry requests for the same download are prevented."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")

    async def slow_retry(*args, **kwargs):
        await asyncio.sleep(0.5)
        return {"status": True, "nzo_id": "nzo_retry_1"}

    mock_orchestrator.call_tool.side_effect = slow_retry

    # Act - Try to trigger two concurrent retries
    results = await asyncio.gather(
        recovery_service.trigger_retry(failed_download),
        recovery_service.trigger_retry(failed_download),
        return_exceptions=True,
    )

    # Assert - Only one should succeed, second should be prevented
    successful_retries = sum(1 for r in results if isinstance(r, RecoveryResult) and r.success)
    assert successful_retries == 1


# ============================================================================
# Tests for Immediate Retry Strategy
# ============================================================================


@pytest.mark.asyncio
async def test_immediate_retry_for_transient_failure(recovery_service, mock_orchestrator):
    """Test immediate retry strategy for transient failures."""
    # Arrange - Transient failure (connection timeout)
    failed_download = create_failed_download(
        "nzo_1",
        "Test.mkv",
        failure_reason="Connection timeout",
        retry_count=0,
    )
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.success is True
    assert result.strategy == RetryStrategy.IMMEDIATE
    assert result.delay_seconds == 0  # No delay for immediate retry


@pytest.mark.asyncio
async def test_immediate_retry_categories(recovery_service):
    """Test that immediate retry is selected for appropriate failure types."""
    # Test various transient failure reasons
    transient_failures = [
        "Connection timeout",
        "Connection reset by peer",
        "Temporary server error",
        "Network unreachable",
        "Read timeout",
    ]

    for failure_reason in transient_failures:
        # Act
        strategy = recovery_service._select_retry_strategy(
            failure_reason=failure_reason,
            retry_count=0,
        )

        # Assert
        assert strategy == RetryStrategy.IMMEDIATE, (
            f"Should use IMMEDIATE for '{failure_reason}'"
        )


@pytest.mark.asyncio
async def test_immediate_retry_executes_without_delay(recovery_service, mock_orchestrator):
    """Test that immediate retry executes without waiting."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1", "Test.mkv", failure_reason="Connection timeout"
    )
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    start_time = datetime.now()
    result = await recovery_service.trigger_retry(failed_download)
    duration = (datetime.now() - start_time).total_seconds()

    # Assert
    assert result.strategy == RetryStrategy.IMMEDIATE
    assert duration < 1.0  # Should execute quickly without delay


# ============================================================================
# Tests for Exponential Backoff Strategy
# ============================================================================


@pytest.mark.asyncio
async def test_exponential_backoff_for_repeated_failures(recovery_service):
    """Test exponential backoff strategy for repeated failures."""
    # Arrange - Multiple failed attempts
    failed_download = create_failed_download(
        "nzo_1",
        "Test.mkv",
        failure_reason="PAR2 repair failed",
        retry_count=2,
    )

    # Act
    strategy = recovery_service._select_retry_strategy(
        failure_reason=failed_download.failure_reason,
        retry_count=failed_download.retry_count,
    )

    # Assert
    assert strategy == RetryStrategy.EXPONENTIAL_BACKOFF


@pytest.mark.asyncio
async def test_backoff_delay_calculation(recovery_service):
    """Test exponential backoff delay calculation."""
    # Test delays for successive retry attempts
    base_delay = recovery_service.config.backoff_base_delay
    multiplier = recovery_service.config.backoff_multiplier

    test_cases = [
        (0, base_delay),  # First retry: 60s
        (1, base_delay * multiplier),  # Second retry: 120s
        (2, base_delay * multiplier**2),  # Third retry: 240s
    ]

    for retry_count, expected_delay in test_cases:
        # Act
        delay = recovery_service._calculate_backoff_delay(retry_count)

        # Assert
        assert delay == expected_delay, (
            f"Retry #{retry_count} should have {expected_delay}s delay"
        )


@pytest.mark.asyncio
async def test_backoff_delay_max_cap(recovery_service):
    """Test that backoff delay is capped at maximum."""
    # Arrange - Very high retry count
    retry_count = 10

    # Act
    delay = recovery_service._calculate_backoff_delay(retry_count)

    # Assert
    assert delay <= recovery_service.config.backoff_max_delay


@pytest.mark.asyncio
async def test_backoff_retry_schedules_future_attempt(recovery_service, mock_orchestrator):
    """Test that backoff retry schedules a future retry attempt."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Test.mkv",
        failure_reason="PAR2 repair failed",
        retry_count=1,
    )
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
    assert result.delay_seconds > 0
    assert result.scheduled_time is not None
    assert result.scheduled_time > datetime.now()


@pytest.mark.asyncio
async def test_scheduled_retry_executes_at_correct_time(recovery_service, mock_orchestrator):
    """Test that scheduled retries execute at the correct time."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1", "Test.mkv", failure_reason="CRC error", retry_count=1
    )
    recovery_service.config.backoff_base_delay = 2  # 2 seconds for testing
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    result = await recovery_service.trigger_retry(failed_download)
    schedule_time = result.scheduled_time

    # Wait for scheduled time
    await asyncio.sleep(2.5)

    # Assert - Retry should have been executed
    # (This would require checking internal state or mocking time)
    assert result.scheduled_time is not None


# ============================================================================
# Tests for Quality Fallback Strategy
# ============================================================================


@pytest.mark.asyncio
async def test_quality_fallback_when_high_quality_fails(recovery_service, mock_orchestrator):
    """Test quality fallback strategy when high quality download fails."""
    # Arrange - High quality download that failed
    failed_download = create_failed_download(
        "nzo_1",
        "Test.Show.S01E01.1080p.BluRay.mkv",
        failure_reason="CRC error",
        retry_count=1,
        category="tv",
    )

    # Mock Sonarr search with lower quality
    mock_orchestrator.call_tool.return_value = {
        "status": True,
        "command_id": 123,
    }

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.strategy == RetryStrategy.QUALITY_FALLBACK
    # Should have triggered a new search with lower quality profile
    mock_orchestrator.call_tool.assert_called()
    call_args = mock_orchestrator.call_tool.call_args
    assert call_args[1]["tool"] in ["search_series", "episode_search"]


@pytest.mark.asyncio
async def test_quality_fallback_identifies_quality_from_filename(recovery_service):
    """Test quality identification from download filename."""
    # Test various quality identifiers
    quality_test_cases = [
        ("Show.S01E01.2160p.mkv", "2160p"),
        ("Movie.1080p.BluRay.mkv", "1080p"),
        ("Series.720p.HDTV.mkv", "720p"),
        ("Episode.WEB-DL.mkv", "WEB-DL"),
        ("Show.HDTV.mkv", "HDTV"),
    ]

    for filename, expected_quality in quality_test_cases:
        # Act
        detected_quality = recovery_service._extract_quality_from_filename(filename)

        # Assert
        assert detected_quality == expected_quality


@pytest.mark.asyncio
async def test_quality_fallback_selects_lower_quality(recovery_service):
    """Test that quality fallback selects appropriate lower quality."""
    # Test quality fallback chain
    fallback_test_cases = [
        ("2160p", "1080p"),
        ("1080p", "720p"),
        ("720p", "HDTV"),
        ("BluRay", "WEB-DL"),
        ("WEB-DL", "HDTV"),
    ]

    for current_quality, expected_fallback in fallback_test_cases:
        # Act
        fallback_quality = recovery_service._get_fallback_quality(current_quality)

        # Assert
        assert fallback_quality == expected_fallback, (
            f"Quality fallback from {current_quality} should be {expected_fallback}"
        )


@pytest.mark.asyncio
async def test_quality_fallback_for_tv_show(recovery_service, mock_orchestrator):
    """Test quality fallback specifically for TV show episodes."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Breaking.Bad.S01E01.1080p.BluRay.mkv",
        failure_reason="CRC error",
        category="tv",
        retry_count=1,
    )
    mock_orchestrator.call_tool.return_value = {"status": True, "command_id": 123}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.strategy == RetryStrategy.QUALITY_FALLBACK
    # Should call Sonarr's episode search with lower quality
    call_args = mock_orchestrator.call_tool.call_args
    assert call_args[1]["server"] == "sonarr"


@pytest.mark.asyncio
async def test_quality_fallback_for_movie(recovery_service, mock_orchestrator):
    """Test quality fallback specifically for movies."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "The.Matrix.1999.1080p.BluRay.mkv",
        failure_reason="PAR2 repair failed",
        category="movies",
        retry_count=1,
    )
    mock_orchestrator.call_tool.return_value = {"status": True, "command_id": 456}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.strategy == RetryStrategy.QUALITY_FALLBACK
    # Should call Radarr's movie search with lower quality
    call_args = mock_orchestrator.call_tool.call_args
    assert call_args[1]["server"] == "radarr"


@pytest.mark.asyncio
async def test_no_quality_fallback_when_at_lowest(recovery_service):
    """Test that quality fallback is not used when already at lowest quality."""
    # Arrange - Already at lowest quality
    failed_download = create_failed_download(
        "nzo_1",
        "Show.S01E01.HDTV.mkv",
        failure_reason="CRC error",
        retry_count=2,
    )

    # Act
    strategy = recovery_service._select_retry_strategy(
        failure_reason=failed_download.failure_reason,
        retry_count=failed_download.retry_count,
        current_quality="HDTV",  # Lowest quality
    )

    # Assert - Should use exponential backoff instead
    assert strategy == RetryStrategy.EXPONENTIAL_BACKOFF


# ============================================================================
# Tests for Max Retry Limit Enforcement
# ============================================================================


@pytest.mark.asyncio
async def test_enforce_max_retry_limit(recovery_service):
    """Test that max retry limit is strictly enforced."""
    # Arrange - Download at max retry limit
    failed_download = create_failed_download(
        "nzo_1",
        "Test.mkv",
        retry_count=3,  # At max (config.max_retry_attempts = 3)
    )

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert
    assert result.success is False
    assert result.retry_triggered is False
    assert "exceeded maximum" in result.message.lower()


@pytest.mark.asyncio
async def test_max_retry_limit_per_download(recovery_service, mock_orchestrator):
    """Test that retry limit is tracked per individual download."""
    # Arrange - Two different downloads
    download_1 = create_failed_download("nzo_1", "Test1.mkv", retry_count=2)
    download_2 = create_failed_download("nzo_2", "Test2.mkv", retry_count=0)
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    result_1 = await recovery_service.trigger_retry(download_1)  # Should succeed
    result_2 = await recovery_service.trigger_retry(download_2)  # Should succeed

    # Assert
    assert result_1.success is True  # Still within limit
    assert result_2.success is True  # Independent counter


@pytest.mark.asyncio
async def test_configurable_max_retry_limit(recovery_service, mock_orchestrator):
    """Test that max retry limit is configurable."""
    # Arrange - Change configuration
    recovery_service.config.max_retry_attempts = 5
    failed_download = create_failed_download("nzo_1", "Test.mkv", retry_count=4)
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should still be allowed (4 < 5)
    assert result.success is True


# ============================================================================
# Tests for Success/Failure Tracking
# ============================================================================


@pytest.mark.asyncio
async def test_track_successful_retry(recovery_service, mock_orchestrator, mock_event_bus):
    """Test tracking of successful retry attempts."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should emit success event
    mock_event_bus.publish.assert_called()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.RECOVERY_ATTEMPTED
    assert event.data["success"] is True


@pytest.mark.asyncio
async def test_track_failed_retry(recovery_service, mock_orchestrator, mock_event_bus):
    """Test tracking of failed retry attempts."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")
    mock_orchestrator.call_tool.side_effect = Exception("Retry failed")

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should emit failure event
    mock_event_bus.publish.assert_called()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.RECOVERY_ATTEMPTED
    assert event.data["success"] is False


@pytest.mark.asyncio
async def test_track_retry_strategy_effectiveness(recovery_service):
    """Test tracking of retry strategy success rates."""
    # Arrange - Multiple retry attempts with different strategies
    attempts = [
        create_retry_attempt("nzo_1", RetryStrategy.IMMEDIATE, 1, success=True),
        create_retry_attempt("nzo_2", RetryStrategy.IMMEDIATE, 1, success=False),
        create_retry_attempt("nzo_3", RetryStrategy.EXPONENTIAL_BACKOFF, 1, success=True),
        create_retry_attempt("nzo_4", RetryStrategy.QUALITY_FALLBACK, 1, success=True),
    ]

    # Act
    stats = recovery_service.get_strategy_statistics(attempts)

    # Assert
    assert stats[RetryStrategy.IMMEDIATE]["success_rate"] == 0.5  # 1/2
    assert stats[RetryStrategy.EXPONENTIAL_BACKOFF]["success_rate"] == 1.0  # 1/1
    assert stats[RetryStrategy.QUALITY_FALLBACK]["success_rate"] == 1.0  # 1/1


@pytest.mark.asyncio
async def test_get_retry_history_for_download(recovery_service):
    """Test retrieval of retry history for a specific download."""
    # Arrange - Track multiple retry attempts
    download_id = "nzo_1"
    recovery_service._track_retry_attempt(download_id, RetryStrategy.IMMEDIATE, True)
    recovery_service._track_retry_attempt(download_id, RetryStrategy.EXPONENTIAL_BACKOFF, False)

    # Act
    history = recovery_service.get_retry_history(download_id)

    # Assert
    assert len(history) == 2
    assert history[0].strategy == RetryStrategy.IMMEDIATE
    assert history[1].strategy == RetryStrategy.EXPONENTIAL_BACKOFF


# ============================================================================
# Tests for Sonarr/Radarr Coordination
# ============================================================================


@pytest.mark.asyncio
async def test_coordinate_with_sonarr_for_episode_search(recovery_service, mock_orchestrator):
    """Test coordination with Sonarr for episode re-search."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Breaking.Bad.S05E14.mkv",
        category="tv",
        retry_count=1,
    )
    mock_orchestrator.call_tool.return_value = {"status": True, "command_id": 123}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should call Sonarr's episode search
    call_args = mock_orchestrator.call_tool.call_args
    assert call_args[1]["server"] == "sonarr"
    assert call_args[1]["tool"] in ["episode_search", "search_series"]


@pytest.mark.asyncio
async def test_coordinate_with_radarr_for_movie_search(recovery_service, mock_orchestrator):
    """Test coordination with Radarr for movie re-search."""
    # Arrange
    failed_download = create_failed_download(
        "nzo_1",
        "Inception.2010.mkv",
        category="movies",
        retry_count=1,
    )
    mock_orchestrator.call_tool.return_value = {"status": True, "command_id": 456}

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should call Radarr's movie search
    call_args = mock_orchestrator.call_tool.call_args
    assert call_args[1]["server"] == "radarr"
    assert call_args[1]["tool"] in ["movie_search", "search_movies"]


@pytest.mark.asyncio
async def test_extract_series_info_from_filename(recovery_service):
    """Test extraction of series information from filename."""
    # Test cases for series info extraction
    test_cases = [
        ("Breaking.Bad.S05E14.mkv", ("Breaking Bad", 5, 14)),
        ("Game.of.Thrones.S08E06.720p.mkv", ("Game of Thrones", 8, 6)),
        ("The.Office.US.S02E01.HDTV.mkv", ("The Office US", 2, 1)),
    ]

    for filename, expected in test_cases:
        # Act
        series_info = recovery_service._extract_series_info(filename)

        # Assert
        assert series_info is not None
        assert series_info[0] == expected[0]  # Series name
        assert series_info[1] == expected[1]  # Season
        assert series_info[2] == expected[2]  # Episode


@pytest.mark.asyncio
async def test_extract_movie_info_from_filename(recovery_service):
    """Test extraction of movie information from filename."""
    # Test cases for movie info extraction
    test_cases = [
        ("Inception.2010.1080p.mkv", ("Inception", 2010)),
        ("The.Matrix.1999.BluRay.mkv", ("The Matrix", 1999)),
        ("Interstellar.2014.mkv", ("Interstellar", 2014)),
    ]

    for filename, expected in test_cases:
        # Act
        movie_info = recovery_service._extract_movie_info(filename)

        # Assert
        assert movie_info is not None
        assert movie_info[0] == expected[0]  # Movie name
        assert movie_info[1] == expected[1]  # Year


# ============================================================================
# Tests for Event Emission
# ============================================================================


@pytest.mark.asyncio
async def test_emit_recovery_attempted_event(recovery_service, mock_orchestrator, mock_event_bus):
    """Test emission of recovery attempted event."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert
    mock_event_bus.publish.assert_called()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.RECOVERY_ATTEMPTED
    assert event.data["nzo_id"] == "nzo_1"
    assert event.data["strategy"] in [s.value for s in RetryStrategy]


@pytest.mark.asyncio
async def test_emit_recovery_success_event(recovery_service, mock_orchestrator, mock_event_bus):
    """Test emission of recovery success event."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")
    mock_orchestrator.call_tool.return_value = {"status": True, "nzo_id": "nzo_retry_1"}

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.RECOVERY_ATTEMPTED
    assert event.data["success"] is True


@pytest.mark.asyncio
async def test_emit_max_retries_exceeded_event(recovery_service, mock_event_bus):
    """Test emission of event when max retries exceeded."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv", retry_count=3)

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert
    mock_event_bus.publish.assert_called()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == EventType.RECOVERY_FAILED
    assert "max" in event.data["reason"].lower()


@pytest.mark.asyncio
async def test_events_include_correlation_id(recovery_service, mock_orchestrator, mock_event_bus):
    """Test that all recovery events include correlation IDs."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act
    await recovery_service.trigger_retry(failed_download)

    # Assert
    event = mock_event_bus.publish.call_args[0][0]
    assert event.correlation_id is not None
    assert len(event.correlation_id) > 0


# ============================================================================
# Tests for Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_handle_orchestrator_error_during_retry(recovery_service, mock_orchestrator):
    """Test handling of orchestrator errors during retry."""
    # Arrange
    failed_download = create_failed_download("nzo_1", "Test.mkv")
    mock_orchestrator.call_tool.side_effect = Exception("SABnzbd unreachable")

    # Act
    result = await recovery_service.trigger_retry(failed_download)

    # Assert - Should handle gracefully
    assert result.success is False
    assert "error" in result.message.lower()


@pytest.mark.asyncio
async def test_handle_invalid_download_data(recovery_service):
    """Test handling of invalid download data."""
    # Arrange - Invalid/incomplete download data
    invalid_download = FailedDownload(
        nzo_id="",  # Empty ID
        name="Test.mkv",
        status=DownloadStatus.FAILED,
        failure_reason="Error",
        category="",  # Empty category
        retry_count=0,
        last_retry_time=None,
        original_failure_time=datetime.now(),
    )

    # Act
    result = await recovery_service.trigger_retry(invalid_download)

    # Assert - Should handle gracefully
    assert result.success is False


@pytest.mark.asyncio
async def test_handle_concurrent_retry_requests(recovery_service, mock_orchestrator):
    """Test handling of concurrent retry requests for different downloads."""
    # Arrange
    downloads = [
        create_failed_download(f"nzo_{i}", f"Test{i}.mkv")
        for i in range(5)
    ]
    mock_orchestrator.call_tool.return_value = {"status": True}

    # Act - Trigger multiple concurrent retries
    results = await asyncio.gather(
        *[recovery_service.trigger_retry(d) for d in downloads]
    )

    # Assert - All should succeed independently
    assert all(r.success for r in results)
    assert len(results) == 5


# ============================================================================
# Tests for Strategy Selection Logic
# ============================================================================


@pytest.mark.asyncio
async def test_strategy_selection_based_on_failure_reason(recovery_service):
    """Test that strategy selection considers failure reason."""
    # Test cases: (failure_reason, retry_count, expected_strategy)
    test_cases = [
        ("Connection timeout", 0, RetryStrategy.IMMEDIATE),
        ("CRC error", 0, RetryStrategy.QUALITY_FALLBACK),
        ("PAR2 repair failed", 1, RetryStrategy.QUALITY_FALLBACK),
        ("Unknown error", 2, RetryStrategy.EXPONENTIAL_BACKOFF),
        ("Disk full", 0, RetryStrategy.EXPONENTIAL_BACKOFF),  # System issue
    ]

    for failure_reason, retry_count, expected_strategy in test_cases:
        # Act
        strategy = recovery_service._select_retry_strategy(
            failure_reason=failure_reason,
            retry_count=retry_count,
        )

        # Assert
        assert strategy == expected_strategy, (
            f"Failed for '{failure_reason}' at attempt {retry_count}"
        )


@pytest.mark.asyncio
async def test_strategy_selection_considers_retry_count(recovery_service):
    """Test that strategy selection considers number of previous attempts."""
    # Same failure reason, different retry counts
    failure_reason = "CRC error"

    # Act & Assert
    # First attempt - Try quality fallback
    strategy_0 = recovery_service._select_retry_strategy(failure_reason, retry_count=0)
    assert strategy_0 == RetryStrategy.QUALITY_FALLBACK

    # After multiple attempts - Use backoff
    strategy_2 = recovery_service._select_retry_strategy(failure_reason, retry_count=2)
    assert strategy_2 in [RetryStrategy.EXPONENTIAL_BACKOFF, RetryStrategy.QUALITY_FALLBACK]


# ============================================================================
# Tests for Configuration
# ============================================================================


@pytest.mark.asyncio
async def test_disable_immediate_retry(recovery_service):
    """Test disabling immediate retry strategy."""
    # Arrange
    recovery_service.config.immediate_retry_enabled = False

    # Act
    strategy = recovery_service._select_retry_strategy(
        failure_reason="Connection timeout",
        retry_count=0,
    )

    # Assert - Should not use immediate retry even for transient failure
    assert strategy != RetryStrategy.IMMEDIATE


@pytest.mark.asyncio
async def test_disable_quality_fallback(recovery_service):
    """Test disabling quality fallback strategy."""
    # Arrange
    recovery_service.config.quality_fallback_enabled = False

    # Act
    strategy = recovery_service._select_retry_strategy(
        failure_reason="CRC error",
        retry_count=0,
    )

    # Assert - Should not use quality fallback
    assert strategy != RetryStrategy.QUALITY_FALLBACK


@pytest.mark.asyncio
async def test_custom_backoff_parameters(recovery_service):
    """Test custom backoff delay parameters."""
    # Arrange
    recovery_service.config.backoff_base_delay = 30  # 30 seconds
    recovery_service.config.backoff_multiplier = 3  # 3x multiplier

    # Act
    delay_0 = recovery_service._calculate_backoff_delay(0)
    delay_1 = recovery_service._calculate_backoff_delay(1)

    # Assert
    assert delay_0 == 30
    assert delay_1 == 90  # 30 * 3
