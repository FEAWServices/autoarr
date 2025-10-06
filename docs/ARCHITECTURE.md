# AutoArr Technical Architecture

## System Overview

AutoArr is a containerized orchestration platform built on a microservices architecture with MCP (Model Context Protocol) as the integration backbone. The system emphasizes modularity, testability, and intelligent decision-making.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         AutoArr Container                      │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Web UI Layer                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐│ │
│  │  │Dashboard │  │Chat UI   │  │Config Audit UI       ││ │
│  │  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘│ │
│  │       │             │                   │             │ │
│  │       └─────────────┴───────────────────┘             │ │
│  └────────────────────────┬────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │                   API Gateway                           │ │
│  │              (FastAPI / Express)                        │ │
│  └────────────────────────┬────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │                 Core Services Layer                     │ │
│  │                                                         │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │Configuration│  │  Monitoring  │  │   Request    │ │ │
│  │  │   Manager   │  │   Service    │  │   Handler    │ │ │
│  │  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘ │ │
│  │         │                │                  │         │ │
│  │  ┌──────▼────────────────▼──────────────────▼───────┐ │ │
│  │  │          Intelligence Engine                     │ │ │
│  │  │  ┌──────────┐  ┌────────────┐  ┌──────────────┐│ │ │
│  │  │  │LLM Agent │  │Web Search  │  │Decision Tree ││ │ │
│  │  │  └──────────┘  └────────────┘  └──────────────┘│ │ │
│  │  └──────────────────────┬──────────────────────────┘ │ │
│  │                         │                            │ │
│  │  ┌──────────────────────▼──────────────────────────┐ │ │
│  │  │            MCP Client Orchestrator               │ │ │
│  │  └──────┬──────────┬──────────┬───────────┬────────┘ │ │
│  └─────────┼──────────┼──────────┼───────────┼──────────┘ │
│            │          │          │           │            │
│  ┌─────────▼───┐ ┌────▼────┐ ┌──▼─────┐ ┌───▼──────┐    │
│  │  SABnzbd    │ │ Sonarr  │ │ Radarr │ │  Plex    │    │
│  │ MCP Server  │ │   MCP   │ │  MCP   │ │   MCP    │    │
│  └─────────┬───┘ └────┬────┘ └──┬─────┘ └───┬──────┘    │
└────────────┼──────────┼─────────┼───────────┼────────────┘
             │          │         │           │
             │          │         │           │
    ┌────────▼──────────▼─────────▼───────────▼────────┐
    │           External Applications                   │
    │  ┌──────────┐  ┌────────┐  ┌────────┐  ┌─────┐  │
    │  │ SABnzbd  │  │ Sonarr │  │ Radarr │  │Plex │  │
    │  └──────────┘  └────────┘  └────────┘  └─────┘  │
    └───────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Web UI Layer

**Technology**: React 18+ with TypeScript  
**Styling**: Tailwind CSS for mobile-first design  
**State Management**: Zustand (lightweight, ideal for our use case)  
**Build Tool**: Vite

#### Components
- **Dashboard**: Real-time status overview, health indicators
- **Chat Interface**: Natural language content requests
- **Configuration Audit**: Interactive checklist with explanations
- **Settings**: MCP server connections, user preferences
- **Activity Log**: Transparent action history

#### Responsibilities
- Render responsive, mobile-first UI
- WebSocket connection for real-time updates
- Client-side validation
- Optimistic UI updates

### 2. API Gateway

**Technology**: FastAPI (Python) for rapid development and async support  
**Alternative**: Express.js (TypeScript) if team prefers Node.js

#### Endpoints
```
POST   /api/v1/config/audit          - Trigger configuration audit
GET    /api/v1/config/recommendations - Get optimization recommendations
POST   /api/v1/config/apply           - Apply configuration change
POST   /api/v1/request/content        - Natural language content request
GET    /api/v1/monitoring/status      - Get system status
GET    /api/v1/monitoring/queue       - Get download queue status
POST   /api/v1/monitoring/retry       - Manually trigger retry
WS     /api/v1/stream                 - WebSocket for real-time updates
```

#### Responsibilities
- Request validation
- Authentication/Authorization (JWT)
- Rate limiting
- WebSocket management
- Error handling and logging

### 3. Core Services Layer

#### Configuration Manager
**Responsibilities:**
- Connects to MCP servers to fetch current configurations
- Compares against best practice database
- Generates audit checklist
- Applies approved configuration changes
- Tracks configuration history

**Key Classes:**
```python
class ConfigurationManager:
    async def audit_application(app_name: str) -> AuditResult
    async def get_recommendations(app_name: str) -> List[Recommendation]
    async def apply_configuration(app_name: str, changes: Dict) -> bool
    async def rollback_configuration(app_name: str, version: int) -> bool
```

#### Monitoring Service
**Responsibilities:**
- Polls MCP servers for queue status (SABnzbd)
- Monitors wanted lists (Sonarr, Radarr)
- Detects failed downloads
- Triggers recovery actions
- Maintains health metrics

