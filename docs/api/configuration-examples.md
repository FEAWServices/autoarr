# Configuration Audit API - Example Usage

This document provides example curl commands and usage patterns for the Configuration Audit API endpoints.

## Base URL

```
http://localhost:8000/api/v1/config
```

## Endpoints

### 1. POST /api/v1/config/audit

Trigger a configuration audit for one or more services.

**Example: Audit single service**

```bash
curl -X POST http://localhost:8000/api/v1/config/audit \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["sabnzbd"],
    "include_web_search": false
  }'
```

**Example: Audit multiple services with web search**

```bash
curl -X POST http://localhost:8000/api/v1/config/audit \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["sabnzbd", "sonarr", "radarr"],
    "include_web_search": true
  }'
```

**Response:**

```json
{
  "audit_id": "audit_abc123",
  "timestamp": "2025-10-08T10:00:00Z",
  "services": ["sabnzbd", "sonarr"],
  "recommendations": [
    {
      "id": 1,
      "service": "sabnzbd",
      "category": "performance",
      "priority": "high",
      "title": "Increase article cache",
      "description": "Current cache is too small for optimal performance",
      "current_value": "100M",
      "recommended_value": "500M",
      "impact": "Improved download speed",
      "source": "database",
      "applied": false,
      "applied_at": null
    }
  ],
  "total_recommendations": 1,
  "web_search_used": false
}
```

**Rate Limit:** 10 audits per hour per service

---

### 2. GET /api/v1/config/recommendations

List all recommendations from the latest audit with optional filtering and pagination.

**Example: Get all recommendations**

```bash
curl -X GET http://localhost:8000/api/v1/config/recommendations
```

**Example: Filter by service**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?service=sabnzbd"
```

**Example: Filter by priority**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?priority=high"
```

**Example: Filter by category**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?category=performance"
```

**Example: Pagination**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?page=2&page_size=10"
```

