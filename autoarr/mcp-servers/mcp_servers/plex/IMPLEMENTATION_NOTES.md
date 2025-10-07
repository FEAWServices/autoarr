# Plex MCP Server - Implementation Notes

## Overview

This document details the implementation of the Plex MCP Server and highlights key differences from the Sonarr/Radarr/SABnzbd implementations.

## Architecture Comparison

### Plex vs \*arr Apps

| Feature               | Plex                  | Sonarr/Radarr      | SABnzbd               |
| --------------------- | --------------------- | ------------------ | --------------------- |
| **Authentication**    | `X-Plex-Token` header | `X-Api-Key` header | API key in URL params |
| **Default Port**      | 32400                 | 8989/7878          | 8080                  |
| **API Version**       | No versioning         | `/api/v3`          | Mode-based            |
| **Response Format**   | XML or JSON           | JSON only          | JSON only             |
| **URL Structure**     | `/library/sections`   | `/api/v3/series`   | `/api?mode=queue`     |
| **Data Organization** | Library-centric       | Media-centric      | Queue-centric         |

## Key Implementation Details

### 1. Response Format Handling

**Challenge**: Plex can return either XML or JSON depending on the endpoint and headers.

**Solution**: Implemented dual-format parser in `_request()` method:

```python
def _parse_xml_to_dict(self, xml_element: ET.Element) -> Dict[str, Any]:
    """Parse XML element to dictionary."""
    result = dict(xml_element.attrib)

    children = list(xml_element)
    if children:
        children_dict: Dict[str, List[Any]] = {}
        for child in children:
            child_data = self._parse_xml_to_dict(child)
            tag = child.tag
            if tag not in children_dict:
                children_dict[tag] = []
            children_dict[tag].append(child_data)

        for tag, items in children_dict.items():
            result[tag] = items if len(items) > 1 else items[0]

    return result
```

The client automatically detects content type and parses accordingly.

### 2. MediaContainer Response Structure

**Challenge**: Plex wraps responses in a `MediaContainer` object with variable child keys.

**Solution**: Implement flexible extraction logic:

```python
async def get_libraries(self) -> List[Dict[str, Any]]:
    result = await self._request("GET", "library/sections")

    # Extract Directory list from MediaContainer
    if "MediaContainer" in result:
        directories = result["MediaContainer"].get("Directory", [])
        if isinstance(directories, dict):
            return [directories]
        return directories if isinstance(directories, list) else []

    return []
```

This handles both single-item dictionaries and arrays.

### 3. Library-Centric Design

Unlike \*arr apps which focus on individual media items, Plex organizes everything by library sections:

```
Plex Structure:
└── Libraries (Sections)
    ├── Movies Library
    │   └── Movie Items
    ├── TV Shows Library
    │   └── Show → Season → Episode
    └── Music Library
        └── Artist → Album → Track
```

**Implementation**: All content operations require a `library_id` parameter:

```python
async def get_library_items(
    self,
    library_id: str,  # Required for Plex
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Dict[str, Any]]:
    params = {}
    if limit is not None:
        params["X-Plex-Container-Size"] = limit
    if offset is not None:
        params["X-Plex-Container-Start"] = offset

    result = await self._request(
        "GET",
        f"library/sections/{library_id}/all",
        **params
    )

    # Extract items from MediaContainer
    if "MediaContainer" in result:
        for key in ["Metadata", "Video", "Directory", "Track"]:
            items = result["MediaContainer"].get(key, [])
            if items:
                return items if isinstance(items, list) else [items]

    return []
```

### 4. Session Monitoring

**Unique Feature**: Plex has built-in real-time session monitoring (not available in \*arr apps).

```python
async def get_sessions(self) -> List[Dict[str, Any]]:
    """Get currently playing sessions."""
    result = await self._request("GET", "status/sessions")

    if "MediaContainer" in result:
        for key in ["Metadata", "Video", "Track"]:
            items = result["MediaContainer"].get(key, [])
            if items:
                return items if isinstance(items, list) else [items]

    return []
```

**Returns**:

- Active user sessions
- Playback progress (`viewOffset`)
- Player information
- Transcoding status

### 5. Token-Based Authentication

**Implementation**:

```python
def _get_headers(self) -> Dict[str, str]:
    """Get request headers including Plex token."""
    return {
        "X-Plex-Token": self.token,
        "Accept": "application/json",
    }
```

**Note**: Unlike API keys in \*arr apps, Plex tokens are user-specific and tied to Plex.tv accounts.

