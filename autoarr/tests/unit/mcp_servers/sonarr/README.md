# Sonarr MCP Server - Test Suite

## Overview

This directory contains comprehensive unit tests for the Sonarr MCP Server, following Test-Driven Development (TDD) principles. All tests were written **BEFORE** implementation to drive the development process through the red-green-refactor cycle.

## Test Structure

### Unit Tests (Current Directory)

#### `test_sonarr_client.py` - Sonarr API Client Tests

**Coverage Target: 90%+**

Comprehensive unit tests for the `SonarrClient` class that handles all HTTP communication with the Sonarr API v3.

**Test Categories:**

- **Initialization & Connection** (8 tests)
  - URL and API key validation
  - Connection validation
  - Health checks
  - Context manager support

- **Series Operations** (10 tests)
  - Get all series
  - Get series by ID
  - Add series with validation
  - Search series (TVDB lookup)
  - Delete series with options

- **Episode Operations** (5 tests)
  - Get episodes (with season filtering)
  - Get episode by ID
  - Search for episodes
  - Command tracking

- **Command Operations** (4 tests)
  - Command execution
  - Command status retrieval
  - Series search command
  - Refresh/rescan commands

- **Calendar, Queue & Wanted** (6 tests)
  - Calendar with date ranges
  - Download queue with pagination
  - Wanted/missing episodes

- **System Status** (1 test)
  - System status retrieval

- **Error Handling** (7 tests)
  - 401 Unauthorized
  - 404 Not Found
  - 500 Server Error
  - Connection timeouts
  - Invalid JSON responses
  - Retry logic
  - Max retry limits

- **Authentication & Request Building** (4 tests)
  - API key in headers (NOT in URL)
  - Correct API v3 URL construction
  - Content-Type headers

- **Resource Management** (3 tests)
  - Connection cleanup
  - HTTP client reuse
  - Concurrent requests

- **Edge Cases** (6 tests)
  - Empty responses
  - Large datasets
  - Special characters
  - Missing optional fields
  - Null values

**Total: 54 unit tests**

#### `test_sonarr_server.py` - Sonarr MCP Server Tests

**Coverage Target: 90%+**

Comprehensive unit tests for the `SonarrMCPServer` class that exposes Sonarr functionality through the Model Context Protocol.

**Test Categories:**

- **Server Initialization** (3 tests)
  - Client requirement validation
  - Proper initialization
  - MCP handler setup

- **Tool Registration** (10 tests)
  - All 10 required tools registered
  - Correct schemas for each tool
  - Required parameter validation

- **Tool Execution** (11 tests)
  - Get series
  - Get series by ID
  - Add series
  - Search series
  - Get episodes (with filtering)
  - Search episode
  - Get wanted (with pagination)
  - Get calendar
  - Get queue
  - Delete series

- **Error Handling** (6 tests)
  - Unknown tool names
  - Client errors
  - Missing required parameters
  - Invalid parameter types
  - Network errors
  - Unexpected exceptions

- **Response Formatting** (4 tests)
  - Success response format
  - Error response format
  - Valid JSON responses
  - Response metadata

- **MCP Protocol Compliance** (4 tests)
  - JSON Schema validation
  - Naming conventions
  - Informative descriptions
  - Parameter documentation

- **Client Integration** (3 tests)
  - Argument passing
  - Response handling
  - Data structure preservation

**Total: 41 unit tests**

### Integration Tests (`../../../integration/mcp_servers/sonarr/`)

#### `test_sonarr_api_integration.py`

**Coverage Target: 20% of total suite**

Integration tests validating client interaction with Sonarr API (mocked at HTTP layer).

**Test Categories:**

- Full Series Lifecycle (2 tests)
  - Search → Add → Get → Delete workflow
  - Episode search and monitoring workflow

- API Endpoint Validation (3 tests)
  - API v3 prefix usage
  - X-Api-Key header verification
  - Content-Type headers

- Error Scenarios (4 tests)
  - Sonarr 404 error format
  - 400 validation errors
  - 401 unauthorized
  - 503 retry logic

- Data Integrity (3 tests)
  - Complex structure preservation
  - Pagination handling
  - Unicode/special characters

