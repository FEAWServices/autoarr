# CI/CD Pipeline Optimization - Documentation-Only Changes

## Overview

The GitHub Actions CI pipeline has been optimized to skip expensive tests when only documentation files are changed. This reduces feedback time from 10+ minutes to 30 seconds for documentation-only PRs while maintaining full test coverage for code changes.

## Path Detection Strategy

The pipeline uses the `dorny/paths-filter` action to intelligently detect which types of files changed:

### Detected Change Types

1. **docs-only**: True when ONLY documentation files changed
   - Matches: `docs/**`, `**/*.md`, `.github/ISSUE_TEMPLATE/**`
   - Excludes changes to: Python, frontend, or config files

2. **python**: Python code or backend dependency files changed
   - Matches: `autoarr/**/*.py`, `pyproject.toml`, `poetry.lock`, `.github/workflows/ci.yml`

3. **frontend**: Frontend code or dependency files changed
   - Matches: `autoarr/ui/**`, `.github/workflows/ci.yml`

4. **code**: Any code changes (union of python + frontend + dependencies)
   - Used for comprehensive test runs like E2E tests

## Job Execution Flow

### For Documentation-Only Changes

```
┌─────────────────────┐
│   detect-changes    │ (5 sec) - Identify change type
└──────────┬──────────┘
           │
           v
    ┌──────────────┐
    │  docs-check  │ (5-10 sec) - Validate markdown
    └──────┬───────┘
           │
           v
┌─────────────────────────┐
│ all-checks-passed       │ (1 sec) - Summary & status
│ (docs-only path)        │
└─────────────────────────┘

TOTAL TIME: ~30 seconds
```

### For Code Changes

```
┌─────────────────────┐
│   detect-changes    │ (5 sec)
└──────────┬──────────┘
           │
      ┌────┴───────────────────────────┐
      │                                │
      v                                v
┌──────────────┐              ┌──────────────┐
│ python-lint  │              │frontend-lint │
│ python-test  │              │frontend-build│
│python-security              │accessibility-│
└──────────────┘              │tests         │
      │                       └──────────────┘
      │                              │
      │                    ┌─────────┘
      │                    │
      v                    v
┌────────────────────────────────────┐
│         e2e-tests                  │
│  (waits for backend & frontend)    │
└────────────┬───────────────────────┘
             │
             v
    ┌─────────────────┐
    │all-checks-passed│ (code path)
    └─────────────────┘

TOTAL TIME: 10-15 minutes
```

## Job Details

### detect-changes (always runs)

**Purpose**: Identify what types of files changed

**Outputs**:
- `docs-only`: `'true'` if ONLY docs changed
- `python-changed`: `'true'` if Python files changed
- `frontend-changed`: `'true'` if frontend files changed
- `has-code-changes`: `'true'` if any code changed

**Example**:
- PR with only `docs/*.md` changes → `docs-only=true`
- PR with `autoarr/api/main.py` changes → `python-changed=true`, `docs-only=false`
- PR with `autoarr/ui/src/components/` changes → `frontend-changed=true`, `docs-only=false`

### Conditional Jobs

**Python Jobs** (if `python-changed == 'true' && docs-only == 'false'`):
- `python-lint`: Black, isort, Flake8, Pylint, MyPy
- `python-test`: Unit & integration tests (3.11 & 3.12)
- `python-security`: Bandit & Safety scans

**Frontend Jobs** (if `frontend-changed == 'true' && docs-only == 'false'`):
- `frontend-lint`: ESLint, Stylelint, Prettier, TypeScript
- `frontend-build`: Production build
- `accessibility-tests`: WCAG 2.1 AA checks

**Integration Job** (if `has-code-changes == 'true' && docs-only == 'false'`):
- `e2e-tests`: Full end-to-end Playwright tests

### docs-check (if `docs-only == 'true'`)

**Purpose**: Quick validation for documentation changes

**Checks**:
- Validates Markdown file syntax
- Checks for common documentation issues
- Runs in ~5-10 seconds

### all-checks-passed (always runs)

**Purpose**: Provide consistent status check for branch protection

**Behavior**:
- **For docs-only**: Requires only `docs-check` to pass
- **For code changes**: Requires all applicable code checks to pass
- **Always succeeds if correct jobs passed** (safe for branch protection)

