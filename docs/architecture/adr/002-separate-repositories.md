# ADR-002: Separate Repositories for GPL and Premium (AutoArr + AutoArr Premium)

**Date:** 2025-01-12
**Status:** Accepted
**Deciders:** AutoArr Core Team
**Technical Story:** Separate GPL and Premium code while maintaining development efficiency

---

## Context and Problem Statement

AutoArr has two products:

1. **AutoArr (GPL-3.0)** - 100% open source, local-only, free forever
2. **AutoArr Premium** - ML-powered features, advanced recovery, licensed product

We need a repository structure that:

- Clearly separates GPL from proprietary code
- Prevents accidental license violations
- Allows efficient development across both products
- Enables public release of GPL version while keeping Premium private
- Maintains clear licensing boundaries

## Decision Drivers

- **Legal Clarity**: GPL and proprietary code MUST be completely separated
- **Development Efficiency**: Want to iterate quickly without constant repo switching
- **Future Flexibility**: GPL version can go public at any time without exposing Premium code
- **Build System**: Each product builds and deploys independently
- **Open Source Trust**: Community can verify GPL code has no proprietary dependencies

## Considered Options

### Option 1: Monorepo with Subdirectories

**Structure:**

```
autoarr/
├── autoarr/          # GPL-3.0
├── autoarr-premium/  # Proprietary
└── shared/           # MIT shared utilities
```

**Pros:**

- ✅ Fast iteration (one repo)
- ✅ Easy code sharing
- ✅ Single CI/CD setup

**Cons:**

- ❌ Risk of mixing GPL/proprietary code
- ❌ Premium code visible in GPL repo history
- ❌ Complex git subtree split when going public
- ❌ Harder to audit GPL purity

### Option 2: Separate Repositories + VS Code Workspace ✅ CHOSEN

**Structure:**

```
FEAWServices/autoarr          (Private → Public when ready)
  ├── autoarr/                # GPL-3.0 code
  ├── docs/                   # GPL documentation
  ├── LICENSE                 # GPL-3.0
  └── README.md               # GPL project

FEAWServices/autoarr-premium  (Private, stays private)
  ├── autoarr_premium/        # Proprietary code
  ├── ml/                     # ML training/inference
  ├── licensing/              # License validation
  ├── docs/                   # Premium documentation
  ├── LICENSE                 # Proprietary
  └── README.md               # Premium project

Development:
  └── autoarr.code-workspace  # VS Code multi-root workspace
```

**Pros:**

- ✅ **Perfect legal separation** - No GPL/proprietary mixing possible
- ✅ **Clean history** - GPL repo can go public instantly
- ✅ **Independent versioning** - v1.0.0 GPL, v2.5.0 Premium
- ✅ **Separate CI/CD** - GPL → Docker Hub, Premium → Azure
- ✅ **Clear dependencies** - Premium can depend on GPL (import as package), not vice versa
- ✅ **VS Code workspace** - Still feels like one project during development

**Cons:**

- ⚠️ Slightly slower switching (minimal with workspace)
- ⚠️ Must avoid code duplication (use shared package if needed)

### Option 3: Git Submodules

**Structure:**

```
autoarr-workspace/
├── autoarr/ (submodule)
└── autoarr-premium/ (submodule)
```

**Pros:**

- ✅ Technically linked repos

**Cons:**

- ❌ Submodules are notoriously painful
- ❌ Complex for contributors
- ❌ CI/CD nightmare

---

## Decision Outcome

**Chosen option:** "Separate Repositories + VS Code Workspace" (Option 2)

This provides the best balance of legal safety, development efficiency, and future flexibility.

### Implementation

#### Repository Structure

**AutoArr (GPL) Repository:**

```
FEAWServices/autoarr/
├── autoarr/
│   ├── api/              # FastAPI backend
│   ├── ui/               # React frontend
│   ├── mcp_servers/      # MCP implementations
│   ├── shared/           # Internal shared code
│   └── tests/            # Test suite
├── docs/
│   ├── architecture/adr/ # Architecture decisions
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   └── QUICK-START.md
├── .github/
│   └── workflows/
│       ├── ci.yml        # Tests + Docker Hub publish
│       └── docs-ci.yml
├── Dockerfile
├── docker-compose.yml
├── LICENSE               # GPL-3.0-or-later
├── pyproject.toml
└── README.md
```

