"""
FastAPI Gateway main application.

This module initializes the FastAPI application, configures middleware,
and sets up all API routes.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import get_settings
from .dependencies import shutdown_orchestrator
from .middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    add_security_headers,
)
from .routers import downloads, health, media, mcp, movies, shows
from .routers import settings as settings_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Manages startup and shutdown events.
    """
    # Startup
    logger.info("Starting AutoArr FastAPI Gateway...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Log level: {settings.log_level}")

    yield

    # Shutdown
    logger.info("Shutting down AutoArr FastAPI Gateway...")
    await shutdown_orchestrator()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
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
    prefix=f"{settings.api_v1_prefix}/mcp",
    tags=["mcp"],
)

# Downloads endpoints (SABnzbd)
app.include_router(
    downloads.router,
    prefix=f"{settings.api_v1_prefix}/downloads",
    tags=["downloads"],
)

# Shows endpoints (Sonarr)
app.include_router(
    shows.router,
    prefix=f"{settings.api_v1_prefix}/shows",
    tags=["shows"],
)

# Movies endpoints (Radarr)
app.include_router(
    movies.router,
    prefix=f"{settings.api_v1_prefix}/movies",
    tags=["movies"],
)

# Media endpoints (Plex)
app.include_router(
    media.router,
    prefix=f"{settings.api_v1_prefix}/media",
    tags=["media"],
)

# Settings endpoints
app.include_router(
    settings_router.router,
    prefix=f"{settings.api_v1_prefix}/settings",
    tags=["settings"],
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
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "docs": settings.docs_url,
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
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
