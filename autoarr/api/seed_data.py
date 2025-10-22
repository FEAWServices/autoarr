"""
Seed data for best practices database.

This module contains initial best practices for SABnzbd, Sonarr, Radarr, and Plex.
Best practices are based on official documentation, community recommendations,
and common configuration issues.
"""

import json
from typing import Any


def get_best_practices_seed_data() -> list[dict[str, Any]]:
    """
    Get seed data for best practices.

    Returns:
        List of best practice dictionaries ready for database insertion
    """
    return [
        # ====================================================================
        # SABnzbd Best Practices (5 practices)
        # ====================================================================
        {
            "application": "sabnzbd",
            "category": "downloads",
            "setting_name": "incomplete_dir",
            "setting_path": "misc.incomplete_dir",
            "recommended_value": json.dumps(
                {
                    "type": "not_empty",
                    "description": "Separate directory for incomplete downloads",
                    "example": "/downloads/incomplete",
                }
            ),
            "current_check_type": "not_empty",
            "explanation": (
                "Using a separate incomplete directory prevents partially "
                "downloaded files from being processed by post-processing "
                "scripts and keeps your completed downloads directory clean. "
                "This avoids automation tools from trying to process "
                "incomplete files."
            ),
            "priority": "high",
            "impact": (
                "Incomplete downloads may be processed by automation tools, "
                "causing errors, corrupted media files, and wasted bandwidth "
                "on reprocessing."
            ),
            "documentation_url": "https://sabnzbd.org/wiki/configuration/2.3/folders",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sabnzbd",
            "category": "performance",
            "setting_name": "article_cache",
            "setting_path": "misc.article_cache_max",
            "recommended_value": json.dumps(
                {
                    "type": "greater_than",
                    "value": 500,
                    "description": "Cache size in MB (recommended 500-1000MB)",
                    "min": 500,
                    "max": 2000,
                }
            ),
            "current_check_type": "greater_than",
            "explanation": (
                "Increasing the article cache improves download performance "
                "by reducing disk I/O operations. SABnzbd can keep more data "
                "in memory before writing to disk, especially beneficial for "
                "fast internet connections."
            ),
            "priority": "medium",
            "impact": (
                "Lower cache values result in more frequent disk writes, "
                "reducing download speed and increasing disk wear on SSDs."
            ),
            "documentation_url": (
                "https://sabnzbd.org/wiki/configuration/2.3/general#article_cache_max"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sabnzbd",
            "category": "security",
            "setting_name": "enable_https",
            "setting_path": "misc.enable_https",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": True,
                    "description": "Enable HTTPS for web interface",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Enabling HTTPS encrypts communication with the web "
                "interface, protecting your API key and credentials from "
                "being intercepted, especially important if accessing "
                "SABnzbd remotely."
            ),
            "priority": "critical",
            "impact": (
                "Without HTTPS, API keys and credentials are transmitted in "
                "plain text, allowing potential interception by malicious "
                "actors on the network."
            ),
            "documentation_url": "https://sabnzbd.org/wiki/configuration/2.3/general#https",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sabnzbd",
            "category": "post_processing",
            "setting_name": "par2_multicore",
            "setting_path": "misc.par2_multicore",
            "recommended_value": json.dumps(
                {"type": "boolean", "value": True, "description": "Enable multi-core PAR2 repair"}
            ),
            "current_check_type": "equals",
            "explanation": (
                "Multi-core PAR2 processing dramatically reduces repair times "
                "by using all available CPU cores. This is especially "
                "important for large downloads that require verification and "
                "repair."
            ),
            "priority": "high",
            "impact": (
                "Single-core PAR2 processing can take significantly longer "
                "(2-10x), creating bottlenecks in your download pipeline."
            ),
            "documentation_url": (
                "https://sabnzbd.org/wiki/configuration/2.3/switches#par2_multicore"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sabnzbd",
            "category": "downloads",
            "setting_name": "download_dir",
            "setting_path": "misc.download_dir",
            "recommended_value": json.dumps(
                {
                    "type": "not_equals",
                    "value": "/downloads",
                    "description": "Should not be same as incomplete directory",
                }
            ),
            "current_check_type": "not_equals",
            "explanation": (
                "The download directory (completed) should be different from "
                "the incomplete directory to prevent processing scripts from "
                "accessing incomplete files and to maintain clear "
                "organization."
            ),
            "priority": "high",
            "impact": (
                "Using the same directory can cause automation tools to "
                "process incomplete downloads, resulting in failed imports "
                "and corrupted files."
            ),
            "documentation_url": "https://sabnzbd.org/wiki/configuration/2.3/folders",
            "version_added": "1.0.0",
            "enabled": True,
        },
        # ====================================================================
        # Sonarr Best Practices (6 practices)
        # ====================================================================
        {
            "application": "sonarr",
            "category": "media_management",
            "setting_name": "rename_episodes",
            "setting_path": "settings.mediaManagement.renameEpisodes",
            "recommended_value": json.dumps(
                {"type": "boolean", "value": True, "description": "Enable episode renaming"}
            ),
            "current_check_type": "equals",
            "explanation": (
                "Enabling episode renaming ensures consistent file naming "
                "across your library, making it easier for media players like "
                "Plex to identify and match episodes correctly. It also helps "
                "with library organization and searching."
            ),
            "priority": "high",
            "impact": (
                "Without renaming, episodes may have inconsistent names from "
                "different sources, causing metadata matching issues in media "
                "servers and making manual searching difficult."
            ),
            "documentation_url": "https://wiki.servarr.com/sonarr/settings#media-management",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sonarr",
            "category": "media_management",
            "setting_name": "auto_unmonitor_previously_downloaded",
            "setting_path": "settings.mediaManagement.autoUnmonitorPreviouslyDownloadedEpisodes",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": True,
                    "description": "Automatically unmonitor previously downloaded episodes",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Automatically unmonitoring previously downloaded episodes "
                "prevents Sonarr from re-downloading episodes when switching "
                "quality profiles or re-syncing, saving bandwidth and "
                "avoiding duplicate files."
            ),
            "priority": "medium",
            "impact": (
                "May result in duplicate downloads and wasted bandwidth when "
                "upgrading quality profiles or performing full library "
                "rescans."
            ),
            "documentation_url": "https://wiki.servarr.com/sonarr/settings#media-management",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sonarr",
            "category": "quality",
            "setting_name": "quality_cutof",
            "setting_path": "settings.profiles.quality_cutof",
            "recommended_value": json.dumps(
                {
                    "type": "exists",
                    "description": "Quality cutoff should be defined to prevent endless upgrades",
                }
            ),
            "current_check_type": "exists",
            "explanation": (
                "Setting a quality cutoff prevents Sonarr from continuously "
                "searching for better quality versions, which wastes "
                "bandwidth and disk space. Once the cutoff quality is "
                "reached, Sonarr stops searching for upgrades."
            ),
            "priority": "medium",
            "impact": (
                "Without a cutoff, Sonarr may continuously upgrade files, "
                "wasting bandwidth and disk I/O on marginal quality "
                "improvements."
            ),
            "documentation_url": "https://wiki.servarr.com/sonarr/settings#quality-profiles",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sonarr",
            "category": "indexers",
            "setting_name": "multiple_indexers",
            "setting_path": "settings.indexers.count",
            "recommended_value": json.dumps(
                {
                    "type": "greater_than",
                    "value": 1,
                    "description": "Configure multiple indexers for redundancy",
                    "min": 2,
                }
            ),
            "current_check_type": "greater_than",
            "explanation": (
                "Using multiple indexers provides redundancy and increases "
                "the chances of finding releases. If one indexer is down or "
                "doesn't have a particular release, others can fill the gap."
            ),
            "priority": "high",
            "impact": (
                "Single indexer configurations create a single point of "
                "failure, risking missed episodes when the indexer is "
                "unavailable or lacking content."
            ),
            "documentation_url": "https://wiki.servarr.com/sonarr/settings#indexers",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sonarr",
            "category": "media_management",
            "setting_name": "create_empty_folders",
            "setting_path": "settings.mediaManagement.createEmptySeriesFolders",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": False,
                    "description": "Disable creating empty series folders",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Disabling empty folder creation prevents clutter in your "
                "media library from shows that haven't had any episodes "
                "downloaded yet. Folders are created only when actual content "
                "is added."
            ),
            "priority": "low",
            "impact": (
                "Empty folders clutter your media library and can confuse "
                "media servers about available content."
            ),
            "documentation_url": "https://wiki.servarr.com/sonarr/settings#media-management",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "sonarr",
            "category": "download_clients",
            "setting_name": "completed_download_handling",
            "setting_path": "settings.downloadClient.enableCompletedDownloadHandling",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": True,
                    "description": "Enable completed download handling",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Completed download handling allows Sonarr to automatically "
                "import and process downloads, moving them to your media "
                "library and triggering renaming/organizing actions."
            ),
            "priority": "critical",
            "impact": (
                "Without this, downloads must be manually imported, defeating "
                "the purpose of automation and potentially leaving files in "
                "the download directory."
            ),
            "documentation_url": (
                "https://wiki.servarr.com/sonarr/settings#completed-download-handling"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        # ====================================================================
        # Radarr Best Practices (5 practices)
        # ====================================================================
        {
            "application": "radarr",
            "category": "media_management",
            "setting_name": "rename_movies",
            "setting_path": "settings.mediaManagement.renameMovies",
            "recommended_value": json.dumps(
                {"type": "boolean", "value": True, "description": "Enable movie renaming"}
            ),
            "current_check_type": "equals",
            "explanation": (
                "Enabling movie renaming ensures consistent file naming "
                "across your library, making it easier for media players to "
                "identify and match movies correctly with metadata providers."
            ),
            "priority": "high",
            "impact": (
                "Without renaming, movies may have inconsistent names from "
                "different sources, causing metadata matching issues in media "
                "servers."
            ),
            "documentation_url": "https://wiki.servarr.com/radarr/settings#media-management",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "radarr",
            "category": "quality",
            "setting_name": "quality_cutof",
            "setting_path": "settings.profiles.quality_cutof",
            "recommended_value": json.dumps(
                {
                    "type": "exists",
                    "description": "Quality cutoff should be defined to prevent endless upgrades",
                }
            ),
            "current_check_type": "exists",
            "explanation": (
                "Setting a quality cutoff prevents Radarr from continuously "
                "searching for better quality versions, which wastes "
                "bandwidth and disk space. Once the cutoff quality is "
                "reached, Radarr stops searching for upgrades."
            ),
            "priority": "medium",
            "impact": (
                "Without a cutoff, Radarr may continuously upgrade files, "
                "wasting bandwidth and disk space on marginal quality "
                "improvements."
            ),
            "documentation_url": "https://wiki.servarr.com/radarr/settings#quality-profiles",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "radarr",
            "category": "indexers",
            "setting_name": "multiple_indexers",
            "setting_path": "settings.indexers.count",
            "recommended_value": json.dumps(
                {
                    "type": "greater_than",
                    "value": 1,
                    "description": "Configure multiple indexers for redundancy",
                    "min": 2,
                }
            ),
            "current_check_type": "greater_than",
            "explanation": (
                "Using multiple indexers provides redundancy and increases "
                "the chances of finding releases. If one indexer is down or "
                "doesn't have a particular release, others can fill the gap."
            ),
            "priority": "high",
            "impact": (
                "Single indexer configurations create a single point of "
                "failure, risking missed movies when the indexer is "
                "unavailable or lacking content."
            ),
            "documentation_url": "https://wiki.servarr.com/radarr/settings#indexers",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "radarr",
            "category": "media_management",
            "setting_name": "minimum_free_space",
            "setting_path": "settings.mediaManagement.minimumFreeSpaceWhenImporting",
            "recommended_value": json.dumps(
                {
                    "type": "greater_than",
                    "value": 100,
                    "description": "Minimum free space in MB (recommended 100MB+)",
                    "min": 100,
                }
            ),
            "current_check_type": "greater_than",
            "explanation": (
                "Setting a minimum free space threshold prevents Radarr from "
                "filling your disk completely, which can cause system "
                "instability and prevent other applications from functioning."
            ),
            "priority": "high",
            "impact": (
                "Without minimum free space, the disk can fill completely, "
                "causing system crashes, database corruption, and preventing "
                "other applications from writing data."
            ),
            "documentation_url": "https://wiki.servarr.com/radarr/settings#media-management",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "radarr",
            "category": "download_clients",
            "setting_name": "completed_download_handling",
            "setting_path": "settings.downloadClient.enableCompletedDownloadHandling",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": True,
                    "description": "Enable completed download handling",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Completed download handling allows Radarr to automatically "
                "import and process downloads, moving them to your media "
                "library and triggering renaming/organizing actions."
            ),
            "priority": "critical",
            "impact": (
                "Without this, downloads must be manually imported, defeating "
                "the purpose of automation and potentially leaving files in "
                "the download directory."
            ),
            "documentation_url": (
                "https://wiki.servarr.com/radarr/settings#completed-download-handling"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        # ====================================================================
        # Plex Best Practices (6 practices)
        # ====================================================================
        {
            "application": "plex",
            "category": "library",
            "setting_name": "scan_on_startup",
            "setting_path": "settings.library.scanOnStartup",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": False,
                    "description": "Disable scan on startup to reduce server load",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Disabling scan on startup prevents resource-intensive "
                "library scans when the server restarts, which can slow down "
                "server availability and impact other services during boot."
            ),
            "priority": "medium",
            "impact": (
                "Scanning on startup delays server availability and can cause "
                "high CPU/disk usage during boot, impacting other services."
            ),
            "documentation_url": (
                "https://support.plex.tv/articles/200289306-scanning-vs-refreshing-a-library/"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "plex",
            "category": "transcoding",
            "setting_name": "hardware_transcoding",
            "setting_path": "settings.transcoder.hardwareAcceleration",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": True,
                    "description": "Enable hardware transcoding if supported",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Hardware transcoding offloads video processing to GPU, "
                "dramatically reducing CPU usage and allowing more "
                "simultaneous transcoding streams. This is especially "
                "important for 4K content."
            ),
            "priority": "high",
            "impact": (
                "Software transcoding uses significantly more CPU (5-10x), "
                "limiting concurrent streams and potentially causing buffering "
                "issues."
            ),
            "documentation_url": (
                "https://support.plex.tv/articles/"
                "115002178853-using-hardware-accelerated-streaming/"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "plex",
            "category": "network",
            "setting_name": "secure_connections",
            "setting_path": "settings.network.secureConnections",
            "recommended_value": json.dumps(
                {
                    "type": "equals",
                    "value": "preferred",
                    "description": "Set secure connections to 'preferred' or 'required'",
                    "alternatives": ["preferred", "required"],
                }
            ),
            "current_check_type": "contains",
            "explanation": (
                "Enabling secure connections encrypts traffic between clients "
                "and the server, protecting your media consumption patterns "
                "and credentials from being intercepted."
            ),
            "priority": "high",
            "impact": (
                "Unencrypted connections expose viewing habits and "
                "potentially sensitive information to network eavesdropping."
            ),
            "documentation_url": (
                "https://support.plex.tv/articles/"
                "206225077-how-to-use-secure-server-connections/"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "plex",
            "category": "transcoding",
            "setting_name": "transcoder_temp_directory",
            "setting_path": "settings.transcoder.tempDirectory",
            "recommended_value": json.dumps(
                {
                    "type": "not_empty",
                    "description": "Transcoder temp directory should be set to fast storage",
                }
            ),
            "current_check_type": "not_empty",
            "explanation": (
                "Setting the transcoder temp directory to fast storage "
                "(SSD/NVMe) improves transcoding performance and reduces seek "
                "times, especially important for 4K content and multiple "
                "streams."
            ),
            "priority": "medium",
            "impact": (
                "Slow storage for transcoding causes buffering, longer "
                "transcode times, and poor playback experience, especially "
                "with high-bitrate content."
            ),
            "documentation_url": "https://support.plex.tv/articles/200250347-transcoder/",
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "plex",
            "category": "library",
            "setting_name": "generate_video_preview_thumbnails",
            "setting_path": "settings.library.generateVideoPreviewThumbnails",
            "recommended_value": json.dumps(
                {
                    "type": "equals",
                    "value": "never",
                    "description": "Disable video preview thumbnails to save resources",
                    "alternatives": ["never", "as_scheduled"],
                }
            ),
            "current_check_type": "contains",
            "explanation": (
                "Disabling video preview thumbnails saves significant disk "
                "space and processing time, especially for large libraries. "
                "Preview thumbnails are rarely used and can be generated "
                "on-demand if needed."
            ),
            "priority": "low",
            "impact": (
                "Generating previews consumes disk space (1-2GB per 100 "
                "movies) and CPU time during scanning, slowing down library "
                "updates."
            ),
            "documentation_url": (
                "https://support.plex.tv/articles/234974307-video-preview-thumbnails/"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
        {
            "application": "plex",
            "category": "agents",
            "setting_name": "local_media_assets",
            "setting_path": "settings.agents.enableLocalMediaAssets",
            "recommended_value": json.dumps(
                {
                    "type": "boolean",
                    "value": True,
                    "description": "Enable local media assets (artwork, subtitles)",
                }
            ),
            "current_check_type": "equals",
            "explanation": (
                "Enabling local media assets allows Plex to use custom "
                "artwork, subtitles, and other media stored alongside your "
                "content, providing better customization and offline "
                "functionality."
            ),
            "priority": "medium",
            "impact": (
                "Without local media assets, Plex relies solely on online "
                "metadata providers, potentially missing custom artwork and "
                "local subtitles."
            ),
            "documentation_url": (
                "https://support.plex.tv/articles/200220677-local-media-assets-movies/"
            ),
            "version_added": "1.0.0",
            "enabled": True,
        },
    ]


async def seed_best_practices(db) -> int:
    """
    Seed the database with initial best practices.

    Args:
        db: Database instance

    Returns:
        Number of best practices inserted
    """
    from autoarr.api.database import BestPracticesRepository

    repository = BestPracticesRepository(db)
    practices_data = get_best_practices_seed_data()

    # Use bulk create for efficiency
    practices = await repository.bulk_create(practices_data)

    return len(practices)