- Performance (2 tests)
  - Concurrent requests
  - Large response sets

- Calendar & Queue (2 tests)
  - Date range filtering
  - Queue status monitoring

**Total: 16 integration tests**

#### `test_sonarr_mcp_integration.py`

**Coverage Target: 10% of total suite (E2E)**

End-to-end tests validating MCP protocol compliance and complete workflows.

**Test Categories:**

- E2E MCP Workflows (2 tests)
  - Complete series management via MCP
  - Episode search workflow via MCP

- MCP Protocol Compliance (3 tests)
  - Response format compliance
  - Schema validation enforcement
  - Error response format

- Error Propagation (3 tests)
  - Client errors through MCP
  - Validation errors through MCP
  - Connection errors through MCP

- Data Transformation (2 tests)
  - Complex data preservation
  - Paginated data preservation

- Calendar & Queue via MCP (2 tests)
  - Calendar retrieval
  - Wanted episodes retrieval

- Concurrency (1 test)
  - Concurrent MCP tool calls

**Total: 13 integration tests**

## Test Data Factories

All test data factories are defined in `tests/fixtures/conftest.py`:

### Sonarr Factories

- **`sonarr_series_factory`** - Creates realistic TV series data
- **`sonarr_episode_factory`** - Creates episode data with optional files
- **`sonarr_quality_profile_factory`** - Creates quality profiles
- **`sonarr_command_factory`** - Creates command responses
- **`sonarr_calendar_factory`** - Creates calendar/upcoming episodes
- **`sonarr_queue_factory`** - Creates download queue data
- **`sonarr_wanted_factory`** - Creates wanted/missing episodes
- **`sonarr_system_status_factory`** - Creates system status responses

## Running Tests

### Run All Sonarr Tests

```bash
pytest tests/unit/mcp_servers/sonarr/ tests/integration/mcp_servers/sonarr/ -v
```

### Run Unit Tests Only

```bash
pytest tests/unit/mcp_servers/sonarr/ -v
```

### Run Integration Tests Only

```bash
pytest tests/integration/mcp_servers/sonarr/ -v
```

### Run with Coverage

```bash
pytest tests/unit/mcp_servers/sonarr/ tests/integration/mcp_servers/sonarr/ \
  --cov=mcp_servers.sonarr \
  --cov-report=term-missing \
  --cov-report=html
```

### Run Specific Test Class

```bash
pytest tests/unit/mcp_servers/sonarr/test_sonarr_client.py::TestSonarrClientSeriesOperations -v
```

### Run Specific Test

```bash
pytest tests/unit/mcp_servers/sonarr/test_sonarr_client.py::TestSonarrClientSeriesOperations::test_add_series_sends_correct_payload -v
```

## Test Coverage Summary

**Total Test Count: 124 tests**

- Unit Tests: 95 (77%)
- Integration Tests: 29 (23%)

**Coverage Distribution:**

- Client Unit Tests: 54 tests
- Server Unit Tests: 41 tests
- API Integration Tests: 16 tests
- MCP Integration Tests: 13 tests

**Expected Coverage: 90%+**

## TDD Red-Green-Refactor Process

### RED Phase (Current State)

All tests are currently written and **will fail** because the implementation doesn't exist yet.

To verify red phase:

```bash
pytest tests/unit/mcp_servers/sonarr/ -v
# Expected: All tests fail with ImportError or similar
```

### GREEN Phase (Next Step)

1. Create `mcp-servers/sonarr/client.py` with `SonarrClient` class
2. Create `mcp-servers/sonarr/server.py` with `SonarrMCPServer` class
3. Implement minimum code to make tests pass

Expected outcome:

```bash
pytest tests/unit/mcp_servers/sonarr/ -v
# Expected: All tests pass
```

### REFACTOR Phase (After Green)

1. Improve code quality
2. Extract common patterns
3. Add type hints
4. Optimize performance
5. Ensure tests still pass

## Key Implementation Requirements

Based on the tests, the implementation must include:

### SonarrClient (`mcp-servers/sonarr/client.py`)

