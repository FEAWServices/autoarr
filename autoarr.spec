# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AutoArr native builds.

This configuration bundles the AutoArr application with:
- FastAPI backend
- Uvicorn ASGI server
- Frontend static files
- All Python dependencies

Build commands:
    # Standard build (folder)
    pyinstaller autoarr.spec --noconfirm

    # Single file build (slower startup, easier distribution)
    pyinstaller autoarr.spec --noconfirm --onefile

Platforms:
    - Windows x64
    - macOS x64 (Intel)
    - macOS ARM64 (Apple Silicon)
    - Linux x64
"""

import sys
from pathlib import Path

# Determine platform-specific settings
is_windows = sys.platform == 'win32'
is_macos = sys.platform == 'darwin'
is_linux = sys.platform.startswith('linux')

# Get the project root
project_root = Path(SPECPATH)

# Define paths
frontend_dist = project_root / 'autoarr' / 'ui' / 'dist'
autoarr_package = project_root / 'autoarr'

# Analysis configuration
a = Analysis(
    ['autoarr_launcher.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include frontend static files
        (str(frontend_dist), 'autoarr/ui/dist') if frontend_dist.exists() else (None, None),
    ],
    hiddenimports=[
        # FastAPI and dependencies
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        'starlette',
        'starlette.middleware',
        'starlette.routing',
        'starlette.responses',
        'starlette.staticfiles',

        # Uvicorn and ASGI
        'uvicorn',
        'uvicorn.config',
        'uvicorn.main',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.logging',
        'uvloop',
        'httptools',

        # Pydantic
        'pydantic',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'pydantic_settings',
        'pydantic_core',

        # Database
        'sqlalchemy',
        'sqlalchemy.ext.asyncio',
        'sqlalchemy.orm',
        'aiosqlite',
        'sqlite3',

        # HTTP clients
        'httpx',
        'aiohttp',

        # WebSocket
        'websockets',

        # JSON
        'json',
        'orjson',

        # Async
        'asyncio',
        'anyio',

        # Logging
        'logging',
        'logging.config',

        # AutoArr modules
        'autoarr',
        'autoarr.api',
        'autoarr.api.main',
        'autoarr.api.routers',
        'autoarr.api.services',
        'autoarr.api.models',
        'autoarr.shared',
        'autoarr.shared.core',
        'autoarr.mcp_servers',

        # Multiprocessing (Windows)
        'multiprocessing',
        'multiprocessing.resource_tracker',
        'multiprocessing.popen_spawn_win32' if is_windows else 'multiprocessing.popen_fork',

        # Email (optional, for notifications)
        'email',
        'email.mime',
        'email.mime.text',

        # Standard library commonly used
        'pathlib',
        'os',
        'sys',
        'signal',
        'typing',
        'datetime',
        'uuid',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude development/test packages
        'pytest',
        'pylint',
        'mypy',
        'black',
        'flake8',
        'isort',
        'bandit',
        'locust',
        'playwright',
        'coverage',

        # Exclude unused large packages
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tensorflow',
        'torch',
        'PIL',
        'cv2',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out None entries from datas
a.datas = [d for d in a.datas if d[0] is not None]

# PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='autoarr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console for server output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if available: 'assets/icon.ico' or 'assets/icon.icns'
)

# Collect all files into a folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='autoarr',
)

# macOS app bundle (optional)
if is_macos:
    app = BUNDLE(
        coll,
        name='AutoArr.app',
        icon=None,  # Add icon path: 'assets/icon.icns'
        bundle_identifier='com.autoarr.app',
        info_plist={
            'CFBundleName': 'AutoArr',
            'CFBundleDisplayName': 'AutoArr',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
        },
    )
