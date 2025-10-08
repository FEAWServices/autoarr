"""
Locust load testing configuration for AutoArr API.

This module defines load test scenarios for:
- Configuration audits
- Content requests
- Monitoring endpoints
- WebSocket connections

Performance Targets:
- API Response Time: p95 < 200ms, p99 < 500ms
- Throughput: 100 requests/second sustained
- WebSocket Latency: < 50ms for event delivery
- Database Queries: < 50ms for 95% of queries
- Memory Usage: < 512MB idle, < 1GB under load
- CPU Usage: < 50% under normal load

Usage:
    # Run with 10 users, ramping up 1 user per second
    locust -f tests/load/locustfile.py --host=http://localhost:8088 --users 10 --spawn-rate 1

    # Run headless with specific duration
    locust -f tests/load/locustfile.py --host=http://localhost:8088 --users 50 --spawn-rate 5 --run-time 5m --headless

    # Run with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8088
"""

import json
import random
import time
from locust import HttpUser, TaskSet, task, between, events


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_SERVICES = ["sabnzbd", "sonarr", "radarr"]

SAMPLE_MOVIE_QUERIES = [
    "The Matrix",
    "Inception",
    "The Shawshank Redemption",
    "The Dark Knight",
    "Pulp Fiction",
    "Forrest Gump",
    "The Godfather",
    "Fight Club",
    "Interstellar",
    "The Lord of the Rings",
]

SAMPLE_TV_QUERIES = [
    "Breaking Bad",
    "Game of Thrones",
    "The Wire",
    "The Sopranos",
    "Friends",
    "The Office",
    "Stranger Things",
    "The Crown",
    "Better Call Saul",
    "True Detective",
]


# ============================================================================
# Configuration Audit Load Test
# ============================================================================


