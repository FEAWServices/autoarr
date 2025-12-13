# FastAPI Patterns Skill

## Overview

This skill covers FastAPI best practices for AutoArr's backend API, including
router organization, dependency injection, async patterns, and error handling.

## Project Structure

```
autoarr/api/
├── main.py              # FastAPI app factory
├── dependencies.py      # Shared dependencies
├── exceptions.py        # Custom exceptions
├── middleware/          # Custom middleware
├── models.py           # Pydantic request/response models
├── routers/
│   ├── __init__.py
│   ├── audit.py        # /api/v1/audit/*
│   ├── chat.py         # /api/v1/chat/*
│   ├── activity.py     # /api/v1/activity/*
│   ├── settings.py     # /api/v1/settings/*
│   ├── health.py       # /health, /ready
│   └── websocket.py    # WebSocket endpoints
└── services/
    ├── configuration_manager.py
    ├── llm_agent.py
    ├── monitoring_service.py
    ├── recovery_service.py
    ├── request_handler.py
    ├── event_bus.py
    └── websocket_manager.py
```

## Router Organization

### Router Setup

```python
# autoarr/api/routers/settings.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from autoarr.api.dependencies import get_config_service
from autoarr.api.services.configuration_manager import ConfigurationManager

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"},
    },
)

class ConnectionTestRequest(BaseModel):
    """Request model for connection testing."""
    url: str = Field(..., description="Service URL")
    api_key_or_token: str = Field(..., description="API key or token")
    timeout: int = Field(default=10, ge=1, le=60, description="Timeout in seconds")

class ConnectionTestResponse(BaseModel):
    """Response model for connection testing."""
    success: bool
    message: str
    version: Optional[str] = None
    error: Optional[str] = None

@router.post(
    "/test/{service}",
    response_model=ConnectionTestResponse,
    summary="Test service connection",
    description="Test connection to an external service (sabnzbd, sonarr, radarr, plex)",
)
async def test_connection(
    service: str,
    request: ConnectionTestRequest,
    config_service: ConfigurationManager = Depends(get_config_service),
) -> ConnectionTestResponse:
    """Test connection to external service."""
    if service not in ["sabnzbd", "sonarr", "radarr", "plex"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown service: {service}",
        )

    try:
        result = await config_service.test_connection(
            service=service,
            url=request.url,
            api_key=request.api_key_or_token,
            timeout=request.timeout,
        )
        return ConnectionTestResponse(
            success=True,
            message="Connection successful",
            version=result.get("version"),
        )
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message="Connection failed",
            error=str(e),
        )
```

### Router Registration

```python
# autoarr/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from autoarr.api.routers import audit, chat, activity, settings, health, websocket

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="AutoArr API",
        description="Intelligent media automation orchestrator",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(activity.router, prefix="/api/v1")
    app.include_router(settings.router, prefix="/api/v1")
    app.include_router(websocket.router, prefix="/api/v1")

    return app

app = create_app()
```

## Dependency Injection

### Service Dependencies

```python
# autoarr/api/dependencies.py
from functools import lru_cache
from fastapi import Depends
from autoarr.api.services.configuration_manager import ConfigurationManager
from autoarr.api.services.llm_agent import LLMAgent
from autoarr.api.services.event_bus import EventBus
from autoarr.shared.core.config import Settings, get_settings

@lru_cache
def get_settings_cached() -> Settings:
    """Get cached application settings."""
    return get_settings()

def get_event_bus() -> EventBus:
    """Get event bus singleton."""
    return EventBus.get_instance()

def get_llm_agent(
    settings: Settings = Depends(get_settings_cached),
) -> LLMAgent:
    """Get LLM agent with settings."""
    return LLMAgent(api_key=settings.claude_api_key)

def get_config_service(
    settings: Settings = Depends(get_settings_cached),
    event_bus: EventBus = Depends(get_event_bus),
) -> ConfigurationManager:
    """Get configuration manager service."""
    return ConfigurationManager(
        event_bus=event_bus,
        sabnzbd_url=settings.sabnzbd_url,
        sonarr_url=settings.sonarr_url,
        radarr_url=settings.radarr_url,
    )
```

### Testing with Dependency Overrides

```python
# autoarr/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from autoarr.api.main import app
from autoarr.api.dependencies import get_config_service

@pytest.fixture
def mock_config_service():
    """Mock configuration service for testing."""
    from unittest.mock import AsyncMock

    service = AsyncMock()
    service.test_connection.return_value = {"version": "4.0.0"}
    return service

@pytest.fixture
async def client(mock_config_service):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_config_service] = lambda: mock_config_service

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

## Async Patterns

### Async Service Methods

```python
# autoarr/api/services/configuration_manager.py
import asyncio
from typing import Dict, Any, List
from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient
from autoarr.mcp_servers.sonarr.client import SonarrClient

