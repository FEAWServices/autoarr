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
            # Try to get from settings
            try:
                import httpx

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "http://localhost:8088/api/v1/settings/sabnzbd", timeout=5.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("enabled") and data.get("url") and data.get("api_key"):
                            self._url = data["url"]
                            self._api_key = data["api_key"]
            except Exception as e:
                logger.debug(f"Failed to get SABnzbd settings: {e}")
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
                description="Get the current SABnzbd download queue with status and progress for each item. Shows download name, size, progress %, ETA, and status.",
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
                description="Get SABnzbd download history including completed and failed downloads. Shows completion time, status, and failure reasons.",
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
                description="Get current SABnzbd status: download speed (MB/s), disk space, queue size, paused state, and active server connections.",
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
                description="Pause the entire download queue. All active downloads will be paused until resumed.",
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
                description="Resume the download queue if paused. Downloads will continue from where they left off.",
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
                description="Pause a specific download in the queue by its NZO ID. The download will remain in queue but not actively download.",
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": "The NZO ID of the download to pause (get from sabnzbd_get_queue)",
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
                description="Retry a failed download. SABnzbd will re-fetch the NZB and attempt to download again.",
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": "The NZO ID of the failed download to retry (get from sabnzbd_get_history with failed_only=true)",
                        },
                    },
                    "required": ["nzo_id"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_delete_download",
                description="Delete a download from the queue. Optionally delete the partially downloaded files.",
                parameters={
                    "type": "object",
                    "properties": {
                        "nzo_id": {
                            "type": "string",
                            "description": "The NZO ID of the download to delete",
                        },
                        "delete_files": {
                            "type": "boolean",
                            "description": "Also delete downloaded/incomplete files (default: false)",
                        },
                    },
                    "required": ["nzo_id"],
                },
                service="sabnzbd",
                min_version="2.0.0",
            ),
            ToolDefinition(
                name="sabnzbd_get_config",
                description="Get SABnzbd configuration settings. Returns all settings or a specific section.",
                parameters={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Config section: 'misc' (general), 'servers' (news servers), 'categories', 'rss', 'scheduling'",
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
                description="Set a SABnzbd configuration value. Useful for tuning performance settings.",
                parameters={
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Configuration section (misc, servers, categories)",
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Configuration key (e.g., 'bandwidth_max', 'cache_limit')",
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
                description="Enable/disable Direct Unpack (SABnzbd 3.0+). When enabled, SABnzbd unpacks files during download for faster completion.",
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
                description="Set propagation delay in minutes (SABnzbd 3.0+). Useful when posts aren't fully propagated across servers yet.",
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
                description="Configure filename deobfuscation (SABnzbd 4.0+). Renames obfuscated filenames to readable ones.",
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
        ]

        # Filter by version if provided
        use_version = version or self._version
        return self.filter_tools_by_version(tools, use_version)

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
            return await client.health_check()
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
        return await client.get_queue(
            start=args.get("start", 0),
            limit=args.get("limit"),
        )

    async def _handle_get_history(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_history tool."""
        return await client.get_history(
            start=args.get("start", 0),
            limit=args.get("limit"),
            failed_only=args.get("failed_only", False),
            category=args.get("category"),
        )

    async def _handle_get_status(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_status tool."""
        return await client.get_status()

    async def _handle_pause_queue(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pause_queue tool."""
        return await client.pause_queue()

    async def _handle_resume_queue(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resume_queue tool."""
        return await client.resume_queue()

    async def _handle_pause_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pause_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        return await client.pause_download(nzo_id)

    async def _handle_resume_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle resume_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        return await client.resume_download(nzo_id)

    async def _handle_retry_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle retry_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        return await client.retry_download(nzo_id)

    async def _handle_delete_download(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle delete_download tool."""
        nzo_id = args.get("nzo_id")
        if not nzo_id:
            raise ValueError("nzo_id is required")
        return await client.delete_download(
            nzo_id,
            delete_files=args.get("delete_files", False),
        )

    async def _handle_get_config(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle get_config tool."""
        return await client.get_config(section=args.get("section"))

    async def _handle_set_config(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_config tool."""
        section = args.get("section")
        keyword = args.get("keyword")
        value = args.get("value")

        if not section or not keyword:
            raise ValueError("section and keyword are required")

        return await client.set_config(section, keyword, value)

    # Version-specific handlers (SABnzbd 3.x+)
    async def _handle_set_direct_unpack(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_direct_unpack tool (SABnzbd 3.0+)."""
        enabled = args.get("enabled", False)
        value = "1" if enabled else "0"
        return await client.set_config("misc", "direct_unpack", value)

    async def _handle_set_propagation_delay(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_propagation_delay tool (SABnzbd 3.0+)."""
        minutes = args.get("minutes", 0)
        if minutes < 0 or minutes > 1440:
            raise ValueError("minutes must be between 0 and 1440")
        return await client.set_config("misc", "propagation_delay", str(minutes))

    # Version-specific handlers (SABnzbd 4.x+)
    async def _handle_set_deobfuscate(
        self, client: SABnzbdClient, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle set_deobfuscate tool (SABnzbd 4.0+)."""
        enabled = args.get("enabled", False)
        value = "1" if enabled else "0"
        return await client.set_config("misc", "deobfuscate_final_filenames", value)
