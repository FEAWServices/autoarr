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
Tests for FastAPI middleware.

This module tests the custom middleware for error handling, logging,
and security headers.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from autoarr.api.middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    add_security_headers,
)
from autoarr.shared.core.exceptions import (
    CircuitBreakerOpenError,
    MCPConnectionError,
    MCPOrchestratorError,
    MCPTimeoutError,
    MCPToolError,
)

# Create test app
app = FastAPI()


@app.get("/test")
async def test_endpoint():
    """Test endpoint for middleware testing."""
    return {"message": "success"}


@app.get("/error/connection")
async def error_connection():
    """Endpoint that raises MCPConnectionError."""
    raise MCPConnectionError("Connection failed")


@app.get("/error/timeout")
async def error_timeout():
    """Endpoint that raises MCPTimeoutError."""
    raise MCPTimeoutError("Request timeout")


@app.get("/error/circuit-breaker")
async def error_circuit_breaker():
    """Endpoint that raises CircuitBreakerOpenError."""
    raise CircuitBreakerOpenError("Circuit breaker is open")


@app.get("/error/tool")
async def error_tool():
    """Endpoint that raises MCPToolError."""
    raise MCPToolError("Tool execution failed")


@app.get("/error/orchestrator")
async def error_orchestrator():
    """Endpoint that raises MCPOrchestratorError."""
    raise MCPOrchestratorError("Orchestrator error")


@app.get("/error/value")
async def error_value():
    """Endpoint that raises ValueError."""
    raise ValueError("Invalid value")


@app.get("/error/generic")
async def error_generic():
    """Endpoint that raises generic exception."""
    raise Exception("Unexpected error")


