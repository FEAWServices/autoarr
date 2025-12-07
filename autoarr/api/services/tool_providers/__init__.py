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
Tool Providers Package for AutoArr.

This package contains service-specific tool providers that expose
service APIs as tools for the LLM chat agent.

Each provider implements the BaseToolProvider interface and provides
version-aware tool definitions for its service.

Available Providers:
- SABnzbdToolProvider: SABnzbd download client tools
- (Sonarr, Radarr, Plex providers to be added)

Usage:
    from autoarr.api.services.tool_providers import SABnzbdToolProvider
    from autoarr.api.services.tool_provider import get_tool_registry

    # Register providers
    registry = get_tool_registry()
    registry.register_provider(SABnzbdToolProvider())

    # Get all available tools
    tools = await registry.get_available_tools()
"""

from .sabnzbd_provider import SABnzbdToolProvider

__all__ = [
    "SABnzbdToolProvider",
]
