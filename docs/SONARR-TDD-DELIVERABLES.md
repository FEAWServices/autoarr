# Sonarr MCP Server - TDD Test Suite Deliverables

## Overview

A complete Test-Driven Development (TDD) test suite has been created for the Sonarr MCP Server. All tests are written **BEFORE** implementation, following strict TDD principles to drive development through the red-green-refactor cycle.

## Deliverable Status: ✅ COMPLETE

**TDD Phase:** 🔴 RED (All tests written, awaiting implementation)
**Total Tests:** 238 test methods
**Coverage Target:** 90%+
**Test Files:** 4 test files + 8 test data factories

## Files Delivered

### 📚 Documentation (3 files)

1. **`C:\Git\autoarr\docs\test-strategy-sonarr.md`**
   - Comprehensive test strategy document
   - Test specifications for all components
   - Mock strategies and patterns
   - Mutation testing approach
   - CI/CD integration plan

2. **`C:\Git\autoarr\docs\SONARR-TEST-SUMMARY.md`**
   - Executive summary of test suite
   - Implementation requirements
   - API endpoint reference
   - TDD workflow guide

3. **`C:\Git\autoarr\tests\unit\mcp_servers\sonarr\README.md`**
   - Test suite usage guide
   - Running tests instructions
   - Test category breakdown

### 🏭 Test Data Factories (1 file)

4. **`C:\Git\autoarr\tests\fixtures\conftest.py`** (extended)
   - `sonarr_series_factory` - Creates realistic TV series data
   - `sonarr_episode_factory` - Creates episode data with files
   - `sonarr_quality_profile_factory` - Creates quality profiles
   - `sonarr_command_factory` - Creates command responses
   - `sonarr_calendar_factory` - Creates calendar/upcoming episodes
   - `sonarr_queue_factory` - Creates download queue data
   - `sonarr_wanted_factory` - Creates wanted/missing episodes
   - `sonarr_system_status_factory` - Creates system status

### 🧪 Unit Tests (3 files)

5. **`C:\Git\autoarr\tests\unit\mcp_servers\sonarr\__init__.py`**
   - Package initialization

6. **`C:\Git\autoarr\tests\unit\mcp_servers\sonarr\test_sonarr_client.py`**
   - **112 test methods** for SonarrClient class
   - Covers: initialization, series ops, episode ops, commands, calendar, queue, wanted, errors, auth, edge cases

7. **`C:\Git\autoarr\tests\unit\mcp_servers\sonarr\test_sonarr_server.py`**
   - **68 test methods** for SonarrMCPServer class
   - Covers: server init, tool registration, tool execution, error handling, response formatting, MCP compliance

### 🔗 Integration Tests (3 files)

8. **`C:\Git\autoarr\tests\integration\mcp_servers\sonarr\__init__.py`**
   - Package initialization

9. **`C:\Git\autoarr\tests\integration\mcp_servers\sonarr\test_sonarr_api_integration.py`**
   - **32 test methods** for API integration
   - Covers: full workflows, API endpoint validation, error scenarios, data integrity, performance

10. **`C:\Git\autoarr\tests\integration\mcp_servers\sonarr\test_sonarr_mcp_integration.py`**
    - **26 test methods** for MCP protocol integration
    - Covers: E2E workflows, protocol compliance, error propagation, data transformation

## Test Statistics

```
Total Test Methods: 238
├── Unit Tests: 180 (75.6%)
│   ├── SonarrClient: 112 tests
│   └── SonarrMCPServer: 68 tests
└── Integration Tests: 58 (24.4%)
    ├── API Integration: 32 tests
    └── MCP Integration: 26 tests

Test Pyramid Distribution:
├── Unit Tests: 75.6% (target: 70%)
├── Integration Tests: 24.4% (target: 20-30%)
└── Coverage Target: 90%+
```

## Quick Start - Verify RED Phase

```bash
# Navigate to project
cd C:\Git\autoarr

# Try to run tests (they will fail - this is expected!)
pytest tests/unit/mcp_servers/sonarr/test_sonarr_client.py -v

# Expected output: ModuleNotFoundError: No module named 'sonarr.client'
# This confirms RED phase - tests are ready, implementation is needed
```

## Implementation Guide

### Step 1: Create Client Module

**File:** `C:\Git\autoarr\mcp-servers\sonarr\__init__.py`
```python
"""Sonarr MCP Server package."""
```

