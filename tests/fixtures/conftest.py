"""
Fixtures for test data factories.

This module provides reusable test data factories for creating
mock SABnzbd API responses and test objects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import pytest


@dataclass
class SABnzbdQueueSlot:
    """Represents a single download slot in SABnzbd queue."""

    nzo_id: str
    filename: str
    status: str
    mb_left: float
    mb_total: float
    percentage: int
    category: str
    priority: str
    eta: str


@dataclass
class SABnzbdHistorySlot:
    """Represents a single entry in SABnzbd history."""

    nzo_id: str
    name: str
    status: str
    fail_message: str
    category: str
    size: str
    download_time: int
    completed: int


@pytest.fixture
def sabnzbd_queue_factory() -> callable:
    """
    Factory to create mock SABnzbd queue responses.

    Usage:
        queue_data = sabnzbd_queue_factory(slots=2, paused=False)
    """

    def _create_queue(
        slots: int = 1,
        paused: bool = False,
        speed: str = "5.2 MB/s",
        mb_left: float = 1250.5,
        mb_total: float = 2500.0,
    ) -> Dict[str, Any]:
        """Create a mock queue response with specified parameters."""
        queue_slots = []
        for i in range(slots):
            queue_slots.append(
                {
                    "nzo_id": f"SABnzbd_nzo_{i}",
                    "filename": f"Test.Download.S01E{i:02d}.mkv",
                    "status": "Downloading" if not paused else "Paused",
                    "mb_left": mb_left / slots,
                    "mb": mb_total / slots,
                    "percentage": 50,
                    "category": "tv" if i % 2 == 0 else "movies",
                    "priority": "Normal",
                    "eta": "00:04:30",
                    "timeleft": "0:04:30",
                }
            )

        return {
            "queue": {
                "status": "Paused" if paused else "Downloading",
                "speed": speed,
                "speedlimit": "",
                "speedlimit_abs": "",
                "mb": mb_total,
                "mbleft": mb_left,
                "slots": queue_slots,
                "size": f"{mb_total / 1024:.2f} GB",
                "sizeleft": f"{mb_left / 1024:.2f} GB",
                "noofslots": len(queue_slots),
                "pause_int": "0" if not paused else "1",
                "paused": paused,
            }
        }

    return _create_queue


@pytest.fixture
def sabnzbd_history_factory() -> callable:
    """
    Factory to create mock SABnzbd history responses.

    Usage:
        history_data = sabnzbd_history_factory(entries=5, failed=2)
    """

    def _create_history(
        entries: int = 1, failed: int = 0, start: int = 0, limit: int = 10
    ) -> Dict[str, Any]:
        """Create a mock history response with specified parameters."""
        history_slots = []

        # Create failed entries first
        for i in range(failed):
            history_slots.append(
                {
                    "nzo_id": f"SABnzbd_nzo_failed_{i}",
                    "name": f"Failed.Download.S01E{i:02d}",
                    "status": "Failed",
                    "fail_message": "Unpacking failed, write error or disk is full?",
                    "category": "tv",
                    "size": "1.2 GB",
                    "download_time": 300,
                    "completed": int(datetime.now().timestamp()) - (i * 3600),
                    "storage": "",
                    "action_line": "",
                    "retry": 0,
                }
            )

        # Create successful entries
        for i in range(entries - failed):
            history_slots.append(
                {
                    "nzo_id": f"SABnzbd_nzo_success_{i}",
                    "name": f"Successful.Download.S01E{i + failed:02d}",
                    "status": "Completed",
                    "fail_message": "",
                    "category": "movies" if i % 2 == 0 else "tv",
                    "size": "2.5 GB",
                    "download_time": 450,
                    "completed": int(datetime.now().timestamp()) - (i * 1800),
                    "storage": "/downloads/complete/",
                    "action_line": "",
                    "retry": 0,
                }
            )

        return {
            "history": {
                "total_size": f"{entries * 2.5:.1f} GB",
                "month_size": "150 GB",
                "week_size": "45 GB",
                "noofslots": len(history_slots),
                "slots": history_slots[start : start + limit],
                "day_size": "12 GB",
            }
        }

    return _create_history


@pytest.fixture
def sabnzbd_config_factory() -> callable:
    """
    Factory to create mock SABnzbd configuration responses.

    Usage:
        config_data = sabnzbd_config_factory(complete_dir="/downloads/complete")
    """

    def _create_config(
        complete_dir: str = "/downloads/complete",
        download_dir: str = "/downloads/incomplete",
        enable_https: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock configuration response."""
        config = {
            "config": {
                "misc": {
                    "complete_dir": complete_dir,
                    "download_dir": download_dir,
                    "enable_https": enable_https,
                    "host": "0.0.0.0",
                    "port": 8080,
                    "https_port": 9090,
                    "username": "",
                    "password": "",
                    "api_key": "test_api_key",
                    "nzb_backup_dir": "",
                    "auto_browser": 0,
                    "refresh_rate": 1,
                    "cache_limit": "500M",
                    "auto_disconnect": 1,
                    "par_option": "Extra PAR2",
                    "pre_check": 1,
                    "nice": "",
                    "ionice": "",
                    "cleanup_list": [".nzb", ".par2", ".sfv"],
                },
                "servers": [],
                "categories": {
                    "tv": {
                        "name": "tv",
                        "order": 0,
                        "pp": 3,
                        "script": "Default",
                        "dir": "tv",
                        "newzbin": "",
                        "priority": 0,
                    },
                    "movies": {
                        "name": "movies",
                        "order": 1,
                        "pp": 3,
                        "script": "Default",
                        "dir": "movies",
                        "newzbin": "",
                        "priority": -100,
                    },
                },
            }
        }

        # Allow kwargs to override any nested config values
        for key, value in kwargs.items():
            if "." in key:
                # Support nested keys like "misc.cache_limit"
                parts = key.split(".")
                target = config["config"]
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = value

        return config

    return _create_config


