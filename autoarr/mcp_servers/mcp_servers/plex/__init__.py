"""
Plex MCP Server Package.

This package provides a Model Context Protocol (MCP) server for Plex Media Server,
enabling LLM-based interactions with Plex media management and playback.
"""

from .client import PlexClient, PlexClientError, PlexConnectionError
from .models import (ErrorResponse, PlexHistoryRecord, PlexLibrary,
                     PlexMediaItem, PlexServerIdentity, PlexSession)
from .server import PlexMCPServer

__all__ = [
    "PlexClient",
    "PlexClientError",
    "PlexConnectionError",
    "PlexMCPServer",
    "PlexLibrary",
    "PlexMediaItem",
    "PlexSession",
    "PlexServerIdentity",
    "PlexHistoryRecord",
    "ErrorResponse",
]

__version__ = "0.1.0"
