# ADR-002: Monorepo Structure for GPL and Premium (AutoArr + AutoArrX)

**Date:** 2025-01-12
**Status:** Accepted
**Deciders:** AutoArr Core Team
**Technical Story:** Separate GPL and Premium code while maintaining development efficiency

---

## Context and Problem Statement

AutoArr has two products:
1. **AutoArr (GPL-3.0)** - 100% open source, local-only, free forever
2. **AutoArrX (Premium)** - Cloud-enhanced features, privacy-first, paid service

We need a repository structure that:
- Clearly separates GPL from proprietary code
- Allows efficient development in a single repository (during development)
- Enables future split into separate repositories (before public launch)
- Maintains clear licensing boundaries
- Facilitates shared code where appropriate

## Decision Drivers

- **Legal Clarity**: GPL and proprietary code must be clearly separated
- **Development Efficiency**: Want to iterate quickly without managing 2 repos
- **Future Flexibility**: Easy to split when ready for public launch
- **Build System**: Simple to build either GPL-only or full monorepo
- **Open Source Trust**: Community can verify GPL code is truly separate

## Considered Options

### Option 1: Separate Repositories from Day 1

**Structure:**
```
autoarr/ (public, GPL)
autoarrx-cloud/ (private, proprietary)
```

**Pros:**
- ✅ Perfect legal separation
- ✅ Public repo clean from day 1

**Cons:**
- ❌ Slower development (switching repos)
- ❌ Duplicate code/tooling
- ❌ Harder to share utilities
- ❌ More complex CI/CD

### Option 2: Flat Monorepo with Clear Boundaries ✅ CHOSEN

**Structure:**
```
/app/
├── autoarr/               # GPL-3.0 (Docker Hub + future public repo)
│   ├── LICENSE            # GPL-3.0
│   ├── Dockerfile         # Docker Hub optimized
│   ├── docker-compose.yml # User deployment
│   ├── pyproject.toml     # Python dependencies
│   ├── README.md          # User-facing docs
│   ├── api/               # FastAPI backend
│   ├── ui/                # React frontend
│   ├── mcp_servers/       # SABnzbd, Sonarr, Radarr, Plex
│   ├── shared/            # GPL-internal shared code
│   └── tests/             # GPL test suite
│
├── autoarrx/              # Proprietary (Azure SaaS deployment)
│   ├── LICENSE            # Proprietary
│   ├── Dockerfile         # Azure optimized
│   ├── terraform/         # Azure infrastructure as code
│   ├── .github/
│   │   └── workflows/
│   │       └── azure-deploy.yml
│   ├── pyproject.toml     # Premium dependencies
│   ├── README.md          # Internal docs
│   ├── bridge/            # Secure connection service
│   ├── cloud/             # Cloud intelligence
│   ├── notifications/     # Smart notification system
│   ├── analytics/         # Predictive analytics
│   └── tests/             # Premium test suite
│
├── docs/
│   ├── architecture/      # ADRs and architecture docs
│   ├── autoarr/           # GPL user documentation
│   └── autoarrx/          # Premium internal docs
│
├── .github/
│   └── workflows/
│       ├── autoarr-ci.yml        # GPL tests + Docker Hub
│       ├── autoarrx-ci.yml       # Premium tests + Azure
│       └── docs-ci.yml           # Documentation checks
│
├── LICENSE                # Root: Dual license notice
└── README.md              # Monorepo overview
```

**Key Decisions:**
- **Flat structure** (no packages/) - simpler for development
- **Separate Dockerfiles** - optimized for different deployment targets
- **AutoArr** = Docker Hub + eventually public GitHub
- **AutoArrX** = Azure deployment + private repo
- **No shared package** - duplicate utilities if needed (simpler than managing shared dependencies)

**Pros:**
- ✅ Fast development iteration
- ✅ Easy code sharing
- ✅ Clear legal boundaries
- ✅ Single CI/CD setup
- ✅ Easy to split later

