"""
Contract test configuration and fixtures.

This module provides shared fixtures for contract and path-based testing.
"""

import pytest


@pytest.fixture
def sample_sabnzbd_queue():
    """Sample SABnzbd queue response for testing."""
    return {
        "queue": {
            "slots": [
                {
                    "nzo_id": "SABnzbd_nzo_test123",
                    "filename": "Test.Show.S01E01.720p.WEB-DL",
                    "status": "Downloading",
                    "percentage": "45",
                    "timeleft": "0:15:30",
                    "mb": "1500.00",
                    "mbleft": "825.00",
                }
            ],
            "status": "Downloading",
            "speed": "5.2 M",
            "paused": False,
        }
    }


@pytest.fixture
def sample_sabnzbd_history():
    """Sample SABnzbd history response for testing."""
    return {
        "history": {
            "slots": [
                {
                    "nzo_id": "SABnzbd_nzo_completed",
                    "name": "Completed.Show.S01E02",
                    "status": "Completed",
                    "fail_message": "",
                    "completed": 1699999999,
                },
                {
                    "nzo_id": "SABnzbd_nzo_failed",
                    "name": "Failed.Download",
                    "status": "Failed",
                    "fail_message": "Repair failed, not enough blocks",
                    "completed": 1699999998,
                },
            ]
        }
    }


@pytest.fixture
def sample_sonarr_series():
    """Sample Sonarr series response for testing."""
    return [
        {
            "id": 1,
            "title": "Breaking Bad",
            "tvdbId": 81189,
            "year": 2008,
            "overview": "A chemistry teacher diagnosed with cancer...",
            "path": "/tv/Breaking Bad",
            "qualityProfileId": 1,
            "monitored": True,
            "seasonFolder": True,
        },
        {
            "id": 2,
            "title": "Game of Thrones",
            "tvdbId": 121361,
            "year": 2011,
            "overview": "Noble families vie for control...",
            "path": "/tv/Game of Thrones",
            "qualityProfileId": 1,
            "monitored": True,
            "seasonFolder": True,
        },
    ]


@pytest.fixture
def sample_radarr_movies():
    """Sample Radarr movies response for testing."""
    return [
        {
            "id": 1,
            "title": "The Matrix",
            "tmdbId": 603,
            "year": 1999,
            "overview": "A computer programmer discovers...",
            "path": "/movies/The Matrix (1999)",
            "qualityProfileId": 1,
            "monitored": True,
            "hasFile": True,
        },
        {
            "id": 2,
            "title": "Inception",
            "tmdbId": 27205,
            "year": 2010,
            "overview": "A thief who steals secrets...",
            "path": "/movies/Inception (2010)",
            "qualityProfileId": 1,
            "monitored": True,
            "hasFile": False,
        },
    ]


@pytest.fixture
def sample_audit_findings():
    """Sample configuration audit findings for testing."""
    return [
        {
            "setting": "cache_limit",
            "current": "512M",
            "recommended": "1G",
            "severity": "medium",
            "explanation": "Increasing cache improves performance for large downloads",
        },
        {
            "setting": "bandwidth_max",
            "current": "0",
            "recommended": "0",
            "severity": "low",
            "explanation": "Unlimited bandwidth is optimal for most setups",
        },
    ]


@pytest.fixture
def sample_correlation_id():
    """Sample correlation ID for event tracking tests."""
    return "corr_test_abc123"


@pytest.fixture
def sample_activity_chain(sample_correlation_id):
    """Sample activity event chain for testing."""
    return [
        {
            "id": f"act_1_{sample_correlation_id}",
            "action": "download_started",
            "timestamp": "2024-01-15T10:00:00Z",
            "correlation_id": sample_correlation_id,
            "details": {"nzo_id": "SABnzbd_nzo_123"},
            "source": "sabnzbd",
        },
        {
            "id": f"act_2_{sample_correlation_id}",
            "action": "download_progress",
            "timestamp": "2024-01-15T10:15:00Z",
            "correlation_id": sample_correlation_id,
            "details": {"nzo_id": "SABnzbd_nzo_123", "progress": 50},
            "source": "sabnzbd",
        },
        {
            "id": f"act_3_{sample_correlation_id}",
            "action": "download_completed",
            "timestamp": "2024-01-15T10:30:00Z",
            "correlation_id": sample_correlation_id,
            "details": {"nzo_id": "SABnzbd_nzo_123"},
            "source": "sabnzbd",
        },
    ]
