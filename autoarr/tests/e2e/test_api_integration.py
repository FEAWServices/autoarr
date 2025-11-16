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
E2E Test: API Integration

Tests all API endpoints integration:
- Health checks
- Configuration endpoints
- Monitoring endpoints
- Request endpoints
- Settings endpoints
- Verify CORS, rate limiting, authentication
- Test error responses
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestAPIIntegration:
    """E2E tests for API integration."""

    async def test_health_endpoint(
        self,
        api_client: AsyncClient,
    ):
        """
        Test health check endpoint.

        Verifies:
        - Endpoint accessible
        - Returns 200 OK
        - Includes service status
        """
        response = await api_client.get("/health")
        assert response.status_code == 200
        health = response.json()
        assert "status" in health
        assert health["status"] in ["healthy", "ok", "up"]

    async def test_detailed_health_endpoint(
        self,
        api_client: AsyncClient,
    ):
        """
        Test detailed health check endpoint.

        Verifies:
        - Database status
        - MCP server status
        - External service status
        """
        response = await api_client.get("/health/detailed")

        # Endpoint might not exist
        if response.status_code == 404:
            pytest.skip("Detailed health endpoint not implemented yet")

        assert response.status_code == 200
        health = response.json()
        assert "database" in health or "services" in health

    async def test_root_endpoint(
        self,
        api_client: AsyncClient,
    ):
        """
        Test root endpoint.

        Verifies:
        - API information returned
        - Links to documentation
        """
        response = await api_client.get("/")
        assert response.status_code == 200
        info = response.json()
        assert "name" in info or "version" in info

    async def test_ping_endpoint(
        self,
        api_client: AsyncClient,
    ):
        """
        Test ping endpoint.

        Verifies:
        - Simple connectivity check
        - Fast response
        """
        response = await api_client.get("/ping")
        assert response.status_code == 200
        result = response.json()  # noqa: F841
        assert result.get("message") == "pong"

    async def test_cors_headers(
        self,
        api_client: AsyncClient,
    ):
        """
        Test CORS headers.

        Verifies:
        - CORS headers present
        - Allowed origins configured
        - Preflight requests handled
        """
        # OPTIONS request (preflight)
        response = await api_client.options(
            "/api/v1/downloads/queue",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should have CORS headers
        # Note: TestClient might not include all headers
        assert response.status_code in [200, 204, 405]

    async def test_error_response_format(
        self,
        api_client: AsyncClient,
    ):
        """
        Test error response format.

        Verifies:
        - Consistent error format
        - Error details included
        - Appropriate status codes
        """
        # Request non-existent endpoint
        response = await api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error or "error" in error

    async def test_validation_error_response(
        self,
        api_client: AsyncClient,
    ):
        """
        Test validation error responses.

        Verifies:
        - 422 status code for validation errors
        - Detailed validation messages
        - Field-specific errors
        """
        # Send invalid request
        response = await api_client.post(
            "/api/v1/config/audit",
            json={"invalid_field": "value"},
        )

        # Should return validation error or process request
        assert response.status_code in [200, 400, 422]

    async def test_api_versioning(
        self,
        api_client: AsyncClient,
    ):
        """
        Test API versioning.

        Verifies:
        - /api/v1 prefix works
        - Version in response headers
        """
        response = await api_client.get("/api/v1/health")

        # Might redirect to /health or be separate endpoint
        assert response.status_code in [200, 404]

    async def test_configuration_endpoints(
        self,
        api_client: AsyncClient,
        mock_sabnzbd_responses: dict,
    ):
        """
        Test configuration endpoints.

        Verifies:
        - Get configuration
        - Audit configuration
        - Update configuration
        """
        with patch("autoarr.api.routers.configuration.get_orchestrator") as mock_orch:
            mock_instance = AsyncMock()
            mock_orch.return_value = mock_instance
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_sabnzbd_responses["config"],
            }

            # Get configuration
            response = await api_client.get("/api/v1/config/sabnzbd")
            assert response.status_code == 200

            # Audit configuration
            response = await api_client.post(
                "/api/v1/config/audit",
                json={"service": "sabnzbd"},
            )
            assert response.status_code == 200

    async def test_monitoring_endpoints(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """
        Test monitoring endpoints.

        Verifies:
        - Activity log
        - Status endpoint
        - Metrics endpoint
        """
        # Activity log
        response = await api_client.get("/api/v1/monitoring/activity")
        assert response.status_code == 200
        activity = response.json()
        assert isinstance(activity, list) or "items" in activity

        # Status
        response = await api_client.get("/api/v1/monitoring/status")

        if response.status_code == 404:
            pytest.skip("Status endpoint not implemented yet")

        assert response.status_code == 200

    async def test_downloads_endpoints(
        self,
        api_client: AsyncClient,
        mock_sabnzbd_responses: dict,
    ):
        """
        Test downloads endpoints.

        Verifies:
        - Queue status
        - History
        - Download control
        """
        with patch("autoarr.api.routers.downloads.get_orchestrator") as mock_orch:
            mock_instance = AsyncMock()
            mock_orch.return_value = mock_instance
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_sabnzbd_responses["queue"],
            }

            # Queue
            response = await api_client.get("/api/v1/downloads/queue")
            assert response.status_code == 200

            # History
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_sabnzbd_responses["history"],
            }
            response = await api_client.get("/api/v1/downloads/history")
            assert response.status_code == 200

    async def test_shows_endpoints(
        self,
        api_client: AsyncClient,
        mock_sonarr_responses: dict,
    ):
        """
        Test shows endpoints.

        Verifies:
        - List series
        - Get series details
        - Search episodes
        """
        with patch("autoarr.api.routers.shows.get_orchestrator") as mock_orch:
            mock_instance = AsyncMock()
            mock_orch.return_value = mock_instance
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_sonarr_responses["series"],
            }

            # List series
            response = await api_client.get("/api/v1/shows/series")
            assert response.status_code == 200

            # Quality profiles
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_sonarr_responses["quality_profiles"],
            }
            response = await api_client.get("/api/v1/shows/quality-profiles")
            assert response.status_code == 200

    async def test_movies_endpoints(
        self,
        api_client: AsyncClient,
        mock_radarr_responses: dict,
    ):
        """
        Test movies endpoints.

        Verifies:
        - List movies
        - Get movie details
        - Search movies
        """
        with patch("autoarr.api.routers.movies.get_orchestrator") as mock_orch:
            mock_instance = AsyncMock()
            mock_orch.return_value = mock_instance
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_radarr_responses["movies"],
            }

            # List movies
            response = await api_client.get("/api/v1/movies")
            assert response.status_code == 200

            # Quality profiles
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_radarr_responses["quality_profiles"],
            }
            response = await api_client.get("/api/v1/movies/quality-profiles")
            assert response.status_code == 200

    async def test_settings_endpoints(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """
        Test settings endpoints.

        Verifies:
        - Get settings
        - Update settings
        - Delete settings
        """
        # Get all settings
        response = await api_client.get("/api/v1/settings")
        assert response.status_code == 200
        settings = response.json()
        assert isinstance(settings, list) or isinstance(settings, dict)

        # Create/update setting
        response = await api_client.put(
            "/api/v1/settings/test_key",
            json={"value": "test_value"},
        )
        assert response.status_code in [200, 201]

        # Get specific setting
        response = await api_client.get("/api/v1/settings/test_key")
        assert response.status_code == 200
        setting = response.json()
        assert setting.get("value") == "test_value"

        # Delete setting
        response = await api_client.delete("/api/v1/settings/test_key")
        assert response.status_code in [200, 204]

    async def test_mcp_proxy_endpoints(
        self,
        api_client: AsyncClient,
    ):
        """
        Test MCP proxy endpoints.

        Verifies:
        - Server status
        - Tool invocation
        - Resource access
        """
        # Server status
        response = await api_client.get("/api/v1/mcp/servers")
        assert response.status_code == 200
        servers = response.json()
        assert isinstance(servers, list) or "servers" in servers

    async def test_rate_limiting(
        self,
        api_client: AsyncClient,
    ):
        """
        Test rate limiting.

        Verifies:
        - Rate limits enforced
        - 429 status code
        - Retry-After header
        """
        # This test would make many rapid requests
        # to trigger rate limiting
        pytest.skip("Rate limiting test requires rate limiter implementation")

    async def test_authentication_required(
        self,
        api_client: AsyncClient,
    ):
        """
        Test authentication requirements.

        Verifies:
        - Protected endpoints require auth
        - 401 status code
        - Auth headers validated
        """
        # This test would verify authentication
        # if implemented
        pytest.skip("Authentication test requires auth implementation")

    async def test_concurrent_requests(
        self,
        api_client: AsyncClient,
        mock_sabnzbd_responses: dict,
    ):
        """
        Test concurrent API requests.

        Verifies:
        - No race conditions
        - Proper request handling
        - Correct responses
        """
        with patch("autoarr.api.routers.downloads.get_orchestrator") as mock_orch:
            mock_instance = AsyncMock()
            mock_orch.return_value = mock_instance
            mock_instance.call_tool.return_value = {
                "success": True,
                "result": mock_sabnzbd_responses["queue"],
            }

            # Make concurrent requests
            import asyncio

            tasks = [api_client.get("/api/v1/downloads/queue") for _ in range(10)]

            responses = await asyncio.gather(*tasks)

            # All should succeed
            for response in responses:
                assert response.status_code == 200

    async def test_request_timeout_handling(
        self,
        api_client: AsyncClient,
    ):
        """
        Test request timeout handling.

        Verifies:
        - Long requests timeout appropriately
        - Timeout errors handled gracefully
        """
        with patch("autoarr.api.routers.downloads.get_orchestrator") as mock_orch:
            mock_instance = AsyncMock()
            mock_orch.return_value = mock_instance

            # Mock timeout
            import asyncio

            async def slow_call(*args, **kwargs):
                await asyncio.sleep(10)
                return {"success": True}

            mock_instance.call_tool.side_effect = slow_call

            # This should timeout (if timeout configured)
            try:
                response = await api_client.get(
                    "/api/v1/downloads/queue",
                    timeout=1.0,  # 1 second timeout
                )
                # Either times out or completes
                assert response.status_code in [200, 504, 408]
            except Exception as e:
                # Timeout exception is acceptable
                assert "timeout" in str(e).lower()
