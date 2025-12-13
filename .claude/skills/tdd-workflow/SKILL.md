# TDD Workflow Skill

## Overview

This skill defines the strict Test-Driven Development workflow for AutoArr.
Every feature implementation follows the Red-Green-Refactor cycle in small,
verifiable increments.

## Core Principles

### 1. No Big Code Dumps

Never implement a full solution in one shot. Work in tiny increments:

- One behavior at a time
- One focused test at a time
- Like a 3D printer adding thin, verified layers

### 2. Test First, Always

```
┌─────────────────────────────────────────────────────────┐
│                  TDD Cycle                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│     ┌─────────┐                                         │
│     │   RED   │  Write a failing test                   │
│     │  Test   │  that defines desired behavior          │
│     └────┬────┘                                         │
│          │                                              │
│          ▼                                              │
│     ┌─────────┐                                         │
│     │  GREEN  │  Write minimal code                     │
│     │  Code   │  to make test pass                      │
│     └────┬────┘                                         │
│          │                                              │
│          ▼                                              │
│     ┌─────────┐                                         │
│     │REFACTOR │  Improve code quality                   │
│     │  Clean  │  while keeping tests green              │
│     └────┬────┘                                         │
│          │                                              │
│          └──────────────► Repeat                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. Verify Before Proceeding

Never write more code until current tests pass:

```bash
# Run specific test file
poetry run pytest autoarr/tests/unit/api/test_settings.py -v

# Run tests in watch mode during development
poetry run pytest autoarr/tests/unit/ -v --tb=short

# Check types after changes
poetry run mypy autoarr/

# Run full test suite
poetry run test
```

## Test Patterns for AutoArr

### Unit Tests (autoarr/tests/unit/)

```python
# autoarr/tests/unit/api/test_config_audit.py
import pytest
from unittest.mock import AsyncMock, patch
from autoarr.api.services.configuration_manager import ConfigurationManager

@pytest.fixture
def config_manager():
    return ConfigurationManager()

@pytest.fixture
def mock_sabnzbd_config():
    return {
        "misc": {"download_dir": "/downloads", "complete_dir": "/complete"},
        "servers": [{"host": "news.example.com", "connections": 20}],
    }

class TestConfigurationAudit:
    async def test_audit_returns_recommendations_for_suboptimal_config(
        self, config_manager, mock_sabnzbd_config
    ):
        """RED: Write this test first, then implement the service."""
        # Arrange
        mock_sabnzbd_config["misc"]["article_cache_limit"] = 100  # Too low

        # Act
        result = await config_manager.audit_sabnzbd(mock_sabnzbd_config)

        # Assert
        assert len(result.recommendations) > 0
        assert any(r.setting == "article_cache_limit" for r in result.recommendations)

    async def test_audit_passes_for_optimal_config(
        self, config_manager, mock_sabnzbd_config
    ):
        """Config meeting best practices should have no critical recommendations."""
        # Arrange
        mock_sabnzbd_config["misc"]["article_cache_limit"] = 500

        # Act
        result = await config_manager.audit_sabnzbd(mock_sabnzbd_config)

        # Assert
        critical = [r for r in result.recommendations if r.priority == "critical"]
        assert len(critical) == 0
```

### Integration Tests (autoarr/tests/integration/)

```python
# autoarr/tests/integration/api/test_settings_integration.py
import pytest
from httpx import AsyncClient
from autoarr.api.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

