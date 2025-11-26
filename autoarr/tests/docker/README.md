# Docker Build Tests

Comprehensive test suite for validating the AutoArr Docker image build process, container behavior, and security.

## Overview

This directory contains three types of Docker tests:

1. **Shell Script Smoke Tests** (`test_docker_build.sh`) - Quick validation tests
2. **Container Structure Tests** (`test_container_structure.yaml`) - Google's container-structure-test framework
3. **Python Integration Tests** (`test_docker_integration.py`) - Comprehensive pytest-based tests

## Prerequisites

### Required

- Docker installed and running
- Build context at `/app` (repository root)

### Optional

- `container-structure-test` for structure validation
- `trivy` for security vulnerability scanning
- Python with pytest for integration tests

## Running Tests

### 1. Shell Script Smoke Tests (Fastest)

```bash
# From repository root
./autoarr/tests/docker/test_docker_build.sh
```

**What it tests:**

- Docker image builds successfully
- Python version is 3.11
- Required packages are installed (uvicorn, FastAPI, AutoArr)
- Frontend assets are built and present
- Container runs as non-root user (autoarr:1001)
- Port 8088 is exposed
- Container starts and stays running
- Health check endpoint responds
- No critical errors in logs
- Security: No root processes

**Duration:** ~2-3 minutes

### 2. Container Structure Tests

Install container-structure-test:

```bash
curl -LO https://storage.googleapis.com/container-structure-test/latest/container-structure-test-linux-amd64
chmod +x container-structure-test-linux-amd64
sudo mv container-structure-test-linux-amd64 /usr/local/bin/container-structure-test
```

Run tests:

```bash
# Build image first
docker build -t autoarr:test -f Dockerfile .

# Run structure tests
container-structure-test test \
    --image autoarr:test \
    --config autoarr/tests/docker/test_container_structure.yaml
```

**What it tests:**

- File existence (app code, frontend assets, data directory)
- Python and package imports
- User permissions and ownership
- Exposed ports and metadata
- Development dependencies are NOT installed

**Duration:** ~30 seconds

### 3. Python Integration Tests (Most Comprehensive)

```bash
# From repository root
pytest autoarr/tests/docker/test_docker_integration.py -v
```

**What it tests:**

All smoke tests PLUS:

- Multiple dependency imports (fastapi, uvicorn, sqlalchemy, mcp, anthropic)
- Dev dependencies are properly excluded
- Container persistence (stays running)
- Read-only filesystem compatibility
- Security: Non-root user enforcement
- Optional: Trivy vulnerability scanning (if installed)

**Duration:** ~3-4 minutes

## Test Output

### Success Example

```
========================================
Docker Build Smoke Tests
========================================

Building Docker image...
✓ PASS: Docker image builds successfully
✓ PASS: Python version is 3.11
✓ PASS: Uvicorn is installed
✓ PASS: AutoArr package is installed
✓ PASS: FastAPI is installed
✓ PASS: Frontend assets exist
✓ PASS: Container runs as non-root user
✓ PASS: Port 8088 is exposed
✓ PASS: Container starts and stays running
✓ PASS: Health check endpoint responds
✓ PASS: No critical errors in container logs

========================================
Test Summary
========================================
Passed: 12
Failed: 0

All tests passed!
```

## CI/CD Integration

### GitHub Actions

Add to your workflow:

```yaml
- name: Run Docker Build Tests
  run: |
    ./autoarr/tests/docker/test_docker_build.sh

- name: Run Docker Integration Tests
  run: |
    pytest autoarr/tests/docker/test_docker_integration.py -v
```

## Troubleshooting

### Build Fails: "No such file or directory: README.md"

**Solution:** Ensure `.dockerignore` includes `!README.md` exception:

```
# In .dockerignore
*.md
!README.md
```

### Container Stops Immediately

**Symptoms:**

```
✗ FAIL: Container failed to start or stopped
```

**Debug:**

```bash
docker logs autoarr-smoke-test
```

**Common causes:**

- Missing required environment variables
- Python import errors
- Port already in use

### Health Check Fails

**Note:** This is expected if SABnzbd, Sonarr, and Radarr services are not available. The health check may return 503 but the container is still functional.

**Verify manually:**

```bash
curl http://localhost:8089/health
# Expected: 200 OK or 503 Service Unavailable
```

### Python Version Mismatch

**Expected:** Python 3.11

**If wrong version:**

1. Check `Dockerfile` line 25: `FROM python:3.11-slim`
2. Rebuild image: `docker build --no-cache -t autoarr:test .`

## Security Tests

### Vulnerability Scanning with Trivy

Install Trivy:

```bash
# Ubuntu/Debian
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Or use Docker
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image autoarr:test
```

Run scan:

```bash
trivy image --severity HIGH,CRITICAL autoarr:test
```

## Test Coverage

| Test Category        | Shell Script | Structure Test | Pytest |
| -------------------- | ------------ | -------------- | ------ |
| Build Success        | ✓            | ✓              | ✓      |
| Python Version       | ✓            | ✓              | ✓      |
| Package Installation | ✓            | ✓              | ✓      |
| Frontend Assets      | ✓            | ✓              | ✓      |
| Non-Root User        | ✓            | ✓              | ✓      |
| Port Exposure        | ✓            | ✓              | ✓      |
| Container Startup    | ✓            | ✗              | ✓      |
| Health Check         | ✓            | ✗              | ✓      |
| Log Analysis         | ✓            | ✗              | ✓      |
| Dev Dependencies     | ✗            | ✓              | ✓      |
| Read-Only Filesystem | ✗            | ✗              | ✓      |
| Vulnerability Scan   | ✗            | ✗              | ✓\*    |

\* Requires Trivy installation

## Best Practices

1. **Run tests before every release** to catch build issues early
2. **Run in CI/CD pipeline** to prevent broken builds from being deployed
3. **Update tests** when adding new dependencies or changing container configuration
4. **Monitor test duration** - if tests take >5 minutes, optimize or parallelize
5. **Fix vulnerabilities** found by Trivy before deploying to production

## Related Documentation

- [Dockerfile](/app/Dockerfile)
- [Docker Compose Configuration](/app/docker/)
- [CI/CD Workflows](/app/.github/workflows/docker-deploy.yml)
- [AutoArr Architecture](/app/docs/ARCHITECTURE.md)

## Contributing

When making changes to the Dockerfile:

1. Run all three test suites locally
2. Update tests if adding new dependencies or changing container structure
3. Document any new test requirements in this README
4. Ensure all tests pass before submitting PR

## Known Issues

- Health check test may warn if external services (SABnzbd, Sonarr, Radarr) are not available
- Trivy may report vulnerabilities in base Python image dependencies (not always fixable)

## Support

If tests fail unexpectedly:

1. Check Docker daemon is running: `docker ps`
2. Verify no port conflicts: `lsof -i :8089`
3. Check build logs: `docker build -t autoarr:test . 2>&1 | tee build.log`
4. Review container logs: `docker logs autoarr-smoke-test`
5. Open an issue with test output and logs
