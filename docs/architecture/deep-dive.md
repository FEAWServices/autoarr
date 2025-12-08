# AutoArr Architecture Deep Dive

**Version:** 1.0.0
**Last Updated:** 2025-01-08
**Maintainers:** AutoArr Core Team

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [MCP Integration](#mcp-integration)
4. [Event-Driven Architecture](#event-driven-architecture)
5. [LLM Integration](#llm-integration)
6. [Database Design](#database-design)
7. [Frontend Architecture](#frontend-architecture)
8. [Security Architecture](#security-architecture)
9. [Deployment Architecture](#deployment-architecture)
10. [Performance Considerations](#performance-considerations)

---

## System Overview

### High-Level Architecture

AutoArr is an intelligent orchestration layer built on a modern, event-driven microservices architecture. The system leverages the Model Context Protocol (MCP) to create a unified interface for managing your media automation stack.

```mermaid
graph TB
    subgraph "Client Layer"
        UI[React Web UI]
        Mobile[Mobile Browser]
    end

    subgraph "API Gateway Layer"
        Gateway[FastAPI Gateway]
        WS[WebSocket Manager]
    end

    subgraph "Service Layer"
        Config[Configuration Service]
        Monitor[Monitoring Service]
        Request[Request Handler Service]
        Intelligence[Intelligence Engine]
    end

    subgraph "Integration Layer"
        Orchestrator[MCP Orchestrator]
        EventBus[Event Bus]
    end

    subgraph "MCP Servers"
        SAB[SABnzbd MCP]
        SON[Sonarr MCP]
        RAD[Radarr MCP]
        PLEX[Plex MCP]
    end

    subgraph "External Services"
        Claude[Claude API]
        Cache[Redis Cache]
        DB[(PostgreSQL/SQLite)]
    end

    UI --> Gateway
    Mobile --> Gateway
    Gateway --> Config
    Gateway --> Monitor
    Gateway --> Request
    Gateway <--> WS
    Config --> Intelligence
    Monitor --> Intelligence
    Request --> Intelligence
    Intelligence --> Orchestrator
    Orchestrator --> EventBus
    Orchestrator --> SAB
    Orchestrator --> SON
    Orchestrator --> RAD
    Orchestrator --> PLEX
    Intelligence --> Claude
    Gateway --> Cache
    Gateway --> DB
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant API as FastAPI Gateway
    participant Service as Core Service
    participant Intelligence as LLM Engine
    participant Orchestrator as MCP Orchestrator
    participant MCP as MCP Server
    participant External as External App

    UI->>API: HTTP Request
    API->>Service: Process Request
    Service->>Intelligence: Analyze Context
    Intelligence->>Intelligence: LLM Processing
    Intelligence->>Orchestrator: Execute MCP Call
    Orchestrator->>MCP: MCP Protocol Request
    MCP->>External: API Call
    External-->>MCP: API Response
    MCP-->>Orchestrator: MCP Response
    Orchestrator-->>Service: Processed Data
    Service->>API: Response Data
    API->>UI: HTTP Response
    API->>UI: WebSocket Update (async)
```

### Data Flow Architecture

```mermaid
graph LR
    subgraph "Ingestion"
        A[User Input] --> B[API Gateway]
        C[MCP Events] --> B
    end

    subgraph "Processing"
        B --> D[Service Layer]
        D --> E[Intelligence Engine]
        E --> F[LLM Analysis]
    end

    subgraph "Orchestration"
        F --> G[MCP Orchestrator]
        G --> H[Connection Pool]
    end

    subgraph "Integration"
        H --> I[SABnzbd]
        H --> J[Sonarr]
        H --> K[Radarr]
        H --> L[Plex]
    end

    subgraph "Persistence"
        D --> M[(Database)]
        D --> N[Event Log]
    end

    subgraph "Notification"
        D --> O[WebSocket]
        O --> P[UI Updates]
    end
```

### Technology Stack

#### Backend

- **Python 3.11+**: Modern async/await support, type hints
- **FastAPI 0.109+**: High-performance async web framework
- **SQLAlchemy 2.0**: ORM with async support
- **Alembic**: Database migrations
- **AsyncPG**: PostgreSQL async driver
- **aiosqlite**: SQLite async driver
- **Redis**: Caching and session storage
- **Anthropic Claude**: LLM intelligence

#### Frontend

- **React 18.2+**: Modern UI library with hooks
- **TypeScript 5.0+**: Type-safe JavaScript
- **Vite 5.0+**: Lightning-fast build tool
- **Tailwind CSS 4.0**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **React Query**: Data fetching and caching
- **React Router 6**: Client-side routing

#### MCP Integration

- **Python MCP SDK**: Official MCP implementation
- **stdio transport**: Local process communication
- **SSE transport**: Server-sent events for web

#### Testing & Quality

- **pytest**: Python testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **Playwright**: E2E browser testing
- **Black**: Python code formatting
- **ESLint**: TypeScript linting
- **Prettier**: Code formatting

---

## Backend Architecture

### FastAPI Application Structure

```
autoarr/api/
├── main.py                 # Application entry point
├── config.py               # Settings and configuration
├── database.py             # Database connection and session management
├── dependencies.py         # Dependency injection
├── middleware.py           # Custom middleware
├── models.py               # SQLAlchemy ORM models
├── models_config.py        # Configuration-specific models
├── routers/                # API endpoint routers
│   ├── configuration.py    # Configuration audit endpoints
│   ├── downloads.py        # Download monitoring endpoints
│   ├── health.py           # Health check endpoints
│   ├── media.py            # Plex integration endpoints
│   ├── mcp.py              # MCP proxy endpoints
│   ├── movies.py           # Radarr integration endpoints
│   ├── settings.py         # Settings management endpoints
│   └── shows.py            # Sonarr integration endpoints
├── services/               # Business logic services
│   ├── config_audit.py     # Configuration auditing service
│   ├── intelligent_recommendation.py  # LLM-powered recommendations
│   └── web_search.py       # Best practices web search
└── static/                 # Static assets
    └── admin.html          # Admin interface
```

### Service Layer Pattern

AutoArr uses a clear separation between routers (controllers) and services (business logic):

```python
# Router (routers/configuration.py)
@router.post("/audit")
async def audit_configuration(
    service: ConfigAuditService = Depends(get_config_audit_service)
):
    """API endpoint - thin layer"""
    return await service.run_audit()

# Service (services/config_audit.py)
class ConfigAuditService:
    """Business logic - thick layer"""

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        recommendation_engine: IntelligentRecommendationEngine,
        db: Database
    ):
        self.orchestrator = orchestrator
        self.engine = recommendation_engine
        self.db = db

    async def run_audit(self) -> AuditResult:
        # Fetch current configurations
        configs = await self._fetch_all_configs()

        # Get intelligent recommendations
        recommendations = await self.engine.generate_recommendations(configs)

        # Persist results
        await self.db.save_audit_result(recommendations)

        return recommendations
```

### Repository Pattern

Data access is abstracted through repository classes:

```python
class ConfigurationRepository:
    """Database access for configuration data"""

    def __init__(self, db: Database):
        self.db = db

    async def get_by_id(self, audit_id: str) -> Optional[ConfigAudit]:
        async with self.db.session() as session:
            result = await session.execute(
                select(ConfigAudit).where(ConfigAudit.id == audit_id)
            )
            return result.scalar_one_or_none()

    async def save(self, audit: ConfigAudit) -> ConfigAudit:
        async with self.db.session() as session:
            session.add(audit)
            await session.commit()
            await session.refresh(audit)
            return audit
```

### Dependency Injection

FastAPI's dependency injection system provides clean service instantiation:

```python
# dependencies.py
_orchestrator: Optional[MCPOrchestrator] = None

def get_orchestrator() -> MCPOrchestrator:
    """Get or create MCP orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MCPOrchestrator()
    return _orchestrator

async def get_config_audit_service(
    orchestrator: MCPOrchestrator = Depends(get_orchestrator),
    db: Database = Depends(get_database)
) -> ConfigAuditService:
    """Inject configuration audit service"""
    recommendation_engine = IntelligentRecommendationEngine(
        orchestrator=orchestrator
    )
    return ConfigAuditService(
        orchestrator=orchestrator,
        recommendation_engine=recommendation_engine,
        db=db
    )
```

### Error Handling Strategy

Comprehensive error handling at multiple levels:

```python
# Custom exceptions
class AutoArrException(Exception):
    """Base exception for AutoArr"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class MCPConnectionError(AutoArrException):
    """MCP server connection failed"""
    def __init__(self, server_name: str):
        super().__init__(
            f"Failed to connect to {server_name} MCP server",
            "MCP_CONNECTION_ERROR"
        )

# Middleware error handler
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AutoArrException as e:
            logger.error(f"AutoArr error: {e.code} - {e.message}")
            return JSONResponse(
                status_code=500,
                content={"error": e.code, "message": e.message}
            )
        except Exception as e:
            logger.exception("Unexpected error")
            return JSONResponse(
                status_code=500,
                content={"error": "INTERNAL_ERROR", "message": str(e)}
            )
```

### Logging and Monitoring

Structured logging throughout the application:

```python
import logging
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

class StructuredLogger:
    """JSON structured logging"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, event: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event": event,
            **kwargs
        }
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_entry)
        )

    def info(self, event: str, **kwargs):
        self.log("info", event, **kwargs)

    def error(self, event: str, **kwargs):
        self.log("error", event, **kwargs)

# Usage
logger = StructuredLogger("autoarr.service")
logger.info("config_audit_started", audit_id="12345", user_id="user1")
```

---

## MCP Integration

### MCP Protocol Overview

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to LLMs. AutoArr uses MCP to create a unified interface for all external media services.

#### MCP Architecture

```mermaid
graph TB
    subgraph "MCP Host (AutoArr)"
        Client[MCP Client]
        Orchestrator[MCP Orchestrator]
        Pool[Connection Pool]
    end

    subgraph "MCP Servers"
        SAB[SABnzbd Server]
        SON[Sonarr Server]
        RAD[Radarr Server]
        PLEX[Plex Server]
    end

    subgraph "External Applications"
        SAB_API[SABnzbd API]
        SON_API[Sonarr API]
        RAD_API[Radarr API]
        PLEX_API[Plex API]
    end

    Client --> Orchestrator
    Orchestrator --> Pool
    Pool --> SAB
    Pool --> SON
    Pool --> RAD
    Pool --> PLEX
    SAB --> SAB_API
    SON --> SON_API
    RAD --> RAD_API
    PLEX --> PLEX_API
```

### Orchestrator Pattern

The MCP Orchestrator manages all MCP server connections:

```python
class MCPOrchestrator:
    """
    Central orchestrator for all MCP server communications.

    Responsibilities:
    - Connection lifecycle management
    - Request routing
    - Error handling and retries
    - Performance monitoring
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConnection] = {}
        self._connection_pool = ConnectionPool(max_size=10)
        self._circuit_breaker = CircuitBreaker()
        self._metrics = MetricsCollector()

    async def connect_server(
        self,
        server_name: str,
        config: MCPServerConfig
    ) -> None:
        """
        Establish connection to an MCP server.

        Args:
            server_name: Unique identifier (e.g., "sabnzbd")
            config: Server configuration including transport and params
        """
        if server_name in self._servers:
            logger.warning(f"Server {server_name} already connected")
            return

        connection = await self._connection_pool.acquire(
            server_name=server_name,
            config=config
        )

        self._servers[server_name] = connection
        logger.info(f"Connected to MCP server: {server_name}")

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict
    ) -> Any:
        """
        Execute a tool on an MCP server with error handling.

        Args:
            server_name: Target MCP server
            tool_name: Tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPConnectionError: If server is not connected
            MCPToolError: If tool execution fails
        """
        if server_name not in self._servers:
            raise MCPConnectionError(server_name)

        # Circuit breaker pattern
        if not self._circuit_breaker.is_available(server_name):
            raise MCPConnectionError(
                f"Circuit breaker open for {server_name}"
            )

        server = self._servers[server_name]

        try:
            # Execute with retry
            result = await self._execute_with_retry(
                server=server,
                tool_name=tool_name,
                arguments=arguments,
                max_retries=3
            )

            # Record success
            self._circuit_breaker.record_success(server_name)
            self._metrics.record_call(server_name, tool_name, "success")

            return result

        except Exception as e:
            # Record failure
            self._circuit_breaker.record_failure(server_name)
            self._metrics.record_call(server_name, tool_name, "failure")

            logger.error(
                f"MCP tool call failed: {server_name}.{tool_name}",
                error=str(e)
            )
            raise MCPToolError(server_name, tool_name, str(e))

    async def _execute_with_retry(
        self,
        server: MCPServerConnection,
        tool_name: str,
        arguments: dict,
        max_retries: int
    ) -> Any:
        """Execute tool with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                result = await server.call_tool(tool_name, arguments)
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise

                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"Tool call failed, retrying in {wait_time}s",
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
                await asyncio.sleep(wait_time)
```

### Connection Pooling

Efficient connection management:

```python
class ConnectionPool:
    """
    Manages a pool of MCP server connections.

    Features:
    - Connection reuse
    - Health checking
    - Automatic reconnection
    - Resource limits
    """

    def __init__(self, max_size: int = 10):
        self._max_size = max_size
        self._connections: Dict[str, MCPServerConnection] = {}
        self._health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None

    async def acquire(
        self,
        server_name: str,
        config: MCPServerConfig
    ) -> MCPServerConnection:
        """Get or create a connection"""
        if server_name in self._connections:
            conn = self._connections[server_name]
            if await self._is_healthy(conn):
                return conn
            else:
                await self._remove_connection(server_name)

        if len(self._connections) >= self._max_size:
            raise ConnectionPoolExhausted(
                f"Connection pool full ({self._max_size})"
            )

        conn = await self._create_connection(config)
        self._connections[server_name] = conn

        # Start health checking if not running
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )

        return conn

    async def _create_connection(
        self,
        config: MCPServerConfig
    ) -> MCPServerConnection:
        """Create new MCP connection"""
        if config.transport == "stdio":
            return await StdioServerConnection.create(
                command=config.command,
                args=config.args,
                env=config.env
            )
        elif config.transport == "sse":
            return await SSEServerConnection.create(
                url=config.url,
                headers=config.headers
            )
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")

    async def _is_healthy(self, conn: MCPServerConnection) -> bool:
        """Check if connection is healthy"""
        try:
            await conn.ping(timeout=5.0)
            return True
        except Exception:
            return False

    async def _health_check_loop(self):
        """Periodic health checking"""
        while True:
            await asyncio.sleep(self._health_check_interval)

            for server_name, conn in list(self._connections.items()):
                if not await self._is_healthy(conn):
                    logger.warning(
                        f"Health check failed for {server_name}, removing"
                    )
                    await self._remove_connection(server_name)
```

### Error Handling and Retries

Robust error handling for MCP operations:

```python
class CircuitBreaker:
    """
    Circuit breaker pattern for MCP servers.

    States:
    - CLOSED: Normal operation
    - OPEN: Server unavailable, fail fast
    - HALF_OPEN: Testing if server recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self._states: Dict[str, str] = {}
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout

    def is_available(self, server_name: str) -> bool:
        """Check if server is available"""
        state = self._states.get(server_name, "CLOSED")

        if state == "CLOSED":
            return True

        if state == "OPEN":
            # Check if recovery timeout passed
            last_failure = self._last_failure_time.get(server_name, 0)
            if time.time() - last_failure > self._recovery_timeout:
                self._states[server_name] = "HALF_OPEN"
                return True
            return False

        if state == "HALF_OPEN":
            return True

        return False

    def record_success(self, server_name: str):
        """Record successful call"""
        self._states[server_name] = "CLOSED"
        self._failure_counts[server_name] = 0

    def record_failure(self, server_name: str):
        """Record failed call"""
        count = self._failure_counts.get(server_name, 0) + 1
        self._failure_counts[server_name] = count
        self._last_failure_time[server_name] = time.time()

        if count >= self._failure_threshold:
            self._states[server_name] = "OPEN"
            logger.error(
                f"Circuit breaker opened for {server_name}",
                failure_count=count
            )
```

### Adding New MCP Servers

Step-by-step guide to adding a new MCP server:

```python
# 1. Create MCP server package structure
# autoarr/mcp_servers/newservice/
# ├── __init__.py
# ├── server.py      # MCP server implementation
# └── README.md      # Documentation

# 2. Implement MCP server (server.py)
from mcp.server import Server
from mcp.types import Tool, TextContent

class NewServiceMCPServer:
    """MCP server for NewService"""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.server = Server("newservice")
        self._register_tools()

    def _register_tools(self):
        """Register available tools"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="get_status",
                    description="Get NewService status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "get_status":
                return await self._get_status()
            raise ValueError(f"Unknown tool: {name}")

    async def _get_status(self) -> list[TextContent]:
        """Fetch service status"""
        # Implement API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/status",
                headers={"X-Api-Key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()

        return [TextContent(
            type="text",
            text=json.dumps(data, indent=2)
        )]

    async def run(self):
        """Run MCP server"""
        async with stdio_server() as (read, write):
            await self.server.run(
                read,
                write,
                self.server.create_initialization_options()
            )

# 3. Add configuration support (config.py)
class Settings(BaseSettings):
    # Existing settings...

    # NewService MCP configuration
    newservice_api_url: Optional[str] = None
    newservice_api_key: Optional[str] = None

# 4. Register in orchestrator (dependencies.py)
async def initialize_mcp_servers(orchestrator: MCPOrchestrator):
    """Initialize all MCP servers"""
    settings = get_settings()

    # Existing servers...

    # NewService
    if settings.newservice_api_url and settings.newservice_api_key:
        await orchestrator.connect_server(
            "newservice",
            MCPServerConfig(
                transport="stdio",
                command="python",
                args=["-m", "autoarr.mcp_servers.newservice.server"],
                env={
                    "API_URL": settings.newservice_api_url,
                    "API_KEY": settings.newservice_api_key
                }
            )
        )

# 5. Add service integration (services/newservice.py)
class NewServiceService:
    """Business logic for NewService integration"""

    def __init__(self, orchestrator: MCPOrchestrator):
        self.orchestrator = orchestrator

    async def get_status(self) -> dict:
        """Get NewService status"""
        result = await self.orchestrator.call_tool(
            server_name="newservice",
            tool_name="get_status",
            arguments={}
        )
        return json.loads(result[0].text)

# 6. Create API endpoints (routers/newservice.py)
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/status")
async def get_status(
    service: NewServiceService = Depends(get_newservice_service)
):
    """Get NewService status"""
    return await service.get_status()

# 7. Add tests (tests/unit/mcp_servers/newservice/)
@pytest.mark.asyncio
async def test_get_status():
    """Test NewService status retrieval"""
    server = NewServiceMCPServer(
        api_url="http://localhost:8080",
        api_key="test-key"
    )
    # Add test implementation
```

---

## Event-Driven Architecture

### Event Bus Implementation

AutoArr uses an in-memory event bus for component communication:

```python
from typing import Callable, Dict, List
import asyncio

class EventBus:
    """
    Asynchronous event bus for component communication.

    Features:
    - Async event handlers
    - Topic-based subscription
    - Event history
    - Correlation tracking
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: str, handler: Callable):
        """
        Subscribe to event type.

        Args:
            event_type: Event type to subscribe to
            handler: Async callback function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type}", handler=handler.__name__)

    async def publish(self, event: Event):
        """
        Publish event to all subscribers.

        Args:
            event: Event to publish
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Get subscribers
        handlers = self._subscribers.get(event.type, [])

        if not handlers:
            logger.debug(f"No subscribers for event: {event.type}")
            return

        # Execute handlers in parallel
        tasks = [self._safe_execute(handler, event) for handler in handlers]
        await asyncio.gather(*tasks)

        logger.info(
            f"Published event: {event.type}",
            correlation_id=event.correlation_id,
            subscriber_count=len(handlers)
        )

    async def _safe_execute(self, handler: Callable, event: Event):
        """Execute handler with error handling"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Event handler failed: {handler.__name__}",
                event_type=event.type,
                error=str(e)
            )

    def get_history(
        self,
        event_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """Query event history"""
        filtered = self._event_history

        if event_type:
            filtered = [e for e in filtered if e.type == event_type]

        if correlation_id:
            filtered = [e for e in filtered if e.correlation_id == correlation_id]

        return filtered[-limit:]
```

### Event Types and Schemas

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import uuid

@dataclass
class Event:
    """Base event class"""
    type: str
    data: dict
    correlation_id: str
    timestamp: datetime = None
    source: str = "autoarr"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if not self.correlation_id:
            self.correlation_id = str(uuid.uuid4())

# Configuration Events
class ConfigAuditStartedEvent(Event):
    """Configuration audit started"""
    def __init__(self, audit_id: str, correlation_id: str):
        super().__init__(
            type="config.audit.started",
            data={"audit_id": audit_id},
            correlation_id=correlation_id
        )

class ConfigAuditCompletedEvent(Event):
    """Configuration audit completed"""
    def __init__(
        self,
        audit_id: str,
        recommendation_count: int,
        correlation_id: str
    ):
        super().__init__(
            type="config.audit.completed",
            data={
                "audit_id": audit_id,
                "recommendation_count": recommendation_count
            },
            correlation_id=correlation_id
        )

# Download Events
class DownloadFailedEvent(Event):
    """Download failed"""
    def __init__(
        self,
        download_id: str,
        title: str,
        reason: str,
        correlation_id: str
    ):
        super().__init__(
            type="download.failed",
            data={
                "download_id": download_id,
                "title": title,
                "reason": reason
            },
            correlation_id=correlation_id
        )

class DownloadRetryStartedEvent(Event):
    """Download retry started"""
    def __init__(
        self,
        download_id: str,
        retry_attempt: int,
        correlation_id: str
    ):
        super().__init__(
            type="download.retry.started",
            data={
                "download_id": download_id,
                "retry_attempt": retry_attempt
            },
            correlation_id=correlation_id
        )

# Content Request Events
class ContentRequestedEvent(Event):
    """Content requested"""
    def __init__(
        self,
        request_id: str,
        content_type: str,
        query: str,
        correlation_id: str
    ):
        super().__init__(
            type="content.requested",
            data={
                "request_id": request_id,
                "content_type": content_type,
                "query": query
            },
            correlation_id=correlation_id
        )

class ContentAddedEvent(Event):
    """Content added to library"""
    def __init__(
        self,
        request_id: str,
        content_id: str,
        title: str,
        correlation_id: str
    ):
        super().__init__(
            type="content.added",
            data={
                "request_id": request_id,
                "content_id": content_id,
                "title": title
            },
            correlation_id=correlation_id
        )
```

### Correlation Tracking

Track request flow across services:

```python
class CorrelationContext:
    """Context manager for correlation tracking"""

    _context: contextvars.ContextVar[str] = contextvars.ContextVar(
        "correlation_id",
        default=None
    )

    @classmethod
    def get(cls) -> Optional[str]:
        """Get current correlation ID"""
        return cls._context.get()

    @classmethod
    def set(cls, correlation_id: str):
        """Set correlation ID"""
        cls._context.set(correlation_id)

    @classmethod
    def generate(cls) -> str:
        """Generate and set new correlation ID"""
        correlation_id = str(uuid.uuid4())
        cls.set(correlation_id)
        return correlation_id

    @classmethod
    @contextmanager
    def with_correlation_id(cls, correlation_id: Optional[str] = None):
        """Context manager for correlation tracking"""
        if correlation_id is None:
            correlation_id = cls.generate()
        else:
            cls.set(correlation_id)

        try:
            yield correlation_id
        finally:
            cls._context.set(None)

# Usage in middleware
class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )

        with CorrelationContext.with_correlation_id(correlation_id):
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

# Usage in services
class ConfigAuditService:
    async def run_audit(self) -> AuditResult:
        correlation_id = CorrelationContext.get()

        # Publish event with correlation
        await self.event_bus.publish(
            ConfigAuditStartedEvent(
                audit_id=audit_id,
                correlation_id=correlation_id
            )
        )

        # Service logic...

        await self.event_bus.publish(
            ConfigAuditCompletedEvent(
                audit_id=audit_id,
                recommendation_count=len(recommendations),
                correlation_id=correlation_id
            )
        )
```

### Subscriber Patterns

Common event subscriber patterns:

```python
# WebSocket notification subscriber
class WebSocketNotifier:
    """Send events to connected WebSocket clients"""

    def __init__(self, connection_manager: WebSocketManager):
        self.connection_manager = connection_manager

    async def handle_event(self, event: Event):
        """Send event to WebSocket clients"""
        await self.connection_manager.broadcast({
            "type": event.type,
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        })

# Database persistence subscriber
class EventPersister:
    """Persist events to database"""

    def __init__(self, db: Database):
        self.db = db

    async def handle_event(self, event: Event):
        """Save event to database"""
        async with self.db.session() as session:
            event_record = EventRecord(
                type=event.type,
                data=event.data,
                correlation_id=event.correlation_id,
                timestamp=event.timestamp,
                source=event.source
            )
            session.add(event_record)
            await session.commit()

# Metrics collection subscriber
class MetricsCollector:
    """Collect metrics from events"""

    def __init__(self):
        self.metrics = {}

    async def handle_event(self, event: Event):
        """Update metrics based on event"""
        metric_key = f"event.{event.type}.count"
        self.metrics[metric_key] = self.metrics.get(metric_key, 0) + 1

# Register subscribers
event_bus = EventBus()

# WebSocket notifications
ws_notifier = WebSocketNotifier(connection_manager)
event_bus.subscribe("config.audit.completed", ws_notifier.handle_event)
event_bus.subscribe("download.failed", ws_notifier.handle_event)
event_bus.subscribe("content.added", ws_notifier.handle_event)

# Event persistence
persister = EventPersister(database)
event_bus.subscribe("*", persister.handle_event)  # Subscribe to all

# Metrics
metrics = MetricsCollector()
event_bus.subscribe("*", metrics.handle_event)
```

### WebSocket Integration

Real-time updates via WebSocket:

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class WebSocketManager:
    """
    Manages WebSocket connections.

    Features:
    - Connection tracking
    - Broadcast messaging
    - Room/channel support
    - Automatic reconnection handling
    """

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._rooms: Dict[str, Set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str
    ):
        """Accept and track WebSocket connection"""
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    async def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self._connections:
            del self._connections[client_id]

            # Remove from all rooms
            for room_clients in self._rooms.values():
                room_clients.discard(client_id)

            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self._connections:
            websocket = self._connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {client_id}: {e}")
                await self.disconnect(client_id)

    async def broadcast(self, message: dict, room: Optional[str] = None):
        """Broadcast message to all clients or room"""
        if room:
            client_ids = self._rooms.get(room, set())
        else:
            client_ids = self._connections.keys()

        tasks = [
            self.send_personal(message, client_id)
            for client_id in client_ids
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def join_room(self, client_id: str, room: str):
        """Add client to room"""
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(client_id)

    async def leave_room(self, client_id: str, room: str):
        """Remove client from room"""
        if room in self._rooms:
            self._rooms[room].discard(client_id)

# WebSocket endpoint
connection_manager = WebSocketManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await connection_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()

            # Handle client messages
            if data.get("type") == "join_room":
                await connection_manager.join_room(
                    client_id,
                    data["room"]
                )
            elif data.get("type") == "ping":
                await connection_manager.send_personal(
                    {"type": "pong"},
                    client_id
                )
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
```

---

## LLM Integration

### Claude API Integration

AutoArr uses Anthropic's Claude API for intelligent analysis:

````python
from anthropic import AsyncAnthropic
from typing import List, Optional

class ClaudeClient:
    """
    Claude API client for intelligent recommendations.

    Features:
    - Async API calls
    - Token usage tracking
    - Cost monitoring
    - Rate limiting
    - Fallback handling
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet-20240229"
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self._token_usage = TokenUsageTracker()
        self._rate_limiter = RateLimiter(requests_per_minute=50)

    async def analyze_configuration(
        self,
        config_data: dict,
        best_practices: List[dict]
    ) -> dict:
        """
        Analyze configuration against best practices.

        Args:
            config_data: Current configuration
            best_practices: List of best practices

        Returns:
            Analysis with recommendations
        """
        await self._rate_limiter.acquire()

        prompt = self._build_config_analysis_prompt(
            config_data,
            best_practices
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Track token usage
            self._token_usage.record(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )

            # Parse response
            analysis = self._parse_analysis_response(
                response.content[0].text
            )

            return analysis

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise LLMError(f"Failed to analyze configuration: {e}")

    def _build_config_analysis_prompt(
        self,
        config_data: dict,
        best_practices: List[dict]
    ) -> str:
        """Build structured prompt for configuration analysis"""
        return f"""You are an expert in media automation configuration.

Analyze the following configuration and provide recommendations based on best practices.

**Current Configuration:**
```json
{json.dumps(config_data, indent=2)}
````

**Best Practices:**
{self.\_format_best_practices(best_practices)}

**Task:**

1. Identify any configurations that deviate from best practices
2. Prioritize recommendations (critical, high, medium, low)
3. Provide clear explanations for each recommendation
4. Include specific configuration values to apply

**Output Format (JSON):**

````json
{{
  "recommendations": [
    {{
      "category": "category_name",
      "current_value": "current setting",
      "recommended_value": "recommended setting",
      "priority": "critical|high|medium|low",
      "rationale": "why this change is recommended",
      "impact": "what will improve"
    }}
  ],
  "summary": "overall assessment"
}}
```"""

    def _format_best_practices(self, practices: List[dict]) -> str:
        """Format best practices for prompt"""
        formatted = []
        for practice in practices:
            formatted.append(
                f"- **{practice['setting']}**: {practice['description']}\n"
                f"  Recommended: {practice['recommended_value']}\n"
                f"  Rationale: {practice['rationale']}"
            )
        return "\n\n".join(formatted)

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.rfind("```")
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return {"recommendations": [], "summary": "Parse error"}
````

### Prompt Engineering Strategy

Structured prompts for consistent results:

```python
class PromptTemplate:
    """Reusable prompt templates"""

    CONFIG_ANALYSIS = """You are an expert in {service} configuration...

**Context:**
{context}

**Task:**
{task}

**Output Format:**
{output_format}"""

    CONTENT_CLASSIFICATION = """Classify the following content request...

**User Request:**
"{user_query}"

**Classification:**
Determine if this is a:
1. Movie request
2. TV show request
3. Ambiguous (needs clarification)

Output JSON:
{{
  "type": "movie|tv|ambiguous",
  "confidence": 0.0-1.0,
  "reason": "explanation"
}}"""

    FAILURE_ANALYSIS = """Analyze why this download failed...

**Download Details:**
{download_info}

**Error Message:**
{error_message}

**Suggest:**
1. Root cause
2. Retry strategy
3. Alternative approaches"""

class PromptBuilder:
    """Build prompts from templates"""

    @staticmethod
    def build_config_analysis(
        service: str,
        config: dict,
        practices: List[dict]
    ) -> str:
        """Build configuration analysis prompt"""
        return PromptTemplate.CONFIG_ANALYSIS.format(
            service=service,
            context=json.dumps(config, indent=2),
            task="Analyze and recommend improvements",
            output_format="JSON with recommendations array"
        )

    @staticmethod
    def build_content_classification(query: str) -> str:
        """Build content classification prompt"""
        return PromptTemplate.CONTENT_CLASSIFICATION.format(
            user_query=query
        )
```

### Token Usage Optimization

Monitor and optimize LLM costs:

```python
class TokenUsageTracker:
    """Track and report token usage"""

    def __init__(self):
        self._usage_history: List[dict] = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def record(self, input_tokens: int, output_tokens: int):
        """Record token usage"""
        self._usage_history.append({
            "timestamp": datetime.utcnow(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        })
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

    def get_stats(self) -> dict:
        """Get usage statistics"""
        total_tokens = self._total_input_tokens + self._total_output_tokens

        # Estimate cost (Claude Sonnet pricing as of 2024)
        input_cost = (self._total_input_tokens / 1_000_000) * 3.00
        output_cost = (self._total_output_tokens / 1_000_000) * 15.00
        total_cost = input_cost + output_cost

        return {
            "total_requests": len(self._usage_history),
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "average_tokens_per_request": (
                total_tokens / len(self._usage_history)
                if self._usage_history else 0
            )
        }

    def get_recent_usage(self, hours: int = 24) -> List[dict]:
        """Get recent usage within time window"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            entry for entry in self._usage_history
            if entry["timestamp"] > cutoff
        ]
```

### Fallback Mechanisms

Graceful degradation when LLM unavailable:

```python
class IntelligentRecommendationEngine:
    """
    Generate recommendations using LLM with fallback.
    """

    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        rule_engine: Optional[RuleBasedEngine] = None
    ):
        self.claude_client = claude_client
        self.rule_engine = rule_engine or RuleBasedEngine()
        self._fallback_mode = False

    async def generate_recommendations(
        self,
        config_data: dict,
        best_practices: List[dict]
    ) -> List[Recommendation]:
        """
        Generate recommendations with fallback.

        Tries:
        1. Claude API (if available)
        2. Rule-based engine (fallback)
        """
        if self.claude_client and not self._fallback_mode:
            try:
                return await self._generate_with_llm(
                    config_data,
                    best_practices
                )
            except LLMError as e:
                logger.warning(
                    f"LLM generation failed, using fallback: {e}"
                )
                self._fallback_mode = True

        # Fallback to rule-based engine
        return await self._generate_with_rules(
            config_data,
            best_practices
        )

    async def _generate_with_llm(
        self,
        config_data: dict,
        best_practices: List[dict]
    ) -> List[Recommendation]:
        """Generate using Claude"""
        analysis = await self.claude_client.analyze_configuration(
            config_data,
            best_practices
        )
        return [
            Recommendation(**rec)
            for rec in analysis["recommendations"]
        ]

    async def _generate_with_rules(
        self,
        config_data: dict,
        best_practices: List[dict]
    ) -> List[Recommendation]:
        """Generate using rule-based logic"""
        return await self.rule_engine.analyze(
            config_data,
            best_practices
        )

class RuleBasedEngine:
    """Fallback rule-based recommendation engine"""

    async def analyze(
        self,
        config_data: dict,
        best_practices: List[dict]
    ) -> List[Recommendation]:
        """Apply rules to generate recommendations"""
        recommendations = []

        for practice in best_practices:
            setting_path = practice["setting"]
            current_value = self._get_nested_value(
                config_data,
                setting_path
            )
            recommended_value = practice["recommended_value"]

            if current_value != recommended_value:
                recommendations.append(Recommendation(
                    category=practice["category"],
                    current_value=str(current_value),
                    recommended_value=str(recommended_value),
                    priority=practice.get("priority", "medium"),
                    rationale=practice["rationale"],
                    impact=practice.get("impact", "Performance improvement")
                ))

        return recommendations

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = path.split(".")
        value = data
        for key in keys:
            value = value.get(key)
            if value is None:
                break
        return value
```

### Cost Monitoring

Track and alert on LLM costs:

```python
class CostMonitor:
    """Monitor LLM API costs"""

    def __init__(
        self,
        budget_limit_usd: float = 100.0,
        alert_threshold: float = 0.8
    ):
        self.budget_limit = budget_limit_usd
        self.alert_threshold = alert_threshold
        self.token_tracker = TokenUsageTracker()

    async def check_budget(self) -> dict:
        """Check current budget status"""
        stats = self.token_tracker.get_stats()
        current_cost = stats["estimated_cost_usd"]
        remaining = self.budget_limit - current_cost
        percentage_used = (current_cost / self.budget_limit) * 100

        status = {
            "current_cost_usd": current_cost,
            "budget_limit_usd": self.budget_limit,
            "remaining_usd": remaining,
            "percentage_used": percentage_used,
            "alert": percentage_used >= (self.alert_threshold * 100)
        }

        if status["alert"]:
            await self._send_alert(status)

        return status

    async def _send_alert(self, status: dict):
        """Send cost alert"""
        logger.warning(
            "LLM budget alert triggered",
            **status
        )
        # Could send email, Slack notification, etc.
```

---

## Database Design

### Schema Overview

AutoArr uses a relational database with the following main entities:

```mermaid
erDiagram
    ConfigAudit ||--o{ Recommendation : contains
    ConfigAudit {
        string id PK
        datetime created_at
        datetime updated_at
        string status
        int recommendation_count
        json metadata
    }

    Recommendation {
        string id PK
        string audit_id FK
        string category
        string current_value
        string recommended_value
        string priority
        text rationale
        text impact
        boolean applied
        datetime applied_at
    }

    DownloadHistory ||--o{ RetryAttempt : has
    DownloadHistory {
        string id PK
        string download_id
        string title
        string status
        datetime failed_at
        string failure_reason
        boolean recovered
        datetime recovered_at
    }

    RetryAttempt {
        string id PK
        string download_id FK
        int attempt_number
        string strategy
        datetime attempted_at
        string result
        text error_message
    }

    ContentRequest {
        string id PK
        string user_id
        string query
        string content_type
        string status
        datetime created_at
        string matched_title
        string matched_id
        datetime added_at
    }

    MCPServerConfig {
        string id PK
        string server_name UK
        string transport
        json config
        boolean enabled
        datetime last_connected
    }

    EventLog {
        string id PK
        string event_type
        json event_data
        string correlation_id
        datetime timestamp
        string source
    }

    Settings {
        string key PK
        json value
        datetime updated_at
    }
```

### SQLAlchemy Models

```python
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, JSON, Text, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class ConfigAudit(Base):
    """Configuration audit results"""
    __tablename__ = "config_audits"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, nullable=False)  # pending, completed, failed
    recommendation_count = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)

    # Relationships
    recommendations = relationship(
        "Recommendation",
        back_populates="audit",
        cascade="all, delete-orphan"
    )

class Recommendation(Base):
    """Configuration recommendation"""
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_id = Column(String, ForeignKey("config_audits.id"), nullable=False)
    category = Column(String, nullable=False)
    current_value = Column(Text)
    recommended_value = Column(Text)
    priority = Column(String, nullable=False)  # critical, high, medium, low
    rationale = Column(Text, nullable=False)
    impact = Column(Text)
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime)

    # Relationships
    audit = relationship("ConfigAudit", back_populates="recommendations")

class DownloadHistory(Base):
    """Download failure and recovery history"""
    __tablename__ = "download_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    download_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)  # failed, recovering, recovered
    failed_at = Column(DateTime, nullable=False)
    failure_reason = Column(Text)
    recovered = Column(Boolean, default=False)
    recovered_at = Column(DateTime)

    # Relationships
    retry_attempts = relationship(
        "RetryAttempt",
        back_populates="download",
        cascade="all, delete-orphan"
    )

class RetryAttempt(Base):
    """Download retry attempt"""
    __tablename__ = "retry_attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    download_id = Column(String, ForeignKey("download_history.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    strategy = Column(String, nullable=False)  # quality_fallback, alternative_release
    attempted_at = Column(DateTime, default=datetime.utcnow)
    result = Column(String)  # success, failed, pending
    error_message = Column(Text)

    # Relationships
    download = relationship("DownloadHistory", back_populates="retry_attempts")

class ContentRequest(Base):
    """Natural language content request"""
    __tablename__ = "content_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    query = Column(Text, nullable=False)
    content_type = Column(String)  # movie, tv, unknown
    status = Column(String, nullable=False)  # pending, matched, added, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    matched_title = Column(String)
    matched_id = Column(String)
    added_at = Column(DateTime)

class MCPServerConfig(Base):
    """MCP server configuration"""
    __tablename__ = "mcp_server_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    server_name = Column(String, unique=True, nullable=False)
    transport = Column(String, nullable=False)  # stdio, sse
    config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    last_connected = Column(DateTime)

class EventLog(Base):
    """Event log for auditing"""
    __tablename__ = "event_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String, nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    correlation_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, default="autoarr")

class Settings(Base):
    """Application settings"""
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Migration Strategy

Using Alembic for database migrations:

```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from autoarr.api.models import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

```bash
# Create new migration
alembic revision --autogenerate -m "Add download history table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Indexing Strategy

Optimized indexes for common queries:

```python
from sqlalchemy import Index

# Composite index for audit queries
Index(
    'ix_config_audits_status_created',
    ConfigAudit.status,
    ConfigAudit.created_at.desc()
)

# Covering index for download lookup
Index(
    'ix_download_history_lookup',
    DownloadHistory.download_id,
    DownloadHistory.status,
    DownloadHistory.failed_at
)

# Index for event correlation
Index(
    'ix_event_logs_correlation',
    EventLog.correlation_id,
    EventLog.timestamp.desc()
)

# Partial index for active requests
Index(
    'ix_content_requests_active',
    ContentRequest.status,
    ContentRequest.created_at,
    postgresql_where=(ContentRequest.status.in_(['pending', 'matched']))
)
```

### Query Optimization

Common optimized queries:

```python
class ConfigAuditRepository:
    """Optimized config audit queries"""

    async def get_recent_audits(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[ConfigAudit]:
        """Get recent audits with eager loading"""
        async with self.db.session() as session:
            query = (
                select(ConfigAudit)
                .options(selectinload(ConfigAudit.recommendations))
                .order_by(ConfigAudit.created_at.desc())
                .limit(limit)
            )

            if status:
                query = query.where(ConfigAudit.status == status)

            result = await session.execute(query)
            return result.scalars().all()

    async def get_audit_with_recommendations(
        self,
        audit_id: str
    ) -> Optional[ConfigAudit]:
        """Get audit with all recommendations"""
        async with self.db.session() as session:
            query = (
                select(ConfigAudit)
                .options(selectinload(ConfigAudit.recommendations))
                .where(ConfigAudit.id == audit_id)
            )

            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_unapplied_recommendations(
        self,
        priority: Optional[str] = None
    ) -> List[Recommendation]:
        """Get all unapplied recommendations"""
        async with self.db.session() as session:
            query = (
                select(Recommendation)
                .where(Recommendation.applied == False)
                .order_by(
                    case(
                        (Recommendation.priority == "critical", 1),
                        (Recommendation.priority == "high", 2),
                        (Recommendation.priority == "medium", 3),
                        else_=4
                    )
                )
            )

            if priority:
                query = query.where(Recommendation.priority == priority)

            result = await session.execute(query)
            return result.scalars().all()
```

---

## Frontend Architecture

### React Component Hierarchy

```
src/
├── App.tsx                    # Root component
├── layouts/
│   └── MainLayout.tsx         # Main layout with navigation
├── pages/
│   ├── Dashboard.tsx          # Dashboard page
│   ├── ConfigAudit.tsx        # Configuration audit page
│   ├── Downloads.tsx          # Download monitoring page
│   ├── ContentRequest.tsx     # Content request page
│   └── Settings.tsx           # Settings page
├── components/
│   ├── Dashboard/
│   │   ├── StatusCard.tsx     # Status overview card
│   │   ├── HealthIndicator.tsx # Health status indicator
│   │   └── ActivityFeed.tsx   # Recent activity feed
│   ├── ConfigAudit/
│   │   ├── AuditResults.tsx   # Audit results list
│   │   ├── RecommendationCard.tsx # Single recommendation
│   │   └── ApplyButton.tsx    # Apply recommendation button
│   ├── Downloads/
│   │   ├── QueueList.tsx      # Download queue list
│   │   ├── FailedDownloads.tsx # Failed downloads
│   │   └── RetryHistory.tsx   # Retry attempt history
│   ├── Chat/
│   │   ├── ChatInterface.tsx  # Chat container
│   │   ├── MessageList.tsx    # Message list
│   │   └── MessageInput.tsx   # Message input
│   └── common/
│       ├── Button.tsx         # Reusable button
│       ├── Card.tsx           # Card component
│       ├── Loading.tsx        # Loading spinner
│       └── ErrorBoundary.tsx  # Error boundary
├── services/
│   ├── api.ts                 # API client
│   ├── websocket.ts           # WebSocket client
│   └── auth.ts                # Authentication service
├── stores/
│   ├── configStore.ts         # Configuration state (Zustand)
│   ├── downloadStore.ts       # Download state
│   └── uiStore.ts             # UI state
├── hooks/
│   ├── useWebSocket.ts        # WebSocket hook
│   ├── useConfigAudit.ts      # Config audit hook
│   └── useDownloads.ts        # Downloads hook
├── types/
│   ├── api.ts                 # API types
│   ├── config.ts              # Configuration types
│   └── download.ts            # Download types
└── utils/
    ├── formatting.ts          # Formatting utilities
    └── validation.ts          # Validation utilities
```

### State Management with Zustand

```typescript
// stores/configStore.ts
import create from "zustand";
import { ConfigAudit, Recommendation } from "../types/config";

interface ConfigState {
  audits: ConfigAudit[];
  currentAudit: ConfigAudit | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchAudits: () => Promise<void>;
  runAudit: () => Promise<void>;
  applyRecommendation: (id: string) => Promise<void>;
  setCurrentAudit: (audit: ConfigAudit | null) => void;
}

export const useConfigStore = create<ConfigState>((set, get) => ({
  audits: [],
  currentAudit: null,
  loading: false,
  error: null,

  fetchAudits: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get("/api/v1/config/audits");
      set({ audits: response.data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  runAudit: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post("/api/v1/config/audit");
      const newAudit = response.data;
      set((state) => ({
        audits: [newAudit, ...state.audits],
        currentAudit: newAudit,
        loading: false,
      }));
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  applyRecommendation: async (id: string) => {
    try {
      await apiClient.post(`/api/v1/config/recommendations/${id}/apply`);

      // Update recommendation in state
      set((state) => ({
        currentAudit: state.currentAudit
          ? {
              ...state.currentAudit,
              recommendations: state.currentAudit.recommendations.map((rec) =>
                rec.id === id
                  ? { ...rec, applied: true, applied_at: new Date() }
                  : rec,
              ),
            }
          : null,
      }));
    } catch (error) {
      set({ error: error.message });
    }
  },

  setCurrentAudit: (audit) => set({ currentAudit: audit }),
}));
```

### API Service Layer

```typescript
// services/api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem("auth_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add correlation ID
        config.headers["X-Correlation-ID"] = this.generateCorrelationId();

        return config;
      },
      (error) => Promise.reject(error),
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle authentication error
          this.handleAuthError();
        }
        return Promise.reject(error);
      },
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  private generateCorrelationId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private handleAuthError(): void {
    localStorage.removeItem("auth_token");
    window.location.href = "/login";
  }
}

export const apiClient = new APIClient(
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
);
```

### WebSocket Management

```typescript
// services/websocket.ts
import { EventEmitter } from "events";

export class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private clientId: string;

  constructor(url: string) {
    super();
    this.url = url;
    this.clientId = this.generateClientId();
  }

  connect(): void {
    const wsUrl = `${this.url}/ws/${this.clientId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = this.handleOpen.bind(this);
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onerror = this.handleError.bind(this);
    this.ws.onclose = this.handleClose.bind(this);
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  joinRoom(room: string): void {
    this.send({
      type: "join_room",
      room,
    });
  }

  private handleOpen(): void {
    console.log("WebSocket connected");
    this.reconnectAttempts = 0;
    this.emit("connected");

    // Start heartbeat
    this.startHeartbeat();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data);
      this.emit("message", message);
      this.emit(message.type, message.data);
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }

  private handleError(error: Event): void {
    console.error("WebSocket error:", error);
    this.emit("error", error);
  }

  private handleClose(): void {
    console.log("WebSocket disconnected");
    this.emit("disconnected");

    // Attempt reconnection
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);

      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    } else {
      console.error("Max reconnection attempts reached");
      this.emit("reconnect_failed");
    }
  }

  private startHeartbeat(): void {
    setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: "ping" });
      }
    }, 30000);
  }

  private generateClientId(): string {
    return `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Hook for using WebSocket
import { useEffect, useRef } from "react";

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    wsRef.current = new WebSocketClient(url);
    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, [url]);

  return wsRef.current;
}
```

### Routing Strategy

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import ConfigAudit from './pages/ConfigAudit';
import Downloads from './pages/Downloads';
import ContentRequest from './pages/ContentRequest';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="config-audit" element={<ConfigAudit />} />
          <Route path="downloads" element={<Downloads />} />
          <Route path="content-request" element={<ContentRequest />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

---

## Security Architecture

### Authentication and Authorization

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = "your-secret-key"  # From environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract and validate user from JWT token"""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

### Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional

class ConfigAuditRequest(BaseModel):
    """Validated config audit request"""
    services: list[str] = Field(..., min_items=1, max_items=10)
    priority_filter: Optional[str] = Field(None, regex="^(critical|high|medium|low)$")

    @validator('services')
    def validate_services(cls, v):
        """Validate service names"""
        allowed_services = ['sabnzbd', 'sonarr', 'radarr', 'plex']
        for service in v:
            if service not in allowed_services:
                raise ValueError(f"Invalid service: {service}")
        return v

class ContentRequestInput(BaseModel):
    """Validated content request"""
    query: str = Field(..., min_length=1, max_length=500)

    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize user input"""
        # Remove potential SQL injection attempts
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            if char in v.lower():
                raise ValueError("Invalid characters in query")
        return v.strip()
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/config/audit")
@limiter.limit("10/minute")
async def audit_configuration(
    request: Request,
    service: ConfigAuditService = Depends(get_config_audit_service)
):
    """Rate-limited audit endpoint"""
    return await service.run_audit()
```

### Security Headers

```python
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response
```

### API Key Management

```python
class APIKeyManager:
    """Secure API key storage and retrieval"""

    def __init__(self, encryption_key: bytes):
        self.fernet = Fernet(encryption_key)

    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        return self.fernet.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
        return self.fernet.decrypt(encrypted_key.encode()).decode()

    async def store_api_key(
        self,
        service_name: str,
        api_key: str,
        db: Database
    ):
        """Store encrypted API key"""
        encrypted = self.encrypt_api_key(api_key)

        async with db.session() as session:
            setting = Settings(
                key=f"api_key.{service_name}",
                value={"encrypted_key": encrypted}
            )
            session.add(setting)
            await session.commit()

    async def get_api_key(
        self,
        service_name: str,
        db: Database
    ) -> Optional[str]:
        """Retrieve and decrypt API key"""
        async with db.session() as session:
            result = await session.execute(
                select(Settings).where(
                    Settings.key == f"api_key.{service_name}"
                )
            )
            setting = result.scalar_one_or_none()

            if setting:
                encrypted = setting.value["encrypted_key"]
                return self.decrypt_api_key(encrypted)

            return None
```

---

## Deployment Architecture

### Docker Container Architecture

```dockerfile
# Multi-stage build for optimized image
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-dev --no-root

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY autoarr /app/autoarr

# Create non-root user
RUN useradd -m -u 1000 autoarr && \
    chown -R autoarr:autoarr /app

USER autoarr

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "autoarr.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Production

```yaml
version: "3.8"

services:
  autoarr:
    image: autoarr/autoarr:latest
    container_name: autoarr
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://autoarr:${DB_PASSWORD}@postgres:5432/autoarr
      - REDIS_URL=redis://redis:6379/0
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - SABNZBD_API_URL=${SABNZBD_API_URL}
      - SABNZBD_API_KEY=${SABNZBD_API_KEY}
      - SONARR_API_URL=${SONARR_API_URL}
      - SONARR_API_KEY=${SONARR_API_KEY}
      - RADARR_API_URL=${RADARR_API_URL}
      - RADARR_API_KEY=${RADARR_API_KEY}
    volumes:
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    container_name: autoarr-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=autoarr
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=autoarr
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autoarr"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: autoarr-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: autoarr-network
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autoarr
  namespace: autoarr
spec:
  replicas: 3
  selector:
    matchLabels:
      app: autoarr
  template:
    metadata:
      labels:
        app: autoarr
    spec:
      containers:
        - name: autoarr
          image: autoarr/autoarr:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: autoarr-secrets
                  key: database-url
            - name: CLAUDE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: autoarr-secrets
                  key: claude-api-key
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: autoarr
  namespace: autoarr
spec:
  selector:
    app: autoarr
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

---

## Performance Considerations

### Caching Strategy

```python
from redis import asyncio as aioredis
import json

class CacheManager:
    """Redis-based caching"""

    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ):
        """Set cached value with TTL"""
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

    async def invalidate(self, pattern: str):
        """Invalidate cache by pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Cache decorator
def cached(ttl: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

# Usage
@cached(ttl=600)
async def get_configuration(service_name: str) -> dict:
    """Get configuration with caching"""
    return await fetch_configuration(service_name)
```

### Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class Database:
    """Database with connection pooling"""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )

        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self):
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
```

### Query Optimization

```python
# Use select_in loading for relationships
from sqlalchemy.orm import selectinload

async def get_audit_with_recommendations(audit_id: str):
    async with db.session() as session:
        result = await session.execute(
            select(ConfigAudit)
            .options(selectinload(ConfigAudit.recommendations))
            .where(ConfigAudit.id == audit_id)
        )
        return result.scalar_one_or_none()

# Use pagination for large result sets
async def get_audits_paginated(page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size

    async with db.session() as session:
        result = await session.execute(
            select(ConfigAudit)
            .order_by(ConfigAudit.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        return result.scalars().all()

# Use aggregation in database
async def get_recommendation_stats():
    async with db.session() as session:
        result = await session.execute(
            select(
                Recommendation.priority,
                func.count(Recommendation.id).label('count')
            )
            .group_by(Recommendation.priority)
        )
        return dict(result.all())
```

### Async Operations

```python
import asyncio

# Parallel API calls
async def fetch_all_configurations():
    """Fetch all service configurations in parallel"""
    tasks = [
        orchestrator.call_tool("sabnzbd", "get_config", {}),
        orchestrator.call_tool("sonarr", "get_config", {}),
        orchestrator.call_tool("radarr", "get_config", {}),
        orchestrator.call_tool("plex", "get_config", {})
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        "sabnzbd": results[0] if not isinstance(results[0], Exception) else None,
        "sonarr": results[1] if not isinstance(results[1], Exception) else None,
        "radarr": results[2] if not isinstance(results[2], Exception) else None,
        "plex": results[3] if not isinstance(results[3], Exception) else None
    }
```

---

## Conclusion

This architecture deep dive provides a comprehensive view of AutoArr's technical implementation. Key takeaways:

1. **Modular Design**: Clean separation of concerns with service layer pattern
2. **MCP Integration**: Unified interface for all external services
3. **Event-Driven**: Decoupled components communicate via event bus
4. **Intelligent**: LLM-powered analysis with fallback mechanisms
5. **Scalable**: Async operations, caching, and connection pooling
6. **Secure**: Authentication, input validation, and encrypted secrets
7. **Observable**: Structured logging, metrics, and correlation tracking

For questions or contributions, see [CONTRIBUTING.md](/app/docs/CONTRIBUTING.md).