**AutoArr Premium Repository:**

```
FEAWServices/autoarr-premium/
├── autoarr_premium/
│   ├── services/         # Premium services
│   ├── ml/               # ML training/inference
│   ├── licensing/        # License system
│   └── api/              # Premium API extensions
├── infrastructure/
│   └── terraform/        # Azure deployment
├── docs/
│   ├── architecture/adr/ # Premium-specific ADRs
│   ├── ARCHITECTURE.md
│   └── VISION.md
├── .github/
│   └── workflows/
│       ├── ci.yml        # Tests
│       └── azure-deploy.yml  # Azure deployment
├── Dockerfile
├── LICENSE               # Proprietary
├── pyproject.toml
└── README.md
```

#### VS Code Workspace Configuration

`autoarr.code-workspace`:

```json
{
  "folders": [
    {
      "name": "AutoArr (GPL-3.0)",
      "path": "."
    },
    {
      "name": "AutoArr Premium (Proprietary)",
      "path": "../autoarr-premium"
    }
  ]
}
```

#### Dependency Management

**Premium can import GPL:**

```python
# In autoarr-premium/pyproject.toml
[tool.poetry.dependencies]
autoarr = { path = "../autoarr", develop = true }  # Local dev
# OR
autoarr = "^1.0.0"  # Published package
```

**GPL NEVER imports Premium:**

- GPL must be completely standalone
- No Premium dependencies or references

#### Development Workflow

1. **Clone both repos:**

   ```bash
   git clone git@github.com:FEAWServices/autoarr.git
   git clone git@github.com:FEAWServices/autoarr-premium.git
   ```

2. **Open workspace:**

   ```bash
   code autoarr/autoarr.code-workspace
   ```

3. **Work across both repos** with unified search, navigation, and terminal

4. **Independent commits/PRs:**
   - GPL changes → `autoarr` repo
   - Premium changes → `autoarr-premium` repo

#### Deployment Targets

**GPL → Docker Hub:**

```bash
docker pull autoarr/autoarr:latest
```

**Premium → Azure Container Registry:**

```bash
docker pull autoarr.azurecr.io/autoarr-premium:latest
```

---

## Positive Consequences

- ✅ **Legal safety** - Zero risk of GPL/proprietary code mixing
- ✅ **Clean public release** - GPL repo can go public instantly
- ✅ **Independent evolution** - Each product versions/releases independently
- ✅ **Clear licensing** - Community can audit GPL purity
- ✅ **Efficient development** - VS Code workspace feels like monorepo
- ✅ **Flexible deployment** - GPL: Docker Hub, Premium: Azure

## Negative Consequences

- ⚠️ **Code duplication risk** - Must be disciplined about shared utilities
- ⚠️ **Two CI/CD pipelines** - More infrastructure to maintain
- ⚠️ **Context switching** - Slight overhead when working across repos (mitigated by workspace)

## Mitigation Strategies

### Avoiding Code Duplication

**Option A: Publish shared package (future):**

```bash
pip install autoarr-shared  # MIT-licensed shared utilities
```

**Option B: Copy minimal utilities (current):**

- Accept some duplication for simplicity
- Only share critical utilities

### Development Efficiency

- ✅ Use VS Code workspace (done)
- ✅ Consistent tooling (Poetry, Black, pytest)
- ✅ Shared pre-commit hooks configuration
- ✅ Cross-repo search in VS Code

---

## Compliance Checklist

- [x] GPL repo contains ONLY GPL-3.0 code
- [x] Premium repo clearly marked as Proprietary
- [x] No Premium code references in GPL repo
- [x] Premium can import GPL (one-way dependency)
- [x] Separate CI/CD pipelines
- [x] Separate deployment targets
- [x] VS Code workspace for development efficiency

---

## References

- [GPL-3.0 License](https://www.gnu.org/licenses/gpl-3.0.html)
- [ADR-001: No Ollama Dependency](./001-no-ollama-dependency.md)
- [VISION_AND_PRICING.md](/docs/VISION_AND_PRICING.md)
- [AutoArr Premium Repository](https://github.com/FEAWServices/autoarr-premium)

---

_This ADR establishes the foundation for maintaining strict GPL/proprietary separation while enabling efficient development._