**Cons:**
- ⚠️ Must be disciplined about boundaries
- ⚠️ Premium code visible during development (private repo)

### Option 3: Git Submodules

**Structure:**
```
autoarr-monorepo/
├── autoarr/ (submodule → separate repo)
└── autoarrx/ (submodule → separate repo)
```

**Pros:**
- ✅ Technically separate repos
- ✅ Can make one public anytime

**Cons:**
- ❌ Submodules are painful to work with
- ❌ Complex for contributors
- ❌ CI/CD complexity

---

## Decision Outcome

**Chosen option:** "Single Repo with Clear Boundaries" (Option 2)

We'll use a **monorepo with packages/** structure during development, then split before public launch.

### Implementation Plan

#### Phase 1: Restructure (Now)

```bash
# Create monorepo structure
mkdir -p packages/autoarr packages/autoarrx packages/shared

# Move GPL code
mv autoarr/* packages/autoarr/
mv LICENSE packages/autoarr/LICENSE

# Create premium structure
mkdir -p packages/autoarrx/{bridge,cloud,notifications}
touch packages/autoarrx/LICENSE.proprietary

# Create shared code
mkdir -p packages/shared/{types,utils,protocols}
```

#### Phase 2: License Files

**`packages/autoarr/LICENSE`** - GPL-3.0 (keep existing)

**`packages/autoarrx/LICENSE`** - Proprietary:
```
Copyright (C) 2025 AutoArr Contributors

All Rights Reserved.

This software is proprietary and confidential. Unauthorized copying,
modification, distribution, or use is strictly prohibited.

For licensing inquiries: hello@autoarr.io
```

**`packages/shared/LICENSE`** - MIT:
```
MIT License - Can be used by both GPL and proprietary code
```

**Root `/app/LICENSE`** - Dual License Notice:
```
AutoArr Monorepo
================

This repository contains multiple packages with different licenses:

1. packages/autoarr/ - GPL-3.0-or-later (Open Source)
2. packages/autoarrx/ - Proprietary (All Rights Reserved)
3. packages/shared/ - MIT (Permissive)

See individual package LICENSE files for details.
```

#### Phase 3: Package Configuration

**`packages/autoarr/pyproject.toml`**:
```toml
[tool.poetry]
name = "autoarr"
version = "1.0.0"
description = "Intelligent orchestration layer for media automation (GPL)"
license = "GPL-3.0-or-later"

[tool.poetry.dependencies]
python = "^3.11"
# ... dependencies
autoarr-shared = { path = "../shared", develop = true }

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**`packages/autoarrx/pyproject.toml`**:
```toml
[tool.poetry]
name = "autoarrx"
version = "1.0.0"
description = "Premium cloud intelligence for AutoArr"
license = "Proprietary"

[tool.poetry.dependencies]
python = "^3.11"
autoarr = { path = "../autoarr", develop = true }
autoarr-shared = { path = "../shared", develop = true }
# Premium dependencies

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### Phase 4: Docker Images

**GPL-only Build:**
```dockerfile
# Dockerfile.autoarr
FROM python:3.11-slim
WORKDIR /app
COPY packages/autoarr /app/autoarr
COPY packages/shared /app/shared
RUN pip install /app/autoarr
CMD ["python", "-m", "autoarr"]
```

**Full Build (with Premium):**
```dockerfile
# Dockerfile.full
FROM python:3.11-slim
WORKDIR /app
COPY packages/ /app/packages/
RUN pip install /app/packages/autoarr /app/packages/autoarrx
CMD ["python", "-m", "autoarr"]
```

#### Phase 5: CI/CD

```yaml
# .github/workflows/autoarr-ci.yml
name: AutoArr (GPL) CI
on: [push, pull_request]

jobs:
  test-gpl:
    runs-on: [self-hosted]
    steps:
      - uses: actions/checkout@v5
      - name: Test GPL package only
        run: |
          cd packages/autoarr
          poetry install
          poetry run pytest
```

