"""
Pydantic models for API request/response validation.

This module defines all request and response models used in the FastAPI Gateway,
ensuring type safety and automatic validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# MCP Tool Models
# ============================================================================


class ToolCallRequest(BaseModel):
    """Request model for calling a single MCP tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "server": "sabnzbd",
                "tool": "get_queue",
                "params": {},
                "timeout": 30.0,
            }
        }
    )

    server: str = Field(..., description="MCP server name (sabnzbd, sonarr, radarr, plex)")
    tool: str = Field(..., description="Tool name to call")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    timeout: Optional[float] = Field(None, description="Optional timeout in seconds")


class ToolCallResponse(BaseModel):
    """Response model for tool call results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"queue": []},
                "error": None,
                "metadata": {"server": "sabnzbd", "tool": "get_queue", "duration": 0.123},
            }
        }
    )

    success: bool = Field(..., description="Whether the tool call was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Tool call result data")
    error: Optional[str] = Field(None, description="Error message if call failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchToolCallRequest(BaseModel):
    """Request model for calling multiple MCP tools in parallel."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calls": [
                    {"server": "sabnzbd", "tool": "get_queue", "params": {}},
                    {"server": "sonarr", "tool": "get_series", "params": {}},
                ],
                "return_partial": False,
            }
        }
    )

    calls: List[ToolCallRequest] = Field(..., description="List of tool calls to execute")
    return_partial: bool = Field(False, description="Return partial results if some calls fail")


class ToolListResponse(BaseModel):
    """Response model for listing available tools."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tools": {
                    "sabnzbd": ["get_queue", "get_history", "retry_download"],
                    "sonarr": ["get_series", "search_series", "get_calendar"],
                }
            }
        }
    )

    tools: Dict[str, List[str]] = Field(..., description="Tools grouped by server")


# ============================================================================
# Health Check Models
# ============================================================================


class ServiceHealth(BaseModel):
    """Health status for a single service."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "healthy": True,
                "latency_ms": 45.2,
                "error": None,
                "last_check": "2025-01-15T10:30:00Z",
                "circuit_breaker_state": "closed",
            }
        }
    )

    healthy: bool = Field(..., description="Whether the service is healthy")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    last_check: str = Field(..., description="ISO timestamp of last health check")
    circuit_breaker_state: Optional[str] = Field(
        None, description="Circuit breaker state (closed, open, half_open)"
    )