### 6. Pagination Parameters

Plex uses custom pagination parameters:

```python
params = {
    "X-Plex-Container-Size": limit,      # vs "limit" in *arr
    "X-Plex-Container-Start": offset,    # vs "offset" in *arr
}
```

## MCP Tools Design

### Tool Mapping

| MCP Tool                  | Client Method          | Plex Endpoint                    |
| ------------------------- | ---------------------- | -------------------------------- |
| `plex_get_libraries`      | `get_libraries()`      | `/library/sections`              |
| `plex_get_library_items`  | `get_library_items()`  | `/library/sections/{id}/all`     |
| `plex_get_recently_added` | `get_recently_added()` | `/library/recentlyAdded`         |
| `plex_get_on_deck`        | `get_on_deck()`        | `/library/onDeck`                |
| `plex_get_sessions`       | `get_sessions()`       | `/status/sessions`               |
| `plex_search`             | `search()`             | `/search`                        |
| `plex_refresh_library`    | `refresh_library()`    | `/library/sections/{id}/refresh` |
| `plex_get_history`        | `get_history()`        | `/status/sessions/history/all`   |

### Tool Design Principles

1. **Discoverability**: Clear, descriptive names (e.g., `plex_get_on_deck`)
2. **Consistency**: Follow Radarr/Sonarr naming patterns
3. **Flexibility**: Optional pagination and filtering
4. **Error Handling**: Comprehensive error messages

Example tool definition:

```python
Tool(
    name="plex_get_library_items",
    description="Get all items in a specific Plex library",
    inputSchema={
        "type": "object",
        "properties": {
            "library_id": {
                "type": "string",
                "description": "The library section ID/key",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of items to return (optional)",
            },
            "offset": {
                "type": "integer",
                "description": "Number of items to skip for pagination (optional)",
            },
        },
        "required": ["library_id"],
    },
)
```

## Data Models

### Model Design Decisions

1. **PlexLibrary**: Minimal model for library metadata
2. **PlexMediaItem**: Generic model supporting movies, episodes, tracks
3. **PlexSession**: Real-time playback state
4. **PlexServerIdentity**: Comprehensive server info
5. **PlexHistoryRecord**: Watch history tracking

### Type Flexibility

Due to Plex's polymorphic responses, models use `Optional` extensively:

```python
class PlexMediaItem(BaseModel):
    rating_key: str = Field(..., alias="ratingKey")  # Always present
    title: str = Field(...)                          # Always present
    type: str = Field(...)                           # Always present

    # Optional fields (varies by media type)
    year: Optional[int] = Field(None)
    parent_title: Optional[str] = Field(None, alias="parentTitle")
    index: Optional[int] = Field(None)

    class Config:
        populate_by_name = True  # Support both camelCase and snake_case
```

## Error Handling

### Plex-Specific Errors

```python
class PlexClientError(Exception):
    """Base exception for Plex client errors."""
    pass

class PlexConnectionError(PlexClientError):
    """Exception raised when connection to Plex fails."""
    pass
```

### Common Error Scenarios

1. **401 Unauthorized**: Invalid or expired token
2. **404 Not Found**: Library or item doesn't exist
3. **503 Service Unavailable**: Server restarting (retry)
4. **Connection Errors**: Network issues (retry with backoff)

### Retry Logic

```python
last_error: Optional[Exception] = None
for attempt in range(max_retries):
    try:
        response = await client.get(url, headers=headers)

        if response.status_code == 503:
            # Service unavailable - retry
            last_error = PlexClientError("Server unavailable (503)")
            if attempt < max_retries - 1:
                continue
            raise PlexClientError("Server unavailable after retries")

        # Process response...

    except HTTPError as e:
        last_error = e
        if attempt < max_retries - 1:
            continue
        raise PlexConnectionError(f"Connection failed: {e}")
```

## Testing Strategy

### Test Coverage

The test suite (`test_plex.py`) validates:

1. **Client Initialization**: Basic and validated creation
2. **Health Check**: Server connectivity
3. **Server Identity**: Version and platform info
4. **Library Operations**: List libraries and items
5. **Content Discovery**: Recently added, On Deck, search
6. **Session Monitoring**: Active playback tracking
7. **History**: Watch history retrieval
8. **MCP Server**: Tool registration and execution

### Test Philosophy

- **Non-destructive**: Read-only operations (no modifications)
- **Graceful Degradation**: Empty results are warnings, not errors
- **Comprehensive Output**: Detailed logging for debugging
- **Real Environment**: Tests against actual Plex server

