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
Unit tests for the Tool Provider System.

Tests the base tool provider interface, tool registry, and version-aware
tool filtering for service API exposure.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.api.services.tool_provider import (
    BaseToolProvider,
    ServiceInfo,
    ToolDefinition,
    ToolRegistry,
    ToolResult,
    get_tool_registry,
    reset_tool_registry,
)

# =============================================================================
# Test Fixtures and Mock Providers
# =============================================================================


class MockToolProvider(BaseToolProvider):
    """Mock tool provider for testing."""

    def __init__(
        self,
        name: str = "mock_service",
        available: bool = True,
        version: str = "1.0.0",
    ):
        self._name = name
        self._available = available
        self._version = version
        self.execute_called_with: List[tuple] = []

    @property
    def service_name(self) -> str:
        return self._name

    def get_tools(self, version: Optional[str] = None) -> List[ToolDefinition]:
        tools = [
            ToolDefinition(
                name=f"{self._name}_basic_tool",
                description="A basic test tool",
                parameters={"type": "object", "properties": {}, "required": []},
                service=self._name,
                min_version="1.0.0",
            ),
            ToolDefinition(
                name=f"{self._name}_advanced_tool",
                description="An advanced test tool requiring 2.0+",
                parameters={"type": "object", "properties": {}, "required": []},
                service=self._name,
                min_version="2.0.0",
            ),
            ToolDefinition(
                name=f"{self._name}_deprecated_tool",
                description="A deprecated tool (max version 1.5.0)",
                parameters={"type": "object", "properties": {}, "required": []},
                service=self._name,
                min_version="1.0.0",
                max_version="1.5.0",
            ),
        ]
        return self.filter_tools_by_version(tools, version or self._version)

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        self.execute_called_with.append((tool_name, arguments))
        if "error" in arguments:
            return ToolResult(success=False, error="Mock error occurred")
        return ToolResult(success=True, data={"result": "success", "tool": tool_name})

    async def is_available(self) -> bool:
        return self._available

    async def get_service_info(self) -> ServiceInfo:
        return ServiceInfo(
            name=self._name,
            version=self._version,
            connected=self._available,
            healthy=self._available,
            url="http://localhost:8080",
            capabilities=["basic", "advanced"],
        )


# =============================================================================
# ToolDefinition Tests
# =============================================================================


class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_tool_definition_creation(self):
        """Test creating a tool definition with all fields."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            service="test_service",
            min_version="1.0.0",
            max_version="2.0.0",
            requires_connection=True,
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.service == "test_service"
        assert tool.min_version == "1.0.0"
        assert tool.max_version == "2.0.0"
        assert tool.requires_connection is True

    def test_to_openai_format(self):
        """Test converting tool definition to OpenAI format."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Max items"}},
                "required": [],
            },
            service="test_service",
        )
        openai_format = tool.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "test_tool"
        assert openai_format["function"]["description"] == "A test tool"
        assert "properties" in openai_format["function"]["parameters"]


# =============================================================================
# ToolResult Tests
# =============================================================================


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """Test creating a successful tool result."""
        result = ToolResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_error_result(self):
        """Test creating an error tool result."""
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"

    def test_to_dict_success(self):
        """Test converting success result to dict."""
        result = ToolResult(success=True, data={"queue_size": 5})
        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["data"] == {"queue_size": 5}
        assert "error" not in result_dict

    def test_to_dict_error(self):
        """Test converting error result to dict."""
        result = ToolResult(success=False, error="Connection failed")
        result_dict = result.to_dict()

        assert result_dict["success"] is False
        assert result_dict["error"] == "Connection failed"
        assert "data" not in result_dict


# =============================================================================
# BaseToolProvider Tests
# =============================================================================


