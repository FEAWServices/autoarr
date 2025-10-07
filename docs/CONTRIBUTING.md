# Contributing to AutoArr

Thank you for your interest in contributing to AutoArr! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Using Claude Code Agents](#using-claude-code-agents)
- [Project Structure](#project-structure)

---

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in AutoArr a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors include:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors include:**

- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive behavior may be reported to the project team at conduct@autoarr.io. All complaints will be reviewed and investigated promptly and fairly.

---

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (for running services)
- **Python 3.11+** (for backend development)
- **Node.js 20+** (for frontend development)
- **Git** (for version control)
- **Claude Code** (optional, for AI-assisted development)

### Setting Up Your Development Environment

1. **Fork and clone the repository**:

```bash
git clone https://github.com/YOUR_USERNAME/autoarr.git
cd autoarr
git remote add upstream https://github.com/autoarr/autoarr.git
```

2. **Start development services**:

```bash
# Start test instances of SABnzbd, Sonarr, Radarr, Plex
docker-compose -f docker-compose.dev.yml up -d
```

3. **Install backend dependencies**:

```bash
cd api
poetry install
poetry shell  # Activate virtual environment
```

4. **Install frontend dependencies**:

```bash
cd ui
pnpm install
```

5. **Set up environment variables**:

```bash
cp .env.example .env
# Edit .env with your test API keys
```

6. **Run the application**:

```bash
# Terminal 1: Backend
cd api
uvicorn main:app --reload

# Terminal 2: Frontend
cd ui
pnpm dev
```

7. **Access the application**:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Test SABnzbd: http://localhost:8080
- Test Sonarr: http://localhost:8989
- Test Radarr: http://localhost:7878

---

## 🔄 Development Workflow

### Branching Strategy

We follow a simplified Git Flow:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

### Keeping Your Branch Updated

```bash
git fetch upstream
git rebase upstream/develop
```

---

## 🧪 Testing

AutoArr follows **Test-Driven Development (TDD)**. Tests should be written before implementation.

### Running Tests

**Backend tests**:

```bash
cd api
pytest tests/ --cov --cov-report=html
```

**Frontend tests**:

```bash
cd ui
pnpm test        # Unit tests
pnpm test:e2e    # E2E tests with Playwright
```

**Integration tests**:

```bash
pytest tests/integration/ -v
```

### Writing Tests

#### Backend (pytest)

```python
# tests/services/test_configuration_manager.py
import pytest
from services.configuration_manager import ConfigurationManager

@pytest.mark.asyncio
async def test_audit_identifies_non_optimal_settings():
    """Test that audit identifies non-optimal configuration."""
    # Arrange
    manager = ConfigurationManager()
    config = {"setting1": "value1"}

    # Act
    result = await manager.audit_configuration("sabnzbd", config)

    # Assert
    assert result.has_recommendations
    assert len(result.recommendations) > 0
```

#### Frontend (Playwright)

```typescript
// tests/ui/dashboard.spec.ts
import { test, expect } from "@playwright/test";

test("dashboard shows configuration audit results", async ({ page }) => {
  await page.goto("http://localhost:3000");

  // Click audit button
  await page.getByRole("button", { name: "Run Audit" }).click();

  // Check for results
  await expect(page.getByText("Configuration Audit Complete")).toBeVisible();
  await expect(page.getByTestId("recommendation-card")).toHaveCount.greaterThan(
    0,
  );
});
```

### Test Coverage Requirements

- **Unit tests**: 85%+ coverage
- **Integration tests**: All critical paths
- **E2E tests**: All user-facing features

---

## 📏 Coding Standards

### Python (Backend)

We follow **PEP 8** with some modifications:

- **Line length**: 88 characters (Black default)
- **Quotes**: Double quotes for strings
- **Imports**: Sorted with `isort`
- **Type hints**: Required for all function signatures
- **Docstrings**: Google-style for all public functions

**Example**:

```python
from typing import List, Optional

async def fetch_configuration(
    app_name: str,
    include_hidden: bool = False
) -> Optional[dict]:
    """Fetch configuration from an application.

    Args:
        app_name: Name of the application (e.g., "sabnzbd")
        include_hidden: Whether to include hidden settings

    Returns:
        Configuration dictionary, or None if app not found

    Raises:
        ConnectionError: If unable to connect to application
    """
    # Implementation
    pass
```

**Formatting tools**:

```bash
black .              # Format code
isort .              # Sort imports
flake8 .             # Lint code
mypy .               # Type checking
```

### TypeScript (Frontend)

We follow **Airbnb Style Guide** with TypeScript:

- **Quotes**: Single quotes
- **Semicolons**: Required
- **Indent**: 2 spaces
- **Types**: Explicit types for props and state
- **Components**: Functional components with hooks

**Example**:

```typescript
import { useState, useEffect } from 'react';

interface ConfigAuditProps {
  appName: string;
  onComplete?: (results: AuditResult[]) => void;
}

export function ConfigAudit({ appName, onComplete }: ConfigAuditProps) {
  const [results, setResults] = useState<AuditResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Implementation
  }, [appName]);

  return (
    <div className="config-audit">
      {/* JSX */}
    </div>
  );
}
```

**Formatting tools**:

```bash
pnpm lint           # ESLint
pnpm format         # Prettier
pnpm type-check     # TypeScript compiler
```

### Commit Messages

Follow **Conventional Commits**:

```
type(scope): subject

body

footer
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```bash
feat(config-manager): add configuration rollback feature
fix(monitoring): handle failed downloads correctly
docs(readme): update installation instructions
test(services): add tests for request handler
```

---

## 🔃 Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code is formatted
3. ✅ No linting errors
4. ✅ Documentation updated
5. ✅ Commits follow convention
6. ✅ Branch is up-to-date with `develop`

### Submitting a Pull Request

1. **Push your branch**:

```bash
git push origin feature/your-feature-name
```

2. **Create PR on GitHub**:

- Base: `develop`
- Compare: `feature/your-feature-name`
- Fill out the PR template

3. **PR Template**:

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] All tests passing

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. **Automated checks**: CI runs tests and linting
2. **Code review**: Maintainers review code
3. **Changes requested**: Address feedback
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainer merges PR

### After Merge

1. Delete your feature branch
2. Pull latest `develop`
3. Start new feature!

---

## 🤖 Using Claude Code Agents

AutoArr leverages Claude Code for accelerated development. Here's how to use it effectively.

### Setup Claude Code

1. Install Claude Code:

```bash
npm install -g @anthropic-ai/claude-code
```

2. Configure with your API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Agent Types

#### Backend Agent

For Python, FastAPI, services, MCP servers:

```bash
claude-code implement service \
  --name=MonitoringService \
  --dependencies=MCPOrchestrator \
  --tdd=true \
  --coverage-target=90
```

#### Frontend Agent

For React components, UI/UX:

```bash
claude-code create component \
  --name=ActivityFeed \
  --test-framework=playwright \
  --mobile-first=true \
  --a11y=true
```

#### Testing Agent

For comprehensive test suites:

```bash
claude-code create tests \
  --target=services/request_handler.py \
  --framework=pytest \
  --include=unit,integration \
  --coverage-target=90
```

#### Documentation Agent

For user and developer docs:

```bash
claude-code create docs \
  --type=api-reference \
  --format=openapi \
  --include-examples=true
```

### Best Practices

1. **Start with tests**: Use TDD approach
2. **Review generated code**: Always review and understand
3. **Iterate**: Use multiple prompts to refine
4. **Document**: Add comments for complex logic
5. **Test thoroughly**: Don't rely solely on generated tests

### Example Workflow

```bash
# 1. Create tests first
claude-code create tests \
  --target=services/new_feature.py \
  --tdd=true

# 2. Implement feature
claude-code implement service \
  --name=NewFeature \
  --from-tests=tests/services/test_new_feature.py

# 3. Create docs
claude-code create docs \
  --target=services/new_feature.py \
  --type=module-docs
```

---

## 📁 Project Structure

```
autoarr/
├── api/                          # Backend (Python/FastAPI)
│   ├── services/                 # Business logic services
│   │   ├── configuration_manager.py
│   │   ├── monitoring_service.py
│   │   └── request_handler.py
│   ├── intelligence/             # LLM and AI components
│   │   ├── llm_agent.py
│   │   └── decision_tree.py
│   ├── mcp/                      # MCP orchestrator
│   │   └── orchestrator.py
│   ├── routes/                   # API endpoints
│   │   ├── config.py
│   │   ├── monitoring.py
│   │   └── requests.py
│   ├── models/                   # Data models
│   ├── tests/                    # Backend tests
│   └── main.py                   # Application entry
│
├── ui/                           # Frontend (React/TypeScript)
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── Dashboard/
│   │   │   ├── ConfigAudit/
│   │   │   ├── ChatInterface/
│   │   │   └── ActivityFeed/
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # API clients
│   │   ├── store/                # State management (Zustand)
│   │   ├── types/                # TypeScript types
│   │   └── App.tsx               # Root component
│   ├── tests/                    # Frontend tests
│   └── package.json
│
├── mcp-servers/                  # MCP server implementations
│   ├── sabnzbd/
│   │   ├── server.py
│   │   ├── tools/
│   │   └── tests/
│   ├── sonarr/
│   ├── radarr/
│   └── plex/
│
├── shared/                       # Shared utilities
│   ├── types/                    # Shared TypeScript types
│   └── utils/                    # Shared utilities
│
├── docs/                         # Documentation
│   ├── USER-GUIDE.md
│   ├── API.md
│   └── ARCHITECTURE.md
│
├── docker/                       # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
├── .github/                      # GitHub configuration
│   ├── workflows/                # CI/CD workflows
│   └── ISSUE_TEMPLATE/
│
├── VISION.md                     # Product vision
├── ARCHITECTURE.md               # Technical architecture
├── BUILD-PLAN.md                 # Development roadmap
├── README.md                     # Project README
└── CONTRIBUTING.md               # This file
```

---

## 🎯 Good First Issues

Looking for where to start? Check out issues labeled [`good first issue`](https://github.com/autoarr/autoarr/labels/good%20first%20issue).

Some ideas:

- Add tests for existing components
- Improve documentation
- Fix typos or formatting
- Add new best practices to database
- Improve error messages
- Add new UI components

---

## 💬 Getting Help

- **Discord**: Join our [Discord server](https://discord.gg/autoarr)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/autoarr/autoarr/discussions)
- **Issues**: Report bugs in [GitHub Issues](https://github.com/autoarr/autoarr/issues)

---

## 🏆 Recognition

Contributors are recognized in:

- GitHub contributors page
- Release notes
- Monthly contributor highlights
- Annual contributor awards

---

## 📄 License

By contributing to AutoArr, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AutoArr! 🎉

<p align="center">
  Made with ❤️ by the AutoArr community
</p>
