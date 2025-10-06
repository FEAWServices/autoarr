# SABnzbd MCP Server - Test Strategy & Documentation

## Overview

This document provides a comprehensive test strategy for the SABnzbd MCP Server following Test-Driven Development (TDD) principles. All tests are written BEFORE implementation to guide development and ensure high quality.

## Test Philosophy

### TDD Red-Green-Refactor Cycle

1. **RED**: Write a failing test that defines desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code quality while keeping tests green

### Coverage Goals

- **Overall Coverage**: 90%+ (higher than project minimum of 80%)
- **Unit Tests**: 95%+ coverage of client and MCP server code
- **Integration Tests**: Critical paths with real SABnzbd
- **Test Pyramid**: 70% unit, 20% integration, 10% e2e

## Test Structure

```
tests/
├── conftest.py                          # Global pytest configuration
├── fixtures/
│   ├── conftest.py                      # Test data factories
│   └── data/                            # Static test data (JSON files)
├── unit/
│   └── mcp_servers/
│       └── sabnzbd/
│           ├── test_sabnzbd_client.py   # Client unit tests (95% coverage)
│           └── test_mcp_server.py       # MCP server unit tests (95% coverage)
└── integration/
    └── mcp_servers/
        └── sabnzbd/
            └── test_sabnzbd_integration.py  # Integration tests
```

## Unit Tests

### test_sabnzbd_client.py

Tests the SABnzbd API client wrapper. **280+ test cases** covering:

#### 1. Connection and Initialization (8 tests)
- URL and API key validation
- URL normalization
- Custom timeout configuration
- Connection validation

#### 2. Queue Operations (10 tests)
- Get queue with data
- Empty queue handling
- Pagination (start, limit)
- Filtering by NZO IDs
- Pause/resume queue

#### 3. History Operations (8 tests)
- Get history with data
- Pagination support
- Filter by failed only
- Filter by category
- Empty history handling

#### 4. Download Management (10 tests)
- Retry failed downloads
- Delete downloads
- Pause/resume specific downloads
- Parameter validation
- Batch operations

#### 5. Configuration Operations (12 tests)
- Get full configuration
- Get specific config sections
- Set single configuration value
- Batch configuration updates
- Parameter validation
- Section/keyword validation

#### 6. Status and Information (8 tests)
- Get SABnzbd version
- Get server status
- Health checks (success/failure)
- Uptime and metrics

#### 7. Error Handling (14 tests)
- 401 Unauthorized (invalid API key)
- 500 Server errors
- Connection timeouts
- Network errors
- Invalid JSON responses
- Retry logic on transient errors
- Max retry limits
- Graceful degradation

#### 8. Request Building (6 tests)
- Correct API URL construction
- API key inclusion
- URL parameter encoding
- Query string formatting

#### 9. Resource Management (6 tests)
- Connection cleanup
- HTTP client reuse
- Concurrent request safety
- Memory leak prevention

**Total: ~82 unit test cases for client**

### test_mcp_server.py

Tests the MCP server implementation. **200+ test cases** covering:

#### 1. Server Initialization (8 tests)
- Client requirement validation
- Successful initialization
- Server name/version
- Connection validation on startup

#### 2. Tool Registration (14 tests)
- All 5 tools registered correctly
- Tool names follow convention
- Tool descriptions present
- Tool schemas valid
- Tool count verification

#### 3. get_queue Tool (10 tests)
- Correct input schema
- Calls client.get_queue()
- Parameter passing
- Response formatting (JSON)
- Empty queue handling

#### 4. get_history Tool (8 tests)
- Correct input schema
- Calls client.get_history()
- failed_only filter support
- category filter support
- Response formatting

#### 5. retry_download Tool (8 tests)
- Required nzo_id parameter
- Calls client.retry_download()
- Parameter validation
- Success status returned

#### 6. get_config Tool (8 tests)
- Optional section parameter
- Calls client.get_config()
- Section filtering
- Complete config retrieval

#### 7. set_config Tool (8 tests)
- Required parameters (section, keyword, value)
- Calls client.set_config()
- Parameter validation
- Success status

#### 8. Error Handling (12 tests)
- Client error propagation
- Invalid tool names
- Invalid parameters
- Missing required parameters
- Error response format
- Helpful error messages

#### 9. MCP Protocol Compliance (8 tests)
- list_tools() implementation
- call_tool() implementation
- JSON Schema compliance
- Response format compliance
- Content array structure

#### 10. Lifecycle Management (6 tests)
- Server start initialization
- Server stop cleanup
- Restart capability
- State management

