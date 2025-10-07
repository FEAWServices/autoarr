#!/usr/bin/env python3
"""Test harness that runs the same checks as CI pipeline.

This ensures local testing matches CI exactly (DRY principle).
"""

import subprocess
import sys
from typing import List


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_status(message: str) -> None:
    """Print a status message in blue."""
    print(f"{Colors.BLUE}==>{Colors.NC} {message}")


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


def run_check(name: str, command: List[str], allow_failure: bool = False) -> bool:
    """Run a check command and report results.

    Args:
        name: Name of the check
        command: Command to run as list of strings
        allow_failure: If True, don't count failures toward overall status

    Returns:
        True if check passed, False otherwise
    """
    print_status(f"Running {name}...")

    try:
        subprocess.run(command, check=True, capture_output=False)
        print_success(f"{name} passed")
        return True
    except subprocess.CalledProcessError:
        if allow_failure:
            print_warning(f"{name} found issues (non-blocking)")
            return True
        else:
            print_error(f"{name} failed")
            return False


def main() -> int:
    """Run all test checks."""
    print()
    print_status("Starting AutoArr Test Harness")
    print()

    failed = False

    # Run Black (code formatting check)
    if not run_check("Black (code formatting)", ["poetry", "run", "black", "--check", "."]):
        failed = True

    # Run Flake8 (linting)
    if not run_check(
        "Flake8 (linting)",
        [
            "poetry",
            "run",
            "flake8",
            "api/",
            "mcp-servers/mcp_servers/",
            "shared/",
            "tests/",
            "--max-line-length=100",
            "--extend-ignore=E203",
        ],
    ):
        failed = True

    # Run MyPy (type checking) - non-blocking like CI
    run_check(
        "MyPy (type checking)",
        [
            "poetry",
            "run",
            "mypy",
            "api/",
            "mcp-servers/mcp_servers/",
            "shared/",
            "--config-file=pyproject.toml",
        ],
        allow_failure=True,
    )

    # Run pytest (unit tests with coverage)
    if not run_check(
        "Pytest (unit tests)",
        [
            "poetry",
            "run",
            "pytest",
            "tests/",
            "-v",
            "--cov=api",
            "--cov=mcp_servers",
            "--cov=shared",
            "--cov-report=xml",
            "--cov-report=term-missing",
        ],
    ):
        failed = True

    print()
    if not failed:
        print_success("All tests passed! ✨")
        return 0
    else:
        print_error("Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
