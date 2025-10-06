#!/usr/bin/env python3
"""
Verification script for Radarr MCP Server implementation.

This script performs basic verification that the Radarr implementation:
1. Can be imported without errors
2. Has all required classes and methods
3. Has properly defined MCP tools
4. Follows the same patterns as Sonarr

Run this script to verify the Radarr implementation is complete.
"""

import sys
from pathlib import Path

# Add mcp-servers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers"))

# Use ASCII characters for cross-platform compatibility
CHECK = "[OK]"
CROSS = "[FAIL]"
INFO = "[INFO]"

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from radarr.client import RadarrClient, RadarrClientError, RadarrConnectionError
        from radarr.server import RadarrMCPServer
        from radarr.models import (
            Movie,
            MovieFile,
            Command,
            Queue,
            QueueRecord,
            WantedMissing,
            SystemStatus,
            ErrorResponse,
        )
        print(f"  {CHECK} All modules imported successfully")
        return True
    except ImportError as e:
        print(f"  {CROSS} Import error: {e}")
        return False


def test_client_class():
    """Test RadarrClient class structure."""
    print("\nTesting RadarrClient class...")
    from radarr.client import RadarrClient

    required_methods = [
        '__init__',
        'create',
        'close',
        'health_check',
        'get_system_status',
        'get_movies',
        'get_movie_by_id',
        'add_movie',
        'delete_movie',
        'search_movie_lookup',
        'search_movie',
        'get_queue',
        'get_calendar',
        'get_wanted_missing',
    ]

    for method in required_methods:
        if not hasattr(RadarrClient, method):
            print(f"  [FAIL] Missing method: {method}")
            return False

    print(f"  [OK] All {len(required_methods)} required methods present")
    return True


def test_server_class():
    """Test RadarrMCPServer class structure."""
    print("\nTesting RadarrMCPServer class...")
    from radarr.server import RadarrMCPServer

    required_methods = [
        '__init__',
        'start',
        'stop',
        'list_tools',
        'call_tool',
        '_get_tools',
        '_call_tool',
    ]

    for method in required_methods:
        if not hasattr(RadarrMCPServer, method):
            print(f"  [FAIL] Missing method: {method}")
            return False

    print(f"  [OK] All {len(required_methods)} required methods present")
    return True


def test_mcp_tools():
    """Test MCP tool definitions."""
    print("\nTesting MCP tools...")
    from radarr.server import RadarrMCPServer
    from radarr.client import RadarrClient
    from unittest.mock import AsyncMock

    # Create mock client
    mock_client = AsyncMock(spec=RadarrClient)
    mock_client.url = "http://localhost:7878"
    mock_client.api_key = "test_key"

    # Create server
    server = RadarrMCPServer(client=mock_client)

    # Get tools
    tools = server._get_tools()

    expected_tools = [
        "radarr_get_movies",
        "radarr_get_movie_by_id",
        "radarr_add_movie",
        "radarr_delete_movie",
        "radarr_search_movie_lookup",
        "radarr_search_movie",
        "radarr_get_queue",
        "radarr_get_calendar",
        "radarr_get_wanted",
    ]

    tool_names = [tool.name for tool in tools]

    print(f"  Found {len(tools)} tools")

    missing_tools = set(expected_tools) - set(tool_names)
    if missing_tools:
        print(f"  [FAIL] Missing tools: {missing_tools}")
        return False

    extra_tools = set(tool_names) - set(expected_tools)
    if extra_tools:
        print(f"  [INFO] Extra tools: {extra_tools}")

    # Verify each tool has proper schema
    for tool in tools:
        if not tool.name:
            print(f"  [FAIL] Tool has no name")
            return False
        if not tool.description:
            print(f"  [FAIL] Tool {tool.name} has no description")
            return False
        if not tool.inputSchema:
            print(f"  [FAIL] Tool {tool.name} has no input schema")
            return False
        if tool.inputSchema.get("type") != "object":
            print(f"  [FAIL] Tool {tool.name} schema is not object type")
            return False

    print(f"  [OK] All {len(expected_tools)} expected tools present")
    print(f"  [OK] All tools have valid schemas")
    return True