# Add middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.middleware("http")(add_security_headers)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestErrorHandlerMiddleware:
    """Test error handler middleware."""

    def test_successful_request(self, client):
        """Test that successful requests pass through."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

    def test_mcp_connection_error(self, client):
        """Test handling of MCPConnectionError."""
        response = client.get("/error/connection")
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "Service Unavailable"
        assert "Connection failed" in data["detail"]
        assert "timestamp" in data
        assert data["path"] == "/error/connection"

    def test_mcp_timeout_error(self, client):
        """Test handling of MCPTimeoutError."""
        response = client.get("/error/timeout")
        assert response.status_code == 504
        data = response.json()
        assert data["error"] == "Request Timeout"
        assert "Request timeout" in data["detail"]
        assert "timestamp" in data
        assert data["path"] == "/error/timeout"

    def test_circuit_breaker_open_error(self, client):
        """Test handling of CircuitBreakerOpenError."""
        response = client.get("/error/circuit-breaker")
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "Service Temporarily Unavailable"
        assert "Circuit breaker is open" in data["detail"]
        assert "timestamp" in data
        assert data["path"] == "/error/circuit-breaker"

    def test_mcp_tool_error(self, client):
        """Test handling of MCPToolError."""
        response = client.get("/error/tool")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Tool Execution Failed"
        assert "Tool execution failed" in data["detail"]
        assert "timestamp" in data
        assert data["path"] == "/error/tool"

    def test_mcp_orchestrator_error(self, client):
        """Test handling of MCPOrchestratorError."""
        response = client.get("/error/orchestrator")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Orchestrator Error"
        assert "Orchestrator error" in data["detail"]
        assert "timestamp" in data
        assert data["path"] == "/error/orchestrator"

    def test_value_error(self, client):
        """Test handling of ValueError."""
        response = client.get("/error/value")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Invalid Request"
        assert "Invalid value" in data["detail"]
        assert "timestamp" in data
        assert data["path"] == "/error/value"

    def test_generic_error(self, client):
        """Test handling of generic exceptions."""
        response = client.get("/error/generic")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal Server Error"
        assert data["detail"] == "An unexpected error occurred"
        assert "timestamp" in data
        assert data["path"] == "/error/generic"

    @patch("autoarr.api.middleware.logger")
    def test_generic_error_logs_exception(self, mock_logger, client):
        """Test that generic errors are logged."""
        client.get("/error/generic")
        # Verify logger.exception was called
        mock_logger.exception.assert_called_once()
        assert "Unhandled error" in str(mock_logger.exception.call_args)


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""

    @patch("autoarr.api.middleware.logger")
    def test_logs_request_start(self, mock_logger, client):
        """Test that request start is logged."""
        client.get("/test")
        # Check for request started log
        calls = [str(call) for call in mock_logger.info.call_args_list]  # noqa: F841
        assert any("Request started" in call for call in calls)
        assert any("GET /test" in call for call in calls)

    @patch("autoarr.api.middleware.logger")
    def test_logs_request_completion(self, mock_logger, client):
        """Test that request completion is logged."""
        client.get("/test")
        # Check for request completed log
        calls = [str(call) for call in mock_logger.info.call_args_list]  # noqa: F841
        assert any("Request completed" in call for call in calls)
        assert any("Status: 200" in call for call in calls)

    @patch("autoarr.api.middleware.logger")
    def test_logs_request_duration(self, mock_logger, client):
        """Test that request duration is logged."""
        client.get("/test")
        # Check for duration in logs
        calls = [str(call) for call in mock_logger.info.call_args_list]  # noqa: F841
        assert any("Duration:" in call for call in calls)

    def test_adds_request_id_header(self, client):
        """Test that X-Request-ID header is added to response."""
        response = client.get("/test", headers={"X-Request-ID": "test-123"})
        assert response.headers["X-Request-ID"] == "test-123"

    def test_adds_default_request_id_when_missing(self, client):
        """Test that default request ID is added when missing."""
        response = client.get("/test")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == "N/A"

    def test_adds_process_time_header(self, client):
        """Test that X-Process-Time header is added."""
        response = client.get("/test")
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    @patch("autoarr.api.middleware.logger")
    def test_logs_with_custom_request_id(self, mock_logger, client):
        """Test that custom request ID is logged."""
        client.get("/test", headers={"X-Request-ID": "custom-id-456"})
        calls = [str(call) for call in mock_logger.info.call_args_list]  # noqa: F841
        assert any("custom-id-456" in call for call in calls)


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""

    def test_adds_x_content_type_options_header(self, client):
        """Test that X-Content-Type-Options header is added."""
        response = client.get("/test")
        assert response.headers["X-Content-Type-Options"] == "nosnif"

    def test_adds_x_frame_options_header(self, client):
        """Test that X-Frame-Options header is added."""
        response = client.get("/test")
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_adds_x_xss_protection_header(self, client):
        """Test that X-XSS-Protection header is added."""
        response = client.get("/test")
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_adds_strict_transport_security_header(self, client):
        """Test that Strict-Transport-Security header is added."""
        response = client.get("/test")
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]

    def test_security_headers_on_error_responses(self, client):
        """Test that security headers are added even on error responses."""
        response = client.get("/error/value")
        assert response.headers["X-Content-Type-Options"] == "nosnif"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers


class TestMiddlewareIntegration:
    """Test middleware integration and interaction."""

    def test_all_middleware_applied_to_successful_request(self, client):
        """Test that all middleware is applied to successful requests."""
        response = client.get("/test", headers={"X-Request-ID": "integration-test"})

        # Check status
        assert response.status_code == 200

        # Check logging headers
        assert response.headers["X-Request-ID"] == "integration-test"
        assert "X-Process-Time" in response.headers

        # Check security headers
        assert response.headers["X-Content-Type-Options"] == "nosnif"
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_all_middleware_applied_to_error_request(self, client):
        """Test that all middleware is applied to error requests."""
        response = client.get("/error/tool", headers={"X-Request-ID": "error-test"})

        # Check error handling
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Tool Execution Failed"

        # Check logging headers
        assert response.headers["X-Request-ID"] == "error-test"
        assert "X-Process-Time" in response.headers

        # Check security headers
        assert response.headers["X-Content-Type-Options"] == "nosnif"

    @patch("autoarr.api.middleware.logger")
    def test_error_logged_with_request_tracking(self, mock_logger, client):
        """Test that errors are logged with request tracking information."""
        client.get("/error/generic", headers={"X-Request-ID": "error-tracking-test"})

        # Check that request was logged
        calls = [str(call) for call in mock_logger.info.call_args_list]  # noqa: F841
        assert any("error-tracking-test" in call for call in calls)

        # Check that error was logged
        mock_logger.exception.assert_called_once()
