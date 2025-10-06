# AutoArr FastAPI Gateway

The FastAPI Gateway is the REST API layer that exposes AutoArr's functionality to users. It sits on top of the MCP Orchestrator and provides HTTP endpoints for all operations.

## Features

- **Health Checks**: Monitor overall system health and individual service health
- **MCP Proxy**: Direct access to MCP tools across all services
- **Service-Specific Endpoints**: Dedicated endpoints for Downloads, Shows, Movies, and Media
- **CORS Support**: Configured for web UI integration
- **Error Handling**: Comprehensive error handling middleware
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`

## Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure your services:

```bash
# SABnzbd Configuration
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=your_sabnzbd_api_key_here

# Sonarr Configuration
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_sonarr_api_key_here

# Radarr Configuration
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_radarr_api_key_here

# Plex Configuration
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_plex_token_here
```

### 3. Start the Server

```bash
# Using the startup script
python scripts/start_api.py

# Or using uvicorn directly
uvicorn api.main:app --reload

# Or using the main module
python -m api.main
```

### 4. Access API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8088/docs
- **ReDoc**: http://localhost:8088/redoc
- **OpenAPI JSON**: http://localhost:8088/openapi.json

## API Endpoints

### Health Checks

- `GET /health` - Overall system health
- `GET /health/{service}` - Individual service health (sabnzbd, sonarr, radarr, plex)
- `GET /health/circuit-breaker/{service}` - Circuit breaker status

### MCP Proxy

- `POST /api/v1/mcp/call` - Call a single MCP tool
- `POST /api/v1/mcp/batch` - Call multiple tools in parallel
- `GET /api/v1/mcp/tools` - List all available tools
- `GET /api/v1/mcp/tools/{server}` - List tools for specific server
- `GET /api/v1/mcp/stats` - Get orchestrator statistics

### Downloads (SABnzbd)

- `GET /api/v1/downloads/queue` - Get download queue
- `GET /api/v1/downloads/history` - Get download history
- `POST /api/v1/downloads/retry/{nzo_id}` - Retry a failed download
- `POST /api/v1/downloads/pause` - Pause download queue
- `POST /api/v1/downloads/resume` - Resume download queue
- `DELETE /api/v1/downloads/{nzo_id}` - Delete a download
- `GET /api/v1/downloads/status` - Get SABnzbd status

### Shows (Sonarr)

- `GET /api/v1/shows/` - List all TV shows
- `GET /api/v1/shows/{series_id}` - Get specific show
- `POST /api/v1/shows/` - Add a new show
- `DELETE /api/v1/shows/{series_id}` - Delete a show
- `GET /api/v1/shows/search/{query}` - Search for shows
- `GET /api/v1/shows/calendar/upcoming` - Get upcoming episodes
- `GET /api/v1/shows/queue/active` - Get download queue
- `POST /api/v1/shows/command/series-search` - Trigger series search
- `POST /api/v1/shows/command/episode-search` - Trigger episode search

### Movies (Radarr)

- `GET /api/v1/movies/` - List all movies
- `GET /api/v1/movies/{movie_id}` - Get specific movie
- `POST /api/v1/movies/` - Add a new movie
- `DELETE /api/v1/movies/{movie_id}` - Delete a movie
- `GET /api/v1/movies/search/{query}` - Search for movies
- `GET /api/v1/movies/calendar/upcoming` - Get upcoming movies
- `GET /api/v1/movies/queue/active` - Get download queue
- `POST /api/v1/movies/command/movie-search` - Trigger movie search
- `POST /api/v1/movies/command/refresh` - Refresh movie metadata
- `GET /api/v1/movies/missing` - Get missing movies

### Media (Plex)

- `GET /api/v1/media/libraries` - List all libraries
- `GET /api/v1/media/libraries/{library_key}` - Get specific library
- `GET /api/v1/media/recently-added` - Get recently added media
- `POST /api/v1/media/scan` - Scan a library
- `POST /api/v1/media/refresh/{rating_key}` - Refresh metadata
- `GET /api/v1/media/search` - Search for media
- `GET /api/v1/media/on-deck` - Get on deck items
- `GET /api/v1/media/sessions` - Get active playback sessions
- `GET /api/v1/media/server/status` - Get server status
- `POST /api/v1/media/optimize/{rating_key}` - Optimize media item

## Example Usage

### Call a Tool

```bash
curl -X POST "http://localhost:8088/api/v1/mcp/call" \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sabnzbd",
    "tool": "get_queue",
    "params": {}
  }'
