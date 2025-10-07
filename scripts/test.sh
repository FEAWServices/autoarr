#!/bin/bash
# Test harness that runs the same checks as CI pipeline
# This ensures local testing matches CI exactly (DRY principle)

set -e  # Exit on any error

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored status messages
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Track overall success
FAILED=0

# Function to run a check and track failures
run_check() {
    local name="$1"
    shift
    print_status "Running $name..."

    if "$@"; then
        print_success "$name passed"
    else
        print_error "$name failed"
        FAILED=1
        return 1
    fi
}

echo ""
print_status "Starting AutoArr Test Harness"
echo ""

# Run Black (code formatting check)
run_check "Black (code formatting)" poetry run black --check . || true

# Run Flake8 (linting)
run_check "Flake8 (linting)" poetry run flake8 api/ mcp-servers/mcp_servers/ shared/ tests/ --max-line-length=100 --extend-ignore=E203 || true

# Run MyPy (type checking) - non-blocking like CI
print_status "Running MyPy (type checking)..."
if poetry run mypy api/ mcp-servers/mcp_servers/ shared/ --config-file=pyproject.toml; then
    print_success "MyPy passed"
else
    print_warning "MyPy found issues (non-blocking)"
fi

# Run pytest (unit tests with coverage)
run_check "Pytest (unit tests)" poetry run pytest tests/ -v --cov=api --cov=mcp_servers --cov=shared --cov-report=xml --cov-report=term-missing || true

echo ""
if [ $FAILED -eq 0 ]; then
    print_success "All tests passed! ✨"
    exit 0
else
    print_error "Some tests failed. Please fix the issues above."
    exit 1
fi
