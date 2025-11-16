# AutoArr API Reference

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`
**Last Updated:** 2025-01-08

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Configuration Management](#configuration-management)
   - [Downloads (SABnzbd)](#downloads-sabnzbd)
   - [TV Shows (Sonarr)](#tv-shows-sonarr)
   - [Movies (Radarr)](#movies-radarr)
   - [Media (Plex)](#media-plex)
   - [Settings](#settings)
   - [MCP Proxy](#mcp-proxy)
5. [WebSocket API](#websocket-api)
6. [Request/Response Examples](#requestresponse-examples)

---

## Authentication

AutoArr currently uses API key authentication. All requests must include an `X-API-Key` header.

### Header Format

```
X-API-Key: your-api-key-here
```

### Getting an API Key

API keys are configured in the settings or generated during initial setup.

```bash
# Example request with API key
curl -H "X-API-Key: abc123..." http://localhost:8000/api/v1/health
```

---

## Rate Limiting

AutoArr implements rate limiting to prevent abuse and ensure fair resource usage.

### Rate Limits

| Endpoint Category   | Limit               |
| ------------------- | ------------------- |
| Health Checks       | 60 requests/minute  |
| Configuration Audit | 10 requests/hour    |
| Apply Configuration | 20 requests/hour    |
| Content Requests    | 30 requests/hour    |
| General API         | 100 requests/minute |

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642087200
```

### Rate Limit Exceeded

When rate limit is exceeded, the API returns:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 30 seconds.",
  "retry_after": 30
}
```

**Status Code:** `429 Too Many Requests`

---

## Error Handling

### Error Response Format

All errors follow a consistent JSON format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

### HTTP Status Codes

| Code | Meaning               | Description                     |
| ---- | --------------------- | ------------------------------- |
| 200  | OK                    | Request successful              |
| 201  | Created               | Resource created successfully   |
| 400  | Bad Request           | Invalid request parameters      |
| 401  | Unauthorized          | Missing or invalid API key      |
| 403  | Forbidden             | Insufficient permissions        |
| 404  | Not Found             | Resource not found              |
| 429  | Too Many Requests     | Rate limit exceeded             |
| 500  | Internal Server Error | Server error occurred           |
| 503  | Service Unavailable   | Service temporarily unavailable |

### Common Error Codes

| Error Code             | Description                      |
| ---------------------- | -------------------------------- |
| `invalid_request`      | Request parameters are invalid   |
| `not_found`            | Requested resource doesn't exist |
| `mcp_connection_error` | Cannot connect to MCP server     |
| `service_unavailable`  | External service is down         |
| `rate_limit_exceeded`  | Too many requests                |
| `internal_error`       | Unexpected server error          |

---

## Endpoints

### Health Check

Check system and service health status.

#### GET /health

Get overall system health including all connected services.

**Request:**

```bash
curl -X GET http://localhost:8000/health
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "services": {
    "sabnzbd": {
      "healthy": true,
      "latency_ms": 45.2,
      "error": null,
      "last_check": "2025-01-08T10:30:00Z",
      "circuit_breaker_state": "closed"
    },
    "sonarr": {
      "healthy": true,
      "latency_ms": 38.7,
      "error": null,
      "last_check": "2025-01-08T10:30:00Z",
      "circuit_breaker_state": "closed"
    },
    "radarr": {
      "healthy": true,
      "latency_ms": 42.1,
      "error": null,
      "last_check": "2025-01-08T10:30:00Z",
      "circuit_breaker_state": "closed"
    }
  },
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Status Values:**

- `healthy` - All services operational
- `degraded` - Some services unavailable
- `unhealthy` - All services unavailable

---

#### GET /health/{service}

Check health of a specific service.

**Parameters:**

- `service` (path): Service name (`sabnzbd`, `sonarr`, `radarr`, `plex`)

**Request:**

```bash
curl -X GET http://localhost:8000/health/sabnzbd
```

