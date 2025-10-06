#!/usr/bin/env python
"""
Startup script for the AutoArr FastAPI Gateway.

This script starts the FastAPI server with proper configuration.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from api.config import get_settings


def main():
    """Start the FastAPI server."""
    settings = get_settings()

    print(f"Starting AutoArr FastAPI Gateway on {settings.host}:{settings.port}")
    print(f"Environment: {settings.app_env}")
    print(f"Docs available at: http://{settings.host}:{settings.port}{settings.docs_url}")
    print(f"API available at: http://{settings.host}:{settings.port}{settings.api_v1_prefix}")

    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload or settings.app_env == "development",
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
