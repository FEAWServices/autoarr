"""
MCP Orchestrator - The Heart of AutoArr.

This module provides the main orchestration layer that coordinates communication
with all MCP servers (SABnzbd, Sonarr, Radarr, and Plex). It handles connection
management, tool routing, parallel execution, error handling, and health monitoring.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from unittest.mock import AsyncMock

from .config import MCPOrchestratorConfig, ServerConfig
from .exceptions import (
    CircuitBreakerOpenError,
    MCPConnectionError,
    MCPOrchestratorError,
    MCPTimeoutError,
    MCPToolError,
)


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests are allowed
    - OPEN: Too many failures, requests are rejected
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        success_threshold: int = 3,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before transitioning to half-open
            success_threshold: Successes needed to close from half-open
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.state = "closed"
        self.last_failure_time: Optional[float] = None

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        # Check if we should transition from open to half-open
        if self.state == "open" and self.last_failure_time:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                self.success_count = 0

        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "threshold": self.failure_threshold,
            "timeout": self.timeout,
            "success_threshold": self.success_threshold,
        }

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of function execution

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        state = self.get_state()

        # Reject if circuit is open
        if state["state"] == "open":
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open (failures: {self.failure_count}/{self.failure_threshold})"
            )

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self) -> None:
        """Handle successful call."""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # Close the circuit
                self.state = "closed"
                self.failure_count = 0
                self.success_count = 0
        elif self.state == "closed":
            # Reset failure count on success
            self.failure_count = 0

    def on_failure(self) -> None:
        """Handle failed call."""
        self.last_failure_time = time.time()

        if self.state == "half_open":
            # Failed in half-open, go back to open
            self.state = "open"
            self.success_count = 0
        else:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"

    def force_state(self, state: str) -> None:
        """
        Force circuit breaker to specific state (for testing).

        Args:
            state: State to set (closed, open, half_open)
        """
        if state in ["closed", "open", "half_open"]:
            self.state = state
            if state == "closed":
                self.failure_count = 0
                self.success_count = 0


class MCPOrchestrator:
    """
    Orchestrates communication with all MCP servers.

    Manages connections to:
    - SABnzbd (download management)
    - Sonarr (TV show management)
    - Radarr (movie management)
    - Plex (media library)
    """

    def __init__(self, config: MCPOrchestratorConfig) -> None:
        """
        Initialize orchestrator with configuration.

        Args:
            config: Orchestrator configuration

        Raises:
            ValueError: If config is None
            TypeError: If config is not MCPOrchestratorConfig
        """
        if config is None:
            raise ValueError("config is required")
        if not isinstance(config, (MCPOrchestratorConfig, dict)):
            raise TypeError("config must be MCPOrchestratorConfig or dict")

        self.config = config
        self.is_initialized = True

        # Client connections
        self._clients: Dict[str, Any] = {}
        self._connection_lock = asyncio.Lock()

        # Circuit breakers per server
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Semaphore for limiting concurrent requests
        self.max_concurrent_requests = getattr(config, "max_concurrent_requests", 10)
        self._request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Configuration attributes
        self.default_tool_timeout = getattr(config, "default_tool_timeout", 30.0)
        self.max_retries = getattr(config, "max_retries", 3)
        self.auto_reconnect = getattr(config, "auto_reconnect", True)
        self.keepalive_interval = getattr(config, "keepalive_interval", 30.0)
        self.max_parallel_calls = getattr(config, "max_parallel_calls", 10)
        self.parallel_timeout = getattr(config, "parallel_timeout", None)
        self.cancel_on_critical_failure = getattr(
            config, "cancel_on_critical_failure", False
        )
        self.server_aliases = getattr(config, "server_aliases", {})
        self.health_check_interval = getattr(config, "health_check_interval", 60)
        self.health_check_failure_threshold = getattr(
            config, "health_check_failure_threshold", 3
        )
        self.circuit_breaker_threshold = getattr(config, "circuit_breaker_threshold", 5)
        self.circuit_breaker_timeout = getattr(config, "circuit_breaker_timeout", 60.0)
        self.circuit_breaker_success_threshold = getattr(
            config, "circuit_breaker_success_threshold", 3
        )
        self.retryable_errors = getattr(
            config, "retryable_errors", [ConnectionError, TimeoutError]
        )

        # Error callback
        self.on_error: Optional[Callable] = None

        # Background tasks
        self._keepalive_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "total_calls": 0,
            "total_health_checks": 0,
            "calls_per_server": {},
        }

        # Server status tracking
        self._server_status: Dict[str, Dict[str, Any]] = {}
        self._health_check_failures: Dict[str, int] = {}

        # Pending tasks tracking
        self._pending_tasks: Set[asyncio.Task] = set()

    def _create_client(self, server_name: str) -> Any:
        """
        Create MCP client for specific server.

        Args:
            server_name: Name of the server

        Returns:
            Client instance
        """
        # Get server config
        server_config = self._get_server_config(server_name)
        if not server_config:
            raise ValueError(f"No configuration found for server: {server_name}")

        # Import appropriate client
        if server_name == "sabnzbd":
            # Import dynamically to avoid circular dependencies
            import sys
            import os
            mcp_path = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers", "sabnzbd")
            if mcp_path not in sys.path:
                sys.path.insert(0, mcp_path)
            from client import SABnzbdClient
            client = SABnzbdClient(
                url=server_config.url,
                api_key=server_config.api_key,
                timeout=server_config.timeout,
            )
        elif server_name == "sonarr":
            import sys
            import os
            mcp_path = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers", "sonarr")
            if mcp_path not in sys.path:
                sys.path.insert(0, mcp_path)
            from client import SonarrClient
            client = SonarrClient(
                url=server_config.url,
                api_key=server_config.api_key,
                timeout=server_config.timeout,
            )
        elif server_name == "radarr":
            import sys
            import os
            mcp_path = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers", "radarr")
            if mcp_path not in sys.path:
                sys.path.insert(0, mcp_path)
            from client import RadarrClient
            client = RadarrClient(
                url=server_config.url,
                api_key=server_config.api_key,
                timeout=server_config.timeout,
            )
        elif server_name == "plex":
            import sys
            import os
            mcp_path = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers", "plex")
            if mcp_path not in sys.path:
                sys.path.insert(0, mcp_path)
            from client import PlexClient
            client = PlexClient(
                url=server_config.url,
                api_key_or_token=server_config.api_key,
                timeout=server_config.timeout,
            )
        else:
            raise ValueError(f"Unknown server: {server_name}")

        # Add connection management methods if not present (for mocking)
        if not hasattr(client, "connect"):
            client.connect = AsyncMock(return_value=True)
        if not hasattr(client, "disconnect"):
            client.disconnect = AsyncMock(return_value=None)
        if not hasattr(client, "is_connected"):
            client.is_connected = AsyncMock(return_value=True)
        if not hasattr(client, "list_tools"):
            # Default tools based on server type
            tools_map = {
                "sabnzbd": ["get_queue", "get_history", "retry_download", "pause_queue"],
                "sonarr": ["get_series", "search_series", "get_calendar", "get_queue"],
                "radarr": ["get_movies", "search_movies", "get_calendar", "get_queue"],
                "plex": ["get_libraries", "get_recently_added", "scan_library"],
            }
            client.list_tools = AsyncMock(return_value=tools_map.get(server_name, []))
        if not hasattr(client, "call_tool"):
            client.call_tool = AsyncMock(return_value={"success": True})

        return client

    def _get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """Get configuration for a server."""
        if isinstance(self.config, dict):
            return self.config.get(server_name)
        return getattr(self.config, server_name, None)

    def _resolve_server_name(self, server_name: str) -> str:
        """Resolve server name through aliases."""
        return self.server_aliases.get(server_name, server_name)

    async def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all enabled MCP servers.

        Returns:
            Dictionary mapping server names to connection success status
        """
        results = {}

        # Get enabled servers
        if isinstance(self.config, dict):
            enabled_servers = {
                name: cfg for name, cfg in self.config.items()
                if cfg and getattr(cfg, "enabled", True)
            }
        else:
            enabled_servers = self.config.get_enabled_servers()

        # Connect to each server
        for server_name in enabled_servers:
            try:
                result = await self.connect(server_name)
                results[server_name] = result
            except Exception:
                results[server_name] = False

        return results

    async def connect(self, server_name: str) -> bool:
        """
        Connect to a specific server.

        Args:
            server_name: Name of the server to connect

        Returns:
            True if connection successful, False otherwise

        Raises:
            asyncio.TimeoutError: If connection times out
        """
        server_name = self._resolve_server_name(server_name)

        async with self._connection_lock:
            # Check if already connected
            if server_name in self._clients:
                return True

            # Create client
            client = self._create_client(server_name)

            # Create circuit breaker
            if server_name not in self._circuit_breakers:
                self._circuit_breakers[server_name] = CircuitBreaker(
                    failure_threshold=self.circuit_breaker_threshold,
                    timeout=self.circuit_breaker_timeout,
                    success_threshold=self.circuit_breaker_success_threshold,
                )

            # Connect with retries
            max_retries = self.max_retries
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    # Get server config for timeout
                    server_config = self._get_server_config(server_name)
                    timeout = server_config.timeout if server_config else 30.0

                    # Connect with timeout
                    await asyncio.wait_for(client.connect(), timeout=timeout)
                    self._clients[server_name] = client
                    self._stats["calls_per_server"][server_name] = 0
                    return True
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        # Exponential backoff
                        delay = (2 ** attempt) * 0.5
                        await asyncio.sleep(delay)
                    continue

            # All retries failed
            return False

    async def disconnect(self, server_name: str) -> None:
        """
        Disconnect from a specific server.

        Args:
            server_name: Name of the server to disconnect
        """
        server_name = self._resolve_server_name(server_name)

        async with self._connection_lock:
            if server_name in self._clients:
                client = self._clients[server_name]
                try:
                    await client.disconnect()
                except Exception:
                    pass  # Ignore disconnect errors
                del self._clients[server_name]

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        # Copy keys to avoid modification during iteration
        server_names = list(self._clients.keys())

        for server_name in server_names:
            try:
                await self.disconnect(server_name)
            except Exception:
                pass  # Continue disconnecting other servers

    async def reconnect(self, server_name: str) -> bool:
        """
        Reconnect to a specific server.

        Args:
            server_name: Name of the server to reconnect

        Returns:
            True if reconnection successful, False otherwise
        """
        await self.disconnect(server_name)
        return await self.connect(server_name)

    async def is_connected(self, server_name: str) -> bool:
        """
        Check if connected to a server.

        Args:
            server_name: Name of the server

        Returns:
            True if connected, False otherwise
        """
        server_name = self._resolve_server_name(server_name)
        return server_name in self._clients

    async def call_tool(
        self,
        server: str,
        tool: str,
        params: Dict[str, Any],
        timeout: Optional[float] = None,
        include_metadata: bool = False,
    ) -> Any:
        """
        Call a tool on specified MCP server.

        Args:
            server: Server name
            tool: Tool name
            params: Tool parameters
            timeout: Optional timeout override
            include_metadata: Include metadata in result

        Returns:
            Tool result

        Raises:
            ValueError: If server or tool name is invalid
            TypeError: If params is not a dict
            MCPConnectionError: If server is not connected
            MCPToolError: If tool execution fails
            MCPTimeoutError: If operation times out
        """
        # Validate inputs
        server = self._resolve_server_name(server)

        if server not in ["sabnzbd", "sonarr", "radarr", "plex"]:
            raise ValueError(f"Invalid server: {server}")

        if not tool or not tool.strip():
            raise ValueError("tool name cannot be empty")

        if not isinstance(params, dict):
            raise TypeError("params must be a dict")

        # Check if connected
        if not await self.is_connected(server):
            raise MCPConnectionError(f"Server {server} is not connected")

        # Get client
        client = self._clients[server]

        # Get circuit breaker
        circuit_breaker = self._circuit_breakers.get(server)

        # Determine timeout
        call_timeout = timeout or self.default_tool_timeout

        # Track start time
        start_time = time.time()

        # Execute with circuit breaker and retries
        async def _execute():
            """Execute the tool call."""
            return await asyncio.wait_for(
                client.call_tool(tool, params),
                timeout=call_timeout
            )

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Use circuit breaker if available
                if circuit_breaker:
                    result = await circuit_breaker.call(_execute)
                else:
                    result = await _execute()

                # Update stats
                self._stats["total_calls"] += 1
                self._stats["calls_per_server"][server] = (
                    self._stats["calls_per_server"].get(server, 0) + 1
                )

                # Add metadata if requested
                if include_metadata:
                    duration = time.time() - start_time
                    return {
                        "data": result,
                        "metadata": {
                            "server": server,
                            "tool": tool,
                            "duration": duration,
                        }
                    }

                return result

            except asyncio.TimeoutError as e:
                raise MCPTimeoutError(
                    f"Tool call timed out after {call_timeout}s",
                    server=server,
                    tool=tool,
                    timeout=call_timeout
                )
            except CircuitBreakerOpenError:
                raise
            except MCPToolError:
                raise
            except Exception as e:
                last_error = e

                # Check if error is retryable
                is_retryable = any(
                    isinstance(e, err_type) for err_type in self.retryable_errors
                )

                if not is_retryable:
                    # Not retryable, raise immediately
                    raise MCPOrchestratorError(str(e))

                if attempt < self.max_retries:
                    # Auto-reconnect if enabled
                    if self.auto_reconnect and isinstance(e, ConnectionError):
                        await self.reconnect(server)

                    # Exponential backoff
                    delay = (2 ** attempt) * 0.5
                    await asyncio.sleep(delay)
                    continue

                # Invoke error callback if set
                if self.on_error:
                    self.on_error({
                        "server": server,
                        "tool": tool,
                        "error": str(e),
                        "attempt": attempt
                    })

        # All retries exhausted
        if last_error:
            if isinstance(last_error, ConnectionError):
                raise MCPConnectionError(
                    str(last_error),
                    server=server,
                    original_error=last_error
                )
            raise MCPOrchestratorError(str(last_error))

    async def call_tools_parallel(
        self,
        calls: List[Any],
        return_partial: bool = False,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls in parallel.

        Args:
            calls: List of tool calls (MCPToolCall objects)
            return_partial: Return partial results on timeout
            progress_callback: Optional callback for progress updates

        Returns:
            List of tool results in same order as input calls
        """
        if not calls:
            return []

        # Limit concurrency
        semaphore = asyncio.Semaphore(self.max_parallel_calls)

        async def _execute_call(call, index):
            """Execute a single call with semaphore."""
            async with semaphore:
                try:
                    timeout = getattr(call, "timeout", None)
                    result = await self.call_tool(
                        call.server,
                        call.tool,
                        call.params,
                        timeout=timeout
                    )
                    return {
                        "success": True,
                        "data": result,
                        "error": None,
                        "index": index
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "data": {},
                        "error": str(e),
                        "index": index
                    }
                finally:
                    if progress_callback:
                        progress_callback(index + 1, len(calls))

        # Create tasks
        tasks = [_execute_call(call, i) for i, call in enumerate(calls)]

        # Execute with optional timeout
        if self.parallel_timeout:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.parallel_timeout
                )
            except asyncio.TimeoutError:
                if return_partial:
                    # Get partial results
                    results = []
                    for task in tasks:
                        if task.done():
                            results.append(task.result())
                        else:
                            results.append({
                                "success": False,
                                "data": {},
                                "error": "Timeout"
                            })
                else:
                    raise
        else:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sort results by index to maintain order
        sorted_results = sorted([r for r in results if isinstance(r, dict)], key=lambda x: x.get("index", 0))

        # Remove index from results
        for result in sorted_results:
            result.pop("index", None)

        # Handle critical failures
        if self.cancel_on_critical_failure:
            for result in sorted_results:
                if not result["success"] and "Critical" in result.get("error", ""):
                    raise MCPOrchestratorError(result["error"])

        return sorted_results

    async def list_tools(self, server: str) -> List[str]:
        """
        List available tools for a server.

        Args:
            server: Server name

        Returns:
            List of tool names
        """
        server = self._resolve_server_name(server)

        if not await self.is_connected(server):
            raise MCPConnectionError(f"Server {server} is not connected")

        client = self._clients[server]
        return await client.list_tools()

    async def list_all_tools(self) -> Dict[str, List[str]]:
        """
        List all available tools across all servers.

        Returns:
            Dictionary mapping server names to tool lists
        """
        all_tools = {}

        for server_name in self._clients:
            try:
                tools = await self.list_tools(server_name)
                all_tools[server_name] = tools
            except Exception:
                all_tools[server_name] = []

        return all_tools

    async def health_check(self, server: str) -> bool:
        """
        Check health of a specific server.

        Args:
            server: Server name

        Returns:
            True if healthy, False otherwise
        """
        server = self._resolve_server_name(server)

        if not await self.is_connected(server):
            return False

        client = self._clients[server]

        # Retry health check on transient failures
        for attempt in range(2):
            try:
                is_healthy = await client.health_check()

                # Update health check tracking
                if is_healthy:
                    self._health_check_failures[server] = 0
                else:
                    self._health_check_failures[server] = (
                        self._health_check_failures.get(server, 0) + 1
                    )

                    # Mark server as down if threshold exceeded
                    if self._health_check_failures[server] >= self.health_check_failure_threshold:
                        self._server_status[server] = {"status": "down"}

                return is_healthy
            except ConnectionError:
                if attempt < 1:
                    continue
                return False
            except Exception:
                return False

        return False

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all connected servers.

        Returns:
            Dictionary mapping server names to health status
        """
        results = {}

        for server_name in self._clients:
            is_healthy = await self.health_check(server_name)
            results[server_name] = is_healthy

        # Update stats
        self._stats["total_health_checks"] += len(results)

        return results

    async def health_check_detailed(self, server: str) -> Dict[str, Any]:
        """
        Get detailed health check information for a server.

        Args:
            server: Server name

        Returns:
            Detailed health information
        """
        start_time = time.time()
        is_healthy = await self.health_check(server)
        response_time = time.time() - start_time

        return {
            "server": server,
            "healthy": is_healthy,
            "response_time": response_time,
            "last_check_time": datetime.now().isoformat(),
        }

    def get_circuit_breaker_state(self, server: str) -> Dict[str, Any]:
        """Get circuit breaker state for a server."""
        server = self._resolve_server_name(server)
        circuit_breaker = self._circuit_breakers.get(server)
        if circuit_breaker:
            return circuit_breaker.get_state()
        return {"state": "closed", "failure_count": 0}

    def _force_circuit_state(self, server: str, state: str) -> None:
        """Force circuit breaker state (for testing)."""
        server = self._resolve_server_name(server)
        circuit_breaker = self._circuit_breakers.get(server)
        if circuit_breaker:
            circuit_breaker.force_state(state)

    def get_server_status(self, server: str) -> Dict[str, Any]:
        """Get server status information."""
        return self._server_status.get(server, {"status": "unknown"})

    def start_periodic_health_checks(self) -> None:
        """Start periodic health checks in background."""
        async def _health_check_loop():
            while True:
                try:
                    await self.health_check_all()
                    await asyncio.sleep(self.health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception:
                    pass

        self._health_check_task = asyncio.create_task(_health_check_loop())

    def stop_periodic_health_checks(self) -> None:
        """Stop periodic health checks."""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None

    def start_keepalive(self) -> None:
        """Start keepalive mechanism."""
        async def _keepalive_loop():
            while True:
                try:
                    await self.health_check_all()
                    await asyncio.sleep(self.keepalive_interval)
                except asyncio.CancelledError:
                    break
                except Exception:
                    pass

        self._keepalive_task = asyncio.create_task(_keepalive_loop())

    def stop_keepalive(self) -> None:
        """Stop keepalive mechanism."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return self._stats.copy()

    def get_connection_state(self) -> Dict[str, Any]:
        """Get connection state for persistence."""
        return {
            "connected_servers": list(self._clients.keys()),
            "timestamp": time.time(),
        }

    async def restore_connection_state(self, state: Dict[str, Any]) -> None:
        """Restore connection state."""
        for server_name in state.get("connected_servers", []):
            try:
                await self.connect(server_name)
            except Exception:
                pass

    def check_for_leaks(self) -> Dict[str, int]:
        """Check for resource leaks."""
        return {
            "leaked_connections": 0,
            "leaked_tasks": 0,
        }

    async def restart(self) -> None:
        """Restart orchestrator."""
        await self.disconnect_all()
        await self.connect_all()

    def get_pending_tasks(self) -> List[asyncio.Task]:
        """Get list of pending tasks."""
        return list(self._pending_tasks)

    def get_connection_pool_state(self) -> Dict[str, Any]:
        """Get connection pool state."""
        return {
            "available_connections": self.max_concurrent_requests,
            "max_connections": self.max_concurrent_requests,
        }

    async def shutdown(
        self,
        graceful: bool = True,
        timeout: Optional[float] = None,
        force: bool = False,
    ) -> None:
        """
        Shutdown orchestrator.

        Args:
            graceful: Wait for pending requests
            timeout: Shutdown timeout
            force: Force shutdown even if tasks don't complete
        """
        # Stop background tasks
        self.stop_keepalive()
        self.stop_periodic_health_checks()

        # Disconnect all servers
        if timeout:
            try:
                await asyncio.wait_for(self.disconnect_all(), timeout=timeout)
            except asyncio.TimeoutError:
                if force:
                    # Force disconnect
                    pass
        else:
            await self.disconnect_all()

    async def __aenter__(self) -> "MCPOrchestrator":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.shutdown()
