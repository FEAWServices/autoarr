# 🛡️ AutoArr - Early Error Detection Guide

This guide explains the "compile-time" validation system that catches errors **before** they reach CI, similar to how C catches linker/compiler errors.

## 🎯 Quick Reference

| Command                                    | When to Use                  | Time  |
| ------------------------------------------ | ---------------------------- | ----- |
| `./scripts/quick-validation.sh --fast`     | Quick check while developing | ~30s  |
| `./scripts/quick-validation.sh`            | Before pushing (full check)  | ~2min |
| `./scripts/quick-validation.sh --fix`      | Auto-fix formatting issues   | ~2min |
| `./scripts/quick-validation.sh --python`   | Python only                  | ~1min |
| `./scripts/quick-validation.sh --frontend` | Frontend only                | ~1min |

## 🔧 What Was Configured

### 1. VS Code Settings (`.vscode/settings.json`)

**Python:**

- **Pylance** with workspace-wide diagnostics
- **MyPy** integration for type checking
- **Flake8** for linting
- **Black** formatter on save

**TypeScript:**

- **Project-wide diagnostics** - shows errors across ALL files
- **4GB memory** for TypeScript server
- **ESLint** integration

**To see all project errors**: Open Problems panel (`Ctrl+Shift+M`)

### 2. Pre-Commit Hooks (`.pre-commit-config.yaml`)

Already configured with:

- **Black** - Python formatting
- **isort** - Import sorting
- **Flake8** - Python linting
- **MyPy** - Python type checking
- **Bandit** - Security scanning
- **Prettier** - Frontend formatting
- **Hadolint** - Dockerfile linting

Install hooks: `poetry run pre-commit install`

### 3. Quick Validation Script (`scripts/quick-validation.sh`)

Comprehensive local check that mimics CI:

- **MyPy** - Python type checking
- **Black/isort** - Python formatting
- **Flake8** - Python linting
- **TypeScript** - Frontend type checking
- **ESLint** - Frontend linting
- **Build verification**

### 4. CI Quick-Fail Job (`.github/workflows/ci.yml`)

New `⚡ Quick Type Check` job runs **immediately** and:

- Takes only 2-3 minutes
- Checks Python formatting (Black, isort)
- Checks TypeScript types
- **Fails fast** if there are issues
- **Blocks lint jobs** from wasting time

## 📋 VS Code Tasks

Press `Ctrl+Shift+P` → "Tasks: Run Task" → Choose:

### Validation

| Task                            | Description           |
| ------------------------------- | --------------------- |
| ⚡ Validate: Quick (Fast Mode)  | 30-second check       |
| ✅ Validate: Full (Before Push) | Complete validation   |
| 🔧 Validate: Auto-Fix           | Fix formatting issues |

### Python

| Task                         | Description            |
| ---------------------------- | ---------------------- |
| 🐍 Python: Type Check (MyPy) | Run MyPy type checker  |
| 🐍 Python: Lint (Flake8)     | Run Flake8 linter      |
| 🐍 Python: Format (Black)    | Auto-format with Black |
| 🧪 Python: Run Tests         | Run all tests          |

### Frontend

| Task                    | Description               |
| ----------------------- | ------------------------- |
| 🔍 Frontend: Type Check | Run TypeScript type check |
| 📝 Frontend: Lint       | Run ESLint                |
| 🔨 Frontend: Build      | Build frontend            |

## 🚦 Recommended Workflow

### While Developing

1. VS Code shows errors in Problems panel automatically
2. Fix red squiggles as you code

### Before Committing

```bash
# Pre-commit hooks run automatically
git commit -m "message"

# Or run manually
poetry run pre-commit run --all-files
```

### Before Pushing

```bash
# Quick check
./scripts/quick-validation.sh --fast

# Full check (recommended)
./scripts/quick-validation.sh

# Auto-fix formatting
./scripts/quick-validation.sh --fix
```

## 🔍 Troubleshooting

### Pre-commit hooks not running?

```bash
poetry run pre-commit install
```

### Only want to check one language?

```bash
./scripts/quick-validation.sh --python
./scripts/quick-validation.sh --frontend
```

## 📊 Error Detection Timeline

| Stage                 | Time    | What's Caught                |
| --------------------- | ------- | ---------------------------- |
| VS Code (as you type) | Instant | Type errors in open files    |
| Pre-commit hook       | ~30s    | All formatting & lint issues |
| Quick validation      | ~2min   | Full type + lint check       |
| CI Quick Type Check   | ~3min   | Server-side validation       |
| CI Full Lint          | ~10min  | Complete lint suite          |
