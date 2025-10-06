# Plex MCP Server

A Model Context Protocol (MCP) server for Plex Media Server, enabling LLM-based interactions with Plex media management and playback monitoring.

## Overview

The Plex MCP Server provides a bridge between Large Language Models (LLMs) and Plex Media Server, allowing AI assistants to query libraries, monitor playback sessions, search for content, and manage media through natural language interactions.

## Features

- **Library Management**: Browse and manage Plex library sections
- **Content Discovery**: Search across all media, view recently added items
- **Playback Monitoring**: Track active streaming sessions and watch history
- **Continue Watching**: Access On Deck items for resuming playback
- **Library Maintenance**: Trigger library scans and refreshes

## Installation

### Prerequisites

- Python 3.11 or higher
- Plex Media Server with API access
- Plex authentication token

### Install Dependencies

```bash
pip install httpx pydantic mcp
```

## Configuration

### Getting Your Plex Token

To interact with Plex, you need an authentication token:

1. Sign in to Plex Web App (https://app.plex.tv)
2. Open any media item in your library
3. Click the three dots (...) menu
4. Select "Get Info" → "View XML"
5. Look for `X-Plex-Token` in the URL
6. Copy the token value

### Environment Variables

```bash
export PLEX_URL="http://localhost:32400"  # Your Plex server URL
export PLEX_TOKEN="your_token_here"        # Your Plex authentication token
```

## Usage

### As a Python Library

```python
import asyncio
from plex import PlexClient, PlexMCPServer

async def main():
    # Create Plex client
    client = await PlexClient.create(
        url="http://localhost:32400",
        token="your_token_here",
        validate_connection=True
    )

    # Create MCP server
    server = PlexMCPServer(client=client)
    await server.start()

    # Use client methods
    libraries = await client.get_libraries()
    print(f"Found {len(libraries)} libraries")

    recently_added = await client.get_recently_added(limit=10)
    print(f"Recently added: {len(recently_added)} items")

    # Cleanup
    await server.stop()

asyncio.run(main())
```

### Testing the Implementation

Run the comprehensive test suite:

```bash
# Using command-line arguments
python mcp-servers/plex/test_plex.py --url http://localhost:32400 --token YOUR_TOKEN

# Using environment variables
export PLEX_URL="http://localhost:32400"
export PLEX_TOKEN="your_token_here"
python mcp-servers/plex/test_plex.py
```

The test suite validates:
- Client initialization and connection
- Server identity retrieval
- Library operations
- Content search
- Session monitoring
- MCP tool functionality

## MCP Tools

The server exposes 8 MCP tools for LLM interaction:

### 1. plex_get_libraries

List all Plex library sections (Movies, TV Shows, Music, etc.).

```json
{
  "name": "plex_get_libraries",
  "arguments": {}
}
```

**Returns**: Array of library objects with metadata

### 2. plex_get_library_items

Get all items in a specific library.

```json
{
  "name": "plex_get_library_items",
  "arguments": {
    "library_id": "1",
    "limit": 50,
    "offset": 0
  }
}
```

**Parameters**:
- `library_id` (string, required): Library section ID/key
- `limit` (integer, optional): Maximum number of items
- `offset` (integer, optional): Number of items to skip

**Returns**: Array of media items

### 3. plex_get_recently_added

Get recently added content across all libraries.

```json
{
  "name": "plex_get_recently_added",
  "arguments": {
    "limit": 20
  }
}
```

**Parameters**:
- `limit` (integer, optional): Maximum number of items (default: 50)

**Returns**: Array of recently added media items

### 4. plex_get_on_deck

Get On Deck items (continue watching).

```json
{
  "name": "plex_get_on_deck",
  "arguments": {
    "limit": 12
  }
}
```

**Parameters**:
- `limit` (integer, optional): Maximum number of items (default: 12)

**Returns**: Array of On Deck media items for resuming

### 5. plex_get_sessions

Get currently playing sessions and active streams.

```json
{
  "name": "plex_get_sessions",
  "arguments": {}
}
```

**Returns**: Array of active session objects with user, player, and media info

### 6. plex_search

Search for content across all libraries or within a specific library.

```json
{
  "name": "plex_search",
  "arguments": {
    "query": "inception",
    "limit": 10,
    "section_id": "1"
  }
}
```

**Parameters**:
- `query` (string, required): Search query
- `limit` (integer, optional): Maximum results
- `section_id` (string, optional): Limit to specific library

**Returns**: Array of search results

### 7. plex_refresh_library

Trigger a library refresh/scan to update content.

```json
{
  "name": "plex_refresh_library",
  "arguments": {
    "library_id": "1"
  }
}
```

**Parameters**:
- `library_id` (string, required): Library section ID to refresh

**Returns**: Success confirmation

### 8. plex_get_history

Get watch history for all users.

```json
{
  "name": "plex_get_history",
  "arguments": {
    "limit": 50,
    "offset": 0
  }
}
```

**Parameters**:
- `limit` (integer, optional): Maximum items (default: 50)
- `offset` (integer, optional): Number to skip for pagination

**Returns**: Array of watch history records

## API Client Methods

### PlexClient

The `PlexClient` class provides async methods for interacting with Plex Media Server.

#### Initialization

```python
client = PlexClient(
    url="http://localhost:32400",
    token="your_token_here",
    timeout=30.0
)

# Or with validation
client = await PlexClient.create(
    url="http://localhost:32400",
    token="your_token_here",
    validate_connection=True
)
```

#### System Operations

- `get_server_identity()`: Get server info (version, platform, capabilities)
- `health_check()`: Check if server is accessible

#### Library Operations

- `get_libraries()`: List all library sections
- `get_library_items(library_id, limit, offset)`: Get items in a library
- `get_recently_added(limit)`: Recently added content
- `get_on_deck(limit)`: On Deck (continue watching) items
- `refresh_library(library_id)`: Trigger library scan

#### Playback Operations

- `get_sessions()`: Currently playing sessions
- `get_history(limit, offset)`: Watch history

#### Search Operations

- `search(query, limit, section_id)`: Search for content

## Data Models

### PlexLibrary

```python
class PlexLibrary(BaseModel):
    key: str                 # Library ID
    title: str              # Library name
    type: str               # movie, show, artist, photo
    agent: str              # Metadata agent
    scanner: str            # Scanner type
    language: str           # Library language
    uuid: str               # Library UUID
    updated_at: int         # Last update timestamp
```

### PlexMediaItem

```python
class PlexMediaItem(BaseModel):
    rating_key: str         # Unique rating key
    key: str                # Media item key
    type: str               # movie, episode, track
    title: str              # Media title
    summary: Optional[str]  # Description
    year: Optional[int]     # Release year
    duration: Optional[int] # Duration in ms
    added_at: int           # Date added timestamp
    updated_at: int         # Last update timestamp
    view_count: Optional[int] # Times viewed
```

### PlexSession

```python
class PlexSession(BaseModel):
    session_key: str        # Session key
    user: Dict[str, Any]    # User information
    player: Dict[str, Any]  # Player information
    view_offset: int        # Current position (ms)
    rating_key: Optional[str]  # Media rating key
    title: Optional[str]    # Media title
    type: Optional[str]     # Media type
    duration: Optional[int] # Total duration (ms)
```

### PlexServerIdentity

```python
class PlexServerIdentity(BaseModel):
    machine_identifier: str # Unique machine ID
    version: str            # Plex version
    platform: str           # Server platform
    platform_version: str   # Platform version
    friendly_name: Optional[str]  # Server name
    my_plex: Optional[bool] # Connected to Plex.tv
```

## Error Handling

The client provides custom exceptions:

- `PlexClientError`: Base exception for client errors
- `PlexConnectionError`: Connection-related errors

```python
from plex import PlexClient, PlexClientError, PlexConnectionError

try:
    client = await PlexClient.create(
        url="http://localhost:32400",
        token="invalid_token",
        validate_connection=True
    )
except PlexConnectionError as e:
    print(f"Connection failed: {e}")
except PlexClientError as e:
    print(f"Client error: {e}")
```

## Architecture

### Key Differences from *arr Apps

Plex has a unique API structure:

1. **Authentication**: Uses `X-Plex-Token` header (not `X-Api-Key`)
2. **Port**: Default port 32400 (vs 7878/8989 for *arr apps)
3. **Response Format**: Can be XML or JSON (client handles both)
4. **Library Structure**: Organized by library sections with different media types
5. **Sessions**: Real-time playback monitoring built-in

### Client Architecture

```
PlexClient
├── _get_client() - HTTP client management
├── _build_url() - URL construction with X-Plex-Token
├── _get_headers() - Token-based authentication
├── _parse_xml_to_dict() - XML response parsing
├── _request() - Core HTTP request handler
└── [Public Methods] - Library, playback, search operations
```

### Server Architecture

```
PlexMCPServer
├── _setup_handlers() - MCP protocol handlers
├── _get_tools() - Tool definitions (8 tools)
├── _call_tool() - Tool dispatcher
└── [Handler Methods] - Tool-specific logic
```

## Examples

### Example 1: Browse Libraries

```python
async def browse_libraries():
    client = await PlexClient.create(
        url="http://localhost:32400",
        token="your_token"
    )

    libraries = await client.get_libraries()

    for lib in libraries:
        print(f"\nLibrary: {lib['title']}")
        print(f"Type: {lib['type']}")
        print(f"ID: {lib['key']}")

        # Get first 5 items
        items = await client.get_library_items(
            library_id=lib['key'],
            limit=5
        )

        print(f"Items: {len(items)}")
        for item in items:
            print(f"  - {item.get('title', 'Unknown')}")

    await client.close()
```

### Example 2: Monitor Playback

```python
async def monitor_playback():
    client = await PlexClient.create(
        url="http://localhost:32400",
        token="your_token"
    )

    sessions = await client.get_sessions()

    if sessions:
        print(f"Active streams: {len(sessions)}")
        for session in sessions:
            user = session.get('User', {})
            player = session.get('Player', {})

            print(f"\nUser: {user.get('title', 'Unknown')}")
            print(f"Playing: {session.get('title', 'Unknown')}")
            print(f"Player: {player.get('product', 'Unknown')}")

            # Calculate progress
            offset = session.get('viewOffset', 0)
            duration = session.get('duration', 0)
            if duration > 0:
                progress = (offset / duration) * 100
                print(f"Progress: {progress:.1f}%")
    else:
        print("No active streams")

    await client.close()
```

### Example 3: Search and Discover

```python
async def search_content():
    client = await PlexClient.create(
        url="http://localhost:32400",
        token="your_token"
    )

    # Search across all libraries
    results = await client.search(query="inception", limit=10)

    print(f"Search results: {len(results)}")
    for result in results:
        print(f"- {result.get('title', 'Unknown')} ({result.get('type', 'Unknown')})")
        print(f"  Year: {result.get('year', 'N/A')}")

    # Get recently added
    recent = await client.get_recently_added(limit=10)

    print(f"\nRecently added: {len(recent)}")
    for item in recent:
        print(f"- {item.get('title', 'Unknown')}")

    await client.close()
```

## Troubleshooting

### Common Issues

#### 1. "Unauthorized: Invalid Plex token (401)"

**Solution**: Verify your token is correct
```bash
# Test with curl
curl -H "X-Plex-Token: YOUR_TOKEN" http://localhost:32400/
```

#### 2. "Connection failed"

**Solutions**:
- Verify Plex is running
- Check URL and port (default: 32400)
- Ensure network connectivity
- Check firewall settings

#### 3. "No libraries found"

**Solution**: Verify libraries exist in Plex Web App

#### 4. XML/JSON Parsing Errors

**Solution**: The client handles both formats automatically. If you see parsing errors, update the client or report the issue.

### Debugging

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("plex")

# Your code here
```

## Contributing

When contributing to the Plex MCP server:

1. Follow the existing code patterns from Radarr/Sonarr
2. Add tests for new functionality
3. Update documentation
4. Ensure type hints are complete
5. Follow PEP 8 style guidelines

## License

Part of the AutoArr project. See main project LICENSE.

## Related Documentation

- [Plex API Documentation](https://www.plexopedia.com/plex-media-server/api/)
- [Model Context Protocol (MCP)](https://github.com/anthropics/mcp)
- [AutoArr Project](../../README.md)

## Version History

### 0.1.0 (2025-10-06)
- Initial implementation
- 8 MCP tools for Plex interaction
- Full async/await support
- Comprehensive test suite
- XML and JSON response handling
