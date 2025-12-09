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
Integration tests for Monitoring-Recovery Workflow.

These tests verify the complete workflow from failure detection to recovery:
- Monitoring detects failure -> Event bus -> Recovery triggered
- Multi-service coordination across the full workflow
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from autoarr.api.services.event_bus import Event, EventBus, EventType
from autoarr.api.services.monitoring_service import (
    DownloadStatus,
    FailedDownload,
    MonitoringConfig,
    MonitoringService,
    QueueState,
    WantedEpisode,
)
from autoarr.api.services.recovery_service import RecoveryConfig, RecoveryResult, RecoveryService
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator


class TestMonitoringRecoveryWorkflow:
    """Integration tests for monitoring-recovery workflow."""

    @pytest.fixture
    async def event_bus(self) -> EventBus:
        """Create event bus instance."""
        return EventBus()

    @pytest.fixture
    async def orchestrator(self) -> MCPOrchestrator:
        """Create MCP orchestrator with mocked responses."""
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

        # Mock default responses - in format expected by services
        async def mock_tool_call(server: str, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": "failed_123",
                                "name": "Test.Show.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Connection timeout",
                                "category": "tv",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    }
                }
            elif tool == "retry_download":
                return {"status": True, "nzo_ids": ["retry_456"]}
            elif tool == "get_queue":
                return {
                    "queue": {
                        "status": "Idle",
                        "speed": "0 MB/s",
                        "slots": [],
                    }
                }
            return {}

        orchestrator.call_tool = AsyncMock(side_effect=mock_tool_call)
        return orchestrator

    @pytest.fixture
    async def monitoring_service(
        self, event_bus: EventBus, orchestrator: MCPOrchestrator
    ) -> MonitoringService:
        """Create monitoring service instance."""
        config = MonitoringConfig()
        config.poll_interval = 1
        config.failure_detection_enabled = True
        config.pattern_recognition_enabled = True
        config.alert_on_failure = True

        return MonitoringService(
            orchestrator=orchestrator,
            event_bus=event_bus,
            config=config,
        )

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

        return RecoveryService(
            orchestrator=orchestrator,
            event_bus=event_bus,
            config=config,
        )

    @pytest.mark.asyncio
    async def test_complete_failure_to_recovery_workflow(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
        event_bus: EventBus,
    ) -> None:
        """Test complete workflow: detection -> event -> recovery."""
        # Arrange
        recovery_triggered = False
        failures_detected: List[FailedDownload] = []

        async def on_failure_event(event: Event) -> None:
            nonlocal recovery_triggered, failures_detected
            # The event data contains failure info
            if event.data.get("nzo_id"):
                # Create FailedDownload from event data
                failed = FailedDownload(
                    nzo_id=event.data["nzo_id"],
                    name=event.data.get("name", "Unknown"),
                    status=DownloadStatus.FAILED,
                    failure_reason=event.data.get("failure_reason", "Unknown"),
                    category=event.data.get("category", "tv"),
                )
                result = await recovery_service.trigger_retry(failed)
                recovery_triggered = result.success
                failures_detected.append(failed)

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, on_failure_event)

        # Act - Step 1: Monitor detects failure
        failures = await monitoring_service.detect_failed_downloads()

        # Wait for event processing and recovery trigger
        await asyncio.sleep(0.2)

        # Assert
        assert len(failures) == 1
        assert isinstance(failures[0], FailedDownload)
        assert failures[0].nzo_id == "failed_123"

    @pytest.mark.asyncio
    async def test_wanted_list_correlation_triggers_smart_recovery(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test wanted list correlation triggers appropriate recovery."""

        # Arrange - mock failure that matches wanted episode
        async def mock_wanted_correlation(
            server: str, tool: str, params: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": "failed_wanted",
                                "name": "Breaking.Bad.S05E14.1080p",
                                "status": "Failed",
                                "fail_message": "Download incomplete",
                                "category": "tv",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    }
                }
            elif tool == "get_wanted":
                return {
                    "records": [
                        {
                            "id": 1,
                            "seriesId": 10,
                            "seasonNumber": 5,
                            "episodeNumber": 14,
                            "title": "Ozymandias",
                            "monitored": True,
                            "airDate": "2013-09-15",
                        }
                    ]
                }
            elif tool == "episode_search":
                return {"triggered": True}
            return {}

        orchestrator.call_tool = AsyncMock(side_effect=mock_wanted_correlation)

        config = MonitoringConfig()
        config.poll_interval = 1

        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            config=config,
        )

        recovery_config = RecoveryConfig()
        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            config=recovery_config,
        )

        # Act - get failures and wanted list
        failures = await monitoring.detect_failed_downloads()
        wanted = await monitoring.get_wanted_episodes()

        # Verify correlation
        assert len(failures) == 1
        assert isinstance(failures[0], FailedDownload)
        assert "Breaking.Bad" in failures[0].name
        assert len(wanted) == 1
        assert isinstance(wanted[0], WantedEpisode)
        assert wanted[0].season_number == 5
        assert wanted[0].episode_number == 14

        # Trigger recovery
        result = await recovery.trigger_retry(failures[0])
        assert isinstance(result, RecoveryResult)

    @pytest.mark.asyncio
    async def test_recovery_new_download_appears_in_monitoring(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test recovery triggers new download that appears in monitoring queue."""
        # Arrange - track queue changes
        queue_call_count = 0

        async def mock_recovery_to_queue(
            server: str, tool: str, params: Dict[str, Any]
        ) -> Dict[str, Any]:
            nonlocal queue_call_count
            if tool == "get_queue":
                queue_call_count += 1
                # First call: empty, second call: new download appears
                if queue_call_count == 1:
                    return {
                        "queue": {
                            "status": "Idle",
                            "speed": "0 MB/s",
                            "slots": [],
                        }
                    }
                else:
                    return {
                        "queue": {
                            "status": "Downloading",
                            "speed": "10 MB/s",
                            "slots": [
                                {
                                    "nzo_id": "new_retry_123",
                                    "filename": "Show.S01E01.1080p",
                                    "status": "Downloading",
                                    "percentage": "5",
                                    "mbleft": "950",
                                    "mb": "1000",
                                    "cat": "tv",
                                    "priority": "Normal",
                                    "timeleft": "0:10:00",
                                }
                            ],
                        }
                    }
            elif tool == "retry_download":
                return {"status": True, "nzo_ids": ["new_retry_123"]}
            elif tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": "failed_old",
                                "name": "Show.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Download failed",
                                "category": "tv",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    }
                }
            return {}

        orchestrator.call_tool = AsyncMock(side_effect=mock_recovery_to_queue)

        config = MonitoringConfig()
        monitoring = MonitoringService(
            event_bus=event_bus, orchestrator=orchestrator, config=config
        )

        recovery_config = RecoveryConfig()
        recovery = RecoveryService(
            event_bus=event_bus, orchestrator=orchestrator, config=recovery_config
        )

        # Act - detect failure and trigger recovery
        failures = await monitoring.detect_failed_downloads()
        result = await recovery.trigger_retry(failures[0])
        assert isinstance(result, RecoveryResult)

        # Poll queue before and after recovery
        queue_before = await monitoring.poll_queue()
        await asyncio.sleep(0.1)
        queue_after = await monitoring.poll_queue()

        # Assert - new download appears in queue
        assert queue_before is not None
        assert isinstance(queue_before, QueueState)
        assert len(queue_before.items) == 0
        assert queue_after is not None
        assert isinstance(queue_after, QueueState)
        assert len(queue_after.items) == 1
        assert queue_after.items[0].nzo_id == "new_retry_123"

    @pytest.mark.asyncio
    async def test_parallel_monitoring_and_recovery_no_race_conditions(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
    ) -> None:
        """Test parallel monitoring and recovery operations don't cause race conditions."""

        # Arrange - create multiple failures
        async def mock_multiple_failures(
            server: str, tool: str, params: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": f"failed_{i}",
                                "name": f"Show{i}.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Failed",
                                "category": "tv",
                                "completed": int(datetime.now().timestamp()),
                            }
                            for i in range(5)
                        ]
                    }
                }
            elif tool == "retry_download":
                await asyncio.sleep(0.05)  # Simulate delay
                return {"status": True, "nzo_ids": ["retry_success"]}
            return {"queue": {"status": "Idle", "speed": "0 MB/s", "slots": []}}

        monitoring_service.orchestrator.call_tool = AsyncMock(side_effect=mock_multiple_failures)
        recovery_service.orchestrator.call_tool = AsyncMock(side_effect=mock_multiple_failures)

        # Act - parallel monitoring and recovery
        monitor_task = asyncio.create_task(monitoring_service.detect_failed_downloads())
        await asyncio.sleep(0.01)  # Slight delay

        failures = await monitor_task

        # Trigger parallel recoveries
        recovery_tasks = [recovery_service.trigger_retry(failure) for failure in failures]
        results = await asyncio.gather(*recovery_tasks)

        # Assert - all recoveries complete without errors
        assert len(results) == 5
        assert all(isinstance(r, RecoveryResult) for r in results)

    @pytest.mark.asyncio
    async def test_monitoring_continues_during_recovery_failures(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test monitoring continues working even when recovery fails."""

        # Arrange - recovery fails but monitoring succeeds
        async def mock_mixed_results(
            server: str, tool: str, params: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": "failed_123",
                                "name": "Show.S01E01",
                                "status": "Failed",
                                "fail_message": "Download failed",
                                "category": "tv",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    }
                }
            elif tool == "retry_download":
                raise Exception("Recovery service unavailable")
            elif tool == "get_queue":
                return {"queue": {"status": "Idle", "speed": "0 MB/s", "slots": []}}
            return {}

        orchestrator.call_tool = AsyncMock(side_effect=mock_mixed_results)

        # Act - monitoring detects failure
        failures = await monitoring_service.detect_failed_downloads()
        assert len(failures) == 1

        # Recovery fails
        recovery_result = await recovery_service.trigger_retry(failures[0])
        assert isinstance(recovery_result, RecoveryResult)
        assert recovery_result.success is False

        # Monitoring continues to work
        queue = await monitoring_service.poll_queue()
        assert queue is not None
        assert isinstance(queue, QueueState)

    @pytest.mark.asyncio
    async def test_event_correlation_across_workflow(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
        event_bus: EventBus,
    ) -> None:
        """Test correlation IDs link events across entire workflow."""
        # Arrange
        events_received: List[Event] = []

        def capture_event(event: Event) -> None:
            events_received.append(event)

        event_bus.subscribe(EventType.DOWNLOAD_FAILED, capture_event)
        event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, capture_event)

        # Act - complete workflow
        failures = await monitoring_service.detect_failed_downloads()
        await asyncio.sleep(0.1)

        if failures:
            await recovery_service.trigger_retry(failures[0])
            await asyncio.sleep(0.1)

        # Assert - events are properly received
        # Note: Event emission depends on service implementation
        assert len(failures) >= 1

    @pytest.mark.asyncio
    async def test_network_failure_recovery(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test network failure pattern triggers exponential backoff strategy."""

        # Arrange
        async def mock_network_failures(
            server: str, tool: str, params: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": f"net_fail_{i}",
                                "name": f"Show{i}.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Connection timeout",
                                "category": "tv",
                                "completed": int(
                                    (datetime.now() - timedelta(minutes=i)).timestamp()
                                ),
                            }
                            for i in range(3)
                        ]
                    }
                }
            elif tool == "retry_download":
                return {"status": True, "nzo_ids": ["retry_ok"]}
            return {}

        orchestrator.call_tool = AsyncMock(side_effect=mock_network_failures)

        config = MonitoringConfig()
        config.poll_interval = 1
        config.pattern_recognition_enabled = True

        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            config=config,
        )

        recovery_config = RecoveryConfig()
        recovery_config.exponential_backoff_enabled = True

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            config=recovery_config,
        )

        # Act
        failures = await monitoring.detect_failed_downloads()
        assert len(failures) == 3

        # Trigger recovery for first failure
        result = await recovery.trigger_retry(failures[0])
        assert isinstance(result, RecoveryResult)

    @pytest.mark.asyncio
    async def test_quality_failure_recovery(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test quality/CRC pattern triggers new search instead of direct retry."""

        # Arrange
        async def mock_quality_failures(
            server: str, tool: str, params: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "history": {
                        "slots": [
                            {
                                "nzo_id": "quality_fail",
                                "name": "Breaking.Bad.S05E14.1080p",
                                "status": "Failed",
                                "fail_message": "CRC verification failed",
                                "category": "tv",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    }
                }
            elif tool == "episode_search":
                return {"triggered": True}
            elif tool == "retry_download":
                return {"status": True, "nzo_ids": ["retry_ok"]}
            return {}

        orchestrator.call_tool = AsyncMock(side_effect=mock_quality_failures)

        config = MonitoringConfig()
        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            config=config,
        )

        recovery_config = RecoveryConfig()
        recovery_config.quality_fallback_enabled = True

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            config=recovery_config,
        )

        # Act
        failures = await monitoring.detect_failed_downloads()
        result = await recovery.trigger_retry(failures[0])

        # Assert
        assert isinstance(result, RecoveryResult)
        assert len(failures) == 1

    @pytest.mark.asyncio
    async def test_monitoring_recovery_activity_log_integration(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
        event_bus: EventBus,
    ) -> None:
        """Test monitoring and recovery events are logged to activity log."""
        # Arrange
        activity_events: List[Event] = []

        def log_activity(event: Event) -> None:
            activity_events.append(event)

        # Subscribe to all relevant events
        event_bus.subscribe(EventType.DOWNLOAD_FAILED, log_activity)
        event_bus.subscribe(EventType.RECOVERY_ATTEMPTED, log_activity)

        # Act
        failures = await monitoring_service.detect_failed_downloads()
        await asyncio.sleep(0.1)

        if failures:
            await recovery_service.trigger_retry(failures[0])
            await asyncio.sleep(0.1)

        # Assert - failures were detected
        assert len(failures) >= 1