**Response:** `200 OK`

```json
{
  "healthy": true,
  "latency_ms": 45.2,
  "error": null,
  "last_check": "2025-01-08T10:30:00Z",
  "circuit_breaker_state": "closed"
}
```

**Error Response:** `503 Service Unavailable`

```json
{
  "error": "service_unavailable",
  "message": "Service 'sabnzbd' is not connected"
}
```

---

#### GET /health/circuit-breaker/{service}

Get circuit breaker status for a service.

**Parameters:**

- `service` (path): Service name

**Request:**

```bash
curl -X GET http://localhost:8000/health/circuit-breaker/sabnzbd
```

**Response:** `200 OK`

```json
{
  "state": "closed",
  "failure_count": 0,
  "success_count": 15,
  "threshold": 5,
  "timeout": 60.0
}
```

**Circuit Breaker States:**

- `closed` - Normal operation
- `open` - Too many failures, blocking requests
- `half_open` - Testing if service recovered

---

### Configuration Management

Intelligent configuration auditing and recommendations.

#### POST /api/v1/config/audit

Trigger a configuration audit for one or more services.

**Rate Limit:** 10 requests/hour

**Request Body:**

```json
{
  "services": ["sabnzbd", "sonarr"],
  "include_web_search": true
}
```

**Parameters:**

- `services` (required): Array of service names to audit
- `include_web_search` (optional): Include web search for latest best practices (default: true)

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/config/audit \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["sabnzbd", "sonarr"],
    "include_web_search": true
  }'
```

**Response:** `200 OK`

```json
{
  "audit_id": "audit_abc123",
  "timestamp": "2025-01-08T10:30:00Z",
  "services_audited": ["sabnzbd", "sonarr"],
  "total_recommendations": 8,
  "recommendations_by_priority": {
    "critical": 1,
    "high": 3,
    "medium": 3,
    "low": 1
  },
  "summary": {
    "sabnzbd": {
      "issues_found": 5,
      "recommendations": 5
    },
    "sonarr": {
      "issues_found": 3,
      "recommendations": 3
    }
  }
}
```

**Error Response:** `400 Bad Request`

```json
{
  "error": "invalid_request",
  "message": "At least one service must be specified"
}
```

---

#### GET /api/v1/config/recommendations

List all configuration recommendations with filtering and pagination.

**Rate Limit:** 50 requests/hour

**Query Parameters:**

- `service` (optional): Filter by service name
- `priority` (optional): Filter by priority (`critical`, `high`, `medium`, `low`)
- `category` (optional): Filter by category (`performance`, `security`, `best_practices`)
- `page` (optional): Page number, 1-indexed (default: 1)
- `page_size` (optional): Items per page, 1-100 (default: 10)

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?service=sabnzbd&priority=high&page=1&page_size=10"
```

**Response:** `200 OK`

```json
{
  "recommendations": [
    {
      "id": 1,
      "service": "sabnzbd",
      "category": "performance",
      "setting_name": "article_cache_max",
      "current_value": "200M",
      "recommended_value": "500M",
      "priority": "high",
      "rationale": "Increasing article cache improves download speeds for slower connections",
      "impact": "15-25% faster downloads",
      "applied": false,
      "created_at": "2025-01-08T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 25,
    "total_pages": 3
  },
  "filters_applied": {
    "service": "sabnzbd",
    "priority": "high"
  }
}
```

---

#### GET /api/v1/config/recommendations/{recommendation_id}

Get detailed information about a specific recommendation.

**Rate Limit:** 50 requests/hour

**Parameters:**

