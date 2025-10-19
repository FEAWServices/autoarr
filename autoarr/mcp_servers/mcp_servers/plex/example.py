#!/usr/bin/env python3
"""
Plex MCP Server Example Usage.

This script demonstrates how to use the Plex MCP Server to interact with
Plex Media Server through both the client API and MCP tools.

Usage:
    python example.py --url http://localhost:32400 --token YOUR_TOKEN
"""

import argparse
import asyncio
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plex import PlexClient, PlexMCPServer  # noqa: E402


async def example_1_basic_client_usage():
    """Example 1: Basic client operations."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Client Usage")
    print("=" * 80 + "\n")

    # Create client
    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
        validate_connection=True,
    )

    try:
        # Get server identity
        identity = await client.get_server_identity()
        print(f"Connected to: {identity.get('friendlyName', 'Unknown')}")
        print(f"Version: {identity.get('version', 'Unknown')}")
        print(f"Platform: {identity.get('platform', 'Unknown')}")

        # Get libraries
        libraries = await client.get_libraries()
        print(f"\nLibraries ({len(libraries)}):")
        for lib in libraries:
            print(f"  - {lib['title']} (Type: {lib['type']}, ID: {lib['key']})")

    finally:
        await client.close()


async def example_2_browse_content():
    """Example 2: Browse content in libraries."""
    print("\n" + "=" * 80)
    print("Example 2: Browse Content")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        libraries = await client.get_libraries()

        if libraries:
            # Browse first library
            first_lib = libraries[0]
            print(f"Browsing: {first_lib['title']}")

            items = await client.get_library_items(library_id=first_lib["key"], limit=10)

            print(f"Found {len(items)} items (showing 10):\n")
            for i, item in enumerate(items, 1):
                title = item.get("title", "Unknown")
                year = item.get("year", "N/A")
                item_type = item.get("type", "Unknown")
                print(f"{i}. {title} ({year}) - {item_type}")

    finally:
        await client.close()


async def example_3_recently_added_and_on_deck():
    """Example 3: Recently added and On Deck content."""
    print("\n" + "=" * 80)
    print("Example 3: Recently Added & On Deck")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        # Recently added
        recent = await client.get_recently_added(limit=5)
        print("Recently Added:")
        for item in recent:
            print(f"  - {item.get('title', 'Unknown')} ({item.get('type', 'Unknown')})")

        # On Deck
        on_deck = await client.get_on_deck(limit=5)
        print(f"\nOn Deck (Continue Watching): {len(on_deck)} items")
        for item in on_deck:
            title = item.get("title", "Unknown")
            print(f"  - {title}")

    finally:
        await client.close()


async def example_4_monitor_playback():
    """Example 4: Monitor active playback sessions."""
    print("\n" + "=" * 80)
    print("Example 4: Monitor Playback")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        sessions = await client.get_sessions()

        if sessions:
            print(f"Active Sessions: {len(sessions)}\n")
            for i, session in enumerate(sessions, 1):
                user = session.get("User", {})
                player = session.get("Player", {})

                print(f"Session {i}:")
                print(f"  User: {user.get('title', 'Unknown')}")
                print(f"  Title: {session.get('title', 'Unknown')}")
                print(f"  Type: {session.get('type', 'Unknown')}")
                print(
                    f"  Player: {player.get('product', 'Unknown')} on {player.get('platform', 'Unknown')}"  # noqa: E501
                )

                # Progress
                offset = session.get("viewOffset", 0)
                duration = session.get("duration", 0)
                if duration > 0:
                    progress = (offset / duration) * 100
                    mins_watched = offset // 60000
                    mins_total = duration // 60000
                    print(f"  Progress: {progress:.1f}% ({mins_watched}/{mins_total} min)")
                print()
        else:
            print("No active playback sessions")

    finally:
        await client.close()


async def example_5_search_content():
    """Example 5: Search for content."""
    print("\n" + "=" * 80)
    print("Example 5: Search Content")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        query = "the"
        print(f"Searching for: '{query}'")

        results = await client.search(query=query, limit=10)

        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            title = result.get("title", "Unknown")
            year = result.get("year", "N/A")
            result_type = result.get("type", "Unknown")
            print(f"{i}. {title} ({year}) - {result_type}")

    finally:
        await client.close()


async def example_6_watch_history():
    """Example 6: View watch history."""
    print("\n" + "=" * 80)
    print("Example 6: Watch History")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        history = await client.get_history(limit=10)

        if history:
            print(f"Recent Watch History ({len(history)} items):\n")
            for i, item in enumerate(history, 1):
                title = item.get("title", "Unknown")
                item_type = item.get("type", "Unknown")
                print(f"{i}. {title} - {item_type}")
        else:
            print("No watch history found")

    finally:
        await client.close()


async def example_7_mcp_tools():
    """Example 7: Using MCP tools."""
    print("\n" + "=" * 80)
    print("Example 7: MCP Tools")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        # Create MCP server
        server = PlexMCPServer(client=client)
        await server.start()

        # List available tools
        tools = server.list_tools()
        print(f"Available MCP Tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}")
            print(f"    {tool.description}")
        print()

        # Call a tool: get_libraries
        print("Calling tool: plex_get_libraries")
        result = await server.call_tool("plex_get_libraries", {})  # noqa: F841

        if not result.isError:
            # Parse the result
            content_text = result.content[0].text
            data = json.loads(content_text)

            if data.get("success"):
                libraries = data.get("data", [])
                print(f"Success! Found {len(libraries)} libraries")
                for lib in libraries[:3]:  # Show first 3
                    print(f"  - {lib.get('title', 'Unknown')}")
            else:
                print("Tool returned an error")
        else:
            print("Tool call failed")

    finally:
        await client.close()


async def example_8_library_refresh():
    """Example 8: Refresh a library."""
    print("\n" + "=" * 80)
    print("Example 8: Library Refresh")
    print("=" * 80 + "\n")

    client = await PlexClient.create(  # noqa: F841
        url=os.getenv("PLEX_URL", "http://localhost:32400"),
        token=os.getenv("PLEX_TOKEN", ""),
    )

    try:
        # Get libraries
        libraries = await client.get_libraries()

        if libraries:
            first_lib = libraries[0]
            lib_id = first_lib["key"]
            lib_title = first_lib["title"]

            print(f"Refreshing library: {lib_title} (ID: {lib_id})")

            result = await client.refresh_library(library_id=lib_id)  # noqa: F841

            if result.get("success"):
                print("Library refresh triggered successfully!")
                print("Note: Refresh happens in the background on the server")
            else:
                print("Failed to trigger library refresh")

    finally:
        await client.close()


async def main():
    """Run all examples."""
    # Check for required environment variable
    if not os.getenv("PLEX_TOKEN"):
        print("Error: PLEX_TOKEN environment variable is required")
        print("\nSet it with: export PLEX_TOKEN='your_token_here'")
        print("\nTo get your token:")
        print("  1. Sign in to Plex Web App")
        print("  2. Open any media item")
        print("  3. Click '...' > 'Get Info' > 'View XML'")
        print("  4. Look for 'X-Plex-Token' in the URL")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("Plex MCP Server - Example Usage")
    print("=" * 80)
    print(f"Plex URL: {os.getenv('PLEX_URL', 'http://localhost:32400')}")
    print("=" * 80)

    # Run all examples
    try:
        await example_1_basic_client_usage()
        await example_2_browse_content()
        await example_3_recently_added_and_on_deck()
        await example_4_monitor_playback()
        await example_5_search_content()
        await example_6_watch_history()
        await example_7_mcp_tools()
        await example_8_library_refresh()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plex MCP Server Examples")
    parser.add_argument(
        "--url", default=os.getenv("PLEX_URL", "http://localhost:32400"), help="Plex server URL"
    )
    parser.add_argument(
        "--token", default=os.getenv("PLEX_TOKEN"), help="Plex authentication token"
    )

    args = parser.parse_args()

    # Set environment variables for examples
    os.environ["PLEX_URL"] = args.url
    if args.token:
        os.environ["PLEX_TOKEN"] = args.token

    asyncio.run(main())
