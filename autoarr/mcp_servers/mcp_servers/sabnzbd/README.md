# SABnzbd MCP Server

A Model Context Protocol (MCP) server implementation for SABnzbd, enabling LLMs to interact with SABnzbd's download management system.

## Overview

The SABnzbd MCP Server provides a protocol-compliant interface that exposes SABnzbd's functionality as MCP tools. This allows LLMs and AI agents to monitor downloads, manage the queue, retry failed downloads, and configure SABnzbd settings.

## Features

- **Queue Management**: Get current queue status, pause/resume downloads
- **History Access**: View download history with filtering options
- **Download Recovery**: Retry failed downloads automatically
- **Configuration Management**: Get and set SABnzbd configuration
- **Connection Health**: Health checks and connection validation
- **Error Handling**: Comprehensive error handling with retries
- **Type Safety**: Full type hints and Pydantic models for validation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   LLM / AI Agent                        │
└────────────────────┬────────────────────────────────────┘
                     │ MCP Protocol
                     ▼
┌─────────────────────────────────────────────────────────┐
│            SABnzbdMCPServer                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tool Registry & Validation                       │  │
│  │  - sabnzbd_get_queue                             │  │
│  │  - sabnzbd_get_history                           │  │
│  │  - sabnzbd_retry_download                        │  │
│  │  - sabnzbd_get_config                            │  │
│  │  - sabnzbd_set_config                            │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                     │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │  SABnzbdClient (API Wrapper)                     │  │
│  │  - Connection management                         │  │
│  │  - Request/response handling                     │  │
│  │  - Retry logic & error handling                  │  │
│  │  - URL building & authentication                 │  │
│  └────────────────┬─────────────────────────────────┘  │
└───────────────────┼─────────────────────────────────────┘
                    │ HTTPS/HTTP
                    ▼
┌─────────────────────────────────────────────────────────┐
│              SABnzbd API                                │
│  /api?mode=queue                                        │
│  /api?mode=history                                      │
│  /api?mode=retry                                        │
│  /api?mode=get_config                                   │
│  /api?mode=set_config                                   │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Install dependencies
pip install mcp httpx pydantic

# Or install the entire autoarr package
pip install -e .
```

## Usage

### Basic Setup

```python
from autoarr.mcp_servers.mcp_servers.sabnzbd.client import SABnzbdClient
from autoarr.mcp_servers.mcp_servers.sabnzbd.server import SABnzbdMCPServer

# Create client
client = SABnzbdClient(
    url="http://localhost:8080",
    api_key="your_api_key_here",
    timeout=30.0
)

# Create MCP server
server = SABnzbdMCPServer(client=client)

# Start server (validates connection)
await server.start()

# List available tools
tools = server.list_tools()
for tool in tools:
    print(f"Tool: {tool.name} - {tool.description}")

# Call a tool
result = await server.call_tool("sabnzbd_get_queue", {})
print(result.content[0].text)

# Cleanup
await server.stop()
```

### Using the Client Directly

```python
from autoarr.mcp_servers.mcp_servers.sabnzbd.client import SABnzbdClient

async with SABnzbdClient(
    url="http://localhost:8080",
    api_key="your_api_key_here"
) as client:
    # Get queue
    queue = await client.get_queue()
    print(f"Downloads in queue: {queue['queue']['noofslots']}")

    # Get history with filtering
    history = await client.get_history(
        limit=10,
        failed_only=True
    )

    # Retry a failed download
    result = await client.retry_download(nzo_id="failed_nzo_123")

    # Get configuration
    config = await client.get_config(section="misc")

    # Update configuration
    await client.set_config(
        section="misc",
        keyword="cache_limit",
        value="1000M"
    )