- `recommendation_id` (path): Recommendation ID

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/config/recommendations/1
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "service": "sabnzbd",
  "category": "performance",
  "setting_name": "article_cache_max",
  "current_value": "200M",
  "recommended_value": "500M",
  "priority": "high",
  "rationale": "Increasing article cache improves download speeds for slower connections",
  "impact": "15-25% faster downloads",
  "explanation": "The article cache stores partially downloaded articles in memory...",
  "references": [
    "https://sabnzbd.org/wiki/configuration/general#article-cache",
    "https://forums.sabnzbd.org/viewtopic.php?t=12345"
  ],
  "applied": false,
  "created_at": "2025-01-08T10:30:00Z",
  "applied_at": null
}
```

**Error Response:** `404 Not Found`

```json
{
  "error": "not_found",
  "message": "Recommendation with ID 999 not found"
}
```

---

#### POST /api/v1/config/apply

Apply one or more configuration recommendations.

**Rate Limit:** 20 requests/hour

**Request Body:**

```json
{
  "recommendation_ids": [1, 2, 3],
  "dry_run": false
}
```

**Parameters:**

- `recommendation_ids` (required): Array of recommendation IDs to apply
- `dry_run` (optional): Test without making changes (default: false)

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1, 2, 3],
    "dry_run": false
  }'
```

**Response:** `200 OK`

```json
{
  "results": [
    {
      "recommendation_id": 1,
      "success": true,
      "message": "Configuration applied successfully",
      "previous_value": "200M",
      "new_value": "500M",
      "rollback_available": true
    },
    {
      "recommendation_id": 2,
      "success": false,
      "message": "Service connection failed",
      "error": "mcp_connection_error"
    }
  ],
  "summary": {
    "total": 3,
    "successful": 2,
    "failed": 1
  },
  "dry_run": false
}
```

---

#### GET /api/v1/config/audit/history

View configuration audit history with pagination.

**Rate Limit:** 50 requests/hour

**Query Parameters:**

