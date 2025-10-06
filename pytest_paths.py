"""
Pytest plugin to set up Python paths before test collection.

This must be loaded via pytest_plugins in conftest or via -p flag.
"""

import sys
from pathlib import Path

# Set up paths at module import time (happens before pytest collection)
_root_dir = Path(__file__).parent
_root_path = str(_root_dir)
if _root_path not in sys.path:
    sys.path.insert(0, _root_path)

_mcp_path = str(_root_dir / "mcp-servers")
if _mcp_path not in sys.path:
    sys.path.insert(0, _mcp_path)


def pytest_load_initial_conftests(early_config, parser, args):
    """
    Hook that runs very early, before conftest files are loaded.

    This is the earliest hook and ensures paths are set up before any test modules are imported.
    """
    root_dir = Path(__file__).parent

    # Add root directory
    root_path = str(root_dir)
    if root_path not in sys.path:
        sys.path.insert(0, root_path)
        print(f"[pytest_paths] Added {root_path} to sys.path")

    # Add mcp-servers directory
    mcp_path = str(root_dir / "mcp-servers")
    if mcp_path not in sys.path:
        sys.path.insert(0, mcp_path)
        print(f"[pytest_paths] Added {mcp_path} to sys.path")
