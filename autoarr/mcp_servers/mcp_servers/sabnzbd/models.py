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
Pydantic models for SABnzbd API data validation.

This module provides type-safe models for SABnzbd API requests and responses,
enabling validation, serialization, and documentation of data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueueSlot(BaseModel):
    """Model for a single download slot in the queue."""

    nzo_id: str = Field(..., description="Unique ID for this download")
    filename: str = Field(..., description="Name of the file being downloaded")
    status: str = Field(..., description="Current status (Downloading, Paused, etc.)")
    mb_left: float = Field(..., description="Megabytes remaining")
    mb: float = Field(..., description="Total size in megabytes")
    percentage: int = Field(..., description="Download progress percentage")
    category: str = Field(..., description="Category assigned to this download")
    priority: str = Field(..., description="Download priority")
    eta: str = Field(..., description="Estimated time of arrival")
    timeleft: str = Field(..., description="Time remaining")


class Queue(BaseModel):
    """Model for the SABnzbd download queue."""

    status: str = Field(..., description="Overall queue status")
    speed: str = Field(..., description="Current download speed")
    speedlimit: str = Field(default="", description="Speed limit setting")
    speedlimit_abs: str = Field(default="", description="Absolute speed limit")
    mb: float = Field(..., description="Total megabytes in queue")
    mbleft: float = Field(..., description="Megabytes remaining in queue")
    slots: List[QueueSlot] = Field(default_factory=list, description="List of download slots")
    size: str = Field(..., description="Human-readable total size")
    sizeleft: str = Field(..., description="Human-readable size remaining")
    noofslots: int = Field(..., description="Number of downloads in queue")
    pause_int: str = Field(default="0", description="Pause state as integer string")
    paused: bool = Field(default=False, description="Whether queue is paused")


class QueueResponse(BaseModel):
    """Model for the complete queue API response."""

    queue: Queue = Field(..., description="Queue data")


class HistorySlot(BaseModel):
    """Model for a single entry in the download history."""

    nzo_id: str = Field(..., description="Unique ID for this download")
    name: str = Field(..., description="Name of the downloaded file")
    status: str = Field(..., description="Final status (Completed, Failed, etc.)")
    fail_message: str = Field(default="", description="Failure message if failed")
    category: str = Field(..., description="Category assigned to this download")
    size: str = Field(..., description="Download size")
    download_time: int = Field(..., description="Time taken to download in seconds")
    completed: int = Field(..., description="Completion timestamp")
    storage: str = Field(default="", description="Storage location")
    action_line: str = Field(default="", description="Action line")
    retry: int = Field(default=0, description="Retry count")


class History(BaseModel):
    """Model for the SABnzbd download history."""

    total_size: str = Field(..., description="Total size of all history")
    month_size: str = Field(..., description="Size downloaded this month")
    week_size: str = Field(..., description="Size downloaded this week")
    day_size: str = Field(..., description="Size downloaded today")
    noofslots: int = Field(..., description="Number of history entries")
    slots: List[HistorySlot] = Field(default_factory=list, description="List of history entries")


class HistoryResponse(BaseModel):
    """Model for the complete history API response."""

    history: History = Field(..., description="History data")


class ConfigMisc(BaseModel):
    """Model for misc configuration section."""

    complete_dir: str = Field(..., description="Completed downloads directory")
    download_dir: str = Field(..., description="Incomplete downloads directory")
    enable_https: bool = Field(..., description="Whether HTTPS is enabled")
    host: str = Field(..., description="Host address")
    port: int = Field(..., description="HTTP port")
    https_port: int = Field(..., description="HTTPS port")
    username: str = Field(default="", description="Web interface username")
    password: str = Field(default="", description="Web interface password")
    api_key: str = Field(..., description="API key")
    nzb_backup_dir: str = Field(default="", description="NZB backup directory")
    auto_browser: int = Field(default=0, description="Auto-launch browser")
    refresh_rate: int = Field(default=1, description="Web UI refresh rate")
    cache_limit: str = Field(default="500M", description="Article cache limit")
    auto_disconnect: int = Field(default=1, description="Auto-disconnect setting")
    par_option: str = Field(default="", description="PAR2 processing option")
    pre_check: int = Field(default=1, description="Pre-check setting")
    nice: str = Field(default="", description="Nice level")
    ionice: str = Field(default="", description="IO nice level")
    cleanup_list: List[str] = Field(default_factory=list, description="Files to clean up")


class ConfigCategory(BaseModel):
    """Model for a category configuration."""

    name: str = Field(..., description="Category name")
    order: int = Field(..., description="Display order")
    pp: int = Field(..., description="Post-processing setting")
    script: str = Field(..., description="Post-processing script")
    dir: str = Field(..., description="Category subdirectory")
    newzbin: str = Field(default="", description="Newzbin setting")
    priority: int = Field(..., description="Priority setting")


class Config(BaseModel):
    """Model for the SABnzbd configuration."""

    misc: ConfigMisc = Field(..., description="Miscellaneous settings")
    servers: List[Dict[str, Any]] = Field(default_factory=list, description="Server configurations")
    categories: Dict[str, ConfigCategory] = Field(
        default_factory=dict, description="Category configurations"
    )


class ConfigResponse(BaseModel):
    """Model for the complete config API response."""

    config: Config = Field(..., description="Configuration data")


class VersionResponse(BaseModel):
    """Model for the version API response."""

    version: str = Field(..., description="SABnzbd version")


class StatusInfo(BaseModel):
    """Model for the status information."""

    version: str = Field(..., description="SABnzbd version")
    uptime: str = Field(..., description="Server uptime")
    color: str = Field(..., description="Status color indicator")
    pp: str = Field(..., description="Post-processing status")
    loadavg: str = Field(..., description="System load average")
    speedlimit: int = Field(..., description="Speed limit setting")
    speedlimit_abs: str = Field(default="", description="Absolute speed limit")
    have_warnings: str = Field(..., description="Whether there are warnings")
    finishaction: Optional[str] = Field(None, description="Action on finish")
    quota: str = Field(..., description="Download quota setting")
    diskspacetotal1: str = Field(..., description="Total disk space 1")
    diskspace1: str = Field(..., description="Available disk space 1")
    diskspacetotal2: str = Field(..., description="Total disk space 2")
    diskspace2: str = Field(..., description="Available disk space 2")
    localipv4: str = Field(..., description="Local IPv4 address")
    publicipv4: str = Field(..., description="Public IPv4 address")


class StatusResponse(BaseModel):
    """Model for the complete status API response."""

    status: StatusInfo = Field(..., description="Status information")


class ActionResponse(BaseModel):
    """Model for action responses (pause, resume, delete, retry, etc.)."""

    status: bool = Field(..., description="Whether the action succeeded")
    nzo_ids: List[str] = Field(default_factory=list, description="Affected NZO IDs")


class ErrorResponse(BaseModel):
    """Model for error responses from SABnzbd API."""

    status: bool = Field(default=False, description="Status (always False for errors)")
    error: str = Field(..., description="Error message")
    error_code: int = Field(default=400, description="Error code")
