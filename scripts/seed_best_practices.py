"""
Seed best practices database.

This script populates the database with best practice recommendations
for all supported applications (SABnzbd, Sonarr, Radarr, Plex).
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from autoarr.api.database import BestPracticesRepository, Database, init_database

# ============================================================================
# Best Practices Data
# ============================================================================

BEST_PRACTICES = [
    # SABnzbd Best Practices
    {
        "application": "sabnzbd",
        "category": "downloads",
        "setting_name": "incomplete_dir",
        "recommended_value": "/downloads/incomplete",
        "priority": "high",
        "description": "Use separate incomplete download directory",
        "reasoning": "Separating incomplete downloads prevents partial files from being processed by media managers",
        "impact": "Risk of corrupted or incomplete files being imported into your media library",
        "source_url": "https://sabnzbd.org/wiki/configuration/folders",
    },
    {
        "application": "sabnzbd",
        "category": "storage",
        "setting_name": "download_free",
        "recommended_value": "10G",
        "priority": "medium",
        "description": "Maintain adequate free disk space",
        "reasoning": "Ensures system stability and prevents download failures due to insufficient space",
        "impact": "Downloads may fail or cause system issues if disk fills up",
        "source_url": "https://sabnzbd.org/wiki/configuration/folders",
    },
    {
        "application": "sabnzbd",
        "category": "performance",
        "setting_name": "refresh_rate",
        "recommended_value": "2",
        "priority": "medium",
        "description": "Set appropriate UI refresh rate",
        "reasoning": "Reduces server load and API request frequency while maintaining responsiveness",
        "impact": "Excessive API calls can trigger rate limiting or increase server load",
        "source_url": "https://sabnzbd.org/wiki/configuration/general",
    },
    {
        "application": "sabnzbd",
        "category": "notifications",
        "setting_name": "queue_complete",
        "recommended_value": "script",
        "priority": "low",
        "description": "Configure queue completion notifications",
        "reasoning": "Enables automated workflows when downloads complete",
        "impact": "Missing notifications about completed downloads",
        "source_url": "https://sabnzbd.org/wiki/configuration/notifications",
    },
    {
        "application": "sabnzbd",
        "category": "downloads",
        "setting_name": "pre_script",
        "recommended_value": "None",
        "priority": "low",
        "description": "Configure pre-processing script if needed",
        "reasoning": "Allows custom processing before extraction",
        "impact": "No automated pre-processing of downloads",
        "source_url": "https://sabnzbd.org/wiki/scripts",
    },
    # Sonarr Best Practices
    {
        "application": "sonarr",
        "category": "downloads",
        "setting_name": "enableCompletedDownloadHandling",
        "recommended_value": "true",
        "priority": "high",
        "description": "Enable completed download handling",
        "reasoning": "Automatically imports completed downloads from your download client",
        "impact": "Manual intervention required to import completed episodes",
        "source_url": "https://wiki.servarr.com/sonarr/settings#completed-download-handling",
    },
    {
        "application": "sonarr",
        "category": "downloads",
        "setting_name": "autoRedownloadFailed",
        "recommended_value": "true",
        "priority": "high",
        "description": "Enable automatic redownload of failed releases",
        "reasoning": "Automatically retries failed downloads with alternative releases",
        "impact": "Missing episodes due to failed downloads not being retried",
        "source_url": "https://wiki.servarr.com/sonarr/settings#failed-download-handling",
    },
    {
        "application": "sonarr",
        "category": "downloads",
        "setting_name": "removeFailedDownloads",
        "recommended_value": "true",
        "priority": "medium",
        "description": "Automatically remove failed downloads",
        "reasoning": "Keeps download queue clean by removing failed items",
        "impact": "Failed downloads clutter the queue and may cause confusion",
        "source_url": "https://wiki.servarr.com/sonarr/settings#failed-download-handling",
    },
    {
        "application": "sonarr",
        "category": "quality",
        "setting_name": "preferredWordScore",
        "recommended_value": "10",
        "priority": "low",
        "description": "Configure preferred word scoring",
        "reasoning": "Prioritizes releases matching your preferred criteria",
        "impact": "May not get preferred release versions",
        "source_url": "https://wiki.servarr.com/sonarr/settings#profiles",
    },
    {
        "application": "sonarr",
        "category": "monitoring",
        "setting_name": "monitorEpisodes",
        "recommended_value": "all",
        "priority": "medium",
        "description": "Configure episode monitoring strategy",
        "reasoning": "Determines which episodes are automatically searched",
        "impact": "May miss episodes if monitoring is too restrictive",
        "source_url": "https://wiki.servarr.com/sonarr/settings#series",
    },
    # Radarr Best Practices
    {
        "application": "radarr",
        "category": "downloads",
        "setting_name": "enableCompletedDownloadHandling",
        "recommended_value": "true",
        "priority": "high",
        "description": "Enable completed download handling",
        "reasoning": "Automatically imports completed downloads from your download client",
        "impact": "Manual intervention required to import completed movies",
        "source_url": "https://wiki.servarr.com/radarr/settings#completed-download-handling",
    },
    {
        "application": "radarr",
        "category": "downloads",
        "setting_name": "autoRedownloadFailed",
        "recommended_value": "true",
        "priority": "high",
        "description": "Enable automatic redownload of failed releases",
        "reasoning": "Automatically retries failed downloads with alternative releases",
        "impact": "Missing movies due to failed downloads not being retried",
        "source_url": "https://wiki.servarr.com/radarr/settings#failed-download-handling",
    },
    {
        "application": "radarr",
        "category": "downloads",
        "setting_name": "removeFailedDownloads",
        "recommended_value": "true",
        "priority": "medium",
        "description": "Automatically remove failed downloads",
        "reasoning": "Keeps download queue clean by removing failed items",
        "impact": "Failed downloads clutter the queue",
        "source_url": "https://wiki.servarr.com/radarr/settings#failed-download-handling",
    },
    {
        "application": "radarr",
        "category": "quality",
        "setting_name": "minimumAvailability",
        "recommended_value": "released",
        "priority": "medium",
        "description": "Set minimum availability for searching",
        "reasoning": "Prevents searching for movies before they're available",
        "impact": "May search for movies prematurely, wasting resources",
        "source_url": "https://wiki.servarr.com/radarr/settings#movies",
    },
    {
        "application": "radarr",
        "category": "quality",
        "setting_name": "preferredWordScore",
        "recommended_value": "10",
        "priority": "low",
        "description": "Configure preferred word scoring",
        "reasoning": "Prioritizes releases matching your preferred criteria",
        "impact": "May not get preferred release versions",
        "source_url": "https://wiki.servarr.com/radarr/settings#profiles",
    },
    # Plex Best Practices
    {
        "application": "plex",
        "category": "library",
        "setting_name": "scanLibraryOnStartup",
        "recommended_value": "false",
        "priority": "medium",
        "description": "Disable library scan on startup",
        "reasoning": "Reduces startup time and server load",
        "impact": "Slower startup but less resource intensive",
        "source_url": "https://support.plex.tv/articles/200289306-scanning-vs-refreshing-a-library/",
    },
    {
        "application": "plex",
        "category": "library",
        "setting_name": "autoEmptyTrash",
        "recommended_value": "true",
        "priority": "low",
        "description": "Automatically empty trash",
        "reasoning": "Keeps library clean and frees up space",
        "impact": "Manual trash emptying required, potential space waste",
        "source_url": "https://support.plex.tv/articles/200289326-emptying-library-trash/",
    },
    {
        "application": "plex",
        "category": "transcoding",
        "setting_name": "transcodeDirectory",
        "recommended_value": "/tmp/plex",
        "priority": "high",
        "description": "Use fast storage for transcoding",
        "reasoning": "Improves transcoding performance and reduces wear on main drives",
        "impact": "Slower transcoding and increased disk wear",
        "source_url": "https://support.plex.tv/articles/200250347-transcoder/",
    },
    {
        "application": "plex",
        "category": "metadata",
        "setting_name": "enableGenerateThumbnails",
        "recommended_value": "true",
        "priority": "medium",
        "description": "Generate video thumbnails",
        "reasoning": "Improves user experience with visual previews",
        "impact": "No thumbnail previews in media",
        "source_url": "https://support.plex.tv/articles/200289326-video-preview-thumbnails/",
    },
]


async def seed_best_practices(database_url: str = "sqlite:///./autoarr.db"):
    """
    Seed the database with best practices.

    Args:
        database_url: Database connection URL
    """
    print(f"Initializing database: {database_url}")
    db = init_database(database_url)
    await db.init_db()

    repo = BestPracticesRepository(db)

    print(f"\nSeeding {len(BEST_PRACTICES)} best practices...")

    for practice_data in BEST_PRACTICES:
        try:
            practice = await repo.add_best_practice(**practice_data)
            print(
                f"  + [{practice.application}] {practice.setting_name} "
                f"({practice.priority} priority)"
            )
        except Exception as e:
            print(f"  ! Error adding practice: {e}")

    await db.close()
    print("\nBest practices seeded successfully!")


if __name__ == "__main__":
    database_url = sys.argv[1] if len(sys.argv) > 1 else "sqlite:///./autoarr.db"
    asyncio.run(seed_best_practices(database_url))
