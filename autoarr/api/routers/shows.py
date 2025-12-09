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

from __future__ import annotations

"""
TV Shows endpoints (Sonarr).

This module provides endpoints for managing TV shows via Sonarr.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator
from ..models import AddSeriesRequest

router = APIRouter()


@router.get("/", tags=["shows"])
async def list_shows(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    List all TV shows.

    Returns a list of all TV shows in Sonarr.

    Returns:
        dict: List of TV shows

    Example:
        ```
        GET /api/v1/shows/
        {
            "series": [...],
            "total": 25
        }
        ```
    """
    result = await orchestrator.call_tool("sonarr", "get_series", {})  # noqa: F841

    # Ensure consistent response format
    if isinstance(result, list):
        return {"series": result, "total": len(result)}
    return result


@router.get("/{series_id}", tags=["shows"])
async def get_show(
    series_id: int,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get a specific TV show by ID.

    Args:
        series_id: Sonarr series ID

    Returns:
        dict: TV show details

    Example:
        ```
        GET /api/v1/shows/123
        {
            "id": 123,
            "title": "Breaking Bad",
            "status": "ended",
            ...
        }
        ```
    """
    result = await orchestrator.call_tool(
        "sonarr", "get_series_by_id", {"series_id": series_id}
    )  # noqa: F841
    return result


@router.post("/", tags=["shows"])
async def add_show(
    request: AddSeriesRequest,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Add a new TV show to Sonarr.

    Args:
        request: Series configuration

    Returns:
        dict: Added series information

    Example:
        ```
        POST /api/v1/shows/
        {
            "title": "Breaking Bad",
            "tvdb_id": 81189,
            "quality_profile_id": 1,
            "root_folder_path": "/tv",
            "monitored": true,
            "season_folder": true
        }
        ```
    """
    result = await orchestrator.call_tool(
        "sonarr", "add_series", request.model_dump()
    )  # noqa: F841
    return result


@router.delete("/{series_id}", tags=["shows"])
async def delete_show(
    series_id: int,
    delete_files: bool = False,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Delete a TV show from Sonarr.

    Args:
        series_id: Sonarr series ID
        delete_files: Whether to delete files from disk

    Returns:
        dict: Delete operation result

    Example:
        ```
        DELETE /api/v1/shows/123?delete_files=true
        {
            "success": true,
            "message": "Series deleted successfully"
        }
        ```
    """
    result = await orchestrator.call_tool(  # noqa: F841
        "sonarr", "delete_series", {"series_id": series_id, "delete_files": delete_files}
    )
    return result


@router.get("/search/{query}", tags=["shows"])
async def search_shows(
    query: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> List[Dict[str, Any]]:
    """
    Search for TV shows.

    Args:
        query: Search query (show title)

    Returns:
        list: Search results

    Example:
        ```
        GET /api/v1/shows/search/breaking%20bad
        [
            {
                "title": "Breaking Bad",
                "tvdbId": 81189,
                "year": 2008,
                ...
            }
        ]
        ```
    """
    result = await orchestrator.call_tool("sonarr", "search_series", {"query": query})  # noqa: F841
    return result if isinstance(result, list) else []


@router.get("/calendar/upcoming", tags=["shows"])
async def get_calendar(
    start_date: str = None,
    end_date: str = None,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> List[Dict[str, Any]]:
    """
    Get upcoming episodes calendar.

    Args:
        start_date: Start date (ISO format, optional)
        end_date: End date (ISO format, optional)

    Returns:
        list: Upcoming episodes

    Example:
        ```
        GET /api/v1/shows/calendar/upcoming?start_date=2025-01-01&end_date=2025-01-31
        [
            {
                "seriesTitle": "Breaking Bad",
                "episodeTitle": "Pilot",
                "airDateUtc": "2025-01-15T20:00:00Z",
                ...
            }
        ]
        ```
    """
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    result = await orchestrator.call_tool("sonarr", "get_calendar", params)  # noqa: F841
    return result if isinstance(result, list) else []


@router.get("/queue/active", tags=["shows"])
async def get_queue(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get Sonarr download queue.

    Returns currently downloading episodes.

    Returns:
        dict: Download queue

    Example:
        ```
        GET /api/v1/shows/queue/active
        {
            "queue": [...],
            "total": 3
        }
        ```
    """
    result = await orchestrator.call_tool("sonarr", "get_queue", {})  # noqa: F841

    # Ensure consistent response format
    if isinstance(result, list):
        return {"queue": result, "total": len(result)}
    return result


@router.post("/command/series-search", tags=["shows"])
async def search_series_episodes(
    series_id: int,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Trigger a search for all episodes of a series.

    Args:
        series_id: Sonarr series ID

    Returns:
        dict: Command execution result

    Example:
        ```
        POST /api/v1/shows/command/series-search?series_id=123
        {
            "success": true,
            "commandId": 456
        }
        ```
    """
    result = await orchestrator.call_tool(  # noqa: F841
        "sonarr", "trigger_series_search", {"series_id": series_id}
    )
    return result


@router.post("/command/episode-search", tags=["shows"])
async def search_episode(
    episode_id: int,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Trigger a search for a specific episode.

    Args:
        episode_id: Sonarr episode ID

    Returns:
        dict: Command execution result

    Example:
        ```
        POST /api/v1/shows/command/episode-search?episode_id=789
        {
            "success": true,
            "commandId": 456
        }
        ```
    """
    result = await orchestrator.call_tool(  # noqa: F841
        "sonarr", "trigger_episode_search", {"episode_id": episode_id}
    )
    return result
