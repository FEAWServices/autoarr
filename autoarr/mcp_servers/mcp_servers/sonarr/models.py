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
Pydantic models for Sonarr API data validation.

This module provides type-safe models for Sonarr API requests and responses,
enabling validation, serialization, and documentation of data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Season(BaseModel):
    """Model for a TV series season."""

    season_number: int = Field(..., alias="seasonNumber", description="Season number")
    monitored: bool = Field(..., description="Whether the season is monitored")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Season statistics")


class Series(BaseModel):
    """Model for a TV series."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Unique series ID")
    title: str = Field(..., description="Series title")
    sort_title: Optional[str] = Field(None, alias="sortTitle", description="Title for sorting")
    status: str = Field(..., description="Series status (continuing, ended, etc.)")
    overview: Optional[str] = Field(None, description="Series overview/description")
    network: Optional[str] = Field(None, description="Network the series airs on")
    air_time: Optional[str] = Field(None, alias="airTime", description="Time series airs")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Series images")
    seasons: List[Dict[str, Any]] = Field(default_factory=list, description="Series seasons")
    year: Optional[int] = Field(None, description="Year series started")
    path: str = Field(..., description="Path to series directory")
    quality_profile_id: int = Field(..., alias="qualityProfileId", description="Quality profile ID")
    season_folder: bool = Field(..., alias="seasonFolder", description="Use season folders")
    monitored: bool = Field(..., description="Whether series is monitored")
    runtime: Optional[int] = Field(None, description="Episode runtime in minutes")
    tvdb_id: int = Field(..., alias="tvdbId", description="TVDB ID")
    imdb_id: Optional[str] = Field(None, alias="imdbId", description="IMDB ID")
    title_slug: Optional[str] = Field(None, alias="titleSlug", description="URL-friendly title")
    root_folder_path: Optional[str] = Field(
        None, alias="rootFolderPath", description="Root folder path"
    )
    certification: Optional[str] = Field(None, description="Content rating")
    genres: List[str] = Field(default_factory=list, description="Series genres")
    tags: List[int] = Field(default_factory=list, description="Tag IDs")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Series statistics")


class Episode(BaseModel):
    """Model for a TV episode."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Unique episode ID")
    series_id: int = Field(..., alias="seriesId", description="Parent series ID")
    tvdb_id: Optional[int] = Field(None, alias="tvdbId", description="TVDB ID")
    episode_file_id: int = Field(0, alias="episodeFileId", description="Episode file ID")
    season_number: int = Field(..., alias="seasonNumber", description="Season number")
    episode_number: int = Field(..., alias="episodeNumber", description="Episode number")
    title: str = Field(..., description="Episode title")
    air_date: Optional[str] = Field(None, alias="airDate", description="Air date (YYYY-MM-DD)")
    air_date_utc: Optional[str] = Field(None, alias="airDateUtc", description="Air date UTC")
    overview: Optional[str] = Field(None, description="Episode overview")
    has_file: bool = Field(False, alias="hasFile", description="Whether episode has file")
    monitored: bool = Field(True, description="Whether episode is monitored")
    absolute_episode_number: Optional[int] = Field(
        None, alias="absoluteEpisodeNumber", description="Absolute episode number"
    )
    grabbed: Optional[bool] = Field(False, description="Whether episode is grabbed")


