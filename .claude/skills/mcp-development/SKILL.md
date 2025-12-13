# MCP Server Development Skill

## Overview

This skill covers best practices for building Model Context Protocol (MCP) servers
in AutoArr for integrating with SABnzbd, Sonarr, Radarr, and Plex.

## MCP Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AutoArr MCP Architecture                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────┐                                                  │
│   │   FastAPI    │  HTTP API for frontend                           │
│   │   Gateway    │                                                  │
│   └──────┬───────┘                                                  │
│          │                                                          │
│          ▼                                                          │
│   ┌──────────────┐                                                  │
│   │     MCP      │  Coordinates all MCP servers                     │
│   │ Orchestrator │  Connection pooling, error handling              │
│   └──────┬───────┘                                                  │
│          │                                                          │
│    ┌─────┼─────┬─────────┬─────────┐                               │
│    │     │     │         │         │                               │
│    ▼     ▼     ▼         ▼         ▼                               │
│ ┌─────┐┌─────┐┌───────┐┌───────┐┌─────┐                           │
│ │SABn-││Sonarr││Radarr ││ Plex  ││Future│                          │
│ │ zbd ││ MCP ││  MCP  ││  MCP  ││ MCP  │                          │
│ │ MCP ││     ││       ││       ││      │                          │
│ └──┬──┘└──┬──┘└───┬───┘└───┬───┘└──────┘                           │
│    │      │       │        │                                        │
│    ▼      ▼       ▼        ▼                                        │
│ ┌─────┐┌─────┐┌───────┐┌───────┐                                   │
│ │SABn-││Sonarr││Radarr ││ Plex  │  External Services               │
│ │ zbd ││ API ││  API  ││  API  │  (User's network)                 │
│ └─────┘└─────┘└───────┘└───────┘                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## MCP Server Structure

Each MCP server follows this standard structure:

```
autoarr/mcp_servers/{service}/
├── __init__.py
├── client.py          # HTTP client for external API
├── models.py          # Pydantic models for data types
├── server.py          # MCP server implementation
└── tools.py           # Tool definitions and handlers
```

## Creating an MCP Server

### 1. Define the Client

```python
# autoarr/mcp_servers/sabnzbd/client.py
from typing import Any
import httpx
from autoarr.mcp_servers.sabnzbd.models import QueueResponse, HistoryResponse

class SABnzbdClient:
    """HTTP client for SABnzbd API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SABnzbdClient":
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def _request(self, mode: str, **params: Any) -> dict[str, Any]:
        """Make authenticated request to SABnzbd API."""
        url = f"{self.base_url}/api"
        params = {
            "mode": mode,
            "apikey": self.api_key,
            "output": "json",
            **params,
        }

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_queue(self) -> QueueResponse:
        """Get current download queue."""
        data = await self._request("queue")
        return QueueResponse.model_validate(data)

    async def get_history(self, limit: int = 50) -> HistoryResponse:
        """Get download history."""
        data = await self._request("history", limit=limit)
        return HistoryResponse.model_validate(data)

    async def retry(self, nzo_id: str) -> dict[str, Any]:
        """Retry a failed download."""
        return await self._request("retry", value=nzo_id)

    async def test_connection(self) -> dict[str, str]:
        """Test connection and return version info."""
        data = await self._request("version")
        return {"version": data.get("version", "unknown")}
```

### 2. Define Models

```python
# autoarr/mcp_servers/sabnzbd/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class QueueSlot(BaseModel):
    """A single item in the download queue."""
    nzo_id: str
    filename: str
    status: str
    percentage: float = Field(ge=0, le=100)
    size: str
    sizeleft: str
    eta: Optional[str] = None
    category: str = ""
    priority: str = "Normal"

class QueueResponse(BaseModel):
    """Response from queue API."""
    queue: list[QueueSlot] = Field(default_factory=list)
    speed: str = "0"
    size: str = "0"
    sizeleft: str = "0"

class HistorySlot(BaseModel):
    """A single item in history."""
    nzo_id: str
    name: str
    status: str  # Completed, Failed, etc.
    size: str
    category: str = ""
    completed: Optional[datetime] = None
    fail_message: Optional[str] = None

class HistoryResponse(BaseModel):
    """Response from history API."""
    slots: list[HistorySlot] = Field(default_factory=list)
```

### 3. Implement MCP Server

```python
# autoarr/mcp_servers/sabnzbd/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient
from autoarr.mcp_servers.sabnzbd.models import QueueResponse

class SABnzbdMCPServer:
    """MCP server for SABnzbd integration."""

    def __init__(self):
        self.server = Server("sabnzbd")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register all available tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="get_queue",
                    description="Get current SABnzbd download queue with status, progress, and ETA",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                Tool(
                    name="get_history",
                    description="Get SABnzbd download history including completed and failed downloads",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of history items to return",
                                "default": 50,
                            },
                        },
                    },
                ),
                Tool(
                    name="retry_download",
                    description="Retry a failed download by its NZO ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "nzo_id": {
                                "type": "string",
                                "description": "The NZO ID of the download to retry",
                            },
                        },
                        "required": ["nzo_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            client = self._get_client()

            async with client:
                if name == "get_queue":
                    result = await client.get_queue()
                    return [TextContent(type="text", text=result.model_dump_json())]

                elif name == "get_history":
                    limit = arguments.get("limit", 50)
                    result = await client.get_history(limit=limit)
                    return [TextContent(type="text", text=result.model_dump_json())]

                elif name == "retry_download":
                    nzo_id = arguments["nzo_id"]
                    result = await client.retry(nzo_id)
                    return [TextContent(type="text", text=str(result))]

                else:
                    raise ValueError(f"Unknown tool: {name}")

    def _get_client(self) -> SABnzbdClient:
        """Get configured SABnzbd client from settings."""
        from autoarr.shared.core.config import get_settings
        settings = get_settings()
        return SABnzbdClient(
            base_url=settings.sabnzbd_url,
            api_key=settings.sabnzbd_api_key,
        )
```

## Error Handling

### Retry Logic with Exponential Backoff

```python
import asyncio
from functools import wraps
from typing import TypeVar, Callable, Any

T = TypeVar("T")

def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (httpx.RequestError, httpx.TimeoutException),
):
    """Decorator for retry with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
                        delay *= backoff_factor

            raise last_exception

        return wrapper
    return decorator

# Usage
class SABnzbdClient:
    @with_retry(max_attempts=3, initial_delay=1.0)
    async def get_queue(self) -> QueueResponse:
        data = await self._request("queue")
        return QueueResponse.model_validate(data)
```

### Distinguishing Error Types

```python
class MCPError(Exception):
    """Base exception for MCP errors."""
    pass

class RetryableError(MCPError):
    """Error that can be retried (network, timeout)."""
    pass

class NonRetryableError(MCPError):
    """Error that should not be retried (auth, not found)."""
    pass

class RateLimitError(RetryableError):
    """API rate limit exceeded."""
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded, retry after {retry_after}s")

# In client
async def _request(self, mode: str, **params: Any) -> dict:
    try:
        response = await self._client.get(url, params=params)

        if response.status_code == 401:
            raise NonRetryableError("Invalid API key")
        if response.status_code == 404:
            raise NonRetryableError(f"Resource not found: {mode}")
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 60))
            raise RateLimitError(retry_after)

        response.raise_for_status()
        return response.json()

    except httpx.TimeoutException as e:
        raise RetryableError(f"Request timed out: {e}")
    except httpx.RequestError as e:
        raise RetryableError(f"Network error: {e}")
```

## Testing MCP Servers

### Unit Tests

```python
# autoarr/tests/unit/mcp_servers/sabnzbd/test_client.py
import pytest
from pytest_httpx import HTTPXMock
from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient

@pytest.fixture
def client():
    return SABnzbdClient(
        base_url="http://localhost:8080/sabnzbd",
        api_key="test-key",
    )

class TestSABnzbdClient:
    async def test_get_queue_returns_parsed_response(
        self, client, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(json={
            "queue": {
                "slots": [
                    {"nzo_id": "123", "filename": "test.nzb", "status": "Downloading", "percentage": 50}
                ]
            }
        })

        async with client:
            result = await client.get_queue()

        assert len(result.queue) == 1
        assert result.queue[0].nzo_id == "123"

    async def test_get_queue_handles_timeout(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_exception(httpx.TimeoutException("timeout"))

        async with client:
            with pytest.raises(RetryableError):
                await client.get_queue()

    async def test_auth_error_is_non_retryable(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=401)

        async with client:
            with pytest.raises(NonRetryableError):
                await client.get_queue()
```

### Integration Tests

```python
# autoarr/tests/integration/mcp_servers/test_sabnzbd_integration.py
import pytest

@pytest.mark.integration
class TestSABnzbdIntegration:
    async def test_full_workflow(self, mock_sabnzbd_server):
        """Test complete queue → history → retry workflow."""
        client = SABnzbdClient(
            base_url=mock_sabnzbd_server.url,
            api_key="test-key",
        )

        async with client:
            # Get queue
            queue = await client.get_queue()
            assert isinstance(queue.queue, list)

            # Get history
            history = await client.get_history(limit=10)
            assert isinstance(history.slots, list)
```

## MCP Orchestrator

The orchestrator manages all MCP servers:

```python
# autoarr/shared/core/orchestrator.py
from typing import Dict, Any
from autoarr.mcp_servers.sabnzbd.server import SABnzbdMCPServer
from autoarr.mcp_servers.sonarr.server import SonarrMCPServer
from autoarr.mcp_servers.radarr.server import RadarrMCPServer
from autoarr.mcp_servers.plex.server import PlexMCPServer

class MCPOrchestrator:
    """Coordinates all MCP servers."""

    def __init__(self):
        self.servers: Dict[str, Any] = {}
        self._initialize_servers()

    def _initialize_servers(self) -> None:
        """Initialize all configured MCP servers."""
        self.servers["sabnzbd"] = SABnzbdMCPServer()
        self.servers["sonarr"] = SonarrMCPServer()
        self.servers["radarr"] = RadarrMCPServer()
        self.servers["plex"] = PlexMCPServer()

    async def call_tool(self, server: str, tool: str, arguments: dict) -> Any:
        """Route tool call to appropriate server."""
        if server not in self.servers:
            raise ValueError(f"Unknown server: {server}")

        return await self.servers[server].call_tool(tool, arguments)

    async def get_all_tools(self) -> Dict[str, list]:
        """Get all available tools from all servers."""
        tools = {}
        for name, server in self.servers.items():
            tools[name] = await server.list_tools()
        return tools
```

## Checklist

Before deploying an MCP server:

- [ ] Client implements all required API operations
- [ ] Models validate all response fields
- [ ] Error handling distinguishes retryable vs non-retryable
- [ ] Retry logic with exponential backoff implemented
- [ ] Rate limiting respected
- [ ] Unit tests cover happy path and error cases
- [ ] Integration tests verify full workflow
- [ ] Tool schemas are accurate and complete
- [ ] Logging captures key operations and errors
- [ ] Connection pooling configured properly
