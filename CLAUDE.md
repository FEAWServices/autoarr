# AutoArr - Claude Code Reference

> **Quick Start for Claude Code**: This file contains everything Claude needs to know about this repository to provide effective assistance.

## 📋 Project Overview

**AutoArr** is an intelligent orchestration layer for media automation stacks (SABnzbd, Sonarr, Radarr, Plex). It provides:

- 🧠 **Configuration Intelligence**: LLM-powered configuration auditing and recommendations
- 🤖 **Autonomous Recovery**: Automatic download failure detection and intelligent retry strategies
- 💬 **Natural Language Interface**: Chat-based content requests with movie/TV classification
- 📊 **Real-time Monitoring**: WebSocket-based live updates and activity tracking

**Status**: v1.0 feature-complete (100% of BUILD-PLAN implemented)

### Two-Product Strategy (Separate Repositories)

**AutoArr (GPL-3.0)** - This repo (`/app`)

- 100% open source, complete media automation with local LLM
- Self-hosted, works standalone without premium

**AutoArrX (Premium)** - Separate repo (`/autoarr-premium`)

- Optional privacy-first cloud SaaS
- AutoArr instances connect TO it via secure outbound WebSocket (like Plex)
- No firewall configuration needed on user's network

See [docs/VISION_AND_PRICING.md](docs/VISION_AND_PRICING.md) for complete details.

### Multi-Repo Development

When working in the devcontainer, both repos are available:

- `/app` - AutoArr GPL (this repo)
- `/autoarr-premium` - AutoArr Premium SaaS (separate repo)

Use `bash scripts/test-all.sh` to run tests across both repos.

## 🏗️ Architecture

### Technology Stack

**Backend** (`/app/autoarr/api/`):

- Python 3.11+ with FastAPI
- SQLite/PostgreSQL for data persistence
- MCP (Model Context Protocol) for external service integration
- Claude 3.5 Sonnet for LLM intelligence
- WebSocket for real-time updates
- Event-driven architecture with pub/sub pattern

**Frontend** (`/app/autoarr/ui/`):

- React 18 + TypeScript
- Tailwind CSS for styling
- Zustand for state management
- React Query for data fetching
- Playwright for E2E testing
- Mobile-first responsive design

**Infrastructure**:

- Docker + Docker Compose
- GitHub Actions for CI/CD
- Pre-commit hooks (black, flake8, prettier)
- Poetry for Python dependency management
- pnpm for Node.js dependencies

### Directory Structure

```
/app/
├── autoarr/
│   ├── api/                    # FastAPI backend
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── models.py          # Database models
│   │   └── main.py            # Application entry
│   ├── mcp_servers/           # MCP server implementations
│   │   ├── sabnzbd/           # SABnzbd MCP server
│   │   ├── sonarr/            # Sonarr MCP server
│   │   ├── radarr/            # Radarr MCP server
│   │   └── plex/              # Plex MCP server
│   ├── shared/                # Shared utilities
│   │   └── core/              # MCP orchestrator, config
│   ├── tests/                 # Test suite
│   │   ├── unit/              # Unit tests
│   │   ├── integration/       # Integration tests
│   │   ├── e2e/               # End-to-end tests
│   │   └── security/          # Security tests
│   └── ui/                    # React frontend
│       ├── src/
│       │   ├── components/    # React components
│       │   ├── pages/         # Page components
│       │   ├── services/      # API clients
│       │   ├── stores/        # Zustand stores
│       │   └── types/         # TypeScript types
│       └── tests/             # Playwright tests
├── docs/                      # Documentation
│   ├── implementation/        # Implementation details
│   ├── ARCHITECTURE.md        # System architecture
│   ├── BUILD-PLAN.md          # 20-week development plan
│   └── ...                    # More documentation
├── docker/                    # Docker configuration
├── .github/                   # GitHub Actions workflows
├── pyproject.toml            # Python dependencies
├── poetry.lock               # Locked Python dependencies
└── README.md                 # Project README
```

