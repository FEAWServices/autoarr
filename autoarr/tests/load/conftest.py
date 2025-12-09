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
Shared configuration and fixtures for load tests.

This module provides:
- Common test utilities
- Performance metrics collection
- CSV report generation
- Performance budget validation
"""

import csv
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Constants
# ============================================================================

# Test environment
BASE_URL = os.getenv("AUTOARR_BASE_URL", "http://localhost:8088")
API_V1_PREFIX = "/api/v1"

# Performance budgets (all in milliseconds)
PERFORMANCE_BUDGETS = {
    "health_endpoints": {"p95": 500, "p99": 1000},
    "read_endpoints": {"p95": 500, "p99": 1000},
    "write_endpoints": {"p95": 2000, "p99": 5000},
    "slow_endpoints": {"p95": 5000, "p99": 10000},  # For audits, LLM operations
    "websocket": {"p95": 1000, "p99": 3000},
}

# Test parameters
DEFAULT_TIMEOUT = 30  # seconds
REPORT_DIR = Path(__file__).parent / "reports"


# ============================================================================
# Performance Metrics Collection
# ============================================================================


class PerformanceMetrics:
    """Collect and analyze performance metrics from load tests."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.start_time = time.time()
        self.response_times: Dict[str, List[float]] = {}
        self.status_codes: Dict[str, Dict[int, int]] = {}
        self.errors: List[Dict[str, Any]] = []
        self.endpoints_tested: set = set()

    def record_response(
        self,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        error: Optional[str] = None,
    ) -> None:
        """Record a response metric."""
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        if endpoint not in self.status_codes:
            self.status_codes[endpoint] = {}

        self.response_times[endpoint].append(response_time_ms)

        status_count = self.status_codes[endpoint].get(status_code, 0)
        self.status_codes[endpoint][status_code] = status_count + 1

        self.endpoints_tested.add(endpoint)

        if error:
            self.errors.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": endpoint,
                    "response_time_ms": response_time_ms,
                    "status_code": status_code,
                    "error": error,
                }
            )

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        duration = time.time() - self.start_time

        summary: Dict[str, Any] = {
            "duration_seconds": round(duration, 2),
            "total_endpoints_tested": len(self.endpoints_tested),
            "total_errors": len(self.errors),
            "endpoints": {},
        }

        for endpoint, times in self.response_times.items():
            sorted_times = sorted(times)
            n = len(sorted_times)

            summary["endpoints"][endpoint] = {
                "request_count": n,
                "min_ms": round(sorted_times[0], 2),
                "max_ms": round(sorted_times[-1], 2),
                "avg_ms": round(sum(sorted_times) / n, 2),
                "p50_ms": round(sorted_times[n // 2], 2),
                "p95_ms": round(sorted_times[int(n * 0.95)], 2),
                "p99_ms": round(sorted_times[int(n * 0.99)], 2),
                "status_codes": self.status_codes.get(endpoint, {}),
            }

        return summary

    def save_report(self, filename: str = "load_test_report.json") -> Path:
        """Save metrics report to JSON."""
        REPORT_DIR.mkdir(exist_ok=True)
        filepath = REPORT_DIR / filename

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "errors": self.errors[-100:],  # Last 100 errors
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {filepath}")
        return filepath


# ============================================================================
# Performance Budget Validation
# ============================================================================


class PerformanceBudgetValidator:
    """Validate if performance meets defined budgets."""

    def __init__(self) -> None:
        """Initialize validator."""
        self.violations: List[Dict[str, Any]] = []

    def validate_endpoint(
        self,
        endpoint: str,
        response_time_ms: float,
        budget_type: str = "read_endpoints",
    ) -> bool:
        """
        Validate if endpoint response time is within budget.

        Args:
            endpoint: API endpoint path
            response_time_ms: Response time in milliseconds
            budget_type: Type of budget to apply

        Returns:
            bool: True if within budget, False otherwise
        """
        if budget_type not in PERFORMANCE_BUDGETS:
            logger.warning(f"Unknown budget type: {budget_type}")
            return True

        budget = PERFORMANCE_BUDGETS[budget_type]

        # For now, validate against p95
        if response_time_ms > budget["p95"]:
            violation = {
                "endpoint": endpoint,
                "response_time_ms": response_time_ms,
                "budget_ms": budget["p95"],
                "exceeded_by_ms": response_time_ms - budget["p95"],
                "timestamp": datetime.now().isoformat(),
            }
            self.violations.append(violation)
            logger.warning(
                f"Performance budget violation: {endpoint} took {response_time_ms}ms "
                f"(budget: {budget['p95']}ms)"
            )
            return False

        return True

    def validate_summary(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Validate metrics summary against budgets."""
        summary = metrics.get_summary()
        validation_result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "total_violations": 0,
            "endpoints_within_budget": 0,
            "endpoints_exceeded_budget": 0,
            "endpoint_results": {},
        }

        for endpoint, stats in summary["endpoints"].items():
            # Determine budget type based on endpoint
            if "health" in endpoint:
                budget_type = "health_endpoints"
            elif "config/audit" in endpoint or "chat" in endpoint:
                budget_type = "slow_endpoints"
            elif endpoint.endswith("/test") or endpoint.endswith("/test/"):
                budget_type = "write_endpoints"
            else:
                # Default to read endpoints for most GET operations
                budget_type = "read_endpoints"

            budget = PERFORMANCE_BUDGETS.get(budget_type, PERFORMANCE_BUDGETS["read_endpoints"])

            p95_within = stats["p95_ms"] <= budget["p95"]
            p99_within = stats["p99_ms"] <= budget["p99"]
            within_budget = p95_within and p99_within

            validation_result["endpoint_results"][endpoint] = {
                "within_budget": within_budget,
                "p95_budget": budget["p95"],
                "p95_actual": stats["p95_ms"],
                "p95_exceeded": not p95_within,
                "p99_budget": budget["p99"],
                "p99_actual": stats["p99_ms"],
                "p99_exceeded": not p99_within,
            }

            if within_budget:
                validation_result["endpoints_within_budget"] += 1
            else:
                validation_result["endpoints_exceeded_budget"] += 1
                validation_result["total_violations"] += 1

        return validation_result

    def save_violations(self, filename: str = "performance_violations.csv") -> Optional[Path]:
        """Save violations to CSV file."""
        if not self.violations:
            logger.info("No performance budget violations found")
            return None

        REPORT_DIR.mkdir(exist_ok=True)
        filepath = REPORT_DIR / filename

        fieldnames = ["timestamp", "endpoint", "response_time_ms", "budget_ms", "exceeded_by_ms"]

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.violations)

        logger.info(f"Violations report saved to {filepath}")
        return filepath


# ============================================================================
# Test Data Generators
# ============================================================================


def generate_test_payload(payload_type: str) -> Dict[str, Any]:
    """Generate test payload for different operations."""
    payloads = {
        "content_request": {
            "user_message": "I'd like to watch Breaking Bad",
            "request_type": "show",
        },
        "onboarding_step": {
            "step": "welcome_screen",
            "status": "completed",
        },
        "service_config": {
            "url": "http://localhost:8090/sabnzbd/",
            "api_key_or_token": "test-key",
            "timeout": 10,
        },
        "settings": {
            "setting_name": "test_setting",
            "value": "test_value",
        },
    }
    return payloads.get(payload_type, {})


# ============================================================================
# URL Builder
# ============================================================================


def build_url(endpoint: str, api_prefix: bool = True) -> str:
    """
    Build full URL for endpoint.

    Args:
        endpoint: API endpoint path
        api_prefix: Whether to add API v1 prefix

    Returns:
        Full URL path
    """
    if api_prefix and not endpoint.startswith(API_V1_PREFIX):
        return f"{API_V1_PREFIX}{endpoint}"
    return endpoint


# ============================================================================
# Environment Validation
# ============================================================================


def validate_environment() -> bool:
    """Validate that test environment is properly configured."""
    logger.info(f"Test Configuration:")
    logger.info(f"  Base URL: {BASE_URL}")
    logger.info(f"  API Prefix: {API_V1_PREFIX}")
    logger.info(f"  Report Directory: {REPORT_DIR}")

    # Attempt to connect to base URL
    try:
        import httpx

        with httpx.Client(timeout=5) as client:
            response = client.get(f"{BASE_URL}/health", follow_redirects=True)
            if response.status_code == 200:
                logger.info("✓ AutoArr API is accessible")
                return True
            else:
                logger.warning(
                    f"✗ AutoArr API returned status {response.status_code}. "
                    "Tests may fail."
                )
                return False
    except Exception as e:
        logger.error(f"✗ Cannot connect to AutoArr API: {e}")
        logger.error("Please ensure the API is running at: http://localhost:8088")
        return False


if __name__ == "__main__":
    """Validate environment when run as script."""
    validate_environment()
