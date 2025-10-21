"""
Core module for AutoArr MCP Orchestrator.

This module provides the main orchestration layer for coordinating
all MCP server communications.
"""

from .config import MCPOrchestratorConfig, ServerConfig
from .exceptions import (CircuitBreakerOpenError, MCPConnectionError,
                         MCPOrchestratorError, MCPTimeoutError, MCPToolError)
from .mcp_orchestrator import CircuitBreaker, MCPOrchestrator

__all__ = [
    # Main orchestrator
    "MCPOrchestrator",
    "CircuitBreaker",
    # Configuration
    "MCPOrchestratorConfig",
    "ServerConfig",
    # Exceptions
    "MCPOrchestratorError",
    "MCPConnectionError",
    "MCPToolError",
    "MCPTimeoutError",
    "CircuitBreakerOpenError",
]
