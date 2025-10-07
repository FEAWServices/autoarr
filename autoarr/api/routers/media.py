"""
Media endpoints (Plex).

This module provides endpoints for accessing Plex media libraries.
"""

from typing import Any, AsyncGenerator, Dict, List

from fastapi import APIRouter, Depends
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator
from ..models import ScanLibraryRequest

router = APIRouter()


@router.get("/libraries", tags=["media"])
async def list_libraries(
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    List all Plex libraries.

    Returns a list of all media libraries in Plex.

    Returns:
        dict: List of libraries

    Example:
        ```
        GET /api/v1/media/libraries
        {
            "libraries": [
                {
                    "key": "1",
                    "title": "Movies",
                    "type": "movie",
                    ...
                }
            ],
            "total": 3
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "get_libraries", {})

    # Ensure consistent response format
    if isinstance(result, list):
        return {"libraries": result, "total": len(result)}
    return result


@router.get("/libraries/{library_key}", tags=["media"])
async def get_library(
    library_key: str,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get a specific library by key.

    Args:
        library_key: Plex library key

    Returns:
        dict: Library details

    Example:
        ```
        GET /api/v1/media/libraries/1
        {
            "key": "1",
            "title": "Movies",
            "type": "movie",
            ...
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "get_library", {"library_key": library_key})
    return result


@router.get("/recently-added", tags=["media"])
async def get_recently_added(
    limit: int = 20,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get recently added media items.

    Args:
        limit: Maximum number of items to return (default: 20)

    Returns:
        dict: Recently added items

    Example:
        ```
        GET /api/v1/media/recently-added?limit=10
        {
            "items": [
                {
                    "rating_key": "12345",
                    "title": "The Matrix",
                    "type": "movie",
                    ...
                }
            ],
            "total": 10
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "get_recently_added", {"limit": limit})

    # Ensure consistent response format
    if isinstance(result, list):
        return {"items": result, "total": len(result)}
    return result


@router.post("/scan", tags=["media"])
async def scan_library(
    request: ScanLibraryRequest,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Scan a Plex library for new media.

    Args:
        request: Scan library request with library_key

    Returns:
        dict: Scan operation result

    Example:
        ```
        POST /api/v1/media/scan
        {
            "library_key": "1"
        }
        ```

        Response:
        ```
        {
            "success": true,
            "message": "Library scan initiated"
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "scan_library", {"library_key": request.library_key})
    return result


@router.post("/refresh/{rating_key}", tags=["media"])
async def refresh_metadata(
    rating_key: str,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Refresh metadata for a specific media item.

    Args:
        rating_key: Plex rating key of the media item

    Returns:
        dict: Refresh operation result

    Example:
        ```
        POST /api/v1/media/refresh/12345
        {
            "success": true,
            "message": "Metadata refresh initiated"
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "refresh_metadata", {"rating_key": rating_key})
    return result


@router.get("/search", tags=["media"])
async def search_media(
    query: str,
    library_key: str = None,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> List[Dict[str, Any]]:
    """
    Search for media in Plex.

    Args:
        query: Search query
        library_key: Optional library key to search within

    Returns:
        list: Search results

    Example:
        ```
        GET /api/v1/media/search?query=matrix&library_key=1
        [
            {
                "rating_key": "12345",
                "title": "The Matrix",
                "type": "movie",
                ...
            }
        ]
        ```
    """
    orch = await orchestrator.__anext__()
    params = {"query": query}
    if library_key:
        params["library_key"] = library_key

    result = await orch.call_tool("plex", "search_media", params)
    return result if isinstance(result, list) else []


@router.get("/on-deck", tags=["media"])
async def get_on_deck(
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get on deck media items (continue watching).

    Returns:
        dict: On deck items

    Example:
        ```
        GET /api/v1/media/on-deck
        {
            "items": [...],
            "total": 5
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "get_on_deck", {})

    # Ensure consistent response format
    if isinstance(result, list):
        return {"items": result, "total": len(result)}
    return result


@router.get("/sessions", tags=["media"])
async def get_sessions(
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get active playback sessions.

    Returns information about currently playing media.

    Returns:
        dict: Active sessions

    Example:
        ```
        GET /api/v1/media/sessions
        {
            "sessions": [
                {
                    "user": "John",
                    "title": "The Matrix",
                    "state": "playing",
                    ...
                }
            ],
            "total": 2
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "get_sessions", {})

    # Ensure consistent response format
    if isinstance(result, list):
        return {"sessions": result, "total": len(result)}
    return result


@router.get("/server/status", tags=["media"])
async def get_server_status(
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get Plex server status and information.

    Returns:
        dict: Server status

    Example:
        ```
        GET /api/v1/media/server/status
        {
            "version": "1.32.0.6865",
            "platform": "Linux",
            "online": true,
            ...
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "get_server_status", {})
    return result


@router.post("/optimize/{rating_key}", tags=["media"])
async def optimize_item(
    rating_key: str,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Optimize a media item for streaming.

    Args:
        rating_key: Plex rating key of the media item

    Returns:
        dict: Optimization operation result

    Example:
        ```
        POST /api/v1/media/optimize/12345
        {
            "success": true,
            "message": "Optimization started"
        }
        ```
    """
    orch = await orchestrator.__anext__()
    result = await orch.call_tool("plex", "optimize_item", {"rating_key": rating_key})
    return result
