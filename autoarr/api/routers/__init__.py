"""
API routers for the FastAPI Gateway.

This package contains all API route handlers organized by service.
"""

from . import downloads, health, mcp, media, movies, shows

__all__ = ["health", "mcp", "downloads", "shows", "movies", "media"]
