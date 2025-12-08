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
Plex Tool Provider for AutoArr Chat Agent.

This module implements the BaseToolProvider interface for Plex,
exposing Plex API operations as tools for the LLM.
"""

import logging
from typing import Any, Dict, List, Optional

from autoarr.api.services.tool_provider import (
    BaseToolProvider,
    ServiceInfo,
    ToolDefinition,
    ToolResult,
)
from autoarr.mcp_servers.plex.client import PlexClient, PlexClientError

logger = logging.getLogger(__name__)


class PlexToolProvider(BaseToolProvider):
    """
    Tool provider for Plex Media Server.

    Exposes Plex API operations as tools that can be called by the LLM.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        client: Optional[PlexClient] = None,
    ):
        """
        Initialize the Plex tool provider.

        Args:
            url: Plex URL (e.g., http://localhost:32400)
            token: Plex authentication token
            client: Optional pre-configured PlexClient
        """
        self._url = url
        self._token = token
        self._client = client
        self._version: Optional[str] = None
        self._connected = False

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return "plex"

    async def _get_client(self) -> Optional[PlexClient]:
        """Get or create the Plex client."""
        if self._client:
            return self._client

        if not self._url or not self._token:
            # Try to get from database
            try:
                from autoarr.api.database import SettingsRepository, get_database

                db = get_database()
                repo = SettingsRepository(db)
                settings = await repo.get_service_settings("plex")
                if settings and settings.enabled and settings.url:
                    self._url = settings.url
                    self._token = settings.api_key_or_token
                    logger.debug(f"Got Plex settings from database: url={self._url}")
            except Exception as e:
                logger.warning(f"Failed to get Plex settings from database: {e}")
                return None

        if self._url and self._token:
            self._client = PlexClient(self._url, self._token)
            return self._client

        return None

    def get_tools(self, version: Optional[str] = None) -> List[ToolDefinition]:
        """
        Get available Plex tools.

        Args:
            version: Plex version for compatibility filtering

        Returns:
            List of ToolDefinition objects
        """
        tools = [
            # Library operations
            ToolDefinition(
                name="plex_get_libraries",
                description=("Get all Plex library sections (Movies, TV Shows, Music, etc.)."),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="plex",
            ),
            ToolDefinition(
                name="plex_get_library_items",
                description="Get all items in a specific Plex library.",
                parameters={
                    "type": "object",
                    "properties": {
                        "library_id": {
                            "type": "string",
                            "description": "The library section ID",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return",
                        },
                    },
                    "required": ["library_id"],
                },
                service="plex",
            ),
            ToolDefinition(
                name="plex_get_recently_added",
                description="Get recently added content across all libraries.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return",
                        },
                    },
                    "required": [],
                },
                service="plex",
            ),
            ToolDefinition(
                name="plex_get_on_deck",
                description="Get On Deck items (continue watching).",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return",
                        },
                    },
                    "required": [],
                },
                service="plex",
            ),
            ToolDefinition(
                name="plex_refresh_library",
                description="Trigger a library refresh/scan for new content.",
                parameters={
                    "type": "object",
                    "properties": {
                        "library_id": {
                            "type": "string",
                            "description": "The library section ID to refresh",
                        },
                    },
                    "required": ["library_id"],
                },
                service="plex",
            ),
            # Search and playback
            ToolDefinition(
                name="plex_search",
                description="Search for content across Plex libraries.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                        },
                        "library_id": {
                            "type": "string",
                            "description": "Limit search to specific library (optional)",
                        },
                    },
                    "required": ["query"],
                },
                service="plex",
            ),
            ToolDefinition(
                name="plex_get_sessions",
                description="Get currently playing sessions (who is watching what).",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="plex",
            ),
            ToolDefinition(
                name="plex_get_history",
                description="Get watch history.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return",
                        },
                    },
                    "required": [],
                },
                service="plex",
            ),
            # System
            ToolDefinition(
                name="plex_get_status",
                description="Get Plex server status and identity information.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="plex",
            ),
            # Optimization assessment
            ToolDefinition(
                name="plex_assess_optimization",
                description=(
                    "Assess Plex configuration for optimization opportunities. "
                    "Returns a health check with recommendations."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="plex",
            ),
        ]

        return tools

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a Plex tool.

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
                error="Plex is not configured. Please set up Plex in Settings first.",
            )

        try:
            # Route to appropriate handler
            handlers = {
                "plex_get_libraries": self._handle_get_libraries,
                "plex_get_library_items": self._handle_get_library_items,
                "plex_get_recently_added": self._handle_get_recently_added,
                "plex_get_on_deck": self._handle_get_on_deck,
                "plex_refresh_library": self._handle_refresh_library,
                "plex_search": self._handle_search,
                "plex_get_sessions": self._handle_get_sessions,
                "plex_get_history": self._handle_get_history,
                "plex_get_status": self._handle_get_status,
                "plex_assess_optimization": self._handle_assess_optimization,
            }

            handler = handlers.get(tool_name)
            if not handler:
                return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

            data = await handler(client, arguments)
            return ToolResult(success=True, data=data)

        except PlexClientError as e:
            logger.error(f"Plex client error: {e}")
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(success=False, error=f"Execution failed: {str(e)}")

    async def is_available(self) -> bool:
        """Check if Plex is available."""
        client = await self._get_client()
        if not client:
            return False

        try:
            result = await client.health_check()
            return bool(result)
        except Exception:
            return False

    async def get_service_info(self) -> ServiceInfo:
        """Get Plex service information."""
        client = await self._get_client()
        if not client:
            return ServiceInfo(
                name="plex",
                connected=False,
                healthy=False,
            )

        try:
            # Get server identity
            identity = await client.get_server_identity()
            version = identity.get("version", "unknown")

            # Check health
            healthy = await client.health_check()

            return ServiceInfo(
                name="plex",
                version=version,
                connected=True,
                healthy=healthy,
                url=self._url,
                capabilities=["libraries", "search", "sessions", "history"],
            )
        except Exception as e:
            logger.warning(f"Failed to get Plex info: {e}")
            return ServiceInfo(
                name="plex",
                connected=False,
                healthy=False,
            )

    # Handler methods
    async def _handle_get_libraries(
        self, client: PlexClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_libraries tool."""
        libraries = await client.get_libraries()
        return {"library_count": len(libraries), "libraries": libraries}

    async def _handle_get_library_items(
        self, client: PlexClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_library_items tool."""
        library_id = args.get("library_id")
        if not library_id:
            raise ValueError("library_id is required")
        items = await client.get_library_items(library_id, limit=args.get("limit"))
        return {"item_count": len(items), "items": items}

    async def _handle_get_recently_added(
        self, client: PlexClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_recently_added tool."""
        items = await client.get_recently_added(limit=args.get("limit"))
        return {"item_count": len(items), "items": items}

    async def _handle_get_on_deck(self, client: PlexClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_on_deck tool."""
        items = await client.get_on_deck(limit=args.get("limit"))
        return {"item_count": len(items), "items": items}

    async def _handle_refresh_library(
        self, client: PlexClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle refresh_library tool."""
        library_id = args.get("library_id")
        if not library_id:
            raise ValueError("library_id is required")
        return await client.refresh_library(library_id)

    async def _handle_search(self, client: PlexClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search tool."""
        query = args.get("query")
        if not query:
            raise ValueError("query is required")
        results = await client.search(
            query,
            limit=args.get("limit"),
            section_id=args.get("library_id"),
        )
        return {"result_count": len(results), "results": results}

    async def _handle_get_sessions(
        self, client: PlexClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_sessions tool."""
        sessions = await client.get_sessions()
        return {"session_count": len(sessions), "sessions": sessions}

    async def _handle_get_history(self, client: PlexClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_history tool."""
        history = await client.get_history(limit=args.get("limit"))
        return {"history_count": len(history), "history": history}

    async def _handle_get_status(self, client: PlexClient, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_status tool."""
        return await client.get_server_identity()

    async def _handle_assess_optimization(
        self, client: PlexClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess Plex configuration for optimization opportunities.

        Returns a health check with recommendations.
        """
        checks: List[Dict[str, Any]] = []

        # Get server identity
        try:
            identity = await client.get_server_identity()
            version = identity.get("version", "unknown")
            server_name = identity.get("friendlyName", "Plex Server")
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get server identity: {e}",
                "checks": [],
            }

        # Get libraries
        try:
            libraries = await client.get_libraries()
        except Exception:
            libraries = []

        # Get active sessions
        try:
            sessions = await client.get_sessions()
        except Exception:
            sessions = []

        # ================================================================
        # CONNECTION CHECKS
        # ================================================================

        checks.append(
            {
                "id": "server_connected",
                "category": "connection",
                "status": "good",
                "title": "Plex Server Connected",
                "description": f"Connected to {server_name} (version {version}).",
                "current_value": version,
                "optimal_value": "Connected",
                "auto_fix": False,
            }
        )

        # ================================================================
        # LIBRARY CHECKS
        # ================================================================

        if not libraries:
            checks.append(
                {
                    "id": "no_libraries",
                    "category": "library",
                    "status": "warning",
                    "title": "No Libraries Configured",
                    "description": "Plex has no library sections.",
                    "recommendation": "Add library sections for your Movies, TV Shows, etc.",
                    "current_value": "0 libraries",
                    "optimal_value": "1+ libraries",
                    "auto_fix": False,
                }
            )
        else:
            # Check library types
            movie_libs = [lib for lib in libraries if lib.get("type") == "movie"]
            tv_libs = [lib for lib in libraries if lib.get("type") == "show"]

            checks.append(
                {
                    "id": "libraries_configured",
                    "category": "library",
                    "status": "good",
                    "title": "Libraries Configured",
                    "description": f"{len(libraries)} library section(s) configured.",
                    "current_value": f"{len(libraries)} libraries",
                    "optimal_value": "1+ libraries",
                    "auto_fix": False,
                }
            )

            # Check if we have both movies and TV for integration with Sonarr/Radarr
            if not movie_libs:
                checks.append(
                    {
                        "id": "no_movie_library",
                        "category": "library",
                        "status": "recommendation",
                        "title": "No Movie Library",
                        "description": "No movie library found. Add one for Radarr.",
                        "current_value": "No movie library",
                        "optimal_value": "1 movie library",
                        "auto_fix": False,
                    }
                )

            if not tv_libs:
                checks.append(
                    {
                        "id": "no_tv_library",
                        "category": "library",
                        "status": "recommendation",
                        "title": "No TV Library",
                        "description": "No TV library found. Add one for Sonarr.",
                        "current_value": "No TV library",
                        "optimal_value": "1 TV library",
                        "auto_fix": False,
                    }
                )

            # Check library sizes
            for lib in libraries:
                lib_name = lib.get("title", "Unknown")
                lib_type = lib.get("type", "unknown")

                # Get item count if available
                try:
                    items = await client.get_library_items(str(lib.get("key", "")), limit=1)
                    # Note: We're just checking if we can access it
                    checks.append(
                        {
                            "id": f"library_accessible_{lib.get('key', 0)}",
                            "category": "library",
                            "status": "good",
                            "title": f"Library Accessible: {lib_name}",
                            "description": f"{lib_type.title()} library is accessible.",
                            "current_value": "Accessible",
                            "optimal_value": "Accessible",
                            "auto_fix": False,
                        }
                    )
                except Exception:
                    checks.append(
                        {
                            "id": f"library_error_{lib.get('key', 0)}",
                            "category": "library",
                            "status": "warning",
                            "title": f"Library Error: {lib_name}",
                            "description": f"Could not access {lib_type} library.",
                            "recommendation": "Check library path and permissions.",
                            "current_value": "Error",
                            "optimal_value": "Accessible",
                            "auto_fix": False,
                        }
                    )

        # ================================================================
        # STREAMING CHECKS
        # ================================================================

        if sessions:
            checks.append(
                {
                    "id": "active_sessions",
                    "category": "streaming",
                    "status": "good",
                    "title": "Active Streaming",
                    "description": f"{len(sessions)} active streaming session(s).",
                    "current_value": f"{len(sessions)} sessions",
                    "optimal_value": "Depends on usage",
                    "auto_fix": False,
                }
            )

            # Check for transcoding vs direct play
            transcoding = [s for s in sessions if s.get("TranscodeSession")]
            direct_play = [s for s in sessions if not s.get("TranscodeSession")]

            if transcoding:
                checks.append(
                    {
                        "id": "transcoding_active",
                        "category": "performance",
                        "status": "recommendation",
                        "title": "Transcoding Active",
                        "description": f"{len(transcoding)} stream(s) are transcoding.",
                        "recommendation": "Direct Play is more efficient. Use compatible formats.",
                        "current_value": f"{len(transcoding)} transcoding",
                        "optimal_value": "Direct Play preferred",
                        "auto_fix": False,
                    }
                )
        else:
            checks.append(
                {
                    "id": "no_active_sessions",
                    "category": "streaming",
                    "status": "good",
                    "title": "No Active Sessions",
                    "description": "No active streaming sessions.",
                    "current_value": "0 sessions",
                    "optimal_value": "N/A",
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
            "service": "plex",
            "version": version,
            "server_name": server_name,
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