- `page` (optional): Page number, 1-indexed (default: 1)
- `page_size` (optional): Items per page, 1-100 (default: 10)

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/config/audit/history?page=1&page_size=10"
```

**Response:** `200 OK`

```json
{
  "audits": [
    {
      "audit_id": "audit_abc123",
      "timestamp": "2025-01-08T10:30:00Z",
      "services": ["sabnzbd", "sonarr"],
      "total_recommendations": 8,
      "critical_count": 1,
      "high_count": 3,
      "medium_count": 3,
      "low_count": 1,
      "applied_count": 5
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 45,
    "total_pages": 5
  }
}
```

---

### Downloads (SABnzbd)

Manage downloads through SABnzbd.

#### GET /api/v1/downloads/queue

Get current download queue.

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/downloads/queue
```

**Response:** `200 OK`

```json
{
  "queue": [
    {
      "nzo_id": "SABnzbd_nzo_abc123",
      "filename": "Movie.Title.2024.1080p.mkv",
      "mb_left": 1536.5,
      "mb": 2048.0,
      "percentage": 25,
      "eta": "00:15:30",
      "status": "Downloading",
      "priority": "Normal"
    }
  ],
  "speed": "5.2 MB/s",
  "size_left": "15.2 GB",
  "paused": false,
  "disk_space": "250.5 GB"
}
```

---

#### GET /api/v1/downloads/history

Get download history.

**Query Parameters:**

- `limit` (optional): Maximum items to return (default: 50)

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/downloads/history?limit=20"
```

**Response:** `200 OK`

```json
{
  "history": [
    {
      "nzo_id": "SABnzbd_nzo_xyz789",
      "name": "Show.S01E01.1080p",
      "category": "tv",
      "status": "Completed",
      "fail_message": "",
      "size": "1.5 GB",
      "completed": "2025-01-08T09:45:00Z"
    },
    {
      "nzo_id": "SABnzbd_nzo_def456",
      "name": "Movie.2024.2160p",
      "category": "movies",
      "status": "Failed",
      "fail_message": "Incomplete download",
      "size": "15.2 GB",
      "completed": "2025-01-08T08:30:00Z"
    }
  ],
  "total": 150
}
```

---

#### POST /api/v1/downloads/retry/{nzo_id}

Retry a failed download.

**Parameters:**

- `nzo_id` (path): NZB ID to retry

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/downloads/retry/SABnzbd_nzo_abc123
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Download retried successfully",
  "nzo_id": "SABnzbd_nzo_abc123",
  "new_nzo_id": "SABnzbd_nzo_new456"
}
```

---

#### POST /api/v1/downloads/pause

Pause the download queue.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/downloads/pause
```

**Response:** `200 OK`

```json
{
  "success": true,
  "paused": true,
  "queue_status": "Paused"
}
```

---

#### POST /api/v1/downloads/resume

Resume the download queue.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/downloads/resume
```

**Response:** `200 OK`

```json
{
  "success": true,
  "paused": false,
  "queue_status": "Downloading"
}
```

---

#### DELETE /api/v1/downloads/{nzo_id}

Delete a download from the queue.

**Parameters:**

- `nzo_id` (path): NZB ID to delete

**Request:**

```bash
curl -X DELETE http://localhost:8000/api/v1/downloads/SABnzbd_nzo_abc123
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Download deleted successfully",
  "nzo_id": "SABnzbd_nzo_abc123"
}
```

---

### TV Shows (Sonarr)

Manage TV shows through Sonarr.

#### GET /api/v1/shows/

List all TV shows.

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/shows/
```

**Response:** `200 OK`

```json
{
  "series": [
    {
      "id": 1,
      "title": "Breaking Bad",
      "tvdbId": 81189,
      "status": "ended",
      "overview": "A high school chemistry teacher...",
      "network": "AMC",
      "year": 2008,
      "seasons": 5,
      "episodeCount": 62,
      "monitored": true,
      "qualityProfileId": 1,
      "path": "/tv/Breaking Bad"
    }
  ],
  "total": 25
}
```

---

#### GET /api/v1/shows/{series_id}

Get a specific TV show.

**Parameters:**

- `series_id` (path): Sonarr series ID

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/shows/123
```

**Response:** `200 OK`

```json
{
  "id": 123,
  "title": "Breaking Bad",
  "tvdbId": 81189,
  "status": "ended",
  "overview": "A high school chemistry teacher...",
  "network": "AMC",
  "year": 2008,
  "seasons": [
    {
      "seasonNumber": 1,
      "monitored": true,
      "statistics": {
        "episodeCount": 7,
        "episodeFileCount": 7,
        "percentOfEpisodes": 100
      }
    }
  ],
  "qualityProfileId": 1,
  "path": "/tv/Breaking Bad",
  "monitored": true,
  "sizeOnDisk": 15360000000
}
```

---

#### POST /api/v1/shows/

Add a new TV show.

**Request Body:**

```json
{
  "title": "Breaking Bad",
  "tvdb_id": 81189,
  "quality_profile_id": 1,
  "root_folder_path": "/tv",
  "monitored": true,
  "season_folder": true,
  "search_for_missing_episodes": false
}
```

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/shows/ \
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

**Response:** `201 Created`

```json
{
  "id": 124,
  "title": "Breaking Bad",
  "tvdbId": 81189,
  "added": "2025-01-08T10:30:00Z",
  "qualityProfileId": 1,
  "path": "/tv/Breaking Bad",
  "monitored": true
}
```

---

#### POST /api/v1/shows/{series_id}/search

Trigger episode search for a series.

**Parameters:**

- `series_id` (path): Series ID to search

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/shows/123/search
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Search triggered for Breaking Bad",
  "command_id": "cmd_789"
}
```

---

#### DELETE /api/v1/shows/{series_id}

Delete a TV show.

**Parameters:**

- `series_id` (path): Series ID to delete
- `delete_files` (query, optional): Delete media files (default: false)

**Request:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/shows/123?delete_files=false"
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Series deleted successfully",
  "series_id": 123,
  "files_deleted": false
}
```

---

### Movies (Radarr)

Manage movies through Radarr.

#### GET /api/v1/movies/

