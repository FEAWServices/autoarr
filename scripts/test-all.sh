#!/bin/bash
# Unified test runner for AutoArr (GPL) + AutoArr Premium
# Runs tests for both repos in sequence
set -e

echo "============================================"
echo "=== Testing AutoArr (GPL) ==="
echo "============================================"
cd /app
poetry run pytest "$@"

echo ""
echo "============================================"
echo "=== Testing AutoArr Premium ==="
echo "============================================"
if [ -d "/autoarr-premium" ]; then
    cd /autoarr-premium
    PYTHONPATH=/app:/autoarr-premium poetry run pytest "$@"
else
    echo "WARN: /autoarr-premium not found - skipping premium tests"
fi

echo ""
echo "============================================"
echo "=== All tests passed! ==="
echo "============================================"