**Key Classes:**
```python
class MonitoringService:
    async def check_download_queue() -> QueueStatus
    async def check_wanted_lists() -> List[WantedItem]
    async def detect_failures() -> List[FailedDownload]
    async def trigger_recovery(item: FailedDownload) -> bool
```

#### Request Handler
**Responsibilities:**
- Processes natural language content requests
- Determines content type (movie vs. TV show)
- Routes to appropriate MCP server (Radarr/Sonarr)
- Tracks request status
- Provides user feedback

**Key Classes:**
```python
class RequestHandler:
    async def process_request(text: str) -> ContentRequest
    async def classify_content(query: str) -> ContentType
    async def add_to_application(content: ContentRequest) -> bool
    async def get_request_status(request_id: str) -> RequestStatus
```

### 4. Intelligence Engine

**Core Technology**: Claude (Anthropic) via API for reasoning
**Local Model**: Llama 3.1 8B fine-tuned on *arr documentation (optional)
**Vector Database**: ChromaDB for documentation embeddings

#### LLM Agent
**Responsibilities:**
- Analyzes configuration audit results
- Generates context-aware recommendations
- Considers application interactions (e.g., Sonarr → SABnzbd settings)
- Explains reasoning for recommendations
- Handles natural language queries

**Interaction Pattern:**
```python
class LLMAgent:
    async def analyze_configuration(
        app: str, 
        current_config: Dict, 
        best_practices: List[Practice]
    ) -> Analysis
    
    async def recommend_next_action(
        context: ConfigurationContext
    ) -> Recommendation
    
    async def classify_content_request(
        query: str
    ) -> ClassificationResult
```

#### Web Search Integration
**Technology**: Brave Search API or SearxNG (self-hosted)

**Responsibilities:**
- Searches for latest best practices
- Finds release notes for applications
- Discovers community recommendations (Reddit, forums)
- Caches results to minimize API calls

**Key Classes:**
```python
class WebSearchService:
    async def search_best_practices(app: str, topic: str) -> List[SearchResult]
    async def get_latest_recommendations(app: str) -> List[Practice]
    async def check_cache(query: str) -> Optional[CachedResult]
```

#### Decision Tree
**Responsibilities:**
- Fallback for LLM (if API unavailable)
- Fast path for common scenarios
- Rule-based recovery logic
- Priority scoring for wanted items

### 5. MCP Client Orchestrator

**Technology**: MCP Python SDK

**Responsibilities:**
- Manages connections to all MCP servers
- Handles authentication
- Provides unified interface to core services
- Connection pooling
- Error handling and retries

**Key Classes:**
```python
class MCPOrchestrator:
    async def connect_all() -> bool
    async def call_tool(server: str, tool: str, params: Dict) -> Result
    async def get_server_status(server: str) -> ServerStatus
    async def disconnect_all() -> None
```

### 6. MCP Servers (One per Application)

Each MCP server is a standalone process that wraps the application's API.

#### SABnzbd MCP Server
**Tools:**
- `get_queue` - Current download queue
- `get_history` - Download history
- `retry_download` - Retry failed download
- `get_config` - Current configuration
- `set_config` - Update configuration
- `pause_queue` - Pause downloads
- `resume_queue` - Resume downloads

#### Sonarr MCP Server
**Tools:**
- `get_series` - List all series
- `get_wanted` - Wanted episodes
- `add_series` - Add new series
- `search_series` - Search for series
- `get_config` - Current configuration
- `set_config` - Update configuration
- `trigger_search` - Manual episode search

#### Radarr MCP Server
**Tools:**
- `get_movies` - List all movies
- `get_wanted` - Wanted movies
- `add_movie` - Add new movie
- `search_movie` - Search for movie
- `get_config` - Current configuration
- `set_config` - Update configuration
- `trigger_search` - Manual movie search

#### Plex MCP Server
**Tools:**
- `get_libraries` - List libraries
- `get_recently_added` - Recent content
- `scan_library` - Trigger library scan
- `get_config` - Current configuration
- `optimize_database` - Optimize Plex DB

## Data Flow

### Configuration Audit Flow
```
1. User requests audit via UI
2. API Gateway receives request
3. Configuration Manager:
   - Calls MCP servers to get current configs
   - Fetches best practices from database
   - Searches web for latest recommendations
4. Intelligence Engine:
   - LLM analyzes differences
   - Generates prioritized recommendations
5. Results returned to UI
6. User reviews and approves changes
7. Configuration Manager applies via MCP
8. Success/failure returned to user
```

### Download Recovery Flow
```
1. Monitoring Service polls SABnzbd queue (every 2 minutes)
2. Detects failed download
3. Identifies source application (Sonarr/Radarr)
4. Intelligence Engine:
   - Analyzes failure reason
   - Determines retry strategy
5. Calls appropriate MCP server to trigger new search
6. Monitors new download
7. Logs action in Activity Log
8. Notifies user via WebSocket
```

### Content Request Flow
```
1. User sends natural language request via chat
2. API Gateway validates and queues request
3. Request Handler:
   - Sends query to LLM for classification
   - Determines if movie (Radarr) or TV show (Sonarr)
   - Extracts title, year, quality preferences
4. Intelligence Engine:
   - May search web for disambiguation
   - Confirms with user if multiple matches
5. MCP Orchestrator:
   - Calls appropriate MCP server to add content
   - Triggers search
6. Monitoring Service tracks progress
7. User receives status updates via WebSocket
```

