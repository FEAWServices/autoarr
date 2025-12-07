#!/bin/bash
# =============================================================================
# AutoArr Smoke Test
# =============================================================================
# Quick post-deployment test to verify the local-test container is responding.
# Works from devcontainer by connecting to the autoarr network.
#
# Usage:
#   bash scripts/smoke-test.sh           # Run smoke tests
#   bash scripts/smoke-test.sh --wait    # Wait for container to be ready first
# =============================================================================

set -e

# Container name and network
CONTAINER_NAME="${CONTAINER_NAME:-autoarr-local}"
NETWORK_NAME="${NETWORK_NAME:-autoarr_app_autoarr-net}"

# API URL - use container hostname (works within shared network)
API_URL="${API_URL:-http://${CONTAINER_NAME}:8088}"
MAX_WAIT="${MAX_WAIT:-120}"

WAIT_MODE=false
if [[ "$1" == "--wait" ]]; then
    WAIT_MODE=true
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              AutoArr Smoke Test                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Container: $CONTAINER_NAME"
echo "API URL:   $API_URL"
echo ""

# Ensure devcontainer is connected to the autoarr network
ensure_network() {
    local dev_container=$(hostname)
    if ! DOCKER_HOST=unix:///var/run/docker.sock docker network inspect "$NETWORK_NAME" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | grep -q "$dev_container"; then
        echo "Connecting devcontainer to $NETWORK_NAME..."
        DOCKER_HOST=unix:///var/run/docker.sock docker network connect "$NETWORK_NAME" "$dev_container" 2>/dev/null || true
    fi
}

# Function to check if API is ready
check_api() {
    curl -sf "${API_URL}/health" > /dev/null 2>&1
}

# Check container is running
check_container() {
    DOCKER_HOST=unix:///var/run/docker.sock docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Ensure network connectivity
ensure_network

# Check container is running
if ! check_container; then
    echo "❌ Container '$CONTAINER_NAME' is not running"
    echo "   Start it with: docker-compose -f docker/docker-compose.local-test.yml up -d"
    exit 1
fi

# Wait for services if requested
if $WAIT_MODE; then
    echo "Waiting for API to be ready (max ${MAX_WAIT}s)..."
    ELAPSED=0
    while ! check_api; do
        if [ $ELAPSED -ge $MAX_WAIT ]; then
            echo "❌ Timeout waiting for API after ${MAX_WAIT}s"
            exit 1
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        printf "."
    done
    echo ""
    echo "API ready after ${ELAPSED}s"
    echo ""
fi

PASSED=0
FAILED=0

# Test function
run_test() {
    local name="$1"
    local cmd="$2"

    printf "%-50s" "Testing: $name..."
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ PASS"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo "❌ FAIL"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# API Health Tests
run_test "API /health responds" \
    "curl -sf ${API_URL}/health"

run_test "API /health returns valid JSON" \
    "curl -sf ${API_URL}/health | grep -q '\"status\"'"

run_test "API /api/v1/health/ready responds" \
    "curl -sf ${API_URL}/api/v1/health/ready"

run_test "API /api/v1/settings responds" \
    "curl -sf ${API_URL}/api/v1/settings"

run_test "API /api/v1/onboarding/status responds" \
    "curl -sf ${API_URL}/api/v1/onboarding/status"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "UI Tests (via API proxy)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test UI via docker exec (Vite blocks external hosts)
run_test "UI Vite server responds" \
    "DOCKER_HOST=unix:///var/run/docker.sock docker exec $CONTAINER_NAME curl -sf http://localhost:5173"

run_test "UI returns HTML" \
    "DOCKER_HOST=unix:///var/run/docker.sock docker exec $CONTAINER_NAME curl -sf http://localhost:5173 | grep -q '<html'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          ✅ All Smoke Tests Passed!                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          ❌ Some Tests Failed                             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 1
fi
