# Bug Tracking

This document tracks all discovered bugs during Sprint 9 testing and bug fixes.

## Bug Tracking Template

```markdown
### BUG-XXX: [Short Description]

**Priority**: Critical | High | Medium | Low
**Status**: Open | In Progress | Fixed | Won't Fix
**Found**: YYYY-MM-DD
**Fixed**: YYYY-MM-DD
**Component**: [API | Frontend | MCP | Database | etc.]
**Severity**: [Impact description]

**Description**:
[Detailed description of the bug]

**Steps to Reproduce**:

1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Error Messages/Logs**:
```

[Error messages or stack traces]

```

**Root Cause**:
[Analysis of what causes the bug]

**Fix**:
[Description of the fix applied]

**Test Coverage**:
[Tests added to prevent regression]
```

---

## Critical Bugs

### BUG-001: Database Connection Not Initialized in Tests

**Priority**: Critical
**Status**: Fixed
**Found**: 2025-10-08
**Fixed**: 2025-10-08
**Component**: Database
**Severity**: Tests fail without proper database setup

**Description**:
E2E tests fail because database is not properly initialized when `DATABASE_URL` is not set.

**Steps to Reproduce**:

1. Run E2E tests without DATABASE_URL
2. Tests fail with "RuntimeError: Database not initialized"

**Expected Behavior**:
Tests should use in-memory SQLite database

**Actual Behavior**:
Tests fail with runtime error

**Root Cause**:
Database initialization depends on DATABASE_URL being set in environment

**Fix**:
Added default SQLite in-memory database for tests in conftest.py

**Test Coverage**:

- Added test_database fixture
- Verified database initialization in E2E tests

---

## High Priority Bugs

### BUG-002: MCP Orchestrator Timeout Not Configurable

**Priority**: High
**Status**: Open
**Found**: 2025-10-08
**Component**: MCP Orchestrator
**Severity**: Long-running operations may timeout prematurely

**Description**:
MCP orchestrator uses hardcoded timeout values that cannot be overridden for long-running operations.

**Steps to Reproduce**:

1. Trigger configuration audit
2. If MCP server is slow, operation times out
3. No way to configure longer timeout

**Expected Behavior**:
Timeout should be configurable per operation or globally

**Actual Behavior**:
Hardcoded 30 second timeout

**Root Cause**:
Timeout value is hardcoded in orchestrator

**Fix**:
[Pending] Add configurable timeout to settings and orchestrator

**Test Coverage**:
[Pending] Add tests for timeout configuration

---

### BUG-003: WebSocket Endpoints Not Implemented

**Priority**: High
**Status**: Open
**Found**: 2025-10-08
**Component**: WebSocket
**Severity**: Real-time event delivery not functional

**Description**:
WebSocket endpoint `/ws` is not implemented, causing real-time event tests to skip.

**Steps to Reproduce**:

1. Run WebSocket E2E tests
2. All tests skip due to missing WebSocket implementation

**Expected Behavior**:
WebSocket endpoint should be available for real-time events

**Actual Behavior**:
Endpoint not found (404)

**Root Cause**:
WebSocket functionality not yet implemented

**Fix**:
[Pending] Implement WebSocket endpoint in main.py

**Test Coverage**:
Tests already written in `test_websocket_flow.py`

---

## Medium Priority Bugs

### BUG-004: Content Request Endpoint Missing

**Priority**: Medium
**Status**: Open
**Found**: 2025-10-08
**Component**: API
**Severity**: Natural language content requests not working

**Description**:
Endpoint `/api/v1/requests/content` for natural language content requests is not implemented.

**Steps to Reproduce**:

1. POST to /api/v1/requests/content with query
2. Returns 404 Not Found

**Expected Behavior**:
Endpoint should accept natural language queries and add content to Radarr/Sonarr

**Actual Behavior**:
404 error

**Root Cause**:
Endpoint not implemented in routers

**Fix**:
[Pending] Implement content request router and LLM integration

**Test Coverage**:
Tests already written in `test_content_request_flow.py`

---

### BUG-005: Download Retry Endpoint Missing

**Priority**: Medium
**Status**: Open
**Found**: 2025-10-08
**Component**: API
**Severity**: Cannot retry failed downloads via API

**Description**:
Endpoint `/api/v1/downloads/retry` for retrying failed downloads is not implemented.

**Steps to Reproduce**:

1. POST to /api/v1/downloads/retry with nzo_id
2. Returns 404 Not Found

**Expected Behavior**:
Endpoint should retry failed download

**Actual Behavior**:
404 error

**Root Cause**:
Endpoint not implemented in downloads router

**Fix**:
[Pending] Implement retry endpoint in downloads router

**Test Coverage**:
Tests already written in `test_download_recovery_flow.py`

---

### BUG-006: Activity Log Filtering Not Working

**Priority**: Medium
**Status**: Open
**Found**: 2025-10-08
**Component**: API
**Severity**: Cannot filter activity log by correlation ID

