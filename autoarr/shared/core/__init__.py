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
Core module for AutoArr MCP Orchestrator.

This module provides the main orchestration layer for coordinating
all MCP server communications.
"""

from .config import MCPOrchestratorConfig, ServerConfig
from .exceptions import (
    CircuitBreakerOpenError,
    MCPConnectionError,
    MCPOrchestratorError,
    MCPTimeoutError,
    MCPToolError,
)
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