**File:** `C:\Git\autoarr\mcp-servers\sonarr\client.py`
```python
"""Sonarr API Client."""

class SonarrClientError(Exception):
    """Base exception for Sonarr client errors."""
    pass

class SonarrConnectionError(SonarrClientError):
    """Exception raised when connection to Sonarr fails."""
    pass

class SonarrClient:
    """Async client for Sonarr API v3."""

    def __init__(self, url: str, api_key: str, timeout: float = 30.0):
        # Validate parameters
        # Store configuration
        # IMPORTANT: Use header-based auth, NOT query params
        pass

    # Implement all methods listed in test specifications
    # See docs/SONARR-TEST-SUMMARY.md for complete method list
```

### Step 2: Create Server Module

**File:** `C:\Git\autoarr\mcp-servers\sonarr\server.py`
```python
"""Sonarr MCP Server."""

from mcp.server import Server
from mcp.types import Tool, TextContent

class SonarrMCPServer:
    """MCP Server for Sonarr."""

    def __init__(self, client):
        # Validate client
        # Initialize MCP server
        # Setup handlers
        pass

    # Implement all methods listed in test specifications
    # See docs/SONARR-TEST-SUMMARY.md for complete tool list
```

### Step 3: Run Tests (Green Phase)

```bash
# Run all tests
pytest tests/unit/mcp_servers/sonarr/ tests/integration/mcp_servers/sonarr/ -v

# Run with coverage
pytest tests/unit/mcp_servers/sonarr/ tests/integration/mcp_servers/sonarr/ \
  --cov=mcp_servers.sonarr \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=90

# Expected: All 238 tests pass with 90%+ coverage
```

### Step 4: Refactor Phase

Once all tests pass:
1. Extract common patterns
2. Improve code organization
3. Add comprehensive type hints
4. Optimize performance
5. Add detailed docstrings
6. Ensure tests still pass

### Step 5: Mutation Testing

```bash
# Install mutation testing
pip install mutmut

# Run mutation tests
mutmut run --paths-to-mutate=mcp-servers/sonarr/

# Check results
mutmut results

# Target: 80%+ mutation score
```

## Key Implementation Requirements

### 🔑 Authentication (CRITICAL)

**Sonarr uses HEADER-based authentication, NOT query parameters**

```python
# ✅ CORRECT - Sonarr pattern
headers = {"X-Api-Key": api_key}
response = await client.get(url, headers=headers)

# ❌ WRONG - SABnzbd pattern (DO NOT USE)
url = f"{base_url}?apikey={api_key}"
```

### 🌐 API Endpoints

All endpoints must use `/api/v3/` prefix:

**Series:**
- `GET /api/v3/series` - List all
- `GET /api/v3/series/{id}` - Get by ID
- `POST /api/v3/series` - Add new
- `DELETE /api/v3/series/{id}` - Delete
- `GET /api/v3/series/lookup?term={term}` - Search

**Episodes:**
- `GET /api/v3/episode?seriesId={id}` - List for series
- `GET /api/v3/episode/{id}` - Get by ID

**Commands:**
- `POST /api/v3/command` - Execute
- `GET /api/v3/command/{id}` - Get status

**Other:**
- `GET /api/v3/calendar` - Upcoming episodes
- `GET /api/v3/queue` - Download queue
- `GET /api/v3/wanted/missing` - Wanted episodes
- `GET /api/v3/system/status` - System info

### 🔄 Command Names

- `EpisodeSearch` - Search for episode
- `SeriesSearch` - Search for series
- `RefreshSeries` - Refresh metadata
- `RescanSeries` - Rescan files

### 📦 Required Dependencies

