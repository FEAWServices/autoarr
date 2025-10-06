"""
Configuration models for MCP Orchestrator.

This module defines the configuration data structures for the MCP Orchestrator,
including server configurations and orchestrator settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""

    name: str
    url: str
    api_key: str
    enabled: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Server name cannot be empty")
        if not self.url:
            raise ValueError("Server URL cannot be empty")
        if not self.api_key:
            raise ValueError("API key cannot be empty")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


@dataclass
class MCPOrchestratorConfig:
    """Configuration for MCP Orchestrator."""

    # Server configurations
    sabnzbd: Optional[ServerConfig] = None
    sonarr: Optional[ServerConfig] = None
    radarr: Optional[ServerConfig] = None
    plex: Optional[ServerConfig] = None

    # Connection pool settings
    connection_pool_size: int = 10
    max_concurrent_requests: int = 10

    # Health check settings
    health_check_interval: int = 60
    health_check_failure_threshold: int = 3

    # Circuit breaker settings
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    circuit_breaker_success_threshold: int = 3

    # Retry settings
    default_tool_timeout: float = 30.0
    max_retries: int = 3
    retryable_errors: List[type] = field(
        default_factory=lambda: [ConnectionError, TimeoutError]
    )

    # Auto-reconnect settings
    auto_reconnect: bool = True

    # Keepalive settings
    keepalive_interval: float = 30.0

    # Parallel execution settings
    max_parallel_calls: int = 10
    parallel_timeout: Optional[float] = None
    cancel_on_critical_failure: bool = False

    # Server aliases
    server_aliases: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.connection_pool_size <= 0:
            raise ValueError("Connection pool size must be positive")
        if self.health_check_interval <= 0:
            raise ValueError("Health check interval must be positive")

    def get_enabled_servers(self) -> Dict[str, ServerConfig]:
        """
        Get all enabled server configurations.

        Returns:
            Dictionary of enabled server configurations
        """
        enabled = {}
        for server_name in ["sabnzbd", "sonarr", "radarr", "plex"]:
            config = getattr(self, server_name, None)
            if config and config.enabled:
                enabled[server_name] = config
        return enabled

    def get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """
        Get configuration for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Server configuration or None if not found
        """
        # Check aliases first
        actual_name = self.server_aliases.get(server_name, server_name)
        return getattr(self, actual_name, None)
