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
Sonarr Tool Provider for AutoArr Chat Agent.

This module implements the BaseToolProvider interface for Sonarr,
exposing Sonarr API operations as tools for the LLM.
"""

import logging
from typing import Any, Dict, List, Optional

from autoarr.api.services.tool_provider import (
    BaseToolProvider,
    ServiceInfo,
    ToolDefinition,
    ToolResult,
)
from autoarr.mcp_servers.sonarr.client import SonarrClient, SonarrClientError

logger = logging.getLogger(__name__)


class SonarrToolProvider(BaseToolProvider):
    """
    Tool provider for Sonarr.

    Exposes Sonarr API operations as tools that can be called by the LLM.
    Supports version-aware tool filtering for API compatibility.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Optional[SonarrClient] = None,
    ):
        """
        Initialize the Sonarr tool provider.

        Args:
            url: Sonarr URL (e.g., http://localhost:8989)
            api_key: Sonarr API key
            client: Optional pre-configured SonarrClient
        """
        self._url = url
        self._api_key = api_key
        self._client = client
        self._version: Optional[str] = None
        self._connected = False

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return "sonarr"

    async def _get_client(self) -> Optional[SonarrClient]:
        """Get or create the Sonarr client."""
        if self._client:
            return self._client

        if not self._url or not self._api_key:
            # Try to get from database
            try:
                from autoarr.api.database import SettingsRepository, get_database

                db = get_database()
                repo = SettingsRepository(db)
                settings = await repo.get_service_settings("sonarr")
                if settings and settings.enabled and settings.url:
                    self._url = settings.url
                    self._api_key = settings.api_key_or_token
                    logger.debug(f"Got Sonarr settings from database: url={self._url}")
            except Exception as e:
                logger.warning(f"Failed to get Sonarr settings from database: {e}")
                return None

        if self._url and self._api_key:
            self._client = SonarrClient(self._url, self._api_key)
            return self._client

        return None

    def get_tools(self, version: Optional[str] = None) -> List[ToolDefinition]:
        """
        Get available Sonarr tools.

        Args:
            version: Sonarr version for compatibility filtering

        Returns:
            List of ToolDefinition objects compatible with the version
        """
        tools = [
            # Core tools - Series operations
            ToolDefinition(
                name="sonarr_get_series",
                description=(
                    "Get all TV series from Sonarr library. "
                    "Shows title, status, season count, and episode progress."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of series to return",
                        },
                    },
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_series_by_id",
                description="Get detailed information about a specific TV series.",
                parameters={
                    "type": "object",
                    "properties": {
                        "series_id": {
                            "type": "integer",
                            "description": "The unique ID of the series",
                        },
                    },
                    "required": ["series_id"],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_search_series",
                description=(
                    "Search for TV series using TVDB lookup. "
                    "Use this before adding a new series to get the TVDB ID."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term (series title or tvdb:id)",
                        },
                    },
                    "required": ["term"],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_add_series",
                description=(
                    "Add a new TV series to Sonarr for monitoring and downloading. "
                    "Requires TVDB ID from search."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "tvdb_id": {
                            "type": "integer",
                            "description": "TVDB ID of the series (required)",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the TV series",
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
                        },
                        "season_folder": {
                            "type": "boolean",
                            "description": "Use season folders (default: true)",
                        },
                    },
                    "required": ["tvdb_id", "quality_profile_id", "root_folder_path"],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_delete_series",
                description=(
                    "Delete a TV series from Sonarr. "
                    "Optionally delete files and exclude from future imports."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "series_id": {
                            "type": "integer",
                            "description": "The series ID to delete",
                        },
                        "delete_files": {
                            "type": "boolean",
                            "description": "Also delete series files (default: false)",
                        },
                        "add_import_exclusion": {
                            "type": "boolean",
                            "description": "Add to import exclusion list",
                        },
                    },
                    "required": ["series_id"],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            # Episode operations
            ToolDefinition(
                name="sonarr_get_episodes",
                description="Get episodes for a specific TV series.",
                parameters={
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
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_search_episode",
                description="Trigger a search for a specific episode to download.",
                parameters={
                    "type": "object",
                    "properties": {
                        "episode_id": {
                            "type": "integer",
                            "description": "The episode ID to search for",
                        },
                    },
                    "required": ["episode_id"],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_search_series_command",
                description="Trigger a search for all episodes in a series.",
                parameters={
                    "type": "object",
                    "properties": {
                        "series_id": {
                            "type": "integer",
                            "description": "The series ID to search",
                        },
                    },
                    "required": ["series_id"],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            # Queue and calendar
            ToolDefinition(
                name="sonarr_get_queue",
                description=("Get the current Sonarr download queue with status and progress."),
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
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_calendar",
                description="Get upcoming episodes from the calendar.",
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
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_wanted",
                description="Get missing/wanted episodes that need downloading.",
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
                service="sonarr",
                min_version="3.0.0",
            ),
            # System and health
            ToolDefinition(
                name="sonarr_get_status",
                description="Get Sonarr system status including version and health.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            # Configuration tools
            ToolDefinition(
                name="sonarr_get_quality_profiles",
                description="List all configured quality profiles for series.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_root_folders",
                description="List all configured root folders for series storage.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_indexers",
                description="List all configured indexers for episode searching.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_download_clients",
                description="List all configured download clients.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            ToolDefinition(
                name="sonarr_get_health",
                description="Get Sonarr health check issues and warnings.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
            # Optimization assessment
            ToolDefinition(
                name="sonarr_assess_optimization",
                description=(
                    "Assess Sonarr configuration for optimization opportunities. "
                    "Returns a health check with recommendations for best practices."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sonarr",
                min_version="3.0.0",
            ),
        ]

        # Filter by version if provided
        use_version = version or self._version
        return list(self.filter_tools_by_version(tools, use_version))

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a Sonarr tool.

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
                error="Sonarr is not configured. Please set up Sonarr in Settings first.",
            )

        try:
            # Route to appropriate handler
            handlers = {
                "sonarr_get_series": self._handle_get_series,
                "sonarr_get_series_by_id": self._handle_get_series_by_id,
                "sonarr_search_series": self._handle_search_series,
                "sonarr_add_series": self._handle_add_series,
                "sonarr_delete_series": self._handle_delete_series,
                "sonarr_get_episodes": self._handle_get_episodes,
                "sonarr_search_episode": self._handle_search_episode,
                "sonarr_search_series_command": self._handle_search_series_command,
                "sonarr_get_queue": self._handle_get_queue,
                "sonarr_get_calendar": self._handle_get_calendar,
                "sonarr_get_wanted": self._handle_get_wanted,
                "sonarr_get_status": self._handle_get_status,
                "sonarr_get_quality_profiles": self._handle_get_quality_profiles,
                "sonarr_get_root_folders": self._handle_get_root_folders,
                "sonarr_get_indexers": self._handle_get_indexers,
                "sonarr_get_download_clients": self._handle_get_download_clients,
                "sonarr_get_health": self._handle_get_health,
                "sonarr_assess_optimization": self._handle_assess_optimization,
            }

            handler = handlers.get(tool_name)
            if not handler:
                return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

            data = await handler(client, arguments)
            return ToolResult(success=True, data=data)

        except SonarrClientError as e:
            logger.error(f"Sonarr client error: {e}")
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(success=False, error=f"Execution failed: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Sonarr is available."""
        client = await self._get_client()
        if not client:
            return False

        try:
            result = await client.health_check()
            return bool(result)
        except Exception:
            return False

    async def get_service_info(self) -> ServiceInfo:
        """Get Sonarr service information."""
        client = await self._get_client()
        if not client:
            return ServiceInfo(
                name="sonarr",
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
                name="sonarr",
                version=version,
                connected=True,
                healthy=healthy,
                url=self._url,
                capabilities=["series", "episodes", "queue", "calendar", "search"],
            )
        except Exception as e:
            logger.warning(f"Failed to get Sonarr info: {e}")
            return ServiceInfo(
                name="sonarr",
                connected=False,
                healthy=False,
            )

    # Handler methods
    async def _handle_get_series(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_series tool."""
        series = await client.get_series(limit=args.get("limit"))
        return {"series_count": len(series), "series": series}

    async def _handle_get_series_by_id(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_series_by_id tool."""
        series_id = args.get("series_id")
        if series_id is None:
            raise ValueError("series_id is required")
        return await client.get_series_by_id(series_id)

    async def _handle_search_series(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle search_series tool."""
        term = args.get("term")
        if not term:
            raise ValueError("term is required")
        results = await client.search_series(term)
        return {"result_count": len(results), "results": results}

    async def _handle_add_series(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle add_series tool."""
        series_data = {
            "tvdbId": args.get("tvdb_id"),
            "qualityProfileId": args.get("quality_profile_id"),
            "rootFolderPath": args.get("root_folder_path"),
            "monitored": args.get("monitored", True),
            "seasonFolder": args.get("season_folder", True),
        }
        if args.get("title"):
            series_data["title"] = args["title"]
        return await client.add_series(series_data)

    async def _handle_delete_series(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle delete_series tool."""
        series_id = args.get("series_id")
        if series_id is None:
            raise ValueError("series_id is required")
        result = await client.delete_series(
            series_id,
            delete_files=args.get("delete_files", False),
            add_import_exclusion=args.get("add_import_exclusion"),
        )
        return {"deleted": True, "result": result}

    async def _handle_get_episodes(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_episodes tool."""
        series_id = args.get("series_id")
        if series_id is None:
            raise ValueError("series_id is required")
        episodes = await client.get_episodes(series_id, season_number=args.get("season_number"))
        return {"episode_count": len(episodes), "episodes": episodes}

    async def _handle_search_episode(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle search_episode tool."""
        episode_id = args.get("episode_id")
        if episode_id is None:
            raise ValueError("episode_id is required")
        return await client.search_episode(episode_id)

    async def _handle_search_series_command(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle search_series_command tool."""
        series_id = args.get("series_id")
        if series_id is None:
            raise ValueError("series_id is required")
        return await client.search_series_command(series_id)

    async def _handle_get_queue(self, client: SonarrClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_queue tool."""
        return await client.get_queue(page=args.get("page"), page_size=args.get("page_size"))

    async def _handle_get_calendar(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_calendar tool."""
        episodes = await client.get_calendar(
            start_date=args.get("start_date"), end_date=args.get("end_date")
        )
        return {"episode_count": len(episodes), "episodes": episodes}

    async def _handle_get_wanted(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_wanted tool."""
        return await client.get_wanted_missing(
            page=args.get("page"), page_size=args.get("page_size")
        )

    async def _handle_get_status(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_status tool."""
        return await client.get_system_status()

    async def _handle_get_quality_profiles(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_quality_profiles tool."""
        profiles = await client._request("GET", "qualityprofile")
        return {"profile_count": len(profiles), "profiles": profiles}

    async def _handle_get_root_folders(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_root_folders tool."""
        folders = await client._request("GET", "rootfolder")
        return {"folder_count": len(folders), "folders": folders}

    async def _handle_get_indexers(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_indexers tool."""
        indexers = await client._request("GET", "indexer")
        return {"indexer_count": len(indexers), "indexers": indexers}

    async def _handle_get_download_clients(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_download_clients tool."""
        clients = await client._request("GET", "downloadclient")
        return {"client_count": len(clients), "clients": clients}

    async def _handle_get_health(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_health tool."""
        health = await client._request("GET", "health")
        return {"issue_count": len(health), "issues": health}

    async def _handle_assess_optimization(
        self, client: SonarrClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess Sonarr configuration for optimization opportunities.

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

        # Get health issues from Sonarr's built-in health check
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
            series = await client.get_series()
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
                    "description": "No indexers configured. Series searches will not work.",
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
                    "description": "Sonarr has no download clients. Downloads will not work.",
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
                    "description": "No root folders for TV series storage.",
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
                if free_gb < 10:
                    checks.append(
                        {
                            "id": f"low_disk_space_{folder.get('id', 0)}",
                            "category": "storage",
                            "status": "warning" if free_gb >= 5 else "critical",
                            "title": f"Low Disk Space: {folder.get('path', 'Unknown')}",
                            "description": f"Only {free_gb:.1f} GB free space remaining.",
                            "recommendation": "Free up disk space or add additional storage.",
                            "current_value": f"{free_gb:.1f} GB",
                            "optimal_value": "50+ GB",
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
                            "optimal_value": "50+ GB",
                            "auto_fix": False,
                        }
                    )

        # ================================================================
        # HEALTH CHECKS FROM SONARR
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
                        f"See Sonarr wiki: {wiki_url}" if wiki_url else "Check Sonarr logs."
                    ),
                    "current_value": "Issue detected",
                    "optimal_value": "No issues",
                    "auto_fix": False,
                }
            )

        # ================================================================
        # LIBRARY CHECKS
        # ================================================================

        if series:
            # Count unmonitored series
            unmonitored = [s for s in series if not s.get("monitored", True)]
            if len(unmonitored) > len(series) * 0.5:
                checks.append(
                    {
                        "id": "many_unmonitored",
                        "category": "library",
                        "status": "recommendation",
                        "title": "Many Unmonitored Series",
                        "description": f"{len(unmonitored)}/{len(series)} series unmonitored.",
                        "recommendation": "Review unmonitored series and enable if wanted.",
                        "current_value": f"{len(unmonitored)} unmonitored",
                        "optimal_value": "Monitor wanted series",
                        "auto_fix": False,
                    }
                )

            # Check for series with issues
            series_without_files = [
                s for s in series if s.get("statistics", {}).get("episodeFileCount", 0) == 0
            ]
            if series_without_files:
                checks.append(
                    {
                        "id": "series_no_files",
                        "category": "library",
                        "status": "recommendation",
                        "title": "Series Without Episodes",
                        "description": f"{len(series_without_files)} series have no episode files.",
                        "recommendation": "Search for missing episodes or remove unwanted series.",
                        "current_value": f"{len(series_without_files)} empty",
                        "optimal_value": "All series have episodes",
                        "auto_fix": False,
                    }
                )
        else:
            checks.append(
                {
                    "id": "no_series",
                    "category": "library",
                    "status": "recommendation",
                    "title": "No Series Added",
                    "description": "Your Sonarr library is empty.",
                    "recommendation": "Add TV series to start monitoring and downloading.",
                    "current_value": "0 series",
                    "optimal_value": "1+ series",
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
            "service": "sonarr",
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