**Example: Combined filters**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?service=sabnzbd&priority=high&category=security&page=1&page_size=20"
```

**Response:**

```json
{
  "recommendations": [
    {
      "id": 1,
      "service": "sabnzbd",
      "category": "performance",
      "priority": "high",
      "title": "Increase article cache",
      "description": "Current cache is too small",
      "current_value": "100M",
      "recommended_value": "500M",
      "impact": "Improved download speed",
      "source": "database",
      "applied": false,
      "applied_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**Rate Limit:** 50 queries per hour

---

### 3. GET /api/v1/config/recommendations/{id}

Get detailed information about a specific recommendation.

**Example:**

```bash
curl -X GET http://localhost:8000/api/v1/config/recommendations/1
```

**Response:**

```json
{
  "id": 1,
  "service": "sabnzbd",
  "category": "performance",
  "priority": "high",
  "title": "Increase article cache",
  "description": "Current cache is too small for optimal performance",
  "current_value": "100M",
  "recommended_value": "500M",
  "impact": "Improved download speed",
  "source": "database",
  "applied": false,
  "applied_at": null,
  "explanation": "A larger article cache reduces disk I/O operations and improves overall download performance, especially on systems with fast internet connections.",
  "references": [
    "https://sabnzbd.org/wiki/configuration",
    "https://forums.sabnzbd.org/viewtopic.php?f=1&t=12345"
  ]
}
```

**Rate Limit:** 50 queries per hour

---

### 4. POST /api/v1/config/apply

Apply recommended configuration changes to services.

**Example: Apply single recommendation**

```bash
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1],
    "dry_run": false
  }'
```

**Example: Apply multiple recommendations**

```bash
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1, 2, 3, 4, 5],
    "dry_run": false
  }'
```

**Example: Dry run (test without applying)**

```bash
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{
    "recommendation_ids": [1, 2, 3],
    "dry_run": true
  }'
```

**Response:**

```json
{
  "results": [
    {
      "recommendation_id": 1,
      "success": true,
      "message": "Configuration applied successfully",
      "service": "sabnzbd",
      "applied_at": "2025-10-08T10:05:00Z",
      "dry_run": false
    },
    {
      "recommendation_id": 2,
      "success": true,
      "message": "Configuration applied successfully",
      "service": "sonarr",
      "applied_at": "2025-10-08T10:05:01Z",
      "dry_run": false
    },
    {
      "recommendation_id": 3,
      "success": false,
      "message": "Service unavailable",
      "service": "radarr",
      "applied_at": null,
      "dry_run": false
    }
  ],
  "total_requested": 3,
  "total_successful": 2,
  "total_failed": 1,
  "dry_run": false
}
```

**Rate Limit:** 20 apply operations per hour

---

### 5. GET /api/v1/config/audit/history

View audit history with timestamps and pagination.

**Example: Get recent audits**

```bash
curl -X GET http://localhost:8000/api/v1/config/audit/history
```

**Example: Pagination**

```bash
curl -X GET "http://localhost:8000/api/v1/config/audit/history?page=2&page_size=20"
```

**Response:**

```json
{
  "audits": [
    {
      "audit_id": "audit_abc123",
      "timestamp": "2025-10-08T10:00:00Z",
      "services": ["sabnzbd", "sonarr"],
      "total_recommendations": 5,
      "applied_recommendations": 2,
      "web_search_used": true
    },
    {
      "audit_id": "audit_def456",
      "timestamp": "2025-10-07T15:30:00Z",
      "services": ["sabnzbd"],
      "total_recommendations": 3,
      "applied_recommendations": 3,
      "web_search_used": false
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

**Rate Limit:** 50 queries per hour

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid service 'invalid_service'. Must be one of: sabnzbd, sonarr, radarr, plex"
}
```

### 404 Not Found

```json
{
  "detail": "Recommendation with ID 999 not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "services"],
      "msg": "Field required"
    }
  ]
}
```

### 429 Too Many Requests (Rate Limit)

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

### 500 Internal Server Error

```json
{
  "detail": "An error occurred during the configuration audit"
}
```

---

## Common Workflows

### Workflow 1: Complete Audit and Apply

1. **Trigger audit**

```bash
curl -X POST http://localhost:8000/api/v1/config/audit \
  -H "Content-Type: application/json" \
  -d '{"services": ["sabnzbd", "sonarr"], "include_web_search": true}'
```

2. **Review recommendations**

```bash
curl -X GET "http://localhost:8000/api/v1/config/recommendations?priority=high"
```

3. **Get details for specific recommendations**

```bash
curl -X GET http://localhost:8000/api/v1/config/recommendations/1
curl -X GET http://localhost:8000/api/v1/config/recommendations/2
```

4. **Test with dry run**

```bash
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{"recommendation_ids": [1, 2], "dry_run": true}'
```

5. **Apply changes**

```bash
curl -X POST http://localhost:8000/api/v1/config/apply \
  -H "Content-Type: application/json" \
  -d '{"recommendation_ids": [1, 2], "dry_run": false}'
```

### Workflow 2: Monitor Audit History

```bash
# Get all audit history
curl -X GET http://localhost:8000/api/v1/config/audit/history

# Get specific page
curl -X GET "http://localhost:8000/api/v1/config/audit/history?page=1&page_size=50"
```

---

## Rate Limits Summary

| Endpoint                                | Rate Limit                     |
| --------------------------------------- | ------------------------------ |
| POST /api/v1/config/audit               | 10 audits per hour per service |
| GET /api/v1/config/recommendations      | 50 queries per hour            |
| GET /api/v1/config/recommendations/{id} | 50 queries per hour            |
| POST /api/v1/config/apply               | 20 apply operations per hour   |
| GET /api/v1/config/audit/history        | 50 queries per hour            |

**Note:** Rate limiting is documented but not yet implemented. Will be added in a future update.

---

## Testing with Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1/config"

# Trigger audit
response = requests.post(
    f"{BASE_URL}/audit",
    json={
        "services": ["sabnzbd", "sonarr"],
        "include_web_search": True
    }
)
audit_result = response.json()
print(f"Audit ID: {audit_result['audit_id']}")
print(f"Total recommendations: {audit_result['total_recommendations']}")

# Get all recommendations
response = requests.get(f"{BASE_URL}/recommendations")
recommendations = response.json()
print(f"Total recommendations: {recommendations['total']}")

# Apply recommendations
rec_ids = [r['id'] for r in recommendations['recommendations'] if r['priority'] == 'high']
response = requests.post(
    f"{BASE_URL}/apply",
    json={
        "recommendation_ids": rec_ids,
        "dry_run": False
    }
)
apply_result = response.json()
print(f"Successfully applied: {apply_result['total_successful']}")
print(f"Failed: {apply_result['total_failed']}")
```

---

## OpenAPI Documentation

Interactive API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
