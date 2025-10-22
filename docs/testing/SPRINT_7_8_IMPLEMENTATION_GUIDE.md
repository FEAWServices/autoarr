# Sprint 7-8 TDD Implementation Guide

**Complete guide for implementing Sprint 7 (Content Request Handler) and Sprint 8 (WebSocket Manager) using Test-Driven Development**

**Status**: Ready for Implementation
**Test Files Created**: 3 core test files + factories
**Expected Test Count**: 145-185 tests
**Target Coverage**: 85%+

---

## Quick Start

### 1. Run Existing Tests (Baseline)

```bash
# Run all existing tests to ensure green baseline
poetry run pytest

# Check current coverage
poetry run pytest --cov=autoarr --cov-report=html
```

### 2. Review Test Specifications

All test specifications are documented in:

- `/app/docs/testing/SPRINT_7_8_TEST_SPECIFICATIONS.md` - Complete test specs
- `/app/autoarr/tests/unit/services/test_request_handler.py` - 80+ tests
- `/app/autoarr/tests/unit/services/test_websocket_manager.py` - 60+ tests
- `/app/autoarr/tests/factories.py` - Test data factories

### 3. TDD Implementation Flow

For each feature:

1. **RED**: Run the test (it should fail)
2. **GREEN**: Write minimal code to make it pass
3. **REFACTOR**: Clean up and optimize

---

## Sprint 7: Content Request Handler

### Phase 1: Service Layer (Week 1)

#### Step 1: Basic Request Parsing

**Tests to implement first** (test_request_handler.py):

- `test_handler_initialization`
- `test_parse_simple_movie_request`
- `test_parse_empty_request_raises_error`

**Implementation**:

```bash
# Run tests (they will fail)
poetry run pytest autoarr/tests/unit/services/test_request_handler.py::TestRequestHandlerInitialization -v

# Create service file
touch autoarr/api/services/request_handler.py
```

**Minimal implementation** (autoarr/api/services/request_handler.py):

```python
"""Content Request Handler Service."""

from typing import Optional
from pydantic import BaseModel


class ParsedRequest(BaseModel):
    """Parsed content request."""
    user_input: str
    title: Optional[str] = None
    media_type: Optional[str] = None
    year: Optional[int] = None
    quality: Optional[str] = None
    confidence: float = 0.0


class RequestHandler:
    """Handle natural language content requests."""

    def __init__(self, llm_agent, tmdb_client, orchestrator, db_session):
        self.llm_agent = llm_agent
        self.tmdb_client = tmdb_client
        self.orchestrator = orchestrator
        self.db_session = db_session

    async def parse_request(self, user_input: str) -> ParsedRequest:
        """Parse user input into structured request."""
        if not user_input or not user_input.strip():
            raise ValueError("Request cannot be empty")

        # Simple parsing logic
        title = user_input.replace("Add ", "").replace("add ", "").strip()

        return ParsedRequest(
            user_input=user_input,
            title=title,
            confidence=0.8
        )
```

**Verify**:

```bash
# Tests should now pass
poetry run pytest autoarr/tests/unit/services/test_request_handler.py::TestRequestHandlerInitialization -v
```

#### Step 2: Advanced Parsing

Implement these test groups in order:

1. Year extraction tests
2. Quality extraction tests
3. Media type detection tests
4. Special character handling

**Run tests**:

```bash
poetry run pytest autoarr/tests/unit/services/test_request_handler.py::TestNaturalLanguageParsing -v
```

#### Step 3: LLM Integration

Implement:

- Media type classification
- Disambiguation
- LLM error handling

**Run tests**:

```bash
poetry run pytest autoarr/tests/unit/services/test_request_handler.py::TestMediaTypeClassification -v
```

#### Step 4: Search Integration

Implement TMDB, Radarr, Sonarr search integration.

**Run tests**:

```bash
poetry run pytest autoarr/tests/unit/services/test_request_handler.py::TestSearchIntegration -v
```

### Phase 2: Database Models (Week 2)

#### Step 1: Create Database Model

**Create migration**:

```bash
# Create database directory if it doesn't exist
mkdir -p autoarr/api/database

# Create models file
touch autoarr/api/database/models.py
```

**Minimal ContentRequest model**:

```python
"""Database models for content requests."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class RequestStatus(str, enum.Enum):
    """Content request status enum."""
    PENDING = "pending"
    SEARCHING = "searching"
    FOUND = "found"
    ADDING = "adding"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentRequest(Base):
    """Content request database model."""

    __tablename__ = "content_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(String, nullable=False)
    media_type = Column(String)  # "movie" or "tv"
    title = Column(String)
    year = Column(Integer)
    quality = Column(String)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    search_results = Column(JSON)  # Store search results as JSON
    selected_result_id = Column(String)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ContentRequest(id={self.id}, title='{self.title}', status='{self.status}')>"
```

