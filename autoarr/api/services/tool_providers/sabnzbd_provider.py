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
SABnzbd Tool Provider for AutoArr Chat Agent.

This module implements the BaseToolProvider interface for SABnzbd,
exposing SABnzbd API operations as tools for the LLM.
"""

import logging
from typing import Any, Dict, List, Optional

from autoarr.api.services.tool_provider import (
    BaseToolProvider,
    ServiceInfo,
    ToolDefinition,
    ToolResult,
)
from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient, SABnzbdClientError

logger = logging.getLogger(__name__)


class SABnzbdToolProvider(BaseToolProvider):
    """
    Tool provider for SABnzbd.

    Exposes SABnzbd API operations as tools that can be called by the LLM.
    Supports version-aware tool filtering for API compatibility.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Optional[SABnzbdClient] = None,
    ):
        """
        Initialize the SABnzbd tool provider.

        Args:
            url: SABnzbd URL (e.g., http://localhost:8080)
            api_key: SABnzbd API key
            client: Optional pre-configured SABnzbdClient
        """
        self._url = url
        self._api_key = api_key
        self._client = client
        self._version: Optional[str] = None
        self._connected = False

    @property
    def service_name(self) -> str:
        """Return the service name."""
        return "sabnzbd"

    async def _get_client(self) -> Optional[SABnzbdClient]:
        """Get or create the SABnzbd client."""
        if self._client:
            return self._client

        if not self._url or not self._api_key:
            # Try to get from database directly (API masks the key for security)
            try:
                from autoarr.api.database import SettingsRepository, get_database

                db = get_database()
                repo = SettingsRepository(db)
                settings = await repo.get_service_settings("sabnzbd")
                if settings and settings.enabled and settings.url:
                    self._url = settings.url
                    self._api_key = settings.api_key_or_token
                    logger.debug(f"Got SABnzbd settings from database: url={self._url}")
            except Exception as e:
                logger.warning(f"Failed to get SABnzbd settings from database: {e}")
                return None

        if self._url and self._api_key:
            self._client = SABnzbdClient(self._url, self._api_key)
            return self._client

        return None

    def get_tools(self, version: Optional[str] = None) -> List[ToolDefinition]:
        """
        Get available SABnzbd tools.

        Version-specific tools:
        - SABnzbd 2.x: Basic queue/history operations
        - SABnzbd 3.x: Added direct_unpack, propagation_delay
        - SABnzbd 4.x: Added more advanced sorting, deobfuscation options

        Args:
            version: SABnzbd version for compatibility filtering

        Returns:
            List of ToolDefinition objects compatible with the version
        """
        tools = [
            # Core tools - available in all versions
            ToolDefinition(
                name="sabnzbd_get_queue",
                description=(
                    "Get the current SABnzbd download queue with status and progress "
                    "for each item. Shows download name, size, progress %, ETA, and status."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "integer",
                            "description": "Start index for pagination (default: 0)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return",
                        },
                    },
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",  # Available since SABnzbd 2.x
            ),
            ToolDefinition(
                name="sabnzbd_get_history",
                description=(
                    "Get SABnzbd download history including completed and failed downloads. "
                    "Shows completion time, status, and failure reasons."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "integer",
                            "description": "Start index for pagination",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items",
                        },
                        "failed_only": {
                            "type": "boolean",
                            "description": "Return only failed downloads",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category (tv, movies, etc.)",
                        },
                    },
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_get_status",
                description=(
                    "Get current SABnzbd status: download speed (MB/s), disk space, "
                    "queue size, paused state, and active server connections."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_pause_queue",
                description=(
                    "Pause the entire download queue. "
                    "All active downloads will be paused until resumed."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_resume_queue",
                description=(
                    "Resume the download queue if paused. "
                    "Downloads will continue from where they left off."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_pause_download",
                description=(
                    "Pause a specific download in the queue by its NZO ID. "
                    "The download will remain in queue but not actively download."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": (
                                "The NZO ID of the download to pause "
                                "(get from sabnzbd_get_queue)"
                            ),
                        },
                    },
                    "required": ["nzo_id"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_resume_download",
                description="Resume a specific paused download by its NZO ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": "The NZO ID of the download to resume",
                        },
                    },
                    "required": ["nzo_id"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_retry_download",
                description=(
                    "Retry a failed download. "
                    "SABnzbd will re-fetch the NZB and attempt to download again."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": (
                                "The NZO ID of the failed download to retry "
                                "(get from sabnzbd_get_history with failed_only=true)"
                            ),
                        },
                    },
                    "required": ["nzo_id"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_delete_download",
                description=(
                    "Delete a download from the queue. "
                    "Optionally delete the partially downloaded files."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": "The NZO ID of the download to delete",
                        },
                        "delete_files": {
                            "type": "boolean",
                            "description": (
                                "Also delete downloaded/incomplete files (default: false)"
                            ),
                        },
                    },
                    "required": ["nzo_id"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_get_config",
                description=(
                    "Get SABnzbd configuration settings. "
                    "Returns all settings or a specific section."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": (
                                "Config section: 'misc' (general), 'servers' (news servers), "
                                "'categories', 'rss', 'scheduling'"
                            ),
                            "enum": ["misc", "servers", "categories", "rss", "scheduling"],
                        },
                    },
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_set_config",
                description=(
                    "Set a SABnzbd configuration value. " "Useful for tuning performance settings."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Configuration section (misc, servers, categories)",
                        },
                        "keyword": {
                            "type": "string",
                            "description": (
                                "Configuration key (e.g., 'bandwidth_max', 'cache_limit')"
                            ),
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to set",
                        },
                    },
                    "required": ["section", "keyword", "value"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            # SABnzbd 3.x+ features - Direct Unpack
            ToolDefinition(
                name="sabnzbd_set_direct_unpack",
                description=(
                    "Enable/disable Direct Unpack (SABnzbd 3.0+). "
                    "When enabled, SABnzbd unpacks files during download for faster completion."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Enable or disable direct unpack",
                        },
                    },
                    "required": ["enabled"],
                },
                service="sabnzbd",
                min_version="3.0.0",  # Direct unpack added in 3.x
            ),
            # SABnzbd 3.x+ - Propagation delay
            ToolDefinition(
                name="sabnzbd_set_propagation_delay",
                description=(
                    "Set propagation delay in minutes (SABnzbd 3.0+). "
                    "Useful when posts aren't fully propagated across servers yet."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "minutes": {
                            "type": "integer",
                            "description": "Delay in minutes before starting download (0-1440)",
                            "minimum": 0,
                            "maximum": 1440,
                        },
                    },
                    "required": ["minutes"],
                },
                service="sabnzbd",
                min_version="3.0.0",
            ),
            # SABnzbd 4.x+ features - Deobfuscation
            ToolDefinition(
                name="sabnzbd_set_deobfuscate",
                description=(
                    "Configure filename deobfuscation (SABnzbd 4.0+). "
                    "Renames obfuscated filenames to readable ones."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Enable or disable deobfuscation",
                        },
                    },
                    "required": ["enabled"],
                },
                service="sabnzbd",
                min_version="4.0.0",  # Deobfuscation improved in 4.x
            ),
            # ================================================================
            # User-friendly configuration tools for common admin tasks
            # ================================================================
            ToolDefinition(
                name="sabnzbd_set_speed_limit",
                description=(
                    "Set the max download speed limit in KB/s, MB/s, or percentage. "
                    "Examples: '10M', '5000K', '50%', '0' for unlimited."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "string",
                            "description": (
                                "Speed limit: number with K (KB/s), M (MB/s), % (percentage), "
                                "or 0 for unlimited. Examples: '10M', '5000K', '50%', '0'"
                            ),
                        },
                    },
                    "required": ["speed"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_set_article_cache",
                description=(
                    "Set article cache size in MB. Larger cache = faster but more RAM. "
                    "Recommended: 500M typical, 1G+ for fast connections."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "size_mb": {
                            "type": "integer",
                            "description": "Cache size in megabytes (e.g., 500, 1000, 2000)",
                            "minimum": 0,
                            "maximum": 8192,
                        },
                    },
                    "required": ["size_mb"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_set_connections",
                description=(
                    "Set the maximum number of simultaneous connections per server. "
                    "More connections = faster downloads but may hit server limits. "
                    "Typical values: 8-20 connections."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "connections": {
                            "type": "integer",
                            "description": "Max connections per server (typically 8-50)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                    },
                    "required": ["connections"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_add_server",
                description=(
                    "Add a new Usenet news server to SABnzbd. "
                    "Requires host, port, username, password, optionally SSL."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "host": {
                            "type": "string",
                            "description": "Server hostname (e.g., 'news.newshosting.com')",
                        },
                        "port": {
                            "type": "integer",
                            "description": "Server port (typically 119 or 563 for SSL)",
                        },
                        "username": {
                            "type": "string",
                            "description": "Login username",
                        },
                        "password": {
                            "type": "string",
                            "description": "Login password",
                        },
                        "ssl": {
                            "type": "boolean",
                            "description": "Use SSL/TLS connection (recommended: true)",
                        },
                        "connections": {
                            "type": "integer",
                            "description": "Number of connections (default: 8)",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Server priority (0=highest, 1+=backup)",
                        },
                    },
                    "required": ["host", "port", "username", "password"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_list_servers",
                description="List all configured Usenet news servers and their status.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_test_server",
                description=(
                    "Test connection to a configured news server. "
                    "Verifies connectivity and authentication."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "Name of the server to test (from sabnzbd_list_servers)",
                        },
                    },
                    "required": ["server_name"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_add_category",
                description=(
                    "Add a download category with custom folder and post-processing settings. "
                    "Categories help organize downloads (e.g., 'tv', 'movies', 'music')."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Category name (e.g., 'tv', 'movies')",
                        },
                        "folder": {
                            "type": "string",
                            "description": "Output folder path for this category",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Download priority (-1=low, 0=normal, 1=high, 2=force)",
                        },
                        "script": {
                            "type": "string",
                            "description": "Post-processing script name (optional)",
                        },
                    },
                    "required": ["name"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_list_categories",
                description="List all configured download categories and their settings.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_set_folders",
                description=(
                    "Configure SABnzbd folder paths: temp folder, complete folder, "
                    "watch folder for NZB files."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "temp_folder": {
                            "type": "string",
                            "description": "Temporary/incomplete downloads folder path",
                        },
                        "complete_folder": {
                            "type": "string",
                            "description": "Completed downloads folder path",
                        },
                        "watch_folder": {
                            "type": "string",
                            "description": "Folder to watch for NZB files to auto-add",
                        },
                    },
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_get_warnings",
                description="Get current warnings and errors from SABnzbd logs.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_clear_warnings",
                description="Clear all warnings from SABnzbd.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_assess_optimization",
                description=(
                    "Assess SABnzbd configuration for optimization opportunities. "
                    "Returns a health check with recommendations for best practices."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
        ]

        # Filter by version if provided
        use_version = version or self._version
        return list(self.filter_tools_by_version(tools, use_version))

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a SABnzbd tool.

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
                error="SABnzbd is not configured. Please set up SABnzbd in Settings first.",
            )

        try:
            # Route to appropriate handler
            handlers = {
                "sabnzbd_get_queue": self._handle_get_queue,
                "sabnzbd_get_history": self._handle_get_history,
                "sabnzbd_get_status": self._handle_get_status,
                "sabnzbd_pause_queue": self._handle_pause_queue,
                "sabnzbd_resume_queue": self._handle_resume_queue,
                "sabnzbd_pause_download": self._handle_pause_download,
                "sabnzbd_resume_download": self._handle_resume_download,
                "sabnzbd_retry_download": self._handle_retry_download,
                "sabnzbd_delete_download": self._handle_delete_download,
                "sabnzbd_get_config": self._handle_get_config,
                "sabnzbd_set_config": self._handle_set_config,
                # Version-specific handlers (3.x+)
                "sabnzbd_set_direct_unpack": self._handle_set_direct_unpack,
                "sabnzbd_set_propagation_delay": self._handle_set_propagation_delay,
                # Version-specific handlers (4.x+)
                "sabnzbd_set_deobfuscate": self._handle_set_deobfuscate,
                # User-friendly configuration handlers
                "sabnzbd_set_speed_limit": self._handle_set_speed_limit,
                "sabnzbd_set_article_cache": self._handle_set_article_cache,
                "sabnzbd_set_connections": self._handle_set_connections,
                "sabnzbd_add_server": self._handle_add_server,
                "sabnzbd_list_servers": self._handle_list_servers,
                "sabnzbd_test_server": self._handle_test_server,
                "sabnzbd_add_category": self._handle_add_category,
                "sabnzbd_list_categories": self._handle_list_categories,
                "sabnzbd_set_folders": self._handle_set_folders,
                "sabnzbd_get_warnings": self._handle_get_warnings,
                "sabnzbd_clear_warnings": self._handle_clear_warnings,
                "sabnzbd_assess_optimization": self._handle_assess_optimization,
            }

            handler = handlers.get(tool_name)
            if not handler:
                return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

            data = await handler(client, arguments)
            return ToolResult(success=True, data=data)

        except SABnzbdClientError as e:
            logger.error(f"SABnzbd client error: {e}")
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResult(success=False, error=f"Execution failed: {str(e)}")

    async def is_available(self) -> bool:
        """Check if SABnzbd is available."""
        client = await self._get_client()
        if not client:
            return False

        try:
            result = await client.health_check()
            return bool(result)
        except Exception:
            return False

    async def get_service_info(self) -> ServiceInfo:
        """Get SABnzbd service information."""
        client = await self._get_client()
        if not client:
            return ServiceInfo(
                name="sabnzbd",
                connected=False,
                healthy=False,
            )

        try:
            # Get version
            version_data = await client.get_version()
            version = version_data.get("version", "unknown")

            # Check health
            healthy = await client.health_check()

            return ServiceInfo(
                name="sabnzbd",
                version=version,
                connected=True,
                healthy=healthy,
                url=self._url,
                capabilities=["queue", "history", "config", "retry"],
            )
        except Exception as e:
            logger.warning(f"Failed to get SABnzbd info: {e}")
            return ServiceInfo(
                name="sabnzbd",
                connected=False,
                healthy=False,
            )

    # Handler methods
    async def _handle_get_queue(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_queue tool."""
        result = await client.get_queue(
            start=args.get("start", 0),
            limit=args.get("limit"),
        )
        return dict(result) if result else {}

    async def _handle_get_history(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_history tool."""
        result = await client.get_history(
            start=args.get("start", 0),
            limit=args.get("limit"),
            failed_only=args.get("failed_only", False),
            category=args.get("category"),
        )
        return dict(result) if result else {}

    async def _handle_get_status(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_status tool."""
        result = await client.get_status()
        return dict(result) if result else {}

    async def _handle_pause_queue(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pause_queue tool."""
        result = await client.pause_queue()
        return dict(result) if result else {}

    async def _handle_resume_queue(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resume_queue tool."""
        result = await client.resume_queue()
        return dict(result) if result else {}

    async def _handle_pause_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pause_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        result = await client.pause_download(nzo_id)
        return dict(result) if result else {}

    async def _handle_resume_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resume_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        result = await client.resume_download(nzo_id)
        return dict(result) if result else {}

    async def _handle_retry_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle retry_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        result = await client.retry_download(nzo_id)
        return dict(result) if result else {}

    async def _handle_delete_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle delete_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        result = await client.delete_download(
            nzo_id,
            delete_files=args.get("delete_files", False),
        )
        return dict(result) if result else {}

    async def _handle_get_config(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_config tool."""
        result = await client.get_config(section=args.get("section"))
        return dict(result) if result else {}

    async def _handle_set_config(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_config tool."""
        section = args.get("section")
        keyword = args.get("keyword")
        value = args.get("value")

        if not section or not keyword:
            raise ValueError("section and keyword are required")

        result = await client.set_config(section, keyword, value)
        return dict(result) if result else {}

    # Version-specific handlers (SABnzbd 3.x+)
    async def _handle_set_direct_unpack(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_direct_unpack tool (SABnzbd 3.0+)."""
        enabled = args.get("enabled", False)
        value = "1" if enabled else "0"
        result = await client.set_config("misc", "direct_unpack", value)
        return dict(result) if result else {}

    async def _handle_set_propagation_delay(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_propagation_delay tool (SABnzbd 3.0+)."""
        minutes = args.get("minutes", 0)
        if minutes < 0 or minutes > 1440:
            raise ValueError("minutes must be between 0 and 1440")
        result = await client.set_config("misc", "propagation_delay", str(minutes))
        return dict(result) if result else {}

    # Version-specific handlers (SABnzbd 4.x+)
    async def _handle_set_deobfuscate(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_deobfuscate tool (SABnzbd 4.0+)."""
        enabled = args.get("enabled", False)
        value = "1" if enabled else "0"
        result = await client.set_config("misc", "deobfuscate_final_filenames", value)
        return dict(result) if result else {}

    # ================================================================
    # User-friendly configuration handlers
    # ================================================================

    async def _handle_set_speed_limit(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_speed_limit tool - set max download speed."""
        speed = args.get("speed", "0")
        # SABnzbd accepts speed in KB/s or with suffixes M/K/%
        # The speedlimit API endpoint handles conversion
        result = await client._request("config", name="speedlimit", value=speed)
        return {
            "status": "success",
            "message": (
                f"Speed limit set to {speed}" if speed != "0" else "Speed limit removed (unlimited)"
            ),
            "result": result,
        }

    async def _handle_set_article_cache(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_article_cache tool - set RAM cache size."""
        size_mb = args.get("size_mb", 0)
        # SABnzbd expects cache_limit in format like "500M" or megabytes
        value = f"{size_mb}M"
        result = await client.set_config("misc", "cache_limit", value)
        return {
            "status": "success",
            "message": f"Article cache set to {size_mb} MB",
            "result": result,
        }

    async def _handle_set_connections(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_connections tool - set max connections per server."""
        connections = args.get("connections", 8)
        # Get all servers and update their connection count
        config = await client.get_config(section="servers")
        servers = config.get("config", {}).get("servers", [])

        updated = []
        for server in servers:
            server_name = server.get("name", server.get("host", "unknown"))
            # Update each server's connections setting
            await client.set_config("servers", f"{server_name}:connections", str(connections))
            updated.append(server_name)

        return {
            "status": "success",
            "message": f"Set {connections} connections for {len(updated)} server(s)",
            "servers_updated": updated,
        }

    async def _handle_add_server(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle add_server tool - add a new Usenet server."""
        host = args.get("host")
        port = args.get("port", 563 if args.get("ssl", True) else 119)
        username = args.get("username", "")
        password = args.get("password", "")
        ssl = args.get("ssl", True)
        connections = args.get("connections", 8)
        priority = args.get("priority", 0)

        if not host:
            raise ValueError("Server host is required")

        # SABnzbd add_server API
        result = await client._request(
            "set_config_default",
            section="servers",
            keyword=host,
        )

        # Now configure the server
        await client.set_config("servers", f"{host}:host", host)
        await client.set_config("servers", f"{host}:port", str(port))
        await client.set_config("servers", f"{host}:username", username)
        await client.set_config("servers", f"{host}:password", password)
        await client.set_config("servers", f"{host}:ssl", "1" if ssl else "0")
        await client.set_config("servers", f"{host}:connections", str(connections))
        await client.set_config("servers", f"{host}:priority", str(priority))
        await client.set_config("servers", f"{host}:enable", "1")

        return {
            "status": "success",
            "message": f"Server {host}:{port} added successfully",
            "server": {
                "host": host,
                "port": port,
                "ssl": ssl,
                "connections": connections,
                "priority": priority,
            },
        }

    async def _handle_list_servers(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle list_servers tool - list configured news servers."""
        config = await client.get_config(section="servers")
        servers = config.get("config", {}).get("servers", [])

        server_list = []
        for server in servers:
            server_list.append(
                {
                    "name": server.get("name", server.get("host", "unknown")),
                    "host": server.get("host", ""),
                    "port": server.get("port", 563),
                    "ssl": server.get("ssl", 1) == 1,
                    "connections": server.get("connections", 0),
                    "priority": server.get("priority", 0),
                    "enabled": server.get("enable", 1) == 1,
                }
            )

        return {
            "server_count": len(server_list),
            "servers": server_list,
        }

    async def _handle_test_server(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle test_server tool - test server connection."""
        server_name = args.get("server_name")
        if not server_name:
            raise ValueError("server_name is required")

        # SABnzbd test_server API
        result = await client._request("test_server", server=server_name)

        # Parse result - SABnzbd returns test status
        return {
            "server": server_name,
            "test_result": result,
            "status": "success" if result.get("value", "") == "" else "failed",
            "message": result.get("value", "Connection successful"),
        }

    async def _handle_add_category(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle add_category tool - add a download category."""
        name = args.get("name")
        folder = args.get("folder", "")
        priority = args.get("priority", 0)
        script = args.get("script", "")

        if not name:
            raise ValueError("Category name is required")

        # Add category via set_config_default then configure
        await client._request("set_config_default", section="categories", keyword=name)
        await client.set_config("categories", f"{name}:name", name)
        if folder:
            await client.set_config("categories", f"{name}:dir", folder)
        await client.set_config("categories", f"{name}:priority", str(priority))
        if script:
            await client.set_config("categories", f"{name}:script", script)

        return {
            "status": "success",
            "message": f"Category '{name}' added",
            "category": {
                "name": name,
                "folder": folder,
                "priority": priority,
                "script": script,
            },
        }

    async def _handle_list_categories(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle list_categories tool - list configured categories."""
        config = await client.get_config(section="categories")
        categories = config.get("config", {}).get("categories", [])

        category_list = []
        for cat in categories:
            category_list.append(
                {
                    "name": cat.get("name", ""),
                    "folder": cat.get("dir", ""),
                    "priority": cat.get("priority", 0),
                    "script": cat.get("script", ""),
                }
            )

        return {
            "category_count": len(category_list),
            "categories": category_list,
        }

    async def _handle_set_folders(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_folders tool - configure SABnzbd folder paths."""
        temp_folder = args.get("temp_folder")
        complete_folder = args.get("complete_folder")
        watch_folder = args.get("watch_folder")

        updated = []

        if temp_folder:
            await client.set_config("misc", "download_dir", temp_folder)
            updated.append(f"temp_folder: {temp_folder}")

        if complete_folder:
            await client.set_config("misc", "complete_dir", complete_folder)
            updated.append(f"complete_folder: {complete_folder}")

        if watch_folder:
            await client.set_config("misc", "dirscan_dir", watch_folder)
            updated.append(f"watch_folder: {watch_folder}")

        if not updated:
            return {"status": "no_change", "message": "No folders specified to update"}

        return {
            "status": "success",
            "message": f"Updated {len(updated)} folder(s)",
            "updated": updated,
        }

    async def _handle_get_warnings(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_warnings tool - get SABnzbd warnings."""
        result = await client._request("warnings")
        warnings = result.get("warnings", [])

        return {
            "warning_count": len(warnings),
            "warnings": warnings[:50],  # Limit to 50 most recent
        }

    async def _handle_clear_warnings(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle clear_warnings tool - clear all SABnzbd warnings."""
        result = await client._request("warnings", name="clear")
        return {
            "status": "success",
            "message": "All warnings cleared",
            "result": result,
        }

    async def _handle_assess_optimization(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess SABnzbd configuration for optimization opportunities.

        Returns a comprehensive health check with version-specific best practices.
        """
        checks: List[Dict[str, Any]] = []

        # Get current configuration
        try:
            config = await client.get_config()
            misc = config.get("config", {}).get("misc", {})
            servers = config.get("config", {}).get("servers", [])
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get configuration: {e}",
                "checks": [],
            }

        # Get version for version-specific checks
        try:
            version_data = await client.get_version()
            version = version_data.get("version", "4.0.0")
            major_version = int(version.split(".")[0]) if version else 4
        except Exception:
            version = "unknown"
            major_version = 4

        # Get status for runtime checks
        try:
            status = await client.get_status()
        except Exception:
            status = {}

        # Get warnings count
        try:
            warnings_data = await client._request("warnings")
            warning_count = len(warnings_data.get("warnings", []))
        except Exception:
            warning_count = 0

        # ================================================================
        # CRITICAL CHECKS (status: critical)
        # ================================================================

        # Check: No servers configured
        if not servers:
            checks.append(
                {
                    "id": "no_servers",
                    "category": "connection",
                    "status": "critical",
                    "title": "No Usenet Servers Configured",
                    "description": "SABnzbd has no news servers configured. Downloads cannot work.",
                    "recommendation": "Add at least one Usenet server in SABnzbd settings.",
                    "current_value": "0 servers",
                    "optimal_value": "1+ servers",
                    "auto_fix": False,
                }
            )
        else:
            # Check: All servers disabled
            enabled_servers = [s for s in servers if s.get("enable", 1) == 1]
            if not enabled_servers:
                checks.append(
                    {
                        "id": "all_servers_disabled",
                        "category": "connection",
                        "status": "critical",
                        "title": "All Servers Disabled",
                        "description": "All configured servers are disabled.",
                        "recommendation": "Enable at least one server.",
                        "current_value": f"0/{len(servers)} enabled",
                        "optimal_value": "1+ enabled",
                        "auto_fix": False,
                    }
                )
            else:
                checks.append(
                    {
                        "id": "servers_configured",
                        "category": "connection",
                        "status": "good",
                        "title": "Usenet Servers Configured",
                        "description": f"{len(enabled_servers)} server(s) configured and enabled.",
                        "current_value": f"{len(enabled_servers)} enabled",
                        "optimal_value": "1+ enabled",
                        "auto_fix": False,
                    }
                )

        # Check: Warnings present
        if warning_count > 0:
            checks.append(
                {
                    "id": "warnings_present",
                    "category": "health",
                    "status": "warning" if warning_count < 10 else "critical",
                    "title": f"{warning_count} Warning(s) Present",
                    "description": "SABnzbd has logged warnings that may indicate issues.",
                    "recommendation": "Review warnings in SABnzbd Status page.",
                    "current_value": str(warning_count),
                    "optimal_value": "0",
                    "auto_fix": True,
                    "fix_action": "sabnzbd_clear_warnings",
                }
            )
        else:
            checks.append(
                {
                    "id": "no_warnings",
                    "category": "health",
                    "status": "good",
                    "title": "No Warnings",
                    "description": "SABnzbd has no logged warnings.",
                    "current_value": "0",
                    "optimal_value": "0",
                    "auto_fix": False,
                }
            )

        # ================================================================
        # PERFORMANCE CHECKS (status: warning/recommendation)
        # ================================================================

        # Check: Article cache size
        cache_limit = misc.get("cache_limit", "0")
        cache_mb = self._parse_size_to_mb(cache_limit)
        if cache_mb < 256:
            checks.append(
                {
                    "id": "low_cache",
                    "category": "performance",
                    "status": "warning",
                    "title": "Low Article Cache",
                    "description": (
                        "Article cache is below recommended minimum. "
                        "Larger cache improves download speed."
                    ),
                    "recommendation": "Set cache to at least 500MB for optimal performance.",
                    "current_value": cache_limit or "0",
                    "optimal_value": "500M - 1G",
                    "auto_fix": True,
                    "fix_action": "sabnzbd_set_article_cache",
                    "fix_params": {"size_mb": 500},
                }
            )
        elif cache_mb >= 500:
            checks.append(
                {
                    "id": "good_cache",
                    "category": "performance",
                    "status": "good",
                    "title": "Article Cache Optimized",
                    "description": "Cache size is at recommended level.",
                    "current_value": cache_limit,
                    "optimal_value": "500M - 1G",
                    "auto_fix": False,
                }
            )
        else:
            checks.append(
                {
                    "id": "acceptable_cache",
                    "category": "performance",
                    "status": "recommendation",
                    "title": "Article Cache Could Be Increased",
                    "description": "Cache is adequate but could be improved.",
                    "current_value": cache_limit,
                    "optimal_value": "500M - 1G",
                    "auto_fix": True,
                    "fix_action": "sabnzbd_set_article_cache",
                    "fix_params": {"size_mb": 500},
                }
            )

        # Check: Server connections
        for server in servers:
            server_name = server.get("name", server.get("host", "unknown"))
            connections = int(server.get("connections", 0))
            if connections < 5:
                checks.append(
                    {
                        "id": f"low_connections_{server_name}",
                        "category": "performance",
                        "status": "warning",
                        "title": f"Low Connections: {server_name}",
                        "description": f"Only {connections} connections. Consider increasing.",
                        "recommendation": "Most providers allow 10-50 connections.",
                        "current_value": str(connections),
                        "optimal_value": "8-20",
                        "auto_fix": False,
                    }
                )
            elif connections > 50:
                checks.append(
                    {
                        "id": f"high_connections_{server_name}",
                        "category": "performance",
                        "status": "recommendation",
                        "title": f"High Connections: {server_name}",
                        "description": (f"{connections} connections may exceed provider limits."),
                        "recommendation": "Check your provider's connection limit.",
                        "current_value": str(connections),
                        "optimal_value": "8-20",
                        "auto_fix": False,
                    }
                )

        # Check: SSL on servers
        for server in servers:
            server_name = server.get("name", server.get("host", "unknown"))
            ssl_enabled = server.get("ssl", 0) == 1
            if not ssl_enabled:
                checks.append(
                    {
                        "id": f"no_ssl_{server_name}",
                        "category": "security",
                        "status": "warning",
                        "title": f"No SSL: {server_name}",
                        "description": "Server connection is not encrypted.",
                        "recommendation": "Enable SSL for security (port 563 or 443).",
                        "current_value": "Disabled",
                        "optimal_value": "Enabled",
                        "auto_fix": False,
                    }
                )

        # ================================================================
        # VERSION-SPECIFIC CHECKS (SABnzbd 3.x+)
        # ================================================================

        if major_version >= 3:
            # Check: Direct Unpack (3.0+)
            direct_unpack = misc.get("direct_unpack", 0)
            if direct_unpack != 1:
                checks.append(
                    {
                        "id": "direct_unpack_disabled",
                        "category": "performance",
                        "status": "recommendation",
                        "title": "Direct Unpack Disabled",
                        "description": (
                            "Direct Unpack extracts files during download for faster completion."
                        ),
                        "recommendation": "Enable Direct Unpack for faster post-processing.",
                        "current_value": "Disabled",
                        "optimal_value": "Enabled",
                        "auto_fix": True,
                        "fix_action": "sabnzbd_set_direct_unpack",
                        "fix_params": {"enabled": True},
                        "min_version": "3.0.0",
                    }
                )
            else:
                checks.append(
                    {
                        "id": "direct_unpack_enabled",
                        "category": "performance",
                        "status": "good",
                        "title": "Direct Unpack Enabled",
                        "description": "Files are extracted during download.",
                        "current_value": "Enabled",
                        "optimal_value": "Enabled",
                        "auto_fix": False,
                    }
                )

        # ================================================================
        # VERSION-SPECIFIC CHECKS (SABnzbd 4.x+)
        # ================================================================

        if major_version >= 4:
            # Check: Deobfuscation (4.0+)
            deobfuscate = misc.get("deobfuscate_final_filenames", 0)
            if deobfuscate != 1:
                checks.append(
                    {
                        "id": "deobfuscate_disabled",
                        "category": "usability",
                        "status": "recommendation",
                        "title": "Filename Deobfuscation Disabled",
                        "description": ("Obfuscated filenames are not automatically renamed."),
                        "recommendation": "Enable to get readable filenames automatically.",
                        "current_value": "Disabled",
                        "optimal_value": "Enabled",
                        "auto_fix": True,
                        "fix_action": "sabnzbd_set_deobfuscate",
                        "fix_params": {"enabled": True},
                        "min_version": "4.0.0",
                    }
                )
            else:
                checks.append(
                    {
                        "id": "deobfuscate_enabled",
                        "category": "usability",
                        "status": "good",
                        "title": "Filename Deobfuscation Enabled",
                        "description": "Obfuscated filenames are automatically renamed.",
                        "current_value": "Enabled",
                        "optimal_value": "Enabled",
                        "auto_fix": False,
                    }
                )

        # ================================================================
        # FOLDER CHECKS
        # ================================================================

        # Check: Temp and complete folders are different
        download_dir = misc.get("download_dir", "")
        complete_dir = misc.get("complete_dir", "")
        if download_dir and complete_dir and download_dir == complete_dir:
            checks.append(
                {
                    "id": "same_folders",
                    "category": "configuration",
                    "status": "warning",
                    "title": "Same Temp and Complete Folder",
                    "description": "Temp and complete folders are the same location.",
                    "recommendation": "Use separate folders for better organization.",
                    "current_value": download_dir,
                    "optimal_value": "Different folders",
                    "auto_fix": False,
                }
            )

        # ================================================================
        # CATEGORY CHECKS
        # ================================================================

        categories = config.get("config", {}).get("categories", [])
        category_names = [c.get("name", "") for c in categories]
        recommended_categories = ["tv", "movies"]

        for cat in recommended_categories:
            if cat not in category_names:
                checks.append(
                    {
                        "id": f"missing_category_{cat}",
                        "category": "organization",
                        "status": "recommendation",
                        "title": f"Missing Category: {cat}",
                        "description": f"No '{cat}' category for Sonarr/Radarr integration.",
                        "recommendation": f"Add a '{cat}' category for better organization.",
                        "current_value": "Not configured",
                        "optimal_value": "Configured",
                        "auto_fix": True,
                        "fix_action": "sabnzbd_add_category",
                        "fix_params": {"name": cat},
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
        # Score: good=100%, recommendation=75%, warning=50%, critical=0%
        score_sum = (
            good_count * 100 + recommendation_count * 75 + warning_count * 50 + critical_count * 0
        )
        overall_score = round(score_sum / total_checks) if total_checks > 0 else 0

        # Determine overall status
        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        elif recommendation_count > 0:
            overall_status = "good"  # Recommendations don't affect overall status
        else:
            overall_status = "excellent"

        return {
            "service": "sabnzbd",
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

    def _parse_size_to_mb(self, size_str: str) -> int:
        """Parse a size string like '500M' or '1G' to megabytes."""
        if not size_str:
            return 0
        size_str = str(size_str).strip().upper()
        try:
            if size_str.endswith("G"):
                return int(float(size_str[:-1]) * 1024)
            elif size_str.endswith("M"):
                return int(float(size_str[:-1]))
            elif size_str.endswith("K"):
                return int(float(size_str[:-1]) / 1024)
            else:
                return int(float(size_str))
        except (ValueError, TypeError):
            return 0
