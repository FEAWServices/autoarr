"""
Radarr MCP Server Package.

This package provides a Model Context Protocol (MCP) server for Radarr,
enabling LLM-based interactions with Radarr movie management.
"""

from .client import RadarrClient, RadarrClientError, RadarrConnectionError
from .models import (
    Command,
    ErrorResponse,
    Movie,
    MovieFile,
    Queue,
    QueueRecord,
    SystemStatus,
    WantedMissing,
)
from .server import RadarrMCPServer

__all__ = [
    "RadarrClient",
    "RadarrClientError",
    "RadarrConnectionError",
    "RadarrMCPServer",
    "Movie",
    "MovieFile",
    "Command",
    "Queue",
    "QueueRecord",
    "WantedMissing",
    "SystemStatus",
    "ErrorResponse",
]

__version__ = "0.1.0"
