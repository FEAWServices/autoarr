# E2E Test Command

Run Playwright end-to-end tests for the AutoArr frontend. Tests MUST run inside
the Docker container for reliable results.

## Usage

```
/e2e-test [pattern]
```

Examples:

- `/e2e-test` - Run all E2E tests
- `/e2e-test home` - Run tests matching "home"
- `/e2e-test tests/settings.spec.ts` - Run specific file

## Prerequisites

The local test container must be running:

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d
```

## Step 1: Verify Container Status

```bash
# Check if container is running
DOCKER_HOST=unix:///var/run/docker.sock docker ps --filter "name=autoarr-local"

# Check container health
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -s http://localhost:8088/health

# View container logs if issues
DOCKER_HOST=unix:///var/run/docker.sock docker logs autoarr-local --tail 50
```

## Step 2: Apply Latest Code Changes

If you've made code changes, they need to be copied to the container:

```bash
# Build frontend
cd /app/autoarr/ui && pnpm run build

# Copy frontend build to container
DOCKER_HOST=unix:///var/run/docker.sock docker cp /app/autoarr/ui/dist/. autoarr-local:/app/autoarr/ui/dist/

# Copy backend Python files if changed
DOCKER_HOST=unix:///var/run/docker.sock docker cp /app/autoarr/api/. autoarr-local:/app/autoarr/api/

# Restart container to apply changes
DOCKER_HOST=unix:///var/run/docker.sock docker restart autoarr-local

# Re-install httpx after restart (required for MCP clients)
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local pip install httpx --quiet
```

## Step 3: Run E2E Tests

### Using the Helper Script (Recommended)

```bash
# Run all tests
./scripts/run-e2e-tests.sh

# Run specific file
./scripts/run-e2e-tests.sh tests/home.spec.ts

# Run tests matching pattern
./scripts/run-e2e-tests.sh "dashboard"
```

### Manual Execution

```bash
# Run all tests
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test --config=playwright-container.config.ts"

# Run specific test file
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test tests/home.spec.ts --config=playwright-container.config.ts"

# Run with pattern
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test -g 'dashboard' --config=playwright-container.config.ts"
```

## Step 4: Debug Failing Tests

### Run with Trace

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright test --config=playwright-container.config.ts --trace on"
```

### View Test Report

```bash
# Generate and view report
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && pnpm exec playwright show-report"
```

### Run Specific Test with Debug Output

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  sh -c "cd /app/autoarr/ui && DEBUG=pw:api pnpm exec playwright test tests/settings.spec.ts --config=playwright-container.config.ts"
```

## Step 5: Review Results

### Success Output

```
Running 15 tests using 4 workers

  ✓ [chromium] › tests/home.spec.ts:12:5 › Home Page › should display dashboard with health scores (2.3s)
  ✓ [chromium] › tests/home.spec.ts:20:5 › Home Page › should show recent activity (1.8s)
  ✓ [chromium] › tests/settings.spec.ts:8:5 › Settings › should test SABnzbd connection (5.2s)
  ...

  15 passed (45.2s)
```

### Failure Output

```
  ✗ [chromium] › tests/settings.spec.ts:8:5 › Settings › should test SABnzbd connection (15.2s)

    Error: Timed out 10000ms waiting for expect(locator).toBeVisible()

    Call log:
      - waiting for getByText("Connection successful")

    Attachments:
      - screenshot: /app/autoarr/ui/test-results/settings-should-test-SABnzbd-connection-chromium/screenshot.png
      - trace: /app/autoarr/ui/test-results/settings-should-test-SABnzbd-connection-chromium/trace.zip
```

## Common Issues

### "Container not running"

```bash
# Start the container
DOCKER_HOST=unix:///var/run/docker.sock docker-compose -f docker/docker-compose.local-test.yml up -d

# Wait for it to be healthy
sleep 10
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local curl -s http://localhost:8088/health
```

### "Tests timeout waiting for element"

1. Check if UI changes were copied to container
2. Verify the backend is responding: `docker exec autoarr-local curl http://localhost:8088/api/v1/health`
3. Check browser console for JS errors in trace

### "ModuleNotFoundError: httpx"

```bash
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local pip install httpx --quiet
```

### "Connection refused to external service"

The container needs to reach external services (SABnzbd, etc.):

```bash
# Test from inside container
DOCKER_HOST=unix:///var/run/docker.sock docker exec autoarr-local \
  curl -s "http://192.168.0.80:8090/sabnzbd/api?mode=version"
```

## Test Categories

| Category   | Files                  | Purpose                          |
| ---------- | ---------------------- | -------------------------------- |
| Dashboard  | `home.spec.ts`         | Health scores, activity feed     |
| Chat       | `chat.spec.ts`         | Content requests, responses      |
| Settings   | `settings.spec.ts`     | Connection tests, save settings  |
| Audit      | `config-audit.spec.ts` | Audit results, recommendations   |
| Activity   | `activity.spec.ts`     | Activity feed, real-time updates |
| Onboarding | `onboarding.spec.ts`   | First-time setup flow            |

## CI Integration

E2E tests run automatically in GitHub Actions:

```yaml
# .github/workflows/e2e.yml
e2e-tests:
  runs-on: ubuntu-latest
  services:
    autoarr:
      image: feawservices/autoarr:latest
      ports:
        - 8088:8088
  steps:
    - uses: actions/checkout@v4
    - name: Install Playwright
      run: cd autoarr/ui && pnpm install && pnpm exec playwright install
    - name: Run E2E Tests
      run: cd autoarr/ui && pnpm exec playwright test
```
