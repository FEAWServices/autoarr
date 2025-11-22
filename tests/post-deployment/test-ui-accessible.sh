#!/bin/bash

echo "=== UI Accessibility Test ==="
echo ""

# Test 1: UI loads (returns HTML, not JSON)
echo "Step 1: Check UI returns HTML..."
UI_RESPONSE=$(curl -s http://localhost:8088/)

if echo "$UI_RESPONSE" | grep -iq "<!doctype html>"; then
    echo "✅ UI serves HTML: PASSED"
else
    echo "❌ UI serves HTML: FAILED (got JSON or error)"
    exit 1
fi

echo ""

# Test 2: Check for React app mounting element
echo "Step 2: Check for React root element..."
if echo "$UI_RESPONSE" | grep -q 'id="root"'; then
    echo "✅ React root element found: PASSED"
else
    echo "❌ React root element not found: FAILED"
    exit 1
fi

echo ""

# Test 3: Check assets are accessible
echo "Step 3: Check static assets load..."
ASSET_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/assets/)

if [ "$ASSET_STATUS" = "200" ] || [ "$ASSET_STATUS" = "403" ]; then
    echo "✅ Assets directory accessible: PASSED"
else
    echo "⚠️  Assets check returned: $ASSET_STATUS"
fi

echo ""
echo "✅ UI Accessibility Test Complete!"
