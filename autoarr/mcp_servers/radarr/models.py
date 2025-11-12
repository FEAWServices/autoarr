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
Pydantic models for Radarr API data validation.

This module provides type-safe models for Radarr API requests and responses,
enabling validation, serialization, and documentation of data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Movie(BaseModel):
    """Model for a movie."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Unique movie ID")
    title: str = Field(..., description="Movie title")
    sort_title: Optional[str] = Field(None, alias="sortTitle", description="Title for sorting")
    status: str = Field(..., description="Movie status (announced, in cinemas, released, etc.)")
    overview: Optional[str] = Field(None, description="Movie overview/description")
    in_cinemas: Optional[str] = Field(
        None, alias="inCinemas", description="Date movie was released in cinemas"
    )
    physical_release: Optional[str] = Field(
        None, alias="physicalRelease", description="Physical release date"
    )
    digital_release: Optional[str] = Field(
        None, alias="digitalRelease", description="Digital release date"
    )
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Movie images")
    year: int = Field(..., description="Movie release year")
    has_file: bool = Field(False, alias="hasFile", description="Whether movie has file")
    path: str = Field(..., description="Path to movie directory")
    quality_profile_id: int = Field(..., alias="qualityProfileId", description="Quality profile ID")
    monitored: bool = Field(..., description="Whether movie is monitored")
    runtime: Optional[int] = Field(None, description="Movie runtime in minutes")
    tmdb_id: int = Field(..., alias="tmdbId", description="TMDb ID")
    imdb_id: Optional[str] = Field(None, alias="imdbId", description="IMDb ID")
    title_slug: Optional[str] = Field(None, alias="titleSlug", description="URL-friendly title")
    root_folder_path: Optional[str] = Field(
        None, alias="rootFolderPath", description="Root folder path"
    )
    certification: Optional[str] = Field(None, description="Content rating")
    genres: List[str] = Field(default_factory=list, description="Movie genres")
    tags: List[int] = Field(default_factory=list, description="Tag IDs")
    website: Optional[str] = Field(None, description="Movie website")
    youtube_trailer_id: Optional[str] = Field(
        None, alias="youTubeTrailerId", description="YouTube trailer ID"
    )
    studio: Optional[str] = Field(None, description="Movie studio")
    minimum_availability: Optional[str] = Field(
        None, alias="minimumAvailability", description="Minimum availability"
    )
    folder_name: Optional[str] = Field(None, alias="folderName", description="Folder name")
    clean_title: Optional[str] = Field(
        None, alias="cleanTitle", description="Clean title for search"
    )
    size_on_disk: Optional[int] = Field(
        None, alias="sizeOnDisk", description="Size on disk in bytes"
    )
    movie_file: Optional[Dict[str, Any]] = Field(
        None, alias="movieFile", description="Movie file information"
    )


class MovieFile(BaseModel):
    """Model for a movie file."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Unique file ID")
    movie_id: int = Field(..., alias="movieId", description="Parent movie ID")
    relative_path: str = Field(..., alias="relativePath", description="Relative path to file")
    path: Optional[str] = Field(None, description="Full path to file")
    size: int = Field(..., description="File size in bytes")
    date_added: Optional[str] = Field(None, alias="dateAdded", description="Date file was added")
    quality: Dict[str, Any] = Field(..., description="Quality information")
    media_info: Optional[Dict[str, Any]] = Field(
        None, alias="mediaInfo", description="Media information"
    )


class Command(BaseModel):
    """Model for a Radarr command."""

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
    movie_id: int = Field(..., alias="movieId", description="Movie ID")
    movie: Optional[Dict[str, Any]] = Field(None, description="Movie information")
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
    """Model for wanted/missing movies."""

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., alias="pageSize", description="Page size")
    sort_key: Optional[str] = Field(None, alias="sortKey", description="Sort key")
    sort_direction: Optional[str] = Field(None, alias="sortDirection", description="Sort direction")
    total_records: int = Field(..., alias="totalRecords", description="Total number of records")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="Missing movie records")


class SystemStatus(BaseModel):
    """Model for Radarr system status."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(..., description="Radarr version")
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
    """Model for error responses from Radarr API."""

    model_config = ConfigDict(populate_by_name=True)

    status: bool = Field(default=False, description="Status (always False for errors)")
    error: str = Field(..., description="Error message")
    message: Optional[str] = Field(None, description="Additional error message")
    status_code: Optional[int] = Field(None, alias="statusCode", description="HTTP status code")
