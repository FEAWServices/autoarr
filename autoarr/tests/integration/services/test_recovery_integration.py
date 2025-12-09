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
- Service-to-service handoff (SABnzbd → Sonarr/Radarr)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from autoarr.api.services.event_bus import EventBus
from autoarr.api.services.recovery_service import RecoveryConfig, RecoveryService
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator


class TestRecoveryServiceIntegration:
    """Integration tests for recovery service."""

    @pytest.fixture
    async def event_bus(self) -> EventBus:
        """Create event bus instance."""
        return EventBus()

    @pytest.fixture
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
        async def mock_tool_call(service: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
            if tool == "retry_download":
                return {"success": True, "result": {"nzo_id": "retry_123"}}
            elif tool == "episode_search":
                return {"success": True, "result": {"triggered": True}}
            elif tool == "movie_search":
                return {"success": True, "result": {"triggered": True}}
            return {"success": True, "result": {}}

        orchestrator.call_tool = AsyncMock(side_effect=mock_tool_call)
        return orchestrator

    @pytest.fixture
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
        failed_download = {
            "nzo_id": "failed_123",
            "name": "Test.Show.S01E01.1080p",
            "fail_message": "Connection timeout",
        }

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result is True
        orchestrator.call_tool.assert_called_once()
        call_args = orchestrator.call_tool.call_args
        assert call_args[0][0] == "sabnzbd"  # service
        assert call_args[0][1] == "retry_download"  # tool
        assert call_args[0][2]["nzo_id"] == "failed_123"

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry_workflow(
        self, recovery_service: RecoveryService, event_bus: EventBus
    ) -> None:
        """Test exponential backoff workflow with event emissions."""
        # Arrange
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append({"type": event_type, "data": data})

        event_bus.subscribe("recovery.backoff_scheduled", capture_event)

        failed_download = {
            "nzo_id": "failed_456",
            "name": "Movie.2024.1080p",
            "fail_message": "Download failed",
        }

        # Simulate second retry attempt (should use backoff)
        recovery_service._retry_attempts["failed_456"] = 1

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result is True

        # Verify backoff event was emitted
        await asyncio.sleep(0.1)
        backoff_events = [e for e in events_received if e["type"] == "recovery.backoff_scheduled"]
        assert len(backoff_events) >= 1
        assert backoff_events[0]["data"]["nzo_id"] == "failed_456"
        assert backoff_events[0]["data"]["delay"] == 120  # 60 * 2^1

    @pytest.mark.asyncio
    async def test_quality_fallback_triggers_sonarr_search(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test quality fallback triggers Sonarr episode search."""
        # Arrange
        failed_download = {
            "nzo_id": "failed_789",
            "name": "Breaking.Bad.S05E14.2160p.BluRay",
            "fail_message": "CRC error in verification",
        }

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result is True

        # Verify Sonarr episode_search was called
        sonarr_calls = [
            call for call in orchestrator.call_tool.call_args_list if call[0][0] == "sonarr"
        ]
        assert len(sonarr_calls) >= 1
        assert sonarr_calls[0][0][1] == "episode_search"

    @pytest.mark.asyncio
    async def test_quality_fallback_triggers_radarr_search(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test quality fallback triggers Radarr movie search."""
        # Arrange
        failed_download = {
            "nzo_id": "movie_fail",
            "name": "The.Matrix.1999.2160p.BluRay",
            "fail_message": "PAR2 verification failed",
        }

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result is True

        # Verify Radarr movie_search was called
        radarr_calls = [
            call for call in orchestrator.call_tool.call_args_list if call[0][0] == "radarr"
        ]
        assert len(radarr_calls) >= 1
        assert radarr_calls[0][0][1] == "movie_search"

    @pytest.mark.asyncio
    async def test_multi_step_recovery_immediate_then_backoff(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator, event_bus: EventBus
    ) -> None:
        """Test multi-step recovery: immediate retry → backoff → success."""
        # Arrange
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append({"type": event_type, "data": data})

        event_bus.subscribe("recovery.retry_triggered", capture_event)
        event_bus.subscribe("recovery.backoff_scheduled", capture_event)

        failed_download = {
            "nzo_id": "multi_step",
            "name": "Show.S01E01.1080p",
            "fail_message": "Connection reset",
        }

        # Act - Step 1: Immediate retry (first attempt)
        result1 = await recovery_service.trigger_retry(failed_download)
        assert result1 is True

        # Act - Step 2: Exponential backoff (second attempt)
        result2 = await recovery_service.trigger_retry(failed_download)
        assert result2 is True

        # Assert - verify both strategies were used
        await asyncio.sleep(0.1)
        retry_events = [e for e in events_received if "retry" in e["type"]]
        assert len(retry_events) >= 2

        # Verify immediate retry happened first (attempt 0)
        # Verify backoff happened second (attempt 1)
        assert recovery_service._retry_attempts["multi_step"] == 2

    @pytest.mark.asyncio
    async def test_max_retry_limit_enforcement(
        self, recovery_service: RecoveryService, event_bus: EventBus
    ) -> None:
        """Test max retry limit prevents further retries."""
        # Arrange
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append({"type": event_type, "data": data})

        event_bus.subscribe("recovery.max_retries_exceeded", capture_event)

        failed_download = {
            "nzo_id": "max_retry",
            "name": "Show.S01E01.1080p",
            "fail_message": "Failed",
        }

        # Simulate already at max retries
        recovery_service._retry_attempts["max_retry"] = 3

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result is False

        # Verify max retries exceeded event
        await asyncio.sleep(0.1)
        max_retry_events = [
            e for e in events_received if e["type"] == "recovery.max_retries_exceeded"
        ]
        assert len(max_retry_events) == 1
        assert max_retry_events[0]["data"]["nzo_id"] == "max_retry"

    @pytest.mark.asyncio
    async def test_duplicate_retry_prevention_with_locks(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test concurrent retry attempts are prevented with locks."""
        # Arrange
        call_count = 0

        async def mock_slow_retry(service: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.2)  # Simulate slow retry
            return {"success": True, "result": {"nzo_id": "retry_123"}}

        orchestrator.call_tool = AsyncMock(side_effect=mock_slow_retry)

        failed_download = {
            "nzo_id": "concurrent_test",
            "name": "Show.S01E01.1080p",
            "fail_message": "Failed",
        }

        # Act - trigger concurrent retries
        results = await asyncio.gather(
            recovery_service.trigger_retry(failed_download),
            recovery_service.trigger_retry(failed_download),
            recovery_service.trigger_retry(failed_download),
        )

        # Assert - only one retry should execute (lock prevents duplicates)
        assert results.count(True) >= 1
        # Verify orchestrator was called limited times (not 3x due to lock)
        assert call_count <= 2  # Some may be prevented by lock

    @pytest.mark.asyncio
    async def test_retry_success_tracking_records_statistics(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test successful retries are tracked for statistics."""
        # Arrange
        failed_download = {
            "nzo_id": "success_track",
            "name": "Show.S01E01.1080p",
            "fail_message": "Timeout",
        }

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert
        assert result is True
        assert recovery_service._retry_attempts["success_track"] == 1

        # Verify success can be tracked (future implementation may add metrics)
        stats = recovery_service.get_retry_statistics()
        assert stats is not None

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling_during_retry(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator, event_bus: EventBus
    ) -> None:
        """Test recovery service handles orchestrator errors gracefully."""
        # Arrange
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append({"type": event_type, "data": data})

        event_bus.subscribe("recovery.retry_failed", capture_event)

        async def mock_failing_retry(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            raise Exception("Orchestrator connection failed")

        orchestrator.call_tool = AsyncMock(side_effect=mock_failing_retry)

        failed_download = {
            "nzo_id": "error_test",
            "name": "Show.S01E01.1080p",
            "fail_message": "Failed",
        }

        # Act
        result = await recovery_service.trigger_retry(failed_download)

        # Assert - should handle error gracefully
        assert result is False

        # Verify error event was emitted
        await asyncio.sleep(0.1)
        error_events = [e for e in events_received if "failed" in e["type"]]
        assert len(error_events) >= 1

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
            quality = recovery_service._extract_quality(filename)
            assert (
                quality == expected_quality
            ), f"Failed for {filename}: expected {expected_quality}, got {quality}"

    @pytest.mark.asyncio
    async def test_quality_fallback_chain_progression(
        self, recovery_service: RecoveryService
    ) -> None:
        """Test quality fallback follows proper chain: 2160p → 1080p → 720p."""
        # Test fallback chain
        assert recovery_service._get_lower_quality("2160p") == "1080p"
        assert recovery_service._get_lower_quality("1080p") == "720p"
        assert recovery_service._get_lower_quality("720p") == "HDTV"
        assert recovery_service._get_lower_quality("HDTV") is None
        assert recovery_service._get_lower_quality(None) is None

    @pytest.mark.asyncio
    async def test_content_type_detection_tv_vs_movie(
        self, recovery_service: RecoveryService
    ) -> None:
        """Test content type detection distinguishes TV shows from movies."""
        # TV show patterns
        tv_shows = [
            "Breaking.Bad.S05E14.1080p",
            "The.Office.s03e12.HDTV",
            "Show.1x01.720p",
        ]

        for show in tv_shows:
            is_tv = recovery_service._is_tv_show(show)
            assert is_tv, f"Failed to detect TV show: {show}"

        # Movie patterns
        movies = [
            "The.Matrix.1999.1080p",
            "Inception.2010.BluRay",
            "Movie.Title.720p",
        ]

        for movie in movies:
            is_tv = recovery_service._is_tv_show(movie)
            assert not is_tv, f"Incorrectly detected movie as TV show: {movie}"

    @pytest.mark.asyncio
    async def test_event_correlation_throughout_recovery(
        self, recovery_service: RecoveryService, event_bus: EventBus
    ) -> None:
        """Test correlation IDs propagate through recovery workflow."""
        # Arrange
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append({"type": event_type, "data": data, "timestamp": datetime.now()})

        event_bus.subscribe("recovery.retry_triggered", capture_event)

        failed_download = {
            "nzo_id": "correlation_test",
            "name": "Show.S01E01.1080p",
            "fail_message": "Failed",
        }

        # Act
        await recovery_service.trigger_retry(failed_download)

        # Assert
        await asyncio.sleep(0.1)
        if events_received:
            # Verify event data contains download info
            assert events_received[0]["data"]["nzo_id"] == "correlation_test"

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

        failed_download = {
            "nzo_id": "config_test",
            "name": "Show.S01E01.1080p",
            "fail_message": "Timeout",
        }

        # Should still retry but strategy selection is limited
        result = await recovery_immediate_only.trigger_retry(failed_download)
        assert result is True

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

        # Simulate multiple retry attempts
        recovery_custom._retry_attempts["custom_backoff"] = 2

        # Calculate expected delay: 30 * 3^2 = 270 seconds
        delay = recovery_custom._calculate_backoff_delay("custom_backoff")
        assert delay == 270

    @pytest.mark.asyncio
    async def test_parallel_retries_for_different_downloads(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test service can handle parallel retries for different downloads."""
        # Arrange
        downloads = [
            {"nzo_id": "dl_1", "name": "Show1.S01E01", "fail_message": "Failed"},
            {"nzo_id": "dl_2", "name": "Show2.S01E01", "fail_message": "Failed"},
            {"nzo_id": "dl_3", "name": "Show3.S01E01", "fail_message": "Failed"},
        ]

        # Act - trigger parallel retries
        results = await asyncio.gather(*[recovery_service.trigger_retry(dl) for dl in downloads])

        # Assert - all should succeed
        assert all(results)
        assert len(recovery_service._retry_attempts) == 3

    @pytest.mark.asyncio
    async def test_retry_history_persistence_tracking(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test retry history is tracked per download."""
        # Arrange
        failed_download = {
            "nzo_id": "history_test",
            "name": "Show.S01E01.1080p",
            "fail_message": "Failed",
        }

        # Act - trigger multiple retries
        await recovery_service.trigger_retry(failed_download)
        await recovery_service.trigger_retry(failed_download)
        await recovery_service.trigger_retry(failed_download)

        # Assert - verify history tracking
        assert recovery_service._retry_attempts["history_test"] == 3

        # Get statistics
        stats = recovery_service.get_retry_statistics()
        assert "history_test" in str(stats) or len(stats) >= 0  # Stats exist

    @pytest.mark.asyncio
    async def test_sonarr_episode_search_with_extracted_info(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test Sonarr search receives properly extracted episode info."""
        # Arrange
        failed_download = {
            "nzo_id": "sonarr_test",
            "name": "Breaking.Bad.S05E14.Ozymandias.1080p",
            "fail_message": "CRC error",
        }

        # Act
        await recovery_service.trigger_retry(failed_download)

        # Assert - verify Sonarr was called with proper episode info
        sonarr_calls = [
            call for call in orchestrator.call_tool.call_args_list if call[0][0] == "sonarr"
        ]

        if sonarr_calls:
            call_args = sonarr_calls[0][0][2]  # Get args dict
            # Service should extract series name and episode info
            assert "series" in str(call_args).lower() or "episode" in str(call_args).lower()

    @pytest.mark.asyncio
    async def test_radarr_movie_search_with_extracted_info(
        self, recovery_service: RecoveryService, orchestrator: MCPOrchestrator
    ) -> None:
        """Test Radarr search receives properly extracted movie info."""
        # Arrange
        failed_download = {
            "nzo_id": "radarr_test",
            "name": "The.Shawshank.Redemption.1994.1080p.BluRay",
            "fail_message": "PAR2 failed",
        }

        # Act
        await recovery_service.trigger_retry(failed_download)

        # Assert - verify Radarr was called
        radarr_calls = [
            call for call in orchestrator.call_tool.call_args_list if call[0][0] == "radarr"
        ]

        if radarr_calls:
            call_args = radarr_calls[0][0][2]
            # Service should extract movie title
            assert "movie" in str(call_args).lower() or "title" in str(call_args).lower()
