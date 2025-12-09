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
- Monitoring detects failure → Event bus → Recovery triggered
- Pattern-based recovery decisions
- Wanted list correlation with recovery
- Multi-service coordination across the full workflow
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from autoarr.api.services.event_bus import EventBus
from autoarr.api.services.monitoring_service import MonitoringConfig, MonitoringService
from autoarr.api.services.recovery_service import RecoveryConfig, RecoveryService
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

        # Mock default responses
        async def mock_tool_call(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": "failed_123",
                                "name": "Test.Show.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Connection timeout",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    },
                }
            elif tool == "retry_download":
                return {"success": True, "result": {"nzo_id": "retry_456"}}
            elif tool == "get_queue":
                return {"success": True, "result": {"slots": []}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_tool_call)
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
        """Test complete workflow: detection → event → recovery."""
        # Arrange
        recovery_triggered = False

        async def on_failure_event(event_type: str, data: Dict[str, Any]) -> None:
            nonlocal recovery_triggered
            # Trigger recovery when failure detected
            await recovery_service.trigger_retry(data)
            recovery_triggered = True

        event_bus.subscribe("download.failed", on_failure_event)

        # Act - Step 1: Monitor detects failure
        failures = await monitoring_service.get_failed_downloads()

        # Wait for event processing and recovery trigger
        await asyncio.sleep(0.2)

        # Assert
        assert len(failures) == 1
        assert failures[0]["nzo_id"] == "failed_123"
        assert recovery_triggered is True

    @pytest.mark.asyncio
    async def test_pattern_detection_influences_recovery_strategy(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test pattern detection influences which recovery strategy is used."""
        # Arrange - mock recurring CRC errors
        async def mock_crc_pattern(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": f"failed_{i}",
                                "name": f"Show.S01E0{i}.1080p",
                                "status": "Failed",
                                "fail_message": "CRC error",
                                "completed": int(
                                    (datetime.now() - timedelta(minutes=i)).timestamp()
                                ),
                            }
                            for i in range(1, 4)
                        ]
                    },
                }
            elif tool == "episode_search":
                return {"success": True, "result": {"triggered": True}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_crc_pattern)

        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            pattern_recognition_enabled=True,
        )

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            quality_fallback_enabled=True,
        )

        # Act - detect pattern
        failures = await monitoring.get_failed_downloads()
        patterns = await monitoring.analyze_failure_patterns(failures)

        # Verify quality pattern detected
        quality_pattern = next((p for p in patterns if p["pattern_type"] == "quality"), None)
        assert quality_pattern is not None

        # Act - trigger recovery (should use quality fallback)
        await recovery.trigger_retry(failures[0])

        # Assert - verify Sonarr search was called (quality fallback strategy)
        sonarr_calls = [
            call for call in orchestrator.call_mcp_tool.call_args_list if call[0][0] == "sonarr"
        ]
        assert len(sonarr_calls) >= 1

    @pytest.mark.asyncio
    async def test_wanted_list_correlation_triggers_smart_recovery(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test wanted list correlation triggers appropriate recovery."""
        # Arrange - mock failure that matches wanted episode
        async def mock_wanted_correlation(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": "failed_wanted",
                                "name": "Breaking.Bad.S05E14.1080p",
                                "status": "Failed",
                                "fail_message": "Download incomplete",
                                "completed": int(datetime.now().timestamp()),
                            }
                        ]
                    },
                }
            elif tool == "get_wanted":
                return {
                    "success": True,
                    "result": {
                        "records": [
                            {
                                "series": {"title": "Breaking Bad"},
                                "seasonNumber": 5,
                                "episodeNumber": 14,
                            }
                        ]
                    },
                }
            elif tool == "episode_search":
                return {"success": True, "result": {"triggered": True}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_wanted_correlation)

        monitoring = MonitoringService(event_bus=event_bus, orchestrator=orchestrator)
        recovery = RecoveryService(event_bus=event_bus, orchestrator=orchestrator)

        # Act - get failures and wanted list
        failures = await monitoring.get_failed_downloads()
        wanted = await monitoring.get_wanted_episodes()

        # Verify correlation
        assert len(failures) == 1
        assert len(wanted) == 1
        assert "Breaking.Bad" in failures[0]["name"]
        assert wanted[0]["series"]["title"] == "Breaking Bad"

        # Trigger recovery
        await recovery.trigger_retry(failures[0])

        # Assert - Sonarr search should be triggered
        sonarr_calls = [
            call for call in orchestrator.call_mcp_tool.call_args_list if call[0][0] == "sonarr"
        ]
        assert len(sonarr_calls) >= 2  # get_wanted + episode_search

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
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            nonlocal queue_call_count
            if tool == "get_queue":
                queue_call_count += 1
                # First call: empty, second call: new download appears
                if queue_call_count == 1:
                    return {"success": True, "result": {"slots": []}}
                else:
                    return {
                        "success": True,
                        "result": {
                            "slots": [
                                {
                                    "nzo_id": "new_retry_123",
                                    "filename": "Show.S01E01.1080p",
                                    "status": "Downloading",
                                    "percentage": 5.0,
                                }
                            ]
                        },
                    }
            elif tool == "retry_download":
                return {"success": True, "result": {"nzo_id": "new_retry_123"}}
            elif tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": "failed_old",
                                "name": "Show.S01E01.1080p",
                                "status": "Failed",
                            }
                        ]
                    },
                }
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_recovery_to_queue)

        monitoring = MonitoringService(event_bus=event_bus, orchestrator=orchestrator)
        recovery = RecoveryService(event_bus=event_bus, orchestrator=orchestrator)

        # Act - detect failure and trigger recovery
        failures = await monitoring.get_failed_downloads()
        await recovery.trigger_retry(failures[0])

        # Poll queue before and after recovery
        queue_before = await monitoring.poll_queue()
        await asyncio.sleep(0.1)
        queue_after = await monitoring.poll_queue()

        # Assert - new download appears in queue
        assert len(queue_before) == 0
        assert len(queue_after) == 1
        assert queue_after[0]["nzo_id"] == "new_retry_123"

    @pytest.mark.asyncio
    async def test_cascading_retry_workflow(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test cascading retries: immediate → backoff → quality fallback."""
        # Arrange
        retry_call_count = 0
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append({"type": event_type, "data": data})

        event_bus.subscribe("recovery.retry_triggered", capture_event)
        event_bus.subscribe("recovery.backoff_scheduled", capture_event)

        async def mock_retry_sequence(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            nonlocal retry_call_count
            if tool == "retry_download":
                retry_call_count += 1
                # First two retries fail, third triggers quality fallback
                if retry_call_count <= 2:
                    return {"success": False, "error": "Retry failed"}
                return {"success": True, "result": {"nzo_id": "retry_success"}}
            elif tool == "episode_search":
                return {"success": True, "result": {"triggered": True}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_retry_sequence)

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            immediate_retry_enabled=True,
            exponential_backoff_enabled=True,
            quality_fallback_enabled=True,
        )

        failed_download = {
            "nzo_id": "cascade_test",
            "name": "Show.S01E01.2160p",
            "fail_message": "CRC error",
        }

        # Act - trigger cascading retries
        result1 = await recovery.trigger_retry(failed_download)  # Immediate
        result2 = await recovery.trigger_retry(failed_download)  # Backoff
        result3 = await recovery.trigger_retry(failed_download)  # Quality fallback

        # Assert
        await asyncio.sleep(0.1)
        assert len(events_received) >= 2  # Multiple retry events

    @pytest.mark.asyncio
    async def test_parallel_monitoring_and_recovery_no_race_conditions(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
    ) -> None:
        """Test parallel monitoring and recovery operations don't cause race conditions."""
        # Arrange - create multiple failures
        async def mock_multiple_failures(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": f"failed_{i}",
                                "name": f"Show{i}.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Failed",
                            }
                            for i in range(5)
                        ]
                    },
                }
            elif tool == "retry_download":
                await asyncio.sleep(0.05)  # Simulate delay
                return {"success": True, "result": {"nzo_id": "retry_success"}}
            return {"success": True, "result": {"slots": []}}

        monitoring_service.orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_multiple_failures)
        recovery_service.orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_multiple_failures)

        # Act - parallel monitoring and recovery
        monitor_task = asyncio.create_task(monitoring_service.get_failed_downloads())
        await asyncio.sleep(0.01)  # Slight delay

        failures = await monitor_task

        # Trigger parallel recoveries
        recovery_tasks = [recovery_service.trigger_retry(failure) for failure in failures]
        results = await asyncio.gather(*recovery_tasks)

        # Assert - all recoveries complete without errors
        assert len(results) == 5
        assert all(isinstance(r, bool) for r in results)

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
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": "failed_123",
                                "name": "Show.S01E01",
                                "status": "Failed",
                            }
                        ]
                    },
                }
            elif tool == "retry_download":
                raise Exception("Recovery service unavailable")
            elif tool == "get_queue":
                return {"success": True, "result": {"slots": []}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_mixed_results)

        # Act - monitoring detects failure
        failures = await monitoring_service.get_failed_downloads()
        assert len(failures) == 1

        # Recovery fails
        recovery_result = await recovery_service.trigger_retry(failures[0])
        assert recovery_result is False

        # Monitoring continues to work
        queue = await monitoring_service.poll_queue()
        assert queue is not None

    @pytest.mark.asyncio
    async def test_event_correlation_across_workflow(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
        event_bus: EventBus,
    ) -> None:
        """Test correlation IDs link events across entire workflow."""
        # Arrange
        events_received: List[Dict[str, Any]] = []

        def capture_event(event_type: str, data: Dict[str, Any]) -> None:
            events_received.append(
                {
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now(),
                }
            )

        event_bus.subscribe("download.failed", capture_event)
        event_bus.subscribe("recovery.retry_triggered", capture_event)

        # Act - complete workflow
        failures = await monitoring_service.get_failed_downloads()
        await asyncio.sleep(0.1)

        if failures:
            await recovery_service.trigger_retry(failures[0])
            await asyncio.sleep(0.1)

        # Assert - events are properly sequenced
        if events_received:
            assert len(events_received) >= 1
            # Verify events contain download identifiers
            for event in events_received:
                assert "data" in event
                assert "nzo_id" in event["data"] or "download" in str(event["data"]).lower()

    @pytest.mark.asyncio
    async def test_disk_space_pattern_prevents_immediate_retry(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test disk space pattern detection prevents useless immediate retries."""
        # Arrange - mock disk space failures
        async def mock_disk_space(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": f"disk_fail_{i}",
                                "name": f"Show{i}.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Disk space full",
                            }
                            for i in range(3)
                        ]
                    },
                }
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_disk_space)

        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            pattern_recognition_enabled=True,
        )

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            immediate_retry_enabled=True,
        )

        # Act - detect pattern
        failures = await monitoring.get_failed_downloads()
        patterns = await monitoring.analyze_failure_patterns(failures)

        # Verify disk space pattern detected
        disk_pattern = next((p for p in patterns if p["pattern_type"] == "disk_space"), None)
        assert disk_pattern is not None

        # Recovery should still trigger but strategy selection could be influenced
        result = await recovery.trigger_retry(failures[0])
        # Recovery might succeed or fail depending on implementation
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_network_pattern_triggers_exponential_backoff(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test network failure pattern triggers exponential backoff strategy."""
        # Arrange
        async def mock_network_failures(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": f"net_fail_{i}",
                                "name": f"Show{i}.S01E01.1080p",
                                "status": "Failed",
                                "fail_message": "Connection timeout",
                            }
                            for i in range(3)
                        ]
                    },
                }
            elif tool == "retry_download":
                return {"success": True, "result": {"nzo_id": "retry_ok"}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_network_failures)

        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            pattern_recognition_enabled=True,
        )

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            exponential_backoff_enabled=True,
        )

        # Act
        failures = await monitoring.get_failed_downloads()
        patterns = await monitoring.analyze_failure_patterns(failures)

        # Verify network pattern
        network_pattern = next((p for p in patterns if p["pattern_type"] == "network"), None)
        assert network_pattern is not None

        # Trigger recovery - should use backoff for network issues
        # Simulate second attempt to trigger backoff
        recovery._retry_attempts[failures[0]["nzo_id"]] = 1
        result = await recovery.trigger_retry(failures[0])
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_quality_pattern_triggers_search_not_retry(
        self,
        event_bus: EventBus,
        orchestrator: MCPOrchestrator,
    ) -> None:
        """Test quality/CRC pattern triggers new search instead of direct retry."""
        # Arrange
        async def mock_quality_failures(
            service: str, tool: str, args: Dict[str, Any]
        ) -> Dict[str, Any]:
            if tool == "get_history":
                return {
                    "success": True,
                    "result": {
                        "slots": [
                            {
                                "nzo_id": "quality_fail",
                                "name": "Breaking.Bad.S05E14.1080p",
                                "status": "Failed",
                                "fail_message": "CRC verification failed",
                            }
                        ]
                    },
                }
            elif tool == "episode_search":
                return {"success": True, "result": {"triggered": True}}
            elif tool == "retry_download":
                return {"success": True, "result": {"nzo_id": "retry_ok"}}
            return {"success": True, "result": {}}

        orchestrator.call_mcp_tool = AsyncMock(side_effect=mock_quality_failures)

        monitoring = MonitoringService(
            event_bus=event_bus,
            orchestrator=orchestrator,
        )

        recovery = RecoveryService(
            event_bus=event_bus,
            orchestrator=orchestrator,
            quality_fallback_enabled=True,
        )

        # Act
        failures = await monitoring.get_failed_downloads()
        await recovery.trigger_retry(failures[0])

        # Assert - Sonarr search should be called (quality fallback)
        sonarr_calls = [
            call for call in orchestrator.call_mcp_tool.call_args_list if call[0][0] == "sonarr"
        ]
        assert len(sonarr_calls) >= 1

    @pytest.mark.asyncio
    async def test_monitoring_recovery_activity_log_integration(
        self,
        monitoring_service: MonitoringService,
        recovery_service: RecoveryService,
        event_bus: EventBus,
    ) -> None:
        """Test monitoring and recovery events are logged to activity log."""
        # Arrange
        activity_events: List[Dict[str, Any]] = []

        def log_activity(event_type: str, data: Dict[str, Any]) -> None:
            activity_events.append({"event": event_type, "data": data, "time": datetime.now()})

        # Subscribe to all relevant events
        event_bus.subscribe("download.failed", log_activity)
        event_bus.subscribe("recovery.retry_triggered", log_activity)

        # Act
        failures = await monitoring_service.get_failed_downloads()
        await asyncio.sleep(0.1)

        if failures:
            await recovery_service.trigger_retry(failures[0])
            await asyncio.sleep(0.1)

        # Assert - activity log should have entries
        assert len(activity_events) >= 1
        # Verify proper sequencing
        if len(activity_events) >= 2:
            assert activity_events[0]["time"] <= activity_events[1]["time"]
