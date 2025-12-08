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
Radarr Tool Provider for AutoArr Chat Agent.

This module implements the BaseToolProvider interface for Radarr,
exposing Radarr API operations as tools for the LLM.
"""

import logging
from typing import Any, Dict, List, Optional

from autoarr.api.services.tool_provider import (
    BaseToolProvider,
    ServiceInfo,
    ToolDefinition,
    ToolResult,
)
from autoarr.mcp_servers.radarr.client import RadarrClient, RadarrClientError

logger = logging.getLogger(__name__)


class RadarrToolProvider(BaseToolProvider):
    """
    Tool provider for Radarr.

    Exposes Radarr API operations as tools that can be called by the LLM.
    Supports version-aware tool filtering for API compatibility.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Optional[RadarrClient] = None,
    ):
        """
        Initialize the Radarr tool provider.

        Args:
            url: Radarr URL (e.g., http://localhost:7878)
            api_key: Radarr API key
            client: Optional pre-configured RadarrClient
        """
        self._url = url
        self._api_key = api_key
        self._client = client
        self._version: Optional[str] = None
        self._connected = False

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return "radarr"

    async def _get_client(self) -> Optional[RadarrClient]:
        """Get or create the Radarr client."""
        if self._client:
            return self._client

        if not self._url or not self._api_key:
            # Try to get from database
            try:
                from autoarr.api.database import SettingsRepository, get_database

                db = get_database()
                repo = SettingsRepository(db)
                settings = await repo.get_service_settings("radarr")
                if settings and settings.enabled and settings.url:
                    self._url = settings.url
                    self._api_key = settings.api_key_or_token
                    logger.debug(f"Got Radarr settings from database: url={self._url}")
            except Exception as e:
                logger.warning(f"Failed to get Radarr settings from database: {e}")
                return None

        if self._url and self._api_key:
            self._client = RadarrClient(self._url, self._api_key)
            return self._client

        return None

    def get_tools(self, version: Optional[str] = None) -> List[ToolDefinition]:
        """
        Get available Radarr tools.

        Args:
            version: Radarr version for compatibility filtering

        Returns:
            List of ToolDefinition objects compatible with the version
        """
        tools = [
            # Core tools - Movie operations
            ToolDefinition(
                name="radarr_get_movies",
                description=(
                    "Get all movies from Radarr library. "
                    "Shows title, status, quality, and file information."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of movies to return",
                        },
                    },
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_movie_by_id",
                description="Get detailed information about a specific movie.",
                parameters={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "integer",
                            "description": "The unique ID of the movie",
                        },
                    },
                    "required": ["movie_id"],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_search_movie_lookup",
                description=(
                    "Search for movies using TMDb lookup. "
                    "Use this before adding a new movie to get the TMDb ID."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term (movie title, tmdb:id, or imdb:id)",
                        },
                    },
                    "required": ["term"],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_add_movie",
                description=(
                    "Add a new movie to Radarr for monitoring and downloading. "
                    "Requires TMDb ID from search."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "tmdb_id": {
                            "type": "integer",
                            "description": "TMDb ID of the movie (required)",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the movie",
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
                        },
                        "minimum_availability": {
                            "type": "string",
                            "description": "Minimum availability (announced/inCinemas/released)",
                        },
                    },
                    "required": ["tmdb_id", "quality_profile_id", "root_folder_path"],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_delete_movie",
                description=(
                    "Delete a movie from Radarr. "
                    "Optionally delete files and exclude from future imports."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "integer",
                            "description": "The movie ID to delete",
                        },
                        "delete_files": {
                            "type": "boolean",
                            "description": "Also delete movie files (default: false)",
                        },
                        "add_import_exclusion": {
                            "type": "boolean",
                            "description": "Add to import exclusion list",
                        },
                    },
                    "required": ["movie_id"],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_search_movie",
                description="Trigger a search for a specific movie to download.",
                parameters={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "integer",
                            "description": "The movie ID to search for",
                        },
                    },
                    "required": ["movie_id"],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            # Queue and calendar
            ToolDefinition(
                name="radarr_get_queue",
                description=("Get the current Radarr download queue with status and progress."),
                parameters={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of items per page",
                        },
                    },
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_calendar",
                description="Get upcoming movie releases from the calendar.",
                parameters={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)",
                        },
                    },
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_wanted",
                description="Get missing/wanted movies that need downloading.",
                parameters={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of items per page",
                        },
                    },
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            # System and health
            ToolDefinition(
                name="radarr_get_status",
                description="Get Radarr system status including version and health.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            # Configuration tools
            ToolDefinition(
                name="radarr_get_quality_profiles",
                description="List all configured quality profiles for movies.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_root_folders",
                description="List all configured root folders for movie storage.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_indexers",
                description="List all configured indexers for movie searching.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_download_clients",
                description="List all configured download clients.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="radarr_get_health",
                description="Get Radarr health check issues and warnings.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
            # Optimization assessment
            ToolDefinition(
                name="radarr_assess_optimization",
                description=(
                    "Assess Radarr configuration for optimization opportunities. "
                    "Returns a health check with recommendations for best practices."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="radarr",
                min_version="3.0.0",
            ),
        ]

        # Filter by version if provided
        use_version = version or self._version
        return list(self.filter_tools_by_version(tools, use_version))

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a Radarr tool.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            ToolResult with success status and data/error
        """
        client = await self._get_client()
        if not client:
            return ToolResult(
                success=False,
                error="Radarr is not configured. Please set up Radarr in Settings first.",
            )

        try:
            # Route to appropriate handler
            handlers = {
                "radarr_get_movies": self._handle_get_movies,
                "radarr_get_movie_by_id": self._handle_get_movie_by_id,
                "radarr_search_movie_lookup": self._handle_search_movie_lookup,
                "radarr_add_movie": self._handle_add_movie,
                "radarr_delete_movie": self._handle_delete_movie,
                "radarr_search_movie": self._handle_search_movie,
                "radarr_get_queue": self._handle_get_queue,
                "radarr_get_calendar": self._handle_get_calendar,
                "radarr_get_wanted": self._handle_get_wanted,
                "radarr_get_status": self._handle_get_status,
                "radarr_get_quality_profiles": self._handle_get_quality_profiles,
                "radarr_get_root_folders": self._handle_get_root_folders,
                "radarr_get_indexers": self._handle_get_indexers,
                "radarr_get_download_clients": self._handle_get_download_clients,
                "radarr_get_health": self._handle_get_health,
                "radarr_assess_optimization": self._handle_assess_optimization,
            }

            handler = handlers.get(tool_name)
            if not handler:
                return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

            data = await handler(client, arguments)
            return ToolResult(success=True, data=data)

        except RadarrClientError as e:
            logger.error(f"Radarr client error: {e}")
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(success=False, error=f"Execution failed: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Radarr is available."""
        client = await self._get_client()
        if not client:
            return False

        try:
            result = await client.health_check()
            return bool(result)
        except Exception:
            return False

    async def get_service_info(self) -> ServiceInfo:
        """Get Radarr service information."""
        client = await self._get_client()
        if not client:
            return ServiceInfo(
                name="radarr",
                connected=False,
                healthy=False,
            )

        try:
            # Get version
            status = await client.get_system_status()
            version = status.get("version", "unknown")

            # Check health
            healthy = await client.health_check()

            return ServiceInfo(
                name="radarr",
                version=version,
                connected=True,
                healthy=healthy,
                url=self._url,
                capabilities=["movies", "queue", "calendar", "search"],
            )
        except Exception as e:
            logger.warning(f"Failed to get Radarr info: {e}")
            return ServiceInfo(
                name="radarr",
                connected=False,
                healthy=False,
            )

    # Handler methods
    async def _handle_get_movies(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_movies tool."""
        movies = await client.get_movies(limit=args.get("limit"))
        return {"movie_count": len(movies), "movies": movies}

    async def _handle_get_movie_by_id(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_movie_by_id tool."""
        movie_id = args.get("movie_id")
        if movie_id is None:
            raise ValueError("movie_id is required")
        return await client.get_movie_by_id(movie_id)

    async def _handle_search_movie_lookup(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle search_movie_lookup tool."""
        term = args.get("term")
        if not term:
            raise ValueError("term is required")
        results = await client.search_movie_lookup(term)
        return {"result_count": len(results), "results": results}

    async def _handle_add_movie(self, client: RadarrClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_movie tool."""
        movie_data = {
            "tmdbId": args.get("tmdb_id"),
            "qualityProfileId": args.get("quality_profile_id"),
            "rootFolderPath": args.get("root_folder_path"),
            "monitored": args.get("monitored", True),
        }
        if args.get("title"):
            movie_data["title"] = args["title"]
        if args.get("minimum_availability"):
            movie_data["minimumAvailability"] = args["minimum_availability"]
        return await client.add_movie(movie_data)

    async def _handle_delete_movie(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle delete_movie tool."""
        movie_id = args.get("movie_id")
        if movie_id is None:
            raise ValueError("movie_id is required")
        result = await client.delete_movie(
            movie_id,
            delete_files=args.get("delete_files", False),
            add_import_exclusion=args.get("add_import_exclusion"),
        )
        return {"deleted": True, "result": result}

    async def _handle_search_movie(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle search_movie tool."""
        movie_id = args.get("movie_id")
        if movie_id is None:
            raise ValueError("movie_id is required")
        return await client.search_movie(movie_id)

    async def _handle_get_queue(self, client: RadarrClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_queue tool."""
        return await client.get_queue(page=args.get("page"), page_size=args.get("page_size"))

    async def _handle_get_calendar(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_calendar tool."""
        movies = await client.get_calendar(
            start_date=args.get("start_date"), end_date=args.get("end_date")
        )
        return {"movie_count": len(movies), "movies": movies}

    async def _handle_get_wanted(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_wanted tool."""
        return await client.get_wanted_missing(
            page=args.get("page"), page_size=args.get("page_size")
        )

    async def _handle_get_status(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_status tool."""
        return await client.get_system_status()

    async def _handle_get_quality_profiles(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_quality_profiles tool."""
        profiles = await client._request("GET", "qualityprofile")
        return {"profile_count": len(profiles), "profiles": profiles}

    async def _handle_get_root_folders(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_root_folders tool."""
        folders = await client._request("GET", "rootfolder")
        return {"folder_count": len(folders), "folders": folders}

    async def _handle_get_indexers(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_indexers tool."""
        indexers = await client._request("GET", "indexer")
        return {"indexer_count": len(indexers), "indexers": indexers}

    async def _handle_get_download_clients(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_download_clients tool."""
        clients = await client._request("GET", "downloadclient")
        return {"client_count": len(clients), "clients": clients}

    async def _handle_get_health(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_health tool."""
        health = await client._request("GET", "health")
        return {"issue_count": len(health), "issues": health}

    async def _handle_assess_optimization(
        self, client: RadarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess Radarr configuration for optimization opportunities.

        Returns a comprehensive health check with best practices.
        """
        checks: List[Dict[str, Any]] = []

        # Get system status
        try:
            status = await client.get_system_status()
            version = status.get("version", "unknown")
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get system status: {e}",
                "checks": [],
            }

        # Get health issues from Radarr's built-in health check
        try:
            health_issues = await client._request("GET", "health")
        except Exception:
            health_issues = []

        # Get configuration data
        try:
            indexers = await client._request("GET", "indexer")
            download_clients = await client._request("GET", "downloadclient")
            root_folders = await client._request("GET", "rootfolder")
            quality_profiles = await client._request("GET", "qualityprofile")
            movies = await client.get_movies()
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get configuration: {e}",
                "checks": [],
            }

        # ================================================================
        # CRITICAL CHECKS
        # ================================================================

        # Check: No indexers configured
        enabled_indexers = [i for i in indexers if i.get("enable", True)]
        if not enabled_indexers:
            checks.append(
                {
                    "id": "no_indexers",
                    "category": "connection",
                    "status": "critical",
                    "title": "No Indexers Configured",
                    "description": "No indexers configured. Movie searches will not work.",
                    "recommendation": "Add at least one indexer in Settings > Indexers.",
                    "current_value": "0 indexers",
                    "optimal_value": "1+ indexers",
                    "auto_fix": False,
                }
            )
        else:
            checks.append(
                {
                    "id": "indexers_configured",
                    "category": "connection",
                    "status": "good",
                    "title": "Indexers Configured",
                    "description": f"{len(enabled_indexers)} indexer(s) configured and enabled.",
                    "current_value": f"{len(enabled_indexers)} enabled",
                    "optimal_value": "1+ enabled",
                    "auto_fix": False,
                }
            )

        # Check: No download clients
        enabled_clients = [c for c in download_clients if c.get("enable", True)]
        if not enabled_clients:
            checks.append(
                {
                    "id": "no_download_clients",
                    "category": "connection",
                    "status": "critical",
                    "title": "No Download Clients Configured",
                    "description": "Radarr has no download clients. Downloads will not work.",
                    "recommendation": "Add a download client in Settings > Download Clients.",
                    "current_value": "0 clients",
                    "optimal_value": "1+ clients",
                    "auto_fix": False,
                }
            )
        else:
            checks.append(
                {
                    "id": "download_clients_configured",
                    "category": "connection",
                    "status": "good",
                    "title": "Download Clients Configured",
                    "description": f"{len(enabled_clients)} download client(s) configured.",
                    "current_value": f"{len(enabled_clients)} enabled",
                    "optimal_value": "1+ enabled",
                    "auto_fix": False,
                }
            )

        # Check: No root folders
        if not root_folders:
            checks.append(
                {
                    "id": "no_root_folders",
                    "category": "configuration",
                    "status": "critical",
                    "title": "No Root Folders Configured",
                    "description": "No root folders for movie storage.",
                    "recommendation": "Add a root folder in Settings > Media Management.",
                    "current_value": "0 folders",
                    "optimal_value": "1+ folders",
                    "auto_fix": False,
                }
            )
        else:
            # Check root folder disk space
            for folder in root_folders:
                free_space = folder.get("freeSpace", 0)
                free_gb = free_space / (1024 * 1024 * 1024)
                if free_gb < 20:  # Movies need more space than TV
                    checks.append(
                        {
                            "id": f"low_disk_space_{folder.get('id', 0)}",
                            "category": "storage",
                            "status": "warning" if free_gb >= 10 else "critical",
                            "title": f"Low Disk Space: {folder.get('path', 'Unknown')}",
                            "description": f"Only {free_gb:.1f} GB free space remaining.",
                            "recommendation": "Free up disk space. Movies need 5-50 GB each.",
                            "current_value": f"{free_gb:.1f} GB",
                            "optimal_value": "100+ GB",
                            "auto_fix": False,
                        }
                    )
                else:
                    checks.append(
                        {
                            "id": f"disk_space_ok_{folder.get('id', 0)}",
                            "category": "storage",
                            "status": "good",
                            "title": f"Disk Space OK: {folder.get('path', 'Unknown')}",
                            "description": f"{free_gb:.1f} GB free space available.",
                            "current_value": f"{free_gb:.1f} GB",
                            "optimal_value": "100+ GB",
                            "auto_fix": False,
                        }
                    )

        # ================================================================
        # HEALTH CHECKS FROM RADARR
        # ================================================================

        for issue in health_issues:
            source = issue.get("source", "Unknown")
            issue_type = issue.get("type", "warning")
            message = issue.get("message", "Unknown issue")
            wiki_url = issue.get("wikiUrl", "")

            status = "warning" if issue_type.lower() == "warning" else "critical"
            checks.append(
                {
                    "id": f"health_{source.lower().replace(' ', '_')}",
                    "category": "health",
                    "status": status,
                    "title": source,
                    "description": message,
                    "recommendation": (
                        f"See Radarr wiki: {wiki_url}" if wiki_url else "Check Radarr logs."
                    ),
                    "current_value": "Issue detected",
                    "optimal_value": "No issues",
                    "auto_fix": False,
                }
            )

        # ================================================================
        # LIBRARY CHECKS
        # ================================================================

        if movies:
            # Count unmonitored movies
            unmonitored = [m for m in movies if not m.get("monitored", True)]
            if len(unmonitored) > len(movies) * 0.5:
                checks.append(
                    {
                        "id": "many_unmonitored",
                        "category": "library",
                        "status": "recommendation",
                        "title": "Many Unmonitored Movies",
                        "description": f"{len(unmonitored)}/{len(movies)} movies unmonitored.",
                        "recommendation": "Review unmonitored movies and enable if wanted.",
                        "current_value": f"{len(unmonitored)} unmonitored",
                        "optimal_value": "Monitor wanted movies",
                        "auto_fix": False,
                    }
                )

            # Check for movies without files
            movies_without_files = [m for m in movies if not m.get("hasFile", False)]
            monitored_without_files = [m for m in movies_without_files if m.get("monitored", True)]
            if monitored_without_files:
                checks.append(
                    {
                        "id": "movies_missing_files",
                        "category": "library",
                        "status": "recommendation",
                        "title": "Monitored Movies Without Files",
                        "description": f"{len(monitored_without_files)} monitored movies missing files.",
                        "recommendation": "Search for missing movies or check availability.",
                        "current_value": f"{len(monitored_without_files)} missing",
                        "optimal_value": "All monitored movies downloaded",
                        "auto_fix": False,
                    }
                )
        else:
            checks.append(
                {
                    "id": "no_movies",
                    "category": "library",
                    "status": "recommendation",
                    "title": "No Movies Added",
                    "description": "Your Radarr library is empty.",
                    "recommendation": "Add movies to start monitoring and downloading.",
                    "current_value": "0 movies",
                    "optimal_value": "1+ movies",
                    "auto_fix": False,
                }
            )

        # ================================================================
        # QUALITY PROFILE CHECKS
        # ================================================================

        if not quality_profiles:
            checks.append(
                {
                    "id": "no_quality_profiles",
                    "category": "configuration",
                    "status": "warning",
                    "title": "No Quality Profiles",
                    "description": "No quality profiles configured.",
                    "recommendation": "Configure quality profiles for preferred quality.",
                    "current_value": "0 profiles",
                    "optimal_value": "1+ profiles",
                    "auto_fix": False,
                }
            )

        # ================================================================
        # CALCULATE OVERALL SCORE
        # ================================================================

        critical_count = len([c for c in checks if c["status"] == "critical"])
        warning_count = len([c for c in checks if c["status"] == "warning"])
        recommendation_count = len([c for c in checks if c["status"] == "recommendation"])
        good_count = len([c for c in checks if c["status"] == "good"])

        total_checks = len(checks)
        score_sum = (
            good_count * 100 + recommendation_count * 75 + warning_count * 50 + critical_count * 0
        )
        overall_score = round(score_sum / total_checks) if total_checks > 0 else 0

        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        elif recommendation_count > 0:
            overall_status = "good"
        else:
            overall_status = "excellent"

        return {
            "service": "radarr",
            "version": version,
            "overall_status": overall_status,
            "overall_score": overall_score,
            "summary": {
                "total_checks": total_checks,
                "critical": critical_count,
                "warnings": warning_count,
                "recommendations": recommendation_count,
                "good": good_count,
            },
            "checks": checks,
        }
