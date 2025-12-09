# AutoArr API Versioning

**Last Updated:** 2025-12-09
**Current Version:** v1

---

## Table of Contents

1. [Overview](#overview)
2. [Versioning Strategy](#versioning-strategy)
3. [Using API Versions](#using-api-versions)
4. [Version Lifecycle](#version-lifecycle)
5. [Breaking vs Non-Breaking Changes](#breaking-vs-non-breaking-changes)
6. [Deprecation Policy](#deprecation-policy)
7. [Backward Compatibility](#backward-compatibility)
8. [Migration Guide](#migration-guide)
9. [Version Support Matrix](#version-support-matrix)
10. [Best Practices](#best-practices)

---

## Overview

AutoArr uses **URL-based semantic versioning** for its REST API. This approach provides clear, explicit version control that ensures:

- **Stability**: Existing integrations continue to work without breaking
- **Evolution**: New features can be added without disrupting current users
- **Clarity**: API consumers always know which version they're using
- **Migration Path**: Clear upgrade paths with deprecation notices

### Design Principles

1. **Explicit over Implicit**: Version is always in the URL path
2. **Conservative Breaking Changes**: Major versions change only when necessary
3. **Long Support Windows**: Deprecated versions remain available for reasonable periods
4. **Clear Communication**: Advance notice for deprecations and breaking changes
5. **Backward Compatibility**: Within a major version, changes are additive

---

## Versioning Strategy

### URL-Based Versioning

AutoArr uses URL path prefixes to specify API versions:

```
https://your-autoarr-instance/api/{version}/{resource}
```

**Example:**
```
https://localhost:8088/api/v1/downloads
https://localhost:8088/api/v1/config/audit
https://localhost:8088/api/v1/settings
```

### Semantic Versioning

API versions follow semantic versioning principles:

- **Major Version (v1, v2)**: Breaking changes, incompatible API changes
- **Minor Version**: New functionality added in backward-compatible manner
- **Patch Version**: Backward-compatible bug fixes

**Note**: Only the major version appears in the URL. Minor and patch versions are tracked in the `app_version` field but don't affect the URL structure.

### Current Version

- **Current Stable**: `v1`
- **Application Version**: `1.0.0`
- **Base Path**: `/api/v1`

---

## Using API Versions

### HTTP REST API

All REST endpoints use the `/api/v1` prefix:

```bash
# Health check
curl http://localhost:8088/api/v1/health

# Configuration audit
curl -X POST http://localhost:8088/api/v1/config/audit

# List downloads
curl http://localhost:8088/api/v1/downloads

# Settings
curl http://localhost:8088/api/v1/settings
```

### WebSocket API

WebSocket connections also use versioned endpoints:

```javascript
// Connect to v1 WebSocket endpoint
const ws = new WebSocket('ws://localhost:8088/api/v1/ws');

ws.onopen = () => {
  console.log('Connected to AutoArr v1 WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### OpenAPI Documentation

Interactive API documentation is available at versioned endpoints:

- **Swagger UI**: `http://localhost:8088/docs`
- **ReDoc**: `http://localhost:8088/redoc`
- **OpenAPI JSON**: `http://localhost:8088/openapi.json`

The documentation automatically reflects the current API version.

### Version Discovery

Query the `/api` endpoint to discover available API versions:

```bash
curl http://localhost:8088/api
```

**Response:**
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

---

## Version Lifecycle

### Lifecycle Stages

Each API version goes through the following stages:

1. **Beta**: Testing and stabilization (breaking changes possible)
2. **Stable**: Production-ready, fully supported
3. **Deprecated**: Supported but users should migrate
4. **Sunset**: No longer supported or available

### Support Timeline

| Stage | Duration | Support Level |
|-------|----------|---------------|
| **Beta** | Variable | Best-effort, breaking changes possible |
| **Stable** | Indefinite | Full support, bug fixes, security updates |
| **Deprecated** | 6 months minimum | Security updates only, migration warnings |
| **Sunset** | N/A | No support, endpoint returns 410 Gone |

### Current Version Status

| Version | Status | Release Date | Deprecation Date | Sunset Date |
|---------|--------|--------------|------------------|-------------|
| **v1** | Stable | 2025-01-01 | N/A | N/A |

---

## Breaking vs Non-Breaking Changes

### Breaking Changes (Require Major Version Bump)

Breaking changes require a new major version (v1 → v2):

- **Removing endpoints**: Deleting API endpoints
- **Removing fields**: Removing fields from responses
- **Changing field types**: Changing data types (string → number)
- **Changing behavior**: Altering endpoint semantics
- **Changing authentication**: Modifying auth mechanisms
- **Changing error codes**: Changing HTTP status codes or error formats
- **Renaming fields**: Renaming response/request fields
- **Making fields required**: Changing optional fields to required

**Example:**
```diff
# v1 Response
{
  "download_id": "12345",
  "status": "downloading"
}

# v2 Response (BREAKING: renamed field)
{
  "id": "12345",           # Renamed from download_id
  "state": "downloading"   # Renamed from status
}
```

### Non-Breaking Changes (No Version Bump Required)

These changes can be made within the current version:

- **Adding endpoints**: New API endpoints
- **Adding optional fields**: New optional request parameters
- **Adding response fields**: New fields in responses
- **Adding enum values**: New valid values for existing enums
- **Relaxing validations**: Making required fields optional
- **Bug fixes**: Fixing incorrect behavior
- **Performance improvements**: Optimizing without behavior changes
- **Documentation updates**: Clarifying existing behavior

**Example:**
```diff
# v1 Original Response
{
  "download_id": "12345",
  "status": "downloading"
}

# v1 Enhanced Response (NON-BREAKING: added field)
{
  "download_id": "12345",
  "status": "downloading",
+ "progress_percent": 45.2,  # New optional field
+ "eta_seconds": 120          # New optional field
}
```

---

## Deprecation Policy

### Deprecation Process

When a feature or version needs to be deprecated:

1. **Announcement**: Deprecation announced in release notes and changelog
2. **Header Warnings**: `Deprecation` and `Sunset` HTTP headers added
3. **Documentation Updates**: Deprecated endpoints marked in docs
4. **Migration Guide**: Clear migration path provided
5. **Monitoring Period**: Minimum 6 months before removal
6. **Sunset**: Endpoint removed or returns `410 Gone`

### Deprecation Headers

Deprecated endpoints include HTTP headers:

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jun 2026 00:00:00 GMT
Link: <https://docs.autoarr.io/api/migration-v2>; rel="deprecation"
```

- **Deprecation**: Boolean indicating deprecated status
- **Sunset**: RFC 7231 date when endpoint will be removed
- **Link**: URL to migration documentation

### Client Handling

Clients should:

1. Monitor for `Deprecation` headers
2. Log warnings when deprecated endpoints are used
3. Plan migration before `Sunset` date
4. Test against new version in staging

**Example Client Implementation:**
```javascript
fetch('http://localhost:8088/api/v1/downloads')
  .then(response => {
    // Check for deprecation
    if (response.headers.get('Deprecation')) {
      const sunset = response.headers.get('Sunset');
      console.warn(`API endpoint deprecated. Sunset: ${sunset}`);
      console.warn('Migration guide:', response.headers.get('Link'));
    }
    return response.json();
  });
```

---

## Backward Compatibility

### Guarantees Within Major Versions

Within a major version (e.g., v1):

✅ **Guaranteed**:
- Existing endpoints remain available
- Existing fields maintain types and semantics
- Existing behavior preserved
- Existing error codes unchanged
- Optional parameters remain optional

⚠️ **Not Guaranteed**:
- Response field order
- Error message text (codes are stable)
- Performance characteristics
- Rate limit values (with reasonable notice)

### Handling Unknown Fields

Clients should:

- **Ignore unknown fields**: New fields may be added to responses
- **Validate required fields**: Check for presence of required fields
- **Use defensive parsing**: Don't fail on extra data

**Example:**
```javascript
// Good: Ignore unknown fields
const download = response.data;
const { download_id, status } = download;
// If response adds new fields later, this still works

// Bad: Strict validation that breaks on new fields
const expectedKeys = ['download_id', 'status'];
if (Object.keys(download).some(k => !expectedKeys.includes(k))) {
  throw new Error('Unexpected fields'); // Will break when fields added
}
```

---

## Migration Guide

### Migrating Between Major Versions

When a new major version is released:

1. **Review Changelog**: Read breaking changes and new features
2. **Test in Staging**: Deploy new version to staging environment
3. **Update Client Code**: Modify code for breaking changes
4. **Incremental Rollout**: Gradually migrate traffic to new version
5. **Monitor**: Watch for errors and performance issues
6. **Complete Migration**: Fully switch to new version before old version sunset

### Migration Checklist

- [ ] Read migration guide and changelog
- [ ] Identify affected endpoints in your code
- [ ] Update base URL from `/api/v1` to `/api/v2`
- [ ] Update request/response models for breaking changes
- [ ] Add/remove fields as needed
- [ ] Update error handling for new error codes
- [ ] Test all API interactions thoroughly
- [ ] Update documentation and code comments
- [ ] Monitor logs for deprecation warnings
- [ ] Plan rollback strategy if needed

### Example Migration (v1 → v2, Hypothetical)

**v1 Endpoint:**
```bash
GET /api/v1/downloads
```

**v2 Endpoint:**
```bash
GET /api/v2/queue/items
```

**Code Changes:**
```diff
- const response = await fetch('/api/v1/downloads');
+ const response = await fetch('/api/v2/queue/items');
  const data = await response.json();

  // Handle renamed fields
- const id = item.download_id;
+ const id = item.id;

- const status = item.status;
+ const state = item.state;
```

---

## Version Support Matrix

### Supported Versions

| Version | Status | Python | FastAPI | Support Until |
|---------|--------|--------|---------|---------------|
| **v1** | ✅ Stable | 3.11+ | 0.104+ | Ongoing |

### Planned Versions

| Version | Status | Expected Release | Notes |
|---------|--------|------------------|-------|
| **v2** | 📋 Planned | TBD | Enhanced content classification, improved error handling |

### Dependencies

**Minimum Requirements (v1):**
- Python: 3.11+
- FastAPI: 0.104+
- Pydantic: 2.0+
- httpx: 0.25+

**Recommended:**
- Python: 3.12+
- FastAPI: Latest stable
- uvicorn: Latest stable

---

## Best Practices

### For API Consumers

1. **Always Specify Version**: Use full versioned URLs (`/api/v1/...`)
2. **Monitor Deprecation Headers**: Check for `Deprecation` and `Sunset` headers
3. **Handle Unknown Fields Gracefully**: Ignore fields you don't recognize
4. **Don't Rely on Field Order**: Parse JSON by field name, not position
5. **Use Error Codes, Not Messages**: Error messages may change, codes won't
6. **Set Timeouts**: Always use reasonable request timeouts
7. **Implement Retry Logic**: Use exponential backoff for transient errors
8. **Version Your Client**: Track which API version your client uses
9. **Test Before Migration**: Thoroughly test against new versions
10. **Subscribe to Updates**: Monitor changelog and announcements

### For API Developers

1. **Additive Changes Only**: Only add fields, never remove (within major version)
2. **Default Values**: New optional fields should have sensible defaults
3. **Deprecate Gradually**: Give users time to migrate
4. **Document Everything**: Keep OpenAPI specs current
5. **Version Control**: Tag releases in version control
6. **Changelog**: Maintain detailed changelog
7. **Semantic Versioning**: Follow semver strictly
8. **Backward Compatibility Tests**: Test old clients against new API
9. **Deprecation Warnings**: Log when deprecated features are used
10. **Migration Guides**: Provide clear upgrade paths

### Error Handling

Always handle version-specific errors:

```javascript
async function callAPI(endpoint) {
  try {
    const response = await fetch(`/api/v1${endpoint}`);

    // Check for version-related errors
    if (response.status === 410) {
      throw new Error('API version no longer supported. Please upgrade.');
    }

    if (response.status === 404) {
      // Endpoint not found - might be wrong version
      console.error('Endpoint not found. Check API version.');
    }

    // Check deprecation headers
    if (response.headers.get('Deprecation')) {
      const sunset = response.headers.get('Sunset');
      console.warn(`Warning: This endpoint will be removed on ${sunset}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```

---

## Configuration

### Environment Variables

Control API versioning behavior via environment variables:

```bash
# API version prefix (default: /api/v1)
API_V1_PREFIX=/api/v1

# Application version (semver)
APP_VERSION=1.0.0

# Enable/disable API versioning enforcement
API_VERSION_STRICT=true

# Deprecation warning period (days)
DEPRECATION_WARNING_DAYS=180
```

### Version Detection

The API automatically detects version from URL path:

```python
# Backend (autoarr/api/config.py)
class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    app_version: str = "1.0.0"
```

---

## Frequently Asked Questions

### Why URL-based versioning?

URL-based versioning is:
- **Explicit**: Version is immediately visible in logs and URLs
- **Simple**: Easy to implement and understand
- **Cacheable**: Different versions can be cached separately
- **Testable**: Easy to test multiple versions simultaneously

### When will v2 be released?

v2 is currently in planning. Expected changes include:
- Enhanced content classification system
- Improved error response format
- WebSocket protocol improvements
- Additional metadata endpoints

No release date is set yet.

### Can I use multiple versions simultaneously?

Yes! You can use different API versions in the same application:

```javascript
// Use v1 for stable features
const downloads = await fetch('/api/v1/downloads');

// Use v2 for new features (when available)
const enhanced = await fetch('/api/v2/queue/items');
```

### What happens when a version is sunset?

When a version reaches sunset:
1. All endpoints return `410 Gone`
2. Error message directs to migration guide
3. Requests are logged but not processed
4. Rate limits no longer apply (fast rejection)

### How long will v1 be supported?

v1 will remain supported:
- Until v2 is stable (minimum 6 months after v2 release)
- With security updates for 12 months after deprecation
- At least until 2026

### Do patch releases change the API version?

No. Patch releases (1.0.0 → 1.0.1) are bug fixes only and don't affect:
- API endpoint URLs
- Request/response schemas
- Behavior (except fixing bugs)

The version in the URL (`/api/v1`) remains unchanged.

---

## Resources

### Documentation

- [API Reference](reference.md) - Complete endpoint documentation
- [Testing Guide](testing-guide.md) - API testing best practices
- [Configuration Examples](configuration-examples.md) - Configuration API usage

### External Resources

- [Semantic Versioning](https://semver.org/)
- [RFC 7231 - HTTP Deprecation](https://tools.ietf.org/html/rfc7231)
- [OpenAPI Specification](https://swagger.io/specification/)

### Support

- **Documentation**: `/docs` (Swagger UI)
- **Issues**: [GitHub Issues](https://github.com/FEAWServices/autoarr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/FEAWServices/autoarr/discussions)

---

## Changelog

### v1.0.0 (2025-01-01)

- Initial stable release
- Complete REST API with versioning
- WebSocket support
- MCP proxy endpoints
- Configuration audit
- Download management
- Content requests

---

**Last Updated:** 2025-12-09
**Document Version:** 1.0.0
