# PR Review Command

Automated code review for pull requests using specialized agents.

## Usage

```
/pr-review [pr-number]
```

Or run without arguments to review the current branch's PR.

## Step 1: Identify PR

```bash
# Get current branch
BRANCH=$(git branch --show-current)

# Find associated PR
gh pr view --json number,title,url,headRefName,baseRefName,additions,deletions,changedFiles
```

## Step 2: Gather Context

```bash
# Get PR diff
gh pr diff

# Get changed files list
gh pr diff --name-only

# Get linked issue (if any)
gh pr view --json body | jq -r '.body' | grep -oE '#[0-9]+'
```

## Step 3: Automated Checks

Run automated quality gates first:

```bash
# Type checking
poetry run mypy autoarr/

# Linting and formatting
poetry run format

# Run tests
poetry run pytest --cov

# Full quality suite
poetry run test

# Security scan
poetry run bandit -r autoarr/ -ll
```

## Step 4: Spawn Code Review Agent

Delegate to `@code-reviewer` agent with context:

```markdown
@code-reviewer

## PR Context

- **PR:** #[number] - [title]
- **Branch:** [head] → [base]
- **Changed Files:** [count]
- **Additions:** [+lines] / **Deletions:** [-lines]

## Linked Issue

[Issue details if found]

## Changed Files

[List of files]

## Review Focus Areas

Based on the files changed, focus on:

- [Area 1 based on file types]
- [Area 2 based on patterns]

Please conduct a thorough code review.
```

## Step 5: Security Review (if applicable)

If changes touch security-sensitive areas, spawn `@sast-security-scanner`:

Security-sensitive patterns:

- `api/routers/` - API endpoints
- `mcp_servers/` - External service integration
- `services/llm_agent.py` - LLM interactions
- `.env`, `config/` - Configuration
- `auth`, `token`, `key` in code

## Step 6: E2E Test Verification

If frontend changes:

```bash
# Run E2E tests in Docker container
./scripts/run-e2e-tests.sh
```

## Step 7: Aggregate Findings

Combine findings from all agents:

```markdown
## PR Review Summary

### Automated Checks

| Check    | Status            |
| -------- | ----------------- |
| mypy     | ✅ Pass / ❌ Fail |
| flake8   | ✅ Pass / ❌ Fail |
| black    | ✅ Pass / ❌ Fail |
| Tests    | ✅ Pass / ❌ Fail |
| Coverage | ✅ 87% / ⚠️ 75%   |
| Bandit   | ✅ Pass / ❌ Fail |

### Code Review Findings

#### 🔴 Blockers

[From @code-reviewer]

#### 🟠 Major Issues

[From @code-reviewer]

#### 🟡 Minor Issues

[From @code-reviewer]

### Security Review

[From @sast-security-scanner if applicable]

### E2E Tests

[Pass/Fail status]

### Recommendation

**[APPROVE / REQUEST_CHANGES / COMMENT]**

[Justification]
```

## Step 8: Post to PR

```bash
gh pr comment <PR_NUMBER> --body-file /dev/stdin << 'EOF'
[Generated review summary]
EOF
```

Or request changes:

```bash
gh pr review <PR_NUMBER> --request-changes --body "..."
```

Or approve:

```bash
gh pr review <PR_NUMBER> --approve --body "..."
```

## Review Focus by File Type

| File Pattern          | Review Focus                                    |
| --------------------- | ----------------------------------------------- |
| `api/routers/*.py`    | Input validation, error handling, auth          |
| `api/services/*.py`   | Business logic, async patterns, error handling  |
| `mcp_servers/**/*.py` | API integration, retries, error handling        |
| `ui/src/**/*.tsx`     | React patterns, accessibility, state management |
| `ui/src/**/*.ts`      | Type safety, async patterns                     |
| `tests/**/*.py`       | Test coverage, assertions, mocking              |
| `pyproject.toml`      | Dependency changes, version bumps               |
| `.github/**/*.yml`    | CI/CD security, workflow changes                |

## AutoArr-Specific Review Checklist

### Backend

- [ ] Pydantic models for all request/response?
- [ ] Async/await used for all I/O?
- [ ] Error handling returns appropriate status codes?
- [ ] Logging present without sensitive data?

### MCP Servers

- [ ] API keys handled securely?
- [ ] Retry logic with exponential backoff?
- [ ] Rate limiting respected?
- [ ] Error types distinguished (retryable vs non-retryable)?

### Frontend

- [ ] TypeScript strict mode compliance?
- [ ] Accessibility (WCAG 2.1 AA)?
- [ ] Mobile-first responsive design?
- [ ] No inline styles (Tailwind only)?

### Testing

- [ ] TDD followed (tests exist for new code)?
- [ ] 85%+ coverage maintained?
- [ ] E2E tests for critical paths?
- [ ] Mocks used appropriately?

## Example Output

```markdown
## 🔍 PR Review: #123 - Add retry logic to SABnzbd client

### Automated Checks

| Check    | Status               |
| -------- | -------------------- |
| mypy     | ✅ Pass              |
| flake8   | ✅ Pass              |
| black    | ✅ Pass              |
| Tests    | ✅ Pass (234 passed) |
| Coverage | ✅ 87% (+1%)         |
| Bandit   | ✅ Pass              |

### Code Review Findings

#### 🔴 Blockers

None

#### 🟠 Major Issues

1. **Missing timeout on retry** in `client.py:45`
   - Retry loop doesn't have max timeout
   - Could hang indefinitely on slow responses

#### 🟡 Minor Issues

1. Consider adding docstring to `with_retry` decorator
2. Test coverage for edge case: empty response

### 💚 Highlights

- Good separation of retry logic into decorator
- Comprehensive test coverage
- Clean async implementation

### Recommendation

**REQUEST_CHANGES**

Please add a max timeout to the retry loop before merging.

---

_Reviewed by Claude (@code-reviewer agent)_
```
