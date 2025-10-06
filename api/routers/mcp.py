"""
MCP proxy endpoints.

This module provides endpoints for directly interacting with MCP tools,
allowing clients to call any tool on any server.
"""

from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends
from shared.core.mcp_orchestrator import MCPOrchestrator

from ..dependencies import get_orchestrator
from ..models import (
    BatchToolCallRequest,
    ToolCallRequest,
    ToolCallResponse,
    ToolListResponse,
)

router = APIRouter()


@router.post("/call", response_model=ToolCallResponse, tags=["mcp"])
async def call_tool(
    request: ToolCallRequest,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> ToolCallResponse:
    """
    Call a single MCP tool.

    Execute a tool on a specified MCP server with the given parameters.

    Args:
        request: Tool call request containing server, tool, and parameters

    Returns:
        ToolCallResponse: Tool execution result

    Example:
        ```
        POST /api/v1/mcp/call
        {
            "server": "sabnzbd",
            "tool": "get_queue",
            "params": {},
            "timeout": 30.0
        }
        ```

        Response:
        ```
        {
            "success": true,
            "data": {"queue": [...]},
            "error": null,
            "metadata": {
                "server": "sabnzbd",
                "tool": "get_queue",
                "duration": 0.123
            }
        }
        ```
    """
    # Resolve the async generator to get the orchestrator
    orch = await orchestrator.__anext__()

    try:
        # Call the tool with metadata
        result = await orch.call_tool(
            server=request.server,
            tool=request.tool,
            params=request.params,
            timeout=request.timeout,
            include_metadata=True,
        )

        # If result includes metadata, it's a dict with 'data' and 'metadata'
        if isinstance(result, dict) and "metadata" in result:
            return ToolCallResponse(
                success=True,
                data=result.get("data", {}),
                error=None,
                metadata=result.get("metadata", {}),
            )
        else:
            # Result is the raw data
            return ToolCallResponse(
                success=True,
                data=result if isinstance(result, dict) else {"result": result},
                error=None,
                metadata={
                    "server": request.server,
                    "tool": request.tool,
                },
            )

    except Exception as e:
        return ToolCallResponse(
            success=False,
            data=None,
            error=str(e),
            metadata={
                "server": request.server,
                "tool": request.tool,
            },
        )


@router.post("/batch", response_model=List[ToolCallResponse], tags=["mcp"])
async def call_tools_batch(
    request: BatchToolCallRequest,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> List[ToolCallResponse]:
    """
    Call multiple MCP tools in parallel.

    Execute multiple tools across different servers in parallel for improved performance.

    Args:
        request: Batch tool call request containing list of tool calls

    Returns:
        List[ToolCallResponse]: List of tool execution results in same order as input

    Example:
        ```
        POST /api/v1/mcp/batch
        {
            "calls": [
                {"server": "sabnzbd", "tool": "get_queue", "params": {}},
                {"server": "sonarr", "tool": "get_series", "params": {}}
            ],
            "return_partial": false
        }
        ```

        Response:
        ```
        [
            {
                "success": true,
                "data": {"queue": [...]},
                "error": null
            },
            {
                "success": true,
                "data": {"series": [...]},
                "error": null
            }
        ]
        ```
    """
    # Resolve the async generator to get the orchestrator
    orch = await orchestrator.__anext__()

    # Convert ToolCallRequest objects to MCPToolCall-like objects
    # The orchestrator expects objects with server, tool, params attributes
    class MCPToolCall:
        def __init__(self, server: str, tool: str, params: dict, timeout: float = None):
            self.server = server
            self.tool = tool
            self.params = params
            self.timeout = timeout

    tool_calls = [
        MCPToolCall(call.server, call.tool, call.params, call.timeout)
        for call in request.calls
    ]

    # Execute tools in parallel
    results = await orch.call_tools_parallel(
        calls=tool_calls,
        return_partial=request.return_partial,
    )

    # Convert results to ToolCallResponse objects
    responses = []
    for result in results:
        responses.append(
            ToolCallResponse(
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                metadata=None,
            )
        )

    return responses


@router.get("/tools", response_model=ToolListResponse, tags=["mcp"])
async def list_tools(
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> ToolListResponse:
    """
    List all available MCP tools.

    Get a list of all available tools grouped by server.

    Returns:
        ToolListResponse: Available tools grouped by server

    Example:
        ```
        GET /api/v1/mcp/tools
        {
            "tools": {
                "sabnzbd": ["get_queue", "get_history", "retry_download", "pause_queue"],
                "sonarr": ["get_series", "search_series", "get_calendar", "get_queue"],
                "radarr": ["get_movies", "search_movies", "get_calendar", "get_queue"],
                "plex": ["get_libraries", "get_recently_added", "scan_library"]
            }
        }
        ```
    """
    # Resolve the async generator to get the orchestrator
    orch = await orchestrator.__anext__()

    # Get all tools from all connected servers
    all_tools = await orch.list_all_tools()

    return ToolListResponse(tools=all_tools)


@router.get("/tools/{server}", tags=["mcp"])
async def list_server_tools(
    server: str,
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> dict:
    """
    List available tools for a specific server.

    Args:
        server: Server name (sabnzbd, sonarr, radarr, or plex)

    Returns:
        dict: List of available tools for the server

    Example:
        ```
        GET /api/v1/mcp/tools/sabnzbd
        {
            "server": "sabnzbd",
            "tools": ["get_queue", "get_history", "retry_download", "pause_queue"]
        }
        ```
    """
    # Resolve the async generator to get the orchestrator
    orch = await orchestrator.__anext__()

    # Get tools for specific server
    tools = await orch.list_tools(server)

    return {
        "server": server,
        "tools": tools,
    }


@router.get("/stats", tags=["mcp"])
async def get_stats(
    orchestrator: AsyncGenerator[MCPOrchestrator, None] = Depends(get_orchestrator),
) -> dict:
    """
    Get orchestrator statistics.

    Returns statistics about tool calls, health checks, and server usage.

    Returns:
        dict: Orchestrator statistics

    Example:
        ```
        GET /api/v1/mcp/stats
        {
            "total_calls": 150,
            "total_health_checks": 45,
            "calls_per_server": {
                "sabnzbd": 50,
                "sonarr": 60,
                "radarr": 40
            }
        }
        ```
    """
    # Resolve the async generator to get the orchestrator
    orch = await orchestrator.__anext__()

    # Get orchestrator statistics
    stats = orch.get_stats()

    return stats