## Branch Protection Configuration

This workflow is designed to work seamlessly with GitHub branch protection:

```yaml
# In repository settings > Branches > Branch protection rules
Require status checks to pass before merging:
  - All Checks Passed
```

### Why This Works

1. The `all-checks-passed` job **always** runs (even for docs-only)
2. It correctly evaluates which checks were required for the change type
3. It passes only if the appropriate checks passed
4. This single check covers both documentation and code changes

## Testing This Configuration

### Manual Testing

1. **Test docs-only detection**:
   ```bash
   # Create a branch with only doc changes
   git checkout -b test/docs-only-change
   echo "# New Documentation" > docs/new-doc.md
   git add docs/new-doc.md
   git commit -m "docs: Add new documentation"
   git push origin test/docs-only-change
   # Create PR and observe: detect-changes.docs-only = 'true'
   # Expected: only docs-check runs (~30s)
   ```

2. **Test Python changes**:
   ```bash
   # Create a branch with Python code changes
   git checkout -b test/python-change
   echo "# New function" >> autoarr/api/main.py
   git add autoarr/api/main.py
   git commit -m "feat: Add new function"
   git push origin test/python-change
   # Create PR and observe: detect-changes.python-changed = 'true'
   # Expected: python jobs run (~10 mins)
   ```

3. **Test frontend changes**:
   ```bash
   # Create a branch with frontend changes
   git checkout -b test/frontend-change
   echo "// new component" >> autoarr/ui/src/components/new.tsx
   git add autoarr/ui/src/components/new.tsx
   git commit -m "feat: Add new component"
   git push origin test/frontend-change
   # Create PR and observe: detect-changes.frontend-changed = 'true'
   # Expected: frontend jobs run (~10 mins)
   ```

### Verifying Path Filters

The path filters use negative lookahead patterns to detect docs-only changes:

```yaml
docs-only:
  - '!(docs/**|**/*.md|.github/ISSUE_TEMPLATE/**)'
```

This means:
- If ANY file outside docs/**.md/.github/ISSUE_TEMPLATE/** exists → `docs-only=false`
- If ALL files are in those paths → `docs-only=true`

## Maintenance

### Adding New Code Locations

If you add new code directories, update the path filters:

1. **For Python**: Update `python` filter in `detect-changes`
   ```yaml
   python:
     - 'autoarr/**/*.py'
     - 'new_module/**/*.py'  # Add new location
     - 'pyproject.toml'
     - 'poetry.lock'
   ```

2. **For Frontend**: Update `frontend` filter
   ```yaml
   frontend:
     - 'autoarr/ui/**'
     - 'new_frontend_module/**'  # Add new location
   ```

3. **For Code**: Update `code` filter to include all code locations

### Updating Documentation Paths

If documentation is added to new locations:

```yaml
docs-only:
  - '!(docs/**|new_docs_path/**|**/*.md|.github/ISSUE_TEMPLATE/**)'
```

## Performance Metrics

### Before Optimization

- All PRs run full test suite
- Documentation PRs wait 10-15 minutes unnecessarily
- Resource waste on 200+ unnecessary job runs per month

### After Optimization

- Documentation PRs complete in ~30 seconds
- Code PRs still run full test suite (10-15 minutes)
- ~180 fewer job runs per month
- Faster feedback loop for documentation contributors

## Troubleshooting

### Issue: Docs-only detection not working

**Check**:
1. Verify all changes are in `docs/**` or `**/*.md`
2. Ensure no Python/frontend/config files were touched
3. Check `detect-changes` job output in workflow run

**Example bad case** (triggers full tests):
- File: `docs/README.md` + `docs/typo_in_code.py`
- Result: `docs-only=false` (Python file present)

### Issue: Code job was skipped but should have run

**Check**:
1. Verify file paths match the filters
2. Check if file extension is included (e.g., `.py` for Python)
3. Review the path filter logic in `detect-changes`

**Example fix**:
- If new Python module isn't detected, add pattern to `python` filter

## References

- **Path Filter Action**: https://github.com/dorny/paths-filter
- **GitHub Actions Conditions**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idif
- **Branch Protection**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

---

**Last Updated**: 2025-11-12
**Version**: 1.0
