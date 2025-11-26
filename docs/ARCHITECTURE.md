# AutoArr Technical Architecture

**Last Updated:** 2025-01-12
**Version:** 2.0 (Integrated Single-Container + Optional Cloud)

> **See also:** [VISION_AND_PRICING.md](./VISION_AND_PRICING.md) - Product vision and premium features

---

## Design Philosophy

AutoArr follows a **hybrid architecture** designed for:

- **Easy deployment** - Single container, minimal configuration
- **Low resource usage** - Optimized for NAS devices (4-8GB RAM)
- **Privacy-first** - Local LLM, no external dependencies required
- **Reliability** - Direct API integration, fewer failure points
- **Maintainability** - Simple codebase, easy to understand
- **Optional cloud** - Premium features via secure bridge (see VISION_AND_PRICING.md)

**Inspired by:** Sonarr, Radarr (simple, effective, self-contained)

### Product Structure

**AutoArr (Free/GPL):** Complete, self-hosted solution with local LLM
**AutoArrX (Premium):** Optional cloud intelligence with privacy-first architecture

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AutoArr Container                           │
│                     (Python + React)                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  FastAPI Backend                         │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐│  │
│  │  │         Local LLM Engine                          ││  │
│  │  │  Qwen 2.5-3B (Quantized, ~3GB RAM)              ││  │
│  │  │  - Natural language parsing                      ││  │
│  │  │  - Content classification (movie/TV)            ││  │
│  │  │  - Configuration analysis                        ││  │
│  │  └────────────────────────────────────────────────────┘│  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐│  │
│  │  │         API Client Layer                          ││  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────┐ ││  │
│  │  │  │  Radarr  │ │  Sonarr  │ │ SABnzbd │ │ Plex │ ││  │
│  │  │  │  Client  │ │  Client  │ │  Client │ │Client│ ││  │
│  │  │  └──────────┘ └──────────┘ └─────────┘ └──────┘ ││  │
│  │  └────────────────────────────────────────────────────┘│  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐│  │
│  │  │         Business Logic Services                   ││  │
│  │  │  - ConfigurationManager                           ││  │
│  │  │  - MonitoringService                              ││  │
│  │  │  - RecoveryService                                ││  │
│  │  │  - RequestHandler                                 ││  │
│  │  │  - ActivityLogger                                 ││  │
│  │  └────────────────────────────────────────────────────┘│  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐│  │
│  │  │         SQLite Database                           ││  │
│  │  │  - Configuration history                          ││  │
│  │  │  - Activity logs                                  ││  │
│  │  │  - Content requests                               ││  │
│  │  │  - Best practices                                 ││  │
│  │  └────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  React Frontend                          │  │
│  │  - Dashboard (health monitoring)                         │  │
│  │  - Chat Interface (natural language)                     │  │
│  │  - Configuration Audit                                   │  │
│  │  - Activity Feed                                         │  │
│  │  - Settings                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/JSON APIs
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
   ┌────▼─────┐  ┌─────────┐  ┌──────────┐  ┌──────┐
   │  Radarr  │  │ Sonarr  │  │ SABnzbd  │  │ Plex │
   │  :7878   │  │  :8989  │  │  :8080   │  │:32400│
   └──────────┘  └─────────┘  └──────────┘  └──────┘
```

---

## Component Details

### 1. FastAPI Backend

**Technology Stack:**

- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy (ORM)
- aiohttp (async HTTP client)
- llama-cpp-python (local LLM)

**Key Features:**

- Async/await throughout
- Type hints and Pydantic validation
- Automatic OpenAPI documentation
- WebSocket support for real-time updates
- Background task scheduling

**API Structure:**

```
/api/v1/
├── health              # Health check
├── config/             # Configuration management
│   ├── audit           # Trigger audit
│   ├── recommendations # Get recommendations
│   └── apply           # Apply changes
├── downloads/          # Download management
│   ├── queue           # Current queue
│   ├── history         # Download history
│   └── retry           # Retry failed download
├── content/            # Content requests
│   ├── request         # Natural language request
│   ├── search          # Search content
│   └── status          # Request status
├── activity/           # Activity logs
│   └── logs            # Get activity logs
└── settings/           # Application settings
```

---

### 2. Local LLM Engine

**Model: Qwen 2.5-3B (Quantized)**

```python
from llama_cpp import Llama

