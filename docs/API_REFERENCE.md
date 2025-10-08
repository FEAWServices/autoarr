# AutoArr API Reference

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health Checks](#health-checks)
  - [MCP Proxy](#mcp-proxy)
  - [Configuration](#configuration)
  - [Downloads (SABnzbd)](#downloads-sabnzbd)
  - [TV Shows (Sonarr)](#tv-shows-sonarr)
  - [Movies (Radarr)](#movies-radarr)
  - [Media (Plex)](#media-plex)
  - [Settings](#settings)
- [Data Models](#data-models)
- [WebSocket API](#websocket-api)
- [Code Examples](#code-examples)

## Overview

The AutoArr API is a RESTful API built with FastAPI that provides comprehensive access to all AutoArr functionality. The API follows REST principles and returns JSON responses.

### Key Features

- **OpenAPI/Swagger Documentation**: Interactive API docs at `/docs`
- **Async Operations**: Built on async Python for high performance
- **Type Safety**: Fully typed with Pydantic models
- **Circuit Breaker**: Automatic failure handling and recovery
- **Real-time Updates**: WebSocket support for live data

### API Version

Current API version: **v1**

All endpoints are prefixed with `/api/v1` unless otherwise noted.

## Authentication

### JWT Bearer Token (Future)

Authentication will use JWT Bearer tokens in production.

```http
GET /api/v1/config/audit HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: application/json
```

### API Key (Current Development)

For development, API keys are configured via environment variables.

```bash
# Configuration in .env
SABNZBD_API_KEY=your_key_here
SONARR_API_KEY=your_key_here
RADARR_API_KEY=your_key_here
PLEX_TOKEN=your_token_here
```

## Base URL

### Local Development

```
http://localhost:8000
```

### Docker Deployment

```
http://your-host:8000
```

### Production (Future SaaS)

```
https://api.autoarr.io
```

## Response Format

### Success Response

```json
{
  "data": {
    // Response data
  },
  "metadata": {
    "timestamp": "2025-01-15T10:30:00Z",
    "version": "1.0.0"
  }
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-01-15T10:30:00Z",
  "path": "/api/v1/config/audit"
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning               | Description                      |
| ---- | --------------------- | -------------------------------- |
| 200  | OK                    | Successful request               |
| 201  | Created               | Resource created                 |
| 204  | No Content            | Successful with no response body |
| 400  | Bad Request           | Invalid request parameters       |
| 401  | Unauthorized          | Authentication required          |
| 403  | Forbidden             | Insufficient permissions         |
| 404  | Not Found             | Resource not found               |
| 429  | Too Many Requests     | Rate limit exceeded              |
| 500  | Internal Server Error | Server error                     |
| 503  | Service Unavailable   | External service down            |

### Error Response Schema

```json
{
  "detail": "string",
  "status_code": 400,
  "timestamp": "2025-01-15T10:30:00Z",
  "path": "/api/v1/endpoint",
  "request_id": "abc123",
  "errors": [
    {
      "field": "services",
      "message": "At least one service must be specified"
    }
  ]
}
```

## Rate Limiting

Rate limits are applied per endpoint to prevent abuse and ensure fair usage.

| Endpoint                  | Limit         | Window   |
| ------------------------- | ------------- | -------- |
| `/config/audit`           | 10 requests   | 1 hour   |
| `/config/apply`           | 20 requests   | 1 hour   |
| `/config/recommendations` | 50 requests   | 1 hour   |
| `/mcp/call`               | 100 requests  | 1 minute |
| `/health`                 | 1000 requests | 1 minute |
| `/api/v1/*` (default)     | 100 requests  | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Endpoints

### Root Endpoints

#### GET /

Get API information and available endpoints.

**Response**:

```json
{
  "name": "AutoArr API",
  "version": "1.0.0",
  "description": "Intelligent orchestration for media automation",
  "docs": "/docs",
  "admin": "/static/admin.html",
  "health": "/health"
}
```

#### GET /ping

Simple ping endpoint for basic health checks.

**Response**:

```json
{
  "message": "pong"
}
```

### Health Checks

#### GET /health

Overall system health check.

**Response 200**:

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
    },
    "sonarr": {
      "healthy": true,
      "latency_ms": 52.1,
      "error": null,
      "last_check": "2025-01-15T10:30:00Z",
      "circuit_breaker_state": "closed"
    }
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Status Values**:

- `healthy`: All services operational
- `degraded`: Some services down
- `unhealthy`: All services down

#### GET /health/{service}

Individual service health check.

**Parameters**:

- `service` (path): Service name (sabnzbd, sonarr, radarr, plex)

**Response 200**:

```json
{
  "healthy": true,
  "latency_ms": 45.2,
  "error": null,
  "last_check": "2025-01-15T10:30:00Z",
  "circuit_breaker_state": "closed"
}
```

**Errors**:

- `400`: Invalid service name
- `503`: Service not connected

#### GET /health/circuit-breaker/{service}

Get circuit breaker status for a service.

**Response 200**:

```json
{
  "state": "closed",
  "failure_count": 0,
  "success_count": 10,
  "threshold": 5,
  "timeout": 60.0,
  "last_failure": null,
  "half_open_attempts": 0
}
```

**Circuit Breaker States**:

- `closed`: Normal operation
- `open`: Too many failures, blocking requests
- `half_open`: Testing if service recovered

### MCP Proxy

The MCP proxy endpoints allow direct interaction with MCP tools.

#### POST /api/v1/mcp/call

Call a single MCP tool.

**Request Body**:

```json
{
  "server": "sabnzbd",
  "tool": "get_queue",
  "params": {},
  "timeout": 30.0
}
```

**Response 200**:

```json
{
  "success": true,
  "data": {
    "queue": [
      {
        "nzo_id": "SABnzbd_nzo_abc123",
        "filename": "Movie.2024.1080p.mkv",
        "status": "Downloading",
        "percentage": 45
      }
    ]
  },
  "error": null,
  "metadata": {
    "server": "sabnzbd",
    "tool": "get_queue",
    "duration": 0.123
  }
}
```

#### POST /api/v1/mcp/batch

Call multiple MCP tools in parallel.

**Request Body**:

```json
{
  "calls": [
    {
      "server": "sabnzbd",
      "tool": "get_queue",
      "params": {}
    },
    {
      "server": "sonarr",
      "tool": "get_series",
      "params": { "page": 1, "pageSize": 10 }
    }
  ],
  "return_partial": false
}
```

**Response 200**:

```json
[
  {
    "success": true,
    "data": {"queue": [...]},
    "error": null
  },
  {
    "success": true,
    "data": {"series": [...]},
    "error": null
  }
]
```

**Parameters**:

- `return_partial` (boolean): Return partial results even if some calls fail

#### GET /api/v1/mcp/tools

List all available MCP tools grouped by server.

**Response 200**:

```json
{
  "tools": {
    "sabnzbd": [
      "get_queue",
      "get_history",
      "retry_download",
      "pause_queue",
      "resume_queue",
      "get_config"
    ],
    "sonarr": [
      "get_series",
      "search_series",
      "add_series",
      "get_calendar",
      "get_queue",
      "get_wanted"
    ],
    "radarr": [
      "get_movies",
      "search_movies",
      "add_movie",
      "get_calendar",
      "get_queue",
      "get_wanted"
    ],
    "plex": [
      "get_libraries",
      "get_recently_added",
      "scan_library",
      "get_sessions"
    ]
  }
}
```

#### GET /api/v1/mcp/tools/{server}

List tools for a specific server.

**Response 200**:

```json
{
  "server": "sabnzbd",
  "tools": [
    "get_queue",
    "get_history",
    "retry_download",
    "pause_queue",
    "resume_queue"
  ]
}
```

#### GET /api/v1/mcp/stats

Get orchestrator statistics.

**Response 200**:

```json
{
  "total_calls": 1534,
  "total_health_checks": 458,
  "calls_per_server": {
    "sabnzbd": 523,
    "sonarr": 612,
    "radarr": 399,
    "plex": 0
  },
  "average_latency_ms": {
    "sabnzbd": 45.2,
    "sonarr": 52.1,
    "radarr": 48.3
  },
  "circuit_breaker_trips": {
    "sabnzbd": 0,
    "sonarr": 1,
    "radarr": 0
  }
}
```

### Configuration

Configuration audit endpoints for analyzing and optimizing settings.

#### POST /api/v1/config/audit

Trigger configuration audit for one or more services.

**Request Body**:

```json
{
  "services": ["sabnzbd", "sonarr", "radarr"],
  "include_web_search": true
}
```

**Response 200**:

```json
{
  "audit_id": "audit_123",
  "timestamp": "2025-01-15T10:30:00Z",
  "services_audited": ["sabnzbd", "sonarr", "radarr"],
  "total_recommendations": 12,
  "by_priority": {
    "high": 3,
    "medium": 5,
    "low": 4
  },
  "by_category": {
    "performance": 4,
    "security": 2,
    "best_practices": 6
  },
  "recommendations": [
    {
      "id": 1,
      "service": "sabnzbd",
      "title": "Enable Direct Unpack",
      "description": "Direct Unpack improves extraction performance",
      "priority": "high",
      "category": "performance",
      "current_value": false,
      "recommended_value": true,
      "impact": "30% faster extraction times",
      "references": [
        "https://sabnzbd.org/wiki/configuration/3.7/general#direct_unpack"
      ]
    }
  ]
}
```

**Rate Limit**: 10 requests per hour

#### GET /api/v1/config/recommendations

List all recommendations with filtering and pagination.

**Query Parameters**:

- `service` (string, optional): Filter by service
- `priority` (string, optional): Filter by priority (high, medium, low)
- `category` (string, optional): Filter by category
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 10, max: 100): Items per page

**Response 200**:

```json
{
  "recommendations": [
    {
      "id": 1,
      "service": "sabnzbd",
      "title": "Enable Direct Unpack",
      "description": "Direct Unpack improves extraction performance",
      "priority": "high",
      "category": "performance"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "page_size": 10,
    "total_pages": 3
  }
}
```

#### GET /api/v1/config/recommendations/{id}

Get detailed information about a specific recommendation.

**Response 200**:

```json
{
  "id": 1,
  "service": "sabnzbd",
  "title": "Enable Direct Unpack",
  "description": "Direct Unpack extracts files while still downloading...",
  "priority": "high",
  "category": "performance",
  "current_value": false,
  "recommended_value": true,
  "impact": "30% faster extraction times",
  "explanation": "When enabled, SABnzbd will begin extracting...",
  "references": [
    "https://sabnzbd.org/wiki/configuration/3.7/general#direct_unpack",
    "https://www.reddit.com/r/usenet/comments/..."
  ],
  "implementation_steps": [
    "Navigate to SABnzbd Config > General",
    "Find 'Direct Unpack' setting",
    "Enable the checkbox",
    "Save changes"
  ],
  "risks": "None - This is a performance optimization only",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Errors**:

- `404`: Recommendation not found

#### POST /api/v1/config/apply

Apply recommended configuration changes.

**Request Body**:

```json
{
  "recommendation_ids": [1, 2, 3],
  "dry_run": false
}
```

**Response 200**:

```json
{
  "results": [
    {
      "recommendation_id": 1,
      "service": "sabnzbd",
      "success": true,
      "message": "Setting applied successfully",
      "changes": {
        "direct_unpack": {
          "old": false,
          "new": true
        }
      }
    },
    {
      "recommendation_id": 2,
      "service": "sonarr",
      "success": false,
      "message": "Service unavailable",
      "error": "Connection timeout"
    }
  ],
  "summary": {
    "total": 3,
    "successful": 2,
    "failed": 1
  },
  "dry_run": false,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Parameters**:

- `dry_run` (boolean): If true, validate changes without applying

**Rate Limit**: 20 requests per hour

#### GET /api/v1/config/audit/history

View audit history with pagination.

**Query Parameters**:

- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 10, max: 100): Items per page

**Response 200**:

```json
{
  "audits": [
    {
      "id": "audit_123",
      "timestamp": "2025-01-15T10:30:00Z",
      "services": ["sabnzbd", "sonarr", "radarr"],
      "total_recommendations": 12,
      "applied_count": 5
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 10,
    "total_pages": 5
  }
}
```

### Downloads (SABnzbd)

Endpoints for managing downloads via SABnzbd.

#### GET /api/v1/downloads/queue

Get current download queue.

**Response 200**:

```json
{
  "queue": [
    {
      "nzo_id": "SABnzbd_nzo_abc123",
      "filename": "Movie.2024.1080p.mkv",
      "status": "Downloading",
      "percentage": 45.3,
      "size": "4.2 GB",
      "size_left": "2.3 GB",
      "time_left": "00:15:30",
      "category": "movies",
      "priority": "Normal"
    }
  ],
  "speed": "25.4 MB/s",
  "size_left_total": "8.5 GB",
  "time_left_total": "00:45:00"
}
```

#### GET /api/v1/downloads/history

Get download history.

**Query Parameters**:

- `limit` (integer, default: 50): Number of items
- `start` (integer, default: 0): Starting offset

**Response 200**:

```json
{
  "history": [
    {
      "nzo_id": "SABnzbd_nzo_xyz789",
      "name": "Show.S01E01.1080p.mkv",
      "status": "Completed",
      "fail_message": "",
      "category": "tv",
      "size": "2.1 GB",
      "download_time": "00:08:15",
      "completed_at": "2025-01-15T09:22:00Z"
    }
  ],
  "total": 150
}
```

#### POST /api/v1/downloads/retry/{nzo_id}

Retry a failed download.

**Response 200**:

```json
{
  "success": true,
  "message": "Download retry initiated",
  "nzo_id": "SABnzbd_nzo_abc123"
}
```

### TV Shows (Sonarr)

Endpoints for managing TV shows via Sonarr.

#### GET /api/v1/shows

List all TV shows.

**Query Parameters**:

- `page` (integer): Page number
- `page_size` (integer): Items per page

**Response 200**:

```json
{
  "series": [
    {
      "id": 1,
      "title": "Breaking Bad",
      "year": 2008,
      "status": "continuing",
      "seasons": 5,
      "episodes": 62,
      "monitored": true,
      "quality_profile": "HD-1080p"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "page_size": 10
  }
}
```

#### POST /api/v1/shows/search

Search for TV shows.

**Request Body**:

```json
{
  "term": "Breaking Bad"
}
```

**Response 200**:

```json
{
  "results": [
    {
      "tvdbId": 81189,
      "title": "Breaking Bad",
      "year": 2008,
      "overview": "A high school chemistry teacher...",
      "network": "AMC",
      "status": "ended",
      "seasons": 5
    }
  ]
}
```

#### POST /api/v1/shows/add

Add a TV show to Sonarr.

**Request Body**:

```json
{
  "tvdbId": 81189,
  "title": "Breaking Bad",
  "quality_profile": "HD-1080p",
  "root_folder": "/tv",
  "monitored": true,
  "search_for_missing": true
}
```

**Response 201**:

```json
{
  "id": 1,
  "title": "Breaking Bad",
  "added": true,
  "monitored": true,
  "message": "Series added and search initiated"
}
```

### Movies (Radarr)

Endpoints for managing movies via Radarr.

#### GET /api/v1/movies

List all movies.

**Response 200**:

```json
{
  "movies": [
    {
      "id": 1,
      "title": "Inception",
      "year": 2010,
      "status": "released",
      "monitored": true,
      "quality_profile": "HD-1080p",
      "has_file": true
    }
  ]
}
```

#### POST /api/v1/movies/search

Search for movies.

**Request Body**:

```json
{
  "term": "Inception"
}
```

**Response 200**:

```json
{
  "results": [
    {
      "tmdbId": 27205,
      "title": "Inception",
      "year": 2010,
      "overview": "A thief who steals corporate secrets...",
      "runtime": 148
    }
  ]
}
```

#### POST /api/v1/movies/add

Add a movie to Radarr.

**Request Body**:

```json
{
  "tmdbId": 27205,
  "title": "Inception",
  "quality_profile": "HD-1080p",
  "root_folder": "/movies",
  "monitored": true,
  "search_now": true
}
```

**Response 201**:

```json
{
  "id": 1,
  "title": "Inception",
  "added": true,
  "monitored": true,
  "message": "Movie added and search initiated"
}
```

### Media (Plex)

Endpoints for interacting with Plex.

#### GET /api/v1/media/libraries

List all Plex libraries.

**Response 200**:

```json
{
  "libraries": [
    {
      "key": "1",
      "title": "Movies",
      "type": "movie",
      "count": 450
    },
    {
      "key": "2",
      "title": "TV Shows",
      "type": "show",
      "count": 75
    }
  ]
}
```

#### GET /api/v1/media/recently-added

Get recently added media.

**Query Parameters**:

- `limit` (integer, default: 10): Number of items

**Response 200**:

```json
{
  "items": [
    {
      "title": "Inception",
      "type": "movie",
      "year": 2010,
      "added_at": "2025-01-15T08:00:00Z",
      "library": "Movies"
    }
  ]
}
```

#### POST /api/v1/media/scan

Trigger library scan.

**Request Body**:

```json
{
  "library_key": "1"
}
```

**Response 200**:

```json
{
  "success": true,
  "message": "Library scan initiated",
  "library": "Movies"
}
```

### Settings

Endpoints for managing AutoArr settings.

#### GET /api/v1/settings

Get all settings.

**Response 200**:

```json
{
  "services": {
    "sabnzbd": {
      "enabled": true,
      "url": "http://localhost:8080",
      "connected": true
    },
    "sonarr": {
      "enabled": true,
      "url": "http://localhost:8989",
      "connected": true
    }
  },
  "features": {
    "auto_config_audit": true,
    "download_monitoring": true,
    "auto_retry": true
  },
  "notifications": {
    "webhook_url": null,
    "email_enabled": false
  }
}
```

#### PUT /api/v1/settings

Update settings.

**Request Body**:

```json
{
  "features": {
    "auto_config_audit": false
  }
}
```

**Response 200**:

```json
{
  "success": true,
  "message": "Settings updated",
  "updated_fields": ["features.auto_config_audit"]
}
```

## Data Models

### Common Models

#### Pagination

```typescript
interface Pagination {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

#### ServiceHealth

```typescript
interface ServiceHealth {
  healthy: boolean;
  latency_ms: number | null;
  error: string | null;
  last_check: string;
  circuit_breaker_state: "closed" | "open" | "half_open";
}
```

#### Recommendation

```typescript
interface Recommendation {
  id: number;
  service: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  category: "performance" | "security" | "best_practices";
  current_value: any;
  recommended_value: any;
  impact: string;
  references: string[];
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
```

### Events

#### downloads.update

Real-time download queue updates.

```json
{
  "event": "downloads.update",
  "data": {
    "queue": [...],
    "speed": "25.4 MB/s"
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### config.audit.complete

Configuration audit completed.

```json
{
  "event": "config.audit.complete",
  "data": {
    "audit_id": "audit_123",
    "total_recommendations": 12
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Code Examples

### Python

```python
import httpx

# Initialize client
client = httpx.AsyncClient(base_url="http://localhost:8000")

# Trigger configuration audit
response = await client.post("/api/v1/config/audit", json={
    "services": ["sabnzbd", "sonarr"],
    "include_web_search": True
})
audit = response.json()

# Get recommendations
response = await client.get("/api/v1/config/recommendations", params={
    "priority": "high",
    "page": 1,
    "page_size": 10
})
recommendations = response.json()

# Apply recommendations
response = await client.post("/api/v1/config/apply", json={
    "recommendation_ids": [1, 2, 3],
    "dry_run": False
})
result = response.json()
```

### JavaScript/TypeScript

```typescript
// Initialize client
const baseURL = "http://localhost:8000";

// Trigger configuration audit
const auditResponse = await fetch(`${baseURL}/api/v1/config/audit`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    services: ["sabnzbd", "sonarr"],
    include_web_search: true,
  }),
});
const audit = await auditResponse.json();

// Get recommendations
const recsResponse = await fetch(
  `${baseURL}/api/v1/config/recommendations?priority=high&page=1&page_size=10`,
);
const recommendations = await recsResponse.json();

// Apply recommendations
const applyResponse = await fetch(`${baseURL}/api/v1/config/apply`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    recommendation_ids: [1, 2, 3],
    dry_run: false,
  }),
});
const result = await applyResponse.json();
```

### cURL

```bash
# Trigger configuration audit
curl -X POST http://localhost:8000/api/v1/config/audit \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["sabnzbd", "sonarr"],
    "include_web_search": true
  }'

# Get recommendations
curl http://localhost:8000/api/v1/config/recommendations?priority=high&page=1

# Apply recommendations
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1, 2, 3],
    "dry_run": false
  }'
```

## Interactive Documentation

For interactive API documentation with Try It Out functionality:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

**API Version**: 1.0.0
**Last Updated**: 2025-01-15
**Status**: Active
