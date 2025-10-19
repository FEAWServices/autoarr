#!/usr/bin/env python3
"""
Plex MCP Server Test Script.

This script tests the Plex MCP server implementation by performing various operations
against a Plex Media Server instance. It verifies client functionality and MCP tool execution.

Usage:
    python test_plex.py --url http://localhost:32400 --token YOUR_TOKEN

Environment Variables (alternative to CLI args):
    PLEX_URL: Plex server URL (default: http://localhost:32400)
    PLEX_TOKEN: Plex authentication token (required)
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plex.client import PlexClient
from plex.server import PlexMCPServer

# ============================================================================
# Color Output Utilities
# ============================================================================


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_json(data: Any, indent: int = 2) -> None:
    """Print JSON data with formatting."""
    print(json.dumps(data, indent=indent, default=str))


# ============================================================================
# Test Functions
# ============================================================================


async def test_client_initialization(url: str, token: str) -> bool:
    """Test Plex client initialization and validation."""
    print_header("Test 1: Client Initialization")

    try:
        # Test basic initialization
        print_info("Creating Plex client...")
        client = PlexClient(url=url, token=token)  # noqa: F841
        print_success(f"Client created with URL: {client.url}")

        # Test validation during creation
        print_info("Creating client with connection validation...")
        validated_client = await PlexClient.create(
            url=url, token=token, validate_connection=True
        )  # noqa: F841
        print_success("Client created and validated successfully")

        await validated_client.close()
        return True

    except Exception as e:
        print_error(f"Client initialization failed: {e}")
        return False


async def test_health_check(client: PlexClient) -> bool:
    """Test Plex health check."""
    print_header("Test 2: Health Check")

    try:
        print_info("Performing health check...")
        is_healthy = await client.health_check()

        if is_healthy:
            print_success("Plex server is healthy and responding")
            return True
        else:
            print_error("Plex server health check failed")
            return False

    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


async def test_server_identity(client: PlexClient) -> bool:
    """Test getting Plex server identity."""
    print_header("Test 3: Server Identity")

    try:
        print_info("Fetching server identity...")
        identity = await client.get_server_identity()

        if identity:
            print_success("Server identity retrieved successfully")
            print_info(f"Machine Identifier: {identity.get('machineIdentifier', 'N/A')}")
            print_info(f"Version: {identity.get('version', 'N/A')}")
            print_info(f"Platform: {identity.get('platform', 'N/A')}")
            print_info(f"Platform Version: {identity.get('platformVersion', 'N/A')}")
            return True
        else:
            print_warning("Server identity is empty")
            return False

    except Exception as e:
        print_error(f"Failed to get server identity: {e}")
        return False


async def test_get_libraries(client: PlexClient) -> bool:
    """Test getting Plex libraries."""
    print_header("Test 4: Get Libraries")

    try:
        print_info("Fetching libraries...")
        libraries = await client.get_libraries()

        if libraries:
            print_success(f"Found {len(libraries)} libraries")
            for lib in libraries:
                print_info(
                    f"  - {lib.get('title', 'Unknown')} (Type: {lib.get('type', 'Unknown')}, Key: {lib.get('key', 'N/A')})"  # noqa: E501
                )
            return True
        else:
            print_warning("No libraries found")
            return False

    except Exception as e:
        print_error(f"Failed to get libraries: {e}")
        return False


async def test_get_library_items(client: PlexClient) -> bool:
    """Test getting items from a library."""
    print_header("Test 5: Get Library Items")

    try:
        # First get libraries to find one to query
        libraries = await client.get_libraries()

        if not libraries:
            print_warning("No libraries available to test")
            return False

        # Use first library
        library = libraries[0]
        library_id = library.get("key", "")
        library_title = library.get("title", "Unknown")

        print_info(f"Fetching items from library: {library_title} (ID: {library_id})")
        items = await client.get_library_items(library_id=library_id, limit=5)

        if items:
            print_success(f"Found {len(items)} items (showing up to 5)")
            for item in items[:3]:  # Show first 3
                print_info(
                    f"  - {item.get('title', 'Unknown')} (Type: {item.get('type', 'Unknown')})"
                )
            return True
        else:
            print_warning(f"No items found in library {library_title}")
            return False

    except Exception as e:
        print_error(f"Failed to get library items: {e}")
        return False


async def test_recently_added(client: PlexClient) -> bool:
    """Test getting recently added content."""
    print_header("Test 6: Recently Added Content")

    try:
        print_info("Fetching recently added content...")
        items = await client.get_recently_added(limit=5)

        if items:
            print_success(f"Found {len(items)} recently added items")
            for item in items[:3]:  # Show first 3
                print_info(
                    f"  - {item.get('title', 'Unknown')} (Type: {item.get('type', 'Unknown')})"
                )
            return True
        else:
            print_warning("No recently added content found")
            return False

    except Exception as e:
        print_error(f"Failed to get recently added content: {e}")
        return False


async def test_on_deck(client: PlexClient) -> bool:
    """Test getting On Deck items."""
    print_header("Test 7: On Deck (Continue Watching)")

    try:
        print_info("Fetching On Deck items...")
        items = await client.get_on_deck(limit=5)

        if items:
            print_success(f"Found {len(items)} On Deck items")
            for item in items[:3]:  # Show first 3
                print_info(
                    f"  - {item.get('title', 'Unknown')} (Type: {item.get('type', 'Unknown')})"
                )
            return True
        else:
            print_warning("No On Deck items found (this is normal if nothing has been watched)")
            return True  # This is not an error

    except Exception as e:
        print_error(f"Failed to get On Deck items: {e}")
        return False


async def test_sessions(client: PlexClient) -> bool:
    """Test getting active sessions."""
    print_header("Test 8: Active Sessions")

    try:
        print_info("Fetching active sessions...")
        sessions = await client.get_sessions()

        if sessions:
            print_success(f"Found {len(sessions)} active sessions")
            for session in sessions:
                user_info = session.get("User", {})
                player_info = session.get("Player", {})
                print_info(f"  - User: {user_info.get('title', 'Unknown')}")
                print_info(f"    Player: {player_info.get('product', 'Unknown')}")
                print_info(f"    Title: {session.get('title', 'Unknown')}")
            return True
        else:
            print_warning("No active sessions (this is normal if nothing is playing)")
            return True  # This is not an error

    except Exception as e:
        print_error(f"Failed to get active sessions: {e}")
        return False


async def test_search(client: PlexClient) -> bool:
    """Test search functionality."""
    print_header("Test 9: Search")

    try:
        print_info("Searching for 'the'...")
        results = await client.search(query="the", limit=5)

        if results:
            print_success(f"Found {len(results)} search results")
            for result in results[:3]:  # Show first 3
                print_info(
                    f"  - {result.get('title', 'Unknown')} (Type: {result.get('type', 'Unknown')})"
                )
            return True
        else:
            print_warning("No search results found")
            return False

    except Exception as e:
        print_error(f"Search failed: {e}")
        return False


async def test_history(client: PlexClient) -> bool:
    """Test getting watch history."""
    print_header("Test 10: Watch History")

    try:
        print_info("Fetching watch history...")
        history = await client.get_history(limit=5)

        if history:
            print_success(f"Found {len(history)} history items")
            for item in history[:3]:  # Show first 3
                print_info(
                    f"  - {item.get('title', 'Unknown')} (Type: {item.get('type', 'Unknown')})"
                )
            return True
        else:
            print_warning("No watch history found (this is normal for new servers)")
            return True  # This is not an error

    except Exception as e:
        print_error(f"Failed to get history: {e}")
        return False


async def test_mcp_server(client: PlexClient) -> bool:
    """Test MCP server initialization and tools."""
    print_header("Test 11: MCP Server")

    try:
        print_info("Creating MCP server...")
        server = PlexMCPServer(client=client)
        print_success("MCP server created successfully")

        print_info("Starting MCP server...")
        await server.start()
        print_success("MCP server started successfully")

        print_info("Listing available tools...")
        tools = server.list_tools()
        print_success(f"Found {len(tools)} tools:")
        for tool in tools:
            print_info(f"  - {tool.name}: {tool.description}")

        # Test a simple tool call
        print_info("Testing plex_get_libraries tool...")
        result = await server.call_tool("plex_get_libraries", {})  # noqa: F841

        if not result.isError:
            print_success("Tool call successful")
            return True
        else:
            print_error("Tool call returned an error")
            return False

    except Exception as e:
        print_error(f"MCP server test failed: {e}")
        return False


# ============================================================================
# Main Test Runner
# ============================================================================


async def run_all_tests(url: str, token: str) -> None:
    """Run all tests and report results."""
    print_header("Plex MCP Server Test Suite")
    print_info(f"Plex URL: {url}")
    print_info(f"Token: {'*' * 20}")

    results = []

    # Create client for tests
    client = None  # noqa: F841
    try:
        client = PlexClient(url=url, token=token)  # noqa: F841

        # Run all tests
        results.append(("Client Initialization", await test_client_initialization(url, token)))
        results.append(("Health Check", await test_health_check(client)))
        results.append(("Server Identity", await test_server_identity(client)))
        results.append(("Get Libraries", await test_get_libraries(client)))
        results.append(("Get Library Items", await test_get_library_items(client)))
        results.append(("Recently Added", await test_recently_added(client)))
        results.append(("On Deck", await test_on_deck(client)))
        results.append(("Active Sessions", await test_sessions(client)))
        results.append(("Search", await test_search(client)))
        results.append(("Watch History", await test_history(client)))
        results.append(("MCP Server", await test_mcp_server(client)))

    finally:
        if client:
            await client.close()

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")

    if passed == total:
        print_success("All tests passed!")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed")
        sys.exit(1)


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test Plex MCP Server implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_plex.py --url http://localhost:32400 --token YOUR_TOKEN
  PLEX_URL=http://192.168.1.100:32400 PLEX_TOKEN=abc123 python test_plex.py

Environment Variables:
  PLEX_URL     Plex server URL (default: http://localhost:32400)
  PLEX_TOKEN   Plex authentication token (required if not provided via --token)
        """,
    )

    parser.add_argument(
        "--url",
        type=str,
        default=os.getenv("PLEX_URL", "http://localhost:32400"),
        help="Plex server URL (default: http://localhost:32400 or PLEX_URL env var)",
    )

    parser.add_argument(
        "--token",
        type=str,
        default=os.getenv("PLEX_TOKEN"),
        help="Plex authentication token (required, or use PLEX_TOKEN env var)",
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.token:
        print_error("Error: Plex token is required")
        print_info("Provide it via --token argument or PLEX_TOKEN environment variable")
        print_info("\nTo get your Plex token:")
        print_info("  1. Sign in to Plex Web App")
        print_info("  2. Open any media item")
        print_info("  3. Click '...' > 'Get Info' > 'View XML'")
        print_info("  4. Look for 'X-Plex-Token' in the URL")
        sys.exit(1)

    # Run tests
    asyncio.run(run_all_tests(args.url, args.token))


if __name__ == "__main__":
    main()