```

## MCP Tools

### sabnzbd_get_queue

Get the current SABnzbd download queue with status and progress information.

**Parameters:**

- `start` (integer, optional): Start index for pagination (default: 0)
- `limit` (integer, optional): Maximum number of items to return

**Returns:**

```json
{
  "queue": {
    "status": "Downloading",
    "speed": "5.2 MB/s",
    "mb": 2500.0,
    "mbleft": 1250.5,
    "slots": [
      {
        "nzo_id": "SABnzbd_nzo_abc123",
        "filename": "Download.File.mkv",
        "status": "Downloading",
        "percentage": 50,
        "mb_left": 625.2,
        "mb": 1250.5,
        "eta": "00:04:30",
        "category": "tv"
      }
    ],
    "noofslots": 1,
    "paused": false
  }
}
```

**Example:**

```python
result = await server.call_tool("sabnzbd_get_queue", {"start": 0, "limit": 10})
```

### sabnzbd_get_history

Get SABnzbd download history including completed and failed downloads.

**Parameters:**

- `start` (integer, optional): Start index for pagination (default: 0)
- `limit` (integer, optional): Maximum number of items to return
- `failed_only` (boolean, optional): Return only failed downloads (default: false)
- `category` (string, optional): Filter by category

**Returns:**

```json
{
  "history": {
    "total_size": "125.5 GB",
    "noofslots": 5,
    "slots": [
      {
        "nzo_id": "SABnzbd_nzo_xyz789",
        "name": "Completed.Download",
        "status": "Completed",
        "fail_message": "",
        "category": "tv",
        "size": "2.5 GB",
        "download_time": 450,
        "completed": 1704067200
      }
    ]
  }
}
```

**Example:**

```python
result = await server.call_tool("sabnzbd_get_history", {
    "limit": 20,
    "failed_only": True,
    "category": "tv"
})
```

### sabnzbd_retry_download

Retry a failed download by NZO ID.

**Parameters:**

- `nzo_id` (string, **required**): The NZO ID of the failed download to retry

**Returns:**

```json
{
  "status": true,
  "nzo_ids": ["SABnzbd_nzo_new123"]
}
```

**Example:**

```python
result = await server.call_tool("sabnzbd_retry_download", {
    "nzo_id": "SABnzbd_nzo_failed123"
})
```

### sabnzbd_get_config

Get SABnzbd configuration settings.

**Parameters:**

- `section` (string, optional): Specific config section to retrieve (e.g., "misc", "servers")

**Returns:**

```json
{
  "config": {
    "misc": {
      "complete_dir": "/downloads/complete",
      "download_dir": "/downloads/incomplete",
      "enable_https": false,
      "host": "0.0.0.0",
      "port": 8080,
      "api_key": "...",
      "cache_limit": "500M"
    },
    "servers": [],
    "categories": {}
  }
}
```

**Example:**

```python
result = await server.call_tool("sabnzbd_get_config", {"section": "misc"})
```

### sabnzbd_set_config

Set a SABnzbd configuration value.

**Parameters:**

- `section` (string, **required**): Configuration section (e.g., "misc", "servers")
- `keyword` (string, **required**): Configuration key to set
- `value` (string, **required**): Value to set

**Returns:**

```json
{
  "status": true
}
```

**Example:**

```python
result = await server.call_tool("sabnzbd_set_config", {
    "section": "misc",
    "keyword": "cache_limit",
    "value": "1000M"
})
```

## Client API Reference

### SABnzbdClient

#### Constructor

```python
SABnzbdClient(
    url: str,           # Base URL of SABnzbd instance
    api_key: str,       # API key for authentication
    timeout: float = 30.0  # Request timeout in seconds
)
```

#### Methods

##### Queue Operations

- `async get_queue(start: int = 0, limit: Optional[int] = None, nzo_ids: Optional[List[str]] = None) -> Dict[str, Any]`
- `async pause_queue() -> Dict[str, Any]`
- `async resume_queue() -> Dict[str, Any]`

##### History Operations

- `async get_history(start: int = 0, limit: Optional[int] = None, failed_only: bool = False, category: Optional[str] = None) -> Dict[str, Any]`

##### Download Management

- `async retry_download(nzo_id: str) -> Dict[str, Any]`
- `async delete_download(nzo_id: str, delete_files: bool = False) -> Dict[str, Any]`
- `async pause_download(nzo_id: str) -> Dict[str, Any]`
- `async resume_download(nzo_id: str) -> Dict[str, Any]`

##### Configuration

- `async get_config(section: Optional[str] = None) -> Dict[str, Any]`
- `async set_config(section: str, keyword: str, value: Any) -> Dict[str, Any]`
- `async set_config_batch(config_updates: Dict[str, Any]) -> Dict[str, Any]`

##### Status & Information

- `async get_version() -> Dict[str, Any]`
- `async get_status() -> Dict[str, Any]`
- `async health_check() -> bool`

##### Lifecycle

- `async close() -> None`

## Error Handling

The SABnzbd MCP Server provides comprehensive error handling:

### Exception Types

- **SABnzbdClientError**: Base exception for client errors (API errors, validation errors)
- **SABnzbdConnectionError**: Connection-related errors (timeouts, network failures)

### Retry Behavior

- Automatically retries on transient errors (503, connection timeouts)
- Configurable max retries (default: 3)
- Exponential backoff not implemented (constant retry interval)

### Error Responses

MCP tool errors return a structured error response:

```json
{
  "error": "Error message describing what went wrong",
  "success": false
}
```

## Testing

### Running Unit Tests

```bash
# Run all SABnzbd unit tests
pytest autoarr/tests/unit/mcp_servers/sabnzbd/ -v