## Data Storage

### Database: SQLite (local) or PostgreSQL (SaaS)

#### Schema Overview

**configurations**
- id, app_name, config_json, created_at, applied_at, applied_by

**audit_results**
- id, app_name, audit_json, recommendations_json, created_at

**recommendations**
- id, audit_id, title, description, priority, status, applied_at

**content_requests**
- id, user_query, content_type, title, year, status, created_at, completed_at

**activity_log**
- id, action_type, app_name, details_json, timestamp

**best_practices**
- id, app_name, category, practice_text, source_url, last_updated

**search_cache**
- id, query, results_json, expires_at

## Security Architecture

### Authentication
- JWT tokens for API access
- API keys for MCP server connections (stored encrypted)
- Optional LDAP/OAuth for enterprise

### Authorization
- Role-based access control (Admin, User, Read-only)
- Action-level permissions
- Audit trail for all configuration changes

### Data Protection
- Secrets stored in encrypted vault (HashiCorp Vault or environment variables)
- TLS for all external communications
- MCP connections over secure WebSocket (wss://)

### Container Security
- Non-root user
- Read-only filesystem where possible
- Minimal base image (Alpine Linux)
- Regular security scanning

## Scalability Considerations

### Current Design (Single Container)
- Suitable for up to 10,000 media items
- Single user or small household
- All services in one container

### Future SaaS Design
- Microservices architecture (Kubernetes)
- Separate pods for UI, API, Intelligence, MCP Orchestrator
- Horizontal scaling for MCP servers
- Managed database (PostgreSQL)
- Message queue for async tasks (RabbitMQ/Redis)

## Monitoring and Observability

### Metrics (Prometheus)
- API request latency
- MCP call success rate
- Download recovery success rate
- LLM inference time
- Queue sizes

### Logging (Structured JSON)
- Application logs
- Access logs
- Error logs
- Audit logs

### Tracing (OpenTelemetry)
- Request flow across services
- MCP call chains
- Performance bottlenecks

### Health Checks
- `/health` - Overall system health
- `/health/mcp/{server}` - Individual MCP server health
- `/health/services` - Core services health

## Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Container | Docker | Universal deployment |
| API Gateway | FastAPI (Python) | Async, fast, great docs |
| UI Framework | React + TypeScript | Industry standard, great ecosystem |
| Styling | Tailwind CSS | Rapid development, mobile-first |
| State Management | Zustand | Simple, performant |
| Database | SQLite → PostgreSQL | Easy start, clear upgrade path |
| MCP Servers | Python (MCP SDK) | Official SDK, async support |
| LLM | Claude API + Local Llama | Best reasoning + privacy option |
| Vector DB | ChromaDB | Lightweight, easy embedding |
| Search | Brave Search API | Privacy-focused, good results |
| Monitoring | Prometheus + Grafana | Industry standard |
| Logging | Structured JSON | Easy parsing, searchable |

## Development Environment

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- Git

### Local Setup
```bash
git clone https://github.com/autoarr/autoarr.git
cd autoarr
docker-compose up -d  # Starts all services
npm install           # UI dependencies
pip install -r requirements.txt  # API dependencies
```

### Environment Variables
```
CLAUDE_API_KEY=sk-xxx
BRAVE_SEARCH_API_KEY=xxx
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=xxx
SONARR_URL=http://localhost:8989
SONARR_API_KEY=xxx
RADARR_URL=http://localhost:7878
RADARR_API_KEY=xxx
PLEX_URL=http://localhost:32400
PLEX_TOKEN=xxx
```

## Deployment

### Container Deployment
```yaml
version: '3.8'
services:
  autoarr:
    image: autoarr/autoarr:latest
    ports:
      - "3000:3000"
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    restart: unless-stopped
```

### SaaS Deployment (Future)
- Kubernetes cluster (GKE/EKS)
- Helm charts for deployment
- Managed database
- CDN for UI assets
- Load balancer for API

## Testing Strategy

### Unit Tests
- Each service component isolated
- Mock MCP server responses
- Mock LLM responses
- Target: 80%+ coverage

### Integration Tests
- End-to-end flows
- Real MCP server interactions (test instances)
- Database transactions
- API endpoint tests

### E2E Tests
- Playwright for UI testing
- Critical user journeys
- Mobile device testing

### Performance Tests
- Load testing with Locust
- MCP server response times
- Database query optimization
- LLM inference benchmarking

## Documentation

### Developer Docs
- Architecture overview (this document)
- API reference (OpenAPI/Swagger)
- MCP server guide
- Contribution guide

### User Docs
- Installation guide
- Configuration guide
- Troubleshooting
- FAQ

### API Documentation
- Auto-generated from FastAPI
- Interactive Swagger UI
- Example requests/responses

---

*Document Version: 1.0*  
*Last Updated: October 5, 2025*  
*Owner: AutoArr Team*
