# Claude Code Memories

**Current Year: 2025** - Use this for all date references and documentation.

This file stores persistent learnings and context for Claude Code sessions.
Claude will read this file at the start of sessions to maintain continuity.

## Project Context

### AutoArr Overview

- Intelligent orchestration layer for media automation stacks
- Integrates SABnzbd, Sonarr, Radarr, Plex via MCP servers
- Provides configuration intelligence, autonomous recovery, natural language interface
- v1.0 feature-complete, all 10 sprints from BUILD-PLAN.md complete

### Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLite/PostgreSQL
- **Frontend:** React 18, TypeScript, Tailwind CSS, Zustand
- **Integration:** MCP (Model Context Protocol) servers
- **LLM:** Claude 3.5 Sonnet (or local Llama 3.1)
- **Testing:** pytest, Playwright
- **CI:** GitHub Actions, Docker

## Critical Rules

### E2E Tests Must Run in Docker

- **NEVER** run Playwright tests from devcontainer
- Always use: `./scripts/run-e2e-tests.sh`
- Or: `DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local ...`
- Use `playwright-container.config.ts` for local tests

### Container Development

- Use `DOCKER_HOST=unix:///var/run/docker.sock` prefix for docker commands
- After container restart: `pip install httpx --quiet`
- Copy code changes to container, then restart

### TDD Workflow

- Always follow Red-Green-Refactor cycle
- 85%+ test coverage target
- Run `poetry run test` before committing

## Common Commands

```bash
# Development
poetry install                    # Install backend deps
poetry run test                   # Run all tests + linting
poetry run format                 # Auto-format code
poetry run pytest --cov          # Tests with coverage

# Frontend
cd autoarr/ui && pnpm install    # Install frontend deps
cd autoarr/ui && pnpm run dev    # Start dev server
cd autoarr/ui && pnpm run build  # Build for production

# Docker (from devcontainer)
DOCKER_HOST=unix:///var/run/docker.sock docker ps
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d
DOCKER_HOST=unix:///var/run/docker.sock docker logs autoarr-local --tail 50

# E2E Tests (MUST run in container!)
./scripts/run-e2e-tests.sh
./scripts/run-e2e-tests.sh tests/home.spec.ts
```

## Agent Quick Reference

| Task              | Agent                         |
| ----------------- | ----------------------------- |
| API development   | `@backend-api-developer`      |
| MCP servers       | `@mcp-server-developer`       |
| Frontend React    | `@frontend-dev-tdd`           |
| Code review       | `@code-reviewer`              |
| E2E tests         | `@playwright-e2e-tester`      |
| Integration tests | `@integration-testing-agent`  |
| Security          | `@sast-security-scanner`      |
| Performance       | `@performance-load-tester`    |
| Documentation     | `@documentation-architect`    |
| Docker/Infra      | `@docker-infrastructure-tdd`  |
| LLM integration   | `@llm-integration-architect`  |
| Event system      | `@event-architecture-builder` |

## Session Notes

<!-- Add learnings from each session below -->

### Recent Learnings

- MCP server clients require full import paths: `from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient`
- Frontend API paths must match backend routes exactly
- httpx needs reinstalling after container restart
- Tests require `pytest-asyncio` with `asyncio_mode = "auto"`

### Known Issues

- E2E tests fail if run from devcontainer (network/memory issues)
- httpx not in production Docker image (needs reinstall after restart)
- Some E2E tests skip due to missing endpoint implementations

### Decisions Made

- Using MCP protocol for service integrations
- Claude API for LLM features (local fallback planned)
- WebSocket for real-time updates
- Event-driven architecture with pub/sub pattern
- Mobile-first responsive design

---

_Last updated: Auto-updated by Claude Code_