List all movies.

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/movies/
```

**Response:** `200 OK`

```json
{
  "movies": [
    {
      "id": 1,
      "title": "The Matrix",
      "year": 1999,
      "tmdbId": 603,
      "status": "released",
      "overview": "A computer hacker learns...",
      "runtime": 136,
      "monitored": true,
      "qualityProfileId": 1,
      "path": "/movies/The Matrix (1999)",
      "hasFile": true,
      "sizeOnDisk": 8589934592
    }
  ],
  "total": 150
}
```

---

#### GET /api/v1/movies/{movie_id}

Get a specific movie.

**Parameters:**

- `movie_id` (path): Radarr movie ID

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/movies/123
```

**Response:** `200 OK`

```json
{
  "id": 123,
  "title": "The Matrix",
  "year": 1999,
  "tmdbId": 603,
  "status": "released",
  "overview": "A computer hacker learns...",
  "runtime": 136,
  "genres": ["Action", "Science Fiction"],
  "ratings": {
    "value": 8.2,
    "votes": 18500
  },
  "qualityProfileId": 1,
  "path": "/movies/The Matrix (1999)",
  "monitored": true,
  "hasFile": true,
  "movieFile": {
    "relativePath": "The Matrix (1999) Bluray-1080p.mkv",
    "size": 8589934592,
    "quality": {
      "quality": {
        "name": "Bluray-1080p"
      }
    }
  }
}
```

---

#### POST /api/v1/movies/

Add a new movie.

**Request Body:**

```json
{
  "title": "The Matrix",
  "tmdb_id": 603,
  "quality_profile_id": 1,
  "root_folder_path": "/movies",
  "monitored": true,
  "search_for_movie": true,
  "minimum_availability": "released"
}
```

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/movies/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Matrix",
    "tmdb_id": 603,
    "quality_profile_id": 1,
    "root_folder_path": "/movies",
    "monitored": true,
    "search_for_movie": true
  }'
```

**Response:** `201 Created`

```json
{
  "id": 151,
  "title": "The Matrix",
  "year": 1999,
  "tmdbId": 603,
  "added": "2025-01-08T10:30:00Z",
  "qualityProfileId": 1,
  "path": "/movies/The Matrix (1999)",
  "monitored": true
}
```

---

#### POST /api/v1/movies/{movie_id}/search

Trigger movie search.

**Parameters:**

- `movie_id` (path): Movie ID to search

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/movies/123/search
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Search triggered for The Matrix",
  "command_id": "cmd_456"
}
```

---

#### DELETE /api/v1/movies/{movie_id}

Delete a movie.

**Parameters:**

- `movie_id` (path): Movie ID to delete
- `delete_files` (query, optional): Delete media files (default: false)

**Request:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/movies/123?delete_files=false"
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Movie deleted successfully",
  "movie_id": 123,
  "files_deleted": false
}
```

---

### Media (Plex)

Interact with Plex media server.

#### GET /api/v1/media/libraries

List all Plex libraries.

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/media/libraries
```

**Response:** `200 OK`

```json
{
  "libraries": [
    {
      "key": "1",
      "title": "Movies",
      "type": "movie",
      "scanner": "Plex Movie Scanner",
      "agent": "com.plexapp.agents.themoviedb",
      "count": 450
    },
    {
      "key": "2",
      "title": "TV Shows",
      "type": "show",
      "scanner": "Plex Series Scanner",
      "agent": "com.plexapp.agents.thetvdb",
      "count": 75
    }
  ]
}
```

---

#### GET /api/v1/media/recently-added

Get recently added media.

**Query Parameters:**

