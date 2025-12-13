# Implement Issue Command

Takes a GitHub issue and implements it end-to-end using the appropriate agents,
following TDD workflow and quality standards.

## Usage

```
/implement-issue [issue-number]
```

Or describe the feature and this workflow will be followed.

## Step 1: Gather Issue Context

```bash
# Get issue details
gh issue view <NUMBER> --json title,body,labels,assignees,milestone

# Check related PRs
gh pr list --search "issue:<NUMBER>"
```

Parse the issue to understand:

- **What**: Feature/bug/task description
- **Why**: Business context
- **Acceptance Criteria**: Specific requirements
- **Scope**: Which layers are affected

## Step 2: Analyse and Plan

### Identify Affected Areas

```markdown
## Impact Analysis

### Layers Affected

- [ ] Backend API (FastAPI routers, services)
- [ ] MCP Servers (SABnzbd, Sonarr, Radarr, Plex)
- [ ] Frontend (React components, pages)
- [ ] Database (SQLAlchemy models)
- [ ] Tests (unit, integration, E2E)

### Components Affected

- [ ] Configuration Manager
- [ ] Monitoring Service
- [ ] Recovery Service
- [ ] Request Handler
- [ ] LLM Agent
- [ ] WebSocket Manager
- [ ] Event Bus
```

### Create Implementation Plan

```markdown
## Implementation Plan

### Phase 1: Backend (if needed)

- [ ] 1.1 Define Pydantic models
- [ ] 1.2 Implement service layer (with tests)
- [ ] 1.3 Create FastAPI endpoints (with tests)

### Phase 2: MCP Server (if needed)

- [ ] 2.1 Define client methods
- [ ] 2.2 Implement MCP tools
- [ ] 2.3 Add error handling and retries

### Phase 3: Frontend (if needed)

- [ ] 3.1 Create React components
- [ ] 3.2 Wire up to API
- [ ] 3.3 Add E2E tests

### Phase 4: Quality

- [ ] 4.1 Run full test suite
- [ ] 4.2 Run linting and formatting
- [ ] 4.3 Update documentation
```

## Step 3: Execute with TDD

Follow strict TDD for each task:

### Red Phase - Write Failing Test

```python
# autoarr/tests/unit/api/test_new_feature.py
class TestNewFeature:
    async def test_feature_behavior(self):
        # Arrange
        service = FeatureService()

        # Act
        result = await service.do_something()

        # Assert
        assert result.success is True
```

Run and verify it fails:

```bash
poetry run pytest autoarr/tests/unit/api/test_new_feature.py -v
# Expected: FAIL - function doesn't exist yet
```

### Green Phase - Minimal Implementation

Implement just enough to pass:

```python
# autoarr/api/services/feature_service.py
class FeatureService:
    async def do_something(self) -> FeatureResult:
        return FeatureResult(success=True)
```

Run and verify it passes:

```bash
poetry run pytest autoarr/tests/unit/api/test_new_feature.py -v
# Expected: PASS
```

### Refactor Phase

Clean up while keeping tests green:

```bash
poetry run pytest
poetry run format
```

## Step 4: Delegate to Specialists

Based on the task, spawn appropriate agents:

### Backend Implementation

```
@backend-api-developer Implement [service/endpoint] following TDD
@test-architect-tdd Create comprehensive tests for [feature]
```

### MCP Server Work

```
@mcp-server-developer Create tools for [service integration]
@integration-testing-agent Test MCP server interactions
```

### Frontend Implementation

```
@frontend-dev-tdd Create [component/page] with tests
@playwright-e2e-tester Create E2E tests for [user journey]
```

### Quality Assurance

```
@code-reviewer Review all changes before PR
@sast-security-scanner Run security scan
```

## Step 5: Verify Implementation

### Run All Checks

```bash
# Type checking (Python)
poetry run mypy autoarr/

# Linting and formatting
poetry run format

# All tests
poetry run pytest --cov

# Full quality suite
poetry run test
```

### E2E Tests (IMPORTANT: Run in Docker!)

```bash
# Start container
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d

# Run E2E tests
./scripts/run-e2e-tests.sh
```

## Step 6: Create PR

### Commit Changes

```bash
# Stage changes
git add -A

# Commit with conventional format
git commit -m "feat(audit): add configuration scoring algorithm

- Implement health score calculation
- Add best practices comparison
- Create recommendation engine
- Add comprehensive tests

Closes #123"
```

### Push and Create PR

```bash
# Push branch
git push -u origin feature/issue-123-config-scoring

# Create PR
gh pr create \
  --title "feat(audit): add configuration scoring algorithm" \
  --body "## Summary
Implements configuration health scoring based on best practices.

## Changes
- Added health score calculation
- Implemented best practices comparison
- Created recommendation engine
- Added unit and integration tests

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] E2E tests pass
- [x] Manual testing complete

## Screenshots
[If applicable]

Closes #123"
```

## Agent Routing Guide

| Task Type        | Primary Agent              | Backup Agent               |
| ---------------- | -------------------------- | -------------------------- |
| FastAPI routes   | @backend-api-developer     | @test-architect-tdd        |
| Services         | @backend-api-developer     | @code-reviewer             |
| MCP servers      | @mcp-server-developer      | @integration-testing-agent |
| React components | @frontend-dev-tdd          | @code-reviewer             |
| E2E tests        | @playwright-e2e-tester     | @frontend-dev-tdd          |
| Unit tests       | @test-architect-tdd        | @backend-api-developer     |
| Security         | @sast-security-scanner     | @dast-security-tester      |
| Performance      | @performance-load-tester   | @backend-api-developer     |
| Documentation    | @documentation-architect   | -                          |
| Docker/Infra     | @docker-infrastructure-tdd | -                          |
| Code review      | @code-reviewer             | -                          |

## Quality Gates

Before marking complete:

- [ ] All acceptance criteria met
- [ ] Tests written and passing (85%+ coverage)
- [ ] No mypy errors
- [ ] No linting errors
- [ ] E2E tests pass (run in Docker!)
- [ ] Code reviewed
- [ ] PR created with proper description
- [ ] Issue linked to PR
