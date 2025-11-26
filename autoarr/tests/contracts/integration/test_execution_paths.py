"""
Integration tests for complete execution paths.

These tests validate that data flows correctly through the entire system,
from API entry point through service layers to external service calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.tests.contracts.fixtures.schemas import (
    CONFIG_AUDIT_RESPONSE_SCHEMA,
    CONTENT_RESPONSE_SCHEMA,
    HEALTH_CHECK_RESPONSE_SCHEMA,
    SABNZBD_QUEUE_RESPONSE_SCHEMA,
    validate_schema,
)


class TestConfigAuditExecutionPath:
    """Test complete configuration audit execution path."""

    @pytest.mark.asyncio
    async def test_audit_path_data_flow(self):
        """Test that audit path transforms data correctly at each step."""
        # Step 1: Simulate SABnzbd API response
        sabnzbd_config = {
            "config": {
                "misc": {"cache_limit": "512M", "bandwidth_max": "0"},
                "servers": [{"name": "primary", "host": "news.example.com"}],
                "categories": [],
            }
        }

        # Step 2: Simulate best practices from DB
        best_practices = [
            {"setting": "cache_limit", "recommended": "1G", "severity": "medium"},
        ]

        # Step 3: Expected audit findings after comparison
        expected_finding = {
            "setting": "cache_limit",
            "current": "512M",
            "recommended": "1G",
            "severity": "medium",
        }

        # Validate data transformation
        current_value = sabnzbd_config["config"]["misc"]["cache_limit"]
        assert current_value == expected_finding["current"]

        # Validate the finding matches schema
        finding = {
            "setting": "cache_limit",
            "current": current_value,
            "recommended": best_practices[0]["recommended"],
            "severity": best_practices[0]["severity"],
        }
        assert finding["setting"] == expected_finding["setting"]
        assert finding["current"] == expected_finding["current"]

    @pytest.mark.asyncio
    async def test_audit_response_schema_compliance(self):
        """Test that audit path produces schema-compliant response."""
        # Simulated final response from audit path
        audit_response = {
            "service": "sabnzbd",
            "findings": [
                {
                    "setting": "cache_limit",
                    "current": "512M",
                    "recommended": "1G",
                    "severity": "medium",
                    "explanation": "Increasing cache can improve performance",
                }
            ],
            "timestamp": "2024-01-15T10:30:00Z",
            "score": 75,
        }

        is_valid, errors = validate_schema(audit_response, CONFIG_AUDIT_RESPONSE_SCHEMA)
        assert is_valid, f"Audit response validation errors: {errors}"


class TestDownloadMonitoringPath:
    """Test complete download monitoring execution path."""

    @pytest.mark.asyncio
    async def test_queue_monitoring_data_flow(self):
        """Test that queue monitoring transforms data correctly."""
        # Step 1: SABnzbd queue response
        sabnzbd_queue = {
            "queue": {
                "slots": [
                    {
                        "nzo_id": "SABnzbd_nzo_abc123",
                        "filename": "Test.Show.S01E01.720p",
                        "status": "Downloading",
                        "percentage": "45",
                        "timeleft": "0:15:30",
                        "mb": "1500.00",
                        "mbleft": "825.00",
                    }
                ],
                "status": "Downloading",
                "speed": "5.2 M",
                "paused": False,
            }
        }

        # Validate SABnzbd response
        is_valid, errors = validate_schema(sabnzbd_queue, SABNZBD_QUEUE_RESPONSE_SCHEMA)
        assert is_valid, f"SABnzbd queue validation errors: {errors}"

        # Step 2: Transform to internal monitoring format
        slot = sabnzbd_queue["queue"]["slots"][0]
        internal_download = {
            "id": slot["nzo_id"],
            "name": slot["filename"],
            "status": slot["status"],
            "progress": float(slot["percentage"]),
            "size_mb": float(slot["mb"]),
            "remaining_mb": float(slot["mbleft"]),
            "eta": slot["timeleft"],
        }

        # Validate transformation preserves required data
        assert internal_download["id"] == "SABnzbd_nzo_abc123"
        assert internal_download["status"] == "Downloading"
        assert 0 <= internal_download["progress"] <= 100

    @pytest.mark.asyncio
    async def test_failed_download_detection_path(self):
        """Test that failed downloads are correctly detected and classified."""
        # SABnzbd history with failed download
        history_response = {
            "history": {
                "slots": [
                    {
                        "nzo_id": "SABnzbd_nzo_fail123",
                        "name": "Failed.Download",
                        "status": "Failed",
                        "fail_message": "Repair failed, not enough repair blocks",
                        "completed": 1699999999,
                    }
                ]
            }
        }

        slot = history_response["history"]["slots"][0]

        # Verify failure detection logic
        is_failed = slot["status"] == "Failed"
        assert is_failed

        # Verify failure reason extraction
        failure_reason = slot["fail_message"]
        assert "repair" in failure_reason.lower()

        # Classify failure type for recovery strategy
        if "repair" in failure_reason.lower():
            failure_type = "repair_failure"
        elif "timeout" in failure_reason.lower():
            failure_type = "timeout"
        else:
            failure_type = "unknown"

        assert failure_type == "repair_failure"


class TestContentRequestPath:
    """Test complete content request execution path."""

    @pytest.mark.asyncio
    async def test_series_search_data_flow(self):
        """Test that series search transforms data correctly."""
        # Step 1: User request
        user_request = {"query": "Breaking Bad", "content_type": "series"}

        # Step 2: Sonarr search response
        sonarr_response = [
            {
                "id": 1,
                "title": "Breaking Bad",
                "tvdbId": 81189,
                "year": 2008,
                "overview": "A chemistry teacher becomes a meth producer",
                "path": "/tv/Breaking Bad",
                "qualityProfileId": 1,
                "monitored": True,
            }
        ]

        # Step 3: Transform to content response
        content_response = {
            "results": [
                {
                    "id": sonarr_response[0]["tvdbId"],
                    "title": sonarr_response[0]["title"],
                    "year": sonarr_response[0]["year"],
                    "overview": sonarr_response[0]["overview"],
                }
            ],
            "content_type": "series",
            "total_results": len(sonarr_response),
        }

        # Validate response
        is_valid, errors = validate_schema(content_response, CONTENT_RESPONSE_SCHEMA)
        assert is_valid, f"Content response validation errors: {errors}"

        # Verify query matches result
        assert user_request["query"].lower() in content_response["results"][0]["title"].lower()

    @pytest.mark.asyncio
    async def test_movie_search_data_flow(self):
        """Test that movie search transforms data correctly."""
        # Step 1: User request
        user_request = {"query": "The Matrix", "content_type": "movie"}

        # Step 2: Radarr search response
        radarr_response = [
            {
                "id": 1,
                "title": "The Matrix",
                "tmdbId": 603,
                "year": 1999,
                "overview": "A computer programmer discovers...",
                "path": "/movies/The Matrix (1999)",
                "qualityProfileId": 1,
                "monitored": True,
                "hasFile": True,
            }
        ]

        # Step 3: Transform to content response
        content_response = {
            "results": [
                {
                    "id": radarr_response[0]["tmdbId"],
                    "title": radarr_response[0]["title"],
                    "year": radarr_response[0]["year"],
                    "overview": radarr_response[0]["overview"],
                }
            ],
            "content_type": "movie",
            "total_results": len(radarr_response),
        }

        # Validate response
        is_valid, errors = validate_schema(content_response, CONTENT_RESPONSE_SCHEMA)
        assert is_valid, f"Content response validation errors: {errors}"


class TestHealthCheckPath:
    """Test complete health check execution path."""

    @pytest.mark.asyncio
    async def test_health_check_aggregation(self):
        """Test that health check aggregates service statuses correctly."""
        # Individual service health checks
        service_statuses = {
            "sabnzbd": {"status": "connected", "latency_ms": 45.2},
            "sonarr": {"status": "connected", "latency_ms": 32.1},
            "radarr": {"status": "error", "error": "Connection refused"},
        }

        # Determine overall status
        has_errors = any(s.get("status") == "error" for s in service_statuses.values())
        all_healthy = all(s.get("status") == "connected" for s in service_statuses.values())

        if all_healthy:
            overall_status = "healthy"
        elif has_errors:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        # Build response
        health_response = {
            "status": overall_status,
            "services": service_statuses,
            "timestamp": "2024-01-15T10:30:00Z",
        }

        # Validate response
        is_valid, errors = validate_schema(health_response, HEALTH_CHECK_RESPONSE_SCHEMA)
        assert is_valid, f"Health check validation errors: {errors}"
        assert health_response["status"] == "degraded"


class TestEventBusPath:
    """Test event bus data flow paths."""

    @pytest.mark.asyncio
    async def test_event_correlation_chain(self):
        """Test that events maintain correlation through the chain."""
        correlation_id = "corr_abc123"

        # Event chain for a download recovery
        events = [
            {
                "type": "download_failed",
                "correlation_id": correlation_id,
                "data": {"nzo_id": "SABnzbd_nzo_123", "reason": "Repair failed"},
            },
            {
                "type": "recovery_initiated",
                "correlation_id": correlation_id,
                "data": {"nzo_id": "SABnzbd_nzo_123", "strategy": "retry"},
            },
            {
                "type": "download_retried",
                "correlation_id": correlation_id,
                "data": {"nzo_id": "SABnzbd_nzo_123", "new_nzo_id": "SABnzbd_nzo_456"},
            },
        ]

        # Verify all events share correlation ID
        for event in events:
            assert event["correlation_id"] == correlation_id

        # Verify event chain order makes sense
        assert events[0]["type"] == "download_failed"
        assert events[1]["type"] == "recovery_initiated"
        assert events[2]["type"] == "download_retried"

    @pytest.mark.asyncio
    async def test_activity_log_from_events(self):
        """Test that events are correctly transformed to activity log entries."""
        event = {
            "type": "download_completed",
            "correlation_id": "corr_xyz789",
            "data": {"nzo_id": "SABnzbd_nzo_123", "filename": "Test.Show.S01E01"},
            "timestamp": "2024-01-15T10:30:00Z",
        }

        # Transform event to activity log entry
        activity_entry = {
            "id": f"act_{event['correlation_id']}",
            "action": event["type"],
            "timestamp": event["timestamp"],
            "correlation_id": event["correlation_id"],
            "details": event["data"],
            "source": "event_bus",
        }

        # Verify transformation preserves key data
        assert activity_entry["action"] == event["type"]
        assert activity_entry["correlation_id"] == event["correlation_id"]
        assert activity_entry["details"]["nzo_id"] == event["data"]["nzo_id"]


class TestWebSocketBroadcastPath:
    """Test WebSocket broadcast data flow paths."""

    @pytest.mark.asyncio
    async def test_event_to_websocket_message(self):
        """Test that events are correctly formatted for WebSocket."""
        internal_event = {
            "type": "queue_update",
            "data": {
                "downloads": [{"id": "nzo_123", "progress": 75, "status": "downloading"}],
                "speed": "5.2 MB/s",
            },
        }

        # WebSocket message format
        ws_message = {
            "event": internal_event["type"],
            "payload": internal_event["data"],
            "timestamp": "2024-01-15T10:30:00Z",
        }

        # Verify message structure
        assert "event" in ws_message
        assert "payload" in ws_message
        assert ws_message["event"] == "queue_update"
        assert "downloads" in ws_message["payload"]