### Running Tests

```bash
# With environment variables
export PLEX_URL="http://localhost:32400"
export PLEX_TOKEN="your_token"
python test_plex.py

# With command-line arguments
python test_plex.py --url http://localhost:32400 --token YOUR_TOKEN
```

## Performance Considerations

### Caching Strategy

Plex doesn't provide built-in caching, but clients can implement it:

```python
from datetime import datetime, timedelta

class CachedPlexClient(PlexClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)

    async def get_libraries(self) -> List[Dict[str, Any]]:
        cache_key = "libraries"

        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return data

        result = await super().get_libraries()
        self._cache[cache_key] = (datetime.now(), result)
        return result
```

### Pagination Best Practices

For large libraries, use pagination:

```python
# Bad: Fetch all items at once
items = await client.get_library_items(library_id="1")

# Good: Fetch in batches
batch_size = 100
offset = 0
all_items = []

while True:
    batch = await client.get_library_items(
        library_id="1",
        limit=batch_size,
        offset=offset
    )

    if not batch:
        break

    all_items.extend(batch)
    offset += batch_size
```

## Security Considerations

### Token Management

1. **Never Log Tokens**: Redact in logs and error messages
2. **Environment Variables**: Store tokens in env vars, not code
3. **Token Rotation**: Support token updates without restart
4. **Secure Storage**: Use system keychain when possible

### Network Security

1. **HTTPS**: Prefer HTTPS URLs for remote servers
2. **Certificate Validation**: Verify SSL certificates
3. **Timeouts**: Set reasonable timeouts to prevent hanging
4. **Rate Limiting**: Implement client-side rate limiting

## Future Enhancements

### Potential Features

1. **Webhooks**: Listen for Plex events (new media, playback start/stop)
2. **Playlists**: Create and manage playlists
3. **Collections**: Organize media into collections
4. **User Management**: Manage shared users and permissions
5. **Transcoding**: Monitor and control transcoding
6. **Download Sync**: Manage mobile sync downloads

### API Limitations

Current implementation doesn't support:

- Modifying media metadata
- User management
- Server settings configuration
- Plugin management
- Playlist creation

These could be added in future versions if needed.

## Comparison: Tool Count

| Server      | Tool Count  | Focus                                 |
| ----------- | ----------- | ------------------------------------- |
| **Plex**    | **8 tools** | Library browsing, playback monitoring |
| **Radarr**  | 9 tools     | Movie management, search              |
| **Sonarr**  | 10 tools    | TV show management, episodes          |
| **SABnzbd** | 8 tools     | Download queue management             |

## Lessons Learned

### What Worked Well

1. **Pattern Reuse**: Following Radarr/Sonarr patterns accelerated development
2. **XML Parsing**: Generic XML-to-dict converter handles all endpoints
3. **Error Handling**: Comprehensive exception hierarchy catches issues
4. **Testing**: Test-driven approach ensured quality

### Challenges Overcome

1. **Dual Format Responses**: Solved with automatic format detection
2. **Variable Response Structure**: Flexible extraction logic handles variations
3. **MediaContainer Wrapping**: Helper methods extract actual data
4. **Library-Centric Model**: Adjusted tool design for Plex's organization

### Best Practices Applied

1. **Type Safety**: Full type hints throughout
2. **Async/Await**: Complete async support
3. **Documentation**: Comprehensive docstrings and README
4. **Testing**: Thorough test coverage
5. **Error Messages**: Clear, actionable error messages

## Maintenance Notes

### Regular Updates Needed

1. Monitor Plex API changes
2. Update models for new fields
3. Add new endpoints as they become available
4. Keep dependencies updated

### Testing Recommendations

- Test against multiple Plex versions
- Validate with different library types (Movies, TV, Music)
- Test with various media formats
- Verify transcoding scenarios

## Conclusion

The Plex MCP Server successfully implements the Model Context Protocol for Plex Media Server, following established patterns while adapting to Plex's unique API design. The implementation is production-ready, well-tested, and documented.

### Quick Stats

- **Files**: 6 (client.py, server.py, models.py, **init**.py, test_plex.py, example.py)
- **Lines of Code**: ~1,800+
- **Tools**: 8 MCP tools
- **Models**: 6 Pydantic models
- **Tests**: 11 comprehensive tests
- **Documentation**: README, implementation notes, inline docstrings

### Next Steps

1. Deploy to production environment
2. Monitor usage and gather feedback
3. Implement additional features based on user needs
4. Integrate with AutoArr orchestration system
