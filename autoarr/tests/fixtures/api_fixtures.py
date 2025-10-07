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


# ============================================================================
# MCP Orchestrator Test Fixtures - Import from separate module
# ============================================================================
# Moved pytest_plugins to tests/conftest.py to comply with deprecation warning


@pytest.fixture
def sabnzbd_error_response_factory() -> callable:
    """
    Factory to create mock SABnzbd error responses.

    Usage:
        error_data = sabnzbd_error_response_factory("Invalid API key")
    """

    def _create_error(
        error_message: str = "Unknown error", error_code: int = 400
    ) -> Dict[str, Any]:
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

    def _create_action(success: bool = True, nzo_ids: List[str] | None = None) -> Dict[str, Any]:
        """Create a mock action response."""
        return {
            "status": success,
            "nzo_ids": nzo_ids or [],
        }

    return _create_action


# ============================================================================
# Sonarr Test Data Factories
# ============================================================================


@pytest.fixture
def sonarr_series_factory() -> callable:
    """
    Factory to create mock Sonarr series (TV show) responses.

    Usage:
        series = sonarr_series_factory(series_id=1, title="Breaking Bad")
        series_list = [sonarr_series_factory(series_id=i) for i in range(5)]
    """

    def _create_series(
        series_id: int = 1,
        title: str = "Test Series",
        tvdb_id: int = 12345,
        imdb_id: str = "tt1234567",
        status: str = "continuing",
        overview: str = "A test TV series",
        network: str = "Test Network",
        air_time: str = "21:00",
        monitored: bool = True,
        quality_profile_id: int = 1,
        season_folder: bool = True,
        path: str = "/tv/Test Series",
        root_folder_path: str = "/tv",
        season_count: int = 3,
        year: int = 2020,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr series response."""
        # Build seasons array
        seasons = []
        for i in range(season_count + 1):  # Include season 0 (specials)
            seasons.append(
                {
                    "seasonNumber": i,
                    "monitored": True if i > 0 else False,
                    "statistics": {
                        "episodeFileCount": 10 if i > 0 else 0,
                        "episodeCount": 10 if i > 0 else 5,
                        "totalEpisodeCount": 10 if i > 0 else 5,
                        "sizeOnDisk": 5000000000 if i > 0 else 0,
                        "percentOfEpisodes": 100.0 if i > 0 else 0.0,
                    },
                }
            )

        series = {
            "id": series_id,
            "title": title,
            "sortTitle": title.lower(),
            "status": status,
            "ended": status == "ended",
            "overview": overview,
            "network": network,
            "airTime": air_time,
            "images": [
                {
                    "coverType": "poster",
                    "url": f"http://test.com/poster/{series_id}.jpg",
                    "remoteUrl": f"http://test.com/poster/{series_id}.jpg",
                },
                {
                    "coverType": "banner",
                    "url": f"http://test.com/banner/{series_id}.jpg",
                    "remoteUrl": f"http://test.com/banner/{series_id}.jpg",
                },
            ],
            "seasons": seasons,
            "year": year,
            "path": path,
            "qualityProfileId": quality_profile_id,
            "seasonFolder": season_folder,
            "monitored": monitored,
            "useSceneNumbering": False,
            "runtime": 45,
            "tvdbId": tvdb_id,
            "tvRageId": 0,
            "tvMazeId": 0,
            "firstAired": f"{year}-01-01T00:00:00Z",
            "seriesType": "standard",
            "cleanTitle": title.lower().replace(" ", ""),
            "imdbId": imdb_id,
            "titleSlug": title.lower().replace(" ", "-"),
            "rootFolderPath": root_folder_path,
            "certification": "TV-14",
            "genres": ["Drama", "Thriller"],
            "tags": [],
            "added": datetime.now().isoformat(),
            "ratings": {"votes": 1000, "value": 8.5},
            "statistics": {
                "seasonCount": season_count,
                "episodeFileCount": season_count * 10,
                "episodeCount": season_count * 10,
                "totalEpisodeCount": season_count * 10,
                "sizeOnDisk": season_count * 5000000000,
                "percentOfEpisodes": 100.0,
            },
        }

        # Allow kwargs to override any values
        series.update(kwargs)
        return series

    return _create_series


@pytest.fixture
def sonarr_episode_factory() -> callable:
    """
    Factory to create mock Sonarr episode responses.

    Usage:
        episode = sonarr_episode_factory(episode_id=1, series_id=1, season_number=1)
    """

    def _create_episode(
        episode_id: int = 1,
        series_id: int = 1,
        season_number: int = 1,
        episode_number: int = 1,
        title: str = "Test Episode",
        air_date: str = "2020-01-01",
        has_file: bool = False,
        monitored: bool = True,
        overview: str = "A test episode",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr episode response."""
        episode = {
            "id": episode_id,
            "seriesId": series_id,
            "tvdbId": episode_id + 100000,
            "episodeFileId": episode_id + 1000 if has_file else 0,
            "seasonNumber": season_number,
            "episodeNumber": episode_number,
            "title": title,
            "airDate": air_date,
            "airDateUtc": f"{air_date}T00:00:00Z",
            "overview": overview,
            "hasFile": has_file,
            "monitored": monitored,
            "absoluteEpisodeNumber": (season_number - 1) * 10 + episode_number,
            "sceneEpisodeNumber": 0,
            "sceneSeasonNumber": 0,
            "unverifiedSceneNumbering": False,
            "grabbed": False,
        }

        # Add episode file if it has one
        if has_file:
            episode["episodeFile"] = {
                "seriesId": series_id,
                "seasonNumber": season_number,
                "relativePath": f"Season {season_number}/Episode {episode_number}.mkv",
                "path": f"/tv/Test Series/Season {season_number}/Episode {episode_number}.mkv",
                "size": 1500000000,
                "dateAdded": datetime.now().isoformat(),
                "quality": {
                    "quality": {
                        "id": 4,
                        "name": "HDTV-720p",
                        "source": "television",
                        "resolution": 720,
                    },
                    "revision": {"version": 1, "real": 0, "isRepack": False},
                },
                "mediaInfo": {
                    "videoCodec": "h264",
                    "videoBitDepth": 8,
                    "videoProfile": "main",
                    "audioFormat": "AAC",
                    "audioChannels": 2.0,
                    "runTime": "00:42:30",
                },
                "qualityCutoffNotMet": False,
                "id": episode_id + 1000,
            }

        # Allow kwargs to override any values
        episode.update(kwargs)
        return episode

    return _create_episode


@pytest.fixture
def sonarr_quality_profile_factory() -> callable:
    """
    Factory to create mock Sonarr quality profile responses.

    Usage:
        profile = sonarr_quality_profile_factory(profile_id=1, name="HD")
    """

    def _create_quality_profile(
        profile_id: int = 1,
        name: str = "HD",
        cutoff: int = 4,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr quality profile response."""
        profile = {
            "id": profile_id,
            "name": name,
            "upgradeAllowed": True,
            "cutoff": cutoff,
            "items": [
                {
                    "quality": {"id": 1, "name": "SDTV", "source": "television", "resolution": 480},
                    "allowed": False,
                },
                {
                    "quality": {
                        "id": 4,
                        "name": "HDTV-720p",
                        "source": "television",
                        "resolution": 720,
                    },
                    "allowed": True,
                },
                {
                    "quality": {
                        "id": 5,
                        "name": "HDTV-1080p",
                        "source": "television",
                        "resolution": 1080,
                    },
                    "allowed": True,
                },
            ],
        }

        # Allow kwargs to override any values
        profile.update(kwargs)
        return profile

    return _create_quality_profile


@pytest.fixture
def sonarr_command_factory() -> callable:
    """
    Factory to create mock Sonarr command responses.

    Usage:
        command = sonarr_command_factory(command_id=1, name="SeriesSearch", status="completed")
    """

    def _create_command(
        command_id: int = 1,
        name: str = "SeriesSearch",
        status: str = "queued",
        queued: str = None,
        started: str = None,
        ended: str = None,
        duration: str = "00:00:00",
        message: str = None,
        body: Dict[str, Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr command response."""
        now = datetime.now().isoformat()

        command = {
            "id": command_id,
            "name": name,
            "commandName": name,
            "message": message or f"{name} command",
            "body": body or {"seriesId": 1},
            "priority": "normal",
            "status": status,
            "queued": queued or now,
            "started": started or (now if status in ["started", "completed", "failed"] else None),
            "ended": ended or (now if status in ["completed", "failed"] else None),
            "duration": duration if status in ["completed", "failed"] else "00:00:00",
            "trigger": "manual",
            "sendUpdatesToClient": True,
            "updateScheduledTask": True,
            "lastExecutionTime": now if status == "completed" else None,
        }

        # Allow kwargs to override any values
        command.update(kwargs)
        return command

    return _create_command


@pytest.fixture
def sonarr_calendar_factory() -> callable:
    """
    Factory to create mock Sonarr calendar responses (upcoming episodes).

    Usage:
        calendar = sonarr_calendar_factory(days=7, episodes_per_day=2)
    """

    def _create_calendar(
        days: int = 7,
        episodes_per_day: int = 2,
        start_date: str = None,
    ) -> List[Dict[str, Any]]:
        """Create a mock Sonarr calendar response."""
        from datetime import datetime, timedelta

        base_date = datetime.fromisoformat(start_date) if start_date else datetime.now()
        calendar = []

        episode_id = 1
        for day in range(days):
            air_date = base_date + timedelta(days=day)
            air_date_str = air_date.strftime("%Y-%m-%d")

            for ep in range(episodes_per_day):
                calendar.append(
                    {
                        "id": episode_id,
                        "seriesId": (episode_id % 5) + 1,
                        "tvdbId": episode_id + 100000,
                        "episodeFileId": 0,
                        "seasonNumber": 1,
                        "episodeNumber": episode_id,
                        "title": f"Episode {episode_id}",
                        "airDate": air_date_str,
                        "airDateUtc": f"{air_date_str}T21:00:00Z",
                        "overview": f"Upcoming episode {episode_id}",
                        "hasFile": False,
                        "monitored": True,
                        "absoluteEpisodeNumber": episode_id,
                        "series": {
                            "title": f"Test Series {(episode_id % 5) + 1}",
                            "status": "continuing",
                            "overview": "Test series",
                            "network": "Test Network",
                            "airTime": "21:00",
                            "images": [],
                            "seasons": [],
                            "year": 2020,
                            "path": f"/tv/Test Series {(episode_id % 5) + 1}",
                            "qualityProfileId": 1,
                            "seasonFolder": True,
                            "monitored": True,
                            "runtime": 45,
                            "tvdbId": 12345 + ((episode_id % 5) + 1),
                            "seriesType": "standard",
                            "cleanTitle": f"testseries{(episode_id % 5) + 1}",
                            "imdbId": f"tt{1234567 + ((episode_id % 5) + 1)}",
                            "titleSlug": f"test-series-{(episode_id % 5) + 1}",
                            "certification": "TV-14",
                            "genres": ["Drama"],
                            "tags": [],
                            "added": datetime.now().isoformat(),
                            "ratings": {"votes": 100, "value": 8.0},
                            "id": (episode_id % 5) + 1,
                        },
                    }
                )
                episode_id += 1

        return calendar

    return _create_calendar


@pytest.fixture
def sonarr_queue_factory() -> callable:
    """
    Factory to create mock Sonarr download queue responses.

    Usage:
        queue = sonarr_queue_factory(records=3)
    """

    def _create_queue(
        records: int = 1,
        page: int = 1,
        page_size: int = 20,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr queue response."""
        queue_records = []

        for i in range(records):
            queue_records.append(
                {
                    "id": i + 1,
                    "seriesId": (i % 5) + 1,
                    "episodeId": (i * 10) + 1,
                    "series": {
                        "title": f"Test Series {(i % 5) + 1}",
                        "tvdbId": 12345 + (i % 5) + 1,
                        "id": (i % 5) + 1,
                    },
                    "episode": {
                        "id": (i * 10) + 1,
                        "seasonNumber": 1,
                        "episodeNumber": i + 1,
                        "title": f"Episode {i + 1}",
                        "seriesId": (i % 5) + 1,
                    },
                    "quality": {
                        "quality": {
                            "id": 4,
                            "name": "HDTV-720p",
                            "source": "television",
                            "resolution": 720,
                        },
                        "revision": {"version": 1, "real": 0, "isRepack": False},
                    },
                    "size": 1500000000,
                    "title": f"Test.Series.S01E{i+1:02d}.720p.HDTV.x264",
                    "sizeleft": 750000000,
                    "timeleft": "00:15:00",
                    "estimatedCompletionTime": datetime.now().isoformat(),
                    "status": "downloading",
                    "trackedDownloadStatus": "ok",
                    "trackedDownloadState": "downloading",
                    "statusMessages": [],
                    "downloadId": f"download_{i+1}",
                    "protocol": "usenet",
                    "downloadClient": "SABnzbd",
                    "indexer": "Test Indexer",
                    "outputPath": f"/tv/Test Series {(i % 5) + 1}",
                }
            )

        queue = {
            "page": page,
            "pageSize": page_size,
            "sortKey": "timeleft",
            "sortDirection": "ascending",
            "totalRecords": len(queue_records),
            "records": queue_records,
        }

        # Allow kwargs to override any values
        queue.update(kwargs)
        return queue

    return _create_queue


@pytest.fixture
def sonarr_wanted_factory() -> callable:
    """
    Factory to create mock Sonarr wanted/missing episodes responses.

    Usage:
        wanted = sonarr_wanted_factory(records=5, page=1)
    """

    def _create_wanted(
        records: int = 1,
        page: int = 1,
        page_size: int = 20,
        include_series: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr wanted/missing response."""
        wanted_records = []

        for i in range(records):
            episode = {
                "id": i + 1,
                "seriesId": (i % 5) + 1,
                "tvdbId": (i + 1) + 100000,
                "episodeFileId": 0,
                "seasonNumber": 1,
                "episodeNumber": i + 1,
                "title": f"Missing Episode {i + 1}",
                "airDate": "2020-01-01",
                "airDateUtc": "2020-01-01T21:00:00Z",
                "overview": f"This episode is missing {i + 1}",
                "hasFile": False,
                "monitored": True,
                "absoluteEpisodeNumber": i + 1,
                "grabbed": False,
            }

            if include_series:
                episode["series"] = {
                    "title": f"Test Series {(i % 5) + 1}",
                    "status": "continuing",
                    "overview": "Test series",
                    "network": "Test Network",
                    "airTime": "21:00",
                    "images": [],
                    "seasons": [],
                    "year": 2020,
                    "path": f"/tv/Test Series {(i % 5) + 1}",
                    "qualityProfileId": 1,
                    "seasonFolder": True,
                    "monitored": True,
                    "runtime": 45,
                    "tvdbId": 12345 + ((i % 5) + 1),
                    "seriesType": "standard",
                    "cleanTitle": f"testseries{(i % 5) + 1}",
                    "imdbId": f"tt{1234567 + ((i % 5) + 1)}",
                    "titleSlug": f"test-series-{(i % 5) + 1}",
                    "certification": "TV-14",
                    "genres": ["Drama"],
                    "tags": [],
                    "added": datetime.now().isoformat(),
                    "ratings": {"votes": 100, "value": 8.0},
                    "id": (i % 5) + 1,
                }

            wanted_records.append(episode)

        wanted = {
            "page": page,
            "pageSize": page_size,
            "sortKey": "airDateUtc",
            "sortDirection": "descending",
            "totalRecords": len(wanted_records),
            "records": wanted_records,
        }

        # Allow kwargs to override any values
        wanted.update(kwargs)
        return wanted

    return _create_wanted


@pytest.fixture
def sonarr_system_status_factory() -> callable:
    """
    Factory to create mock Sonarr system status responses.

    Usage:
        status = sonarr_system_status_factory(version="3.0.10")
    """

    def _create_status(
        version: str = "3.0.10.1567",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a mock Sonarr system status response."""
        status = {
            "version": version,
            "buildTime": "2023-01-01T00:00:00Z",
            "isDebug": False,
            "isProduction": True,
            "isAdmin": True,
            "isUserInteractive": False,
            "startupPath": "/app/sonarr/bin",
            "appData": "/config",
            "osName": "ubuntu",
            "osVersion": "20.04",
            "isMonoRuntime": False,
            "isMono": False,
            "isLinux": True,
            "isOsx": False,
            "isWindows": False,
            "isDocker": True,
            "mode": "console",
            "branch": "main",
            "authentication": "forms",
            "sqliteVersion": "3.36.0",
            "urlBase": "",
            "runtimeVersion": "6.0.10",
            "runtimeName": "dotnet",
        }

        # Allow kwargs to override any values
        status.update(kwargs)
        return status

    return _create_status


# ============================================================================
# Database and Settings Test Fixtures
# ============================================================================


@pytest.fixture
def mock_database_init():
    """
    Mock the database initialization to prevent real database connections in tests.

    This fixture patches the database module's init_database and get_database
    functions to prevent tests from requiring a real database.

    Usage:
        Apply this as autouse fixture in conftest or use explicitly in tests.
    """
    from unittest.mock import MagicMock, AsyncMock, patch
    from contextlib import asynccontextmanager

    mock_db = MagicMock()
    mock_db.database_url = "sqlite+aiosqlite:///:memory:"
    mock_db.init_db = AsyncMock()
    mock_db.close = AsyncMock()

    # Mock session
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.delete = AsyncMock()
    mock_session.refresh = AsyncMock()

    @asynccontextmanager
    async def mock_session_context():
        yield mock_session

    mock_db.session = mock_session_context

    with patch("autoarr.api.database.init_database", return_value=mock_db), patch(
        "autoarr.api.database.get_database", return_value=mock_db
    ):
        yield mock_db


@pytest.fixture
async def mock_database():
    """
    Create a mock database instance for testing.

    Usage:
        async with mock_database.session() as session:
            # Use session in tests
    """
    from unittest.mock import AsyncMock, MagicMock
    from contextlib import asynccontextmanager

    db = MagicMock()
    db.database_url = "sqlite+aiosqlite:///:memory:"

    # Mock session
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.delete = AsyncMock()
    mock_session.refresh = AsyncMock()

    @asynccontextmanager
    async def mock_session_context():
        yield mock_session

    db.session = mock_session_context
    db.init_db = AsyncMock()
    db.close = AsyncMock()

    return db


@pytest.fixture
def mock_settings_repository():
    """
    Create a mock SettingsRepository for testing.

    Usage:
        repo = mock_settings_repository
        settings = await repo.get_service_settings("sabnzbd")
    """
    from unittest.mock import AsyncMock, MagicMock

    repo = MagicMock()
    repo.get_service_settings = AsyncMock(return_value=None)
    repo.get_all_service_settings = AsyncMock(return_value={})
    repo.save_service_settings = AsyncMock()
    repo.delete_service_settings = AsyncMock(return_value=False)

    return repo


@pytest.fixture
def service_settings_factory():
    """
    Factory to create ServiceSettings database model instances.

    Usage:
        settings = service_settings_factory("sabnzbd")
        settings = service_settings_factory("sonarr", enabled=False)
    """

    def _create(
        service_name: str,
        enabled: bool = True,
        url: str = None,
        api_key_or_token: str = None,
        timeout: float = 30.0,
    ):
        """Create a ServiceSettings instance."""
        from unittest.mock import MagicMock

        settings = MagicMock()
        settings.service_name = service_name
        settings.enabled = enabled
        settings.url = url or f"http://localhost:808{hash(service_name) % 10}"
        settings.api_key_or_token = api_key_or_token or f"test_api_key_{service_name}"
        settings.timeout = timeout

        return settings

    return _create


@pytest.fixture
def mock_settings_repository_with_data(service_settings_factory):
    """
    Create a mock SettingsRepository pre-populated with test data.

    Usage:
        repo = mock_settings_repository_with_data
        settings = await repo.get_service_settings("sabnzbd")  # Returns mock data
    """
    from unittest.mock import AsyncMock, MagicMock

    # Create mock service settings for all services
    mock_settings = {
        "sabnzbd": service_settings_factory("sabnzbd"),
        "sonarr": service_settings_factory("sonarr"),
        "radarr": service_settings_factory("radarr"),
        "plex": service_settings_factory("plex"),
    }

    repo = MagicMock()

    # Mock get_service_settings to return specific service
    async def mock_get_service(service_name: str):
        return mock_settings.get(service_name)

    repo.get_service_settings = AsyncMock(side_effect=mock_get_service)
    repo.get_all_service_settings = AsyncMock(return_value=mock_settings)

    # Mock save to update the mock data
    async def mock_save(
        service_name: str, enabled: bool, url: str, api_key_or_token: str, timeout: float
    ):
        saved = service_settings_factory(service_name, enabled, url, api_key_or_token, timeout)
        mock_settings[service_name] = saved
        return saved

    repo.save_service_settings = AsyncMock(side_effect=mock_save)

    # Mock delete to remove from mock data
    async def mock_delete(service_name: str):
        if service_name in mock_settings:
            del mock_settings[service_name]
            return True
        return False

    repo.delete_service_settings = AsyncMock(side_effect=mock_delete)

    return repo
