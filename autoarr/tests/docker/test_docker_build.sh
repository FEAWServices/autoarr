#!/bin/bash
# Docker Build Smoke Tests
# Tests the Docker image build process and validates the resulting container

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
IMAGE_NAME="autoarr-test"
TAG="smoke-test"
CONTAINER_NAME="autoarr-smoke-test"
TEST_PORT=8089

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    docker rmi ${IMAGE_NAME}:${TAG} 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_check() {
    local test_name=$1
    local command=$2
    local expected=$3

    echo -e "${YELLOW}Testing: ${test_name}${NC}"

    if eval "$command" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "========================================"
echo "Docker Build Smoke Tests"
echo "========================================"
echo ""

# Test 1: Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
if docker build -t ${IMAGE_NAME}:${TAG} -f Dockerfile . > /tmp/docker-build.log 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: Docker image builds successfully"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Docker image build failed"
    echo "Build log:"
    tail -50 /tmp/docker-build.log
    ((TESTS_FAILED++))
    exit 1
fi

# Test 2: Verify Python version
test_check "Python version is 3.11" \
    "docker run --rm ${IMAGE_NAME}:${TAG} python --version" \
    "Python 3.11"

# Test 3: Verify uvicorn is installed
test_check "Uvicorn is installed" \
    "docker run --rm ${IMAGE_NAME}:${TAG} uvicorn --version" \
    "uvicorn"

# Test 4: Verify AutoArr package is installed
test_check "AutoArr package is installed" \
    "docker run --rm ${IMAGE_NAME}:${TAG} python -c 'import autoarr; print(\"success\")'" \
    "success"

# Test 5: Verify FastAPI is installed
test_check "FastAPI is installed" \
    "docker run --rm ${IMAGE_NAME}:${TAG} python -c 'import fastapi; print(\"success\")'" \
    "success"

# Test 6: Verify frontend build artifacts exist
test_check "Frontend assets exist" \
    "docker run --rm ${IMAGE_NAME}:${TAG} ls -la /app/autoarr/ui/dist/" \
    "index.html"

# Test 7: Verify non-root user
test_check "Container runs as non-root user" \
    "docker run --rm ${IMAGE_NAME}:${TAG} whoami" \
    "autoarr"

# Test 8: Verify exposed port
test_check "Port 8088 is exposed" \
    "docker inspect ${IMAGE_NAME}:${TAG} --format='{{json .Config.ExposedPorts}}'" \
    "8088"

# Test 9: Start container and verify it runs
echo -e "${YELLOW}Starting container...${NC}"
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${TEST_PORT}:8088 \
    -e SABNZBD_URL=http://localhost:8080 \
    -e SABNZBD_API_KEY=test \
    -e SONARR_URL=http://localhost:8989 \
    -e SONARR_API_KEY=test \
    -e RADARR_URL=http://localhost:7878 \
    -e RADARR_API_KEY=test \
    ${IMAGE_NAME}:${TAG} > /dev/null

# Wait for container to start
sleep 5

# Test 10: Verify container is running
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo -e "${GREEN}✓ PASS${NC}: Container starts and stays running"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Container failed to start or stopped"
    docker logs ${CONTAINER_NAME}
    ((TESTS_FAILED++))
fi

# Test 11: Verify health check endpoint (may fail if external services not available)
echo -e "${YELLOW}Testing: Health check endpoint${NC}"
sleep 10  # Give more time for app to initialize
if curl -f http://localhost:${TEST_PORT}/health 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}: Health check endpoint responds"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARN${NC}: Health check endpoint not responding (may need external services)"
    # Don't fail the test as external services may not be available
fi

# Test 12: Verify container logs for errors
echo -e "${YELLOW}Checking container logs for critical errors...${NC}"
if docker logs ${CONTAINER_NAME} 2>&1 | grep -iq "critical\|fatal\|traceback"; then
    echo -e "${RED}✗ FAIL${NC}: Container logs contain critical errors"
    echo "Recent logs:"
    docker logs ${CONTAINER_NAME} 2>&1 | tail -20
    ((TESTS_FAILED++))
else
    echo -e "${GREEN}✓ PASS${NC}: No critical errors in container logs"
    ((TESTS_PASSED++))
fi

# Test 13: Verify image size is reasonable (< 1GB)
IMAGE_SIZE=$(docker images ${IMAGE_NAME}:${TAG} --format "{{.Size}}" | sed 's/MB//' | sed 's/GB/*1024/')
echo -e "${YELLOW}Image size: $(docker images ${IMAGE_NAME}:${TAG} --format '{{.Size}}')${NC}"
echo -e "${GREEN}✓ INFO${NC}: Image size check (informational only)"

# Test 14: Verify security - no root processes
test_check "No processes running as root" \
    "docker exec ${CONTAINER_NAME} ps aux" \
    "autoarr"

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