- `limit` (optional): Maximum items (default: 20)

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/media/recently-added?limit=10"
```

**Response:** `200 OK`

```json
{
  "items": [
    {
      "title": "The Matrix",
      "year": 1999,
      "type": "movie",
      "added_at": "2025-01-08T09:30:00Z",
      "library": "Movies",
      "rating": 8.2
    }
  ],
  "total": 10
}
```

---

#### POST /api/v1/media/scan

Trigger library scan.

**Request Body:**

```json
{
  "library_key": "1"
}
```

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/media/scan \
  -H "Content-Type: application/json" \
  -d '{"library_key": "1"}'
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Library scan triggered",
  "library": "Movies"
}
```

---

### Settings

Manage AutoArr settings and MCP server configurations.

#### GET /api/v1/settings

Get all settings.

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/settings
```

**Response:** `200 OK`

```json
{
  "mcp_servers": {
    "sabnzbd": {
      "enabled": true,
      "url": "http://sabnzbd:8080",
      "connected": true
    },
    "sonarr": {
      "enabled": true,
      "url": "http://sonarr:8989",
      "connected": true
    },
    "radarr": {
      "enabled": true,
      "url": "http://radarr:7878",
      "connected": true
    }
  },
  "llm": {
    "provider": "claude",
    "model": "claude-3-sonnet-20240229"
  },
  "audit": {
    "auto_audit_enabled": false,
    "auto_audit_interval_hours": 24
  }
}
```

---

#### PUT /api/v1/settings

Update settings.

**Request Body:**

```json
{
  "audit": {
    "auto_audit_enabled": true,
    "auto_audit_interval_hours": 12
  }
}
```

**Request:**

```bash
curl -X PUT http://localhost:8000/api/v1/settings \
  -H "Content-Type: application/json" \
  -d '{
    "audit": {
      "auto_audit_enabled": true,
      "auto_audit_interval_hours": 12
    }
  }'
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Settings updated successfully",
  "updated_settings": {
    "audit": {
      "auto_audit_enabled": true,
      "auto_audit_interval_hours": 12
    }
  }
}
```

---

### MCP Proxy

Direct access to MCP servers (advanced usage).

#### POST /api/v1/mcp/{server}/call

Call an MCP tool directly.

**Parameters:**

- `server` (path): Server name (`sabnzbd`, `sonarr`, `radarr`, `plex`)

**Request Body:**

```json
{
  "tool": "get_queue",
  "arguments": {}
}
```

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/mcp/sabnzbd/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_queue",
    "arguments": {}
  }'
```

**Response:** `200 OK`

```json
{
  "result": {
    "queue": [...],
    "speed": "5.2 MB/s"
  },
  "execution_time_ms": 45.2
}
```

---

#### GET /api/v1/mcp/{server}/tools

List available tools for an MCP server.

**Parameters:**

- `server` (path): Server name

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/mcp/sabnzbd/tools
```

**Response:** `200 OK`

```json
{
  "server": "sabnzbd",
  "tools": [
    {
      "name": "get_queue",
      "description": "Get current download queue",
      "parameters": {}
    },
    {
      "name": "get_history",
      "description": "Get download history",
      "parameters": {
        "limit": {
          "type": "integer",
          "description": "Maximum items to return",
          "default": 50
        }
      }
    }
  ]
}
```

---

## WebSocket API

AutoArr provides WebSocket support for real-time updates.

### Connection

**URL:** `ws://localhost:8000/ws/{client_id}`

**Protocol:** WebSocket

### Connection Example

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/client-123");

