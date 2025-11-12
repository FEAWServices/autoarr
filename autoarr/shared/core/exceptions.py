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
Custom exceptions for MCP Orchestrator.

This module defines the exception hierarchy for the MCP Orchestrator,
providing clear error handling and diagnostics for various failure scenarios.
"""

from typing import Any, Optional


class MCPOrchestratorError(Exception):
    """Base exception for all orchestrator errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """
        Initialize orchestrator error.

        Args:
            message: Error message
            **kwargs: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.context = kwargs


class MCPConnectionError(MCPOrchestratorError):
    """Exception raised when connection to MCP server fails."""

    def __init__(
        self,
        message: str,
        server: Optional[str] = None,
        original_error: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize connection error.

        Args:
            message: Error message
            server: Name of the server that failed
            original_error: Original exception that caused this error
            **kwargs: Additional error context
        """
        super().__init__(message, server=server, **kwargs)
        self.server = server
        self.original_error = original_error


class MCPToolError(MCPOrchestratorError):
    """Exception raised when tool operation fails."""

    def __init__(
        self, message: str, server: Optional[str] = None, tool: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        Initialize tool error.

        Args:
            message: Error message
            server: Name of the server
            tool: Name of the tool that failed
            **kwargs: Additional error context
        """
        super().__init__(message, server=server, tool=tool, **kwargs)
        self.server = server
        self.tool = tool


class MCPTimeoutError(MCPOrchestratorError):
    """Exception raised when operation times out."""

    def __init__(
        self,
        message: str,
        server: Optional[str] = None,
        tool: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize timeout error.

        Args:
            message: Error message
            server: Name of the server
            tool: Name of the tool that timed out
            timeout: Timeout value in seconds
            **kwargs: Additional error context
        """
        super().__init__(message, server=server, tool=tool, timeout=timeout, **kwargs)
        self.server = server
        self.tool = tool
        self.timeout = timeout


class CircuitBreakerOpenError(MCPOrchestratorError):
    """Exception raised when circuit breaker is open."""

    def __init__(self, message: str, server: Optional[str] = None, **kwargs: Any) -> None:
        """
        Initialize circuit breaker error.

        Args:
            message: Error message
            server: Name of the server with open circuit
            **kwargs: Additional error context
        """
        super().__init__(message, server=server, **kwargs)
        self.server = server
