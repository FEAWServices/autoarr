# AutoArr API Testing Guide

This guide provides curl commands for testing the FastAPI Gateway endpoints.

## Table of Contents

- [Health Endpoints](#health-endpoints)
- [MCP Proxy Endpoints](#mcp-proxy-endpoints)
- [Downloads Endpoints (SABnzbd)](#downloads-endpoints-sabnzbd)
- [Shows Endpoints (Sonarr)](#shows-endpoints-sonarr)
- [Movies Endpoints (Radarr)](#movies-endpoints-radarr)
- [Media Endpoints (Plex)](#media-endpoints-plex)
- [Settings Endpoints](#settings-endpoints)

## Prerequisites

1. Start the AutoArr API server:

```bash
cd /app
python -m uvicorn autoarr.api.main:app --host 0.0.0.0 --port 8088 --reload
```

2. Set environment variables (in `.env` file):

```bash
SABNZBD_URL=http://localhost:8080
SABNZBD_API_KEY=your_api_key_here
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_api_key_here
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_api_key_here
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_plex_token_here
```

## Health Endpoints

### Get Overall Health Status

```bash
curl -X GET http://localhost:8088/health | jq
```

Response:

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

### Get Individual Service Health

```bash
# SABnzbd health
curl -X GET http://localhost:8088/health/sabnzbd | jq

# Sonarr health
curl -X GET http://localhost:8088/health/sonarr | jq

# Radarr health
curl -X GET http://localhost:8088/health/radarr | jq

# Plex health
curl -X GET http://localhost:8088/health/plex | jq
```

### Get Circuit Breaker Status

```bash
curl -X GET http://localhost:8088/health/circuit-breaker/sabnzbd | jq
```

Response:

```json
{
  "state": "closed",
  "failure_count": 0,
  "success_count": 5,
  "threshold": 5,
  "timeout": 60.0
}
```

## MCP Proxy Endpoints

### List All Available Tools

```bash
curl -X GET http://localhost:8088/api/v1/mcp/tools | jq
```

Response:

```json
{
  "tools": {
    "sabnzbd": ["get_queue", "get_history", "retry_download", "pause_queue"],
    "sonarr": ["get_series", "search_series", "get_calendar", "get_queue"],
    "radarr": ["get_movies", "search_movies", "get_calendar", "get_queue"],
    "plex": ["get_libraries", "get_recently_added", "scan_library"]
  }
}
```

### List Tools for Specific Server

```bash
curl -X GET http://localhost:8088/api/v1/mcp/tools/sabnzbd | jq
```

### Call a Single MCP Tool

```bash
# Get SABnzbd queue
curl -X POST http://localhost:8088/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sabnzbd",
    "tool": "get_queue",
    "params": {}
  }' | jq

# Retry a download
curl -X POST http://localhost:8088/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sabnzbd",
    "tool": "retry_download",
    "params": {
      "nzo_id": "SABnzbd_nzo_abc123"
    }
  }' | jq

# Get Sonarr series
curl -X POST http://localhost:8088/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sonarr",
    "tool": "get_series",
    "params": {}
  }' | jq
```

### Call Multiple Tools in Parallel (Batch)

```bash
curl -X POST http://localhost:8088/api/v1/mcp/batch \
  -H "Content-Type: application/json" \
  -d '{
    "calls": [
      {
        "server": "sabnzbd",
        "tool": "get_queue",
        "params": {}
      },
      {
        "server": "sonarr",
        "tool": "get_series",
        "params": {}
      },
      {
        "server": "radarr",
        "tool": "get_movies",
        "params": {}
      }
    ],
    "return_partial": false
  }' | jq
```

### Get Orchestrator Statistics

```bash
curl -X GET http://localhost:8088/api/v1/mcp/stats | jq
```

## Downloads Endpoints (SABnzbd)

### Get Download Queue

```bash
curl -X GET http://localhost:8088/api/v1/downloads/queue | jq
```

### Get Download History

```bash
curl -X GET http://localhost:8088/api/v1/downloads/history?limit=10 | jq
```

### Retry Failed Download

```bash
curl -X POST http://localhost:8088/api/v1/downloads/retry \
  -H "Content-Type: application/json" \
  -d '{
    "nzo_id": "SABnzbd_nzo_abc123"
  }' | jq
```

### Pause/Resume Queue

```bash
# Pause queue
curl -X POST http://localhost:8088/api/v1/downloads/pause | jq

# Resume queue
curl -X POST http://localhost:8088/api/v1/downloads/resume | jq
```

## Shows Endpoints (Sonarr)

### List All Shows

```bash
curl -X GET http://localhost:8088/api/v1/shows | jq
```

### Search for Shows

```bash
curl -X GET "http://localhost:8088/api/v1/shows/search?query=Breaking+Bad" | jq
```

### Get Show Details

```bash
curl -X GET http://localhost:8088/api/v1/shows/1 | jq
```

### Add a Show

```bash
curl -X POST http://localhost:8088/api/v1/shows \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking Bad",
    "tvdb_id": 81189,
    "quality_profile_id": 1,
    "root_folder_path": "/tv",
    "monitored": true,
    "season_folder": true
  }' | jq
```

### Delete a Show

```bash
curl -X DELETE http://localhost:8088/api/v1/shows/1 | jq
```

## Movies Endpoints (Radarr)

### List All Movies

```bash
curl -X GET http://localhost:8088/api/v1/movies | jq
```

### Search for Movies

```bash
curl -X GET "http://localhost:8088/api/v1/movies/search?query=Inception" | jq
```

### Get Movie Details

```bash
curl -X GET http://localhost:8088/api/v1/movies/1 | jq
```

### Add a Movie

```bash
curl -X POST http://localhost:8088/api/v1/movies \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Inception",
    "tmdb_id": 27205,
    "quality_profile_id": 1,
    "root_folder_path": "/movies",
    "monitored": true
  }' | jq
```

### Delete a Movie

```bash
curl -X DELETE http://localhost:8088/api/v1/movies/1 | jq
```

## Media Endpoints (Plex)

### List All Libraries

```bash
curl -X GET http://localhost:8088/api/v1/media/libraries | jq
```

### Get Recently Added Media

```bash
curl -X GET http://localhost:8088/api/v1/media/recently-added?limit=10 | jq
```

### Scan Library

```bash
curl -X POST http://localhost:8088/api/v1/media/scan \
  -H "Content-Type: application/json" \
  -d '{
    "library_key": "1"
  }' | jq
```

### Search Media

```bash
curl -X GET "http://localhost:8088/api/v1/media/search?query=Inception" | jq
```

### Get Active Sessions

```bash
curl -X GET http://localhost:8088/api/v1/media/sessions | jq
```

## Settings Endpoints

### Get All Settings

```bash
curl -X GET http://localhost:8088/api/v1/settings | jq
```

### Get Service-Specific Settings

```bash
# SABnzbd settings
curl -X GET http://localhost:8088/api/v1/settings/sabnzbd | jq

# Sonarr settings
curl -X GET http://localhost:8088/api/v1/settings/sonarr | jq

# Radarr settings
curl -X GET http://localhost:8088/api/v1/settings/radarr | jq

# Plex settings
curl -X GET http://localhost:8088/api/v1/settings/plex | jq
```

### Update Service Settings

```bash
curl -X PUT http://localhost:8088/api/v1/settings/sabnzbd \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8080",
    "api_key": "new_api_key_here",
    "enabled": true
  }' | jq
```

### Save All Settings

```bash
curl -X POST http://localhost:8088/api/v1/settings/save \
  -H "Content-Type: application/json" \
  -d '{
    "sabnzbd": {
      "url": "http://localhost:8080",
      "api_key": "key1",
      "enabled": true
    },
    "sonarr": {
      "url": "http://localhost:8989",
      "api_key": "key2",
      "enabled": true
    }
  }' | jq
```

## Root Endpoints

### Get API Information

```bash
curl -X GET http://localhost:8088/ | jq
```

Response:

```json
{
  "name": "AutoArr API",
  "version": "1.0.0",
  "description": "Intelligent media automation orchestrator",
  "docs": "/docs",
  "admin": "/static/admin.html",
  "health": "/health"
}
```

### Ping Endpoint

```bash
curl -X GET http://localhost:8088/ping | jq
```

Response:

```json
{
  "message": "pong"
}
```

## OpenAPI Documentation

### View Interactive API Documentation

Open in browser:

- Swagger UI: http://localhost:8088/docs
- ReDoc: http://localhost:8088/redoc

### Get OpenAPI JSON Schema

```bash
curl -X GET http://localhost:8088/openapi.json | jq
```

## Testing Error Handling

### Test Connection Error

```bash
# Disable SABnzbd service first, then:
curl -X GET http://localhost:8088/health/sabnzbd | jq
```

### Test Invalid Service Name

```bash
curl -X GET http://localhost:8088/health/invalid_service | jq
```

### Test Invalid Tool Call

```bash
curl -X POST http://localhost:8088/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sabnzbd",
    "tool": "nonexistent_tool",
    "params": {}
  }' | jq
```

## Performance Testing

### Test Response Time with Headers

```bash
curl -X GET http://localhost:8088/health \
  -H "X-Request-ID: perf-test-123" \
  -v 2>&1 | grep -E "X-Process-Time|X-Request-ID"
```

### Concurrent Requests Test

```bash
# Run 10 concurrent requests
for i in {1..10}; do
  curl -X GET http://localhost:8088/health &
done
wait
```

## Security Headers Verification

### Check Security Headers

```bash
curl -I http://localhost:8088/health
```

Expected headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Tips

1. **Use jq for Pretty Printing**: All examples use `| jq` for formatted JSON output
2. **Add Request IDs**: Use `-H "X-Request-ID: your-id"` for request tracking
3. **Check Response Headers**: Use `-v` or `-I` to see response headers
4. **Save Responses**: Use `-o filename.json` to save responses to file
5. **Environment Variables**: Create a shell script with your API keys:

```bash
# api-test-env.sh
export API_BASE_URL="http://localhost:8088"
export SABNZBD_API_KEY="your_key"
export SONARR_API_KEY="your_key"
export RADARR_API_KEY="your_key"
export PLEX_TOKEN="your_token"
```

Then source it before testing:

```bash
source api-test-env.sh
curl -X GET "${API_BASE_URL}/health" | jq
```

## Troubleshooting

### Connection Refused

- Ensure the API server is running
- Check the port (default: 8088)
- Verify no firewall is blocking the port

### 503 Service Unavailable

- Check if the backend service (SABnzbd/Sonarr/Radarr/Plex) is running
- Verify API keys and URLs in `.env` file
- Check circuit breaker status: `curl http://localhost:8088/health/circuit-breaker/sabnzbd`

### 401 Unauthorized

- Verify API keys are correctly configured
- Check that services are accessible from the API server

### 504 Gateway Timeout

- Check if backend service is responding slowly
- Increase timeout values in settings
- Check service logs for issues
