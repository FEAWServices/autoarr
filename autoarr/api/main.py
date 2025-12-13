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
FastAPI Gateway main application.

This module initializes the FastAPI application, configures middleware,
and sets up all API routes.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .database import get_database, init_database
from .dependencies import get_orchestrator, shutdown_orchestrator
from .middleware import (ErrorHandlerMiddleware, RequestLoggingMiddleware,
                         add_security_headers)
from .rate_limiter import limiter
from .routers import (activity, chat, configuration, downloads, health, logs,
                      mcp, media, movies, onboarding, optimize, requests)
from .routers import settings as settings_router
from .routers import shows
from .routers.logs import setup_log_buffer_handler
from .services.event_bus import get_event_bus
from .services.websocket_bridge import (initialize_websocket_bridge,
                                        shutdown_websocket_bridge)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler.

    Manages startup and shutdown events.
    """
    # Get settings (allows mocking in tests)
    settings = get_settings()

    # Startup
    logger.info("Starting AutoArr FastAPI Gateway...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Log level: {settings.log_level}")

    # Set up log buffer handler for UI log viewer
    setup_log_buffer_handler()

    # Initialize database
    if settings.database_url:
        try:
            logger.info("Initializing database...")
            db = init_database(settings.database_url)
            await db.init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Critical: Database initialization failed: {e}")
            raise  # Fail fast - don't start app without database if one is configured
    else:
        logger.warning("No DATABASE_URL configured, settings will not persist")

    # Initialize WebSocket-EventBus bridge for real-time updates
    try:
        logger.info("Initializing WebSocket-EventBus bridge...")
        event_bus = get_event_bus()
        await initialize_websocket_bridge(event_bus, manager)
        logger.info("WebSocket bridge initialized successfully")
    except Exception as e:
        logger.error(f"Warning: WebSocket bridge initialization failed: {e}")
        # Don't fail startup if WebSocket bridge fails - it's not critical

    # Perform application warmup to preload caches and reduce first-request latency
    try:
        logger.info("Performing application warmup...")
        from .routers.health import perform_warmup

        warmup_result = await perform_warmup()
        logger.info(
            f"Warmup completed in {warmup_result['total_duration_ms']}ms "
            f"({len(warmup_result['tasks'])} tasks)"
        )
    except Exception as e:
        logger.warning(f"Warmup failed (non-critical): {e}")
        # Don't fail startup if warmup fails - app can still serve requests

    # Initialize MCP orchestrator and connect to services configured via env vars
    try:
        logger.info("Initializing MCP orchestrator...")
        # get_orchestrator is an async generator, so we need to iterate it
        async for orchestrator in get_orchestrator():
            connected = orchestrator.get_connected_servers()
            if connected:
                logger.info(f"MCP orchestrator connected to: {', '.join(connected)}")
            else:
                logger.info("MCP orchestrator initialized (no services configured)")
            break  # Only need first yield
    except Exception as e:
        logger.warning(f"MCP orchestrator initialization failed (non-critical): {e}")
        # Don't fail startup - services can still be configured later

    # Start monitoring service if enabled
    if settings.monitoring_enabled:
        try:
            logger.info("Starting monitoring service...")
            from .dependencies import get_monitoring_service

            async for monitoring_service in get_monitoring_service():
                # Start monitoring in background task
                import asyncio

                monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())
                monitoring_service._monitoring_task = monitoring_task
                logger.info("Monitoring service started successfully")
                break  # Only need first yield
        except Exception as e:
            logger.warning(f"Monitoring service initialization failed (non-critical): {e}")
            # Don't fail startup - monitoring can be started later
    else:
        logger.info("Monitoring service disabled (monitoring_enabled=False)")

    yield

    # Shutdown
    logger.info("Shutting down AutoArr FastAPI Gateway...")

    # Stop monitoring service
    try:
        from .dependencies import shutdown_monitoring_service

        await shutdown_monitoring_service()
    except Exception as e:
        logger.error(f"Error shutting down monitoring service: {e}")

    # Shutdown WebSocket bridge
    try:
        await shutdown_websocket_bridge()
    except Exception as e:
        logger.error(f"Error shutting down WebSocket bridge: {e}")

    await shutdown_orchestrator()

    # Close database connections
    try:
        db = get_database()
        await db.close()
        logger.info("Database connections closed")
    except RuntimeError:
        pass  # Database was not initialized

    logger.info("Shutdown complete")


# Get settings for app configuration
_settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=_settings.app_name,
    description=_settings.app_description,
    version=_settings.app_version,
    docs_url=_settings.docs_url,
    redoc_url=_settings.redoc_url,
    openapi_url=_settings.openapi_url,
    lifespan=lifespan,
    redirect_slashes=True,  # Automatically redirect /path to /path/ if needed
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.get_cors_origins(),
    allow_credentials=_settings.cors_allow_credentials,
    allow_methods=_settings.get_cors_methods(),
    allow_headers=_settings.get_cors_headers(),
)

# Error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Security headers middleware
app.middleware("http")(add_security_headers)


# ============================================================================
# Router Configuration
# ============================================================================

# Health check endpoints (no prefix)
app.include_router(
    health.router,
    tags=["health"],
)

# MCP proxy endpoints
app.include_router(
    mcp.router,
    prefix=f"{_settings.api_v1_prefix}/mcp",
    tags=["mcp"],
)

# Downloads endpoints (SABnzbd)
app.include_router(
    downloads.router,
    prefix=f"{_settings.api_v1_prefix}/downloads",
    tags=["downloads"],
)

# Shows endpoints (Sonarr)
app.include_router(
    shows.router,
    prefix=f"{_settings.api_v1_prefix}/shows",
    tags=["shows"],
)

# Movies endpoints (Radarr)
app.include_router(
    movies.router,
    prefix=f"{_settings.api_v1_prefix}/movies",
    tags=["movies"],
)

# Media endpoints (Plex)
app.include_router(
    media.router,
    prefix=f"{_settings.api_v1_prefix}/media",
    tags=["media"],
)

# Settings endpoints
app.include_router(
    settings_router.router,
    prefix=f"{_settings.api_v1_prefix}/settings",
    tags=["settings"],
)

# Onboarding endpoints
app.include_router(
    onboarding.router,
    prefix=f"{_settings.api_v1_prefix}/onboarding",
    tags=["onboarding"],
)

# Configuration audit endpoints
app.include_router(
    configuration.router,
    prefix=f"{_settings.api_v1_prefix}/config",
    tags=["configuration"],
)

# Content request endpoints
app.include_router(
    requests.router,
    tags=["requests"],
)

# Chat endpoints (intelligent assistant)
app.include_router(
    chat.router,
    tags=["chat"],
)

# Logs endpoints
app.include_router(
    logs.router,
    prefix=f"{_settings.api_v1_prefix}/logs",
    tags=["logs"],
)

# Optimization assessment endpoints
app.include_router(
    optimize.router,
    prefix=f"{_settings.api_v1_prefix}/optimize",
    tags=["optimize"],
)

# Activity log endpoints
app.include_router(
    activity.router,
    prefix=f"{_settings.api_v1_prefix}/activity",
    tags=["activity"],
)


# ============================================================================
# Static Files
# ============================================================================

# Mount static files directory
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount UI static files (React app)
ui_dist_dir = Path(__file__).parent.parent / "ui" / "dist"
if ui_dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(ui_dist_dir / "assets")), name="assets")
    # Mount logos directory for PWA icons
    logos_dir = ui_dist_dir / "logos"
    if logos_dir.exists():
        app.mount("/logos", StaticFiles(directory=str(logos_dir)), name="logos")


# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/api", tags=["root"])
async def api_info() -> dict:
    """
    API information endpoint.

    Returns:
        dict: API information
    """
    return {
        "name": _settings.app_name,
        "version": _settings.app_version,
        "description": _settings.app_description,
        "docs": _settings.docs_url,
        "admin": "/static/admin.html",
        "health": "/health",
    }


@app.get("/ping", tags=["root"])
async def ping() -> dict:
    """
    Simple ping endpoint for health checks.

    Returns:
        dict: Pong response
    """
    return {"message": "pong"}


# ============================================================================
# WebSocket Endpoints
# ============================================================================


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection from list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send message to specific connection."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        """Send message to all active connections."""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                dead_connections.append(connection)

        # Remove failed connections to prevent memory leaks
        for connection in dead_connections:
            self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


@app.websocket(f"{_settings.api_v1_prefix}/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time updates.

    Clients can connect to receive real-time notifications about:
    - Configuration audit results
    - Download status updates
    - Content request status changes
    - Activity log entries
    """
    await manager.connect(websocket)
    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to AutoArr WebSocket",
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive and echo any client messages (for future use)
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")

            # For now, just acknowledge receipt
            await websocket.send_json({"type": "ack", "message": "Message received"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# PWA Root-Level Files
# ============================================================================
# Explicit routes for PWA files that must be served from root level
# (manifest.json, service workers, icons, etc.)


@app.get("/manifest.json", include_in_schema=False)
async def serve_manifest() -> FileResponse:
    """Serve PWA manifest.json from UI dist directory."""
    manifest_file = Path(__file__).parent.parent / "ui" / "dist" / "manifest.json"
    if manifest_file.exists():
        return FileResponse(str(manifest_file.resolve()), media_type="application/json")
    raise HTTPException(status_code=404, detail="manifest.json not found")


@app.get("/logo-192.png", include_in_schema=False)
async def serve_logo_192() -> FileResponse:
    """Serve PWA 192x192 icon from UI dist directory."""
    logo_file = Path(__file__).parent.parent / "ui" / "dist" / "logo-192.png"
    if logo_file.exists():
        return FileResponse(str(logo_file.resolve()), media_type="image/png")
    raise HTTPException(status_code=404, detail="logo-192.png not found")


@app.get("/logo-512.png", include_in_schema=False)
async def serve_logo_512() -> FileResponse:
    """Serve PWA 512x512 icon from UI dist directory."""
    logo_file = Path(__file__).parent.parent / "ui" / "dist" / "logo-512.png"
    if logo_file.exists():
        return FileResponse(str(logo_file.resolve()), media_type="image/png")
    raise HTTPException(status_code=404, detail="logo-512.png not found")


@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon() -> FileResponse:
    """Serve favicon from UI dist directory."""
    favicon_file = Path(__file__).parent.parent / "ui" / "dist" / "favicon.ico"
    if favicon_file.exists():
        return FileResponse(str(favicon_file.resolve()), media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="favicon.ico not found")


# ============================================================================
# UI Catch-all Route (SPA)
# ============================================================================


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str) -> FileResponse:
    """
    Catch-all route to serve the React SPA.

    Serves index.html for all routes, allowing React Router to handle
    client-side routing.

    Note: Static assets (JS, CSS, images) are served by FastAPI's
    StaticFiles mount at the root level, configured elsewhere.

    Args:
        full_path: The requested path (unused, kept for route matching)

    Returns:
        FileResponse: The index.html file for SPA routing
    """
    # Explicitly ignore the user-provided path for security
    # Static files are handled by StaticFiles mount, not this catch-all
    _ = full_path  # Mark as intentionally unused

    ui_dist_dir = Path(__file__).parent.parent / "ui" / "dist"
    index_file = ui_dist_dir / "index.html"

    if index_file.exists():
        return FileResponse(str(index_file.resolve()))

    # Fallback if UI not built
    raise HTTPException(status_code=503, detail="UI not available")


# ============================================================================
# Development Server (for testing)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=_settings.host,
        port=_settings.port,
        reload=_settings.reload,
        workers=_settings.workers,
        log_level=_settings.log_level.lower(),
    )
