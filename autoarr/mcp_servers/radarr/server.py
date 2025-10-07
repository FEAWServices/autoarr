"""
Radarr MCP Server.

This module implements the Model Context Protocol (MCP) server for Radarr,
exposing Radarr functionality as MCP tools that can be used by LLMs.
"""

import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .client import RadarrClient, RadarrClientError, RadarrConnectionError


class RadarrMCPServer:
    """
    MCP Server for Radarr.

    This server exposes Radarr operations as MCP tools, allowing LLMs
    to interact with Radarr through the Model Context Protocol.

    Tools:
        - radarr_get_movies: List all movies
        - radarr_get_movie_by_id: Get specific movie details
        - radarr_add_movie: Add a new movie
        - radarr_delete_movie: Delete a movie
        - radarr_search_movie_lookup: Search for movies
        - radarr_search_movie: Trigger movie search
        - radarr_get_queue: Get download queue
        - radarr_get_calendar: Get upcoming releases
        - radarr_get_wanted: Get missing/wanted movies
    """

    def __init__(self, client: RadarrClient) -> None:
        """
        Initialize the Radarr MCP server.

        Args:
            client: Radarr client instance

        Raises:
            ValueError: If client is None
        """
        if client is None:
            raise ValueError("Radarr client is required")

        self.client = client
        self.name = "radarr"
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
                name="radarr_get_movies",
                description="Get all movies from Radarr with optional pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of movies to return (optional)",
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
                name="radarr_get_movie_by_id",
                description="Get detailed information about a specific movie by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "integer",
                            "description": "The unique ID of the movie",
                        },
                    },
                    "required": ["movie_id"],
                },
            ),
            Tool(
                name="radarr_add_movie",
                description="Add a new movie to Radarr for monitoring and downloading",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the movie",
                        },
                        "tmdb_id": {
                            "type": "integer",
                            "description": "TMDb ID of the movie (required)",
                        },
                        "quality_profile_id": {
                            "type": "integer",
                            "description": "Quality profile ID to use (required)",
                        },
                        "root_folder_path": {
                            "type": "string",
                            "description": "Root folder path for the movie (required)",
                        },
                        "monitored": {
                            "type": "boolean",
                            "description": "Whether to monitor the movie (default: true)",
                            "default": True,
                        },
                        "minimum_availability": {
                            "type": "string",
                            "description": "Minimum availability (announced, inCinemas, released, preDB)",
                        },
                    },
                    "required": ["tmdb_id", "quality_profile_id", "root_folder_path"],
                },
            ),
            Tool(
                name="radarr_search_movie_lookup",
                description="Search for movies using TMDb lookup (use before adding)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term (movie title or tmdb:id or imdb:id)",
                        },
                    },
                    "required": ["term"],
                },
            ),
            Tool(
                name="radarr_search_movie",
                description="Trigger a search to download a specific movie",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "integer",
                            "description": "The movie ID to search for",
                        },
                    },
                    "required": ["movie_id"],
                },
            ),
            Tool(
                name="radarr_get_wanted",
                description="Get missing/wanted movies with pagination",
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
                    },
                    "required": [],
                },
            ),
            Tool(
                name="radarr_get_calendar",
                description="Get upcoming movie releases from the calendar",
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
                name="radarr_get_queue",
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
                name="radarr_delete_movie",
                description="Delete a movie from Radarr with optional file deletion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "integer",
                            "description": "The movie ID to delete",
                        },
                        "delete_files": {
                            "type": "boolean",
                            "description": "Whether to delete movie files (default: false)",
                            "default": False,
                        },
                        "add_import_exclusion": {
                            "type": "boolean",
                            "description": "Add to import exclusion list (optional)",
                        },
                    },
                    "required": ["movie_id"],
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
            if name == "radarr_get_movies":
                result = await self._handle_get_movies(arguments)
            elif name == "radarr_get_movie_by_id":
                result = await self._handle_get_movie_by_id(arguments)
            elif name == "radarr_add_movie":
                result = await self._handle_add_movie(arguments)
            elif name == "radarr_search_movie_lookup":
                result = await self._handle_search_movie_lookup(arguments)
            elif name == "radarr_search_movie":
                result = await self._handle_search_movie(arguments)
            elif name == "radarr_get_wanted":
                result = await self._handle_get_wanted(arguments)
            elif name == "radarr_get_calendar":
                result = await self._handle_get_calendar(arguments)
            elif name == "radarr_get_queue":
                result = await self._handle_get_queue(arguments)
            elif name == "radarr_delete_movie":
                result = await self._handle_delete_movie(arguments)
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

        except RadarrConnectionError as e:
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
        except RadarrClientError as e:
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

    async def _handle_get_movies(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle get_movies tool execution."""
        limit = arguments.get("limit")
        page = arguments.get("page")

        return await self.client.get_movies(limit=limit, page=page)

    async def _handle_get_movie_by_id(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_movie_by_id tool execution."""
        movie_id = arguments.get("movie_id")

        # Validate required argument
        if movie_id is None:
            raise ValueError("movie_id is required")
        if not isinstance(movie_id, int):
            raise ValueError("movie_id must be an integer")

        return await self.client.get_movie_by_id(movie_id=movie_id)

    async def _handle_add_movie(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_movie tool execution."""
        # Build movie data from arguments
        movie_data = {}

        # Optional title
        if "title" in arguments:
            movie_data["title"] = arguments["title"]

        # Required fields
        if "tmdb_id" in arguments:
            movie_data["tmdbId"] = arguments["tmdb_id"]
        if "quality_profile_id" in arguments:
            movie_data["qualityProfileId"] = arguments["quality_profile_id"]
        if "root_folder_path" in arguments:
            movie_data["rootFolderPath"] = arguments["root_folder_path"]

        # Optional fields
        if "monitored" in arguments:
            movie_data["monitored"] = arguments["monitored"]
        if "minimum_availability" in arguments:
            movie_data["minimumAvailability"] = arguments["minimum_availability"]

        return await self.client.add_movie(movie_data)

    async def _handle_search_movie_lookup(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle search_movie_lookup tool execution."""
        term = arguments.get("term")

        # Validate required argument
        if not term or not isinstance(term, str) or not term.strip():
            raise ValueError("term is required and must be a non-empty string")

        return await self.client.search_movie_lookup(term=term)

    async def _handle_search_movie(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_movie tool execution."""
        movie_id = arguments.get("movie_id")

        # Validate required argument
        if movie_id is None:
            raise ValueError("movie_id is required")
        if not isinstance(movie_id, int):
            raise ValueError("movie_id must be an integer")

        return await self.client.search_movie(movie_id=movie_id)

    async def _handle_get_wanted(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_wanted tool execution."""
        page = arguments.get("page")
        page_size = arguments.get("page_size")

        return await self.client.get_wanted_missing(page=page, page_size=page_size)

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

    async def _handle_delete_movie(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_movie tool execution."""
        movie_id = arguments.get("movie_id")
        delete_files = arguments.get("delete_files", False)
        add_import_exclusion = arguments.get("add_import_exclusion")

        # Validate required argument
        if movie_id is None:
            raise ValueError("movie_id is required")
        if not isinstance(movie_id, int):
            raise ValueError("movie_id must be an integer")

        result = await self.client.delete_movie(
            movie_id=movie_id,
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

        This validates the connection to Radarr and prepares the server.
        """
        # Validate connection to Radarr
        is_healthy = await self.client.health_check()
        if not is_healthy:
            raise RadarrClientError("Failed to connect to Radarr")

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
