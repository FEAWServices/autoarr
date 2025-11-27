#!/bin/bash

set -e  # Exit on first failure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         AutoArr Post-Deployment Test Suite                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Running all post-deployment tests..."
echo ""

# Track test results
PASSED=0
FAILED=0
TESTS=()

# Function to run a test
run_test() {
    local test_name=$1
    local test_script=$2

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if bash "$SCRIPT_DIR/$test_script"; then
        PASSED=$((PASSED + 1))
        TESTS+=("✅ $test_name")
    else
        FAILED=$((FAILED + 1))
        TESTS+=("❌ $test_name")
    fi

    echo ""
}

# Run all tests
run_test "Health Check" "test-health.sh"
run_test "UI Accessibility" "test-ui-accessible.sh"
run_test "Settings API" "test-settings-api.sh"

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

for test_result in "${TESTS[@]}"; do
    echo "$test_result"
done

echo ""
echo "Total: $((PASSED + FAILED)) tests"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          🎉 All Tests Passed! 🎉                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          ❌ Some Tests Failed                             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 1
fi
