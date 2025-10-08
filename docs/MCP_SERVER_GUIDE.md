# MCP Server Development Guide

## Table of Contents

- [Introduction](#introduction)
- [What is MCP?](#what-is-mcp)
- [Getting Started](#getting-started)
- [MCP Server Structure](#mcp-server-structure)
- [Creating a New MCP Server](#creating-a-new-mcp-server)
- [Implementing Tools](#implementing-tools)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Example Servers](#example-servers)
- [Troubleshooting](#troubleshooting)

## Introduction

This guide teaches you how to create Model Context Protocol (MCP) servers for AutoArr. MCP servers are the integration layer that connects AutoArr to external applications like SABnzbd, Sonarr, Radarr, and Plex.

### Who This Guide Is For

- Developers adding new integrations to AutoArr
- Contributors extending existing MCP servers
- Anyone interested in understanding AutoArr's integration architecture

### Prerequisites

- Python 3.11+
- Understanding of async/await in Python
- Familiarity with REST APIs
- Knowledge of the application you're integrating (e.g., Sonarr API)

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol for AI-application communication developed by Anthropic.

### Key Concepts

**Tools**: Functions that an LLM can call to perform actions
**Resources**: Data sources that an LLM can read
**Prompts**: Templated interactions for common tasks

### Why MCP?

1. **Standardization**: Consistent interface across all integrations
2. **Type Safety**: JSON Schema validation for parameters
3. **Discoverability**: Self-documenting through tool listings
4. **LLM-Friendly**: Designed for AI agent interaction

## Getting Started

### Installation

```bash
# Install MCP SDK
pip install mcp

# Or with poetry
poetry add mcp
```

### Project Structure

```
autoarr/mcp_servers/mcp_servers/{app_name}/
├── __init__.py           # Package initialization
├── client.py             # API client for external app
├── models.py             # Pydantic models
├── server.py             # MCP server implementation
└── tests/
    ├── test_client.py    # Client tests
    └── test_server.py    # Server tests
```

## MCP Server Structure

### Basic Server Template

```python
"""
{App Name} MCP Server.

This module implements the MCP server for {App Name}.
"""

from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from .client import {AppName}Client

class {AppName}MCPServer:
    """
    MCP Server for {App Name}.

    Tools:
        - {app}_get_data: Get data from the application
        - {app}_set_config: Update configuration
    """

    def __init__(self, client: {AppName}Client) -> None:
        """
        Initialize the MCP server.

        Args:
            client: Application client instance
        """
        if client is None:
            raise ValueError("Client is required")

        self.client = client
        self.name = "{app_name}"
        self.version = "0.1.0"
        self._server = Server(self.name)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self._server.list_tools()
        async def list_tools() -> List[Tool]:
            return self._get_tools()

        @self._server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            return await self._call_tool(name, arguments)

    def _get_tools(self) -> List[Tool]:
        """Get list of available MCP tools."""
        return [
            # Tool definitions here
        ]

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Route tool calls to appropriate handlers."""
        # Implementation here
        pass
```

## Creating a New MCP Server

### Step 1: Create the API Client

First, create a client that wraps the external application's API.

```python
# client.py
import httpx
from typing import Dict, List, Optional

class MyAppClientError(Exception):
    """Custom exception for MyApp client errors."""
    pass

class MyAppClient:
    """
    Async HTTP client for MyApp API.

    This client handles all communication with MyApp's REST API.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the MyApp client.

        Args:
            base_url: Base URL of MyApp (e.g., http://localhost:8080)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict:
        """
        Make an HTTP request to MyApp API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body

        Returns:
            Response data as dictionary

        Raises:
            MyAppClientError: If request fails
        """
        url = f"{self.base_url}/api/{endpoint}"

        # Add API key to params
        if params is None:
            params = {}
        params["apikey"] = self.api_key

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise MyAppClientError(f"API request failed: {e}")

    async def get_items(self) -> List[Dict]:
        """
        Get all items.

        Returns:
            List of items
        """
        return await self._make_request("GET", "item")

    async def add_item(self, item_data: Dict) -> Dict:
        """
        Add a new item.

        Args:
            item_data: Item data

        Returns:
            Created item
        """
        return await self._make_request("POST", "item", json=item_data)
```

### Step 2: Define Data Models

Create Pydantic models for type safety and validation.

```python
# models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Item(BaseModel):
    """Item model."""
    id: int
    title: str
    status: str
    added_at: datetime

class ItemList(BaseModel):
    """List of items with pagination."""
    items: List[Item]
    total: int
    page: int = 1
    page_size: int = 10
```

### Step 3: Implement MCP Tools

Create tool definitions with JSON Schema.

```python
# server.py
def _get_tools(self) -> List[Tool]:
    """Get list of available MCP tools."""
    return [
        Tool(
            name="myapp_get_items",
            description="Get all items from MyApp",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1,
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Items per page (default: 10)",
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="myapp_add_item",
            description="Add a new item to MyApp",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Item title",
                    },
                    "data": {
                        "type": "object",
                        "description": "Additional item data",
                    },
                },
                "required": ["title"],
            },
        ),
    ]
```

### Step 4: Implement Tool Handlers

```python
async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Route tool calls to appropriate handlers.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent responses
    """
    try:
        if name == "myapp_get_items":
            return await self._handle_get_items(arguments)
        elif name == "myapp_add_item":
            return await self._handle_add_item(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"}),
                )
            ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": str(e)}),
            )
        ]

async def _handle_get_items(self, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_items tool call."""
    page = arguments.get("page", 1)
    page_size = arguments.get("page_size", 10)

    items = await self.client.get_items()

    # Paginate results
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "items": [item.dict() for item in paginated_items],
                "total": len(items),
                "page": page,
                "page_size": page_size,
            }),
        )
    ]

async def _handle_add_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle add_item tool call."""
    title = arguments.get("title")
    data = arguments.get("data", {})

    if not title:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Title is required"}),
            )
        ]

    item_data = {"title": title, **data}
    result = await self.client.add_item(item_data)

    return [
        TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "item": result,
            }),
        )
    ]
```

## Implementing Tools

### Tool Design Principles

1. **Single Responsibility**: Each tool should do one thing well
2. **Clear Naming**: Use `{app}_{action}_{resource}` pattern
3. **Comprehensive Schema**: Define all parameters with descriptions
4. **Error Messages**: Return helpful error messages
5. **JSON Responses**: Always return valid JSON

### Common Tool Patterns

#### Get/List Pattern

```python
Tool(
    name="app_get_items",
    description="Get items with optional filtering and pagination",
    inputSchema={
        "type": "object",
        "properties": {
            "filter": {
                "type": "string",
                "description": "Filter criteria",
            },
            "page": {
                "type": "integer",
                "description": "Page number",
                "default": 1,
            },
        },
        "required": [],
    },
)
```

#### Create/Add Pattern

```python
Tool(
    name="app_add_item",
    description="Add a new item",
    inputSchema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Item title",
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata",
            },
        },
        "required": ["title"],
    },
)
```

#### Update/Modify Pattern

```python
Tool(
    name="app_update_item",
    description="Update an existing item",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "Item ID",
            },
            "updates": {
                "type": "object",
                "description": "Fields to update",
            },
        },
        "required": ["id", "updates"],
    },
)
```

#### Search Pattern

```python
Tool(
    name="app_search",
    description="Search for items",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "filters": {
                "type": "object",
                "description": "Additional filters",
            },
        },
        "required": ["query"],
    },
)
```

## Error Handling

### Client Error Handling

```python
class MyAppClientError(Exception):
    """Base exception for MyApp client."""
    pass

class MyAppConnectionError(MyAppClientError):
    """Connection error."""
    pass

class MyAppAuthError(MyAppClientError):
    """Authentication error."""
    pass

class MyAppNotFoundError(MyAppClientError):
    """Resource not found."""
    pass

async def _make_request(self, method: str, endpoint: str) -> Dict:
    """Make request with proper error handling."""
    try:
        response = await self._client.request(method, url)
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError as e:
        raise MyAppConnectionError(f"Cannot connect: {e}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise MyAppAuthError("Invalid API key")
        elif e.response.status_code == 404:
            raise MyAppNotFoundError("Resource not found")
        else:
            raise MyAppClientError(f"HTTP {e.response.status_code}: {e}")
    except Exception as e:
        raise MyAppClientError(f"Unexpected error: {e}")
```

### Server Error Handling

```python
async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Call tool with comprehensive error handling."""
    try:
        # Route to handler
        if name == "myapp_get_items":
            return await self._handle_get_items(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Unknown tool: {name}",
                        "available_tools": [t.name for t in self._get_tools()],
                    }),
                )
            ]
    except MyAppAuthError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Authentication failed",
                    "message": str(e),
                    "help": "Check your API key configuration",
                }),
            )
        ]
    except MyAppConnectionError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Connection failed",
                    "message": str(e),
                    "help": "Verify the application is running and accessible",
                }),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Unexpected error",
                    "message": str(e),
                }),
            )
        ]
```

## Testing

### Unit Tests for Client

```python
# tests/test_client.py
import pytest
from unittest.mock import AsyncMock, patch
from myapp.client import MyAppClient, MyAppClientError

@pytest.mark.asyncio
async def test_get_items_success():
    """Test successful get_items call."""
    client = MyAppClient("http://localhost:8080", "test_key")

    with patch.object(client._client, 'request', new=AsyncMock()) as mock_request:
        mock_request.return_value.json.return_value = [
            {"id": 1, "title": "Test Item"}
        ]

        result = await client.get_items()

        assert len(result) == 1
        assert result[0]["title"] == "Test Item"

@pytest.mark.asyncio
async def test_get_items_connection_error():
    """Test connection error handling."""
    client = MyAppClient("http://localhost:8080", "test_key")

    with patch.object(client._client, 'request', new=AsyncMock()) as mock_request:
        mock_request.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(MyAppClientError):
            await client.get_items()
```

### Integration Tests for Server

```python
# tests/test_server.py
import pytest
from myapp.server import MyAppMCPServer
from myapp.client import MyAppClient

@pytest.fixture
async def server():
    """Create test server."""
    client = MyAppClient("http://localhost:8080", "test_key")
    server = MyAppMCPServer(client)
    yield server
    await client.close()

@pytest.mark.asyncio
async def test_list_tools(server):
    """Test tool listing."""
    tools = server._get_tools()
    assert len(tools) > 0
    assert any(t.name == "myapp_get_items" for t in tools)

@pytest.mark.asyncio
async def test_call_tool_success(server):
    """Test successful tool call."""
    with patch.object(server.client, 'get_items', new=AsyncMock()) as mock_get:
        mock_get.return_value = [{"id": 1, "title": "Test"}]

        result = await server._call_tool("myapp_get_items", {})

        assert len(result) == 1
        assert result[0].type == "text"
```

## Best Practices

### 1. Use Async Throughout

```python
# Good
async def get_items(self) -> List[Dict]:
    return await self._make_request("GET", "item")

# Bad
def get_items(self) -> List[Dict]:
    return requests.get(url).json()
```

### 2. Validate Parameters

```python
async def _handle_add_item(self, arguments: Dict[str, Any]) -> List[TextContent]:
    """Validate before processing."""
    title = arguments.get("title")

    if not title or not isinstance(title, str):
        return [TextContent(
            type="text",
            text=json.dumps({"error": "Invalid title parameter"}),
        )]

    # Process request
```

### 3. Use Type Hints

```python
# Good
async def get_items(self, page: int = 1) -> List[Item]:
    pass

# Bad
async def get_items(self, page=1):
    pass
```

### 4. Document Everything

```python
async def search_items(self, query: str, filters: Optional[Dict] = None) -> List[Item]:
    """
    Search for items matching the query.

    Args:
        query: Search query string
        filters: Optional filters (e.g., {"status": "active"})

    Returns:
        List of matching items

    Raises:
        MyAppClientError: If search fails
    """
    pass
```

### 5. Handle Pagination

```python
async def get_all_items(self) -> List[Item]:
    """Get all items with automatic pagination."""
    all_items = []
    page = 1

    while True:
        result = await self.get_items_page(page)
        all_items.extend(result["items"])

        if len(result["items"]) < result["page_size"]:
            break

        page += 1

    return all_items
```

## Example Servers

### SABnzbd MCP Server

The SABnzbd MCP server is a complete reference implementation.

**Location**: `/app/autoarr/mcp_servers/mcp_servers/sabnzbd/`

**Tools**:

- `sabnzbd_get_queue`: Get download queue
- `sabnzbd_get_history`: Get download history
- `sabnzbd_retry_download`: Retry failed download
- `sabnzbd_pause_queue`: Pause downloads
- `sabnzbd_resume_queue`: Resume downloads

**Key Features**:

- Comprehensive error handling
- Pagination support
- Clean separation of concerns
- Full test coverage

### Sonarr MCP Server

**Location**: `/app/autoarr/mcp_servers/mcp_servers/sonarr/`

**Tools**:

- `sonarr_get_series`: List all series
- `sonarr_search_series`: Search for series
- `sonarr_add_series`: Add new series
- `sonarr_get_calendar`: Get upcoming episodes
- `sonarr_get_queue`: Get download queue

## Troubleshooting

### Common Issues

#### Connection Timeouts

```python
# Increase timeout
self._client = httpx.AsyncClient(timeout=60.0)

# Or per-request
response = await self._client.get(url, timeout=60.0)
```

#### SSL/TLS Errors

```python
# Disable verification (development only!)
self._client = httpx.AsyncClient(verify=False)
```

#### JSON Parsing Errors

```python
try:
    data = response.json()
except json.JSONDecodeError:
    # Handle non-JSON response
    raise MyAppClientError(f"Invalid JSON response: {response.text}")
```

### Debugging Tips

1. **Enable Logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Print Requests**:

```python
print(f"Request: {method} {url}")
print(f"Params: {params}")
```

3. **Test with curl**:

```bash
curl -X GET "http://localhost:8080/api/item?apikey=YOUR_KEY"
```

4. **Use pytest with verbose output**:

```bash
pytest -v -s tests/test_server.py
```

---

**Guide Version**: 1.0.0
**Last Updated**: 2025-01-15
**Status**: Active
