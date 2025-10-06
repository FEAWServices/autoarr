# This MUST be at the absolute top before any other imports!
import sys
from pathlib import Path

_root = Path(__file__).parent
_root_str = str(_root)
_mcp_str = str(_root / "mcp-servers")

if _root_str not in sys.path:
    sys.path.insert(0, _root_str)
if _mcp_str not in sys.path:
    sys.path.insert(0, _mcp_str)

# Now safe to import
"""
Root conftest.py - sets up import paths before pytest starts.
"""