## 🔧 Development Workflow

### Getting Started

1. **Install Dependencies**:

   ```bash
   poetry install              # Backend
   cd autoarr/ui && pnpm install  # Frontend
   ```

2. **Run Tests**:

   ```bash
   poetry run test            # All tests + linting
   poetry run pytest          # Just tests
   cd autoarr/ui && pnpm test # Frontend tests
   ```

3. **Format Code**:

   ```bash
   poetry run format          # Auto-format Python
   cd autoarr/ui && pnpm run format  # Frontend
   ```

4. **Run Development Servers**:
   ```bash
   ./run_dev.sh              # Start both backend and frontend
   ```

### Code Style & Standards

**Python**:

- Black formatter (line length: 100)
- flake8 linter
- mypy for type checking
- Type hints required
- Async/await for all I/O operations
- Follows PEP 8

**TypeScript**:

- ESLint + Prettier
- Strict mode enabled
- No inline styles (Tailwind only)
- Functional components with hooks
- WCAG 2.1 AA accessibility

**Testing**:

- TDD approach (write tests first)
- 85%+ test coverage target
- pytest for Python
- Playwright for E2E
- Mock external services in unit tests

### Git Workflow

**Branch Naming**:

- `feature/sprint-N-description` - Sprint implementations
- `feature/description` - General features
- `fix/description` - Bug fixes
- `chore/description` - Maintenance tasks

**Commit Messages** (Conventional Commits):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation
- `chore:` - Maintenance
- `test:` - Tests
- `refactor:` - Code refactoring

**Pre-commit Hooks**:

- Automatically format code
- Run linters
- Check for merge conflicts
- Validate YAML/JSON

## 🧪 Testing Strategy

### Test Coverage

- **789+ tests** across all test types
- **85%+ code coverage** maintained
- Unit → Integration → E2E pyramid (70/20/10)

### Test Locations

```
autoarr/tests/
├── unit/                      # Fast, isolated tests
│   ├── api/                   # API tests
│   ├── services/              # Service layer tests
│   └── mcp_servers/           # MCP server tests
├── integration/               # Multi-component tests
│   ├── api/                   # API integration
│   └── mcp_servers/           # MCP integration
├── e2e/                       # Full system tests
│   ├── test_config_audit_flow.py
│   ├── test_download_recovery_flow.py
│   └── test_content_request_flow.py
├── security/                  # Security tests
│   └── test_security.py
└── post-deployment/           # Post-deployment smoke tests
    ├── run-all-tests.sh       # Test suite runner
    ├── test-health.sh         # Health endpoint tests
    ├── test-ui-accessible.sh  # UI accessibility tests
    ├── test-settings-api.sh   # Settings save tests
    └── README.md              # Test documentation

autoarr/ui/tests/              # Frontend E2E tests
├── chat.spec.ts
├── activity.spec.ts
├── settings.spec.ts
└── ...
```

### Running Tests

```bash
# Backend
poetry run pytest tests/unit/              # Unit tests only
poetry run pytest tests/integration/       # Integration tests
poetry run pytest tests/e2e/               # E2E tests
poetry run pytest --cov                    # With coverage

# Frontend E2E Tests (Playwright)
# IMPORTANT: Run inside Docker container for reliable results!
# See "Running Playwright E2E Tests" section below.

# Post-Deployment Tests
bash run-post-deployment-tests.sh          # Quick runner
cd tests/post-deployment
bash run-all-tests.sh                      # Full suite
bash test-settings-api.sh                  # Settings test only
```

### Running Playwright E2E Tests

**IMPORTANT FOR CLAUDE CODE**: Playwright tests MUST be run inside the Docker container, NOT from the devcontainer. Running from devcontainer causes network/memory issues due to Windows filesystem mounts.

