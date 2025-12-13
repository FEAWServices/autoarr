# Project Instructions for Claude Code

**Current Year: 2025** - Use this for all date references and documentation.

## Critical Rules

1. **Read skills before working** - Always read relevant SKILL.md files before starting
2. **Follow TDD workflow** - Use `/tdd-workflow` for all implementation
3. **E2E tests in Docker** - NEVER run Playwright from devcontainer, use `./scripts/run-e2e-tests.sh`
4. **Use specialized agents** - Delegate to the right agent for the task
5. **Check memories.md** - Review `/.claude/memories.md` for session context

## Quick Reference

### Commands

| Command                | Purpose                             |
| ---------------------- | ----------------------------------- |
| `/implement-issue [n]` | Implement a GitHub issue end-to-end |
| `/pr-review`           | Automated PR review                 |
| `/security-scan`       | Run security audit                  |
| `/e2e-test [pattern]`  | Run Playwright E2E tests            |
| `/tidy-docs`           | Organize documentation              |
| `/fix-pr`              | Fix PR issues                       |
| `/test-paths`          | Verify test paths                   |

### Key Agents

| Agent                        | Use For                  |
| ---------------------------- | ------------------------ |
| `@backend-api-developer`     | FastAPI routes, services |
| `@mcp-server-developer`      | MCP server development   |
| `@frontend-dev-tdd`          | React components         |
| `@code-reviewer`             | PR and code reviews      |
| `@test-architect-tdd`        | Test strategy            |
| `@integration-testing-agent` | Integration tests        |
| `@sast-security-scanner`     | Security scanning        |
| `@llm-integration-architect` | LLM features             |
| `@docker-infrastructure-tdd` | Docker/infra             |
| `@documentation-architect`   | Documentation            |

### Skills (read before working)

| Skill            | Location                                    | When to Use        |
| ---------------- | ------------------------------------------- | ------------------ |
| TDD Workflow     | `/.claude/skills/tdd-workflow/SKILL.md`     | All implementation |
| MCP Development  | `/.claude/skills/mcp-development/SKILL.md`  | MCP servers        |
| FastAPI Patterns | `/.claude/skills/fastapi-patterns/SKILL.md` | Backend API        |
| Playwright E2E   | `/.claude/skills/playwright-e2e/SKILL.md`   | E2E testing        |

## Architecture

AutoArr is an **intelligent media automation orchestrator**:

```
┌─────────────────────────────────────────────────┐
│           React UI (Mobile-First)               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          FastAPI Gateway                        │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              Core Services                      │
│  • Configuration Manager   • Request Handler   │
│  • Monitoring Service      • LLM Agent         │
│  • Recovery Service        • Event Bus         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│           MCP Orchestrator                      │
└─────┬────────┬──────────┬──────────┬────────────┘
      │        │          │          │
┌─────▼───┐ ┌─▼────┐ ┌───▼────┐ ┌───▼────┐
│SABnzbd  │ │Sonarr│ │ Radarr │ │  Plex  │
│   MCP   │ │  MCP │ │   MCP  │ │  MCP   │
└─────────┘ └──────┘ └────────┘ └────────┘
```

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLite/PostgreSQL
- **Frontend**: React 18, TypeScript, Tailwind, Zustand
- **Integration**: MCP (Model Context Protocol) servers
- **LLM**: Claude API (local Llama 3.1 fallback planned)
- **Testing**: pytest (85%+ coverage), Playwright E2E
- **CI**: GitHub Actions, Docker

## Docker Workflow (CRITICAL)

**E2E tests MUST run inside Docker container, NOT from devcontainer!**

```bash
# Start container
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d

# Run E2E tests (correct way)
./scripts/run-e2e-tests.sh

# Apply code changes to container
cd /app/autoarr/ui && pnpm run build
DOCKER_HOST=unix:///var/run/docker.sock docker cp /app/autoarr/ui/dist/. autoarr-local:/app/autoarr/ui/dist/
DOCKER_HOST=unix:///var/run/docker.sock docker restart autoarr-local
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local pip install httpx --quiet
```

## Quality Standards

Before any PR:

- [ ] `poetry run test` passes (linting + tests)
- [ ] `poetry run pytest --cov` shows 85%+ coverage
- [ ] `/security-scan` for security-sensitive changes
- [ ] `/e2e-test` passes (run in Docker!)
- [ ] Code reviewed by `@code-reviewer`

## File Locations

| What              | Where                                      |
| ----------------- | ------------------------------------------ |
| Backend API       | `autoarr/api/`                             |
| API Routers       | `autoarr/api/routers/`                     |
| Services          | `autoarr/api/services/`                    |
| MCP Servers       | `autoarr/mcp_servers/`                     |
| Frontend          | `autoarr/ui/src/`                          |
| Unit Tests        | `autoarr/tests/unit/`                      |
| Integration Tests | `autoarr/tests/integration/`               |
| E2E Tests         | `autoarr/tests/e2e/` + `autoarr/ui/tests/` |
| Documentation     | `docs/`                                    |
| Claude Config     | `.claude/`                                 |

## Workflow Quick Start

### Implementing a Feature

```bash
# 1. Read relevant skills
# 2. Run /implement-issue [number]
# 3. Follow TDD workflow (Red-Green-Refactor)
# 4. Run quality checks
poetry run test
# 5. Run E2E tests (in Docker!)
./scripts/run-e2e-tests.sh
# 6. Create PR with /pr-review
```

### Running Tests

```bash
# Backend (from devcontainer)
poetry run pytest --cov              # All tests
poetry run pytest tests/unit/ -v     # Unit only
poetry run pytest -k "config" -v     # Pattern match

# E2E (MUST be in Docker!)
./scripts/run-e2e-tests.sh           # All E2E
./scripts/run-e2e-tests.sh home      # Pattern match
```

## MCP Server Pattern

When adding MCP server functionality:

1. Define client in `mcp_servers/{service}/client.py`
2. Define models in `mcp_servers/{service}/models.py`
3. Implement server in `mcp_servers/{service}/server.py`
4. Use full import paths: `from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient`
5. Add tests in `tests/unit/mcp_servers/`