```yaml
# .github/workflows/autoarrx-ci.yml
name: AutoArrX (Premium) CI
on: [push]  # Only on push, not PRs (keep private)
if: github.repository == 'FEAWServices/autoarr'  # Private repo only

jobs:
  test-premium:
    runs-on: [self-hosted]
    steps:
      - uses: actions/checkout@v5
      - name: Test premium package
        run: |
          cd packages/autoarrx
          poetry install
          poetry run pytest
```

---

## Migration Strategy

### Step 1: Create Structure (1 day)
```bash
1. Create packages/ directory structure
2. Move existing code to packages/autoarr/
3. Create packages/autoarrx/ skeleton
4. Create packages/shared/ with MIT license
5. Update all imports
```

### Step 2: License Files (1 day)
```bash
1. Create individual LICENSE files
2. Add license headers to all files
3. Create root dual-license notice
4. Update README files
```

### Step 3: Update Build System (1 day)
```bash
1. Create per-package pyproject.toml
2. Update Dockerfiles
3. Test GPL-only build
4. Test full build
```

### Step 4: Update CI/CD (1 day)
```bash
1. Split workflows
2. Add package-specific triggers
3. Test both pipelines
4. Update branch protection
```

### Step 5: Documentation (1 day)
```bash
1. Update ARCHITECTURE.md
2. Update CONTRIBUTING.md
3. Create MONOREPO.md guide
4. Update all file paths in docs
```

---

## Future Split (Pre-Launch)

When ready to make GPL code public:

```bash
# 1. Extract GPL package to new repo
git subtree split -P packages/autoarr -b autoarr-public
git remote add autoarr-public git@github.com:autoarr/autoarr.git
git push autoarr-public autoarr-public:main

# 2. Keep premium in private repo
mv packages/autoarrx/* .
rm -rf packages/

# 3. Shared code → npm package or pip package
cd packages/shared
npm publish @autoarr/shared
# or
poetry publish
```

---

## Shared Code Guidelines

**What Can Be Shared (packages/shared/ - MIT License):**
- ✅ TypeScript type definitions
- ✅ Utility functions (no business logic)
- ✅ API protocol definitions
- ✅ Data schemas (Pydantic models)
- ✅ Constants and enums

**What Cannot Be Shared (Must be duplicated or proprietary):**
- ❌ Business logic
- ❌ LLM prompt templates (competitive advantage)
- ❌ API implementations
- ❌ UI components with business logic
- ❌ Premium algorithms

**Example Shared Code:**

```python
# packages/shared/types/content.py (MIT)
from pydantic import BaseModel
from enum import Enum

class ContentType(Enum):
    MOVIE = "movie"
    TV = "tv"

class ContentRequest(BaseModel):
    """Shared schema for content requests."""
    query: str
    content_type: ContentType | None = None
```

---

## Directory Tree (After Restructure)

