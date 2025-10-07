#!/usr/bin/env python3
"""
Example usage of the Radarr MCP Server.

This script demonstrates how to use the Radarr client and MCP server
to manage movies in Radarr.

Requirements:
- Running Radarr instance
- Valid API key
- httpx, pydantic, mcp packages installed
"""

import asyncio
import os
import sys
from pathlib import Path

# Add mcp-servers to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers"))

from radarr.client import RadarrClient, RadarrClientError, RadarrConnectionError
from radarr.server import RadarrMCPServer


async def example_client_usage():
    """Example of using RadarrClient directly."""
    print("=" * 60)
    print("Radarr Client Example")
    print("=" * 60)

    # Get configuration from environment or use defaults
    radarr_url = os.getenv("RADARR_URL", "http://localhost:7878")
    radarr_api_key = os.getenv("RADARR_API_KEY", "your_api_key_here")

    print(f"\nConnecting to Radarr at {radarr_url}...")

    try:
        # Create client with connection validation
        async with await RadarrClient.create(
            url=radarr_url, api_key=radarr_api_key, validate_connection=True
        ) as client:
            print("[OK] Connected to Radarr!")

            # Get system status
            print("\n1. Getting system status...")
            status = await client.get_system_status()
            print(f"   Radarr version: {status['version']}")
            print(f"   OS: {status.get('osName', 'Unknown')}")

            # Get all movies (limited to 5 for demo)
            print("\n2. Getting movies (first 5)...")
            movies = await client.get_movies(limit=5)
            print(f"   Found {len(movies)} movies:")
            for movie in movies:
                status_icon = "[DOWNLOADED]" if movie.get("hasFile") else "[WANTED]"
                print(f"   {status_icon} {movie['title']} ({movie['year']})")

            # Search for a movie
            print("\n3. Searching for movies...")
            search_term = "Inception"
            results = await client.search_movie_lookup(term=search_term)
            print(f"   Found {len(results)} results for '{search_term}':")
            for result in results[:3]:  # Show first 3
                print(f"   - {result['title']} ({result['year']}) - TMDb ID: {result['tmdbId']}")

            # Get download queue
            print("\n4. Getting download queue...")
            queue = await client.get_queue(page_size=5)
            if queue["totalRecords"] > 0:
                print(f"   {queue['totalRecords']} items in queue:")
                for item in queue["records"]:
                    movie = item.get("movie", {})
                    print(f"   - {movie.get('title', 'Unknown')} ({item['status']})")
            else:
                print("   Queue is empty")

            # Get wanted movies
            print("\n5. Getting wanted movies...")
            wanted = await client.get_wanted_missing(page_size=5)
            if wanted["totalRecords"] > 0:
                print(f"   {wanted['totalRecords']} wanted movies:")
                for record in wanted["records"]:
                    print(f"   - {record['title']} ({record['year']})")
            else:
                print("   No wanted movies")

            # Get calendar
            print("\n6. Getting calendar (upcoming releases)...")
            from datetime import datetime, timedelta

            today = datetime.now().strftime("%Y-%m-%d")
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            calendar = await client.get_calendar(start_date=today, end_date=next_week)
            print(f"   {len(calendar)} movies releasing in the next 7 days")

            print("\n[OK] Client examples completed successfully!")

    except RadarrConnectionError as e:
        print(f"\n[FAIL] Connection error: {e}")
        print("\nTroubleshooting:")
        print("1. Is Radarr running?")
        print("2. Is the URL correct?")
        print("3. Can you access Radarr in a browser?")
    except RadarrClientError as e:
        print(f"\n[FAIL] API error: {e}")
        print("\nTroubleshooting:")
        print("1. Is your API key correct?")
        print("2. Check Settings > General > Security > API Key")
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback

        traceback.print_exc()


async def example_mcp_server_usage():
    """Example of using RadarrMCPServer."""
    print("\n" + "=" * 60)
    print("Radarr MCP Server Example")
    print("=" * 60)

    # Get configuration from environment or use defaults
    radarr_url = os.getenv("RADARR_URL", "http://localhost:7878")
    radarr_api_key = os.getenv("RADARR_API_KEY", "your_api_key_here")

    print(f"\nCreating MCP server for Radarr at {radarr_url}...")

    try:
        # Create client
        client = await RadarrClient.create(
            url=radarr_url, api_key=radarr_api_key, validate_connection=True
        )

        # Create MCP server
        server = RadarrMCPServer(client=client)
        await server.start()

        print("[OK] MCP server started!")

        # List available tools
        print("\n1. Available MCP tools:")
        tools = server.list_tools()
        for tool in tools:
            print(f"   - {tool.name}")
            print(f"     {tool.description}")

        # Example: Call a tool
        print("\n2. Calling radarr_get_movies tool...")
        result = await server.call_tool("radarr_get_movies", {"limit": 3})

        if not result.isError:
            print("   [OK] Tool executed successfully!")
            # Parse response
            import json

            response = json.loads(result.content[0].text)
            movies = response["data"]
            print(f"   Retrieved {len(movies)} movies")
        else:
            print("   [FAIL] Tool execution failed")

        # Example: Search for movies
        print("\n3. Calling radarr_search_movie_lookup tool...")
        result = await server.call_tool("radarr_search_movie_lookup", {"term": "The Matrix"})

        if not result.isError:
            print("   [OK] Search completed!")
            import json

            response = json.loads(result.content[0].text)
            results = response["data"]
            print(f"   Found {len(results)} results")
        else:
            print("   [FAIL] Search failed")

        # Cleanup
        await server.stop()
        print("\n[OK] MCP server examples completed successfully!")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Radarr MCP Server - Usage Examples")
    print("=" * 60)

    # Check for configuration
    radarr_url = os.getenv("RADARR_URL")
    radarr_api_key = os.getenv("RADARR_API_KEY")

    if not radarr_url or not radarr_api_key:
        print("\nConfiguration:")
        print("Set these environment variables before running:")
        print("  export RADARR_URL=http://localhost:7878")
        print("  export RADARR_API_KEY=your_api_key_here")
        print("\nOr edit this script and set the defaults.")
        print("\nUsing default values for demonstration...")

    # Run examples
    await example_client_usage()
    await example_mcp_server_usage()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
