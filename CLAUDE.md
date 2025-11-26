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

# Frontend
cd autoarr/ui
pnpm exec playwright test                  # All E2E tests
pnpm exec playwright test --ui             # Interactive mode
pnpm exec playwright show-report           # View reports

# Post-Deployment Tests
bash run-post-deployment-tests.sh          # Quick runner
cd tests/post-deployment
bash run-all-tests.sh                      # Full suite
bash test-settings-api.sh                  # Settings test only
```

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

## 📞 Getting Help

- **Documentation**: See `/app/docs/` folder
- **Architecture**: `/app/docs/ARCHITECTURE.md`
- **API Reference**: `/app/docs/API_REFERENCE.md`
- **Troubleshooting**: `/app/docs/TROUBLESHOOTING.md`
- **Build Plan**: `/app/docs/BUILD-PLAN.md`

---

_Last Updated: 2025-01-08 (Sprint 10 Complete)_
_Version: 1.0.0_
