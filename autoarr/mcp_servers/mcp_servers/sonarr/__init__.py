"""
Sonarr MCP Server Package.

This package provides a Model Context Protocol (MCP) server for Sonarr,
enabling LLM-based interactions with Sonarr TV show management.
"""

from .client import SonarrClient, SonarrClientError, SonarrConnectionError
from .models import (Command, Episode, ErrorResponse, Queue, QueueRecord,
                     Series, SystemStatus, WantedMissing)
from .server import SonarrMCPServer

__all__ = [
    "SonarrClient",
    "SonarrClientError",
    "SonarrConnectionError",
    "SonarrMCPServer",
    "Series",
    "Episode",
    "Command",
    "Queue",
    "QueueRecord",
    "WantedMissing",
    "SystemStatus",
    "ErrorResponse",
]

__version__ = "0.1.0"
