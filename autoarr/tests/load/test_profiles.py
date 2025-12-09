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
Load test profiles for different testing scenarios.

This module defines different user load profiles that simulate various real-world
scenarios. These can be used to test system behavior under different conditions.

Profiles:
1. BaselineProfile - Minimal load to measure baseline performance
2. NormalLoadProfile - Typical production load
3. PeakLoadProfile - Expected peak usage
4. StressTestProfile - Push system to failure point
5. SpikeTestProfile - Sudden traffic spike
6. DayInTheLifeProfile - Full day simulation
7. WebSocketProfile - WebSocket connection testing
"""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Profile Configuration Data Structures
# ============================================================================


class LoadProfile:
    """Base class for load test profiles."""

    name: str
    description: str
    duration_seconds: int
    user_classes: Dict[str, int]  # {class_name: spawn_rate}
    ramp_up_seconds: int
    ramp_down_seconds: int
    max_users: int

    def __init__(
        self,
        name: str,
        description: str,
        duration_seconds: int,
        user_classes: Dict[str, int],
        ramp_up_seconds: int = 0,
        ramp_down_seconds: int = 0,
    ) -> None:
        """Initialize load profile."""
        self.name = name
        self.description = description
        self.duration_seconds = duration_seconds
        self.user_classes = user_classes
        self.ramp_up_seconds = ramp_up_seconds
        self.ramp_down_seconds = ramp_down_seconds
        self.max_users = sum(user_classes.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "duration_seconds": self.duration_seconds,
            "user_classes": self.user_classes,
            "ramp_up_seconds": self.ramp_up_seconds,
            "ramp_down_seconds": self.ramp_down_seconds,
            "max_users": self.max_users,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LoadProfile({self.name}, max_users={self.max_users}, "
            f"duration={self.duration_seconds}s)"
        )


# ============================================================================
# Profile Definitions
# ============================================================================


# 1. Baseline Profile - Minimal load to establish baseline metrics
BASELINE_PROFILE = LoadProfile(
    name="Baseline",
    description="Minimal load for baseline performance measurement. Single user per class.",
    duration_seconds=300,  # 5 minutes
    user_classes={
        "HealthCheckUser": 1,
        "MonitoringUser": 1,
        "BrowsingUser": 1,
    },
    ramp_up_seconds=30,
    ramp_down_seconds=30,
)

# 2. Normal Load Profile - Typical production-like load
NORMAL_LOAD_PROFILE = LoadProfile(
    name="Normal Load",
    description="Typical production load with expected user distribution.",
    duration_seconds=600,  # 10 minutes
    user_classes={
        "HealthCheckUser": 15,  # Most health checks from monitoring
        "MonitoringUser": 10,   # Active dashboard users
        "BrowsingUser": 8,      # Users browsing content
        "ConfigurationAuditUser": 3,  # Occasional config checks
        "ContentRequestUser": 2,  # Content requests
        "AdminUser": 2,         # Admin operations
    },
    ramp_up_seconds=60,
    ramp_down_seconds=30,
)

# 3. Peak Load Profile - Expected peak usage conditions
PEAK_LOAD_PROFILE = LoadProfile(
    name="Peak Load",
    description="Peak usage scenario - expected maximum production load.",
    duration_seconds=900,  # 15 minutes
    user_classes={
        "HealthCheckUser": 40,   # Heavy health check traffic
        "MonitoringUser": 25,    # Multiple dashboard users
        "BrowsingUser": 20,      # Heavy browsing
        "ConfigurationAuditUser": 8,  # More config operations
        "ContentRequestUser": 5,  # Multiple requests
        "AdminUser": 2,          # Admin operations
    },
    ramp_up_seconds=120,
    ramp_down_seconds=60,
)

# 4. Stress Test Profile - Push system towards failure
STRESS_TEST_PROFILE = LoadProfile(
    name="Stress Test",
    description="Stress testing to find system breaking point.",
    duration_seconds=1200,  # 20 minutes
    user_classes={
        "HealthCheckUser": 100,  # Heavy health checks
        "MonitoringUser": 50,    # Heavy monitoring
        "BrowsingUser": 40,      # Heavy browsing
        "ConfigurationAuditUser": 20,  # Heavy config operations
        "ContentRequestUser": 10,  # Heavy content requests
        "AdminUser": 5,          # Admin operations
    },
    ramp_up_seconds=300,
    ramp_down_seconds=120,
)

# 5. Spike Test Profile - Sudden traffic increase
SPIKE_TEST_PROFILE = LoadProfile(
    name="Spike Test",
    description="Sudden traffic spike to test system resilience.",
    duration_seconds=600,  # 10 minutes
    user_classes={
        "HealthCheckUser": 80,   # Sudden spike in health checks
        "MonitoringUser": 40,    # Sudden spike in monitoring
        "BrowsingUser": 30,      # Sudden spike in browsing
        "ConfigurationAuditUser": 15,
        "ContentRequestUser": 8,
        "AdminUser": 2,
    },
    ramp_up_seconds=30,  # Very quick ramp-up (30 seconds)
    ramp_down_seconds=60,
)

# 6. Day in the Life Profile - Simulate typical day patterns
DAY_IN_THE_LIFE_PROFILE = LoadProfile(
    name="Day in the Life",
    description="Simulate typical usage patterns across a full day (3600 seconds).",
    duration_seconds=3600,  # 1 hour simulation
    user_classes={
        "HealthCheckUser": 20,
        "MonitoringUser": 12,
        "BrowsingUser": 10,
        "ConfigurationAuditUser": 4,
        "ContentRequestUser": 3,
        "AdminUser": 1,
    },
    ramp_up_seconds=60,
    ramp_down_seconds=120,
)

# 7. WebSocket Profile - Test WebSocket connections
WEBSOCKET_PROFILE = LoadProfile(
    name="WebSocket",
    description="WebSocket connection stress testing.",
    duration_seconds=600,  # 10 minutes
    user_classes={
        "HealthCheckUser": 5,
        "MonitoringUser": 50,  # Heavy WebSocket usage
        "BrowsingUser": 30,
    },
    ramp_up_seconds=60,
    ramp_down_seconds=60,
)

# ============================================================================
# Profile Registry
# ============================================================================

PROFILES: Dict[str, LoadProfile] = {
    "baseline": BASELINE_PROFILE,
    "normal": NORMAL_LOAD_PROFILE,
    "peak": PEAK_LOAD_PROFILE,
    "stress": STRESS_TEST_PROFILE,
    "spike": SPIKE_TEST_PROFILE,
    "day": DAY_IN_THE_LIFE_PROFILE,
    "websocket": WEBSOCKET_PROFILE,
}


# ============================================================================
# Scenario Helper Functions
# ============================================================================


def get_profile(profile_name: str) -> LoadProfile:
    """Get a load profile by name."""
    profile_name_lower = profile_name.lower()
    if profile_name_lower not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise ValueError(
            f"Unknown profile '{profile_name}'. Available profiles: {available}"
        )
    return PROFILES[profile_name_lower]


def list_profiles() -> List[str]:
    """List all available profiles."""
    return list(PROFILES.keys())


def print_profiles() -> None:
    """Print all profiles with their details."""
    print("\nAvailable Load Test Profiles:\n")
    print("=" * 80)
    for name, profile in PROFILES.items():
        print(f"\n{name.upper()} Profile:")
        print(f"  Description: {profile.description}")
        print(f"  Max Concurrent Users: {profile.max_users}")
        print(f"  Duration: {profile.duration_seconds} seconds")
        print(f"  Ramp-up: {profile.ramp_up_seconds}s, Ramp-down: {profile.ramp_down_seconds}s")
        print(f"  User Distribution:")
        for user_class, count in profile.user_classes.items():
            print(f"    - {user_class}: {count} users")
    print("\n" + "=" * 80)


# ============================================================================
# Custom Run Configuration Generator
# ============================================================================


def generate_locust_config(profile_name: str) -> Dict[str, Any]:
    """
    Generate Locust configuration from a profile.

    Args:
        profile_name: Name of the profile to use

    Returns:
        Dictionary with Locust configuration parameters
    """
    profile = get_profile(profile_name)

    return {
        "users": profile.max_users,
        "spawn_rate": max(1, profile.max_users // max(1, profile.ramp_up_seconds)),
        "run_time": f"{profile.duration_seconds}s",
        "headless": True,
        "stop_timeout": profile.ramp_down_seconds,
        "profile": profile_name,
    }


if __name__ == "__main__":
    """Print available profiles when run as a script."""
    print_profiles()

    # Example: Generate config for a specific profile
    print("\nExample Locust Config for 'normal' profile:")
    print(generate_locust_config("normal"))