# Run with coverage
pytest autoarr/tests/unit/mcp_servers/sabnzbd/ --cov=autoarr.mcp_servers.mcp_servers.sabnzbd --cov-report=term-missing
```

### Running Integration Tests

Integration tests require a running SABnzbd instance:

```bash
# Set environment variables
export SABNZBD_URL="http://localhost:8080"
export SABNZBD_API_KEY="your_api_key"

# Run integration tests
pytest autoarr/tests/integration/mcp_servers/sabnzbd/ -m integration -v

# Skip integration tests
pytest -m "not integration"
```

### Test Coverage

Current test coverage:

- **SABnzbd Client**: 91% coverage (147 statements, 13 missed)
- **SABnzbd MCP Server**: 97% coverage (105 statements, 3 missed)
- **Overall SABnzbd MCP**: ~94% coverage

## Configuration

### Environment Variables

- `SABNZBD_URL`: SABnzbd instance URL (default: http://localhost:8080)
- `SABNZBD_API_KEY`: API key for authentication (required)

### Connection Settings

- **Default Timeout**: 30 seconds
- **Max Retries**: 3 attempts
- **Connection Pooling**: Enabled via httpx AsyncClient

## Best Practices

1. **Always use context managers** for client lifecycle:

   ```python
   async with SABnzbdClient(url, api_key) as client:
       await client.get_queue()
   ```

2. **Validate connections** before use:

   ```python
   client = await SABnzbdClient.create(
       url=url,
       api_key=api_key,
       validate_connection=True
   )
   ```

3. **Handle errors gracefully**:

   ```python
   try:
       result = await client.get_queue()
   except SABnzbdConnectionError as e:
       logger.error(f"Connection failed: {e}")
   except SABnzbdClientError as e:
       logger.error(f"API error: {e}")
   ```

4. **Use pagination** for large datasets:

   ```python
   page_size = 20
   for page in range(total_pages):
       history = await client.get_history(
           start=page * page_size,
           limit=page_size
       )
   ```

5. **Implement health checks** in production:
   ```python
   if not await client.health_check():
       raise SABnzbdConnectionError("SABnzbd is unreachable")
   ```

## Troubleshooting

### Common Issues

**401 Unauthorized**

- Verify API key is correct
- Check that API access is enabled in SABnzbd settings

**Connection Timeout**

- Verify SABnzbd is running and accessible
- Check firewall rules
- Increase timeout parameter if needed

**503 Service Unavailable**

- SABnzbd may be overloaded
- Client will automatically retry
- Check SABnzbd logs for issues

**Invalid JSON Response**

- SABnzbd may have returned an error page
- Check URL is correct (should end at base URL, not /api)
- Verify SABnzbd version compatibility

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest autoarr/tests/unit/mcp_servers/sabnzbd/`
2. Coverage remains high: `>90%` for new code
3. Code follows PEP 8 style guidelines
4. Type hints are provided for all functions
5. Docstrings follow Google style format

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:

- GitHub Issues: [autoarr/autoarr](https://github.com/autoarr/autoarr/issues)
- Documentation: [AutoArr Docs](https://github.com/autoarr/autoarr/tree/main/docs)

## Related Documentation

- [SABnzbd API Documentation](https://sabnzbd.org/wiki/advanced/api)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [AutoArr Project Documentation](../../README.md)
