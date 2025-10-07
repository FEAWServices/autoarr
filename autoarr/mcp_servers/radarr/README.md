# Radarr MCP Server

Model Context Protocol (MCP) server for Radarr movie management.

## Overview

This MCP server exposes Radarr's movie management functionality through the Model Context Protocol, enabling LLMs to interact with Radarr for automated movie library management.

## Features

- **Movie Management**: List, add, delete, and search for movies
- **Download Queue**: Monitor and manage movie downloads
- **Calendar**: View upcoming movie releases
- **Wanted Movies**: Track missing/wanted movies
- **Search**: Trigger download searches for specific movies
- **TMDb Integration**: Search and lookup movies via TMDb

## Installation

```bash
pip install httpx pydantic mcp
```

## Usage

### Initialize Client

```python
from radarr.client import RadarrClient

# Create client
client = await RadarrClient.create(
    url="http://localhost:7878",
    api_key="your_api_key_here",
    validate_connection=True
)

# Get all movies
movies = await client.get_movies()

# Search for a movie
results = await client.search_movie_lookup(term="Inception")

# Add a movie
movie_data = {
    "tmdbId": 27205,
    "title": "Inception",
    "qualityProfileId": 1,
    "rootFolderPath": "/movies",
    "monitored": True,
    "minimumAvailability": "released"
}
added_movie = await client.add_movie(movie_data)

# Close client
await client.close()
```

### MCP Server

```python
from radarr.server import RadarrMCPServer
from radarr.client import RadarrClient

# Create client and server
client = await RadarrClient.create(
    url="http://localhost:7878",
    api_key="your_api_key_here"
)

server = RadarrMCPServer(client=client)
await server.start()

# List available tools
tools = server.list_tools()
for tool in tools:
    print(f"- {tool.name}: {tool.description}")
```

## Available MCP Tools

### Movie Operations

1. **radarr_get_movies** - List all movies with pagination
2. **radarr_get_movie_by_id** - Get specific movie details
3. **radarr_add_movie** - Add a new movie to Radarr
4. **radarr_delete_movie** - Remove a movie from Radarr
5. **radarr_search_movie_lookup** - Search for movies via TMDb
6. **radarr_search_movie** - Trigger download search for a movie

### Queue & Calendar

7. **radarr_get_queue** - Get current download queue
8. **radarr_get_calendar** - Get upcoming movie releases
9. **radarr_get_wanted** - Get missing/wanted movies

## API Reference

### RadarrClient

#### Movie Operations

- `get_movies(limit=None, page=None)` - Get all movies
- `get_movie_by_id(movie_id)` - Get movie by ID
- `add_movie(movie_data)` - Add new movie
- `delete_movie(movie_id, delete_files=False)` - Delete movie
- `search_movie_lookup(term)` - Search movies via TMDb
- `search_movie(movie_id)` - Trigger movie download search

#### Queue & Calendar

- `get_queue(page=None, page_size=None)` - Get download queue
- `get_calendar(start_date=None, end_date=None)` - Get calendar
- `get_wanted_missing(page=None, page_size=None)` - Get wanted movies

#### System

- `get_system_status()` - Get Radarr system status
- `health_check()` - Validate Radarr connection

## Configuration

### Environment Variables

```bash
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_api_key_here
```

### API Key

Get your Radarr API key from Settings > General > Security > API Key

## Error Handling

```python
from radarr.client import RadarrClientError, RadarrConnectionError

try:
    movies = await client.get_movies()
except RadarrConnectionError as e:
    print(f"Connection failed: {e}")
except RadarrClientError as e:
    print(f"API error: {e}")
```

## Architecture

- **client.py** - Async HTTP client for Radarr API v3
- **server.py** - MCP server implementation
- **models.py** - Pydantic data models for validation
- \***\*init**.py\*\* - Package exports

## Radarr API

This implementation uses Radarr API v3:

- Base URL: `http://localhost:7878/api/v3`
- Authentication: X-Api-Key header
- Endpoints: `/movie`, `/command`, `/queue`, `/calendar`, `/wanted/missing`

## Differences from Sonarr

Radarr and Sonarr share the same codebase but manage different media types:

| Sonarr           | Radarr          |
| ---------------- | --------------- |
| TV Series        | Movies          |
| Episodes         | N/A             |
| TVDB             | TMDb            |
| `/api/v3/series` | `/api/v3/movie` |
| Port 8989        | Port 7878       |

## Testing

```bash
# Run unit tests
pytest tests/unit/mcp_servers/radarr/

# Run integration tests (requires running Radarr instance)
pytest tests/integration/mcp_servers/radarr/
```

## License

Part of the AutoArr project.

## Related

- [Sonarr MCP Server](../sonarr/README.md) - TV show management
- [SABnzbd MCP Server](../sabnzbd/README.md) - Download client management
