"""
FastAPI Gateway main application.

This module initializes the FastAPI application, configures middleware,
and sets up all API routes.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import get_database, init_database
from .dependencies import shutdown_orchestrator
from .middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    add_security_headers,
)
from .routers import configuration, downloads, health, mcp, media, movies
from .routers import settings as settings_router
from .routers import shows

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Manages startup and shutdown events.
    """
    # Get settings (allows mocking in tests)
    settings = get_settings()

    # Startup
    try:
        logger.info("Starting AutoArr FastAPI Gateway...")
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"Log level: {settings.log_level}")

        # Initialize database
        if settings.database_url:
            logger.info("Initializing database...")
            db = init_database(settings.database_url)
            await db.init_db()
            logger.info("Database initialized successfully")
        else:
            logger.warning("No DATABASE_URL configured, settings will not persist")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Continue to yield so shutdown can run

    yield

    # Shutdown
    logger.info("Shutting down AutoArr FastAPI Gateway...")
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
)


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=_settings.cors_allow_credentials,
    allow_methods=_settings.cors_allow_methods,
    allow_headers=_settings.cors_allow_headers,
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

# Configuration audit endpoints
app.include_router(
    configuration.router,
    prefix=f"{_settings.api_v1_prefix}/config",
    tags=["configuration"],
)


# ============================================================================
# Static Files
# ============================================================================

# Mount static files directory
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/", tags=["root"])
async def root() -> dict:
    """
    Root endpoint with API information.

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
