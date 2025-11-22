# Post-Deployment Test Suite

This directory contains automated tests that verify the AutoArr application is working correctly after deployment.

## Overview

These tests are designed to run against a live deployment (local or production) to verify:

1. **Health Checks** - Application and service health endpoints
2. **UI Accessibility** - Frontend loads and serves correctly
3. **Settings API** - Configuration persistence works without errors

## Running Tests

### Run All Tests

```bash
cd /app/tests/post-deployment
bash run-all-tests.sh
```

### Run Individual Tests

```bash
# Health check test
bash test-health.sh

# UI accessibility test
bash test-ui-accessible.sh

# Settings API test
bash test-settings-api.sh
```

## Prerequisites

- AutoArr application must be running (typically on `http://localhost:8088`)
- `curl` and `jq` must be installed
- Application must be in a healthy state

## Test Details

### 1. Health Check Test (`test-health.sh`)

**Purpose**: Verify application health endpoints respond correctly

**Tests**:
- Main health endpoint returns `{"status": "healthy"}`
- Individual service health endpoints are accessible
- MCP server connections are reported

**Expected Output**:
```
✅ Main health check: PASSED
  - sabnzbd: disconnected
  - sonarr: disconnected
  - radarr: disconnected
  - plex: healthy
✅ Health Check Test Complete!
```

### 2. UI Accessibility Test (`test-ui-accessible.sh`)

**Purpose**: Verify frontend is properly served

**Tests**:
- Root URL returns HTML (not JSON)
- React root element exists in HTML
- Static assets directory is accessible

**Expected Output**:
```
✅ UI serves HTML: PASSED
✅ React root element found: PASSED
✅ Assets directory accessible: PASSED
✅ UI Accessibility Test Complete!
```

### 3. Settings API Test (`test-settings-api.sh`)

**Purpose**: Verify settings can be saved and persisted

**Tests**:
1. Retrieve current SABnzbd settings
2. Disable SABnzbd and save
3. Verify settings were saved (enabled = false)
4. Re-enable SABnzbd and save
5. Verify settings were saved (enabled = true)

**Expected Output**:
```
✅ Test Complete: Settings toggle and save works without errors!
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

## Integration with CI/CD

These tests can be integrated into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run Post-Deployment Tests
  run: |
    cd /app/tests/post-deployment
    bash run-all-tests.sh
```

## Adding New Tests

To add a new test:

1. Create a new test script: `test-your-feature.sh`
2. Add execution permissions: `chmod +x test-your-feature.sh`
3. Follow the existing test format:
   ```bash
   #!/bin/bash
   echo "=== Your Test Name ==="
   # Test logic here
   echo "✅ Test Complete!"
   ```
4. Add to `run-all-tests.sh`:
   ```bash
   run_test "Your Feature" "test-your-feature.sh"
   ```

## Troubleshooting

**Tests fail with connection errors**:
- Verify AutoArr is running: `docker-compose ps`
- Check application logs: `docker-compose logs autoarr`
- Verify port 8088 is accessible: `curl http://localhost:8088/health`

**Tests fail with 422 errors**:
- Check backend logs for validation errors
- Verify API request format matches backend expectations
- Review recent code changes to settings endpoints

**Tests timeout**:
- Increase curl timeout in test scripts
- Check for blocking operations in application startup
- Verify database migrations completed successfully

## Maintenance

These tests should be updated when:
- New API endpoints are added
- Settings schema changes
- Health check behavior changes
- New services are integrated

---

**Last Updated**: 2025-11-22
**AutoArr Version**: 1.0.0