class Command(BaseModel):
    """Model for a Sonarr command."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Command ID")
    name: str = Field(..., description="Command name")
    command_name: Optional[str] = Field(None, alias="commandName", description="Command name")
    message: Optional[str] = Field(None, description="Command message")
    body: Optional[Dict[str, Any]] = Field(None, description="Command body/parameters")
    priority: Optional[str] = Field(None, description="Command priority")
    status: str = Field(..., description="Command status (queued, started, completed, failed)")
    queued: Optional[str] = Field(None, description="When command was queued")
    started: Optional[str] = Field(None, description="When command started")
    ended: Optional[str] = Field(None, description="When command ended")
    duration: Optional[str] = Field(None, description="Command duration")
    trigger: Optional[str] = Field(None, description="What triggered the command")


class QueueRecord(BaseModel):
    """Model for a download queue record."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Queue record ID")
    series_id: int = Field(..., alias="seriesId", description="Series ID")
    episode_id: int = Field(..., alias="episodeId", description="Episode ID")
    series: Optional[Dict[str, Any]] = Field(None, description="Series information")
    episode: Optional[Dict[str, Any]] = Field(None, description="Episode information")
    quality: Dict[str, Any] = Field(..., description="Quality information")
    size: int = Field(..., description="Total size in bytes")
    title: str = Field(..., description="Download title")
    sizeleft: int = Field(..., description="Size remaining in bytes")
    timeleft: Optional[str] = Field(None, description="Time remaining")
    estimated_completion_time: Optional[str] = Field(
        None, alias="estimatedCompletionTime", description="ETA"
    )
    status: str = Field(..., description="Download status")
    tracked_download_status: Optional[str] = Field(
        None, alias="trackedDownloadStatus", description="Tracked status"
    )
    tracked_download_state: Optional[str] = Field(
        None, alias="trackedDownloadState", description="Tracked state"
    )
    download_id: Optional[str] = Field(None, alias="downloadId", description="Download client ID")
    protocol: Optional[str] = Field(None, description="Download protocol (usenet, torrent)")
    download_client: Optional[str] = Field(
        None, alias="downloadClient", description="Download client name"
    )


class Queue(BaseModel):
    """Model for the download queue."""

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., alias="pageSize", description="Page size")
    sort_key: Optional[str] = Field(None, alias="sortKey", description="Sort key")
    sort_direction: Optional[str] = Field(None, alias="sortDirection", description="Sort direction")
    total_records: int = Field(..., alias="totalRecords", description="Total number of records")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="Queue records")


class WantedMissing(BaseModel):
    """Model for wanted/missing episodes."""

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., alias="pageSize", description="Page size")
    sort_key: Optional[str] = Field(None, alias="sortKey", description="Sort key")
    sort_direction: Optional[str] = Field(None, alias="sortDirection", description="Sort direction")
    total_records: int = Field(..., alias="totalRecords", description="Total number of records")
    records: List[Dict[str, Any]] = Field(
        default_factory=list, description="Missing episode records"
    )


class SystemStatus(BaseModel):
    """Model for Sonarr system status."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(..., description="Sonarr version")
    build_time: Optional[str] = Field(None, alias="buildTime", description="Build timestamp")
    is_debug: Optional[bool] = Field(None, alias="isDebug", description="Debug mode")
    is_production: Optional[bool] = Field(None, alias="isProduction", description="Production mode")
    is_admin: Optional[bool] = Field(None, alias="isAdmin", description="Admin mode")
    startup_path: Optional[str] = Field(None, alias="startupPath", description="Startup path")
    app_data: Optional[str] = Field(None, alias="appData", description="App data directory")
    os_name: Optional[str] = Field(None, alias="osName", description="Operating system name")
    os_version: Optional[str] = Field(
        None, alias="osVersion", description="Operating system version"
    )
    is_docker: Optional[bool] = Field(None, alias="isDocker", description="Running in Docker")
    mode: Optional[str] = Field(None, description="Running mode")
    branch: Optional[str] = Field(None, description="Git branch")
    authentication: Optional[str] = Field(None, description="Authentication method")
    url_base: Optional[str] = Field(None, alias="urlBase", description="URL base")


class ErrorResponse(BaseModel):
    """Model for error responses from Sonarr API."""

    model_config = ConfigDict(populate_by_name=True)

    status: bool = Field(default=False, description="Status (always False for errors)")
    error: str = Field(..., description="Error message")
    message: Optional[str] = Field(None, description="Additional error message")
    status_code: Optional[int] = Field(None, alias="statusCode", description="HTTP status code")