```bash
# 1. Start the local test container (if not running)
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d

# 2. Run E2E tests INSIDE the container
./scripts/run-e2e-tests.sh                           # Run all tests
./scripts/run-e2e-tests.sh tests/home.spec.ts        # Run specific file
./scripts/run-e2e-tests.sh "dashboard"               # Run tests matching pattern

# Or manually via docker exec:
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test --config=playwright-container.config.ts"
```

**Why run inside container?**

- Tests run against `localhost:8088` (same container as app)
- No network hops or port mapping issues
- No Windows filesystem memory problems
- Fast, reliable feedback

**Config files:**

- `playwright-container.config.ts` - For running inside Docker container
- `playwright.config.ts` - For CI/GitHub Actions (starts own dev server)

## 📚 Key Services

### Backend Services (`autoarr/api/services/`)

1. **configuration_manager.py**: Configuration auditing and recommendations
2. **llm_agent.py**: Claude API integration for intelligent analysis
3. **intelligent_recommendation_engine.py**: Priority assessment and explanations
4. **monitoring_service.py**: SABnzbd queue monitoring
5. **recovery_service.py**: Automatic download retry with strategies
6. **request_handler.py**: Natural language content request processing
7. **event_bus.py**: Pub/sub event system with correlation tracking
8. **activity_log.py**: Activity tracking and logging
9. **websocket_manager.py**: Real-time WebSocket connections
10. **web_search_service.py**: TMDB/Brave Search integration

### MCP Servers (`autoarr/mcp_servers/`)

Each MCP server provides tools to interact with external services:

