"""
Sonarr MCP Server.

This module implements the Model Context Protocol (MCP) server for Sonarr,
exposing Sonarr functionality as MCP tools that can be used by LLMs.
"""

import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import TextContent, Tool

from .client import SonarrClient, SonarrClientError, SonarrConnectionError


class SonarrMCPServer:
    """
    MCP Server for Sonarr.

    This server exposes Sonarr operations as MCP tools, allowing LLMs
    to interact with Sonarr through the Model Context Protocol.

    Tools:
        - sonarr_get_series: List all TV series
        - sonarr_get_series_by_id: Get specific series details
        - sonarr_add_series: Add a new TV series
        - sonarr_delete_series: Delete a TV series
        - sonarr_search_series: Search for TV shows
        - sonarr_get_episodes: Get episodes for a series
        - sonarr_search_episode: Trigger episode search
        - sonarr_get_queue: Get download queue
        - sonarr_get_calendar: Get upcoming episodes
        - sonarr_get_wanted: Get missing/wanted episodes
    """

    def __init__(self, client: SonarrClient) -> None:
        """
        Initialize the Sonarr MCP server.

        Args:
            client: Sonarr client instance

        Raises:
            ValueError: If client is None
        """
        if client is None:
            raise ValueError("Sonarr client is required")

        self.client = client  # noqa: F841
        self.name = "sonarr"
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
                name="sonarr_get_series",
                description="Get all TV series from Sonarr with optional pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of series to return (optional)",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination (optional)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sonarr_get_series_by_id",
                description="Get detailed information about a specific TV series by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "series_id": {
                            "type": "integer",
                            "description": "The unique ID of the series",
                        },
                    },
                    "required": ["series_id"],
                },
            ),
            Tool(
                name="sonarr_add_series",
                description="Add a new TV series to Sonarr for monitoring and downloading",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the TV series",
                        },
                        "tvdb_id": {
                            "type": "integer",
                            "description": "TVDB ID of the series (required)",
                        },
                        "quality_profile_id": {
                            "type": "integer",
                            "description": "Quality profile ID to use (required)",
                        },
                        "root_folder_path": {
                            "type": "string",
                            "description": "Root folder path for the series (required)",
                        },
                        "monitored": {
                            "type": "boolean",
                            "description": "Whether to monitor the series (default: true)",
                            "default": True,
                        },
                        "season_folder": {
                            "type": "boolean",
                            "description": "Use season folders (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["tvdb_id", "quality_profile_id", "root_folder_path"],
                },
            ),
            Tool(
                name="sonarr_search_series",
                description="Search for TV series using TVDB lookup (use before adding)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term (series title or tvdb:id)",
                        },
                    },
                    "required": ["term"],
                },
            ),
            Tool(
                name="sonarr_get_episodes",
                description="Get episodes for a TV series with optional season filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "series_id": {
                            "type": "integer",
                            "description": "The series ID",
                        },
                        "season_number": {
                            "type": "integer",
                            "description": "Filter by season number (optional)",
                        },
                    },
                    "required": ["series_id"],
                },
            ),
            Tool(
                name="sonarr_search_episode",
                description="Trigger a search for a specific episode to download",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "episode_id": {
                            "type": "integer",
                            "description": "The episode ID to search for",
                        },
                    },
                    "required": ["episode_id"],
                },
            ),
            Tool(
                name="sonarr_get_wanted",
                description="Get missing/wanted episodes with pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination (default: 1)",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of items per page (default: 20)",
                        },
                        "include_series": {
                            "type": "boolean",
                            "description": "Include series information (optional)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sonarr_get_calendar",
                description="Get upcoming episodes from the calendar",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (optional)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (optional)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sonarr_get_queue",
                description="Get the current download queue with status and progress",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination (optional)",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of items per page (optional)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="sonarr_delete_series",
                description="Delete a TV series from Sonarr with optional file deletion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "series_id": {
                            "type": "integer",
                            "description": "The series ID to delete",
                        },
                        "delete_files": {
                            "type": "boolean",
                            "description": "Whether to delete series files (default: false)",
                            "default": False,
                        },
                        "add_import_exclusion": {
                            "type": "boolean",
                            "description": "Add to import exclusion list (optional)",
                        },
                    },
                    "required": ["series_id"],
                },
            ),
        ]

    async def _call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:  # noqa: C901, E501
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
            if name == "sonarr_get_series":
                result = await self._handle_get_series(arguments)  # noqa: F841
            elif name == "sonarr_get_series_by_id":
                result = await self._handle_get_series_by_id(arguments)  # noqa: F841
            elif name == "sonarr_add_series":
                result = await self._handle_add_series(arguments)  # noqa: F841
            elif name == "sonarr_search_series":
                result = await self._handle_search_series(arguments)  # noqa: F841
            elif name == "sonarr_get_episodes":
                result = await self._handle_get_episodes(arguments)  # noqa: F841
            elif name == "sonarr_search_episode":
                result = await self._handle_search_episode(arguments)  # noqa: F841
            elif name == "sonarr_get_wanted":
                result = await self._handle_get_wanted(arguments)  # noqa: F841
            elif name == "sonarr_get_calendar":
                result = await self._handle_get_calendar(arguments)  # noqa: F841
            elif name == "sonarr_get_queue":
                result = await self._handle_get_queue(arguments)  # noqa: F841
            elif name == "sonarr_delete_series":
                result = await self._handle_delete_series(arguments)  # noqa: F841
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

        except SonarrConnectionError as e:
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
        except SonarrClientError as e:
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

    async def _handle_get_series(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_series tool execution."""
        limit = arguments.get("limit")
        page = arguments.get("page")

        return await self.client.get_series(limit=limit, page=page)

    async def _handle_get_series_by_id(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_series_by_id tool execution."""
        series_id = arguments.get("series_id")

        # Validate required argument
        if series_id is None:
            raise ValueError("series_id is required")
        if not isinstance(series_id, int):
            raise ValueError("series_id must be an integer")

        return await self.client.get_series_by_id(series_id=series_id)

    async def _handle_add_series(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_series tool execution."""
        # Build series data from arguments
        series_data = {}

        # Optional title
        if "title" in arguments:
            series_data["title"] = arguments["title"]

        # Required fields
        if "tvdb_id" in arguments:
            series_data["tvdbId"] = arguments["tvdb_id"]
        if "quality_profile_id" in arguments:
            series_data["qualityProfileId"] = arguments["quality_profile_id"]
        if "root_folder_path" in arguments:
            series_data["rootFolderPath"] = arguments["root_folder_path"]

        # Optional fields
        if "monitored" in arguments:
            series_data["monitored"] = arguments["monitored"]
        if "season_folder" in arguments:
            series_data["seasonFolder"] = arguments["season_folder"]

        return await self.client.add_series(series_data)

    async def _handle_search_series(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle search_series tool execution."""
        term = arguments.get("term")

        # Validate required argument
        if not term or not isinstance(term, str) or not term.strip():
            raise ValueError("term is required and must be a non-empty string")

        return await self.client.search_series(term=term)

    async def _handle_get_episodes(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_episodes tool execution."""
        series_id = arguments.get("series_id")
        season_number = arguments.get("season_number")

        # Validate required argument
        if series_id is None:
            raise ValueError("series_id is required")
        if not isinstance(series_id, int):
            raise ValueError("series_id must be an integer")

        return await self.client.get_episodes(series_id=series_id, season_number=season_number)

    async def _handle_search_episode(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_episode tool execution."""
        episode_id = arguments.get("episode_id")

        # Validate required argument
        if episode_id is None:
            raise ValueError("episode_id is required")
        if not isinstance(episode_id, int):
            raise ValueError("episode_id must be an integer")

        return await self.client.search_episode(episode_id=episode_id)

    async def _handle_get_wanted(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_wanted tool execution."""
        page = arguments.get("page")
        page_size = arguments.get("page_size")
        include_series = arguments.get("include_series")

        return await self.client.get_wanted_missing(
            page=page, page_size=page_size, include_series=include_series
        )

    async def _handle_get_calendar(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_calendar tool execution."""
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")

        return await self.client.get_calendar(start_date=start_date, end_date=end_date)

    async def _handle_get_queue(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_queue tool execution."""
        page = arguments.get("page")
        page_size = arguments.get("page_size")

        return await self.client.get_queue(page=page, page_size=page_size)

    async def _handle_delete_series(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_series tool execution."""
        series_id = arguments.get("series_id")
        delete_files = arguments.get("delete_files", False)
        add_import_exclusion = arguments.get("add_import_exclusion")

        # Validate required argument
        if series_id is None:
            raise ValueError("series_id is required")
        if not isinstance(series_id, int):
            raise ValueError("series_id must be an integer")

        result = await self.client.delete_series(  # noqa: F841
            series_id=series_id,
            delete_files=delete_files,
            add_import_exclusion=add_import_exclusion,
        )

        # Return success indicator if result is empty
        if not result:
            return {"deleted": True}
        return result

    async def start(self) -> None:
        """
        Start the MCP server.

        This validates the connection to Sonarr and prepares the server.
        """
        # Validate connection to Sonarr
        is_healthy = await self.client.health_check()
        if not is_healthy:
            raise SonarrClientError("Failed to connect to Sonarr")

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