- Header-based authentication (X-Api-Key, NOT query params)
- API v3 endpoint support (`/api/v3/...`)
- Retry logic for transient errors (503)
- Async/await support
- Context manager support
- Exception classes: `SonarrClientError`, `SonarrConnectionError`

**Required Methods:**

- `health_check()` → bool
- `get_series()` → List[Dict]
- `get_series_by_id(series_id)` → Dict
- `add_series(series_data)` → Dict
- `search_series(term)` → List[Dict]
- `delete_series(series_id, delete_files, add_import_exclusion)` → Dict
- `get_episodes(series_id, season_number)` → List[Dict]
- `get_episode_by_id(episode_id)` → Dict
- `search_episode(episode_id)` → Dict
- `_execute_command(name, body)` → Dict
- `get_command(command_id)` → Dict
- `search_series_command(series_id)` → Dict
- `refresh_series(series_id)` → Dict
- `rescan_series(series_id)` → Dict
- `get_calendar(start_date, end_date)` → List[Dict]
- `get_queue(page, page_size)` → Dict
- `get_wanted_missing(page, page_size, include_series)` → Dict
- `get_system_status()` → Dict

### SonarrMCPServer (`mcp-servers/sonarr/server.py`)

- MCP protocol compliance
- 10 registered tools
- Error handling and response formatting
- JSON response format: `{"success": bool, "data": Any, "error": str}`

**Required Tools:**

1. `sonarr_get_series`
2. `sonarr_get_series_by_id` (requires: series_id)
3. `sonarr_add_series` (requires: tvdb_id, quality_profile_id, root_folder_path)
4. `sonarr_search_series` (requires: term)
5. `sonarr_get_episodes` (requires: series_id, optional: season_number)
6. `sonarr_search_episode` (requires: episode_id)
7. `sonarr_get_wanted` (optional: page, page_size, include_series)
8. `sonarr_get_calendar` (optional: start_date, end_date)
9. `sonarr_get_queue` (optional: page, page_size)
10. `sonarr_delete_series` (requires: series_id, optional: delete_files, add_import_exclusion)

## Authentication Pattern

**Critical: Sonarr uses header-based authentication, NOT query parameters**

```python
# CORRECT (Sonarr)
headers = {"X-Api-Key": api_key}
response = await client.get(url, headers=headers)

# WRONG (SABnzbd pattern - DO NOT USE)
url = f"{base_url}?apikey={api_key}"
```

## API Endpoint Reference

All endpoints use the `/api/v3/` prefix:

- `GET /api/v3/series` - List all series
- `GET /api/v3/series/{id}` - Get series by ID
- `POST /api/v3/series` - Add new series
- `DELETE /api/v3/series/{id}?deleteFiles={bool}` - Delete series
- `GET /api/v3/series/lookup?term={term}` - Search for series
- `GET /api/v3/episode?seriesId={id}&seasonNumber={num}` - Get episodes
- `GET /api/v3/episode/{id}` - Get episode by ID
- `POST /api/v3/command` - Execute command
- `GET /api/v3/command/{id}` - Get command status
- `GET /api/v3/calendar?start={date}&end={date}` - Get calendar
- `GET /api/v3/queue?page={num}&pageSize={num}` - Get download queue
- `GET /api/v3/wanted/missing?page={num}&pageSize={num}` - Get wanted episodes
- `GET /api/v3/system/status` - Get system status

## Notes

- All tests use `pytest-asyncio` for async test support
- All HTTP mocking uses `pytest-httpx` (HTTPXMock fixture)
- Test data factories are reusable and composable
- Tests cover both happy paths and error scenarios
- Edge cases include Unicode, special characters, large datasets, and null values
- Integration tests validate real API workflows
- MCP integration tests ensure protocol compliance

## Next Steps

1. **Verify Red Phase**: Run tests to confirm they all fail
2. **Implement Client**: Create `SonarrClient` class
3. **Implement Server**: Create `SonarrMCPServer` class
4. **Verify Green Phase**: Run tests to confirm they all pass
5. **Refactor**: Improve code quality while keeping tests green
6. **Add Mutation Testing**: Use mutmut or pytest-mutagen for test quality validation