class TestBaseToolProvider:
    """Tests for BaseToolProvider abstract class and version filtering."""

    def test_version_gte(self):
        """Test version comparison (greater than or equal)."""
        # Using the static method through our mock provider
        assert MockToolProvider._version_gte("2.0.0", "1.0.0") is True
        assert MockToolProvider._version_gte("1.0.0", "1.0.0") is True
        assert MockToolProvider._version_gte("1.0.0", "2.0.0") is False
        assert MockToolProvider._version_gte("2.5.3", "2.5.0") is True
        assert MockToolProvider._version_gte("3.0", "2.5.0") is True

    def test_version_lte(self):
        """Test version comparison (less than or equal)."""
        assert MockToolProvider._version_lte("1.0.0", "2.0.0") is True
        assert MockToolProvider._version_lte("1.0.0", "1.0.0") is True
        assert MockToolProvider._version_lte("2.0.0", "1.0.0") is False
        assert MockToolProvider._version_lte("1.5.0", "2.0.0") is True

    def test_version_parsing_with_extra_parts(self):
        """Test version parsing with build info."""
        assert MockToolProvider._version_gte("4.3.2-beta", "4.0.0") is True
        # Non-numeric should be handled gracefully (assume compatible)
        assert MockToolProvider._version_gte("invalid", "1.0.0") is True

    def test_filter_tools_by_version_basic(self):
        """Test filtering tools by minimum version."""
        provider = MockToolProvider(version="1.5.0")
        tools = provider.get_tools(version="1.5.0")

        # Should include basic tool (min 1.0.0)
        tool_names = [t.name for t in tools]
        assert "mock_service_basic_tool" in tool_names

        # Should NOT include advanced tool (min 2.0.0)
        assert "mock_service_advanced_tool" not in tool_names

        # Should include deprecated tool (1.0.0 <= 1.5.0 <= 1.5.0)
        assert "mock_service_deprecated_tool" in tool_names

    def test_filter_tools_by_version_advanced(self):
        """Test filtering for advanced version."""
        provider = MockToolProvider(version="2.5.0")
        tools = provider.get_tools(version="2.5.0")

        tool_names = [t.name for t in tools]
        # Basic and advanced should be available
        assert "mock_service_basic_tool" in tool_names
        assert "mock_service_advanced_tool" in tool_names

        # Deprecated should NOT be available (max 1.5.0)
        assert "mock_service_deprecated_tool" not in tool_names

    def test_filter_tools_no_version(self):
        """Test that without version, all tools are returned."""
        provider = MockToolProvider()
        # When passing None to filter_tools_by_version, all tools should pass
        all_tools = [
            ToolDefinition(
                name="tool1",
                description="Test",
                parameters={},
                service="test",
                min_version="5.0.0",
            ),
        ]
        filtered = provider.filter_tools_by_version(all_tools, None)
        assert len(filtered) == 1


