"""
Test fixtures and factories for MCP Orchestrator testing.

This module provides reusable test data factories, mock objects, and fixtures
for testing the MCP Orchestrator - the critical coordination layer that manages
all MCP server connections.

Following TDD Principles:
- These fixtures support comprehensive test coverage (90%+ target)
- Factories enable testing all edge cases and failure scenarios
- Mock strategies isolate orchestrator logic from MCP server implementations
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest


# ============================================================================
# Data Classes for Type Safety
# ============================================================================


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    url: str
    api_key: str
    enabled: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class MCPToolCall:
    """Represents a tool call to an MCP server."""

    server: str
    tool: str
    params: Dict[str, Any]
    timeout: Optional[float] = None


@dataclass
class MCPToolResult:
    """Result from an MCP tool call."""

    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    server: Optional[str] = None
    tool: Optional[str] = None


# ============================================================================
# Configuration Factories
# ============================================================================


@pytest.fixture
def mcp_server_config_factory():
    """
    Factory to create MCP server configuration objects.

    Usage:
        sabnzbd_config = mcp_server_config_factory("sabnzbd")
        disabled_config = mcp_server_config_factory("sonarr", enabled=False)
    """

    def _create(
        name: str,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        enabled: bool = True,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> MCPServerConfig:
        """Create a mock MCP server configuration."""
        return MCPServerConfig(
            name=name,
            url=url or f"http://localhost:808{hash(name) % 10}",
            api_key=api_key or f"test_api_key_{name}",
            enabled=enabled,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

    return _create


@pytest.fixture
def mcp_orchestrator_config_factory(mcp_server_config_factory):
    """
    Factory to create complete MCP orchestrator configuration.

    Usage:
        config = mcp_orchestrator_config_factory()
        partial_config = mcp_orchestrator_config_factory(disabled_servers=["plex"])
    """

    def _create(
        disabled_servers: Optional[List[str]] = None,
        custom_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, MCPServerConfig]:
        """Create a complete orchestrator configuration."""
        disabled = disabled_servers or []
        custom = custom_configs or {}

        servers = ["sabnzbd", "sonarr", "radarr", "plex"]
        config = {}

        for server in servers:
            server_custom = custom.get(server, {})
            config[server] = mcp_server_config_factory(
                name=server,
                enabled=server not in disabled,
                **server_custom
            )

        return config

    return _create


# ============================================================================
# Mock MCP Client Factories
# ============================================================================


@pytest.fixture
def mock_mcp_client_factory():
    """
    Factory to create mock MCP client objects.

    Usage:
        client = mock_mcp_client_factory("sabnzbd")
        failing_client = mock_mcp_client_factory("sonarr", connection_fails=True)
    """

    def _create(
        server_name: str,
        connection_fails: bool = False,
        health_check_result: bool = True,
        available_tools: Optional[List[str]] = None,
    ) -> AsyncMock:
        """Create a mock MCP client."""
        client = AsyncMock()
        client.server_name = server_name

        # Connection management
        if connection_fails:
            client.connect = AsyncMock(side_effect=ConnectionError(f"{server_name} connection failed"))
        else:
            client.connect = AsyncMock(return_value=True)

        client.disconnect = AsyncMock(return_value=None)
        client.is_connected = AsyncMock(return_value=not connection_fails)

        # Health check
        client.health_check = AsyncMock(return_value=health_check_result)

        # Tool information
        tools = available_tools or _get_default_tools(server_name)
        client.list_tools = AsyncMock(return_value=tools)

        # Tool calling
        client.call_tool = AsyncMock(return_value={"success": True, "data": {}})

        return client

    def _get_default_tools(server_name: str) -> List[str]:
        """Get default tools for a server."""
        tools_map = {
            "sabnzbd": ["get_queue", "get_history", "retry_download", "pause_queue"],
            "sonarr": ["get_series", "search_series", "get_calendar", "get_queue"],
            "radarr": ["get_movies", "search_movies", "get_calendar", "get_queue"],
            "plex": ["get_libraries", "get_recently_added", "scan_library"],
        }
        return tools_map.get(server_name, [])

    return _create


@pytest.fixture
def mock_all_mcp_clients(mock_mcp_client_factory):
    """
    Create a complete set of mock MCP clients for all servers.

    Usage:
        clients = mock_all_mcp_clients
        clients = mock_all_mcp_clients(failing_servers=["plex"])
    """

    def _create(
        failing_servers: Optional[List[str]] = None,
        unhealthy_servers: Optional[List[str]] = None,
    ) -> Dict[str, AsyncMock]:
        """Create all MCP client mocks."""
        failing = failing_servers or []
        unhealthy = unhealthy_servers or []

        servers = ["sabnzbd", "sonarr", "radarr", "plex"]
        clients = {}

        for server in servers:
            clients[server] = mock_mcp_client_factory(
                server_name=server,
                connection_fails=server in failing,
                health_check_result=server not in unhealthy,
            )

        return clients

    return _create


# ============================================================================
# Tool Call and Result Factories
# ============================================================================


@pytest.fixture
def mcp_tool_call_factory():
    """
    Factory to create MCP tool call objects.

    Usage:
        call = mcp_tool_call_factory("sabnzbd", "get_queue")
        call_with_params = mcp_tool_call_factory("sonarr", "search_series", {"query": "Breaking Bad"})
    """

    def _create(
        server: str,
        tool: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> MCPToolCall:
        """Create a tool call object."""
        return MCPToolCall(
            server=server,
            tool=tool,
            params=params or {},
            timeout=timeout,
        )

    return _create


@pytest.fixture
def mcp_tool_result_factory():
    """
    Factory to create MCP tool result objects.

    Usage:
        result = mcp_tool_result_factory(success=True, data={"slots": []})
        error_result = mcp_tool_result_factory(success=False, error="Connection timeout")
    """

    def _create(
        success: bool = True,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        server: Optional[str] = None,
        tool: Optional[str] = None,
    ) -> MCPToolResult:
        """Create a tool result object."""
        return MCPToolResult(
            success=success,
            data=data or {},
            error=error,
            server=server,
            tool=tool,
        )

    return _create


@pytest.fixture
def mcp_batch_tool_calls_factory(mcp_tool_call_factory):
    """
    Factory to create batch tool calls for parallel execution testing.

    Usage:
        calls = mcp_batch_tool_calls_factory(count=5)
        mixed_calls = mcp_batch_tool_calls_factory(servers=["sabnzbd", "sonarr"])
    """

    def _create(
        count: int = 3,
        servers: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
    ) -> List[MCPToolCall]:
        """Create multiple tool calls."""
        server_list = servers or ["sabnzbd", "sonarr", "radarr", "plex"]
        tool_list = tools or ["get_queue", "get_status", "health_check"]

        calls = []
        for i in range(count):
            server = server_list[i % len(server_list)]
            tool = tool_list[i % len(tool_list)]
            calls.append(mcp_tool_call_factory(server, tool))

        return calls

    return _create


# ============================================================================
# Error Simulation Fixtures
# ============================================================================


@pytest.fixture
def connection_error_factory():
    """
    Factory to create various connection errors for testing error handling.

    Usage:
        error = connection_error_factory("timeout")
        error = connection_error_factory("refused")
    """

    def _create(error_type: str = "generic") -> Exception:
        """Create a connection error."""
        error_map = {
            "timeout": TimeoutError("Connection timeout"),
            "refused": ConnectionRefusedError("Connection refused"),
            "reset": ConnectionResetError("Connection reset by peer"),
            "generic": ConnectionError("Generic connection error"),
            "network": OSError("Network unreachable"),
        }
        return error_map.get(error_type, Exception("Unknown error"))

    return _create


@pytest.fixture
def circuit_breaker_state_factory():
    """
    Factory to create circuit breaker state for testing.

    Usage:
        state = circuit_breaker_state_factory("closed")
        state = circuit_breaker_state_factory("open", failure_count=5)
    """

    def _create(
        state: str = "closed",  # closed, open, half_open
        failure_count: int = 0,
        last_failure_time: Optional[float] = None,
        success_count: int = 0,
    ) -> Dict[str, Any]:
        """Create circuit breaker state."""
        import time

        return {
            "state": state,
            "failure_count": failure_count,
            "last_failure_time": last_failure_time or (time.time() if failure_count > 0 else None),
            "success_count": success_count,
            "threshold": 5,  # Failures before opening
            "timeout": 60.0,  # Seconds before trying half_open
            "success_threshold": 3,  # Successes needed to close from half_open
        }

    return _create


# ============================================================================
# Health Check Result Factories
# ============================================================================


@pytest.fixture
def health_check_result_factory():
    """
    Factory to create health check results.

    Usage:
        results = health_check_result_factory(all_healthy=True)
        results = health_check_result_factory(unhealthy_servers=["plex"])
    """

    def _create(
        all_healthy: bool = True,
        unhealthy_servers: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """Create health check results for all servers."""
        servers = ["sabnzbd", "sonarr", "radarr", "plex"]
        unhealthy = unhealthy_servers or []

        if all_healthy:
            return {server: True for server in servers}

        return {server: server not in unhealthy for server in servers}

    return _create


# ============================================================================
# Connection Pool State Factories
# ============================================================================


@pytest.fixture
def connection_pool_state_factory():
    """
    Factory to create connection pool state for testing.

    Usage:
        state = connection_pool_state_factory(connected_servers=["sabnzbd", "sonarr"])
    """

    def _create(
        connected_servers: Optional[List[str]] = None,
        total_connections: int = 4,
        active_requests: int = 0,
    ) -> Dict[str, Any]:
        """Create connection pool state."""
        connected = connected_servers or ["sabnzbd", "sonarr", "radarr", "plex"]

        return {
            "total_connections": total_connections,
            "connected_servers": connected,
            "active_connections": len(connected),
            "active_requests": active_requests,
            "max_connections": total_connections,
            "connection_states": {
                server: {
                    "connected": server in connected,
                    "last_health_check": None,
                    "last_error": None,
                    "request_count": 0,
                }
                for server in ["sabnzbd", "sonarr", "radarr", "plex"]
            }
        }

    return _create


# ============================================================================
# Retry Strategy Fixtures
# ============================================================================


@pytest.fixture
def retry_strategy_factory():
    """
    Factory to create retry strategy configurations.

    Usage:
        strategy = retry_strategy_factory(max_retries=3, backoff_factor=2.0)
    """

    def _create(
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retry_on: Optional[List[type]] = None,
    ) -> Dict[str, Any]:
        """Create retry strategy configuration."""
        return {
            "max_retries": max_retries,
            "backoff_factor": backoff_factor,
            "max_delay": max_delay,
            "retry_on": retry_on or [ConnectionError, TimeoutError],
            "jitter": True,  # Add randomness to prevent thundering herd
        }

    return _create


# ============================================================================
# Performance Metric Factories
# ============================================================================


@pytest.fixture
def performance_metrics_factory():
    """
    Factory to create performance metrics for testing.

    Usage:
        metrics = performance_metrics_factory(server="sabnzbd")
    """

    def _create(
        server: Optional[str] = None,
        request_count: int = 0,
        success_count: int = 0,
        failure_count: int = 0,
        avg_response_time: float = 0.0,
    ) -> Dict[str, Any]:
        """Create performance metrics."""
        return {
            "server": server,
            "request_count": request_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "avg_response_time": avg_response_time,
            "success_rate": success_count / request_count if request_count > 0 else 0.0,
            "p50_response_time": avg_response_time * 0.8,
            "p95_response_time": avg_response_time * 1.5,
            "p99_response_time": avg_response_time * 2.0,
        }

    return _create
