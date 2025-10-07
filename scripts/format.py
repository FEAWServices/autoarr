#!/usr/bin/env python3
"""Auto-format code to match project standards."""

import subprocess
import sys


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    NC = "\033[0m"  # No Color


def print_status(message: str) -> None:
    """Print a status message in blue."""
    print(f"{Colors.BLUE}==>{Colors.NC} {message}")


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def main() -> int:
    """Run code formatters."""
    print()
    print_status("Formatting Python code with Black...")
    try:
        subprocess.run(["poetry", "run", "black", "."], check=True)
        print_success("Python code formatted")
    except subprocess.CalledProcessError:
        return 1

    print()
    print_success("All formatting complete! ✨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
