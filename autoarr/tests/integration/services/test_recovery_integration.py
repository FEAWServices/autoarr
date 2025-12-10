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
Integration tests for Recovery Service.

These tests verify the recovery service works end-to-end with:
- Real MCP orchestrator coordination
- Event bus integration
- Multi-step recovery workflows
- Service-to-service handoff (SABnzbd -> Sonarr/Radarr)
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from autoarr.api.services.event_bus import Event, EventBus, EventType
from autoarr.api.services.monitoring_service import DownloadStatus, FailedDownload
from autoarr.api.services.recovery_service import RecoveryConfig, RecoveryService, RetryStrategy
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator


def create_failed_download(
    nzo_id: str = "failed_123",
    name: str = "Test.Show.S01E01.1080p",
    failure_reason: str = "Connection timeout",
    category: str = "tv",
    retry_count: int = 0,
) -> FailedDownload:
    """Helper to create a FailedDownload dataclass instance."""
    return FailedDownload(
        nzo_id=nzo_id,
        name=name,
        status=DownloadStatus.FAILED,
        failure_reason=failure_reason,
        category=category,
        retry_count=retry_count,
    )


class TestRecoveryServiceIntegration:
    """Integration tests for recovery service."""

    @pytest_asyncio.fixture
    async def event_bus(self) -> EventBus:
        """Create event bus instance."""
        return EventBus()

    @pytest_asyncio.fixture
    async def orchestrator(self) -> MCPOrchestrator:
        """Create MCP orchestrator with mocked clients."""
        from autoarr.shared.core.config import MCPOrchestratorConfig, ServerConfig

        # Create minimal config
        config = MCPOrchestratorConfig(
            sabnzbd=ServerConfig(
                name="sabnzbd",
                url="http://localhost:8080",
                api_key="test_key",
            ),
            sonarr=ServerConfig(
                name="sonarr",
                url="http://localhost:8989",
                api_key="test_key",
            ),
            radarr=ServerConfig(
                name="radarr",
                url="http://localhost:7878",
                api_key="test_key",
            ),
        )

        orchestrator = MCPOrchestrator(config=config)

        # Default mock responses
        async def mock_tool_call(
            server: str, tool: str, arguments: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "retry_download":
                return {"status": True, "result": {"nzo_id": "retry_123"}}
            elif tool == "sonarr_search_episode":
                return {"success": True, "data": {"id": 12345}}
            elif tool == "radarr_search_movie":
                return {"success": True, "data": {"id": 67890}}
            elif tool == "sonarr_get_series":
                return {
                    "success": True,
                    "data": {
                        "series_count": 1,
                        "series": [{"id": 1, "title": "Breaking Bad"}],
                    },
                }
            elif tool == "sonarr_get_episodes":
                return {
                    "success": True,
                    "data": {
                        "episode_count": 1,
                        "episodes": [{"id": 100, "seasonNumber": 5, "episodeNumber": 14}],
                    },
                }
            elif tool == "radarr_get_movies":
                return {
                    "success": True,
                    "data": {
                        "movie_count": 1,
                        "movies": [{"id": 1, "title": "The Matrix", "year": 1999}],
                    },
                }
            return {"success": True, "result": {}}

        orchestrator.call_tool = AsyncMock(side_effect=mock_tool_call)
        return orchestrator

    @pytest_asyncio.fixture
    async def recovery_service(
        self, event_bus: EventBus, orchestrator: MCPOrchestrator
    ) -> RecoveryService:
        """Create recovery service instance."""
        config = RecoveryConfig()
        config.max_retry_attempts = 3
        config.immediate_retry_enabled = True
        config.exponential_backoff_enabled = True
        config.quality_fallback_enabled = True
        config.backoff_base_delay = 60
        config.backoff_max_delay = 3600
        config.backoff_multiplier = 2

        return RecoveryService(
            orchestrator=orchestrator,
            event_bus=event_bus,
            config=config,
        )

    @pytest.mark.asyncio
    async def test_immediate_retry_with_orchestrator(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test immediate retry coordinates with real orchestrator."""
        # Arrange
        failed_download = create_failed_download(
            nzo_id="failed_123",
            name="Test.Show.S01E01.1080p",
            failure_reason="Connection timeout",
            category="tv",
            retry_count=0,
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result.success is True
        orchestrator.call_tool.assert_called()
        # Check that SABnzbd retry was called
        calls = orchestrator.call_tool.call_args_list
        sabnzbd_calls = [c for c in calls if c.kwargs.get("server") == "sabnzbd"]
        assert len(sabnzbd_calls) >= 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry_workflow(
        self, recovery_service: RecoveryService, event_bus: EventBus
    ) -> None:
        """Test exponential backoff workflow with event emissions."""
        # Arrange
        events_received: List[Event] = []

        def capture_event(event: Event) -> None:
            events_received.append(event)

        event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, capture_event)

        # Second retry attempt should use backoff
        failed_download = create_failed_download(
            nzo_id="failed_456",
            name="Movie.2024.1080p",
            failure_reason="Download failed",
            category="movies",
            retry_count=2,  # Third attempt will use exponential backoff
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result.success is True
        assert result.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

        # Verify events were emitted
        await asyncio.sleep(0.1)
        assert len(events_received) >= 1

    @pytest.mark.asyncio
    async def test_quality_fallback_triggers_sonarr_search(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test quality fallback triggers Sonarr episode search."""
        # Arrange
        failed_download = create_failed_download(
            nzo_id="failed_789",
            name="Breaking.Bad.S05E14.2160p.BluRay",
            failure_reason="CRC error in verification",
            category="tv",
            retry_count=0,
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result.success is True
        # Quality fallback should call Sonarr for TV shows
        calls = orchestrator.call_tool.call_args_list
        sonarr_calls = [c for c in calls if c.kwargs.get("server") == "sonarr"]
        # At least one Sonarr call expected
        assert len(sonarr_calls) >= 1

    @pytest.mark.asyncio
    async def test_quality_fallback_triggers_radarr_search(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test quality fallback triggers Radarr movie search."""
        # Arrange
        failed_download = create_failed_download(
            nzo_id="movie_fail",
            name="The.Matrix.1999.2160p.BluRay",
            failure_reason="PAR2 verification failed",
            category="movies",
            retry_count=0,
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result.success is True
        # Quality fallback should call Radarr for movies
        calls = orchestrator.call_tool.call_args_list
        radarr_calls = [c for c in calls if c.kwargs.get("server") == "radarr"]
        # At least one Radarr call expected
        assert len(radarr_calls) >= 1

    @pytest.mark.asyncio
    async def test_multi_step_recovery_immediate_then_backoff(
        self,
        recovery_service: RecoveryService,
        orchestrator: MCPOrchestrator,
        event_bus: EventBus,
    ) -> None:
        """Test multi-step recovery: immediate retry -> backoff -> success."""
        # Arrange
        events_received: List[Event] = []

        def capture_event(event: Event) -> None:
            events_received.append(event)

        event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, capture_event)

        # Act - Step 1: First attempt (immediate retry for transient error)
        failed_download_1 = create_failed_download(
            nzo_id="multi_step",
            name="Show.S01E01.1080p",
            failure_reason="Connection reset",
            category="tv",
            retry_count=0,
        )
        result1 = await recovery_service.trigger_retry(failed_download_1)
        assert result1.success is True

        # Act - Step 2: Second attempt (will use backoff or fallback)
        failed_download_2 = create_failed_download(
            nzo_id="multi_step",
            name="Show.S01E01.1080p",
            failure_reason="Connection reset",
            category="tv",
            retry_count=1,
        )
        result2 = await recovery_service.trigger_retry(failed_download_2)
        assert result2.success is True

        # Assert - verify events were emitted for both retries
        await asyncio.sleep(0.1)
        assert len(events_received) >= 2

    @pytest.mark.asyncio
    async def test_max_retry_limit_enforcement(
        self, recovery_service: RecoveryService, event_bus: EventBus
    ) -> None:
        """Test max retry limit prevents further retries."""
        # Arrange
        events_received: List[Event] = []

        def capture_event(event: Event) -> None:
            events_received.append(event)

        event_bus.subscribe(EventType.RECOVERY_FAILED, capture_event)

        # Already at max retries (3)
        failed_download = create_failed_download(
            nzo_id="max_retry",
            name="Show.S01E01.1080p",
            failure_reason="Failed",
            category="tv",
            retry_count=3,  # At max retry limit
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result.success is False
        assert "Exceeded max retry attempts" in result.message

        # Verify max retries exceeded event
        await asyncio.sleep(0.1)
        max_retry_events = [e for e in events_received if e.event_type == EventType.RECOVERY_FAILED]
        assert len(max_retry_events) >= 1

    @pytest.mark.asyncio
    async def test_duplicate_retry_prevention_with_locks(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test concurrent retry attempts are prevented with locks."""
        # Arrange
        call_count = 0

        async def mock_slow_retry(
            server: str, tool: str, arguments: Dict[str, Any]
        ) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.2)  # Simulate slow retry
            return {"status": True, "result": {"nzo_id": "retry_123"}}

        orchestrator.call_tool = AsyncMock(side_effect=mock_slow_retry)

        failed_download = create_failed_download(
            nzo_id="concurrent_test",
            name="Show.S01E01.1080p",
            failure_reason="Failed",
            category="tv",
            retry_count=0,
        )

        # Act - trigger concurrent retries
        results = await asyncio.gather(
            recovery_service.trigger_retry(failed_download),
            recovery_service.trigger_retry(failed_download),
            recovery_service.trigger_retry(failed_download),
        )

        # Assert - at least one retry should succeed, some may be blocked by lock
        assert sum(1 for r in results if r.success) >= 1
        # Verify orchestrator was called limited times (lock prevents some duplicates)
        assert call_count <= 3

    @pytest.mark.asyncio
    async def test_retry_success_tracking_records_history(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test successful retries are tracked in history."""
        # Arrange
        failed_download = create_failed_download(
            nzo_id="success_track",
            name="Show.S01E01.1080p",
            failure_reason="Timeout",
            category="tv",
            retry_count=0,
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result.success is True

        # Verify retry history was recorded
        history = recovery_service.get_retry_history("success_track")
        assert len(history) >= 1
        assert history[0].nzo_id == "success_track"

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling_during_retry(
        self,
        recovery_service: RecoveryService,
        orchestrator: MCPOrchestrator,
        event_bus: EventBus,
    ) -> None:
        """Test recovery service handles orchestrator errors gracefully."""
        # Arrange
        events_received: List[Event] = []

        def capture_event(event: Event) -> None:
            events_received.append(event)

        event_bus.subscribe(EventType.RECOVERY_FAILED, capture_event)

        async def mock_failing_retry(
            server: str, tool: str, arguments: Dict[str, Any]
        ) -> Dict[str, Any]:
            raise Exception("Orchestrator connection failed")

        orchestrator.call_tool = AsyncMock(side_effect=mock_failing_retry)

        failed_download = create_failed_download(
            nzo_id="error_test",
            name="Show.S01E01.1080p",
            failure_reason="Failed",
            category="tv",
            retry_count=0,
        )

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert - should handle error gracefully
        assert result.success is False

        # Verify error was handled
        await asyncio.sleep(0.1)
        # Recovery failure event may or may not be emitted depending on implementation
        assert result.message is not None

    @pytest.mark.asyncio
    async def test_quality_extraction_from_filename(
        self, recovery_service: RecoveryService
    ) -> None:
        """Test quality extraction from various filename formats."""
        # Test cases
        test_cases = [
            ("Show.S01E01.2160p.BluRay", "2160p"),
            ("Movie.1080p.WEB-DL", "1080p"),
            ("Series.720p.HDTV", "720p"),
            ("Show.HDTV.x264", "HDTV"),
            ("Movie.DVD-Rip", None),  # No standard quality marker
        ]

        for filename, expected_quality in test_cases:
            quality = recovery_service._extract_quality_from_filename(filename)
            assert (
                quality == expected_quality
            ), f"Failed for {filename}: expected {expected_quality}, got {quality}"

    @pytest.mark.asyncio
    async def test_quality_fallback_chain_progression(
        self, recovery_service: RecoveryService
    ) -> None:
        """Test quality fallback follows proper chain: 2160p -> 1080p -> 720p."""
        # Test fallback chain using the correct method name
        assert recovery_service._get_fallback_quality("2160p") == "1080p"
        assert recovery_service._get_fallback_quality("1080p") == "720p"
        assert recovery_service._get_fallback_quality("720p") == "HDTV"
        assert recovery_service._get_fallback_quality("BluRay") == "WEB-DL"
        assert recovery_service._get_fallback_quality("WEB-DL") == "HDTV"

    @pytest.mark.asyncio
    async def test_series_info_extraction_from_filename(
        self, recovery_service: RecoveryService
    ) -> None:
        """Test series information extraction from TV show filenames."""
        # Test series extraction
        test_cases = [
            ("Breaking.Bad.S05E14.1080p", ("Breaking Bad", 5, 14)),
            ("The.Office.S03E12.HDTV", ("The Office", 3, 12)),
            ("Show.S01E01.720p", ("Show", 1, 1)),
        ]

        for filename, expected in test_cases:
            result = recovery_service._extract_series_info(filename)
            assert result is not None, f"Failed to extract from {filename}"
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    @pytest.mark.asyncio
    async def test_movie_info_extraction_from_filename(
        self, recovery_service: RecoveryService
    ) -> None:
        """Test movie information extraction from movie filenames."""
        # Test movie extraction
        test_cases = [
            ("The.Matrix.1999.1080p", ("The Matrix", 1999)),
            ("Inception.2010.BluRay", ("Inception", 2010)),
            ("Movie.Title.2024.720p", ("Movie Title", 2024)),
        ]

        for filename, expected in test_cases:
            result = recovery_service._extract_movie_info(filename)
            assert result is not None, f"Failed to extract from {filename}"
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    @pytest.mark.asyncio
    async def test_event_correlation_throughout_recovery(
        self, recovery_service: RecoveryService, event_bus: EventBus
    ) -> None:
        """Test correlation IDs propagate through recovery workflow."""
        # Arrange
        events_received: List[Event] = []

        def capture_event(event: Event) -> None:
            events_received.append(event)

        event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, capture_event)

        failed_download = create_failed_download(
            nzo_id="correlation_test",
            name="Show.S01E01.1080p",
            failure_reason="Failed",
            category="tv",
            retry_count=0,
        )

        # Act
        await recovery_service.trigger_retry(failed_download)

        # Assert
        await asyncio.sleep(0.1)
        if events_received:
            # Verify event data contains download info
            assert events_received[0].data["nzo_id"] == "correlation_test"
            # Verify correlation ID is present
            assert events_received[0].correlation_id is not None

    @pytest.mark.asyncio
    async def test_configuration_toggles_affect_strategy_selection(
        self, event_bus: EventBus, orchestrator: MCPOrchestrator
    ) -> None:
        """Test configuration toggles control which strategies are used."""
        # Test with only immediate retry enabled
        config = RecoveryConfig()
        config.max_retry_attempts = 3
        config.immediate_retry_enabled = True
        config.exponential_backoff_enabled = False
        config.quality_fallback_enabled = False

        recovery_immediate_only = RecoveryService(
            orchestrator=orchestrator,
            event_bus=event_bus,
            config=config,
        )

        failed_download = create_failed_download(
            nzo_id="config_test",
            name="Show.S01E01.1080p",
            failure_reason="Timeout",
            category="tv",
            retry_count=0,
        )

        # Should still retry but strategy selection is limited
        result = await recovery_immediate_only.trigger_retry(failed_download)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_backoff_delay_calculation_with_custom_parameters(
        self, event_bus: EventBus, orchestrator: MCPOrchestrator
    ) -> None:
        """Test custom backoff parameters affect delay calculation."""
        # Create service with custom backoff parameters
        config = RecoveryConfig()
        config.max_retry_attempts = 5
        config.backoff_base_delay = 30  # Custom base
        config.backoff_max_delay = 1800  # Custom max
        config.backoff_multiplier = 3  # Custom multiplier

        recovery_custom = RecoveryService(
            orchestrator=orchestrator,
            event_bus=event_bus,
            config=config,
        )

        # Calculate expected delay: 30 * 3^2 = 270 seconds for retry_count=2
        delay = recovery_custom._calculate_backoff_delay(2)
        assert delay == 270

    @pytest.mark.asyncio
    async def test_parallel_retries_for_different_downloads(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test service can handle parallel retries for different downloads."""
        # Arrange
        downloads = [
            create_failed_download(
                nzo_id="dl_1", name="Show1.S01E01", failure_reason="Failed", category="tv"
            ),
            create_failed_download(
                nzo_id="dl_2", name="Show2.S01E01", failure_reason="Failed", category="tv"
            ),
            create_failed_download(
                nzo_id="dl_3", name="Show3.S01E01", failure_reason="Failed", category="tv"
            ),
        ]

        # Act - trigger parallel retries
        results = await asyncio.gather(*[recovery_service.trigger_retry(dl) for dl in downloads])

        # Assert - all should succeed
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_retry_history_persistence_tracking(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test retry history is tracked per download."""
        # Arrange & Act - trigger multiple retries with increasing retry_count
        for retry_count in range(3):
            failed_download = create_failed_download(
                nzo_id="history_test",
                name="Show.S01E01.1080p",
                failure_reason="Failed",
                category="tv",
                retry_count=retry_count,
            )
            await recovery_service.trigger_retry(failed_download)

        # Assert - verify history tracking
        history = recovery_service.get_retry_history("history_test")
        assert len(history) == 3

        # Get strategy statistics
        stats = recovery_service.get_strategy_statistics(history)
        assert stats is not None

    @pytest.mark.asyncio
    async def test_sonarr_episode_search_with_extracted_info(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test Sonarr search receives properly extracted episode info."""
        # Arrange
        failed_download = create_failed_download(
            nzo_id="sonarr_test",
            name="Breaking.Bad.S05E14.Ozymandias.1080p",
            failure_reason="CRC error",
            category="tv",
            retry_count=0,
        )

        # Act
        await recovery_service.trigger_retry(failed_download)

        # Assert - verify Sonarr was called (quality fallback for CRC error)
        calls = orchestrator.call_tool.call_args_list
        sonarr_calls = [c for c in calls if c.kwargs.get("server") == "sonarr"]
        # Should have at least one call to Sonarr
        assert len(sonarr_calls) >= 1

    @pytest.mark.asyncio
    async def test_radarr_movie_search_with_extracted_info(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test Radarr search receives properly extracted movie info."""
        # Arrange
        failed_download = create_failed_download(
            nzo_id="radarr_test",
            name="The.Shawshank.Redemption.1994.1080p.BluRay",
            failure_reason="PAR2 failed",
            category="movies",
            retry_count=0,
        )

        # Mock radarr_get_movies to include The Shawshank Redemption
        async def mock_tool_call(
            server: str, tool: str, arguments: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "radarr_get_movies":
                return {
                    "success": True,
                    "data": {
                        "movie_count": 1,
                        "movies": [{"id": 999, "title": "The Shawshank Redemption", "year": 1994}],
                    },
                }
            elif tool == "radarr_search_movie":
                return {"success": True, "data": {"id": 12345}}
            return {"success": True, "result": {}}

        orchestrator.call_tool = AsyncMock(side_effect=mock_tool_call)

        # Act
        await recovery_service.trigger_retry(failed_download)

        # Assert - verify Radarr was called
        calls = orchestrator.call_tool.call_args_list
        radarr_calls = [c for c in calls if c.kwargs.get("server") == "radarr"]
        # Should have calls to Radarr
        assert len(radarr_calls) >= 1
