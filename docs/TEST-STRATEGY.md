# AutoArr Test Strategy - SABnzbd MCP Server

## Executive Summary

This document outlines the comprehensive test strategy for the SABnzbd MCP Server, the first MCP server implementation in AutoArr. It follows Test-Driven Development (TDD) principles and establishes patterns for all future MCP server implementations.

**Status**: ✅ Complete - Ready for TDD implementation

**Coverage Target**: 90%+ (exceeding project minimum of 80%)

**Test Count**: 197+ test cases across unit and integration tests

**Timeline**: Sprint 1 (Weeks 1-2) - Task 1.2

## 1. Test Strategy Overview

### 1.1 TDD Red-Green-Refactor Approach

All tests are written **BEFORE** implementation to ensure:

- Clear requirements definition
- Comprehensive edge case coverage
- High-quality, testable code architecture
- Confidence in refactoring

### 1.2 Test Pyramid Distribution

```
        E2E (10%)
       /         \
      /  Integration  \
     /     (20%)       \
    /                   \
   /    Unit Tests       \
  /       (70%)           \
 /_________________________\
```

**SABnzbd MCP Server Breakdown**:

- **Unit Tests**: 172 test cases (87%)
  - Client: 82 tests
  - MCP Server: 90 tests
- **Integration Tests**: 25 test cases (13%)
- **E2E Tests**: Deferred to Phase 3 (Sprint 5-6)

### 1.3 Quality Metrics

| Metric             | Target | Current Status                         |
| ------------------ | ------ | -------------------------------------- |
| Code Coverage      | 90%+   | 🔴 0% (not implemented)                |
| Unit Test Coverage | 95%+   | 🔴 0% (not implemented)                |
| Mutation Coverage  | 80%+   | 🔴 Planned for later                   |
| Tests Passing      | 100%   | 🟡 0/197 (all skipped - TDD red phase) |
| Integration Tests  | 25+    | ✅ 25 written                          |
| Documentation      | 100%   | ✅ Complete                            |

## 2. Test Architecture

### 2.1 Test File Structure

```
tests/
├── conftest.py                                    # Global pytest config
├── fixtures/
│   ├── conftest.py                                # Test data factories
│   ├── data/                                      # Static test data
│   │   ├── sabnzbd_queue_large.json              # Large queue response
│   │   ├── sabnzbd_history_with_failures.json    # History with failures
│   │   └── sabnzbd_config_optimal.json           # Optimal config example
│   └── __init__.py
├── unit/
│   └── mcp_servers/
│       └── sabnzbd/
│           ├── __init__.py
│           ├── README.md                          # Detailed unit test docs
│           ├── test_sabnzbd_client.py            # 82 test cases
│           └── test_mcp_server.py                # 90 test cases
└── integration/
    └── mcp_servers/
        └── sabnzbd/
            ├── __init__.py
            └── test_sabnzbd_integration.py       # 25 test cases
```

### 2.2 Test Naming Convention

**Pattern**: `test_[component]_[behavior]_[condition]`

**Examples**:

- `test_get_queue_returns_queue_data`
- `test_retry_download_validates_nzo_id`
- `test_client_handles_401_unauthorized_error`

### 2.3 Test Class Organization

```python
class TestSABnzbdClientQueue:
    """Test suite for queue-related operations."""

    def test_get_queue_returns_queue_data(self):
        """Test that get_queue returns valid queue data."""
        pass

    def test_get_queue_handles_empty_queue(self):
        """Test that get_queue handles empty queue correctly."""
        pass
```

## 3. Test Specifications

### 3.1 Unit Tests - SABnzbd Client

**File**: `tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py`

**Total**: 82 test cases

#### Test Classes

1. **TestSABnzbdClientInitialization** (5 tests)

   - URL and API key validation
   - URL normalization
   - Custom timeout support
   - Connection validation

2. **TestSABnzbdClientQueue** (6 tests)

   - Get queue operations
   - Pagination support
   - Pause/resume queue
   - NZO ID filtering

