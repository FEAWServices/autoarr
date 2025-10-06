"""
Root conftest.py - sets up import paths before pytest starts.
"""

import sys
from pathlib import Path

# Add mcp-servers directory to Python path for imports
# This allows tests to import from the mcp-servers directory
mcp_servers_path = str(Path(__file__).parent / "mcp-servers")
if mcp_servers_path not in sys.path:
    sys.path.append(mcp_servers_path)  # append instead of insert to avoid conflicts
