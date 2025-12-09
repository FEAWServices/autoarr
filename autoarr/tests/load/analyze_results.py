#!/usr/bin/env python3

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
Analyze Locust load test results and validate against performance budgets.

This script:
1. Reads CSV output from Locust tests
2. Analyzes performance metrics
3. Compares against performance budgets
4. Generates summary report with pass/fail status
5. Identifies performance bottlenecks

Usage:
    python analyze_results.py <results_csv_file>
    python analyze_results.py results/baseline_20231215_120000_stats.csv
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List

# ============================================================================
# Performance Budgets (SLAs)
# ============================================================================

PERFORMANCE_BUDGETS: Dict[str, Dict[str, int]] = {
    "health": {"p95": 500, "p99": 1000},
    "read": {"p95": 500, "p99": 1000},
    "write": {"p95": 2000, "p99": 5000},
    "audit": {"p95": 5000, "p99": 10000},
    "ws": {"p95": 1000, "p99": 3000},
}


# ============================================================================
# Color Codes
# ============================================================================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
END = "\033[0m"


# ============================================================================
# Utility Functions
# ============================================================================


def get_budget_type(endpoint_name: str) -> str:
    """
    Determine budget type based on endpoint name.

    Args:
        endpoint_name: API endpoint name/path

    Returns:
        Budget type key
    """
    endpoint_lower = endpoint_name.lower()

    if "health" in endpoint_lower:
        return "health"
    elif "config/audit" in endpoint_lower or "chat" in endpoint_lower:
        return "audit"
    elif "ws" in endpoint_lower or "websocket" in endpoint_lower:
        return "ws"
    elif any(x in endpoint_lower for x in ["/test", "post", "put", "delete"]):
        return "write"
    else:
        return "read"


def format_ms(value: float) -> str:
    """Format milliseconds for display."""
    return f"{value:.2f}ms"