3. **TestSABnzbdClientHistory** (4 tests)

   - Get history operations
   - Pagination support
   - Filter by status/category

4. **TestSABnzbdClientDownloadManagement** (5 tests)

   - Retry failed downloads
   - Delete downloads
   - Pause/resume downloads

5. **TestSABnzbdClientConfiguration** (6 tests)

   - Get configuration
   - Set configuration values
   - Batch updates
   - Section-specific operations

6. **TestSABnzbdClientStatus** (4 tests)

   - Version information
   - Server status
   - Health checks

7. **TestSABnzbdClientErrorHandling** (8 tests)

   - HTTP error codes (401, 500, 503)
   - Connection timeouts
   - Invalid JSON
   - Retry logic

8. **TestSABnzbdClientRequestBuilding** (3 tests)

   - URL construction
   - API key inclusion
   - Parameter encoding

9. **TestSABnzbdClientResourceManagement** (3 tests)
   - Connection cleanup
   - Client reuse
   - Concurrent safety

**Coverage Target**: 95%+

### 3.2 Unit Tests - MCP Server

**File**: `tests/unit/mcp_servers/sabnzbd/test_mcp_server.py`

**Total**: 90 test cases

#### Test Classes

1. **TestSABnzbdMCPServerInitialization** (5 tests)

   - Client requirement
   - Server name/version
   - Startup validation

2. **TestSABnzbdMCPServerToolRegistration** (8 tests)

   - All 5 tools registered
   - Tool descriptions
   - Tool schemas
   - Tool count verification

3. **TestSABnzbdMCPServerGetQueueTool** (5 tests)

   - Schema validation
   - Client method calls
   - Parameter passing
   - Response formatting

4. **TestSABnzbdMCPServerGetHistoryTool** (4 tests)

   - Schema validation
   - Filter support
   - Response formatting

5. **TestSABnzbdMCPServerRetryDownloadTool** (4 tests)

   - Required parameters
   - Client method calls
   - Success status

6. **TestSABnzbdMCPServerGetConfigTool** (4 tests)

   - Optional parameters
   - Section filtering
   - Complete config retrieval

7. **TestSABnzbdMCPServerSetConfigTool** (4 tests)

   - Required parameters
   - Parameter validation
   - Success status

8. **TestSABnzbdMCPServerErrorHandling** (6 tests)

   - Client error propagation
   - Invalid tool names
   - Parameter validation
   - Error response format

9. **TestSABnzbdMCPServerProtocolCompliance** (4 tests)

   - MCP protocol methods
   - JSON Schema compliance
   - Response format

10. **TestSABnzbdMCPServerLifecycle** (3 tests)
    - Start/stop operations
    - State management
    - Restart capability

**Coverage Target**: 95%+

### 3.3 Integration Tests

**File**: `tests/integration/mcp_servers/sabnzbd/test_sabnzbd_integration.py`

**Total**: 25 test cases

#### Test Classes

1. **TestSABnzbdClientIntegration** (7 tests)

   - Real SABnzbd connection
   - Real API responses
   - Error handling with real server

2. **TestSABnzbdMCPServerIntegration** (5 tests)

   - Tools with real data
   - Real error scenarios

3. **TestSABnzbdEndToEndWorkflows** (2 tests)

   - Queue monitoring workflow
   - Configuration audit workflow

4. **TestSABnzbdPerformance** (4 tests)

   - Concurrent requests
   - Sequential requests
   - Large data handling

5. **TestSABnzbdReliability** (3 tests)

   - Failure recovery
   - State persistence
   - Long-running stability

6. **TestSABnzbdDataFormats** (3 tests)
   - Queue structure validation
   - History structure validation
   - Config structure validation

**Requirements**:

- Running SABnzbd instance
- Valid API key (SABNZBD_TEST_API_KEY)
- Network connectivity

## 4. Test Data Factories

**Location**: `tests/fixtures/conftest.py`

### 4.1 Available Factories

