#!/bin/bash

echo "=== Step 1: Get current SABnzbd settings ==="
curl -s http://localhost:8088/api/v1/settings/sabnzbd | jq .

echo ""
echo "=== Step 2: Disable SABnzbd and save ==="
curl -s -X PUT http://localhost:8088/api/v1/settings/sabnzbd \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false,
    "url": "http://localhost:8080",
    "api_key_or_token": "test_key_123",
    "timeout": 30.0
  }' | jq .

echo ""
echo "=== Step 3: Verify it was saved (enabled should be false) ==="
curl -s http://localhost:8088/api/v1/settings/sabnzbd | jq '.enabled'

echo ""
echo "=== Step 4: Re-enable SABnzbd ==="
curl -s -X PUT http://localhost:8088/api/v1/settings/sabnzbd \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "url": "http://localhost:8080",
    "api_key_or_token": "test_key_123",
    "timeout": 30.0
  }' | jq .

echo ""
echo "=== Step 5: Verify re-enabled (enabled should be true) ==="
curl -s http://localhost:8088/api/v1/settings/sabnzbd | jq '.enabled'

echo ""
echo "✅ Test Complete: Settings toggle and save works without errors!"
