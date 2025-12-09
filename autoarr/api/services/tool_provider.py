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
MCP Tool Provider System for AutoArr Chat Agent.

This module provides a unified interface for exposing service APIs as tools
that can be used by LLMs via function calling. Each service (SABnzbd, Sonarr,
Radarr, Plex) can register tools that the chat agent can invoke.

Architecture:
- BaseToolProvider: Abstract base class all service tool providers implement
- ToolRegistry: Aggregates tools from all connected services
- Version-aware: Tools can be filtered/modified based on service version

Example:
    # Get all available tools for the chat agent
    registry = ToolRegistry()
    await registry.initialize()
    tools = await registry.get_available_tools()

    # Execute a tool
    result = await registry.execute_tool("sabnzbd_get_queue", {"limit": 10})
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    service: str  # Service this tool belongs to (sabnzbd, sonarr, etc.)
    min_version: Optional[str] = None  # Minimum service version required
    max_version: Optional[str] = None  # Maximum service version (for deprecated APIs)
    requires_connection: bool = True  # Whether service must be connected

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class ServiceInfo:
    """Information about a connected service."""

    name: str
    version: Optional[str] = None
    connected: bool = False
    healthy: bool = False
    url: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)


class BaseToolProvider(ABC):
    """
    Abstract base class for service tool providers.

    Each service (SABnzbd, Sonarr, Radarr, Plex) should implement this
    interface to expose its API as tools for the chat agent.

    Example implementation:
        class SABnzbdToolProvider(BaseToolProvider):
            @property
            def service_name(self) -> str:
                return "sabnzbd"

            def get_tools(self) -> List[ToolDefinition]:
                return [
                    ToolDefinition(
                        name="sabnzbd_get_queue",
                        description="Get the current download queue",
                        parameters={...},
                        service="sabnzbd",
                    ),
                ]

            async def execute(self, tool_name: str, args: Dict) -> ToolResult:
                if tool_name == "sabnzbd_get_queue":
                    data = await self.client.get_queue(**args)
                    return ToolResult(success=True, data=data)
    """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Name of the service (e.g., 'sabnzbd', 'sonarr')."""
        pass

    @abstractmethod
    def get_tools(self, version: Optional[str] = None) -> List[ToolDefinition]:
        """
        Get list of available tools for this service.

        Args:
            version: Service version for version-specific tools

        Returns:
            List of ToolDefinition objects
        """
        pass

    @abstractmethod
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            ToolResult with success status and data/error
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the service is available and connected."""
        pass

    async def get_service_info(self) -> ServiceInfo:
        """
        Get information about this service.

        Override to provide version and capability information.
        """
        return ServiceInfo(
            name=self.service_name,
            connected=await self.is_available(),
            healthy=await self.is_available(),
        )

    def filter_tools_by_version(
        self, tools: List[ToolDefinition], version: Optional[str]
    ) -> List[ToolDefinition]:
        """
        Filter tools based on service version compatibility.

        Args:
            tools: List of all tools
            version: Current service version

        Returns:
            List of compatible tools
        """
        if not version:
            return tools

        compatible = []
        for tool in tools:
            # Check minimum version
            if tool.min_version and not self._version_gte(version, tool.min_version):
                logger.debug(
                    f"Tool {tool.name} requires version >= {tool.min_version}, "
                    f"but service is {version}"
                )
                continue

            # Check maximum version
            if tool.max_version and not self._version_lte(version, tool.max_version):
                logger.debug(
                    f"Tool {tool.name} deprecated after version {tool.max_version}, "
                    f"service is {version}"
                )
                continue

            compatible.append(tool)

        return compatible

    @staticmethod
    def _version_gte(version: str, min_version: str) -> bool:
        """Check if version >= min_version using semantic versioning."""
        try:
            v1_parts = [int(x) for x in version.split(".")[:3]]
            v2_parts = [int(x) for x in min_version.split(".")[:3]]
            # Pad with zeros
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            return tuple(v1_parts) >= tuple(v2_parts)
        except (ValueError, AttributeError):
            return True  # Assume compatible if parsing fails

    @staticmethod
    def _version_lte(version: str, max_version: str) -> bool:
        """Check if version <= max_version using semantic versioning."""
        try:
            v1_parts = [int(x) for x in version.split(".")[:3]]
            v2_parts = [int(x) for x in max_version.split(".")[:3]]
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            return tuple(v1_parts) <= tuple(v2_parts)
        except (ValueError, AttributeError):
            return True


