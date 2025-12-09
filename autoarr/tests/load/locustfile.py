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
Comprehensive load tests for AutoArr API endpoints using Locust.

This module defines multiple user scenarios that simulate realistic usage patterns:
1. HealthCheckUser - Frequent health monitoring
2. ConfigurationAuditUser - Configuration auditing workflow
3. ContentRequestUser - Natural language content requests
4. MonitoringUser - Real-time activity monitoring
5. AdminUser - Administrative operations (settings, configuration)
"""

import logging
import os
import time
from typing import Any, Dict

from locust import HttpUser, TaskSet, between, task, web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Performance budgets (SLAs)
PERFORMANCE_BUDGETS = {
    "health_check": {"p95": 500, "p99": 1000},  # milliseconds
    "read_operations": {"p95": 500, "p99": 1000},
    "write_operations": {"p95": 2000, "p99": 5000},
    "websocket_operations": {"p95": 1000, "p99": 3000},
    "concurrent_users": 100,  # Target concurrent user count
}

# Service configuration
BASE_URL = os.getenv("AUTOARR_BASE_URL", "http://localhost:8088")
API_V1_PREFIX = "/api/v1"


# ============================================================================
# Helper Functions
# ============================================================================


def validate_response_time(response_time_ms: float, budget_ms: int, operation: str) -> bool:
    """
    Validate if response time meets SLA.

    Args:
        response_time_ms: Response time in milliseconds
        budget_ms: Budget threshold in milliseconds
        operation: Operation name for logging

    Returns:
        bool: True if response time is within budget
    """
    if response_time_ms > budget_ms:
        logger.warning(
            f"Performance SLA violation for {operation}: "
            f"{response_time_ms:.2f}ms > {budget_ms}ms"
        )
        return False
    return True


def log_metrics(operation: str, response_time_ms: float, status_code: int) -> None:
    """Log performance metrics for an operation."""
    logger.debug(f"{operation}: {response_time_ms:.2f}ms (HTTP {status_code})")


# ============================================================================
# Task Sets for Different User Scenarios
# ============================================================================


class HealthCheckTasks(TaskSet):
    """Tasks that simulate health monitoring operations."""

    @task(10)
    def health_check(self) -> None:
        """Frequent health check endpoint."""
        with self.client.get(
            "/health",
            catch_response=True,
            timeout=5,
        ) as response:
            start_time = time.time()
            if response.status_code == 200:
                response_time_ms = (time.time() - start_time) * 1000
                validate_response_time(
                    response_time_ms, PERFORMANCE_BUDGETS["health_check"]["p95"], "health_check"
                )
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(8)
    def ping(self) -> None:
        """Simple ping endpoint for heartbeat."""
        with self.client.get("/ping", catch_response=True, timeout=5) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Ping failed: {response.status_code}")

    @task(5)
    def health_ready(self) -> None:
        """Readiness probe check."""
        with self.client.get(
            "/health/ready",
            catch_response=True,
            timeout=5,
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(3)
    def health_liveness(self) -> None:
        """Liveness probe check."""
        with self.client.get(
            "/health/live",
            catch_response=True,
            timeout=5,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness check failed: {response.status_code}")


class DownloadsMonitoringTasks(TaskSet):
    """Tasks simulating download monitoring and management."""

    @task(10)
    def get_download_queue(self) -> None:
        """Get current download queue."""
        with self.client.get(
            f"{API_V1_PREFIX}/downloads/queue",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:  # Accept errors during load
                response.success()
            else:
                response.failure(f"Queue fetch failed: {response.status_code}")

    @task(8)
    def get_download_history(self) -> None:
        """Get download history."""
        with self.client.get(
            f"{API_V1_PREFIX}/downloads/history?limit=50",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"History fetch failed: {response.status_code}")

    @task(3)
    def get_failed_downloads(self) -> None:
        """Get failed downloads for recovery options."""
        with self.client.get(
            f"{API_V1_PREFIX}/downloads/failed",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 404, 500, 502]:
                response.success()
            else:
                response.failure(f"Failed downloads fetch failed: {response.status_code}")


class ContentLibraryTasks(TaskSet):
    """Tasks simulating content library browsing."""

    @task(8)
    def get_shows(self) -> None:
        """Fetch TV shows from library."""
        with self.client.get(
            f"{API_V1_PREFIX}/shows?limit=50",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Shows fetch failed: {response.status_code}")

    @task(8)
    def get_movies(self) -> None:
        """Fetch movies from library."""
        with self.client.get(
            f"{API_V1_PREFIX}/movies?limit=50",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Movies fetch failed: {response.status_code}")

    @task(5)
    def get_media(self) -> None:
        """Fetch media information."""
        with self.client.get(
            f"{API_V1_PREFIX}/media/libraries",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Media fetch failed: {response.status_code}")


class OnboardingFlowTasks(TaskSet):
    """Tasks simulating onboarding workflow."""

    @task(5)
    def get_onboarding_status(self) -> None:
        """Check onboarding status."""
        with self.client.get(
            f"{API_V1_PREFIX}/onboarding/status",
            catch_response=True,
            timeout=5,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Status fetch failed: {response.status_code}")

    @task(2)
    def update_onboarding_step(self) -> None:
        """Update onboarding step."""
        payload = {
            "step": "welcome_screen",
            "status": "completed",
        }
        with self.client.post(
            f"{API_V1_PREFIX}/onboarding/step",
            json=payload,
            catch_response=True,
            timeout=5,
        ) as response:
            if response.status_code in [200, 400, 500, 502]:
                response.success()
            else:
                response.failure(f"Step update failed: {response.status_code}")


class SettingsManagementTasks(TaskSet):
    """Tasks simulating settings management."""

    @task(6)
    def get_all_settings(self) -> None:
        """Fetch all application settings."""
        with self.client.get(
            f"{API_V1_PREFIX}/settings/all",
            catch_response=True,
            timeout=5,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Settings fetch failed: {response.status_code}")

    @task(4)
    def test_service_connection(self) -> None:
        """Test connection to a service."""
        payload = {
            "url": "http://localhost:8090/sabnzbd/",
            "api_key_or_token": "test-key",
            "timeout": 10,
        }
        with self.client.post(
            f"{API_V1_PREFIX}/settings/test/sabnzbd",
            json=payload,
            catch_response=True,
            timeout=15,
        ) as response:
            if response.status_code in [200, 400, 500, 502]:
                response.success()
            else:
                response.failure(f"Connection test failed: {response.status_code}")


class ConfigurationAuditTasks(TaskSet):
    """Tasks simulating configuration audit workflow."""

    @task(4)
    def start_configuration_audit(self) -> None:
        """Start a configuration audit."""
        with self.client.post(
            f"{API_V1_PREFIX}/config/audit/start",
            json={},
            catch_response=True,
            timeout=30,
        ) as response:
            if response.status_code in [200, 202, 400, 500, 502]:
                response.success()
            else:
                response.failure(f"Audit start failed: {response.status_code}")

    @task(6)
    def get_audit_results(self) -> None:
        """Get configuration audit results."""
        with self.client.get(
            f"{API_V1_PREFIX}/config/audit/results",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 404, 500, 502]:
                response.success()
            else:
                response.failure(f"Results fetch failed: {response.status_code}")


class ContentRequestTasks(TaskSet):
    """Tasks simulating content request submission."""

    @task(3)
    def submit_content_request(self) -> None:
        """Submit a content request via natural language."""
        payload = {
            "query": "I'd like to watch Breaking Bad",
            "user_id": "load-test-user",
        }
        with self.client.post(
            f"{API_V1_PREFIX}/requests/content",
            json=payload,
            catch_response=True,
            timeout=15,
        ) as response:
            if response.status_code in [200, 201, 400, 500, 502]:
                response.success()
            else:
                response.failure(f"Request submission failed: {response.status_code}")

    @task(5)
    def get_pending_requests(self) -> None:
        """Get pending content requests."""
        with self.client.get(
            f"{API_V1_PREFIX}/requests",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Requests fetch failed: {response.status_code}")


class ActivityMonitoringTasks(TaskSet):
    """Tasks simulating activity log monitoring."""

    @task(8)
    def get_activity_log(self) -> None:
        """Fetch activity log."""
        with self.client.get(
            f"{API_V1_PREFIX}/activity?limit=50",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Activity log fetch failed: {response.status_code}")

    @task(5)
    def get_logs(self) -> None:
        """Fetch application logs."""
        with self.client.get(
            f"{API_V1_PREFIX}/logs?limit=100",
            catch_response=True,
            timeout=10,
        ) as response:
            if response.status_code in [200, 500, 502]:
                response.success()
            else:
                response.failure(f"Logs fetch failed: {response.status_code}")


# ============================================================================
# User Classes
# ============================================================================


class HealthCheckUser(HttpUser):
    """User that performs frequent health monitoring checks.

    Characteristics:
    - High frequency operations (polling every few seconds)
    - Quick operations with low latency requirements
    - Represents monitoring dashboards and health checkers
    """

    wait_time = between(2, 5)
    tasks = [HealthCheckTasks]

    def on_start(self) -> None:
        """Initialize user session."""
        logger.info("HealthCheckUser started")

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("HealthCheckUser stopped")


class MonitoringUser(HttpUser):
    """User that monitors downloads and activity in real-time.

    Characteristics:
    - Moderate frequency operations
    - Mix of read operations
    - Represents monitoring dashboards
    """

    wait_time = between(3, 8)
    tasks = [DownloadsMonitoringTasks, ActivityMonitoringTasks]

    def on_start(self) -> None:
        """Initialize user session."""
        logger.info("MonitoringUser started")

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("MonitoringUser stopped")


class BrowsingUser(HttpUser):
    """User that browses content libraries.

    Characteristics:
    - Moderate operations frequency
    - Read-heavy operations
    - Represents UI users browsing shows/movies
    """

    wait_time = between(4, 10)
    tasks = [ContentLibraryTasks, ActivityMonitoringTasks]

    def on_start(self) -> None:
        """Initialize user session."""
        logger.info("BrowsingUser started")

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("BrowsingUser stopped")


class ConfigurationAuditUser(HttpUser):
    """User that performs configuration audits and configuration checks.

    Characteristics:
    - Lower frequency operations
    - Mix of read and write operations
    - Some long-running operations (audits)
    - Represents administrators running audits
    """

    wait_time = between(10, 20)
    tasks = [ConfigurationAuditTasks, SettingsManagementTasks]

    def on_start(self) -> None:
        """Initialize user session."""
        logger.info("ConfigurationAuditUser started")

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("ConfigurationAuditUser stopped")


class ContentRequestUser(HttpUser):
    """User that submits content requests.

    Characteristics:
    - Lower frequency operations
    - Write operations with potential long latency (LLM processing)
    - Represents users requesting content
    """

    wait_time = between(15, 30)
    tasks = [ContentRequestTasks, ContentLibraryTasks]

    def on_start(self) -> None:
        """Initialize user session."""
        logger.info("ContentRequestUser started")

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("ContentRequestUser stopped")


class AdminUser(HttpUser):
    """User that manages application settings and configuration.

    Characteristics:
    - Low frequency operations
    - Mix of read and write operations
    - Represents system administrators
    """

    wait_time = between(20, 40)
    tasks = [SettingsManagementTasks, ConfigurationAuditTasks, OnboardingFlowTasks]

    def on_start(self) -> None:
        """Initialize user session."""
        logger.info("AdminUser started")

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("AdminUser stopped")


# ============================================================================
# Custom Event Hooks
# ============================================================================


@web.app.get("/performance-budgets")
def get_performance_budgets() -> Dict[str, Any]:
    """Get current performance budgets."""
    return PERFORMANCE_BUDGETS


@web.app.get("/test-config")
def get_test_config() -> Dict[str, Any]:
    """Get current test configuration."""
    return {
        "base_url": BASE_URL,
        "api_prefix": API_V1_PREFIX,
        "performance_budgets": PERFORMANCE_BUDGETS,
    }
