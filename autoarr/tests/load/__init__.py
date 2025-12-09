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
AutoArr API Load Testing Suite.

This package contains comprehensive load tests for validating AutoArr API
performance under various load conditions.

Modules:
- locustfile: Main load test scenarios with multiple user types
- test_profiles: Pre-configured load test profiles
- websocket_load_test: WebSocket connection stress testing
- conftest: Shared configuration and utilities

Usage:
    # Run with web UI
    locust -f locustfile.py --host=http://localhost:8088

    # Run headless with specific profile
    locust -f locustfile.py --host=http://localhost:8088 --users=100 --run-time=10m --headless

    # Use convenience shell script
    ./run_load_tests.sh baseline
    ./run_load_tests.sh all
"""