```
/app/
├── LICENSE                      # Dual license notice
├── README.md                    # Monorepo guide
├── pyproject.toml              # Workspace config
│
├── packages/
│   ├── autoarr/                # GPL-3.0 ✅ Public-ready
│   │   ├── LICENSE             # GPL-3.0
│   │   ├── README.md           # GPL docs
│   │   ├── pyproject.toml
│   │   ├── poetry.lock
│   │   ├── autoarr/
│   │   │   ├── __init__.py
│   │   │   ├── api/            # FastAPI
│   │   │   ├── ui/             # React
│   │   │   ├── mcp_servers/    # MCP implementations
│   │   │   └── shared/         # GPL-internal shared code
│   │   ├── tests/
│   │   ├── docker/
│   │   │   └── Dockerfile      # GPL-only image
│   │   └── .env.example
│   │
│   ├── autoarrx/               # Proprietary ❌ Private
│   │   ├── LICENSE             # Proprietary
│   │   ├── README.md           # Premium docs
│   │   ├── pyproject.toml
│   │   ├── poetry.lock
│   │   ├── autoarrx/
│   │   │   ├── __init__.py
│   │   │   ├── bridge/         # Secure connection service
│   │   │   │   ├── websocket_server.py
│   │   │   │   ├── encryption.py
│   │   │   │   └── license_validator.py
│   │   │   ├── cloud/          # Cloud services
│   │   │   │   ├── intelligence/  # Advanced LLM
│   │   │   │   ├── notifications/ # Smart notifications
│   │   │   │   ├── analytics/     # Predictive analytics
│   │   │   │   └── storage/       # Cloud storage
│   │   │   └── api/            # Premium API
│   │   ├── tests/
│   │   ├── docker/
│   │   │   └── Dockerfile      # Cloud service image
│   │   └── .env.example
│   │
│   └── shared/                 # MIT ✅ Shared by both
│       ├── LICENSE             # MIT
│       ├── README.md
│       ├── pyproject.toml
│       ├── autoarr_shared/
│       │   ├── __init__.py
│       │   ├── types/          # Shared types
│       │   │   ├── content.py
│       │   │   ├── config.py
│       │   │   └── events.py
│       │   ├── utils/          # Utilities
│       │   │   ├── crypto.py
│       │   │   ├── time.py
│       │   │   └── validation.py
│       │   └── protocols/      # API contracts
│       │       ├── bridge.py
│       │       └── mcp.py
│       └── tests/
│
├── docs/
│   ├── architecture/
│   │   └── adr/                # Architecture decisions
│   ├── autoarr/                # GPL docs
│   │   ├── QUICK_START.md
│   │   ├── API_REFERENCE.md
│   │   └── ...
│   ├── autoarrx/               # Premium docs
│   │   ├── PRICING.md
│   │   ├── PRIVACY.md
│   │   └── ...
│   └── MONOREPO.md             # Monorepo guide
│
└── .github/
    └── workflows/
        ├── autoarr-ci.yml      # GPL CI
        ├── autoarrx-ci.yml     # Premium CI
        ├── docs-ci.yml         # Docs validation
        └── docker-deploy.yml   # Multi-image builds
```

---

## Benefits

### During Development
1. **Fast Iteration** - Work in one codebase
2. **Shared Tooling** - One CI/CD setup
3. **Easy Refactoring** - Move code between packages easily
4. **Clear Boundaries** - Separate directories enforce separation

### Pre-Launch
5. **Easy Split** - `git subtree split` for GPL repo
6. **Verified Separation** - Community can audit GPL code
7. **Independent Releases** - Different version numbers

### Post-Launch
8. **Public Trust** - GPL code is genuinely separate
9. **Flexible Development** - Can develop in either repo
10. **Clear Licensing** - No confusion about what's open source

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accidentally mix GPL/proprietary | Legal issues | Pre-commit hooks, linters, code review |
| Complex imports | Confusion | Clear import conventions, documentation |
| Build system complexity | Slower builds | Layer Docker builds, cache dependencies |
| CI/CD overhead | Longer pipelines | Parallel jobs, conditional triggers |
| Import cycles | Build failures | Enforce dependency direction (shared → autoarr → autoarrx) |

---

## Dependency Rules

```
packages/shared/     (MIT)
       ↓
packages/autoarr/    (GPL) - Can use MIT
       ↓
packages/autoarrx/   (Proprietary) - Can use both MIT and GPL
```

**Enforced by:**
- Import linters (no reverse imports)
- Package dependencies in pyproject.toml
- Pre-commit hooks

---

## References

- [Monorepo Best Practices](https://monorepo.tools/)
- [GPL Compliance Guide](https://www.gnu.org/licenses/gpl-3.0.html)
- [Poetry Workspaces](https://python-poetry.org/docs/managing-dependencies/)
- [ADR-001: No Ollama](./001-no-ollama-dependency.md)
- [VISION_AND_PRICING.md](../../VISION_AND_PRICING.md)

---

_This ADR establishes the foundation for building both GPL and premium products in parallel._
