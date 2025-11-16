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
Sonarr MCP Server Package.

This package provides a Model Context Protocol (MCP) server for Sonarr,
enabling LLM-based interactions with Sonarr TV show management.
"""

from .client import SonarrClient, SonarrClientError, SonarrConnectionError
from .models import (
    Command,
    Episode,
    ErrorResponse,
    Queue,
    QueueRecord,
    Series,
    SystemStatus,
    WantedMissing,
)
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