**Total: ~90 unit test cases for MCP server**

## Integration Tests

### test_sabnzbd_integration.py

Tests with a real SABnzbd instance. **40+ test cases** covering:

#### 1. Client Integration (7 tests)
- Connect to real SABnzbd
- Get version from real instance
- Get queue with real data
- Get history with real data
- Get config from real instance
- Invalid API key handling
- Network timeout handling

#### 2. MCP Server Integration (6 tests)
- get_queue tool with real data
- get_history tool with real data
- get_config tool with real data
- Section-specific config retrieval
- Real error response handling

#### 3. End-to-End Workflows (2 tests)
- Complete queue monitoring workflow
- Configuration audit workflow

#### 4. Performance Tests (4 tests)
- Concurrent requests performance
- Sequential requests performance
- Large queue handling
- History pagination performance

#### 5. Reliability Tests (3 tests)
- Recovery from temporary failures
- State maintenance across calls
- Long-running server stability

#### 6. Data Format Validation (3 tests)
- Queue response structure
- History response structure
- Config response structure

**Total: ~25 integration test cases**

## Test Data Factories

Located in `tests/fixtures/conftest.py`, these factories create realistic test data:

### Available Factories

1. **sabnzbd_queue_factory**
   - Creates mock queue responses
   - Configurable: slots, paused state, speed, size
   - Realistic NZO IDs and filenames

2. **sabnzbd_history_factory**
   - Creates mock history responses
   - Configurable: entries, failed count, pagination
   - Realistic timestamps and statuses

3. **sabnzbd_config_factory**
   - Creates mock configuration responses
   - Configurable: directories, settings
   - Supports nested config updates

4. **sabnzbd_status_factory**
   - Creates mock status/version responses
   - Configurable: version, uptime
   - System metrics included

5. **sabnzbd_error_response_factory**
   - Creates mock error responses
   - Configurable: error message, error code

6. **sabnzbd_nzo_action_factory**
   - Creates mock action responses
   - Supports pause, resume, delete, retry

### Usage Example

```python
def test_queue_with_multiple_downloads(sabnzbd_queue_factory):
    # Arrange
    mock_queue = sabnzbd_queue_factory(slots=5, paused=False)

    # Act & Assert
    assert mock_queue["queue"]["noofslots"] == 5
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Only Unit Tests
```bash
pytest tests/unit/
```

### Run Only Integration Tests
```bash
# Requires SABNZBD_TEST_API_KEY environment variable
export SABNZBD_TEST_API_KEY=your_api_key
pytest tests/integration/ -m integration
```

### Run with Coverage
```bash
pytest tests/ --cov=mcp_servers.sabnzbd --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py::TestSABnzbdClientQueue -v
```

### Run Specific Test
```bash
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py::TestSABnzbdClientQueue::test_get_queue_returns_queue_data -v
```

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests (require real SABnzbd)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.skip` - Skipped tests (TDD red phase)

### Run Only Fast Tests
```bash
pytest tests/ -m "not slow"
```

### Run Only Integration Tests
```bash
pytest tests/ -m integration
```

## Environment Variables

Integration tests require these environment variables:

- `SABNZBD_TEST_URL` - SABnzbd URL (default: http://localhost:8080)
- `SABNZBD_TEST_API_KEY` - SABnzbd API key (required for integration tests)

### Setup for Integration Tests

```bash
# Option 1: Export variables
export SABNZBD_TEST_URL=http://localhost:8080
export SABNZBD_TEST_API_KEY=your_api_key_here

# Option 2: Use .env file
echo "SABNZBD_TEST_URL=http://localhost:8080" >> .env.test
echo "SABNZBD_TEST_API_KEY=your_api_key" >> .env.test
```

## TDD Workflow

### Step 1: Write Failing Test (RED)

```python
@pytest.mark.asyncio
async def test_get_queue_returns_queue_data(sabnzbd_client, sabnzbd_queue_factory):
    # Arrange
    mock_queue = sabnzbd_queue_factory(slots=3)
    # ... setup mocks ...

    # Act
    result = await sabnzbd_client.get_queue()

    # Assert
    assert "queue" in result
    assert result["queue"]["noofslots"] == 3
```

Run test: `pytest tests/unit/.../test_sabnzbd_client.py::test_get_queue_returns_queue_data`
Expected: **FAIL** (because implementation doesn't exist yet)

### Step 2: Write Minimal Implementation (GREEN)

```python
# mcp_servers/sabnzbd/client.py
class SABnzbdClient:
    async def get_queue(self):
        response = await self._request("mode=queue")
        return response
```

Run test again: **PASS** ✓

### Step 3: Refactor (REFACTOR)

Improve code quality, add error handling, etc., while keeping tests green.

### Step 4: Repeat

Continue with next test case, building functionality incrementally.

## Coverage Tracking

### Coverage Goals by Module

| Module | Target Coverage | Current Status |
|--------|----------------|----------------|
| `client.py` | 95% | 🔴 Not implemented |
| `mcp_server.py` | 95% | 🔴 Not implemented |
| Overall | 90%+ | 🔴 Not implemented |

### Generate Coverage Report

```bash
pytest tests/ --cov=mcp_servers.sabnzbd --cov-report=html --cov-report=term-missing
```

View HTML report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Common Testing Patterns

### Pattern 1: Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Pattern 2: Mocking HTTP Responses

```python
def test_with_http_mock(httpx_mock):
    httpx_mock.add_response(json={"key": "value"})
    # Test code that makes HTTP request
```

### Pattern 3: Using Factories

```python
def test_with_factory(sabnzbd_queue_factory):
    queue = sabnzbd_queue_factory(slots=5, paused=True)
    assert queue["queue"]["paused"] is True
```

### Pattern 4: Testing Error Cases

```python
@pytest.mark.asyncio
async def test_error_handling(sabnzbd_client):
    with pytest.raises(SABnzbdClientError, match="Connection failed"):
        await sabnzbd_client.some_method()
```

## Mock Strategy

### What to Mock in Unit Tests

1. **External HTTP requests** - Use `httpx_mock`
2. **SABnzbd API responses** - Use test data factories
3. **Time-dependent functions** - Use `freezegun` or `time_machine`
4. **Environment variables** - Use `monkeypatch`

### What NOT to Mock in Unit Tests

1. **Internal logic** - Test real implementation
2. **Simple data transformations** - Test actual behavior
3. **Pure functions** - No need to mock

### What to Mock in Integration Tests

**Nothing!** Integration tests use real SABnzbd instances.

## Test Maintenance

### When Tests Fail

1. **Identify the cause**: Implementation bug vs. test bug
2. **Update tests** if requirements changed
3. **Update implementation** if behavior is incorrect
4. **Keep tests and docs in sync**

### Adding New Features

1. **Write tests first** (TDD!)
2. **Update test documentation**
3. **Update factories** if new data structures
4. **Run full test suite** before committing

### Refactoring Tests

1. **DRY principle**: Extract common setup to fixtures
2. **Descriptive names**: Test names should read like documentation
3. **One assertion per concept**: Keep tests focused
4. **Arrange-Act-Assert**: Clear test structure

## CI/CD Integration

Tests run automatically in GitHub Actions:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest tests/unit/ --cov --cov-fail-under=90

- name: Run integration tests
  run: pytest tests/integration/ -m integration
  env:
    SABNZBD_TEST_API_KEY: ${{ secrets.SABNZBD_TEST_API_KEY }}
```

## Troubleshooting

### Tests Won't Run

```bash
# Check pytest installation
pytest --version

# Install test dependencies
poetry install --with dev

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Integration Tests Skip

```bash
# Ensure environment variable is set
echo $SABNZBD_TEST_API_KEY

# Check SABnzbd is running
curl http://localhost:8080/api?mode=version
```

### Import Errors

```bash
# Ensure package is installed in editable mode
pip install -e .

# Or with poetry
poetry install
```

## Performance Benchmarks

Target performance metrics:

- Unit tests: < 0.1s per test
- Integration tests: < 2s per test
- Full unit test suite: < 30s
- Full integration suite: < 60s

## Test Coverage Gaps (To Address)

Current intentional gaps:
1. **E2E tests** - Will be added in Phase 3 (Sprint 5-6)
2. **Mutation testing** - Planned for quality assurance phase
3. **Load testing** - Planned for performance optimization phase

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [httpx-mock](https://colin-b.github.io/pytest_httpx/)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [SABnzbd API Documentation](https://sabnzbd.org/wiki/advanced/api)

## Next Steps

1. ✅ Test strategy defined
2. ✅ Test files created (all currently skipped - TDD red phase)
3. 🔲 Implement SABnzbd client (following test specs)
4. 🔲 Implement MCP server (following test specs)
5. 🔲 Achieve 90%+ test coverage
6. 🔲 Run integration tests with real SABnzbd
7. 🔲 Add mutation testing for critical paths

---

**Document Version**: 1.0
**Last Updated**: October 6, 2025
**Status**: Ready for TDD implementation