llm = Llama(
    model_path="/app/models/qwen2.5-3b-instruct-q4_k_m.gguf",
    n_ctx=2048,        # Context window
    n_threads=4,       # CPU threads
    n_gpu_layers=0,    # CPU only
    verbose=False
)
```

**Capabilities:**

- Natural language understanding
- Content type classification (movie vs TV)
- Title and metadata extraction
- Configuration analysis
- Reasoning and decision-making

**Performance:**

- Inference speed: 20-30 tokens/second (CPU)
- Memory usage: ~3GB RAM
- Latency: 200-500ms per query

**Quantization:** Q4_K_M (4-bit quantized)

- 75% smaller than full precision
- Minimal accuracy loss
- Optimized for CPU inference

---

### 3. API Client Layer

#### Radarr Client

```python
class RadarrClient:
    """Direct API integration with Radarr"""

    async def search_movies(self, query: str) -> List[Movie]:
        """Search for movies"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v3/movie/lookup",
                params={"term": query},
                headers={"X-Api-Key": self.api_key}
            ) as resp:
                return await resp.json()

    async def add_movie(
        self,
        tmdb_id: int,
        quality_profile_id: int,
        root_folder: str
    ) -> Movie:
        """Add movie to Radarr"""
        # Implementation
```

**Similar clients for:**

- Sonarr (TV shows)
- SABnzbd (downloads)
- Plex (library management)

**Features:**

- Async HTTP calls
- Automatic retry with exponential backoff
- Connection pooling
- Rate limiting
- Error handling

---

### 4. Business Logic Services

#### Configuration Manager

```python
class ConfigurationManager:
    """Audit and optimize application configurations"""

    async def audit_all(self) -> AuditResult:
        """Audit all connected applications"""
        results = []

        # Fetch current configurations
        radarr_config = await self.radarr.get_config()
        sonarr_config = await self.sonarr.get_config()
        sabnzbd_config = await self.sabnzbd.get_config()

        # Compare against best practices
        recommendations = await self._analyze_configs(
            radarr_config,
            sonarr_config,
            sabnzbd_config
        )

        return AuditResult(recommendations=recommendations)

    async def _analyze_configs(self, *configs) -> List[Recommendation]:
        """Use LLM to analyze configurations"""
        # LLM analysis with best practices context
```

#### Monitoring Service

```python
class MonitoringService:
    """Monitor download queue and detect failures"""

    async def poll_queue(self):
        """Poll SABnzbd queue periodically"""
        queue = await self.sabnzbd.get_queue()

        # Detect failures
        for item in queue:
            if item.status == "Failed":
                await self._handle_failure(item)

    async def _handle_failure(self, item: DownloadItem):
        """Handle failed download"""
        # Log failure
        await self.activity_log.log(
            service="sabnzbd",
            event="download_failed",
            details=item.dict()
        )

        # Trigger recovery
        await self.recovery_service.retry(item)
```

#### Recovery Service

```python
class RecoveryService:
    """Intelligent retry strategies for failed downloads"""

    async def retry(self, item: DownloadItem):
        """Retry failed download with appropriate strategy"""
        strategy = self._select_strategy(item)

        if strategy == "immediate":
            await self._immediate_retry(item)
        elif strategy == "quality_fallback":
            await self._quality_fallback(item)
        elif strategy == "exponential_backoff":
            await self._schedule_retry(item)

    def _select_strategy(self, item: DownloadItem) -> str:
        """Select retry strategy based on failure reason"""
        if "connection" in item.fail_message.lower():
            return "immediate"
        elif "par2" in item.fail_message.lower():
            return "quality_fallback"
        else:
            return "exponential_backoff"
```

#### Request Handler

```python
class RequestHandler:
    """Process natural language content requests"""

    async def process_request(self, query: str) -> ContentRequest:
        """Process natural language query"""
        # Use LLM to classify and extract metadata
        result = await self.llm.classify_content(query)

        if result.content_type == "movie":
            # Search Radarr
            movies = await self.radarr.search_movies(result.title)
            return ContentRequest(
                type="movie",
                matches=movies,
                confidence=result.confidence
            )
        elif result.content_type == "tv":
            # Search Sonarr
            shows = await self.sonarr.search_series(result.title)
            return ContentRequest(
                type="tv",
                matches=shows,
                confidence=result.confidence
            )
```

---

### 5. Database Schema (SQLite)

```sql
-- Configuration history
CREATE TABLE configuration_history (
    id INTEGER PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    config_json TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity logs
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    correlation_id VARCHAR(100),
    metadata JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_correlation (correlation_id)
);

-- Content requests
CREATE TABLE content_requests (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL,
    content_type VARCHAR(20),
    title VARCHAR(255),
    year INTEGER,
    status VARCHAR(50) NOT NULL,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Best practices
CREATE TABLE best_practices (
    id INTEGER PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    recommended_value TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    source_url VARCHAR(500),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Download failures (for tracking retry attempts)
CREATE TABLE download_failures (
    id INTEGER PRIMARY KEY,
    nzo_id VARCHAR(100) NOT NULL UNIQUE,
    filename VARCHAR(500) NOT NULL,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 6. React Frontend

**Technology Stack:**

- React 18
- TypeScript
- Tailwind CSS (mobile-first)
- Zustand (state management)
- React Query (data fetching)
- WebSocket (real-time updates)

**Key Pages:**

1. **Dashboard** - System health overview
2. **Chat** - Natural language interface
3. **Configuration Audit** - Recommendations
4. **Activity Feed** - Recent actions
5. **Settings** - Service connections

**State Management:**

```typescript
// Zustand store
interface AutoArrState {
  services: ServiceStatus[];
  activities: Activity[];
  config: Configuration;

  fetchServices: () => Promise<void>;
  fetchActivities: () => Promise<void>;
  updateConfig: (config: Configuration) => Promise<void>;
}

const useAutoArrStore = create<AutoArrState>((set) => ({
  // Implementation
}));
```

---

## Data Flow Examples

### Example 1: Natural Language Content Request

```
User: "Add the new Dune movie in 4K"
  │
  ├─> Frontend sends: POST /api/v1/content/request
  │   { "query": "Add the new Dune movie in 4K" }
  │
  ├─> RequestHandler receives query
  │   │
  │   ├─> LLM classifies content
  │   │   Input: "Add the new Dune movie in 4K"
  │   │   Output: { type: "movie", title: "Dune", quality: "4K" }
  │   │
  │   ├─> RadarrClient searches
  │   │   GET /api/v3/movie/lookup?term=Dune
  │   │   Returns: [{ tmdbId: 438631, title: "Dune" (2021) }]
  │   │
  │   └─> Return matches to user for confirmation
  │
  ├─> User confirms: "Yes, add it"
  │
  ├─> RadarrClient adds movie
  │   POST /api/v3/movie
  │   { tmdbId: 438631, qualityProfileId: 6, ... }
  │
  ├─> ActivityLogger logs action
  │   INSERT INTO activity_logs ...
  │
  └─> Frontend shows success message
```

### Example 2: Automatic Download Recovery

```
MonitoringService (background task, runs every 60s)
  │
  ├─> Poll SABnzbd queue
  │   GET /api?mode=queue
  │   Response: [{ nzo_id: "abc123", status: "Failed", ... }]
  │
  ├─> Detect failure
  │   Filter: status == "Failed"
  │   Found: "Show.S01E01.mkv" failed (PAR2 error)
  │
  ├─> ActivityLogger logs failure
  │   INSERT INTO activity_logs
  │   (service='sabnzbd', event='download_failed', ...)
  │
  ├─> RecoveryService handles
  │   │
  │   ├─> Determine strategy
  │   │   Reason: "PAR2 repair failed"
  │   │   Strategy: "quality_fallback"
  │   │
  │   ├─> Parse filename
  │   │   Extract: series="Show", season=1, episode=1
  │   │
  │   ├─> SonarrClient searches lower quality
  │   │   POST /api/v3/command
  │   │   { name: "EpisodeSearch", episodeIds: [123], ... }
  │   │
  │   └─> ActivityLogger logs retry
  │       INSERT INTO activity_logs
  │       (event='recovery_attempted', ...)
  │
  └─> WebSocket notifies frontend
      ws.send({ type: "recovery_started", nzo_id: "abc123" })
```

### Example 3: Configuration Audit

```
User clicks: "Run Audit"
  │
  ├─> Frontend: POST /api/v1/config/audit
  │
  ├─> ConfigurationManager.audit_all()
  │   │
  │   ├─> Fetch current configs (parallel)
  │   │   ├─> RadarrClient.get_config()
  │   │   ├─> SonarrClient.get_config()
  │   │   └─> SABnzbdClient.get_config()
  │   │
  │   ├─> Load best practices from DB
  │   │   SELECT * FROM best_practices
  │   │
  │   ├─> LLM analyzes configs
  │   │   Prompt: "Compare these configs against best practices..."
  │   │   Response: [{
  │   │     setting: "radarr.quality_profile",
  │   │     current: "HD-1080p",
  │   │     recommended: "Ultra-HD",
  │   │     priority: "medium",
  │   │     reasoning: "..."
  │   │   }]
  │   │
  │   └─> Return recommendations
  │
  └─> Frontend displays audit results
```

---

## Deployment Architecture

### Docker Compose (Recommended)

```yaml
version: "3.8"

services:
  autoarr:
    build: .
    container_name: autoarr
    ports:
      - "8080:8080"
    environment:
      # Service connections
      - RADARR_URL=http://radarr:7878
      - RADARR_API_KEY=${RADARR_API_KEY}
      - SONARR_URL=http://sonarr:8989
      - SONARR_API_KEY=${SONARR_API_KEY}
      - SABNZBD_URL=http://sabnzbd:8080
      - SABNZBD_API_KEY=${SABNZBD_API_KEY}
      - PLEX_URL=http://plex:32400
      - PLEX_TOKEN=${PLEX_TOKEN}

      # Application settings
      - LOG_LEVEL=INFO
      - DATABASE_PATH=/data/autoarr.db
      - MODEL_PATH=/models/qwen2.5-3b-instruct-q4_k_m.gguf
    volumes:
      - ./data:/data # Database persistence
      - ./models:/models # LLM model (cached)
    restart: unless-stopped
    mem_limit: 6g # 2GB app + 3GB LLM + 1GB buffer
    cpus: 4.0
    networks:
      - media-network

networks:
  media-network:
    external: true # Shared with Radarr, Sonarr, etc.
```

### Dockerfile (Multi-stage)

```dockerfile
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY autoarr/ui/package*.json ./
RUN npm ci --only=production
COPY autoarr/ui ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download quantized LLM model
RUN mkdir -p /models && \
    curl -L -o /models/qwen2.5-3b-instruct-q4_k_m.gguf \
    https://huggingface.co/Qwen/Qwen2.5-3B-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf

# Copy application
COPY autoarr /app/autoarr
COPY --from=frontend-build /app/dist /app/autoarr/ui/dist

# Create non-root user
RUN useradd -m -u 1000 autoarr && \
    chown -R autoarr:autoarr /app /models
USER autoarr

WORKDIR /app
EXPOSE 8080

CMD ["uvicorn", "autoarr.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## Resource Usage

### Memory Profile

```
Component              Memory Usage
────────────────────────────────────
Python Runtime         ~200 MB
FastAPI Application    ~300 MB
LLM (Qwen 2.5-3B Q4)  ~3000 MB
SQLite Database        ~50 MB
Frontend Assets        ~100 MB
────────────────────────────────────
Total                  ~3650 MB
Peak (during LLM)      ~4200 MB
```

**Recommended:** 6-8GB RAM (leaves headroom for OS and other apps)

### CPU Usage

- **Idle:** 1-2% (background monitoring)
- **LLM Inference:** 80-100% of allocated cores (brief spikes)
- **API Calls:** 5-10% (network I/O bound)

### Disk Usage

```
/app/autoarr          ~500 MB (application code)
/models               ~2.5 GB (LLM model)
/data/autoarr.db      ~10-100 MB (grows with history)
/data/logs            ~50-500 MB (rotated daily)
────────────────────────────────────
Total                 ~3-4 GB
```

---

## Security Architecture

### Threat Model

**In Scope:**

- API authentication
- Service credential storage
- Input validation
- CORS protection
- Rate limiting

**Out of Scope:**

- Network security (handled by firewall/proxy)
- TLS/HTTPS (handled by reverse proxy)
- Physical security

### Security Measures

1. **API Authentication**
   - Optional API key for external access
   - Session-based auth for web UI
   - No default credentials

2. **Credential Storage**
   - Service API keys encrypted at rest
   - Uses system keyring where available
   - Environment variables as fallback

3. **Input Validation**
   - Pydantic models for all API inputs
   - Sanitization of user queries before LLM
   - SQL injection protection (ORM)

4. **CORS Configuration**
   - Whitelist of allowed origins
   - Credentials allowed only for same-origin
   - Configurable in settings

5. **Rate Limiting**
   - Per-IP rate limits on API endpoints
   - Prevents abuse of LLM inference
   - Configurable thresholds

---

## Performance Optimization

### LLM Optimization

```python
# Cache common queries
@lru_cache(maxsize=100)
async def classify_content(query: str) -> Classification:
    # Cache reduces LLM calls for repeated queries
    pass

# Batch processing
async def process_batch(queries: List[str]):
    # Process multiple queries in one LLM call
    pass
```

### Database Optimization

```sql
-- Indexes for common queries
CREATE INDEX idx_activity_timestamp ON activity_logs(timestamp DESC);
CREATE INDEX idx_activity_correlation ON activity_logs(correlation_id);
CREATE INDEX idx_requests_status ON content_requests(status, created_at);

-- Query optimization
PRAGMA journal_mode=WAL;  -- Better concurrency
PRAGMA synchronous=NORMAL; -- Balance safety/speed
PRAGMA cache_size=-64000;  -- 64MB cache
```

### API Optimization

```python
# Connection pooling
connector = aiohttp.TCPConnector(
    limit=100,           # Max connections
    limit_per_host=10,   # Per host
    ttl_dns_cache=300    # DNS cache
)

# Request caching
@cache(expire=300)  # 5 minute cache
async def get_radarr_movies():
    # Expensive API call cached
    pass
```

---

## Monitoring & Observability

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": await check_database(),
            "llm": await check_llm(),
            "radarr": await radarr.health_check(),
            "sonarr": await sonarr.health_check(),
            "sabnzbd": await sabnzbd.health_check(),
            "plex": await plex.health_check()
        }
    }
```

### Logging

```python
import logging
import structlog

# Structured logging
logger = structlog.get_logger()

logger.info(
    "download_failed",
    nzo_id="abc123",
    filename="Show.S01E01.mkv",
    reason="PAR2 repair failed",
    retry_count=1
)
```

### Metrics

```python
from prometheus_client import Counter, Histogram

# Track key metrics
requests_total = Counter('autoarr_requests_total', 'Total requests')
request_duration = Histogram('autoarr_request_duration_seconds', 'Request duration')
llm_inference_duration = Histogram('autoarr_llm_inference_seconds', 'LLM inference time')
```

---

## Development Environment

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- 8GB+ RAM

### Setup

```bash
# Clone repository
git clone https://github.com/autoarr/autoarr.git
cd autoarr

# Install Python dependencies
poetry install

# Install frontend dependencies
cd autoarr/ui
pnpm install

# Start development services (Radarr, Sonarr, etc.)
docker-compose -f docker/docker-compose.dev.yml up -d

# Download LLM model
mkdir -p models
curl -L -o models/qwen2.5-3b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-3B-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf

# Start backend
poetry run uvicorn autoarr.main:app --reload

# Start frontend (separate terminal)
cd autoarr/ui
pnpm dev
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=autoarr --cov-report=html

# Run specific tests
poetry run pytest tests/unit/test_llm.py -v

# Frontend tests
cd autoarr/ui
pnpm test
```

---

## Technology Rationale

### Why Single Container?

**Pros:**

- ✅ Easy deployment (one command)
- ✅ Lower resource usage (shared memory)
- ✅ Simpler networking (no inter-container communication)
- ✅ Easier to debug (one log stream)
- ✅ Better for NAS devices (limited Docker support)

**Cons:**

- ❌ Less scalable (can't scale components independently)
- ❌ Harder to update one component

**Decision:** Single container for v1.0, microservices later if needed

### Why Local LLM vs API?

**Local (Qwen 2.5-3B):**

- ✅ Privacy (nothing leaves your server)
- ✅ No API costs
- ✅ No rate limits
- ✅ Works offline
- ❌ Slower than cloud APIs
- ❌ Limited capabilities

**Cloud API (Claude/GPT-4):**

- ✅ More powerful
- ✅ Faster inference
- ❌ Privacy concerns
- ❌ Recurring costs ($20-50/month)
- ❌ Rate limits
- ❌ Requires internet

**Decision:** Local LLM for v1.0, optional cloud API later

### Why Direct API vs MCP Protocol?

**Direct API Integration:**

- ✅ Simpler code
- ✅ Fewer dependencies
- ✅ More reliable (fewer failure points)
- ✅ Better performance (no protocol overhead)
- ❌ Tightly coupled to specific services

**MCP Protocol:**

- ✅ Standardized interface
- ✅ Easier to add new services
- ❌ Additional complexity
- ❌ Overhead from protocol layer
- ❌ Overkill for 4 services

**Decision:** Direct API for v1.0, MCP if we add 10+ services

---

## Future Enhancements (Post-v1.0)

### AutoArr Core (Free) Features

1. **Plugin System**
   - Custom integrations
   - Community plugins
   - JavaScript API

2. **Larger LLM Models**
   - Optional GPU support
   - Local model switching
   - Fallback options

### AutoArrX Premium Features

See [VISION_AND_PRICING.md](./VISION_AND_PRICING.md) for complete premium tier breakdown:

1. **Shield ($4.99/mo)** - Smart notifications & community intelligence
2. **Vault ($9.99/mo)** - Advanced automation & predictive analytics
3. **Phantom ($14.99/mo)** - Multi-instance & zero-knowledge features
4. **Teams ($24.99/mo)** - Family/community management

All premium features maintain **privacy-first architecture** with client-side encryption.

---

## Summary

AutoArr uses a **hybrid architecture** optimized for flexibility:

### Free/GPL (AutoArr)

✅ **Single container** - Easy deployment
✅ **Local LLM** - Privacy-first, no cloud required
✅ **Direct API integration** - Reliable and fast
✅ **Minimal resources** - NAS-friendly (4-8GB RAM)
✅ **100% open source** - GPL-3.0, community-driven
✅ **Complete features** - No limitations

### Premium/Cloud (AutoArrX)

✅ **Secure bridge** - Outbound WebSocket only
✅ **Client-side encryption** - We never see your library
✅ **Enhanced LLM** - Claude/GPT-4 for complex tasks
✅ **Community intelligence** - Anonymous pattern matching
✅ **Predictive features** - Prevent problems before they happen
✅ **Optional** - Core works perfectly without it

**Perfect for home media servers running Sonarr, Radarr, SABnzbd, and Plex.**

---

**Related Documentation:**

- [VISION_AND_PRICING.md](./VISION_AND_PRICING.md) - Product vision & pricing
- [BUILD-PLAN.md](./BUILD-PLAN.md) - Development roadmap
- [CONTRIBUTING.md](./CONTRIBUTING.md) - How to contribute
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment
- [LLM_PROVIDER_MIGRATION_GUIDE.md](./LLM_PROVIDER_MIGRATION_GUIDE.md) - LLM implementation
