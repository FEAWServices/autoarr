"""
SABnzbd MCP Server.

This module implements the Model Context Protocol (MCP) server for SABnzbd,
exposing SABnzbd functionality as MCP tools that can be used by LLMs.
"""

import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import TextContent, Tool

from .client import SABnzbdClient, SABnzbdClientError


class SABnzbdMCPServer:
    """
    MCP Server for SABnzbd.

    This server exposes SABnzbd operations as MCP tools, allowing LLMs
    to interact with SABnzbd through the Model Context Protocol.

    Tools:
        - sabnzbd_get_queue: Get current download queue
        - sabnzbd_get_history: Get download history
        - sabnzbd_retry_download: Retry a failed download
        - sabnzbd_get_config: Get configuration
        - sabnzbd_set_config: Set configuration value
    """

    def __init__(self, client: SABnzbdClient) -> None:
        """
        Initialize the SABnzbd MCP server.

        Args:
            client: SABnzbd client instance

        Raises:
            ValueError: If client is None
        """
        if client is None:
            raise ValueError("SABnzbd client is required")

        self.client = client  # noqa: F841
        self.name = "sabnzbd"
        self.version = "0.1.0"
        self._server = Server(self.name)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self._server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return self._get_tools()

        @self._server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool by name with arguments."""
            return await self._call_tool(name, arguments)

    def _get_tools(self) -> List[Tool]:
        """
        Get list of available MCP tools.

        Returns:
            List of Tool objects with schemas
        """
        return [
            Tool(
                name="sabnzbd_get_queue",
                description="Get the current SABnzbd download queue with status and progress information",  # noqa: E501
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "integer",
                            "description": "Start index for pagination (default: 0)",
                            "default": 0,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (optional)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sabnzbd_get_history",
                description="Get SABnzbd download history including completed and failed downloads",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "integer",
                            "description": "Start index for pagination (default: 0)",
                            "default": 0,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (optional)",
                        },
                        "failed_only": {
                            "type": "boolean",
                            "description": "Return only failed downloads (default: false)",
                            "default": False,
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category (optional)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sabnzbd_retry_download",
                description="Retry a failed download by NZO ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": "The NZO ID of the failed download to retry",
                        },
                    },
                    "required": ["nzo_id"],
                },
            ),
            Tool(
                name="sabnzbd_get_config",
                description="Get SABnzbd configuration settings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Specific config section to retrieve (optional, returns all if not specified)",  # noqa: E501
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sabnzbd_set_config",
                description="Set a SABnzbd configuration value",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Configuration section (e.g., 'misc', 'servers')",
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Configuration key to set",
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to set",
                        },
                    },
                    "required": ["section", "keyword", "value"],
                },
            ),
        ]

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of TextContent responses
        """
        try:
            # Dispatch to appropriate handler
            if name == "sabnzbd_get_queue":
                result = await self._handle_get_queue(arguments)  # noqa: F841
            elif name == "sabnzbd_get_history":
                result = await self._handle_get_history(arguments)  # noqa: F841
            elif name == "sabnzbd_retry_download":
                result = await self._handle_retry_download(arguments)  # noqa: F841
            elif name == "sabnzbd_get_config":
                result = await self._handle_get_config(arguments)  # noqa: F841
            elif name == "sabnzbd_set_config":
                result = await self._handle_set_config(arguments)  # noqa: F841
            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"error": f"Unknown tool: {name}", "success": False},
                            indent=2,
                        ),
                    )
                ]

            # Format successful response
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except SABnzbdClientError as e:
            # Handle client errors
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": str(e), "success": False},
                        indent=2,
                    ),
                )
            ]
        except ValueError as e:
            # Handle validation errors
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Validation error: {e}", "success": False},
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            # Handle unexpected errors
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Unexpected error: {e}", "success": False},
                        indent=2,
                    ),
                )
            ]

    async def _handle_get_queue(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_queue tool execution."""
        start = arguments.get("start", 0)
        limit = arguments.get("limit")

        # Validate arguments
        if not isinstance(start, int) or start < 0:
            raise ValueError("start must be a non-negative integer")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("limit must be a positive integer")

        return await self.client.get_queue(start=start, limit=limit)

    async def _handle_get_history(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_history tool execution."""
        start = arguments.get("start", 0)
        limit = arguments.get("limit")
        failed_only = arguments.get("failed_only", False)
        category = arguments.get("category")

        # Validate arguments
        if not isinstance(start, int) or start < 0:
            raise ValueError("start must be a non-negative integer")
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("limit must be a positive integer")
        if not isinstance(failed_only, bool):
            raise ValueError("failed_only must be a boolean")

        return await self.client.get_history(
            start=start,
            limit=limit,
            failed_only=failed_only,
            category=category,
        )

    async def _handle_retry_download(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle retry_download tool execution."""
        nzo_id = arguments.get("nzo_id")

        # Validate required argument
        if not nzo_id or not isinstance(nzo_id, str) or not nzo_id.strip():
            raise ValueError("nzo_id is required and must be a non-empty string")

        return await self.client.retry_download(nzo_id=nzo_id)

    async def _handle_get_config(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_config tool execution."""
        section = arguments.get("section")

        return await self.client.get_config(section=section)

    async def _handle_set_config(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle set_config tool execution."""
        section = arguments.get("section")
        keyword = arguments.get("keyword")
        value = arguments.get("value")

        # Validate required arguments
        if not section or not isinstance(section, str) or not section.strip():
            raise ValueError("section is required and must be a non-empty string")
        if not keyword or not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("keyword is required and must be a non-empty string")
        if value is None:
            raise ValueError("value is required")

        return await self.client.set_config(
            section=section,
            keyword=keyword,
            value=value,
        )

    async def start(self) -> None:
        """
        Start the MCP server.

        This validates the connection to SABnzbd and prepares the server.
        """
        # Validate connection to SABnzbd
        is_healthy = await self.client.health_check()
        if not is_healthy:
            raise SABnzbdClientError("Failed to connect to SABnzbd")

    async def stop(self) -> None:
        """
        Stop the MCP server and cleanup resources.
        """
        await self.client.close()

    def list_tools(self) -> List[Tool]:
        """
        List all available tools (synchronous version).

        Returns:
            List of available tools
        """
        return self._get_tools()

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool (returns object for easier testing).

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result object
        """
        contents = await self._call_tool(name, arguments)

        # Parse the result for easier testing
        result_text = contents[0].text
        result_data = json.loads(result_text)

        # Create a simple result object
        class ToolResult:
            def __init__(self, data: Dict[str, Any]):
                self.content = contents
                self.isError = "error" in data

        return ToolResult(result_data)

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a specific tool by name.

        Args:
            name: Tool name

        Returns:
            Tool object or None if not found
        """
        tools = self._get_tools()
        for tool in tools:
            if tool.name == name:
                return tool
        return None