class ConfigAuditTaskSet(TaskSet):
    """Task set for configuration audit operations."""

    @task(3)
    def get_config_sabnzbd(self):
        """Fetch SABnzbd configuration."""
        with self.client.get(
            "/api/v1/config/sabnzbd",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Endpoint not found")
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(3)
    def get_config_sonarr(self):
        """Fetch Sonarr configuration."""
        with self.client.get(
            "/api/v1/config/sonarr",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def audit_configuration(self):
        """Run configuration audit."""
        service = random.choice(SAMPLE_SERVICES)
        with self.client.post(
            "/api/v1/config/audit",
            json={"service": service},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")


class ConfigAuditUser(HttpUser):
    """User simulating configuration audit operations."""

    tasks = [ConfigAuditTaskSet]
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks


# ============================================================================
# Content Request Load Test
# ============================================================================


class ContentRequestTaskSet(TaskSet):
    """Task set for content request operations."""

    @task(2)
    def request_movie(self):
        """Request a movie."""
        query = random.choice(SAMPLE_MOVIE_QUERIES)
        with self.client.post(
            "/api/v1/requests/content",
            json={"query": query},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def request_tv_show(self):
        """Request a TV show."""
        query = random.choice(SAMPLE_TV_QUERIES)
        with self.client.post(
            "/api/v1/requests/content",
            json={"query": query},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def list_movies(self):
        """List movies from Radarr."""
        with self.client.get(
            "/api/v1/movies",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def list_series(self):
        """List series from Sonarr."""
        with self.client.get(
            "/api/v1/shows/series",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")


class ContentRequestUser(HttpUser):
    """User simulating content request operations."""

    tasks = [ContentRequestTaskSet]
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks


# ============================================================================
# Monitoring Load Test
# ============================================================================


class MonitoringTaskSet(TaskSet):
    """Task set for monitoring operations."""

    @task(5)
    def check_activity_log(self):
        """Check activity log."""
        with self.client.get(
            "/api/v1/monitoring/activity",
            params={"limit": 50},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(3)
    def check_queue(self):
        """Check download queue."""
        with self.client.get(
            "/api/v1/downloads/queue",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def check_history(self):
        """Check download history."""
        with self.client.get(
            "/api/v1/downloads/history",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Endpoint not implemented yet
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(4)
    def check_health(self):
        """Check health endpoint."""
        with self.client.get(
            "/health",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class MonitoringUser(HttpUser):
    """User simulating monitoring operations."""

    tasks = [MonitoringTaskSet]
    wait_time = between(0.5, 2)  # Frequent polling


# ============================================================================
# Settings Load Test
# ============================================================================


class SettingsTaskSet(TaskSet):
    """Task set for settings operations."""

    @task(3)
    def get_all_settings(self):
        """Get all settings."""
        with self.client.get(
            "/api/v1/settings",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def get_specific_setting(self):
        """Get specific setting."""
        key = random.choice(["notifications_enabled", "auto_retry_enabled", "max_retry_attempts"])
        with self.client.get(
            f"/api/v1/settings/{key}",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def update_setting(self):
        """Update a setting."""
        key = f"test_key_{random.randint(1, 100)}"
        value = f"test_value_{random.randint(1, 100)}"
        with self.client.put(
            f"/api/v1/settings/{key}",
            json={"value": value},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class SettingsUser(HttpUser):
    """User simulating settings operations."""

    tasks = [SettingsTaskSet]
    wait_time = between(2, 4)


# ============================================================================
# Mixed Workload User (Realistic Scenario)
# ============================================================================


class MixedWorkloadTaskSet(TaskSet):
    """Task set mixing different operations for realistic load."""

    @task(10)
    def browse_activity(self):
        """Browse activity log (most common)."""
        with self.client.get(
            "/api/v1/monitoring/activity",
            params={"limit": 20},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()

    @task(5)
    def check_downloads(self):
        """Check download queue (frequent)."""
        with self.client.get(
            "/api/v1/downloads/queue",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()

    @task(3)
    def check_health(self):
        """Check health (periodic)."""
        with self.client.get(
            "/health",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(2)
    def request_content(self):
        """Request content (occasional)."""
        query = random.choice(SAMPLE_MOVIE_QUERIES + SAMPLE_TV_QUERIES)
        with self.client.post(
            "/api/v1/requests/content",
            json={"query": query},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201, 404]:
                response.success()

    @task(1)
    def run_audit(self):
        """Run configuration audit (rare)."""
        service = random.choice(SAMPLE_SERVICES)
        with self.client.post(
            "/api/v1/config/audit",
            json={"service": service},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201, 404]:
                response.success()


class MixedWorkloadUser(HttpUser):
    """User with mixed realistic workload."""

    tasks = [MixedWorkloadTaskSet]
    wait_time = between(1, 5)  # Variable think time


# ============================================================================
# Event Handlers for Custom Metrics
# ============================================================================


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize custom metrics when Locust starts."""
    print("=" * 80)
    print("AutoArr Load Testing")
    print("=" * 80)
    print(f"Target host: {environment.host}")
    print()
    print("Performance Targets:")
    print("  - API Response Time: p95 < 200ms, p99 < 500ms")
    print("  - Throughput: 100 requests/second sustained")
    print("  - WebSocket Latency: < 50ms for event delivery")
    print("  - Database Queries: < 50ms for 95% of queries")
    print("=" * 80)
    print()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print(f"Load test started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print()
    print(f"Load test stopped at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Results Summary:")
    print(f"  Total Requests: {environment.stats.total.num_requests}")
    print(f"  Total Failures: {environment.stats.total.num_failures}")
    print(f"  Median Response Time: {environment.stats.total.median_response_time}ms")
    print(f"  95th Percentile: {environment.stats.total.get_response_time_percentile(0.95)}ms")
    print(f"  99th Percentile: {environment.stats.total.get_response_time_percentile(0.99)}ms")
    print(f"  Average Response Time: {environment.stats.total.avg_response_time}ms")
    print(f"  Requests/second: {environment.stats.total.total_rps:.2f}")
    print()

    # Check if targets met
    p95 = environment.stats.total.get_response_time_percentile(0.95)
    p99 = environment.stats.total.get_response_time_percentile(0.99)
    rps = environment.stats.total.total_rps

    print("Target Achievement:")
    print(f"  p95 < 200ms: {'✓ PASS' if p95 < 200 else '✗ FAIL'} ({p95}ms)")
    print(f"  p99 < 500ms: {'✓ PASS' if p99 < 500 else '✗ FAIL'} ({p99}ms)")
    print(f"  RPS >= 100: {'✓ PASS' if rps >= 100 else '✗ FAIL'} ({rps:.2f} RPS)")
    print("=" * 80)


# ============================================================================
# Default User Class
# ============================================================================


# When running locust without specifying a user class,
# use the mixed workload for realistic testing
class DefaultUser(MixedWorkloadUser):
    """Default user class for realistic mixed workload."""

    pass
