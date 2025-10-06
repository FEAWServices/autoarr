# MCP Orchestrator Test Strategy

## Executive Summary

This document outlines the comprehensive Test-Driven Development (TDD) strategy for the **MCP Orchestrator** - the critical coordination layer at the heart of AutoArr that manages all MCP server connections (SABnzbd, Sonarr, Radarr, and Plex).

**Coverage Target**: 90%+ code coverage
**Test Pyramid Distribution**: 70% Unit | 20% Integration | 10% E2E
**Total Tests**: 105 tests (75 unit + 30 integration)
**Development Approach**: Red-Green-Refactor TDD

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Test Strategy Overview](#test-strategy-overview)
3. [Test Pyramid Distribution](#test-pyramid-distribution)
4. [Test Specifications](#test-specifications)
5. [Test Data Factories](#test-data-factories)
6. [Mock Strategies](#mock-strategies)
7. [Coverage Plan](#coverage-plan)
8. [Implementation Checklist](#implementation-checklist)
9. [CI/CD Integration](#cicd-integration)
10. [Performance Benchmarks](#performance-benchmarks)

---

## Architecture Overview

### MCP Orchestrator Responsibilities

The MCP Orchestrator is responsible for:

```python
class MCPOrchestrator:
    """
    Orchestrates communication with all MCP servers.

    Core Responsibilities:
    1. Connection Management - Persistent connections with pooling
    2. Tool Routing - Route calls to appropriate servers
    3. Parallel Execution - Execute multiple tools concurrently
    4. Error Handling - Circuit breaker, retries, graceful degradation
    5. Health Monitoring - Continuous health checks
    6. Resource Management - Proper cleanup and lifecycle
    """
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  MCP Orchestrator                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Connection Pool Manager                          │  │
│  ├───────────────────────────────────────────────────┤  │
│  │  Tool Router                                      │  │
│  ├───────────────────────────────────────────────────┤  │
│  │  Circuit Breaker & Retry Logic                   │  │
│  ├───────────────────────────────────────────────────┤  │
│  │  Health Check Monitor                            │  │
│  └───────────────────────────────────────────────────┘  │
└────┬──────────┬──────────┬──────────┬──────────────────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│SABnzbd  ││Sonarr   ││Radarr   ││Plex     │
│MCP      ││MCP      ││MCP      ││MCP      │
│Server   ││Server   ││Server   ││Server   │
└─────────┘└─────────┘└─────────┘└─────────┘
```

---

## Test Strategy Overview

### TDD Approach (Red-Green-Refactor)

All tests in this strategy are written **BEFORE** implementation:

1. **RED Phase** ✗
   - Write failing test
   - Test should fail because feature doesn't exist
   - Validates test is actually testing something

2. **GREEN Phase** ✓
   - Write minimal code to make test pass
   - Focus on functionality, not perfection
   - Get to green as quickly as possible

3. **REFACTOR Phase** ♻
   - Improve code quality
   - Maintain test passing state
   - Refactor with confidence

### Test Categories

| Category | Tests | Coverage Focus | Priority |
|----------|-------|----------------|----------|
| Connection Management | 20 | Connection lifecycle, pooling, reconnection | Critical |
| Tool Routing | 15 | Correct routing, validation, error handling | Critical |
| Parallel Execution | 10 | Concurrency, aggregation, cancellation | High |
| Error Handling | 12 | Circuit breaker, retries, degradation | Critical |
| Health Checks | 8 | Health monitoring, failure detection | High |
| Resource Management | 10 | Cleanup, lifecycle, memory management | High |
| Integration Tests | 30 | Real server interactions, E2E workflows | Medium |

**Total: 105 Tests**

---

## Test Pyramid Distribution

### Target Distribution

```
        ┌───────┐
        │  E2E  │  10% (Integration subset)
        │ Tests │
        └───────┘
      ┌───────────┐
      │Integration│  20% (30 tests)
      │   Tests   │  Real MCP server interactions
      └───────────┘
  ┌─────────────────┐
  │   Unit Tests    │  70% (75 tests)
  │   Fast, Focused │  Mocked dependencies
  └─────────────────┘
```

### Rationale

- **70% Unit Tests**: Fast feedback, isolated testing, drives implementation
- **20% Integration Tests**: Verify real interactions, protocol compliance
- **10% E2E Tests**: End-to-end workflows (subset of integration tests)

### Test Execution Speed

- **Unit Tests**: < 5 seconds total (< 100ms per test)
- **Integration Tests**: < 30 seconds total (~ 1s per test)
- **Full Suite**: < 60 seconds

---

## Test Specifications

### 1. Connection Management Tests (20 tests)

#### 1.1 Initialization Tests (3 tests)

```python
test_orchestrator_initialization_with_config
- Given: Valid configuration object
- When: Create MCPOrchestrator instance
- Then: Orchestrator initializes successfully

test_orchestrator_requires_configuration
- Given: No configuration provided
- When: Attempt to create orchestrator
- Then: Raises ValueError with "config" message

test_orchestrator_validates_config_structure
- Given: Invalid configuration structure
- When: Create orchestrator
- Then: Raises validation error
```

#### 1.2 Connection Tests (8 tests)

```python
test_connect_all_connects_to_all_enabled_servers
- Given: All servers enabled in config
- When: Call connect_all()
- Then: All 4 servers connected successfully

test_connect_all_skips_disabled_servers
- Given: Plex server disabled in config
- When: Call connect_all()
- Then: Only 3 servers connected, plex skipped

test_connect_all_handles_partial_connection_failure
- Given: One server fails to connect
- When: Call connect_all()
- Then: Other servers connect, orchestrator continues

test_connect_all_retries_failed_connections
- Given: Server fails on first attempt
- When: Call connect_all()
- Then: Retries with exponential backoff until success

test_connect_all_respects_max_retries
- Given: Server persistently fails
- When: Call connect_all()
- Then: Stops after max_retries attempts

test_disconnect_all_closes_all_connections
- Given: All servers connected
- When: Call disconnect_all()
- Then: All connections properly closed

test_reconnect_specific_server
- Given: Server was disconnected
- When: Call reconnect(server_name)
- Then: Server reconnects successfully

test_is_connected_returns_connection_status
- Given: Some servers connected
- When: Call is_connected(server_name)
- Then: Returns correct boolean status
```

#### 1.3 Connection Pool Tests (5 tests)

```python
test_connection_pooling_reuses_connections
- Given: Multiple tool calls to same server
- When: Execute calls
- Then: Same connection reused, not recreated

test_connection_pool_limits_concurrent_connections
- Given: Max concurrent = 2
- When: Try 5 concurrent calls
- Then: Only 2 execute simultaneously

test_concurrent_connection_attempts_are_safe
- Given: Multiple connect_all() calls
- When: Execute concurrently
- Then: No race conditions, all succeed

test_connection_timeout_handling
- Given: Server slow to connect
- When: Connection attempt with timeout
- Then: Times out appropriately

test_connection_keepalive_mechanism
- Given: Keepalive enabled
- When: Monitor over time
- Then: Periodic health checks maintain connections
```

#### 1.4 Advanced Connection Tests (4 tests)

```python
test_connection_state_persistence_across_restarts
test_auto_reconnect_on_connection_loss
test_graceful_shutdown_waits_for_pending_requests
test_connection_metrics_tracking
```

### 2. Tool Routing Tests (15 tests)

#### 2.1 Basic Routing (5 tests)

```python
test_call_tool_routes_to_correct_server
- Given: Tool call for "sabnzbd"
- When: call_tool("sabnzbd", "get_queue", {})
- Then: Routes to SABnzbd client only

test_call_tool_validates_server_name
- Given: Invalid server name
- When: call_tool("invalid", "tool", {})
- Then: Raises ValueError

test_call_tool_validates_server_is_connected
- Given: Server not connected
- When: call_tool()
- Then: Raises MCPConnectionError

test_call_tool_validates_tool_name
- Given: Empty tool name
- When: call_tool("sabnzbd", "", {})
- Then: Raises ValueError

test_call_tool_validates_params_type
- Given: Params not a dict
- When: call_tool(..., params="invalid")
- Then: Raises TypeError
```

#### 2.2 Parameter Handling (4 tests)

```python
test_call_tool_passes_params_correctly
test_call_tool_returns_result_data
test_call_tool_handles_tool_not_found_error
test_call_tool_handles_tool_execution_error
```

#### 2.3 Timeout & Configuration (3 tests)

```python
test_call_tool_respects_timeout_parameter
test_call_tool_uses_default_timeout_if_not_specified
test_list_available_tools_for_server
```

#### 2.4 Advanced Routing (3 tests)

```python
test_list_all_tools_across_all_servers
test_tool_routing_with_alias_names
test_call_tool_includes_metadata_in_result
```

### 3. Parallel Execution Tests (10 tests)

```python
test_call_tools_parallel_executes_multiple_calls
test_call_tools_parallel_maintains_call_order
test_call_tools_parallel_handles_mixed_success_failure
test_call_tools_parallel_aggregates_results_correctly
test_call_tools_parallel_respects_individual_timeouts
test_call_tools_parallel_limits_concurrency
test_call_tools_parallel_cancels_pending_on_critical_failure
test_call_tools_parallel_returns_partial_results_on_timeout
test_call_tools_parallel_empty_list_returns_empty_results
test_call_tools_parallel_provides_progress_callback
```

### 4. Error Handling Tests (12 tests)

```python
test_retry_logic_with_exponential_backoff
test_retry_logic_respects_max_retries
test_circuit_breaker_opens_after_failure_threshold
test_circuit_breaker_rejects_calls_when_open
test_circuit_breaker_transitions_to_half_open
test_circuit_breaker_closes_after_successful_calls
test_graceful_degradation_continues_with_available_servers
test_error_aggregation_provides_detailed_failure_info
test_timeout_errors_are_handled_gracefully
test_connection_error_triggers_reconnection_attempt
test_error_callback_is_invoked_on_failures
test_retry_only_on_transient_errors
```

### 5. Health Check Tests (8 tests)

```python
test_health_check_all_returns_status_for_all_servers
test_health_check_all_detects_unhealthy_server
test_health_check_single_server
test_health_check_handles_connection_error
test_health_check_retries_on_transient_failure
test_health_check_marks_server_down_after_failures
test_periodic_health_checks_run_automatically
test_health_check_includes_detailed_diagnostics
```

### 6. Resource Management Tests (10 tests)

```python
test_orchestrator_cleans_up_on_shutdown
test_orchestrator_context_manager_support
test_orchestrator_handles_cleanup_errors
test_resource_leak_detection
test_restart_orchestrator_preserves_configuration
test_orchestrator_memory_usage_stays_bounded
test_proper_task_cleanup_on_cancellation
test_connection_pool_releases_on_error
test_graceful_shutdown_timeout
test_orchestrator_stats_tracking
```

---

## Test Data Factories

### Configuration Factory

```python
@pytest.fixture
def mcp_orchestrator_config_factory():
    """
    Creates complete orchestrator configurations.

    Usage:
        # All servers enabled
        config = mcp_orchestrator_config_factory()

        # With disabled servers
        config = mcp_orchestrator_config_factory(
            disabled_servers=["plex"]
        )

        # With custom settings
        config = mcp_orchestrator_config_factory(
            custom_configs={
                "sabnzbd": {"timeout": 60.0, "max_retries": 5}
            }
        )
    """
```

### Mock Client Factory

```python
@pytest.fixture
def mock_mcp_client_factory():
    """
    Creates mock MCP client instances.

    Usage:
        # Healthy client
        client = mock_mcp_client_factory("sabnzbd")

        # Failing client
        client = mock_mcp_client_factory(
            "sonarr",
            connection_fails=True
        )

        # Unhealthy client
        client = mock_mcp_client_factory(
            "radarr",
            health_check_result=False
        )
    """
```

### Tool Call Factory

```python
@pytest.fixture
def mcp_tool_call_factory():
    """
    Creates tool call objects for testing.

    Usage:
        # Simple call
        call = mcp_tool_call_factory("sabnzbd", "get_queue")

        # With parameters
        call = mcp_tool_call_factory(
            "sonarr",
            "search_series",
            {"query": "Breaking Bad"}
        )

        # With timeout
        call = mcp_tool_call_factory(
            "plex",
            "scan_library",
            {"library_id": 1},
            timeout=5.0
        )
    """
```

### Batch Call Factory

```python
@pytest.fixture
def mcp_batch_tool_calls_factory():
    """
    Creates batches of tool calls for parallel testing.

    Usage:
        # 5 calls across all servers
        calls = mcp_batch_tool_calls_factory(count=5)

        # Specific servers only
        calls = mcp_batch_tool_calls_factory(
            count=3,
            servers=["sabnzbd", "sonarr"]
        )
    """
```

### Error Factory

```python
@pytest.fixture
def connection_error_factory():
    """
    Creates various connection errors for testing.

    Usage:
        error = connection_error_factory("timeout")
        error = connection_error_factory("refused")
        error = connection_error_factory("reset")
    """
```

### Circuit Breaker State Factory

```python
@pytest.fixture
def circuit_breaker_state_factory():
    """
    Creates circuit breaker states for testing.

    Usage:
        state = circuit_breaker_state_factory("closed")
        state = circuit_breaker_state_factory(
            "open",
            failure_count=5
        )
    """
```

---

## Mock Strategies

### 1. Mock MCP Clients

**Strategy**: Use `AsyncMock` to simulate MCP client behavior without real servers.

```python
@pytest.fixture
def mock_mcp_client():
    """Mock a single MCP client."""
    client = AsyncMock()

    # Connection methods
    client.connect = AsyncMock(return_value=True)
    client.disconnect = AsyncMock(return_value=None)
    client.is_connected = AsyncMock(return_value=True)

    # Health check
    client.health_check = AsyncMock(return_value=True)

    # Tool methods
    client.list_tools = AsyncMock(return_value=["tool1", "tool2"])
    client.call_tool = AsyncMock(return_value={"success": True})

    return client
```

### 2. Patch Client Creation

**Strategy**: Patch the `_create_client` method to inject mocks.

```python
with patch.object(orchestrator, "_create_client") as mock_create:
    mock_create.side_effect = lambda name: mock_clients[name]
    await orchestrator.connect_all()
```

### 3. Simulate Failures

**Strategy**: Use `side_effect` to simulate various failure modes.

```python
# Connection failure
mock_client.connect = AsyncMock(
    side_effect=ConnectionError("Connection refused")
)

# Transient failure then success
attempt = 0
async def flaky_connect():
    nonlocal attempt
    attempt += 1
    if attempt < 3:
        raise ConnectionError("Transient")
    return True

mock_client.connect = flaky_connect

# Timeout
async def slow_operation():
    await asyncio.sleep(100)
    return {}

mock_client.call_tool = slow_operation
```

### 4. Track Call Counts

**Strategy**: Use mock call tracking to verify retry logic.

```python
mock_client.connect = AsyncMock(side_effect=ConnectionError())

try:
    await orchestrator.connect_all()
except:
    pass

# Verify retry count
assert mock_client.connect.call_count == 4  # Initial + 3 retries
```

---

## Coverage Plan

### Coverage Targets by Component

| Component | Line Coverage | Branch Coverage | Priority |
|-----------|---------------|-----------------|----------|
| Connection Manager | 95%+ | 90%+ | Critical |
| Tool Router | 95%+ | 95%+ | Critical |
| Circuit Breaker | 90%+ | 85%+ | Critical |
| Parallel Executor | 90%+ | 85%+ | High |
| Health Monitor | 90%+ | 85%+ | High |
| Resource Manager | 85%+ | 80%+ | High |

### Overall Target: 90%+ Coverage

### Critical Paths Requiring 100% Coverage

1. **Connection establishment and cleanup**
2. **Tool routing and validation**
3. **Circuit breaker state transitions**
4. **Error handling and retries**
5. **Resource cleanup on shutdown**

### Acceptable Lower Coverage Areas

- Logging statements (70%+)
- Performance metrics collection (80%+)
- Diagnostic/debug methods (75%+)

---

## Implementation Checklist

### Phase 1: Setup (Week 1, Days 1-2)

- [ ] Create test directory structure
  - `tests/unit/core/`
  - `tests/integration/core/`
- [ ] Set up test fixtures module
  - `tests/fixtures/mcp_orchestrator_fixtures.py`
- [ ] Configure pytest for async tests
- [ ] Set up coverage reporting
- [ ] Configure CI pipeline for tests

### Phase 2: Core Unit Tests (Week 1, Days 3-5)

- [ ] Write connection management tests (20 tests)
  - [ ] Initialization tests
  - [ ] Connection lifecycle tests
  - [ ] Connection pooling tests
- [ ] Verify all tests fail (RED phase)
- [ ] Implement minimal MCPOrchestrator skeleton
- [ ] Implement connection management (GREEN phase)
- [ ] Refactor for quality (REFACTOR phase)
- [ ] Verify 95%+ coverage

### Phase 3: Routing & Parallel Tests (Week 2, Days 1-2)

- [ ] Write tool routing tests (15 tests)
- [ ] Write parallel execution tests (10 tests)
- [ ] RED → GREEN → REFACTOR cycle
- [ ] Verify 90%+ coverage

### Phase 4: Error Handling Tests (Week 2, Days 3-4)

- [ ] Write error handling tests (12 tests)
- [ ] Write health check tests (8 tests)
- [ ] Implement circuit breaker pattern
- [ ] Implement retry logic with backoff
- [ ] RED → GREEN → REFACTOR cycle
- [ ] Verify 90%+ coverage

### Phase 5: Resource Management Tests (Week 2, Day 5)

- [ ] Write resource management tests (10 tests)
- [ ] Implement lifecycle management
- [ ] Implement context manager support
- [ ] RED → GREEN → REFACTOR cycle
- [ ] Verify 85%+ coverage

### Phase 6: Integration Tests (Week 3, Days 1-3)

- [ ] Write integration tests (30 tests)
- [ ] Set up docker-compose test environment
- [ ] Test with real MCP servers
- [ ] Performance benchmarking
- [ ] Load testing

### Phase 7: Documentation & Review (Week 3, Days 4-5)

- [ ] Document orchestrator API
- [ ] Write usage examples
- [ ] Code review
- [ ] Final coverage report
- [ ] Performance metrics report

---

## CI/CD Integration

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest-unit
      name: Run unit tests
      entry: pytest tests/unit/core/ -v
      language: system
      pass_filenames: false
```

### GitHub Actions Workflow

```yaml
# .github/workflows/test-orchestrator.yml
name: MCP Orchestrator Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run unit tests
        run: |
          pytest tests/unit/core/ -v --cov=core --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      sabnzbd:
        image: linuxserver/sabnzbd:latest
      sonarr:
        image: linuxserver/sonarr:latest
      radarr:
        image: linuxserver/radarr:latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: |
          pytest tests/integration/core/ -v -m integration
```

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Connection Establishment | < 1s per server | Time to connect all 4 servers |
| Tool Call Latency | < 100ms overhead | Time added by orchestrator |
| Parallel Call Throughput | 100+ calls/sec | Concurrent tool executions |
| Health Check Interval | Every 30s | Background monitoring |
| Memory Usage | < 100MB | Resident memory |
| CPU Usage | < 5% idle | Background processes |

### Load Test Scenarios

#### Scenario 1: High Volume Single Server

```python
# 1000 calls to SABnzbd get_queue
await asyncio.gather(*[
    orchestrator.call_tool("sabnzbd", "get_queue", {})
    for _ in range(1000)
])

# Expected: Complete in < 10 seconds
```

#### Scenario 2: Parallel Multi-Server

```python
# 100 batches of 4 parallel calls (one per server)
batches = [[
    {"server": s, "tool": "health_check", "params": {}}
    for s in ["sabnzbd", "sonarr", "radarr", "plex"]
] for _ in range(100)]

await asyncio.gather(*[
    orchestrator.call_tools_parallel(batch)
    for batch in batches
])

# Expected: Complete in < 30 seconds
```

#### Scenario 3: Error Recovery

```python
# Simulate repeated failures and recovery
for _ in range(100):
    try:
        await orchestrator.call_tool("failing_server", "tool", {})
    except:
        pass

# Expected: Circuit breaker opens, recovery within 60s
```

---

## Success Criteria

### Phase Completion Criteria

**Phase 1-2 (Connection Management)**
- ✓ All 20 connection tests passing
- ✓ 95%+ code coverage
- ✓ Connection pooling verified
- ✓ Zero memory leaks

**Phase 3 (Routing & Parallel)**
- ✓ All 25 routing/parallel tests passing
- ✓ 90%+ code coverage
- ✓ Parallel execution verified
- ✓ Order preservation confirmed

**Phase 4 (Error Handling)**
- ✓ All 20 error handling tests passing
- ✓ Circuit breaker verified working
- ✓ Exponential backoff confirmed
- ✓ Graceful degradation working

**Phase 5 (Resource Management)**
- ✓ All 10 resource tests passing
- ✓ Clean shutdown verified
- ✓ No resource leaks
- ✓ Context manager working

**Phase 6 (Integration)**
- ✓ All 30 integration tests passing
- ✓ Works with real MCP servers
- ✓ Performance targets met
- ✓ Load tests passing

### Final Acceptance Criteria

- ✓ **All 105 tests passing** (75 unit + 30 integration)
- ✓ **90%+ overall code coverage**
- ✓ **Performance benchmarks met**
- ✓ **Zero critical bugs**
- ✓ **Documentation complete**
- ✓ **Code review approved**
- ✓ **CI/CD pipeline green**

---

## Appendix A: Test File Structure

```
tests/
├── unit/
│   └── core/
│       ├── __init__.py
│       └── test_mcp_orchestrator.py (75 tests)
├── integration/
│   └── core/
│       ├── __init__.py
│       └── test_mcp_orchestrator_integration.py (30 tests)
└── fixtures/
    ├── __init__.py
    ├── conftest.py
    └── mcp_orchestrator_fixtures.py
```

## Appendix B: Dependencies

```toml
# pyproject.toml
[tool.poetry.group.test.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.11.1"
pytest-timeout = "^2.1.0"
httpx = "^0.24.1"
pytest-httpx = "^0.22.0"
```

## Appendix C: Quick Reference Commands

```bash
# Run all unit tests
pytest tests/unit/core/ -v

# Run with coverage
pytest tests/unit/core/ --cov=core --cov-report=html

# Run specific test class
pytest tests/unit/core/test_mcp_orchestrator.py::TestOrchestratorConnectionManagement -v

# Run integration tests (requires docker-compose)
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/core/ -v -m integration
docker-compose -f docker-compose.test.yml down

# Run with performance profiling
pytest tests/unit/core/ --profile

# Watch mode for TDD
pytest-watch tests/unit/core/
```

---

## Document Metadata

**Version**: 1.0.0
**Created**: 2025-10-06
**Author**: Test Architecture Team
**Status**: Ready for Implementation
**Next Review**: After Phase 2 Completion

**Related Documents**:
- `BUILD-PLAN.md` - Overall project plan
- `MCP_PROTOCOL.md` - MCP protocol specification
- `ARCHITECTURE.md` - System architecture

---

**The orchestrator is the heart of AutoArr. These tests will ensure it beats strong and steady!**