class TestSettingsIntegration:
    async def test_connection_test_returns_success_for_valid_service(
        self, client, mock_sabnzbd_server
    ):
        """Integration test: API → Service → External API (mocked)."""
        response = await client.post(
            "/api/v1/settings/test/sabnzbd",
            json={
                "url": mock_sabnzbd_server.url,
                "api_key_or_token": "test-key",
                "timeout": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "version" in data

    async def test_connection_test_returns_error_for_invalid_url(self, client):
        """Verify error handling for unreachable services."""
        response = await client.post(
            "/api/v1/settings/test/sabnzbd",
            json={
                "url": "http://nonexistent:8080",
                "api_key_or_token": "test-key",
                "timeout": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data
```

### E2E Tests (autoarr/tests/e2e/)

```python
# autoarr/tests/e2e/test_config_audit_flow.py
import pytest
from autoarr.api.services.configuration_manager import ConfigurationManager
from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient

@pytest.mark.e2e
class TestConfigAuditFlow:
    async def test_full_audit_workflow(self, live_sabnzbd_url, live_sabnzbd_key):
        """E2E: Full config audit from API call to recommendations."""
        # Arrange
        client = SABnzbdClient(live_sabnzbd_url, live_sabnzbd_key)
        manager = ConfigurationManager()

        # Act - Fetch real config
        config = await client.get_config()

        # Act - Run audit
        result = await manager.audit_sabnzbd(config)

        # Assert
        assert result.health_score >= 0
        assert result.health_score <= 100
        assert isinstance(result.recommendations, list)
```

### MCP Server Tests

```python
# autoarr/tests/unit/mcp_servers/test_sabnzbd_tools.py
import pytest
from autoarr.mcp_servers.sabnzbd.server import SABnzbdMCPServer

class TestSABnzbdTools:
    async def test_get_queue_returns_active_downloads(
        self, mock_sabnzbd_response
    ):
        """MCP tool should return structured queue data."""
        server = SABnzbdMCPServer()

        result = await server.call_tool("get_queue", {})

        assert "queue" in result
        assert isinstance(result["queue"], list)

    async def test_retry_download_triggers_search(
        self, mock_sonarr_client
    ):
        """Retry should trigger search in appropriate *arr app."""
        server = SABnzbdMCPServer()

        result = await server.call_tool("retry_failed", {
            "nzo_id": "test-123",
            "strategy": "quality_fallback"
        })

        assert result["success"] is True
        mock_sonarr_client.search.assert_called_once()
```

## Commands Reference

```bash
# Run all tests with coverage
poetry run pytest --cov

# Run only unit tests
poetry run pytest autoarr/tests/unit/ -v

# Run only integration tests
poetry run pytest autoarr/tests/integration/ -v

# Run only E2E tests
poetry run pytest autoarr/tests/e2e/ -v

# Run tests matching pattern
poetry run pytest -k "config_audit" -v

# Run with verbose output
poetry run pytest -v --tb=long

# Run full quality suite (linting + tests)
poetry run test

# Format code
poetry run format
```

## Frontend TDD (React/TypeScript)

```typescript
// autoarr/ui/src/components/Dashboard/__tests__/HealthScore.test.tsx
import { render, screen } from '@testing-library/react';
import { HealthScore } from '../HealthScore';

describe('HealthScore', () => {
  it('should display score as percentage', () => {
    render(<HealthScore score={85} />);

    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('should show critical status for low scores', () => {
    render(<HealthScore score={30} />);

    expect(screen.getByRole('status')).toHaveClass('text-red-500');
  });

  it('should show healthy status for high scores', () => {
    render(<HealthScore score={90} />);

    expect(screen.getByRole('status')).toHaveClass('text-green-500');
  });
});
```

## Test Coverage Targets

| Layer              | Target | Rationale             |
| ------------------ | ------ | --------------------- |
| API Services       | 85%    | Core business logic   |
| MCP Servers        | 80%    | External integrations |
| API Routers        | 75%    | Request handling      |
| UI Components      | 70%    | User interactions     |
| E2E Critical Paths | 100%   | User journeys         |

## Checklist

Before marking a feature complete:

- [ ] All acceptance criteria have tests
- [ ] Each test was seen failing before passing
- [ ] Edge cases covered
- [ ] Error cases covered
- [ ] Code refactored after tests pass
- [ ] Coverage targets met
- [ ] Tests are readable and maintainable
- [ ] `poetry run test` passes
- [ ] `poetry run format` applied