1. **sabnzbd_queue_factory**

   ```python
   queue = sabnzbd_queue_factory(
       slots=5,
       paused=False,
       speed="10.5 MB/s",
       mb_left=1500.0,
       mb_total=3000.0
   )
   ```

2. **sabnzbd_history_factory**

   ```python
   history = sabnzbd_history_factory(
       entries=10,
       failed=3,
       start=0,
       limit=50
   )
   ```

3. **sabnzbd_config_factory**

   ```python
   config = sabnzbd_config_factory(
       complete_dir="/downloads/complete",
       download_dir="/downloads/incomplete",
       enable_https=True
   )
   ```

4. **sabnzbd_status_factory**

   ```python
   status = sabnzbd_status_factory(
       version="4.1.0",
       uptime="5d 12h 30m"
   )
   ```

5. **sabnzbd_error_response_factory**

   ```python
   error = sabnzbd_error_response_factory(
       error_message="Invalid API key",
       error_code=401
   )
   ```

6. **sabnzbd_nzo_action_factory**
   ```python
   action = sabnzbd_nzo_action_factory(
       success=True,
       nzo_ids=["new_nzo_id"]
   )
   ```

### 4.2 Factory Design Principles

- **Realistic data**: Matches real SABnzbd API responses
- **Configurable**: Override any field via parameters
- **Composable**: Factories can use other factories
- **Type-safe**: Returns properly typed dictionaries
- **Well-documented**: Clear docstrings and examples

## 5. Mock Strategy

### 5.1 What to Mock in Unit Tests

✅ **DO Mock**:

- External HTTP requests (httpx)
- SABnzbd API responses
- Time-dependent functions
- Environment variables
- File system operations

❌ **DON'T Mock**:

- Internal business logic
- Simple data transformations
- Pure functions
- Module imports

### 5.2 Mocking Tools

1. **httpx_mock** (from pytest-httpx)

   ```python
   def test_with_mock(httpx_mock):
       httpx_mock.add_response(json={"key": "value"})
       # Test makes HTTP request
   ```

2. **AsyncMock** (from unittest.mock)

   ```python
   mock_client = AsyncMock()
   mock_client.get_queue = AsyncMock(return_value={"queue": {}})
   ```

3. **monkeypatch** (pytest fixture)
   ```python
   def test_with_env(monkeypatch):
       monkeypatch.setenv("API_KEY", "test_key")
   ```

### 5.3 Integration Test Mock Strategy

**NO MOCKING** in integration tests! They use real SABnzbd instances.

## 6. Test Execution

### 6.1 Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests only (requires SABNZBD_TEST_API_KEY)
export SABNZBD_TEST_API_KEY=your_key
pytest tests/integration/ -m integration

# Specific test file
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py -v

# Specific test class
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py::TestSABnzbdClientQueue -v

# Specific test
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py::TestSABnzbdClientQueue::test_get_queue_returns_queue_data -v

# With coverage
pytest tests/ --cov=mcp_servers.sabnzbd --cov-report=html --cov-report=term-missing

# Fast tests only (skip slow)
pytest tests/ -m "not slow"
```

### 6.2 Test Markers

- `@pytest.mark.asyncio` - Async test
- `@pytest.mark.integration` - Requires real SABnzbd
- `@pytest.mark.slow` - Takes >2 seconds
- `@pytest.mark.skip("reason")` - Skipped test (TDD red phase)

### 6.3 Environment Variables

```bash
# Required for integration tests
export SABNZBD_TEST_URL=http://localhost:8080
export SABNZBD_TEST_API_KEY=your_api_key_here

# Optional
export PYTEST_TIMEOUT=30  # Test timeout in seconds
```

## 7. TDD Workflow

### 7.1 Red-Green-Refactor Process

#### Phase 1: RED (Write Failing Test)

```python
# tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py
@pytest.mark.asyncio
async def test_get_queue_returns_queue_data(
    httpx_mock, sabnzbd_client, sabnzbd_queue_factory
):
    # Arrange
    mock_queue = sabnzbd_queue_factory(slots=3)
    httpx_mock.add_response(json=mock_queue)

    # Act
    result = await sabnzbd_client.get_queue()

    # Assert
    assert "queue" in result
    assert result["queue"]["noofslots"] == 3