**Create migration** (using Alembic or SQLAlchemy):

```bash
# If using Alembic
alembic revision -m "Add ContentRequest model"
alembic upgrade head
```

### Phase 3: API Endpoints (Week 2)

#### Step 1: Create Router

**Create router file**:

```bash
touch autoarr/api/routers/requests.py
```

**Minimal router**:

```python
"""Content Request API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from autoarr.api.database.models import ContentRequest
from autoarr.api.dependencies import get_db_session

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])


@router.post("/", status_code=201)
async def create_request(
    user_input: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new content request."""
    # Implementation here
    pass


@router.get("/")
async def list_requests(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """List content requests."""
    # Implementation here
    pass


@router.get("/{request_id}")
async def get_request(
    request_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get request details."""
    # Implementation here
    pass


@router.put("/{request_id}")
async def update_request(
    request_id: int,
    status: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Update request status."""
    # Implementation here
    pass


@router.delete("/{request_id}")
async def cancel_request(
    request_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Cancel a pending request."""
    # Implementation here
    pass
```

**Add router to main.py**:

```python
from autoarr.api.routers import requests

app.include_router(requests.router)
```

**Run endpoint tests**:

```bash
poetry run pytest autoarr/tests/unit/api/test_request_endpoints.py -v
```

---

## Sprint 8: WebSocket Manager

### Phase 1: Service Layer (Week 3)

#### Step 1: Basic WebSocket Manager

**Create service file**:

```bash
touch autoarr/api/services/websocket_manager.py
```

**Minimal implementation**:

```python
"""WebSocket Manager Service."""

from typing import Dict, Set, Any
from datetime import datetime, timezone
from fastapi import WebSocket
import json


class WebSocketManager:
    """Manage WebSocket connections and event broadcasting."""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()

        self.connections[connection_id] = {
            "websocket": websocket,
            "connected_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc),
            "state": "connected"
        }

    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client."""
        if connection_id in self.connections:
            del self.connections[connection_id]

        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]

    async def broadcast(self, event: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        disconnected = []

        for connection_id, conn_info in self.connections.items():
            try:
                websocket = conn_info["websocket"]
                await websocket.send_json(event)
            except Exception:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)


# Singleton instance
_manager_instance = None


def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = WebSocketManager()
    return _manager_instance
```

**Run tests**:

```bash
poetry run pytest autoarr/tests/unit/services/test_websocket_manager.py::TestWebSocketManagerInitialization -v
```

#### Step 2: Implement Subscription Management

Add subscription methods and event filtering.

**Run tests**:

```bash
poetry run pytest autoarr/tests/unit/services/test_websocket_manager.py::TestSubscriptionManagement -v
```

#### Step 3: Error Handling & Reconnection

Implement error handling and connection cleanup.

**Run tests**:

```bash
poetry run pytest autoarr/tests/unit/services/test_websocket_manager.py::TestErrorHandling -v
```

### Phase 2: WebSocket Endpoint (Week 3)

#### Step 1: Create WebSocket Endpoint

**Add to router** (or create new websocket router):

```python
from fastapi import WebSocket, WebSocketDisconnect
from autoarr.api.services.websocket_manager import get_websocket_manager


@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates."""
    manager = get_websocket_manager()
    connection_id = str(uuid.uuid4())

    try:
        await manager.connect(connection_id, websocket)

        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            # Handle client messages (subscribe, unsubscribe, etc.)
            message = json.loads(data)

            if message.get("type") == "subscribe":
                event_type = message.get("event_type")
                await manager.subscribe(connection_id, event_type)

            elif message.get("type") == "unsubscribe":
                event_type = message.get("event_type")
                await manager.unsubscribe(connection_id, event_type)

    except WebSocketDisconnect:
        await manager.disconnect(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(connection_id)
```

**Run integration tests**:

```bash
poetry run pytest autoarr/tests/integration/test_websocket_integration.py -v
```

---

## Testing Strategy

### Unit Tests (70%)

Run specific test classes:

```bash
# Request Handler
poetry run pytest autoarr/tests/unit/services/test_request_handler.py -v

# WebSocket Manager
poetry run pytest autoarr/tests/unit/services/test_websocket_manager.py -v
```

### Integration Tests (20%)

```bash
# API endpoints
poetry run pytest autoarr/tests/unit/api/test_request_endpoints.py -v

# WebSocket integration
poetry run pytest autoarr/tests/integration/test_websocket_integration.py -v
```

