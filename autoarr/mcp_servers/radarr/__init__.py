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