# =============================================================================
# ToolRegistry Tests
# =============================================================================


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        reset_tool_registry()
        return ToolRegistry()

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider."""
        return MockToolProvider(name="test_service", available=True, version="2.0.0")

    def test_register_provider(self, registry, mock_provider):
        """Test registering a tool provider."""
        registry.register_provider(mock_provider)
        assert "test_service" in registry.providers
        assert registry.providers["test_service"] == mock_provider

    def test_unregister_provider(self, registry, mock_provider):
        """Test unregistering a tool provider."""
        registry.register_provider(mock_provider)
        registry.unregister_provider("test_service")
        assert "test_service" not in registry.providers

    @pytest.mark.asyncio
    async def test_initialize(self, registry, mock_provider):
        """Test initializing the registry."""
        registry.register_provider(mock_provider)
        await registry.initialize()

        service_info = registry.get_service_info("test_service")
        assert service_info is not None
        assert service_info.connected is True
        assert service_info.version == "2.0.0"

    @pytest.mark.asyncio
    async def test_get_available_tools(self, registry, mock_provider):
        """Test getting available tools from registry."""
        registry.register_provider(mock_provider)
        await registry.initialize()

        tools = await registry.get_available_tools()
        assert len(tools) > 0

        # Version 2.0.0 should have basic and advanced, not deprecated
        tool_names = [t.name for t in tools]
        assert "test_service_basic_tool" in tool_names
        assert "test_service_advanced_tool" in tool_names
        assert "test_service_deprecated_tool" not in tool_names

    @pytest.mark.asyncio
    async def test_get_available_tools_filters_by_service(self, registry):
        """Test filtering tools by service name."""
        provider1 = MockToolProvider(name="service_a", version="2.0.0")
        provider2 = MockToolProvider(name="service_b", version="2.0.0")

        registry.register_provider(provider1)
        registry.register_provider(provider2)
        await registry.initialize()

        # Only get service_a tools
        tools = await registry.get_available_tools(services=["service_a"])
        tool_names = [t.name for t in tools]

        assert any("service_a" in name for name in tool_names)
        assert not any("service_b" in name for name in tool_names)

    @pytest.mark.asyncio
    async def test_get_available_tools_excludes_unavailable(self, registry):
        """Test that unavailable services are excluded by default."""
        available_provider = MockToolProvider(name="available", available=True)
        unavailable_provider = MockToolProvider(name="unavailable", available=False)

        registry.register_provider(available_provider)
        registry.register_provider(unavailable_provider)
        await registry.initialize()

        tools = await registry.get_available_tools()
        tool_names = [t.name for t in tools]

        assert any("available" in name for name in tool_names)
        assert not any("unavailable" in name for name in tool_names)

    @pytest.mark.asyncio
    async def test_get_available_tools_include_unavailable(self, registry):
        """Test including unavailable services when flag is set."""
        unavailable_provider = MockToolProvider(name="unavailable", available=False)
        registry.register_provider(unavailable_provider)
        await registry.initialize()

        tools = await registry.get_available_tools(include_unavailable=True)
        tool_names = [t.name for t in tools]

        assert any("unavailable" in name for name in tool_names)

    def test_get_tools_openai_format(self, registry, mock_provider):
        """Test converting tools to OpenAI format."""
        tools = [
            ToolDefinition(
                name="test_tool",
                description="A test",
                parameters={"type": "object"},
                service="test",
            )
        ]
        openai_tools = registry.get_tools_openai_format(tools)

        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, registry, mock_provider):
        """Test successful tool execution."""
        registry.register_provider(mock_provider)
        await registry.initialize()

        result = await registry.execute_tool(
            "test_service_basic_tool",
            {"arg1": "value1"},
        )

        assert result.success is True
        assert result.data["tool"] == "test_service_basic_tool"
        assert len(mock_provider.execute_called_with) == 1

    @pytest.mark.asyncio
    async def test_execute_tool_unknown_tool(self, registry, mock_provider):
        """Test executing an unknown tool."""
        registry.register_provider(mock_provider)
        await registry.initialize()

        result = await registry.execute_tool("unknown_tool", {})

        assert result.success is False
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_service_unavailable(self, registry):
        """Test executing tool when service is unavailable."""
        unavailable_provider = MockToolProvider(name="offline", available=False)
        registry.register_provider(unavailable_provider)
        await registry.initialize()

        result = await registry.execute_tool("offline_basic_tool", {})

        assert result.success is False
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self, registry, mock_provider):
        """Test tool execution that returns an error."""
        registry.register_provider(mock_provider)
        await registry.initialize()

        result = await registry.execute_tool(
            "test_service_basic_tool",
            {"error": True},
        )

        assert result.success is False
        assert "Mock error" in result.error

    @pytest.mark.asyncio
    async def test_refresh_service(self, registry, mock_provider):
        """Test refreshing service info."""
        registry.register_provider(mock_provider)
        await registry.initialize()

        # Change provider state
        mock_provider._version = "3.0.0"
        await registry.refresh_service("test_service")

        service_info = registry.get_service_info("test_service")
        assert service_info.version == "3.0.0"

    def test_get_all_services(self, registry, mock_provider):
        """Test getting all registered services."""
        provider2 = MockToolProvider(name="service2")
        registry.register_provider(mock_provider)
        registry.register_provider(provider2)

        services = registry.get_all_services()
        # Services dict may be empty before initialize()
        # but providers should be registered
        assert len(registry.providers) == 2


# =============================================================================
# Singleton Registry Tests
# =============================================================================


class TestSingletonRegistry:
    """Tests for the singleton registry pattern."""

    def setup_method(self):
        """Reset the singleton before each test."""
        reset_tool_registry()

    def test_get_tool_registry_returns_singleton(self):
        """Test that get_tool_registry returns the same instance."""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is registry2

    def test_reset_tool_registry(self):
        """Test resetting the singleton registry."""
        registry1 = get_tool_registry()
        reset_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is not registry2


# =============================================================================
# Integration Tests with Multiple Providers
# =============================================================================


class TestMultiProviderIntegration:
    """Integration tests with multiple providers."""

    @pytest.fixture
    def registry_with_providers(self):
        """Create a registry with multiple providers."""
        reset_tool_registry()
        registry = ToolRegistry()

        # Simulate different services with different versions
        sabnzbd = MockToolProvider(name="sabnzbd", version="4.0.0", available=True)
        sonarr = MockToolProvider(name="sonarr", version="3.0.0", available=True)
        radarr = MockToolProvider(name="radarr", version="5.0.0", available=False)

        registry.register_provider(sabnzbd)
        registry.register_provider(sonarr)
        registry.register_provider(radarr)

        return registry

    @pytest.mark.asyncio
    async def test_multiple_providers_tool_aggregation(self, registry_with_providers):
        """Test that tools from multiple providers are aggregated."""
        await registry_with_providers.initialize()
        tools = await registry_with_providers.get_available_tools()

        # Should have tools from sabnzbd and sonarr (available)
        # but not radarr (unavailable)
        tool_services = set(t.service for t in tools)
        assert "sabnzbd" in tool_services
        assert "sonarr" in tool_services
        assert "radarr" not in tool_services

    @pytest.mark.asyncio
    async def test_version_specific_tools_per_provider(self, registry_with_providers):
        """Test that version filtering is provider-specific."""
        await registry_with_providers.initialize()
        tools = await registry_with_providers.get_available_tools()

        # SABnzbd 4.0 should have advanced tools
        sabnzbd_tools = [t for t in tools if t.service == "sabnzbd"]
        sabnzbd_tool_names = [t.name for t in sabnzbd_tools]
        assert "sabnzbd_advanced_tool" in sabnzbd_tool_names

        # Sonarr 3.0 should also have advanced tools (version 2.0+)
        sonarr_tools = [t for t in tools if t.service == "sonarr"]
        sonarr_tool_names = [t.name for t in sonarr_tools]
        assert "sonarr_advanced_tool" in sonarr_tool_names

    @pytest.mark.asyncio
    async def test_execute_routes_to_correct_provider(self, registry_with_providers):
        """Test that tool execution routes to the correct provider."""
        await registry_with_providers.initialize()

        # Execute sabnzbd tool
        result1 = await registry_with_providers.execute_tool("sabnzbd_basic_tool", {})
        assert result1.success is True
        assert result1.data["tool"] == "sabnzbd_basic_tool"

        # Execute sonarr tool
        result2 = await registry_with_providers.execute_tool("sonarr_basic_tool", {})
        assert result2.success is True
        assert result2.data["tool"] == "sonarr_basic_tool"

        # Execute unavailable radarr tool should fail
        result3 = await registry_with_providers.execute_tool("radarr_basic_tool", {})
        assert result3.success is False