### Coverage Reports

```bash
# Generate coverage report
poetry run pytest --cov=autoarr.api.services --cov-report=html

# Open in browser
open htmlcov/index.html
```

---

## Test Data Usage

### Using Factories

```python
from autoarr.tests.factories import (
    ContentRequestFactory,
    SearchResultFactory,
    WebSocketEventFactory,
    MockWebSocketFactory,
)

# In tests
def test_something():
    # Create test data
    request = ContentRequestFactory.create(title="Inception", year=2010)
    search_result = SearchResultFactory.create_tmdb_movie_result()
    event = WebSocketEventFactory.create_request_status_event(123, "completed")
    mock_ws = MockWebSocketFactory.create()
```

### Mock Strategies

```python
# Mock LLM Agent
@pytest.fixture
def mock_llm_agent():
    mock = MagicMock()
    mock.classify_media_type = AsyncMock(return_value={"media_type": "movie"})
    return mock

# Mock TMDB Client
@pytest.fixture
def mock_tmdb_client():
    mock = MagicMock()
    mock.search_movie = AsyncMock(return_value={"results": [...]})
    return mock

# Mock WebSocket
@pytest.fixture
def mock_websocket():
    ws = MagicMock(spec=WebSocket)
    ws.send_json = AsyncMock()
    ws.accept = AsyncMock()
    return ws
```

---

## Checklist

### Sprint 7: Content Request Handler

- [ ] **Phase 1: Service Layer**
  - [ ] Basic request parsing (5 tests)
  - [ ] Year/quality extraction (8 tests)
  - [ ] Media type classification (6 tests)
  - [ ] TMDB integration (6 tests)
  - [ ] Radarr/Sonarr integration (4 tests)
  - [ ] Disambiguation (4 tests)
  - [ ] Request tracking (5 tests)
  - [ ] Error handling (4 tests)

- [ ] **Phase 2: Database Models**
  - [ ] ContentRequest model (4 tests)
  - [ ] Database migration
  - [ ] Model validation

- [ ] **Phase 3: API Endpoints**
  - [ ] POST /requests (5 tests)
  - [ ] GET /requests (5 tests)
  - [ ] GET /requests/{id} (3 tests)
  - [ ] PUT /requests/{id} (4 tests)
  - [ ] DELETE /requests/{id} (3 tests)

### Sprint 8: WebSocket Manager

- [ ] **Phase 1: Service Layer**
  - [ ] Connection management (6 tests)
  - [ ] Event broadcasting (5 tests)
  - [ ] Subscription management (6 tests)
  - [ ] Reconnection handling (3 tests)
  - [ ] Error handling (3 tests)
  - [ ] Performance tests (3 tests)

- [ ] **Phase 2: WebSocket Endpoint**
  - [ ] WebSocket connection (8 tests)
  - [ ] Message handling (4 tests)

- [ ] **Phase 3: Integration**
  - [ ] Event bus integration (3 tests)
  - [ ] Complete flow testing (3 tests)

---

## Success Criteria

### Functional

- [ ] All 145+ tests passing
- [ ] 85%+ code coverage
- [ ] All edge cases handled
- [ ] Error scenarios tested

### Non-Functional

- [ ] Request parsing < 100ms
- [ ] WebSocket broadcast < 100ms (100 clients)
- [ ] No memory leaks
- [ ] Thread-safe operations

### Documentation

- [ ] API documentation updated
- [ ] Code comments added
- [ ] Test documentation complete

---

## Troubleshooting

### Tests Failing

1. **Check test order**: Some tests may have dependencies
2. **Verify mocks**: Ensure mocks are set up correctly
3. **Check async**: Use `@pytest.mark.asyncio` for async tests
4. **Database**: Ensure in-memory DB is clean between tests

### Coverage Not Meeting Target

1. **Identify gaps**: `poetry run pytest --cov-report=term-missing`
2. **Add edge cases**: Focus on error paths
3. **Test negative cases**: Not just happy paths

### Performance Issues

1. **Parallel execution**: `poetry run pytest -n auto`
2. **Skip slow tests**: Use markers `@pytest.mark.slow`
3. **Profile tests**: `poetry run pytest --profile`

---

## Next Steps After Implementation

1. **Code Review**: Review all implementations
2. **Integration Testing**: Test complete flows
3. **Performance Testing**: Load test WebSocket with 100+ clients
4. **Documentation**: Update API docs and user guides
5. **Deployment**: Prepare for production deployment

---

**Last Updated**: 2025-10-18
**Sprint Status**: Ready for TDD Implementation
**Estimated Duration**: 3 weeks (1 week per phase)