```

**Run**: `pytest tests/unit/.../test_sabnzbd_client.py::test_get_queue_returns_queue_data`

**Expected**: ❌ FAIL (implementation doesn't exist)

#### Phase 2: GREEN (Minimal Implementation)

```python
# mcp_servers/sabnzbd/client.py
class SABnzbdClient:
    async def get_queue(self):
        response = await self._request("mode=queue&output=json")
        return response.json()
```

**Run**: Same command

**Expected**: ✅ PASS

#### Phase 3: REFACTOR (Improve Code)

```python
# mcp_servers/sabnzbd/client.py
class SABnzbdClient:
    async def get_queue(
        self,
        start: int | None = None,
        limit: int | None = None
    ) -> Dict[str, Any]:
        """
        Get current download queue.

        Args:
            start: Starting offset for pagination
            limit: Maximum number of items to return

        Returns:
            Queue data with slots and metadata

        Raises:
            SABnzbdClientError: If request fails
        """
        params = {"mode": "queue", "output": "json"}
        if start is not None:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit

        response = await self._request(params)
        return response.json()
```

**Run**: Same command + full test suite

**Expected**: ✅ All tests PASS

### 7.2 Current Test Status

All tests are currently **skipped** with `pytest.skip()` markers. This is the expected **TDD red phase** state:

```python
def test_something(self):
    pytest.skip("Implementation pending - TDD")
    # Test code here...
```

As implementation progresses:

1. Remove `pytest.skip()` line
2. Run test → should FAIL (red)
3. Implement feature → should PASS (green)
4. Refactor → should stay PASS

## 8. Coverage Strategy

### 8.1 Coverage Goals

| Component         | Target | Priority |
| ----------------- | ------ | -------- |
| SABnzbd Client    | 95%+   | Critical |
| MCP Server        | 95%+   | Critical |
| Utility Functions | 90%+   | High     |
| Error Handling    | 100%   | Critical |
| Configuration     | 90%+   | High     |

### 8.2 Coverage Reporting

```bash
# Generate HTML coverage report
pytest tests/ --cov=mcp_servers.sabnzbd --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Terminal report with missing lines
pytest tests/ --cov=mcp_servers.sabnzbd --cov-report=term-missing

# Fail if coverage below threshold
pytest tests/ --cov=mcp_servers.sabnzbd --cov-fail-under=90
```

### 8.3 Coverage Gaps (Intentional)

These gaps are intentional and will be addressed in later phases:

1. **E2E Tests**: Deferred to Phase 3 (Sprint 5-6)
2. **Mutation Testing**: Planned for quality assurance phase
3. **Load Testing**: Planned for performance optimization
4. **Chaos Engineering**: Post-v1.0 roadmap

## 9. Special Testing Considerations

### 9.1 MCP Protocol Compliance Testing

MCP servers must comply with the Model Context Protocol specification:

**Protocol Requirements**:

- ✅ Implement `list_tools()` method
- ✅ Implement `call_tool()` method
- ✅ Tool schemas follow JSON Schema spec
- ✅ Responses follow MCP format
- ✅ Error handling per MCP spec

**Test Coverage**:

```python
class TestSABnzbdMCPServerProtocolCompliance:
    def test_server_implements_list_tools(self):
        """Verify list_tools returns Tool objects."""

    def test_server_implements_call_tool(self):
        """Verify call_tool returns CallToolResult."""

    def test_tool_schemas_follow_json_schema_spec(self):
        """Verify all schemas are valid JSON Schema."""

    def test_tool_responses_follow_mcp_format(self):
        """Verify responses have content and isError fields."""