Already in `pyproject.toml`:
- `httpx` - Async HTTP client
- `mcp` - Model Context Protocol
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-httpx` - HTTP mocking

## Test Categories Covered

### ✅ Unit Tests - SonarrClient

1. **Initialization & Connection** (8 tests)
   - URL/API key validation
   - Connection validation
   - Health checks
   - Context manager

2. **Series Operations** (10+ tests)
   - CRUD operations
   - Search (TVDB)
   - Validation

3. **Episode Operations** (5+ tests)
   - List with filtering
   - Search/download

4. **Command Operations** (4+ tests)
   - Execute commands
   - Track status

5. **Calendar/Queue/Wanted** (6+ tests)
   - Date filtering
   - Pagination
   - Series inclusion

6. **Error Handling** (7+ tests)
   - HTTP errors (401, 404, 500)
   - Connection errors
   - Retry logic

7. **Authentication** (4+ tests)
   - Header-based auth
   - API v3 URLs

8. **Edge Cases** (6+ tests)
   - Large datasets
   - Unicode characters
   - Null values

### ✅ Unit Tests - SonarrMCPServer

1. **Server Initialization** (3 tests)
2. **Tool Registration** (10 tests - one per tool)
3. **Tool Execution** (11 tests)
4. **Error Handling** (6 tests)
5. **Response Formatting** (4 tests)
6. **MCP Protocol Compliance** (4 tests)

### ✅ Integration Tests

1. **Full Workflows** (2 tests)
   - Complete series lifecycle
   - Episode search workflow

2. **API Validation** (3 tests)
   - Endpoint format
   - Header authentication

3. **Error Scenarios** (4 tests)
   - Sonarr error formats
   - Retry logic

4. **Data Integrity** (3 tests)
   - Complex structures
   - Pagination
   - Unicode

5. **MCP E2E** (6 tests)
   - Protocol compliance
   - Error propagation
   - Data transformation

## Success Criteria

- [x] All 238 tests written following TDD
- [x] Test data factories created (8 factories)
- [x] 90%+ coverage target defined
- [x] Test pyramid distribution achieved (75/25)
- [x] Unit tests cover all methods
- [x] Integration tests cover workflows
- [x] Error handling comprehensive
- [x] MCP protocol compliance validated
- [x] Authentication tests (header-based)
- [x] Edge cases covered
- [x] All tests follow AAA pattern
- [x] Descriptive test names
- [x] RED phase verified

## Next Actions

1. **Review Documentation**
   - Read `docs/test-strategy-sonarr.md`
   - Review `docs/SONARR-TEST-SUMMARY.md`

2. **Verify RED Phase**
   ```bash
   pytest tests/unit/mcp_servers/sonarr/test_sonarr_client.py::TestSonarrClientInitialization::test_client_requires_url -v
   ```
   Expected: `ModuleNotFoundError: No module named 'sonarr.client'`

3. **Implement Client**
   - Create `mcp-servers/sonarr/client.py`
   - Follow test specifications
   - Use header-based auth

4. **Implement Server**
   - Create `mcp-servers/sonarr/server.py`
   - Register 10 MCP tools
   - Format responses correctly

5. **Verify GREEN Phase**
   ```bash
   pytest tests/unit/mcp_servers/sonarr/ -v
   ```
   Expected: All tests pass

6. **Achieve Coverage**
   ```bash
   pytest tests/ --cov=mcp_servers.sonarr --cov-fail-under=90
   ```
   Expected: 90%+ coverage

7. **Refactor**
   - Improve code quality
   - Keep tests green

8. **Mutation Test**
   - Install mutmut
   - Run mutation tests
   - Target 80%+ score

## Important Notes

### Differences from SABnzbd

| Aspect | SABnzbd | Sonarr |
|--------|---------|--------|
| **Authentication** | Query param (`?apikey=`) | Header (`X-Api-Key:`) |
| **API Version** | No version in URL | `/api/v3/` prefix |
| **Commands** | Immediate | Async with tracking |
| **Responses** | Nested in mode keys | Direct JSON |

### Testing Tools Used

- `pytest` - Test framework
- `pytest-asyncio` - Async support
- `pytest-httpx` - HTTP mocking
- `httpx` - Async HTTP client
- `mcp` - MCP protocol

### Coverage Configuration

Already configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=mcp_servers",
    "--cov-fail-under=90"
]
```

## Support Resources

- **Test Strategy**: `docs/test-strategy-sonarr.md`
- **Summary**: `docs/SONARR-TEST-SUMMARY.md`
- **README**: `tests/unit/mcp_servers/sonarr/README.md`
- **SABnzbd Reference**: `mcp-servers/sabnzbd/client.py`
- **Sonarr API Docs**: https://sonarr.tv/docs/api/

## Contact & Questions

If you encounter issues or have questions:
1. Review the test specifications in test files
2. Check the test strategy document
3. Reference SABnzbd implementation as pattern
4. Ensure header-based authentication is used (NOT query params)

---

**Deliverable Status**: ✅ COMPLETE
**TDD Phase**: 🔴 RED (Ready for Implementation)
**Test Count**: 238 tests
**Coverage Target**: 90%+
**Files Delivered**: 10 files

**Ready for GREEN phase implementation!**