@pytest.fixture
def sabnzbd_status_factory() -> callable:
    """
    Factory to create mock SABnzbd status/version responses.

    Usage:
        status_data = sabnzbd_status_factory(version="4.1.0")
    """

    def _create_status(version: str = "4.1.0", uptime: str = "2d 5h 30m") -> Dict[str, Any]:
        """Create a mock status response."""
        return {
            "status": {
                "version": version,
                "uptime": uptime,
                "color": "green",
                "pp": "Running",
                "loadavg": "0.5 0.4 0.3",
                "speedlimit": 100,
                "speedlimit_abs": "",
                "have_warnings": "0",
                "finishaction": None,
                "quota": "unlimited",
                "diskspacetotal1": "500.00",
                "diskspace1": "250.00",
                "diskspacetotal2": "500.00",
                "diskspace2": "250.00",
                "localipv4": "192.168.1.100",
                "publicipv4": "1.2.3.4",
            }
        }

    return _create_status


@pytest.fixture
def sabnzbd_error_response_factory() -> callable:
    """
    Factory to create mock SABnzbd error responses.

    Usage:
        error_data = sabnzbd_error_response_factory("Invalid API key")
    """

    def _create_error(error_message: str = "Unknown error", error_code: int = 400) -> Dict[str, Any]:
        """Create a mock error response."""
        return {"status": False, "error": error_message, "error_code": error_code}

    return _create_error


@pytest.fixture
def sabnzbd_nzo_action_factory() -> callable:
    """
    Factory to create mock SABnzbd NZO action responses (pause, resume, delete, retry).

    Usage:
        action_data = sabnzbd_nzo_action_factory(success=True)
    """

    def _create_action(
        success: bool = True, nzo_ids: List[str] | None = None
    ) -> Dict[str, Any]:
        """Create a mock action response."""
        return {
            "status": success,
            "nzo_ids": nzo_ids or [],
        }

    return _create_action