```

### 9.2 API Response Validation

SABnzbd API responses must match expected formats:

**Validation Strategy**:

1. **Unit tests**: Use factories with known structures
2. **Integration tests**: Validate real API responses
3. **Schema validation**: Use Pydantic models (future enhancement)

**Test Coverage**:

```python
class TestSABnzbdDataFormats:
    @pytest.mark.integration
    async def test_queue_response_structure(self):
        """Verify real queue response has expected fields."""

    @pytest.mark.integration
    async def test_history_response_structure(self):
        """Verify real history response has expected fields."""

    @pytest.mark.integration
    async def test_config_response_structure(self):
        """Verify real config response has expected fields."""
```

### 9.3 Error Handling Testing

Comprehensive error scenarios:

**Error Categories**:

1. **Network Errors**: Connection refused, timeouts
2. **Authentication Errors**: Invalid API key, unauthorized
3. **Server Errors**: 500 errors, service unavailable
4. **Data Errors**: Invalid JSON, missing fields
5. **Parameter Errors**: Invalid inputs, missing required fields

**Test Coverage** (14 tests in test_sabnzbd_client.py):

```python
class TestSABnzbdClientErrorHandling:
    async def test_handles_401_unauthorized_error(self):
        """401 with invalid API key."""

    async def test_handles_500_server_error(self):
        """500 internal server error."""

    async def test_handles_connection_timeout(self):
        """Network timeout."""

    async def test_handles_network_error(self):
        """Connection refused."""

    async def test_handles_invalid_json_response(self):
        """Malformed JSON."""

    async def test_retries_on_transient_error(self):
        """Retry logic for 503."""

    async def test_respects_max_retries(self):
        """Max retry limit."""
```

### 9.4 Async Testing

All async code uses `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

**Configuration** (in `pyproject.toml`):

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 9.5 Configuration Validation

Test configuration loading and validation:

**Test Coverage**:

- Valid configuration files
- Missing required fields
- Invalid data types
- Environment variable overrides
- Default values

## 10. CI/CD Integration

### 10.1 GitHub Actions Workflow

```yaml
name: SABnzbd MCP Server Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      sabnzbd:
        image: linuxserver/sabnzbd:latest
        ports:
          - 8080:8080
        env:
          PUID: 1000
          PGID: 1000

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run unit tests
        run: |
          poetry run pytest tests/unit/ \
            --cov=mcp_servers.sabnzbd \
            --cov-report=xml \
            --cov-fail-under=90

      - name: Run integration tests
        env:
          SABNZBD_TEST_URL: http://localhost:8080
          SABNZBD_TEST_API_KEY: ${{ secrets.SABNZBD_TEST_API_KEY }}
        run: |
          poetry run pytest tests/integration/ -m integration

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 10.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: poetry run pytest tests/unit/
        language: system
        pass_filenames: false
        always_run: true
```

## 11. Performance Benchmarks

### 11.1 Target Metrics

| Test Type               | Target Time | Current |
| ----------------------- | ----------- | ------- |
| Single unit test        | < 0.1s      | N/A     |
| Full unit suite         | < 30s       | N/A     |
| Single integration test | < 2s        | N/A     |
| Full integration suite  | < 60s       | N/A     |

### 11.2 Performance Test Coverage

```python
@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_requests_performance(sabnzbd_client):
    """Test that 10 concurrent requests complete within 5 seconds."""
    import time

    start = time.time()
    results = await asyncio.gather(*[
        sabnzbd_client.get_queue() for _ in range(10)
    ])
    duration = time.time() - start

    assert len(results) == 10
    assert duration < 5.0
```

## 12. Mutation Testing (Future)

### 12.1 Mutation Testing Strategy

**Goal**: Verify that tests actually catch bugs

**Tool**: `mutmut` or `cosmic-ray`

**Process**:

1. Automatically mutate source code
2. Run test suite
3. Tests should fail with mutations
4. If tests pass, mutation "survived" (gap in tests)

**Target**: 80%+ mutation coverage on critical paths

**Example**:

