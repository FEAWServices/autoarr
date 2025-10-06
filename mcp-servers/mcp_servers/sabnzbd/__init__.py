"""
SABnzbd MCP Server Package.

This package provides MCP (Model Context Protocol) integration for SABnzbd,
enabling LLMs to interact with SABnzbd download manager.
"""

from .client import SABnzbdClient, SABnzbdClientError, SABnzbdConnectionError
from .server import SABnzbdMCPServer

__all__ = [
    "SABnzbdClient",
    "SABnzbdClientError",
    "SABnzbdConnectionError",
    "SABnzbdMCPServer",
]

__version__ = "0.1.0"