**Description**:
Activity log endpoint does not support filtering by correlation_id parameter.

**Steps to Reproduce**:

1. GET /api/v1/monitoring/activity?correlation_id=xxx
2. Parameter is ignored or causes validation error

**Expected Behavior**:
Should return only activities with matching correlation ID

**Actual Behavior**:
Parameter not supported

**Root Cause**:
Correlation ID filtering not implemented in query

**Fix**:
[Pending] Add correlation_id filter to activity log endpoint

**Test Coverage**:
Test already written in `test_download_recovery_flow.py`

---

### BUG-007: Rate Limiting Not Implemented

**Priority**: Medium
**Status**: Open
**Found**: 2025-10-08
**Component**: API
**Severity**: API vulnerable to DoS attacks

**Description**:
No rate limiting middleware implemented, allowing unlimited requests.

**Steps to Reproduce**:

1. Make 1000+ rapid requests
2. All requests processed

**Expected Behavior**:
Requests should be rate limited (e.g., 100/minute per IP)

**Actual Behavior**:
No rate limiting

**Root Cause**:
Rate limiting middleware not implemented

**Fix**:
[Pending] Implement rate limiting using slowapi or similar

**Test Coverage**:
[Pending] Add rate limiting tests

---

## Low Priority Bugs

### BUG-008: API Documentation Examples Missing

**Priority**: Low
**Status**: Open
**Found**: 2025-10-08
**Component**: API Documentation
**Severity**: Developer experience issue

**Description**:
OpenAPI/Swagger documentation missing examples for request bodies.

**Steps to Reproduce**:

1. Open /docs
2. Review endpoint documentation
3. Request examples are minimal

**Expected Behavior**:
Should have comprehensive examples for all endpoints

**Actual Behavior**:
Basic examples only

**Root Cause**:
Examples not added to Pydantic models

**Fix**:
[Pending] Add examples to all Pydantic models

**Test Coverage**:
N/A (documentation improvement)

---

### BUG-009: Frontend npm Audit Warnings

**Priority**: Low
**Status**: Open
**Found**: 2025-10-08
**Component**: Frontend
**Severity**: Potential dependency vulnerabilities

**Description**:
Frontend dependencies may have security advisories.

**Steps to Reproduce**:

1. cd autoarr/ui
2. pnpm audit
3. Check for vulnerabilities

**Expected Behavior**:
No vulnerabilities

**Actual Behavior**:
[To be determined after running audit]

**Root Cause**:
Outdated dependencies

**Fix**:
[Pending] Update vulnerable dependencies

**Test Coverage**:
[Pending] Add automated dependency scanning to CI

---

## Bug Statistics

**Total Bugs**: 9

- **Critical**: 1 (1 fixed, 0 open)
- **High**: 2 (0 fixed, 2 open)
- **Medium**: 5 (0 fixed, 5 open)
- **Low**: 2 (0 fixed, 2 open)

**By Status**:

- **Open**: 8
- **Fixed**: 1
- **In Progress**: 0
- **Won't Fix**: 0

**By Component**:

- API: 4
- MCP: 1
- WebSocket: 1
- Database: 1
- Frontend: 1
- Documentation: 1

## Testing Notes

### Manual Testing Completed

- [x] Health endpoints
- [x] Configuration endpoints
- [x] Settings endpoints
- [x] Download endpoints
- [x] Shows endpoints
- [x] Movies endpoints
- [ ] WebSocket endpoints (not implemented)
- [ ] Content request endpoints (not implemented)
- [ ] Download retry endpoints (not implemented)

### E2E Test Results

All E2E tests written but many skip due to missing endpoint implementations:

- Configuration audit: Partial (some endpoints missing)
- Download recovery: Skipped (retry endpoint missing)
- Content requests: Skipped (endpoint missing)
- WebSocket: Skipped (not implemented)
- API integration: Passing for implemented endpoints

### Integration Test Results

Existing integration tests passing:

- MCP server integration: Passing
- Best practices integration: Passing
- Intelligent recommendation: Passing
- LLM agent integration: Passing

### Unit Test Results

All unit tests passing:

- API endpoints: Passing
- Services: Passing
- MCP clients: Passing
- Models: Passing

---

## Action Items

### Immediate (Critical/High)

1. [ ] Implement WebSocket endpoint for real-time events
2. [ ] Implement content request endpoint with LLM integration
3. [ ] Implement download retry endpoint
4. [ ] Add MCP orchestrator timeout configuration

### Short-term (Medium)

5. [ ] Add correlation ID filtering to activity log
6. [ ] Implement rate limiting middleware
7. [ ] Add configuration update endpoints
8. [ ] Implement batch content request endpoint

### Long-term (Low)

9. [ ] Add comprehensive API documentation examples
10. [ ] Audit and update frontend dependencies
11. [ ] Add automated security scanning to CI
12. [ ] Implement notification system

---

Last updated: 2025-10-08
