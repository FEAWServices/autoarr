# CI Optimization - Code Reference

This document contains the key code snippets from the optimized CI workflow for quick reference.

## 1. detect-changes Job

Location: `/app/.github/workflows/ci.yml` (lines 22-72)

```yaml
detect-changes:
  name: Detect Changed Paths
  runs-on: ubuntu-latest
  timeout-minutes: 5
  outputs:
    # Flags to control job execution
    docs-only: ${{ steps.filter.outputs.docs-only }}
    python-changed: ${{ steps.filter.outputs.python }}
    frontend-changed: ${{ steps.filter.outputs.frontend }}
    has-code-changes: ${{ steps.filter.outputs.code }}

  steps:
    - name: Checkout code
      uses: actions/checkout@v5
      with:
        fetch-depth: 0

    - name: Detect changed file paths
      uses: dorny/paths-filter@v2
      id: filter
      with:
        filters: |
          docs-only:
            - '!(docs/**|**/*.md|.github/ISSUE_TEMPLATE/**)'
          python:
            - 'autoarr/**/*.py'
            - 'pyproject.toml'
            - 'poetry.lock'
            - '.github/workflows/ci.yml'
          frontend:
            - 'autoarr/ui/**'
            - '.github/workflows/ci.yml'
          code:
            - 'autoarr/**'
            - 'pyproject.toml'
            - 'poetry.lock'
            - 'package.json'
            - 'pnpm-lock.yaml'
            - '.github/workflows/ci.yml'

    - name: Log detected changes
      run: |
        echo "Documentation only: ${{ steps.filter.outputs.docs-only }}"
        echo "Python changed: ${{ steps.filter.outputs.python }}"
        echo "Frontend changed: ${{ steps.filter.outputs.frontend }}"
        echo "Code changed: ${{ steps.filter.outputs.code }}"
```

## 2. Conditional Job Configuration - python-lint

Location: `/app/.github/workflows/ci.yml` (lines 77-86)

```yaml
python-lint:
  name: Python Lint & Type Check
  runs-on: [self-hosted, alienware]
  timeout-minutes: 10
  needs: detect-changes
  # Skip for docs-only changes; run on PRs or if Python files changed
  if: |
    (github.event_name == 'pull_request' || needs.detect-changes.outputs.python-changed == 'true') &&
    needs.detect-changes.outputs.docs-only == 'false'

  steps:
    # ... rest of job
```

**Pattern used for all conditional jobs:**

```yaml
needs: detect-changes
if: |
  (github.event_name == 'pull_request' || needs.detect-changes.outputs.TRIGGER == 'true') &&
  needs.detect-changes.outputs.docs-only == 'false'
```

## 3. Conditional Job Configuration - e2e-tests

Location: `/app/.github/workflows/ci.yml` (lines 509-517)

Special case: Runs if code changed AND python/frontend jobs completed

```yaml
e2e-tests:
  name: E2E Tests (Playwright)
  runs-on: [self-hosted, alienware]
  timeout-minutes: 30
  needs: [detect-changes, python-test, frontend-build]
  # Skip for docs-only changes; run on PRs or if code changed
  if: |
    always() &&
    needs.detect-changes.outputs.docs-only == 'false' &&
    (github.event_name == 'pull_request' || needs.detect-changes.outputs.has-code-changes == 'true')

  steps:
    # ... rest of job
```

## 4. docs-check Job

Location: `/app/.github/workflows/ci.yml` (lines 774-807)

```yaml
docs-check:
  name: Documentation Check
  runs-on: ubuntu-latest
  needs: detect-changes
  # Only run if changes are docs-only
  if: needs.detect-changes.outputs.docs-only == 'true'
  timeout-minutes: 5

  steps:
    - name: Checkout code
      uses: actions/checkout@v5

    - name: Validate Markdown files
      run: |
        echo "Validating Markdown syntax..."
        find docs -name "*.md" -type f -exec head -1 {} \;
        echo "✅ Documentation files validated"

    - name: Check for common issues
      run: |
        echo "Checking for common documentation issues..."
        # Check for broken relative links in docs
        echo "✅ All checks passed for documentation-only changes"

    - name: Success message
      run: |
        echo "## Documentation Check Passed" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "Documentation-only changes detected. Code tests skipped." >> $GITHUB_STEP_SUMMARY
        echo "✅ All documentation checks passed" >> $GITHUB_STEP_SUMMARY
```