class ToolRegistry:
    """
    Registry that aggregates tools from all connected services.

    The registry:
    - Discovers and registers tool providers for each service
    - Provides a unified interface to get all available tools
    - Routes tool execution requests to the appropriate provider
    - Handles version-aware tool filtering

    Usage:
        registry = ToolRegistry()
        await registry.initialize()

        # Get tools for LLM function calling
        tools = await registry.get_available_tools()

        # Execute a tool
        result = await registry.execute_tool("sabnzbd_get_queue", {"limit": 10})
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._providers: Dict[str, BaseToolProvider] = {}
        self._service_info: Dict[str, ServiceInfo] = {}
        self._initialized = False

    def register_provider(self, provider: BaseToolProvider) -> None:
        """
        Register a tool provider for a service.

        Args:
            provider: Tool provider instance
        """
        self._providers[provider.service_name] = provider
        logger.info(f"Registered tool provider for {provider.service_name}")

    def unregister_provider(self, service_name: str) -> None:
        """
        Unregister a tool provider.

        Args:
            service_name: Name of service to unregister
        """
        if service_name in self._providers:
            del self._providers[service_name]
            if service_name in self._service_info:
                del self._service_info[service_name]
            logger.info(f"Unregistered tool provider for {service_name}")

    async def initialize(self) -> None:
        """
        Initialize the registry by discovering available services.

        This fetches service info (version, capabilities) from each
        registered provider.
        """
        for name, provider in self._providers.items():
            try:
                self._service_info[name] = await provider.get_service_info()
                logger.info(
                    f"Initialized {name}: connected={self._service_info[name].connected}, "
                    f"version={self._service_info[name].version}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize {name}: {e}")
                self._service_info[name] = ServiceInfo(name=name, connected=False, healthy=False)

        self._initialized = True

    async def refresh_service(self, service_name: str) -> None:
        """
        Refresh service info for a specific service.

        Args:
            service_name: Name of service to refresh
        """
        if service_name not in self._providers:
            logger.warning(f"No provider registered for {service_name}")
            return

        try:
            self._service_info[service_name] = await self._providers[
                service_name
            ].get_service_info()
        except Exception as e:
            logger.warning(f"Failed to refresh {service_name}: {e}")

    async def get_available_tools(
        self,
        services: Optional[List[str]] = None,
        include_unavailable: bool = False,
    ) -> List[ToolDefinition]:
        """
        Get all available tools from registered providers.

        Args:
            services: Optional list of services to include (all if None)
            include_unavailable: Include tools from unavailable services

        Returns:
            List of ToolDefinition objects
        """
        if not self._initialized:
            await self.initialize()

        all_tools = []

        for name, provider in self._providers.items():
            # Filter by service list if provided
            if services and name not in services:
                continue

            # Check availability
            service_info = self._service_info.get(name)
            if not include_unavailable and service_info and not service_info.connected:
                logger.debug(f"Skipping {name} - not connected")
                continue

            # Get version-filtered tools
            version = service_info.version if service_info else None
            try:
                tools = provider.get_tools(version=version)
                all_tools.extend(tools)
                logger.debug(f"Got {len(tools)} tools from {name}")
            except Exception as e:
                logger.warning(f"Failed to get tools from {name}: {e}")

        return all_tools

    def get_tools_openai_format(
        self,
        tools: List[ToolDefinition],
    ) -> List[Dict[str, Any]]:
        """
        Convert tool definitions to OpenAI function calling format.

        Args:
            tools: List of ToolDefinition objects

        Returns:
            List of tool definitions in OpenAI format
        """
        return [tool.to_openai_format() for tool in tools]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute (e.g., "sabnzbd_get_queue")
            arguments: Arguments to pass to the tool

        Returns:
            ToolResult with success status and data/error
        """
        # Determine which provider handles this tool
        service_name = self._get_service_for_tool(tool_name)
        if not service_name:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        provider = self._providers.get(service_name)
        if not provider:
            return ToolResult(
                success=False, error=f"No provider registered for service: {service_name}"
            )

        # Check if service is available
        if not await provider.is_available():
            return ToolResult(success=False, error=f"Service {service_name} is not available")

        # Execute the tool
        try:
            result = await provider.execute(tool_name, arguments)
            logger.info(f"Executed tool {tool_name}: success={result.success}")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}: {e}")
            return ToolResult(success=False, error=f"Tool execution failed: {str(e)}")

    def _get_service_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Determine which service a tool belongs to.

        Convention: tool names are prefixed with service name (e.g., sabnzbd_get_queue)

        Args:
            tool_name: Name of the tool

        Returns:
            Service name or None if not found
        """
        # Check tool name prefix
        for service_name in self._providers.keys():
            if tool_name.startswith(f"{service_name}_"):
                return service_name

        # Fallback: check each provider's tools
        for name, provider in self._providers.items():
            try:
                tools = provider.get_tools()
                if any(t.name == tool_name for t in tools):
                    return name
            except Exception:
                pass

        return None

    def get_service_info(self, service_name: str) -> Optional[ServiceInfo]:
        """Get cached service info."""
        return self._service_info.get(service_name)

    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get info for all registered services."""
        return dict(self._service_info)

    @property
    def providers(self) -> Dict[str, BaseToolProvider]:
        """Get all registered providers."""
        return dict(self._providers)


# Singleton instance for the application
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        The singleton ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_tool_registry() -> None:
    """Reset the global tool registry (for testing)."""
    global _registry
    _registry = None
