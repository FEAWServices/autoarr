"""
Downloads endpoints (SABnzbd).

This module provides endpoints for managing downloads via SABnzbd.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator

router = APIRouter()


@router.get("/queue", tags=["downloads"])
async def get_download_queue(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get SABnzbd download queue.

    Returns the current download queue with all active downloads.

    Returns:
        dict: Download queue information

    Example:
        ```
        GET /api/v1/downloads/queue
        {
            "queue": [...],
            "speed": "5.2 MB/s",
            "size_left": "1.2 GB",
            "paused": false
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "get_queue", {})
    return result


@router.get("/history", tags=["downloads"])
async def get_download_history(
    limit: int = 50,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get SABnzbd download history.

    Args:
        limit: Maximum number of history items to return (default: 50)

    Returns:
        dict: Download history

    Example:
        ```
        GET /api/v1/downloads/history?limit=20
        {
            "history": [...],
            "total": 150
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "get_history", {"limit": limit})
    return result


@router.post("/retry/{nzo_id}", tags=["downloads"])
async def retry_download(
    nzo_id: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Retry a failed download.

    Args:
        nzo_id: NZB ID to retry

    Returns:
        dict: Retry operation result

    Example:
        ```
        POST /api/v1/downloads/retry/SABnzbd_nzo_abc123
        {
            "success": true,
            "message": "Download retried successfully"
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "retry_download", {"nzo_id": nzo_id})
    return result


@router.post("/pause", tags=["downloads"])
async def pause_queue(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Pause the download queue.

    Returns:
        dict: Pause operation result

    Example:
        ```
        POST /api/v1/downloads/pause
        {
            "success": true,
            "paused": true
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "pause_queue", {})
    return result


@router.post("/resume", tags=["downloads"])
async def resume_queue(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Resume the download queue.

    Returns:
        dict: Resume operation result

    Example:
        ```
        POST /api/v1/downloads/resume
        {
            "success": true,
            "paused": false
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "resume_queue", {})
    return result


@router.delete("/{nzo_id}", tags=["downloads"])
async def delete_download(
    nzo_id: str,
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Delete a download from the queue.

    Args:
        nzo_id: NZB ID to delete

    Returns:
        dict: Delete operation result

    Example:
        ```
        DELETE /api/v1/downloads/SABnzbd_nzo_abc123
        {
            "success": true,
            "message": "Download deleted successfully"
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "delete_download", {"nzo_id": nzo_id})
    return result


@router.get("/status", tags=["downloads"])
async def get_status(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get SABnzbd status.

    Returns overall status including speed, queue size, and more.

    Returns:
        dict: SABnzbd status

    Example:
        ```
        GET /api/v1/downloads/status
        {
            "paused": false,
            "speed": "5.2 MB/s",
            "queue_size": "1.2 GB",
            "disk_free": "500 GB"
        }
        ```
    """
    result = await orchestrator.call_tool("sabnzbd", "get_status", {})
    return result
