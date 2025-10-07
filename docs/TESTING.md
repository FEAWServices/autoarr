# Testing Guide

This guide explains how to run tests locally and in CI for the AutoArr project.

## Quick Start

```bash
# Run all tests (matches CI exactly)
poetry run test

# Auto-format code
poetry run format
```

## Local Test Harness

AutoArr follows the **DRY (Don't Repeat Yourself)** principle for testing. The local test harness runs the exact same checks as the CI pipeline, ensuring no surprises when you push code.

### Available Commands

#### Poetry Commands (Recommended)

```bash
poetry run test      # Run all linters and tests
poetry run format    # Auto-format code to match project standards
```

#### Shell Scripts (Alternative)

```bash
bash scripts/test.sh    # Run all checks
bash scripts/format.sh  # Format code
```

## What Gets Tested

The test harness runs the following checks in order:

### 1. Black - Code Formatting Check

Verifies that all Python code follows the project's formatting standards.

```bash
poetry run black --check .
```

**Configuration**: `[tool.black]` in `pyproject.toml`

- Line length: 100 characters
- Target version: Python 3.11

### 2. Flake8 - Linting

Checks for code quality issues, style violations, and potential bugs.

```bash
poetry run flake8 api/ mcp-servers/mcp_servers/ shared/ tests/ \
  --max-line-length=100 --extend-ignore=E203
```

**Key Rules**:

- Maximum line length: 100 characters
- Ignores E203 (whitespace before ':') for Black compatibility
- Catches unused imports, undefined variables, and style issues

### 3. MyPy - Type Checking

Performs static type checking to catch type-related bugs.

```bash
poetry run mypy api/ mcp-servers/mcp_servers/ shared/ --config-file=pyproject.toml
```

**Configuration**: `[tool.mypy]` in `pyproject.toml`

- **Note**: MyPy runs in non-blocking mode (continues even with errors)
- Warns about type issues but doesn't fail the build
- Helps improve code quality over time

### 4. Pytest - Unit Tests

Runs all unit tests with coverage reporting.

```bash
poetry run pytest tests/ -v \
  --cov=api \
  --cov=mcp_servers \
  --cov=shared \
  --cov-report=xml \
  --cov-report=term-missing
```

**Configuration**: `[tool.pytest.ini_options]` in `pyproject.toml`

- Minimum coverage: 80%
- Coverage reports: XML (for CI) and terminal (for local dev)
- Async mode: auto (handles asyncio tests automatically)

## CI Pipeline

The CI pipeline runs on every push and pull request. It uses GitHub Actions and performs identical checks to the local test harness.

### Workflow: `.github/workflows/ci.yml`

**Python Matrix**: Tests against Python 3.11 and 3.12

**Steps**:

1. Checkout code
2. Set up Python
3. Install Poetry 2.2.1
4. Cache dependencies
5. Install dependencies
6. Run Black (formatting check)
7. Run Flake8 (linting)
8. Run MyPy (type checking, non-blocking)
9. Run Pytest (unit tests with coverage)
10. Upload coverage to Codecov

**Frontend Testing** (separate job):

1. Setup Node.js and pnpm
2. Install dependencies
3. Run ESLint
4. Run Prettier check
5. Build frontend
6. Run Playwright E2E tests

## Development Workflow

### Recommended Workflow

1. **Make code changes**

   ```bash
   # Edit your files
   ```

2. **Format code automatically**

   ```bash
   poetry run format
   ```

3. **Run all tests locally**

   ```bash
   poetry run test
   ```

4. **Fix any issues** reported by the test harness

5. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: Your commit message"
   ```

   - Pre-commit hooks will run automatically
   - If hooks fail, fix the issues and commit again

6. **Push to GitHub**
   ```bash
   git push
   ```
   - CI pipeline will run automatically
   - All checks must pass before merging

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Black formatting
- Flake8 linting
- MyPy type checking
- Prettier formatting (for Markdown, JSON, etc.)

**Install hooks**:

```bash
poetry run pre-commit install
```

**Run manually**:

```bash
poetry run pre-commit run --all-files
```

## Test Coverage

### Current Coverage Targets

- **Minimum**: 80% overall coverage
- **Goal**: 85%+ coverage for all modules

### View Coverage Reports

**Terminal report**:

```bash
poetry run pytest tests/ --cov-report=term-missing
```

**HTML report**:

```bash
poetry run pytest tests/
open htmlcov/index.html
```

### Coverage Reports in CI

Coverage reports are automatically uploaded to Codecov on every CI run. You can view detailed coverage reports and trends at:

```
https://codecov.io/gh/FEAWServices/autoarr
```

## Troubleshooting

### Tests Pass Locally But Fail in CI

1. **Check Python version**: CI tests against 3.11
2. **Check dependencies**: Run `poetry lock` to update lock file
3. **Check paths**: Ensure you're testing the same directories

### Black and Flake8 Conflicts

The project is configured to avoid conflicts:

- Both use 100 character line length
- Flake8 ignores E203 (Black-specific formatting)

### MyPy Errors

MyPy is configured as **non-blocking** to allow gradual type coverage improvement:

- Errors are reported but don't fail the build
- Focus on fixing new code first
- Gradually improve type coverage over time

### Pre-commit Hook Failures

If pre-commit hooks fail:

1. **View the error message** - it shows what failed
2. **Run formatter**: `poetry run format`
3. **Run tests**: `poetry run test`
4. **Fix remaining issues** manually
5. **Commit again**: Hooks will run again

**Skip hooks** (not recommended):

```bash
git commit --no-verify
```

## Writing Tests

### Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── api/          # API tests
│   ├── mcp_servers/  # MCP server tests
│   └── shared/       # Shared module tests
├── integration/       # Integration tests
└── e2e/              # End-to-end tests
```

### Test-Driven Development (TDD)

AutoArr follows TDD principles:

1. **Write test first** - Define expected behavior
2. **Run test** - Verify it fails (red)
3. **Write minimal code** - Make test pass (green)
4. **Refactor** - Improve code quality (refactor)
5. **Repeat** - Continue with next feature

### Example Test

```python
import pytest
from httpx import AsyncClient
from api.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Test that the health check endpoint returns 200."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

## Resources

- **pytest docs**: https://docs.pytest.org/
- **Black docs**: https://black.readthedocs.io/
- **Flake8 docs**: https://flake8.pycqa.org/
- **MyPy docs**: https://mypy.readthedocs.io/
- **pre-commit docs**: https://pre-commit.com/

## Summary

The AutoArr testing infrastructure ensures:

✅ **Consistency** - Local tests match CI exactly
✅ **Quality** - High test coverage and strict linting
✅ **Speed** - Fast feedback loop for developers
✅ **Confidence** - Catch issues before they reach production

Run `poetry run test` before every commit to maintain code quality! 🚀