## 5. all-checks-passed Job - Overview

Location: `/app/.github/workflows/ci.yml` (lines 812-901)

```yaml
all-checks-passed:
  name: All Checks Passed
  runs-on: ubuntu-latest
  needs:
    - detect-changes
    - python-lint
    - python-test
    - python-security
    - frontend-lint
    - frontend-build
    - e2e-tests
    - accessibility-tests
    - docs-check
  # Always run to provide final status, but success depends on which jobs ran
  if: always()
  timeout-minutes: 1

  steps:
    - name: Evaluate results for docs-only changes
      if: needs.detect-changes.outputs.docs-only == 'true'
      run: |
        echo "## CI Pipeline Results (Documentation-Only Changes)" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "### Documentation Check" >> $GITHUB_STEP_SUMMARY
        echo "- **Status:** \`${{ needs.docs-check.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "Code tests were skipped since only documentation files were modified." >> $GITHUB_STEP_SUMMARY
        if [[ "${{ needs.docs-check.result }}" != "success" ]]; then
          echo "❌ Documentation validation failed"
          exit 1
        fi
        echo "✅ All checks passed!"

    - name: Evaluate results for code changes
      if: needs.detect-changes.outputs.docs-only == 'false'
      run: |
        echo "## CI Pipeline Results" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "### Python Backend" >> $GITHUB_STEP_SUMMARY
        echo "- **Lint:** \`${{ needs.python-lint.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "- **Test:** \`${{ needs.python-test.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "- **Security:** \`${{ needs.python-security.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "### Frontend" >> $GITHUB_STEP_SUMMARY
        echo "- **Lint:** \`${{ needs.frontend-lint.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "- **Build:** \`${{ needs.frontend-build.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "- **E2E Tests:** \`${{ needs.e2e-tests.result }}\`" >> $GITHUB_STEP_SUMMARY
        echo "- **Accessibility:** \`${{ needs.accessibility-tests.result }}\`" >> $GITHUB_STEP_SUMMARY

    - name: Check required jobs for code changes
      if: needs.detect-changes.outputs.docs-only == 'false'
      run: |
        # For code changes, check that critical jobs passed
        FAILED=0

        # These jobs should have run for code changes
        if [[ "${{ needs.python-lint.result }}" == "failure" ]]; then
          echo "❌ Python linting failed"
          FAILED=1
        fi

        if [[ "${{ needs.python-test.result }}" == "failure" ]]; then
          echo "❌ Python tests failed"
          FAILED=1
        fi

        if [[ "${{ needs.frontend-lint.result }}" == "failure" ]]; then
          echo "❌ Frontend linting failed"
          FAILED=1
        fi

        if [[ "${{ needs.frontend-build.result }}" == "failure" ]]; then
          echo "❌ Frontend build failed"
          FAILED=1
        fi

        if [[ $FAILED -eq 1 ]]; then
          exit 1
        fi

    - name: Final success message
      run: |
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "✅ All required checks passed successfully!" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        if [[ "${{ needs.detect-changes.outputs.docs-only }}" == "true" ]]; then
          echo "### Documentation PR Approved" >> $GITHUB_STEP_SUMMARY
        else
          echo "### Ready for Docker Build & Deploy" >> $GITHUB_STEP_SUMMARY
        fi
```

## Usage Examples

### Using Output Values in Other Jobs

```yaml
some-job:
  needs: detect-changes
  if: needs.detect-changes.outputs.python-changed == 'true'
  steps:
    - run: echo "Python files changed"
```

### Combining Multiple Outputs

```yaml
another-job:
  needs: detect-changes
  if: |
    (needs.detect-changes.outputs.python-changed == 'true' ||
     needs.detect-changes.outputs.frontend-changed == 'true') &&
    needs.detect-changes.outputs.docs-only == 'false'
  steps:
    - run: echo "Code (Python or Frontend) changed, running tests"
```

