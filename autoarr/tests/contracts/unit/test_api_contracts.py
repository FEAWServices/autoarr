"""
Contract tests for API request/response validation.

These tests validate that:
1. API request payloads match expected schemas
2. API responses match expected schemas
3. Error responses follow standard format
"""

import pytest

from autoarr.tests.contracts.fixtures.schemas import (
    ACTIVITY_LOG_ENTRY_SCHEMA,
    CONFIG_AUDIT_REQUEST_SCHEMA,
    CONFIG_AUDIT_RESPONSE_SCHEMA,
    CONTENT_REQUEST_SCHEMA,
    CONTENT_RESPONSE_SCHEMA,
    HEALTH_CHECK_RESPONSE_SCHEMA,
    validate_schema,
)


class TestConfigAuditContracts:
    """Test configuration audit API contracts."""

    def test_valid_audit_request(self):
        """Valid audit request should pass validation."""
        request = {"service": "sabnzbd"}
        is_valid, errors = validate_schema(request, CONFIG_AUDIT_REQUEST_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_all_valid_services(self):
        """All supported services should be valid."""
        for service in ["sabnzbd", "sonarr", "radarr", "plex"]:
            request = {"service": service}
            is_valid, errors = validate_schema(request, CONFIG_AUDIT_REQUEST_SCHEMA)
            assert is_valid, f"Service '{service}' validation errors: {errors}"

    def test_invalid_service_name(self):
        """Invalid service name should fail."""
        request = {"service": "invalid_service"}
        is_valid, errors = validate_schema(request, CONFIG_AUDIT_REQUEST_SCHEMA)
        assert not is_valid

    def test_missing_service(self):
        """Request without service should fail."""
        request = {}
        is_valid, errors = validate_schema(request, CONFIG_AUDIT_REQUEST_SCHEMA)
        assert not is_valid

    def test_valid_audit_response(self):
        """Valid audit response should pass validation."""
        response = {
            "service": "sabnzbd",
            "findings": [
                {
                    "setting": "cache_limit",
                    "current": "512M",
                    "recommended": "1G",
                    "severity": "medium",
                    "explanation": "Increasing cache improves performance",
                }
            ],
            "timestamp": "2024-01-15T10:30:00Z",
            "score": 75,
        }
        is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_audit_response_no_findings(self):
        """Audit response with no findings should be valid."""
        response = {
            "service": "sonarr",
            "findings": [],
            "timestamp": "2024-01-15T10:30:00Z",
            "score": 100,
        }
        is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_all_severity_levels(self):
        """All severity levels should be valid."""
        for severity in ["low", "medium", "high", "critical"]:
            response = {
                "service": "sabnzbd",
                "findings": [
                    {
                        "setting": "test",
                        "current": "a",
                        "recommended": "b",
                        "severity": severity,
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z",
            }
            is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
            assert is_valid, f"Severity '{severity}' validation errors: {errors}"

    def test_invalid_severity_level(self):
        """Invalid severity level should fail."""
        response = {
            "service": "sabnzbd",
            "findings": [
                {
                    "setting": "test",
                    "current": "a",
                    "recommended": "b",
                    "severity": "extreme",
                }
            ],
            "timestamp": "2024-01-15T10:30:00Z",
        }
        is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
        assert not is_valid

    def test_score_bounds(self):
        """Score should be within 0-100."""
        # Valid score at boundaries
        for score in [0, 50, 100]:
            response = {
                "service": "sonarr",
                "findings": [],
                "timestamp": "2024-01-15T10:30:00Z",
                "score": score,
            }
            is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
            assert is_valid, f"Score {score} validation errors: {errors}"

    def test_invalid_score_below_zero(self):
        """Score below 0 should fail."""
        response = {
            "service": "sonarr",
            "findings": [],
            "timestamp": "2024-01-15T10:30:00Z",
            "score": -1,
        }
        is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
        assert not is_valid

    def test_invalid_score_above_hundred(self):
        """Score above 100 should fail."""
        response = {
            "service": "sonarr",
            "findings": [],
            "timestamp": "2024-01-15T10:30:00Z",
            "score": 101,
        }
        is_valid, errors = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)
        assert not is_valid


class TestContentRequestContracts:
    """Test content request API contracts."""

    def test_valid_content_request(self):
        """Valid content request should pass validation."""
        request = {"query": "Breaking Bad", "content_type": "series"}
        is_valid, errors = validate_schema(request, CONTENT_REQUEST_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_request_auto_type(self):
        """Request with auto content type should be valid."""
        request = {"query": "The Matrix", "content_type": "auto"}
        is_valid, errors = validate_schema(request, CONTENT_REQUEST_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_request_minimal(self):
        """Request with only query should be valid."""
        request = {"query": "Some content"}
        is_valid, errors = validate_schema(request, CONTENT_REQUEST_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_empty_query(self):
        """Empty query should fail."""
        request = {"query": ""}
        is_valid, errors = validate_schema(request, CONTENT_REQUEST_SCHEMA)
        assert not is_valid

    def test_missing_query(self):
        """Request without query should fail."""
        request = {"content_type": "movie"}
        is_valid, errors = validate_schema(request, CONTENT_REQUEST_SCHEMA)
        assert not is_valid

    def test_valid_content_response(self):
        """Valid content response should pass validation."""
        response = {
            "results": [
                {
                    "id": 81189,
                    "title": "Breaking Bad",
                    "year": 2008,
                    "overview": "A chemistry teacher becomes a meth producer",
                }
            ],
            "content_type": "series",
            "total_results": 1,
        }
        is_valid, errors = validate_schema(response, CONTENT_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_empty_results(self):
        """Empty results should be valid."""
        response = {"results": [], "content_type": "movie", "total_results": 0}
        is_valid, errors = validate_schema(response, CONTENT_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_multiple_results(self):
        """Multiple results should be valid."""
        response = {
            "results": [
                {"id": 1, "title": "Movie 1", "year": 2020},
                {"id": 2, "title": "Movie 2", "year": 2021},
                {"id": 3, "title": "Movie 3"},
            ],
            "content_type": "movie",
            "total_results": 3,
        }
        is_valid, errors = validate_schema(response, CONTENT_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"


class TestHealthCheckContracts:
    """Test health check API contracts."""

    def test_valid_healthy_response(self):
        """Valid healthy response should pass validation."""
        response = {
            "status": "healthy",
            "services": {
                "sabnzbd": {"status": "connected", "latency_ms": 45.2},
                "sonarr": {"status": "connected", "latency_ms": 32.1},
            },
            "timestamp": "2024-01-15T10:30:00Z",
        }
        is_valid, errors = validate_schema(response, HEALTH_CHECK_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_degraded_response(self):
        """Degraded status should be valid."""
        response = {
            "status": "degraded",
            "services": {
                "sabnzbd": {"status": "connected", "latency_ms": 45.2},
                "sonarr": {"status": "error", "error": "Connection refused"},
            },
            "timestamp": "2024-01-15T10:30:00Z",
        }
        is_valid, errors = validate_schema(response, HEALTH_CHECK_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_unhealthy_response(self):
        """Unhealthy status should be valid."""
        response = {"status": "unhealthy", "timestamp": "2024-01-15T10:30:00Z"}
        is_valid, errors = validate_schema(response, HEALTH_CHECK_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_status(self):
        """Invalid status should fail."""
        response = {"status": "unknown"}
        is_valid, errors = validate_schema(response, HEALTH_CHECK_RESPONSE_SCHEMA)
        assert not is_valid


class TestActivityLogContracts:
    """Test activity log entry contracts."""

    def test_valid_activity_entry(self):
        """Valid activity entry should pass validation."""
        entry = {
            "id": "act_abc123",
            "action": "download_started",
            "timestamp": "2024-01-15T10:30:00Z",
            "correlation_id": "corr_xyz789",
            "details": {"nzo_id": "SABnzbd_nzo_123", "filename": "test.nzb"},
            "source": "sabnzbd",
        }
        is_valid, errors = validate_schema(entry, ACTIVITY_LOG_ENTRY_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_minimal_entry(self):
        """Minimal activity entry should be valid."""
        entry = {"id": "act_min", "action": "system_start", "timestamp": "2024-01-15T10:30:00Z"}
        is_valid, errors = validate_schema(entry, ACTIVITY_LOG_ENTRY_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_missing_required_fields(self):
        """Entry without required fields should fail."""
        entry = {"action": "test"}
        is_valid, errors = validate_schema(entry, ACTIVITY_LOG_ENTRY_SCHEMA)
        assert not is_valid


class TestRequestResponseSymmetry:
    """Test that request and response schemas are symmetric."""

    def test_audit_request_response_service_match(self):
        """Audit response service should match request service."""
        request = {"service": "sabnzbd"}
        response = {
            "service": "sabnzbd",
            "findings": [],
            "timestamp": "2024-01-15T10:30:00Z",
        }

        req_valid, _ = validate_schema(request, CONFIG_AUDIT_REQUEST_SCHEMA)
        resp_valid, _ = validate_schema(response, CONFIG_AUDIT_RESPONSE_SCHEMA)

        assert req_valid and resp_valid
        assert request["service"] == response["service"]

    def test_content_request_response_type_match(self):
        """Content response type should be determinable from request."""
        request = {"query": "Breaking Bad", "content_type": "series"}
        response = {
            "results": [{"id": 1, "title": "Breaking Bad"}],
            "content_type": "series",
            "total_results": 1,
        }

        req_valid, _ = validate_schema(request, CONTENT_REQUEST_SCHEMA)
        resp_valid, _ = validate_schema(response, CONTENT_RESPONSE_SCHEMA)

        assert req_valid and resp_valid
        # If request specifies type, response should match
        if "content_type" in request and request["content_type"] != "auto":
            assert request["content_type"] == response["content_type"]
