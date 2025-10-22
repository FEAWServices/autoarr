"""
Movies endpoints (Radarr).

This module provides endpoints for managing movies via Radarr.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator
from ..models import AddMovieRequest

router = APIRouter()


@router.get("/", tags=["movies"])
async def list_movies(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    List all movies.

    Returns a list of all movies in Radarr.

    Returns:
        dict: List of movies

    Example:
        ```
        GET /api/v1/movies/
        {
            "movies": [...],
            "total": 150
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool("radarr", "get_movies", {})  # noqa: F841

    # Ensure consistent response format
    if isinstance(result, list):
        return {"movies": result, "total": len(result)}
    return result


@router.get("/{movie_id}", tags=["movies"])
async def get_movie(
    movie_id: int,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get a specific movie by ID.

    Args:
        movie_id: Radarr movie ID

    Returns:
        dict: Movie details

    Example:
        ```
        GET /api/v1/movies/123
        {
            "id": 123,
            "title": "The Matrix",
            "year": 1999,
            ...
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool(
        "radarr", "get_movie_by_id", {"movie_id": movie_id}
    )  # noqa: F841
    return result


@router.post("/", tags=["movies"])
async def add_movie(
    request: AddMovieRequest,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Add a new movie to Radarr.

    Args:
        request: Movie configuration

    Returns:
        dict: Added movie information

    Example:
        ```
        POST /api/v1/movies/
        {
            "title": "The Matrix",
            "tmdb_id": 603,
            "quality_profile_id": 1,
            "root_folder_path": "/movies",
            "monitored": true
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool("radarr", "add_movie", request.model_dump())  # noqa: F841
    return result


@router.delete("/{movie_id}", tags=["movies"])
async def delete_movie(
    movie_id: int,
    delete_files: bool = False,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Delete a movie from Radarr.

    Args:
        movie_id: Radarr movie ID
        delete_files: Whether to delete files from disk

    Returns:
        dict: Delete operation result

    Example:
        ```
        DELETE /api/v1/movies/123?delete_files=true
        {
            "success": true,
            "message": "Movie deleted successfully"
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool(  # noqa: F841
        "radarr", "delete_movie", {"movie_id": movie_id, "delete_files": delete_files}
    )
    return result


@router.get("/search/{query}", tags=["movies"])
async def search_movies(
    query: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> List[Dict[str, Any]]:
    """
    Search for movies.

    Args:
        query: Search query (movie title)

    Returns:
        list: Search results

    Example:
        ```
        GET /api/v1/movies/search/matrix
        [
            {
                "title": "The Matrix",
                "tmdbId": 603,
                "year": 1999,
                ...
            }
        ]
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool("radarr", "search_movies", {"query": query})  # noqa: F841
    return result if isinstance(result, list) else []


@router.get("/calendar/upcoming", tags=["movies"])
async def get_calendar(
    start_date: str = None,
    end_date: str = None,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> List[Dict[str, Any]]:
    """
    Get upcoming movies calendar.

    Args:
        start_date: Start date (ISO format, optional)
        end_date: End date (ISO format, optional)

    Returns:
        list: Upcoming movies

    Example:
        ```
        GET /api/v1/movies/calendar/upcoming?start_date=2025-01-01&end_date=2025-01-31
        [
            {
                "title": "The Matrix Resurrections",
                "digitalRelease": "2025-01-15",
                ...
            }
        ]
        ```
    """
    # orchestrator is already resolved by FastAPI
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    result = await orchestrator.call_tool("radarr", "get_calendar", params)  # noqa: F841
    return result if isinstance(result, list) else []


@router.get("/queue/active", tags=["movies"])
async def get_queue(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get Radarr download queue.

    Returns currently downloading movies.

    Returns:
        dict: Download queue

    Example:
        ```
        GET /api/v1/movies/queue/active
        {
            "queue": [...],
            "total": 2
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool("radarr", "get_queue", {})  # noqa: F841

    # Ensure consistent response format
    if isinstance(result, list):
        return {"queue": result, "total": len(result)}
    return result


@router.post("/command/movie-search", tags=["movies"])
async def search_movie(
    movie_id: int,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Trigger a search for a specific movie.

    Args:
        movie_id: Radarr movie ID

    Returns:
        dict: Command execution result

    Example:
        ```
        POST /api/v1/movies/command/movie-search?movie_id=123
        {
            "success": true,
            "commandId": 456
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool(
        "radarr", "trigger_movie_search", {"movie_id": movie_id}
    )  # noqa: F841
    return result


@router.post("/command/refresh", tags=["movies"])
async def refresh_movie(
    movie_id: int,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Refresh movie information from TMDB.

    Args:
        movie_id: Radarr movie ID

    Returns:
        dict: Command execution result

    Example:
        ```
        POST /api/v1/movies/command/refresh?movie_id=123
        {
            "success": true,
            "commandId": 456
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool(
        "radarr", "refresh_movie", {"movie_id": movie_id}
    )  # noqa: F841
    return result


@router.get("/missing", tags=["movies"])
async def get_missing_movies(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get list of missing movies (monitored but not downloaded).

    Returns:
        dict: Missing movies

    Example:
        ```
        GET /api/v1/movies/missing
        {
            "movies": [...],
            "total": 10
        }
        ```
    """
    # orchestrator is already resolved by FastAPI
    result = await orchestrator.call_tool("radarr", "get_missing_movies", {})  # noqa: F841

    # Ensure consistent response format
    if isinstance(result, list):
        return {"movies": result, "total": len(result)}
    return result
