# Testing Documentation

This directory contains comprehensive testing strategies and documentation for the AutoArr project.

## Overview

AutoArr follows **Test-Driven Development (TDD)** principles with a target of 90%+ code coverage across all components.

## Test Strategy Documents

### Core Components

- [**MCP Orchestrator Test Strategy**](./MCP_ORCHESTRATOR_TEST_STRATEGY.md) - Comprehensive test strategy for the MCP Orchestrator, the heart of AutoArr that coordinates all MCP server connections.
  - 105 total tests (75 unit + 30 integration)
  - 90%+ coverage target
  - Covers connection management, tool routing, parallel execution, error handling, and more

### Test Pyramid

```
        ┌───────┐
        │  E2E  │  10%
        │ Tests │
        └───────┘
      ┌───────────┐
      │Integration│  20%
      │   Tests   │
      └───────────┘
  ┌─────────────────┐
  │   Unit Tests    │  70%
  └─────────────────┘
```

## Running Tests

### Quick Start

```bash
# Install dependencies
pip install -e .[dev]

# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific component tests
pytest tests/unit/core/test_mcp_orchestrator.py -v

# Run integration tests (requires docker-compose)
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v -m integration
docker-compose -f docker-compose.test.yml down
```

### Test Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require external services)
- `@pytest.mark.slow` - Slow tests (> 1 second)
- `@pytest.mark.asyncio` - Async tests

### Watch Mode (TDD)

```bash
# Auto-run tests on file changes
pytest-watch tests/unit/

# Or use VS Code with Python extension
# Tests will auto-run in test explorer
```

## Test Structure

```
tests/
├── unit/                           # Unit tests (70% of tests)
│   ├── core/                      # Core orchestration tests
│   │   └── test_mcp_orchestrator.py
│   └── mcp_servers/               # Individual MCP server tests
│       ├── sabnzbd/
│       ├── sonarr/
│       ├── radarr/
│       └── plex/
├── integration/                    # Integration tests (20% of tests)
│   ├── core/
│   │   └── test_mcp_orchestrator_integration.py
│   └── mcp_servers/
└── fixtures/                       # Shared test fixtures
    ├── conftest.py
    └── mcp_orchestrator_fixtures.py
```

## Coverage Reports

Coverage reports are generated after test runs:

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Targets by Component

| Component | Target | Current |
|-----------|--------|---------|
| MCP Orchestrator | 90%+ | TBD |
| SABnzbd MCP Server | 95%+ | TBD |
| Sonarr MCP Server | 95%+ | TBD |
| Radarr MCP Server | 95%+ | TBD |
| Plex MCP Server | 95%+ | TBD |
| FastAPI Backend | 85%+ | TBD |
| Overall | 90%+ | TBD |

## TDD Workflow

### Red-Green-Refactor

1. **🔴 RED**: Write a failing test
   ```bash
   # Test fails because feature doesn't exist
   pytest tests/unit/core/test_mcp_orchestrator.py::test_new_feature -v
   ```

2. **🟢 GREEN**: Write minimal code to pass
   ```python
   # Implement just enough to make test pass
   def new_feature():
       return "minimal implementation"
   ```

3. **♻️ REFACTOR**: Improve the code
   ```python
   # Clean up while keeping tests green
   def new_feature():
       # Better implementation
       pass
   ```

## CI/CD Integration

Tests run automatically on:
- Every push to any branch
- Every pull request
- Before merging to main

### GitHub Actions

```yaml
# .github/workflows/test.yml
- Unit tests (< 5 seconds)
- Integration tests with docker-compose (< 30 seconds)
- Coverage reporting to Codecov
- Fail if coverage drops below 90%
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [Component Name].

Test Coverage:
- [Functionality 1]
- [Functionality 2]
"""

import pytest

class TestComponentName:
    """Test suite for [component]."""

    @pytest.mark.asyncio
    async def test_specific_behavior(self):
        """Test that [specific behavior] works correctly."""
        # Arrange
        component = Component(config)

        # Act
        result = await component.do_something()

        # Assert
        assert result.success
```

### Integration Test Template

```python
"""
Integration tests for [Component Name].

Requires:
- docker-compose test environment
- Test data loaded
"""

import pytest

@pytest.mark.integration
class TestComponentIntegration:
    """Integration test suite for [component]."""

    @pytest.mark.asyncio
    async def test_real_interaction(self, test_server):
        """Test [component] with real server."""
        # Arrange
        component = Component(test_server.url)

        # Act
        result = await component.interact()

        # Assert
        assert result is not None
```

## Test Fixtures

Reusable test fixtures are defined in `tests/fixtures/`:

### Common Fixtures

- `sabnzbd_queue_factory` - Create mock SABnzbd queue data
- `sonarr_series_factory` - Create mock Sonarr series data
- `radarr_movie_factory` - Create mock Radarr movie data
- `mcp_orchestrator_config_factory` - Create orchestrator configs
- `mock_mcp_client_factory` - Create mock MCP clients

### Using Fixtures

```python
def test_with_fixture(sabnzbd_queue_factory):
    """Test using a fixture."""
    # Create test data
    queue = sabnzbd_queue_factory(slots=5, paused=False)

    # Use in test
    assert len(queue["queue"]["slots"]) == 5
```

## Performance Testing

### Benchmarks

Performance benchmarks are defined in test strategy documents:

- Connection establishment: < 1s per server
- Tool call latency: < 100ms overhead
- Parallel throughput: 100+ calls/sec
- Memory usage: < 100MB
- Health check interval: 30s

### Running Performance Tests

```bash
# Run with profiling
pytest tests/unit/core/ --profile

# Generate performance report
pytest tests/integration/ -v -m slow --duration=10
```

## Debugging Failed Tests

### Verbose Output

```bash
# Show print statements and full output
pytest tests/unit/core/ -v -s

# Show local variables on failure
pytest tests/unit/core/ -v -l

# Stop at first failure
pytest tests/unit/core/ -v -x
```

### Debug Mode

```python
# Add breakpoint in test
def test_something():
    # ... test code ...
    import pdb; pdb.set_trace()  # Debugger will stop here
    # ... more test code ...
```

## Best Practices

1. **Write tests first** (TDD) - Red, Green, Refactor
2. **Test one thing** - Each test should verify one behavior
3. **Use descriptive names** - Test names should describe what they test
4. **Arrange-Act-Assert** - Structure tests clearly
5. **Mock external dependencies** - Keep unit tests isolated
6. **Test edge cases** - Not just the happy path
7. **Keep tests fast** - Unit tests should run in < 100ms
8. **Use fixtures** - Share setup code via fixtures
9. **Clean up resources** - Use context managers and teardown
10. **Document complex tests** - Add docstrings explaining why

## Resources

### Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Internal Docs

- [MCP Protocol Specification](../MCP_PROTOCOL.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [BUILD-PLAN.md](../../BUILD-PLAN.md)

## Questions?

If you have questions about testing:

1. Check the test strategy documents in this directory
2. Look at existing tests for examples
3. Review the BUILD-PLAN.md for overall context
4. Ask in the #testing channel

---

**Remember: Tests are not just verification - they're documentation, design tools, and confidence builders. Write tests you'd want to read in 6 months!**
