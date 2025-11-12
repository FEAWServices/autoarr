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
Plex MCP Server.

This module implements the Model Context Protocol (MCP) server for Plex Media Server,
exposing Plex functionality as MCP tools that can be used by LLMs.
"""

import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import TextContent, Tool

from .client import PlexClient, PlexClientError, PlexConnectionError


class PlexMCPServer:
    """
    MCP Server for Plex Media Server.

    This server exposes Plex operations as MCP tools, allowing LLMs
    to interact with Plex through the Model Context Protocol.

    Tools:
        - plex_get_libraries: List all library sections
        - plex_get_library_items: Get items in a library
        - plex_get_recently_added: Recently added content
        - plex_get_on_deck: On Deck (continue watching) items
        - plex_get_sessions: Currently playing sessions
        - plex_search: Search for content
        - plex_refresh_library: Trigger library scan
        - plex_get_history: Watch history
    """

    def __init__(self, client: PlexClient) -> None:
        """
        Initialize the Plex MCP server.

        Args:
            client: Plex client instance

        Raises:
            ValueError: If client is None
        """
        if client is None:
            raise ValueError("Plex client is required")

        self.client = client  # noqa: F841
        self.name = "plex"
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
                name="plex_get_libraries",
                description="List all Plex library sections (Movies, TV Shows, Music, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="plex_get_library_items",
                description="Get all items in a specific Plex library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "library_id": {
                            "type": "string",
                            "description": "The library section ID/key",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (optional)",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of items to skip for pagination (optional)",
                        },
                    },
                    "required": ["library_id"],
                },
            ),
            Tool(
                name="plex_get_recently_added",
                description="Get recently added content across all libraries",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (optional, default: 50)",  # noqa: E501
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="plex_get_on_deck",
                description="Get On Deck items (continue watching) for resuming playback",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (optional, default: 12)",  # noqa: E501
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="plex_get_sessions",
                description="Get currently playing sessions and active streams",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="plex_search",
                description="Search for content across all libraries or within a specific library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (optional)",
                        },
                        "section_id": {
                            "type": "string",
                            "description": "Limit search to specific library section ID (optional)",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="plex_refresh_library",
                description="Trigger a library refresh/scan to update content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "library_id": {
                            "type": "string",
                            "description": "The library section ID/key to refresh",
                        },
                    },
                    "required": ["library_id"],
                },
            ),
            Tool(
                name="plex_get_history",
                description="Get watch history for all users",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (optional, default: 50)",  # noqa: E501
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of items to skip for pagination (optional)",
                        },
                    },
                    "required": [],
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
            if name == "plex_get_libraries":
                result = await self._handle_get_libraries(arguments)  # noqa: F841
            elif name == "plex_get_library_items":
                result = await self._handle_get_library_items(arguments)  # noqa: F841
            elif name == "plex_get_recently_added":
                result = await self._handle_get_recently_added(arguments)  # noqa: F841
            elif name == "plex_get_on_deck":
                result = await self._handle_get_on_deck(arguments)  # noqa: F841
            elif name == "plex_get_sessions":
                result = await self._handle_get_sessions(arguments)  # noqa: F841
            elif name == "plex_search":
                result = await self._handle_search(arguments)  # noqa: F841
            elif name == "plex_refresh_library":
                result = await self._handle_refresh_library(arguments)  # noqa: F841
            elif name == "plex_get_history":
                result = await self._handle_get_history(arguments)  # noqa: F841
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
            response_data = {"success": True, "data": result}
            return [TextContent(type="text", text=json.dumps(response_data, indent=2))]

        except PlexConnectionError as e:
            # Handle connection errors
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": f"Connection error: {e}", "success": False},
                        indent=2,
                    ),
                )
            ]
        except PlexClientError as e:
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

    async def _handle_get_libraries(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_libraries tool execution."""
        return await self.client.get_libraries()

    async def _handle_get_library_items(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_library_items tool execution."""
        library_id = arguments.get("library_id")
        limit = arguments.get("limit")
        offset = arguments.get("offset")

        # Validate required argument
        if not library_id or not isinstance(library_id, str) or not library_id.strip():
            raise ValueError("library_id is required and must be a non-empty string")

        return await self.client.get_library_items(
            library_id=library_id,
            limit=limit,
            offset=offset,
        )

    async def _handle_get_recently_added(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_recently_added tool execution."""
        limit = arguments.get("limit")

        return await self.client.get_recently_added(limit=limit)

    async def _handle_get_on_deck(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_on_deck tool execution."""
        limit = arguments.get("limit")

        return await self.client.get_on_deck(limit=limit)

    async def _handle_get_sessions(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_sessions tool execution."""
        return await self.client.get_sessions()

    async def _handle_search(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle search tool execution."""
        query = arguments.get("query")
        limit = arguments.get("limit")
        section_id = arguments.get("section_id")

        # Validate required argument
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("query is required and must be a non-empty string")

        return await self.client.search(
            query=query,
            limit=limit,
            section_id=section_id,
        )

    async def _handle_refresh_library(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refresh_library tool execution."""
        library_id = arguments.get("library_id")

        # Validate required argument
        if not library_id or not isinstance(library_id, str) or not library_id.strip():
            raise ValueError("library_id is required and must be a non-empty string")

        return await self.client.refresh_library(library_id=library_id)

    async def _handle_get_history(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_history tool execution."""
        limit = arguments.get("limit")
        offset = arguments.get("offset")

        return await self.client.get_history(
            limit=limit,
            offset=offset,
        )

    async def start(self) -> None:
        """
        Start the MCP server.

        This validates the connection to Plex and prepares the server.
        """
        # Validate connection to Plex
        is_healthy = await self.client.health_check()
        if not is_healthy:
            raise PlexClientError("Failed to connect to Plex Media Server")

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
