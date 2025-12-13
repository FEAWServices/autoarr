# Security Scan Command

Performs a comprehensive security audit of the AutoArr codebase, focusing on
common vulnerabilities, dependency security, and API security.

## Usage

```
/security-scan [path]
```

If no path provided, scans the entire codebase.

## Step 1: Dependency Vulnerabilities

```bash
# Check for known vulnerabilities in Python dependencies
poetry run safety check

# Run bandit security scanner
poetry run bandit -r autoarr/ -ll

# Check for outdated packages
poetry show --outdated
```

## Step 2: Secret Detection

Scan for accidentally committed secrets:

```bash
# Search for potential secrets
grep -r -E "(api[_-]?key|secret|password|token|credential)" \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.json" --include="*.env*" \
  autoarr/ \
  | grep -v "node_modules" \
  | grep -v ".test." \
  | grep -v "__pycache__" \
  | grep -v "os.environ" \
  | grep -v "# " \
  | head -50

# Check for hardcoded strings that look like secrets
grep -r -E "['\"][a-zA-Z0-9]{32,}['\"]" \
  --include="*.py" --include="*.ts" \
  autoarr/ \
  | grep -v "node_modules" \
  | grep -v ".test." \
  | head -20
```

## Step 3: API Security Audit

### Check for Input Validation

```bash
# Find endpoints without Pydantic models
grep -r "@router\.(get\|post\|put\|delete)" autoarr/api/routers/ \
  --include="*.py" \
  -A5 \
  | grep -v "BaseModel\|Depends"

# Check for raw SQL (injection risk)
grep -r "execute\|raw" autoarr/ \
  --include="*.py" \
  | grep -v ".test." \
  | grep -v "# "
```

### Check for Authentication

```bash
# Find endpoints that might be missing auth
grep -rn "def.*async\|def.*await" autoarr/api/routers/ \
  --include="*.py" \
  | grep -v "Depends"
```

## Step 4: MCP Server Security

```bash
# Check for proper API key handling
grep -r "api_key\|apikey" autoarr/mcp_servers/ \
  --include="*.py" \
  | grep -v ".test."

# Verify no secrets logged
grep -r "logger\.\|print\(" autoarr/mcp_servers/ \
  --include="*.py" \
  | grep -i "key\|token\|secret"
```

## Step 5: Frontend Security

```bash
# Check for XSS vulnerabilities
grep -r "dangerouslySetInnerHTML\|innerHTML" autoarr/ui/src/ \
  --include="*.tsx" --include="*.ts"

# Check for hardcoded URLs
grep -r "http://\|https://" autoarr/ui/src/ \
  --include="*.tsx" --include="*.ts" \
  | grep -v "localhost\|127.0.0.1" \
  | head -20
```

## Step 6: Error Handling Audit

```bash
# Find empty except blocks
grep -rA2 "except.*:" autoarr/ \
  --include="*.py" \
  | grep -E "except.*:\s*$\|pass$" \
  | head -20

# Find broad exception handling
grep -r "except Exception\|except:" autoarr/ \
  --include="*.py" \
  | grep -v ".test." \
  | head -20
```

## Step 7: Generate Security Report

```markdown
## Security Scan Report

**Date:** [Current Date]
**Scanned By:** Claude Security Scanner
**Repository:** AutoArr

### Summary

| Category         | Issues Found | Severity          |
| ---------------- | ------------ | ----------------- |
| Dependencies     | [count]      | [high/medium/low] |
| Secrets          | [count]      | [high/medium/low] |
| API Security     | [count]      | [high/medium/low] |
| Input Validation | [count]      | [high/medium/low] |
| Error Handling   | [count]      | [high/medium/low] |
| Frontend         | [count]      | [high/medium/low] |

### Critical Issues (must fix immediately)

[List any critical security issues]

### High Priority Issues (fix before merge)

[List high priority issues]

### Medium Priority Issues (fix in sprint)

[List medium priority issues]

### Recommendations

[List recommendations for improving security posture]

### Files Reviewed

[List of files that were scanned]
```

## Automated Security Tools

### Bandit (Python SAST)

```bash
# Run bandit with high severity only
poetry run bandit -r autoarr/ -ll -ii

# Generate JSON report
poetry run bandit -r autoarr/ -f json -o bandit-report.json
```

### Safety (Dependency Check)

```bash
# Check for vulnerable dependencies
poetry run safety check

# Generate JSON report
poetry run safety check --json > safety-report.json
```

## Severity Guidelines

| Severity    | Description                             | Action           |
| ----------- | --------------------------------------- | ---------------- |
| 🔴 Critical | Active vulnerability, data exposure     | Fix immediately  |
| 🟠 High     | Injection, auth bypass, secret exposure | Fix before merge |
| 🟡 Medium   | Info leakage, weak validation           | Fix in sprint    |
| 🔵 Low      | Best practice violation                 | Track in backlog |

## AutoArr-Specific Security Checks

### API Key Handling

1. **Never log API keys** - Check all logging statements
2. **Store in environment** - Use `os.environ` or settings
3. **Validate on use** - Check keys before API calls
4. **Mask in errors** - Don't expose keys in error messages

### External Service Communication

1. **Use HTTPS** - All external calls should use HTTPS
2. **Verify certificates** - Don't disable SSL verification
3. **Timeout all requests** - Prevent hanging connections
4. **Rate limit** - Don't overwhelm external services

### LLM Security

1. **Sanitize prompts** - Don't pass user input directly to LLM
2. **Validate responses** - Don't trust LLM output blindly
3. **Limit token usage** - Prevent prompt injection attacks
4. **Log safely** - Don't log full prompts/responses

## CI Integration

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: poetry install

      - name: Run Bandit
        run: poetry run bandit -r autoarr/ -ll -ii

      - name: Run Safety
        run: poetry run safety check

      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
```