def print_header(text: str) -> None:
    """Print formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*80}{END}")
    print(f"{BOLD}{BLUE}{text:^80}{END}")
    print(f"{BOLD}{BLUE}{'='*80}{END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓{END} {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{RED}✗{END} {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠{END} {text}")


def print_metric(label: str, value: str, ok: bool = True) -> None:
    """Print metric line."""
    color = GREEN if ok else RED
    print(f"  {label:<30} {color}{value}{END}")


# ============================================================================
# Results Analysis
# ============================================================================


class LoadTestAnalyzer:
    """Analyze load test results."""

    def __init__(self, csv_file: Path) -> None:
        """Initialize analyzer with results file."""
        self.csv_file = csv_file
        self.rows: List[Dict[str, str]] = []
        self.summary: Dict[str, Any] = {}
        self.violations: List[Dict[str, Any]] = []

    def load_results(self) -> bool:
        """Load and parse CSV results file."""
        if not self.csv_file.exists():
            print_error(f"File not found: {self.csv_file}")
            return False

        try:
            with open(self.csv_file, "r") as f:
                reader = csv.DictReader(f)
                self.rows = list(reader)

            if not self.rows:
                print_error("CSV file is empty")
                return False

            print_success(f"Loaded {len(self.rows)} endpoint records")
            return True

        except Exception as e:
            print_error(f"Failed to load CSV: {e}")
            return False

    def analyze(self) -> None:
        """Analyze results."""
        print_header("Performance Analysis")

        for row in self.rows:
            # Skip aggregated rows
            if row.get("Name", "").startswith("Aggregated"):
                continue

            endpoint = row.get("Name", "Unknown")
            try:
                # Parse metrics
                request_count = int(row.get("# requests", "0"))
                failure_count = int(row.get("# failures", "0"))
                p50 = float(row.get("50%", "0"))
                p95 = float(row.get("95%", "0"))
                p99 = float(row.get("99%", "0"))
                avg = float(row.get("Average", "0"))
                min_time = float(row.get("Min", "0"))
                max_time = float(row.get("Max", "0"))

                # Determine budget type
                budget_type = get_budget_type(endpoint)
                budget = PERFORMANCE_BUDGETS[budget_type]

                # Check for violations
                p95_ok = p95 <= budget["p95"]
                p99_ok = p99 <= budget["p99"]

                # Store summary
                self.summary[endpoint] = {
                    "request_count": request_count,
                    "failure_count": failure_count,
                    "failure_rate": (
                        (failure_count / request_count * 100) if request_count > 0 else 0
                    ),
                    "p50": p50,
                    "p95": p95,
                    "p99": p99,
                    "avg": avg,
                    "min": min_time,
                    "max": max_time,
                    "budget_type": budget_type,
                    "budget_p95": budget["p95"],
                    "budget_p99": budget["p99"],
                    "p95_ok": p95_ok,
                    "p99_ok": p99_ok,
                }

                # Record violations
                if not p95_ok or not p99_ok:
                    self.violations.append(
                        {
                            "endpoint": endpoint,
                            "p95": p95,
                            "p95_budget": budget["p95"],
                            "p95_exceeded": p95 > budget["p95"],
                            "p99": p99,
                            "p99_budget": budget["p99"],
                            "p99_exceeded": p99 > budget["p99"],
                        }
                    )

            except ValueError as e:
                print_warning(f"Failed to parse metrics for {endpoint}: {e}")
                continue

    def print_summary(self) -> None:
        """Print summary of results."""
        print_header("Test Results Summary")

        total_endpoints = len(self.summary)
        endpoints_ok = sum(1 for s in self.summary.values() if s["p95_ok"] and s["p99_ok"])
        endpoints_violated = total_endpoints - endpoints_ok

        print(f"Total Endpoints: {total_endpoints}")
        print(f"Endpoints Within Budget: {GREEN}{endpoints_ok}{END}")
        print(f"Endpoints Exceeded Budget: {RED}{endpoints_violated}{END}")
        print(f"Performance Violations: {len(self.violations)}")

        # Overall status
        if self.violations:
            overall_status = f"{RED}FAILED{END}"
        else:
            overall_status = f"{GREEN}PASSED{END}"

        print(f"\nOverall Status: {overall_status}\n")

    def print_endpoint_details(self) -> None:
        """Print detailed metrics for each endpoint."""
        print_header("Endpoint Performance Details")

        # Sort by p95 descending (slowest first)
        sorted_endpoints = sorted(
            self.summary.items(),
            key=lambda x: x[1]["p95"],
            reverse=True,
        )

        for endpoint, metrics in sorted_endpoints:
            print(f"\n{BOLD}{endpoint}{END}")

            # Status
            status = (
                GREEN + "OK" + END
                if (metrics["p95_ok"] and metrics["p99_ok"])
                else RED + "VIOLATED" + END
            )
            print(f"  Status: {status}")

            # Request metrics
            print(f"  Requests: {metrics['request_count']}")
            fail_rate = metrics["failure_rate"]
            fail_count = metrics["failure_count"]
            print(f"  Failure Rate: {fail_rate:.2f}% ({fail_count} failures)")

            # Response time metrics
            print("  Response Times:")
            print_metric("    Min", format_ms(metrics["min"]))
            print_metric("    Avg", format_ms(metrics["avg"]))
            print_metric("    p50", format_ms(metrics["p50"]))
            print_metric("    p95", format_ms(metrics["p95"]), metrics["p95_ok"])
            print_metric("    p99", format_ms(metrics["p99"]), metrics["p99_ok"])
            print_metric("    Max", format_ms(metrics["max"]))

            # Budget comparison
            print(f"  Performance Budget ({metrics['budget_type']}):")
            p95_diff = metrics["p95"] - metrics["budget_p95"]
            p99_diff = metrics["p99"] - metrics["budget_p99"]
            print_metric(
                f"    p95 (budget: {format_ms(metrics['budget_p95'])})",
                format_ms(metrics["p95"]),
                metrics["p95_ok"],
            )
            if not metrics["p95_ok"]:
                print(f"      {RED}Exceeded by {format_ms(p95_diff)}{END}")

            print_metric(
                f"    p99 (budget: {format_ms(metrics['budget_p99'])})",
                format_ms(metrics["p99"]),
                metrics["p99_ok"],
            )
            if not metrics["p99_ok"]:
                print(f"      {RED}Exceeded by {format_ms(p99_diff)}{END}")

    def print_violations(self) -> None:
        """Print performance violations."""
        if not self.violations:
            print_header("Performance Violations")
            print_success("No performance violations detected!")
            return

        print_header("Performance Budget Violations")
        print(f"Total Violations: {len(self.violations)}\n")

        for violation in self.violations:
            print(f"{RED}{violation['endpoint']}{END}")

            if violation["p95_exceeded"]:
                exceeded = violation["p95"] - violation["p95_budget"]
                print(
                    f"  p95: {format_ms(violation['p95'])} "
                    f"(budget: {format_ms(violation['p95_budget'])}) "
                    f"{RED}+{format_ms(exceeded)}{END}"
                )

            if violation["p99_exceeded"]:
                exceeded = violation["p99"] - violation["p99_budget"]
                print(
                    f"  p99: {format_ms(violation['p99'])} "
                    f"(budget: {format_ms(violation['p99_budget'])}) "
                    f"{RED}+{format_ms(exceeded)}{END}"
                )
            print()

    def print_recommendations(self) -> None:
        """Print optimization recommendations."""
        if not self.violations:
            return

        print_header("Optimization Recommendations")

        # Group violations by severity
        critical_violations = [
            v
            for v in self.violations
            if v["p95"] > v["p95_budget"] * 1.5  # More than 50% over budget
        ]

        high_violations = [
            v for v in self.violations if v["p95_budget"] < v["p95"] <= v["p95_budget"] * 1.5
        ]

        if critical_violations:
            print(f"{RED}{BOLD}Critical Violations (>50% over budget):{END}\n")
            for violation in critical_violations:
                print(f"  • {violation['endpoint']}")
                print("    - Investigate database queries for bottlenecks")
                print("    - Check for N+1 query problems")
                print("    - Verify indexing on frequently accessed columns")
                print("    - Consider caching frequently accessed data")
                print()

        if high_violations:
            print(f"{YELLOW}{BOLD}High Violations (10-50% over budget):{END}\n")
            for violation in high_violations:
                print(f"  • {violation['endpoint']}")
                print("    - Profile endpoint for performance hotspots")
                print("    - Review API implementation for optimizations")
                print("    - Consider adding output filtering/pagination")
                print()

    def generate_report(self) -> bool:
        """Generate complete analysis report."""
        if not self.load_results():
            return False

        self.analyze()

        # Print all sections
        self.print_summary()
        self.print_endpoint_details()
        self.print_violations()
        self.print_recommendations()

        # Exit with error if violations found
        if self.violations:
            print(f"\n{RED}{BOLD}Test FAILED - Performance budgets exceeded{END}\n")
            return False
        else:
            print(f"\n{GREEN}{BOLD}Test PASSED - All endpoints within performance budgets{END}\n")
            return True


# ============================================================================
# Main
# ============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze Locust load test results and validate against performance budgets"
    )
    parser.add_argument(
        "results_csv",
        help="Path to Locust results CSV file (e.g., results/baseline_stats.csv)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )

    args = parser.parse_args()

    # Analyze results
    analyzer = LoadTestAnalyzer(Path(args.results_csv))

    if not analyzer.generate_report():
        sys.exit(1)


if __name__ == "__main__":
    main()