```

### Check Health

```bash
curl "http://localhost:8088/health"
```

### Add a TV Show

```bash
curl -X POST "http://localhost:8088/api/v1/shows/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking Bad",
    "tvdb_id": 81189,
    "quality_profile_id": 1,
    "root_folder_path": "/tv",
    "monitored": true,
    "season_folder": true
  }'
```

## Running Tests

### Run all API tests

```bash
pytest tests/unit/api/ -v
```

### Run specific test file

```bash
pytest tests/unit/api/test_health_endpoints.py -v
```

### Run with coverage

```bash
pytest tests/unit/api/ --cov=api --cov-report=html
```

## Architecture

### Request Flow

```
Client Request
    ↓
FastAPI Router
    ↓
Dependency Injection (get_orchestrator)
    ↓
MCP Orchestrator
    ↓
MCP Client (SABnzbd/Sonarr/Radarr/Plex)
    ↓
Service Response
    ↓
Pydantic Model Validation
    ↓
JSON Response
```

### Error Handling

The API uses custom middleware to handle errors:

1. **MCPConnectionError** → 503 Service Unavailable
2. **MCPTimeoutError** → 504 Gateway Timeout
3. **CircuitBreakerOpenError** → 503 Service Temporarily Unavailable
4. **MCPToolError** → 400 Bad Request
5. **ValueError** → 400 Invalid Request
6. **Other Exceptions** → 500 Internal Server Error

### Middleware Stack

1. **CORS Middleware** - Handles cross-origin requests
2. **Error Handler Middleware** - Catches and formats errors
3. **Request Logging Middleware** - Logs all requests/responses
4. **Security Headers Middleware** - Adds security headers

## Configuration

All configuration is managed through environment variables and the `Settings` class:

```python
from api.config import get_settings

settings = get_settings()
print(settings.sabnzbd_url)
```

### Available Settings

- **Server**: `host`, `port`, `reload`, `workers`
- **Application**: `app_name`, `app_version`, `app_env`, `log_level`
- **Security**: `secret_key`, `cors_origins`
- **Services**: URLs and API keys for SABnzbd, Sonarr, Radarr, Plex
- **Orchestrator**: Timeouts, retries, circuit breaker settings

## Development

### Adding a New Endpoint

1. Create router in `api/routers/`
2. Define Pydantic models in `api/models.py`
3. Add router to `api/main.py`
4. Write tests in `tests/unit/api/`

### Adding a New Service

1. Update `api/config.py` with service settings
2. Update `api/dependencies.py` to create server config
3. Create router in `api/routers/{service}.py`
4. Add router to `api/main.py`

## Production Deployment

### Using Gunicorn with Uvicorn Workers

```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install poetry && poetry install --no-dev

CMD ["python", "scripts/start_api.py"]
```

### Environment Variables for Production

- Set `APP_ENV=production`
- Set `LOG_LEVEL=WARNING` or `ERROR`
- Set `RELOAD=false`
- Set `WORKERS=4` (or number of CPU cores)
- Configure proper `CORS_ORIGINS`
- Use strong `SECRET_KEY`

## Monitoring

### Health Check

The `/health` endpoint provides comprehensive health information:

```json
{
  "status": "healthy",
  "services": {
    "sabnzbd": {
      "healthy": true,
      "latency_ms": 45.2,
      "error": null,
      "last_check": "2025-01-15T10:30:00Z",
      "circuit_breaker_state": "closed"
    }
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Metrics

Access orchestrator statistics at `/api/v1/mcp/stats`:

```json
{
  "total_calls": 150,
  "total_health_checks": 45,
  "calls_per_server": {
    "sabnzbd": 50,
    "sonarr": 60,
    "radarr": 40
  }
}
```

## Troubleshooting

### Service Not Connected

If you get "Service not connected" errors:

1. Check service URLs in `.env`
2. Verify API keys are correct
3. Ensure services are running
4. Check network connectivity

### Circuit Breaker Open

If circuit breaker is open:

1. Check service health: `GET /health/{service}`
2. View circuit breaker state: `GET /health/circuit-breaker/{service}`
3. Wait for timeout period (default 60s)
4. Service will auto-recover when healthy

### Timeout Errors

If you get timeout errors:

1. Increase `DEFAULT_TOOL_TIMEOUT` in settings
2. Check service response times
3. Verify network latency
4. Consider increasing circuit breaker timeout

## License

MIT License - See LICENSE file for details