class HealthCheckResponse(BaseModel):
    """Overall system health check response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "services": {
                    "sabnzbd": {
                        "healthy": True,
                        "latency_ms": 45.2,
                        "error": None,
                        "last_check": "2025-01-15T10:30:00Z",
                        "circuit_breaker_state": "closed",
                    }
                },
                "timestamp": "2025-01-15T10:30:00Z",
            }
        }
    )

    status: str = Field(..., description="Overall status (healthy, degraded, unhealthy)")
    services: Dict[str, ServiceHealth] = Field(..., description="Individual service health")
    timestamp: str = Field(..., description="ISO timestamp of health check")


# ============================================================================
# Error Response Models
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Service unavailable",
                "detail": "Connection to SABnzbd failed",
                "timestamp": "2025-01-15T10:30:00Z",
                "path": "/api/v1/downloads/queue",
            }
        }
    )

    error: str = Field(..., description="Error type or category")
    detail: str = Field(..., description="Detailed error message")
    timestamp: str = Field(..., description="ISO timestamp of error")
    path: Optional[str] = Field(None, description="Request path that caused the error")


# ============================================================================
# Service-Specific Models (Downloads/SABnzbd)
# ============================================================================


class QueueItem(BaseModel):
    """Download queue item model."""

    nzo_id: str = Field(..., description="NZB ID")
    filename: str = Field(..., description="File name")
    status: str = Field(..., description="Download status")
    mb_left: float = Field(..., description="Megabytes remaining")
    mb_total: float = Field(..., description="Total megabytes")
    percentage: float = Field(..., description="Download percentage")
    eta: Optional[str] = Field(None, description="Estimated time to completion")


class DownloadQueueResponse(BaseModel):
    """SABnzbd download queue response."""

    queue: List[QueueItem] = Field(..., description="Download queue items")
    speed: str = Field(..., description="Current download speed")
    size_left: str = Field(..., description="Total size remaining")
    paused: bool = Field(..., description="Whether queue is paused")


class RetryDownloadRequest(BaseModel):
    """Request to retry a failed download."""

    nzo_id: str = Field(..., description="NZB ID to retry")


# ============================================================================
# Service-Specific Models (Shows/Sonarr)
# ============================================================================


class Series(BaseModel):
    """TV series model."""

    id: int = Field(..., description="Series ID")
    title: str = Field(..., description="Series title")
    status: str = Field(..., description="Series status")
    overview: Optional[str] = Field(None, description="Series overview")
    year: Optional[int] = Field(None, description="Series year")
    season_count: Optional[int] = Field(None, description="Number of seasons")
    monitored: bool = Field(..., description="Whether series is monitored")


class SeriesListResponse(BaseModel):
    """Response for listing TV series."""

    series: List[Series] = Field(..., description="List of TV series")
    total: int = Field(..., description="Total number of series")


class AddSeriesRequest(BaseModel):
    """Request to add a new TV series."""

    title: str = Field(..., description="Series title")
    tvdb_id: int = Field(..., description="TVDB ID")
    quality_profile_id: int = Field(..., description="Quality profile ID")
    root_folder_path: str = Field(..., description="Root folder path")
    monitored: bool = Field(True, description="Monitor the series")
    season_folder: bool = Field(True, description="Use season folders")


# ============================================================================
# Service-Specific Models (Movies/Radarr)
# ============================================================================


class Movie(BaseModel):
    """Movie model."""

    id: int = Field(..., description="Movie ID")
    title: str = Field(..., description="Movie title")
    status: str = Field(..., description="Movie status")
    overview: Optional[str] = Field(None, description="Movie overview")
    year: Optional[int] = Field(None, description="Movie year")
    has_file: bool = Field(..., description="Whether movie has a file")
    monitored: bool = Field(..., description="Whether movie is monitored")


class MovieListResponse(BaseModel):
    """Response for listing movies."""

    movies: List[Movie] = Field(..., description="List of movies")
    total: int = Field(..., description="Total number of movies")


class AddMovieRequest(BaseModel):
    """Request to add a new movie."""

    title: str = Field(..., description="Movie title")
    tmdb_id: int = Field(..., description="TMDB ID")
    quality_profile_id: int = Field(..., description="Quality profile ID")
    root_folder_path: str = Field(..., description="Root folder path")
    monitored: bool = Field(True, description="Monitor the movie")


# ============================================================================
# Service-Specific Models (Media/Plex)
# ============================================================================


class PlexLibrary(BaseModel):
    """Plex library model."""

    key: str = Field(..., description="Library key")
    title: str = Field(..., description="Library title")
    type: str = Field(..., description="Library type (movie, show, etc.)")
    agent: str = Field(..., description="Library agent")
    scanner: str = Field(..., description="Library scanner")
    language: str = Field(..., description="Library language")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class LibraryListResponse(BaseModel):
    """Response for listing Plex libraries."""

    libraries: List[PlexLibrary] = Field(..., description="List of libraries")
    total: int = Field(..., description="Total number of libraries")


class MediaItem(BaseModel):
    """Plex media item model."""

    rating_key: str = Field(..., description="Media rating key")
    title: str = Field(..., description="Media title")
    type: str = Field(..., description="Media type")
    year: Optional[int] = Field(None, description="Media year")
    added_at: str = Field(..., description="Date added")


class RecentlyAddedResponse(BaseModel):
    """Response for recently added media."""

    items: List[MediaItem] = Field(..., description="Recently added items")
    total: int = Field(..., description="Total number of items")


class ScanLibraryRequest(BaseModel):
    """Request to scan a Plex library."""

    library_key: str = Field(..., description="Library key to scan")


# ============================================================================
# Statistics Models
# ============================================================================


class OrchestratorStats(BaseModel):
    """Orchestrator statistics model."""

    total_calls: int = Field(..., description="Total number of tool calls")
    total_health_checks: int = Field(..., description="Total health checks performed")
    calls_per_server: Dict[str, int] = Field(..., description="Number of calls per server")
    uptime_seconds: Optional[float] = Field(None, description="Orchestrator uptime in seconds")


class StatsResponse(BaseModel):
    """Response for statistics endpoint."""

    stats: OrchestratorStats = Field(..., description="Orchestrator statistics")
    timestamp: str = Field(..., description="ISO timestamp")


# ============================================================================
# Best Practices Models
# ============================================================================


# Type definitions for validation
ApplicationType = Literal["sabnzbd", "sonarr", "radarr", "plex"]
PriorityLevel = Literal["critical", "high", "medium", "low"]
CheckType = Literal[
    "equals",
    "not_equals",
    "contains",
    "not_contains",
    "greater_than",
    "less_than",
    "in_range",
    "regex",
    "exists",
    "not_empty",
    "boolean",
    "custom",
]


class BestPracticeBase(BaseModel):
    """Base model for best practice with common fields."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "application": "sabnzbd",
                "category": "downloads",
                "setting_name": "incomplete_dir",
                "setting_path": "misc.incomplete_dir",
                "recommended_value": '{"type": "not_empty", "description": "Separate directory"}',
                "current_check_type": "not_empty",
                "explanation": "Using a separate incomplete directory prevents issues",
                "priority": "high",
                "impact": "Incomplete downloads may be processed incorrectly",
                "documentation_url": "https://sabnzbd.org/wiki/configuration/",
                "version_added": "1.0.0",
                "enabled": True,
            }
        }
    )

    application: ApplicationType = Field(..., description="Application name")
    category: str = Field(..., description="Configuration category", max_length=100)
    setting_name: str = Field(..., description="Name of the setting", max_length=200)
    setting_path: str = Field(..., description="JSON path or config location", max_length=500)
    recommended_value: str = Field(..., description="Recommended value as JSON string")
    current_check_type: CheckType = Field(..., description="How to validate the setting")
    explanation: str = Field(..., description="Why this is recommended")
    priority: PriorityLevel = Field(..., description="Priority level")
    impact: Optional[str] = Field(None, description="Impact of not following this practice")
    documentation_url: Optional[str] = Field(
        None, description="Link to official docs", max_length=500
    )
    version_added: str = Field(..., description="Version when practice was added", max_length=50)
    version_updated: Optional[str] = Field(None, description="Last version updated", max_length=50)
    enabled: bool = Field(True, description="Whether this practice is active")

    @field_validator("recommended_value")
    @classmethod
    def validate_json_string(cls, v: str) -> str:
        """Validate that recommended_value is a valid JSON string."""
        import json

        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"recommended_value must be valid JSON: {e}")
        return v