- **sabnzbd/**: Queue, history, retry, config operations
- **sonarr/**: Series management, quality profiles, search
- **radarr/**: Movie management, quality profiles, search
- **plex/**: Library sections, metadata (optional)

### Frontend Components (`autoarr/ui/src/`)

**Key Pages**:

- `Home.tsx` - Dashboard with system overview
- `ConfigAudit.tsx` - Configuration audit results
- `Activity.tsx` - Activity feed with real-time updates
- `Chat.tsx` - Natural language content requests
- `Settings.tsx` - Application settings

**Key Components**:

- `Dashboard/` - Health scores and service status
- `ConfigAudit/` - Recommendation cards
- `Chat/` - Message components, content cards
- `Toast.tsx` - Notification system
- `WebSocket` service for real-time updates

## 🔍 Common Tasks

### Adding a New API Endpoint

1. Create endpoint in `autoarr/api/routers/`
2. Implement service logic in `autoarr/api/services/`
3. Add Pydantic models in `autoarr/api/models.py`
4. Write tests in `autoarr/tests/unit/api/`
5. Update OpenAPI documentation

### Adding a New React Component

1. Create component in `autoarr/ui/src/components/`
2. Add TypeScript types in `autoarr/ui/src/types/`
3. Write Playwright tests in `autoarr/ui/tests/`
4. Follow mobile-first design principles
5. Ensure WCAG 2.1 AA accessibility

### Adding a New MCP Server

1. Create directory in `autoarr/mcp_servers/`
2. Implement client (`client.py`)
3. Define models (`models.py`)
4. Create MCP server (`server.py`)
5. Add to orchestrator configuration
6. Write comprehensive tests

## 📖 Documentation

All documentation is in `/app/docs/`:

- **ARCHITECTURE.md** - System architecture overview
- **BUILD-PLAN.md** - Complete 20-week development plan
- **API_REFERENCE.md** - Complete API documentation
- **MCP_SERVER_GUIDE.md** - MCP server development
- **QUICK-START.md** - Installation guide
- **CONFIGURATION.md** - Configuration reference
- **TROUBLESHOOTING.md** - Common issues
- **FAQ.md** - Frequently asked questions
- **CONTRIBUTING.md** - Contributing guidelines

## 🐛 Known Issues & Limitations

See `/app/docs/BUGS.md` for tracked issues.

**Current Limitations**:

- Some E2E tests skip due to missing endpoint implementations
- Load tests created but not yet executed
- Local LLM fallback not yet implemented (planned)

## 🚀 Deployment

### Docker Deployment

```bash
# Production (for end users)
docker-compose -f docker/docker-compose.production.yml up -d

# Local Testing (for developers, with host network)
docker-compose -f docker/docker-compose.local-test.yml up -d

# Synology NAS
docker-compose -f docker/docker-compose.synology.yml up -d

# VS Code DevContainer
# Open repo in VS Code → "Reopen in Container"
```

### Docker Files Structure

```
docker/
├── Dockerfile.production         # Multi-stage build for CI/users
├── Dockerfile.local-test         # Lightweight local testing
├── docker-compose.production.yml # End-user deployment
├── docker-compose.local-test.yml # Developer testing (host network)
└── docker-compose.synology.yml   # Synology NAS deployment
```

### Environment Variables

Required:

- `SABNZBD_URL`, `SABNZBD_API_KEY`
- `SONARR_URL`, `SONARR_API_KEY`
- `RADARR_URL`, `RADARR_API_KEY`
- `CLAUDE_API_KEY` (for LLM features)

Optional:

- `PLEX_URL`, `PLEX_TOKEN`
- `REDIS_URL` (for caching)
- `BRAVE_API_KEY` (for web search)

See `.env.example` for complete list.

## 💡 Tips for Claude Code

1. **Always run tests** after making changes:

   ```bash
   poetry run test
   ```

2. **Check test coverage** for new code:

   ```bash
   poetry run pytest --cov
   ```

3. **Format code before committing**:

   ```bash
   poetry run format
   ```

4. **Use existing patterns**:

   - Follow existing service structure
   - Use async/await consistently
   - Mock external services in tests
   - Emit events for activity logging

5. **Documentation**: Update relevant docs in `/app/docs/` when adding features

6. **Feature Branches**: Use sprint-based branches for major features

7. **Reference Implementation**: Check `/app/docs/implementation/` for detailed implementation notes

## 📊 Project Metrics

- **Total Lines of Code**: ~20,000+ (excluding tests)
- **Total Tests**: 789+
- **Test Coverage**: 85%+
- **API Endpoints**: 30+
- **React Components**: 15+
- **MCP Servers**: 4 (SABnzbd, Sonarr, Radarr, Plex)
- **Documentation Files**: 30+

## 🎯 Sprint Status

All 10 sprints from BUILD-PLAN.md are **complete**:

- ✅ Sprint 1-2: Foundation
- ✅ Sprint 3-4: Configuration Intelligence
- ✅ Sprint 5-6: Monitoring & Recovery
- ✅ Sprint 7-8: Natural Language Interface
- ✅ Sprint 9-10: Testing & Documentation

**Project Status**: v1.0 feature-complete, ready for production deployment.

## 🔧 Container Development Workflow

### Applying Code Changes to Running Container

When developing locally, changes need to be copied to the running container:

```bash
# 1. Build frontend
cd /app/autoarr/ui && pnpm run build

# 2. Copy frontend build to container
DOCKER_HOST=unix:///var/run/docker.sock docker cp /app/autoarr/ui/dist/. autoarr-local:/app/autoarr/ui/dist/

# 3. Copy backend Python files if changed
DOCKER_HOST=unix:///var/run/docker.sock docker cp /app/autoarr/api/routers/settings.py autoarr-local:/app/autoarr/api/routers/settings.py

# 4. Restart container to apply changes
DOCKER_HOST=unix:///var/run/docker.sock docker restart autoarr-local

# 5. Re-install httpx after restart (required for MCP clients)
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local pip install httpx --quiet
```

### Container Access

Always use `DOCKER_HOST=unix:///var/run/docker.sock` prefix for docker commands from devcontainer:

```bash
# Check container status
DOCKER_HOST=unix:///var/run/docker.sock docker ps --filter "name=autoarr"

# View container logs
DOCKER_HOST=unix:///var/run/docker.sock docker logs autoarr-local --tail 50

# Execute commands in container
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -s "http://localhost:8088/health"

# Test API endpoint
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -s "http://localhost:8088/api/v1/settings/test/sabnzbd" \
  -X POST -H "Content-Type: application/json" \
  -d '{"url": "http://192.168.0.80:8090/sabnzbd/", "api_key_or_token": "your-key", "timeout": 10}'
```

## 🔌 Service Plugin Architecture

### Frontend Service Plugins (`autoarr/ui/src/plugins/services/`)

Each service (SABnzbd, Sonarr, Radarr, Plex) has a plugin that defines:

- Connection test logic
- Default URLs and ports
- API key instructions
- Color theming

**Critical: API endpoint paths must match backend routes exactly!**

```typescript
// Frontend calls: /api/v1/settings/test/{service}
// Backend route:  /api/v1/settings/test/{service}
testConnection: async (url: string, apiKey: string) => {
  const response = await fetch(
    `/api/v1/settings/test/sabnzbd`, // NOT: /api/v1/settings/sabnzbd/test
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, api_key_or_token: apiKey, timeout: 10 }),
    },
  );
  // ...
};
```

### Backend MCP Client Imports

MCP server clients must use full import paths:

```python
# Correct:
from autoarr.mcp_servers.sabnzbd.client import SABnzbdClient
from autoarr.mcp_servers.sonarr.client import SonarrClient
from autoarr.mcp_servers.radarr.client import RadarrClient
from autoarr.mcp_servers.plex.client import PlexClient

# WRONG (will cause ModuleNotFoundError):
from sabnzbd.client import SABnzbdClient
```

### API Path Contract Tests

The test file `autoarr/tests/unit/api/test_api_path_contract.py` verifies frontend API calls match backend routes. Run these tests when adding/modifying endpoints:

```bash
poetry run pytest autoarr/tests/unit/api/test_api_path_contract.py -v
```

## 🐛 Common Issues & Solutions

### "ModuleNotFoundError: No module named 'httpx'"

The MCP server clients use httpx for async HTTP requests. After container restart:

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local pip install httpx --quiet
```

### "405 Method Not Allowed" on Connection Test

Frontend endpoint URL doesn't match backend route. Check:

1. Frontend: `autoarr/ui/src/plugins/services/index.ts` - `testConnection` function
2. Backend: `autoarr/api/routers/settings.py` - route decorators

### "Connection validation failed" in Onboarding

Debug steps:

1. Check container can reach external service: `docker exec autoarr-local curl -s "http://192.168.0.80:8090/sabnzbd/api?mode=version"`
2. Check backend test endpoint directly: `docker exec autoarr-local curl -s "http://localhost:8088/api/v1/settings/test/sabnzbd" -X POST ...`
3. Check container logs for Python errors: `docker logs autoarr-local --tail 100`

### UI Buttons Not Visible (Mobile Layout)

Check for overflow issues in parent containers. Mobile-first design tips:

- Use `flex-col sm:flex-row` for responsive button groups
- Add `pb-24` padding to scrollable content for button visibility
- Use `overflow-y-auto min-h-0` for scrollable areas

## 📞 Getting Help

- **Documentation**: See `/app/docs/` folder
- **Architecture**: `/app/docs/ARCHITECTURE.md`
- **API Reference**: `/app/docs/API_REFERENCE.md`
- **Troubleshooting**: `/app/docs/TROUBLESHOOTING.md`
- **Build Plan**: `/app/docs/BUILD-PLAN.md`

---

_Last Updated: 2025-12-07_
_Version: 1.0.0_

## Notes

- When you kill all containers, it kills Claude as well - kill services selectively
- Always verify API paths match between frontend plugins and backend routes
- The httpx dependency needs reinstalling after container restart until Dockerfile is updated