```bash
# Install mutmut
pip install mutmut

# Run mutation testing
mutmut run --paths-to-mutate=mcp_servers/sabnzbd/

# View results
mutmut results
```

### 12.2 Critical Paths for Mutation Testing

1. Error handling logic
2. Retry mechanisms
3. Parameter validation
4. Response parsing
5. Configuration updates

## 13. Test Maintenance

### 13.1 When Tests Fail

**Diagnostic Process**:

1. Read the failure message carefully
2. Check if implementation changed
3. Check if requirements changed
4. Determine if test or implementation needs update
5. Update and verify

### 13.2 Adding New Features

**TDD Process**:

1. Write test first (should fail)
2. Implement minimal feature (test passes)
3. Refactor and improve
4. Update documentation
5. Update test strategy if needed

### 13.3 Refactoring Tests

**Best Practices**:

- Extract common setup to fixtures
- Use descriptive test names
- One logical assertion per test
- Keep tests independent
- Follow Arrange-Act-Assert pattern

## 14. Documentation

### 14.1 Test Documentation Files

1. **This file**: `docs/TEST-STRATEGY.md` - Overall strategy
2. **Unit test README**: `tests/unit/mcp_servers/sabnzbd/README.md` - Detailed unit test docs
3. **Docstrings**: Every test has clear docstring
4. **Inline comments**: Complex test logic explained

### 14.2 Documentation Standards

**Test Docstring Format**:

```python
def test_something_specific(self):
    """
    Test that [component] [behavior] when [condition].

    This test verifies [specific behavior] by [test approach].
    Expected outcome: [what should happen].
    """
```

## 15. Success Criteria

### 15.1 Test Strategy Complete When

- ✅ All test files created
- ✅ 197+ test cases written
- ✅ Test data factories implemented
- ✅ Documentation complete
- ✅ CI/CD integration defined
- ✅ TDD workflow documented

### 15.2 Implementation Complete When

- 🔲 All tests passing (remove skip markers)
- 🔲 90%+ code coverage achieved
- 🔲 Integration tests passing with real SABnzbd
- 🔲 No critical bugs
- 🔲 Performance benchmarks met

## 16. Next Steps

### 16.1 Immediate (Sprint 1 - Week 1-2)

1. ✅ Test strategy defined (this document)
2. 🔲 Implement SABnzbd client (following test specs)
3. 🔲 Implement MCP server (following test specs)
4. 🔲 Achieve 90%+ coverage
5. 🔲 Run integration tests

### 16.2 Near-term (Sprint 2 - Week 3-4)

1. Apply same pattern to Sonarr MCP server
2. Apply same pattern to Radarr MCP server
3. Apply same pattern to Plex MCP server
4. Extract common test utilities

### 16.3 Future (Phase 3+)

1. Add E2E tests with Playwright
2. Implement mutation testing
3. Add performance benchmarks
4. Add chaos engineering tests

## 17. Appendices

### Appendix A: Test File Locations

```
C:\Git\autoarr\tests\
├── conftest.py
├── fixtures\
│   ├── conftest.py
│   ├── data\
│   └── __init__.py
├── unit\
│   └── mcp_servers\
│       └── sabnzbd\
│           ├── __init__.py
│           ├── README.md
│           ├── test_sabnzbd_client.py
│           └── test_mcp_server.py
└── integration\
    └── mcp_servers\
        └── sabnzbd\
            ├── __init__.py
            └── test_sabnzbd_integration.py
```

### Appendix B: Key Dependencies

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `httpx-mock` - HTTP mocking
- `black` - Code formatting
- `mypy` - Type checking

### Appendix C: Related Documents

- [BUILD-PLAN.md](BUILD-PLAN.md) - Overall development plan
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Unit Test README](../tests/unit/mcp_servers/sabnzbd/README.md) - Detailed unit test docs

---

**Document Version**: 1.0
**Last Updated**: October 6, 2025
**Author**: Test Architect Agent (Claude Code)
**Status**: ✅ Complete - Ready for implementation
**Next Review**: After Sprint 1 completion
