#!/usr/bin/env python3
"""
AutoArr Launcher - Entry point for PyInstaller bundled executable.

This script serves as the entry point when AutoArr is bundled as a native
executable using PyInstaller. It handles:
- Multiprocessing support for Windows
- Static file serving for the frontend
- Graceful shutdown
- Environment configuration

Usage:
    python autoarr_launcher.py
    # or when bundled:
    ./autoarr  # Linux/macOS
    autoarr.exe  # Windows
"""

import logging
import multiprocessing
import os
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("autoarr.launcher")


def get_base_path() -> Path:
    """Get the base path for the application.

    When running as a PyInstaller bundle, sys._MEIPASS contains the path
    to the temporary folder where the bundle is extracted.
    When running normally, use the script's directory.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running normally
        return Path(__file__).parent


def get_data_path() -> Path:
    """Get the path for persistent data storage.

    This is separate from the base path and persists across runs.
    """
    # Use user's home directory for data
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    data_path = base / "AutoArr"
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def setup_environment() -> None:
    """Configure environment variables for the bundled application."""
    base_path = get_base_path()
    data_path = get_data_path()

    # Set default environment variables if not already set
    # Note: 0.0.0.0 is intentional for container/native app binding
    defaults = {
        "APP_ENV": "production",
        "LOG_LEVEL": "INFO",
        "HOST": "0.0.0.0",  # nosec B104 - intentional for container binding
        "PORT": "8088",
        "DATABASE_URL": f"sqlite:///{data_path / 'autoarr.db'}",
        "REDIS_URL": "memory://",
    }

    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value

    # Set the static files directory
    static_dir = base_path / "autoarr" / "ui" / "dist"
    if static_dir.exists():
        os.environ["STATIC_FILES_DIR"] = str(static_dir)
        logger.info(f"Static files directory: {static_dir}")
    else:
        logger.warning(f"Static files directory not found: {static_dir}")

    logger.info(f"Data directory: {data_path}")
    logger.info(f"Database: {os.environ['DATABASE_URL']}")


def signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, exiting...")
    sys.exit(0)


def main() -> None:
    """Main entry point for the AutoArr application."""
    # Required for Windows multiprocessing support
    multiprocessing.freeze_support()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure environment
    setup_environment()

    # Print startup banner
    print("=" * 60)
    print("  AutoArr - Intelligent Media Automation")
    print("=" * 60)
    print(f"  Version: 1.0.0")
    print(f"  Host: {os.environ.get('HOST', '0.0.0.0')}")  # nosec B104
    print(f"  Port: {os.environ.get('PORT', '8088')}")
    print(f"  Data: {get_data_path()}")
    print("=" * 60)
    print()

    # Import and run the application
    try:
        import uvicorn

        from autoarr.api.main import app

        host = os.environ.get("HOST", "0.0.0.0")  # nosec B104
        port = int(os.environ.get("PORT", "8088"))

        logger.info(f"Starting AutoArr on http://{host}:{port}")
        print(f"  Open http://localhost:{port} in your browser")
        print()

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=os.environ.get("LOG_LEVEL", "info").lower(),
            access_log=True,
        )
    except ImportError as e:
        logger.error(f"Failed to import application: {e}")
        print(f"Error: {e}")
        print("Make sure all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