class ConfigurationManager:
    """Service for configuration management and auditing."""

    async def get_all_configs(self) -> Dict[str, Any]:
        """Fetch configs from all services concurrently."""
        # Use asyncio.gather for concurrent requests
        sabnzbd_task = self._get_sabnzbd_config()
        sonarr_task = self._get_sonarr_config()
        radarr_task = self._get_radarr_config()

        results = await asyncio.gather(
            sabnzbd_task,
            sonarr_task,
            radarr_task,
            return_exceptions=True,  # Don't fail if one service is down
        )

        return {
            "sabnzbd": results[0] if not isinstance(results[0], Exception) else None,
            "sonarr": results[1] if not isinstance(results[1], Exception) else None,
            "radarr": results[2] if not isinstance(results[2], Exception) else None,
        }

    async def _get_sabnzbd_config(self) -> Dict[str, Any]:
        """Get SABnzbd configuration."""
        async with SABnzbdClient(self.sabnzbd_url, self.sabnzbd_key) as client:
            return await client.get_config()
```

### Background Tasks

```python
# autoarr/api/routers/audit.py
from fastapi import BackgroundTasks

@router.post("/audit/start")
async def start_audit(
    background_tasks: BackgroundTasks,
    config_service: ConfigurationManager = Depends(get_config_service),
):
    """Start configuration audit in background."""
    # Schedule audit to run in background
    background_tasks.add_task(config_service.run_full_audit)

    return {"status": "started", "message": "Audit running in background"}
```

## Error Handling

### Custom Exceptions

```python
# autoarr/api/exceptions.py
from fastapi import HTTPException, status

class AutoArrException(Exception):
    """Base exception for AutoArr."""
    pass

class ServiceConnectionError(AutoArrException):
    """Failed to connect to external service."""
    def __init__(self, service: str, message: str):
        self.service = service
        self.message = message
        super().__init__(f"{service}: {message}")

class ConfigurationError(AutoArrException):
    """Configuration validation error."""
    pass

class LLMError(AutoArrException):
    """LLM API error."""
    pass

# HTTP Exceptions
def service_unavailable(service: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Service unavailable: {service}",
    )

def bad_request(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )
```

### Exception Handlers

```python
# autoarr/api/main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from autoarr.api.exceptions import AutoArrException, ServiceConnectionError

@app.exception_handler(AutoArrException)
async def autoarr_exception_handler(request: Request, exc: AutoArrException):
    """Handle AutoArr-specific exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": exc.__class__.__name__},
    )

@app.exception_handler(ServiceConnectionError)
async def service_connection_handler(request: Request, exc: ServiceConnectionError):
    """Handle service connection errors."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.message,
            "service": exc.service,
            "type": "ServiceConnectionError",
        },
    )
```

## WebSocket Handling

```python
# autoarr/api/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from autoarr.api.services.websocket_manager import WebSocketManager

router = APIRouter()
manager = WebSocketManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_json()
            await manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# autoarr/api/services/websocket_manager.py
from typing import List, Dict, Any
from fastapi import WebSocket
import json

class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection closed, will be cleaned up
                pass

    async def send_event(self, event_type: str, data: Dict[str, Any]):
        """Send typed event to all clients."""
        await self.broadcast({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
```

## Request Validation

### Pydantic Models

```python
# autoarr/api/models.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"

class ContentRequest(BaseModel):
    """Request model for content requests via chat."""
    query: str = Field(..., min_length=1, max_length=500)
    content_type: Optional[ContentType] = None
    quality_profile: Optional[str] = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        # Strip and validate
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        return v

class AuditResult(BaseModel):
    """Response model for configuration audit."""
    health_score: int = Field(ge=0, le=100)
    recommendations: List["Recommendation"]
    scanned_at: datetime
    services_checked: List[str]

class Recommendation(BaseModel):
    """A single audit recommendation."""
    id: str
    service: str
    setting: str
    current_value: Optional[str]
    recommended_value: str
    priority: str = Field(pattern="^(critical|high|medium|low)$")
    explanation: str
    auto_apply: bool = False
```

## Testing

```python
# autoarr/tests/unit/api/test_settings_router.py
import pytest
from httpx import AsyncClient

class TestSettingsRouter:
    async def test_test_connection_success(self, client: AsyncClient, mock_config_service):
        """Test successful connection test."""
        response = await client.post(
            "/api/v1/settings/test/sabnzbd",
            json={
                "url": "http://localhost:8080",
                "api_key_or_token": "test-key",
                "timeout": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["version"] == "4.0.0"

    async def test_test_connection_invalid_service(self, client: AsyncClient):
        """Test with invalid service name."""
        response = await client.post(
            "/api/v1/settings/test/invalid",
            json={
                "url": "http://localhost:8080",
                "api_key_or_token": "test-key",
            },
        )

        assert response.status_code == 400
        assert "Unknown service" in response.json()["detail"]

    async def test_test_connection_validation_error(self, client: AsyncClient):
        """Test with invalid request body."""
        response = await client.post(
            "/api/v1/settings/test/sabnzbd",
            json={"url": ""},  # Missing required fields
        )

        assert response.status_code == 422  # Validation error
```

## Checklist

Before deploying API changes:

- [ ] Router has appropriate prefix and tags
- [ ] All endpoints have request/response models
- [ ] Dependency injection used for services
- [ ] Async used for all I/O operations
- [ ] Error handling returns appropriate status codes
- [ ] Input validation with Pydantic
- [ ] Tests cover happy path and error cases
- [ ] OpenAPI documentation is accurate
- [ ] CORS configured appropriately
- [ ] Rate limiting applied where needed