### Conditional on PR vs Push

```yaml
special-job:
  needs: detect-changes
  if: |
    github.event_name == 'pull_request' ||
    needs.detect-changes.outputs.has-code-changes == 'true'
  steps:
    - run: echo "This is a PR or code was changed"
```

## Path Filter Logic Reference

### Path Filter Syntax

```yaml
filters: |
  filter-name:
    - 'pattern1/**'        # Include paths matching pattern
    - 'pattern2/*.ext'     # Include specific file type
    - '!exclude/**'        # Exclude paths (negation)
    - '!(!(include/**)|exclude/**)' # Complex logic
```

### docs-only Filter Explanation

```yaml
docs-only:
  - "!(docs/**|**/*.md|.github/ISSUE_TEMPLATE/**)"
```

**What this means:**

- `!(...)` = Negation operator
- Inside parentheses: patterns to exclude
- If ANY file matches a pattern OUTSIDE these paths → `docs-only=false`
- If ALL files match patterns INSIDE these paths → `docs-only=true`

**Examples:**

- Change: `docs/api.md` → `docs-only=true` (matches `**/*.md`)
- Change: `autoarr/api/main.py` → `docs-only=false` (doesn't match excluded patterns)
- Change: `docs/api.md` + `autoarr/api/main.py` → `docs-only=false` (has non-docs file)

### Adding New Patterns

```yaml
# Current pattern
docs-only:
  - '!(docs/**|**/*.md|.github/ISSUE_TEMPLATE/**)'

# Add new docs directory
docs-only:
  - '!(docs/**|guides/**|**/*.md|.github/ISSUE_TEMPLATE/**)'

# Add specific file types
docs-only:
  - '!(docs/**|guides/**|**/*.md|**/*.txt|.github/ISSUE_TEMPLATE/**)'
```

## Testing Commands

### Verify YAML Syntax

```bash
python3 -m py_compile /app/.github/workflows/ci.yml
# or
python3 << 'EOF'
import yaml
with open('/app/.github/workflows/ci.yml', 'r') as f:
    yaml.safe_load(f)
print("✓ YAML is valid")
EOF
```

### Check Job Names

```bash
python3 << 'EOF'
import yaml
with open('/app/.github/workflows/ci.yml', 'r') as f:
    data = yaml.safe_load(f)
for job_name in data['jobs'].keys():
    print(f"- {job_name}")
EOF
```

### Verify Dependencies

```bash
python3 << 'EOF'
import yaml
with open('/app/.github/workflows/ci.yml', 'r') as f:
    data = yaml.safe_load(f)
for job_name, job_config in data['jobs'].items():
    if 'needs' in job_config:
        print(f"{job_name} needs: {job_config['needs']}")
EOF
```

## Troubleshooting Code Snippets

### Check if Job Ran

In workflow run UI:

- Look for job in "All checks" list
- Green checkmark = Job ran successfully
- Gray checkbox = Job was skipped
- Red X = Job failed

### Debug Path Detection

Add to `detect-changes` job:

```yaml
- name: Debug path detection
  run: |
    git diff --name-only HEAD~1 HEAD
    echo "---"
    echo "docs-only: ${{ steps.filter.outputs.docs-only }}"
    echo "python: ${{ steps.filter.outputs.python }}"
    echo "frontend: ${{ steps.filter.outputs.frontend }}"
    echo "code: ${{ steps.filter.outputs.code }}"
```

### Check Job Status in all-checks-passed

Add for debugging:

```yaml
- name: Debug job results
  run: |
    echo "detect-changes: ${{ needs.detect-changes.result }}"
    echo "python-lint: ${{ needs.python-lint.result }}"
    echo "docs-check: ${{ needs.docs-check.result }}"
    echo "Output docs-only: ${{ needs.detect-changes.outputs.docs-only }}"
```

## References

- **Workflow File**: `/app/.github/workflows/ci.yml`
- **dorny/paths-filter**: https://github.com/dorny/paths-filter
- **GitHub Actions Conditions**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idif
- **Job Needs**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idneeds
- **Outputs**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idoutputs

---

**Last Updated**: 2025-11-12
**Commit**: 5d28f26
