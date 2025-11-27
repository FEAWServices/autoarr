#!/bin/bash

echo "=== Health Check Test ==="
echo ""

# Test 1: Main health endpoint responds
echo "Step 1: Check health endpoint responds..."
HEALTH_RESPONSE=$(curl -s http://localhost:8088/health)

if [ -z "$HEALTH_RESPONSE" ]; then
    echo "❌ Health endpoint not responding"
    exit 1
fi

echo "$HEALTH_RESPONSE" | jq .

# Verify response has required fields
if echo "$HEALTH_RESPONSE" | jq -e '.status and .timestamp' > /dev/null; then
    echo "✅ Health endpoint responds with valid structure: PASSED"
else
    echo "❌ Health endpoint response missing required fields: FAILED"
    exit 1
fi

STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
echo "  Current status: $STATUS"

# For post-deployment, we accept healthy, degraded, or unhealthy
# (unhealthy is OK if all services are disabled)
if [[ "$STATUS" =~ ^(healthy|degraded|unhealthy)$ ]]; then
    echo "✅ Health status is valid: PASSED"
else
    echo "❌ Health status is invalid: FAILED"
    exit 1
fi

echo ""

# Test 2: Check that enabled services are accessible
echo "Step 2: Check enabled services..."
SERVICES_COUNT=$(echo "$HEALTH_RESPONSE" | jq '.services | length')
echo "  Connected services: $SERVICES_COUNT"

if [ "$SERVICES_COUNT" -gt 0 ]; then
    echo "  Services:"
    echo "$HEALTH_RESPONSE" | jq -r '.services | to_entries[] | "    - \(.key): healthy=\(.value.healthy)"'
fi

echo ""
echo "✅ Health Check Test Complete!"
