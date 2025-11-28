#!/bin/bash
# =============================================================================
# Run Playwright E2E Tests Inside Docker Container
# =============================================================================
# This script runs Playwright tests inside the autoarr-local container where
# both the app and browser have direct localhost access.
#
# Usage:
#   ./scripts/run-e2e-tests.sh                    # Run all tests
#   ./scripts/run-e2e-tests.sh home               # Run tests matching "home"
#   ./scripts/run-e2e-tests.sh tests/home.spec.ts # Run specific file
# =============================================================================

set -e

CONTAINER_NAME="autoarr-local"
export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Error: Container '${CONTAINER_NAME}' is not running."
    echo "Start it with: docker-compose -f docker/docker-compose.local-test.yml up -d"
    exit 1
fi

# Build test filter argument
TEST_FILTER=""
if [ -n "$1" ]; then
    TEST_FILTER="$1"
fi

echo "=== Installing Playwright browser inside container ==="
docker exec "${CONTAINER_NAME}" sh -c "cd /app/autoarr/ui && pnpm exec playwright install chromium" 2>&1

echo ""
echo "=== Running Playwright tests inside container ==="
echo "Container: ${CONTAINER_NAME}"
echo "Test filter: ${TEST_FILTER:-all tests}"
echo ""

# Run tests inside container
docker exec "${CONTAINER_NAME}" sh -c "cd /app/autoarr/ui && pnpm exec playwright test ${TEST_FILTER} --config=playwright-container.config.ts" 2>&1

echo ""
echo "=== Tests complete ==="