ws.onopen = () => {
  console.log("Connected");

  // Join a room
  ws.send(
    JSON.stringify({
      type: "join_room",
      room: "config_audit",
    }),
  );
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected");
};
```

### Message Types

#### Client Messages

**Join Room:**

```json
{
  "type": "join_room",
  "room": "config_audit"
}
```

**Leave Room:**

```json
{
  "type": "leave_room",
  "room": "config_audit"
}
```

**Ping:**

```json
{
  "type": "ping"
}
```

#### Server Messages

**Config Audit Completed:**

```json
{
  "type": "config.audit.completed",
  "data": {
    "audit_id": "audit_abc123",
    "recommendation_count": 8
  },
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Download Failed:**

```json
{
  "type": "download.failed",
  "data": {
    "download_id": "SABnzbd_nzo_abc123",
    "title": "Movie.2024.1080p",
    "reason": "Incomplete download"
  },
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Content Added:**

```json
{
  "type": "content.added",
  "data": {
    "request_id": "req_456",
    "content_id": "123",
    "title": "The Matrix",
    "type": "movie"
  },
  "timestamp": "2025-01-08T10:30:00Z"
}
```

**Pong:**

```json
{
  "type": "pong"
}
```

### Available Rooms

- `config_audit` - Configuration audit events
- `downloads` - Download events
- `content_requests` - Content request events
- `system` - System-wide events

---

## Request/Response Examples

### Complete Configuration Audit Workflow

```bash
# 1. Trigger audit
curl -X POST http://localhost:8000/api/v1/config/audit \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["sabnzbd"],
    "include_web_search": true
  }'

# Response
# {
#   "audit_id": "audit_abc123",
#   "total_recommendations": 5,
#   ...
# }

# 2. Get recommendations
curl -X GET "http://localhost:8000/api/v1/config/recommendations?priority=high"

# 3. Get recommendation details
curl -X GET http://localhost:8000/api/v1/config/recommendations/1

# 4. Apply recommendation (dry run first)
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1],
    "dry_run": true
  }'

# 5. Apply for real
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1],
    "dry_run": false
  }'
```

### Monitor Download Queue

```bash
# Get current queue
curl -X GET http://localhost:8000/api/v1/downloads/queue

# Check for failed downloads
curl -X GET http://localhost:8000/api/v1/downloads/history \
  | jq '.history[] | select(.status=="Failed")'

# Retry failed download
curl -X POST http://localhost:8000/api/v1/downloads/retry/SABnzbd_nzo_abc123
```

### Add Content

```bash
# Add a movie
curl -X POST http://localhost:8000/api/v1/movies/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Inception",
    "tmdb_id": 27205,
    "quality_profile_id": 1,
    "root_folder_path": "/movies",
    "monitored": true,
    "search_for_movie": true
  }'

# Add a TV show
curl -X POST http://localhost:8000/api/v1/shows/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking Bad",
    "tvdb_id": 81189,
    "quality_profile_id": 1,
    "root_folder_path": "/tv",
    "monitored": true
  }'
```

---

## SDK Examples

### Python SDK

```python
import httpx

class AutoArrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    async def trigger_audit(self, services: list[str]) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/config/audit",
                json={"services": services},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_download_queue(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/downloads/queue",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

# Usage
client = AutoArrClient("http://localhost:8000", "your-api-key")
audit = await client.trigger_audit(["sabnzbd", "sonarr"])
```

### JavaScript/TypeScript SDK

```typescript
class AutoArrClient {
  constructor(
    private baseUrl: string,
    private apiKey: string,
  ) {}

  async triggerAudit(services: string[]): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/config/audit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": this.apiKey,
      },
      body: JSON.stringify({ services }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getDownloadQueue(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/downloads/queue`, {
      headers: {
        "X-API-Key": this.apiKey,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

// Usage
const client = new AutoArrClient("http://localhost:8000", "your-api-key");
const audit = await client.triggerAudit(["sabnzbd", "sonarr"]);
```

---

## Changelog

### v1.0.0 (2025-01-08)

**Initial Release**

- Complete REST API for configuration management
- Health check endpoints with circuit breaker support
- Download management via SABnzbd
- TV show management via Sonarr
- Movie management via Radarr
- Media library access via Plex
- WebSocket support for real-time updates
- MCP proxy for direct server access

---

## Support

For API support and questions:

- GitHub Issues: https://github.com/autoarr/autoarr/issues
- Discord: https://discord.gg/autoarr
- Documentation: https://docs.autoarr.io

---

**Last Updated:** 2025-01-08
**API Version:** 1.0.0
**Documentation Version:** 1.0.0