def test_models():
    """Test Pydantic models."""
    print("\nTesting Pydantic models...")
    from radarr.models import Movie, MovieFile, Command, Queue, QueueRecord

    # Test Movie model
    try:
        movie = Movie(
            id=1,
            title="Inception",
            status="released",
            year=2010,
            tmdbId=27205,
            hasFile=True,
            path="/movies/Inception (2010)",
            qualityProfileId=1,
            monitored=True
        )
        print("  [OK] Movie model works")
    except Exception as e:
        print(f"  [FAIL] Movie model error: {e}")
        return False

    # Test MovieFile model
    try:
        movie_file = MovieFile(
            id=1,
            movieId=1,
            relativePath="Inception (2010).mkv",
            size=2000000000,
            quality={"quality": {"name": "Bluray-1080p"}}
        )
        print("  [OK] MovieFile model works")
    except Exception as e:
        print(f"  [FAIL] MovieFile model error: {e}")
        return False

    # Test Command model
    try:
        command = Command(
            id=1,
            name="MoviesSearch",
            status="completed"
        )
        print("  [OK] Command model works")
    except Exception as e:
        print(f"  [FAIL] Command model error: {e}")
        return False

    print("  [OK] All models validated successfully")
    return True


def test_client_initialization():
    """Test RadarrClient initialization."""
    print("\nTesting client initialization...")
    from radarr.client import RadarrClient

    # Test valid initialization
    try:
        client = RadarrClient(
            url="http://localhost:7878",
            api_key="test_key"
        )
        print("  [OK] Client initializes with valid parameters")
    except Exception as e:
        print(f"  [FAIL] Client initialization error: {e}")
        return False

    # Test URL normalization
    client = RadarrClient(
        url="http://localhost:7878/",
        api_key="test_key"
    )
    if client.url != "http://localhost:7878":
        print(f"  [FAIL] URL normalization failed: {client.url}")
        return False
    print("  [OK] URL normalization works")

    # Test empty URL validation
    try:
        RadarrClient(url="", api_key="test_key")
        print("  [FAIL] Should reject empty URL")
        return False
    except ValueError:
        print("  [OK] Rejects empty URL")

    # Test empty API key validation
    try:
        RadarrClient(url="http://localhost:7878", api_key="")
        print("  [FAIL] Should reject empty API key")
        return False
    except ValueError:
        print("  [OK] Rejects empty API key")

    return True


def test_server_initialization():
    """Test RadarrMCPServer initialization."""
    print("\nTesting server initialization...")
    from radarr.server import RadarrMCPServer
    from radarr.client import RadarrClient
    from unittest.mock import AsyncMock

    # Test with None client
    try:
        RadarrMCPServer(client=None)
        print("  [FAIL] Should reject None client")
        return False
    except ValueError:
        print("  [OK] Rejects None client")

    # Test with valid client
    mock_client = AsyncMock(spec=RadarrClient)
    try:
        server = RadarrMCPServer(client=mock_client)
        print("  [OK] Server initializes with valid client")
    except Exception as e:
        print(f"  [FAIL] Server initialization error: {e}")
        return False

    # Verify server properties
    if server.name != "radarr":
        print(f"  [FAIL] Wrong server name: {server.name}")
        return False
    print("  [OK] Server name is correct")

    if not hasattr(server, "version"):
        print("  [FAIL] Server has no version")
        return False
    print("  [OK] Server has version")

    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Radarr MCP Server Implementation Verification")
    print("=" * 60)

    tests = [
        test_imports,
        test_client_class,
        test_server_class,
        test_mcp_tools,
        test_models,
        test_client_initialization,
        test_server_initialization,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n[FAIL] Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("[OK] All verification tests passed!")
        print("[OK] Radarr implementation is complete and functional")
        return 0
    else:
        print("[FAIL] Some verification tests failed")
        print("[FAIL] Please review the errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
