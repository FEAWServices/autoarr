# AutoArr Test Suite

Quick reference for running tests in AutoArr.

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run only unit tests
pytest tests/unit/

# Run only integration tests (requires running SABnzbd)
export SABNZBD_TEST_API_KEY=your_key
pytest tests/integration/ -m integration
```

## Test Structure

```
tests/
├── unit/              # Fast, isolated tests (70% of pyramid)
├── integration/       # Tests with real services (20% of pyramid)
├── e2e/              # Full workflow tests (10% of pyramid) - Future
├── fixtures/         # Test data factories
└── conftest.py       # Global pytest configuration
```

## Test Commands

### By Test Type

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/ -m integration

# Slow tests excluded
pytest -m "not slow"
```

### By Component

```bash
# SABnzbd MCP Server tests
pytest tests/unit/mcp_servers/sabnzbd/
pytest tests/integration/mcp_servers/sabnzbd/

# Specific test file
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py

# Specific test class
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py::TestSABnzbdClientQueue

# Specific test
pytest tests/unit/mcp_servers/sabnzbd/test_sabnzbd_client.py::TestSABnzbdClientQueue::test_get_queue_returns_queue_data
```

### With Coverage

```bash
# Coverage report in terminal
pytest --cov=mcp_servers --cov-report=term-missing

# Coverage report as HTML
pytest --cov=mcp_servers --cov-report=html
open htmlcov/index.html

# Fail if coverage below 80%
pytest --cov=mcp_servers --cov-fail-under=80
```

### Verbose Output

```bash
# Show test names
pytest -v

# Show print statements
pytest -s

# Both
pytest -vs
```

## Environment Setup

### For Integration Tests

```bash
# Required environment variables
export SABNZBD_TEST_URL=http://localhost:8080
export SABNZBD_TEST_API_KEY=your_api_key_here

# Or use .env.test file
cat > .env.test << EOF
SABNZBD_TEST_URL=http://localhost:8080
SABNZBD_TEST_API_KEY=your_api_key
EOF
```

### Start Test Services

```bash
# Start SABnzbd for integration tests
docker-compose -f docker/docker-compose.dev.yml up -d sabnzbd

# Check SABnzbd is running
curl http://localhost:8080/api?mode=version
```

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Requires real services
- `@pytest.mark.slow` - Takes >2 seconds
- `@pytest.mark.skip` - Skipped (TDD red phase)

Filter by markers:
```bash
pytest -m integration      # Only integration tests
pytest -m "not slow"       # Exclude slow tests
pytest -m asyncio          # Only async tests
```

## Current Status (TDD Red Phase)

🔴 **All tests currently skipped** - This is expected!

We're following TDD (Test-Driven Development):
1. ✅ Write tests first (DONE - all tests written)
2. 🔲 Implement code to make tests pass (NEXT STEP)
3. 🔲 Refactor while keeping tests green

To see all skipped tests:
```bash
pytest --collect-only
```

## Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| SABnzbd Client | 95% | 0% (not implemented) |
| SABnzbd MCP Server | 95% | 0% (not implemented) |
| Overall | 90% | 0% (not implemented) |

## Troubleshooting

### Tests Won't Run

```bash
# Check pytest is installed
pytest --version

# Install dependencies
poetry install --with dev

# Or with pip
pip install -e .[dev]
```

### Integration Tests Skip

```bash
# Check environment variable
echo $SABNZBD_TEST_API_KEY

# Check SABnzbd is accessible
curl http://localhost:8080/api?mode=version

# Set environment variable
export SABNZBD_TEST_API_KEY=your_key
```

### Import Errors

```bash
# Install package in editable mode
pip install -e .

# Or with poetry
poetry install
```

### Coverage Not Generated

```bash
# Install pytest-cov
pip install pytest-cov

# Run with coverage
pytest --cov=mcp_servers
```

## Performance

Target test execution times:
- Unit tests: < 30 seconds total
- Integration tests: < 60 seconds total
- Single unit test: < 0.1 seconds
- Single integration test: < 2 seconds

Check slow tests:
```bash
# Show slowest 10 tests
pytest --durations=10
```

## CI/CD

Tests run automatically on:
- Every push to main
- Every pull request
- Pre-commit hooks (unit tests only)

GitHub Actions workflow:
```bash
# View workflow file
cat .github/workflows/test.yml
```

## Documentation

- **Test Strategy**: [docs/TEST-STRATEGY.md](../docs/TEST-STRATEGY.md)
- **Unit Test Details**: [tests/unit/mcp_servers/sabnzbd/README.md](unit/mcp_servers/sabnzbd/README.md)
- **Build Plan**: [docs/BUILD-PLAN.md](../docs/BUILD-PLAN.md)

## Contributing

When adding new tests:

1. **Follow TDD**: Write test before implementation
2. **Use factories**: Reuse test data factories from `fixtures/`
3. **Name clearly**: `test_[component]_[behavior]_[condition]`
4. **Document**: Add docstring explaining what test verifies
5. **Run locally**: Ensure tests pass before committing

Example:
```python
@pytest.mark.asyncio
async def test_client_handles_timeout_error(sabnzbd_client):
    """
    Test that client raises SABnzbdConnectionError on timeout.

    This verifies proper error handling when SABnzbd is unreachable
    or network is slow. Client should not hang indefinitely.
    """
    # Test implementation...
```

## Getting Help

- 📚 [Test Strategy Docs](../docs/TEST-STRATEGY.md)
- 💬 [GitHub Discussions](https://github.com/autoarr/autoarr/discussions)
- 🐛 [Report Issues](https://github.com/autoarr/autoarr/issues)
- 📖 [pytest Documentation](https://docs.pytest.org/)

---

**Happy Testing!** 🧪