class BestPracticeCreate(BestPracticeBase):
    """Model for creating a new best practice."""


class BestPracticeUpdate(BaseModel):
    """Model for updating an existing best practice (all fields optional)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "priority": "low",
                "enabled": False,
                "explanation": "Updated explanation",
            }
        }
    )

    application: Optional[ApplicationType] = None
    category: Optional[str] = Field(None, max_length=100)
    setting_name: Optional[str] = Field(None, max_length=200)
    setting_path: Optional[str] = Field(None, max_length=500)
    recommended_value: Optional[str] = None
    current_check_type: Optional[CheckType] = None
    explanation: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    impact: Optional[str] = None
    documentation_url: Optional[str] = Field(None, max_length=500)
    version_updated: Optional[str] = Field(None, max_length=50)
    enabled: Optional[bool] = None

    @field_validator("recommended_value")
    @classmethod
    def validate_json_string(cls, v: Optional[str]) -> Optional[str]:
        """Validate that recommended_value is a valid JSON string if provided."""
        if v is not None:
            import json

            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"recommended_value must be valid JSON: {e}")
        return v


class BestPracticeResponse(BestPracticeBase):
    """Response model for a best practice (includes id and timestamps)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "application": "sabnzbd",
                "category": "downloads",
                "setting_name": "incomplete_dir",
                "setting_path": "misc.incomplete_dir",
                "recommended_value": '{"type": "not_empty"}',
                "current_check_type": "not_empty",
                "explanation": "Prevents issues with incomplete downloads",
                "priority": "high",
                "impact": "May cause processing errors",
                "documentation_url": "https://sabnzbd.org/wiki/",
                "version_added": "1.0.0",
                "version_updated": None,
                "enabled": True,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            }
        },
    )

    id: int = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BestPracticeFilter(BaseModel):
    """Model for filtering best practices."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "application": "sabnzbd",
                "category": "downloads",
                "priority": "high",
                "enabled": True,
            }
        }
    )

    application: Optional[ApplicationType] = None
    category: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    enabled: Optional[bool] = None


class BestPracticeListResponse(BaseModel):
    """Response model for listing best practices."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practices": [
                    {
                        "id": 1,
                        "application": "sabnzbd",
                        "category": "downloads",
                        "setting_name": "incomplete_dir",
                        "priority": "high",
                        "enabled": True,
                    }
                ],
                "total": 1,
            }
        }
    )

    practices: List[BestPracticeResponse] = Field(..., description="List of best practices")
    total: int = Field(..., description="Total number of practices")
