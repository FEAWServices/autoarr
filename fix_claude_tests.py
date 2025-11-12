#!/usr/bin/env python3
"""Fix ClaudeProvider tests to use _client instead of patching client property."""

import re

# Read the test file
with open('autoarr/tests/unit/shared/llm/test_claude_provider.py', 'r') as f:
    content = f.read()

# Pattern to find: with patch.object(provider, "client", create=True) as mock_client:
# Replace with direct assignment: mock_client = MagicMock() ... provider._client = mock_client

# Replace all occurrences of the pattern
content = re.sub(
    r'with patch\.object\(provider, "client", create=True\) as mock_client:\s+mock_client\.messages = AsyncMock\(\)\s+mock_client\.messages\.create = AsyncMock\(return_value=mock_message\)',
    lambda m: (
        "# Create mock client and set it\n        "
        "mock_client = MagicMock()\n        "
        "mock_client.messages = AsyncMock()\n        "
        "mock_client.messages.create = AsyncMock(return_value=mock_message)\n        "
        "provider._client = mock_client"
    ),
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Also fix the streaming tests
content = re.sub(
    r'with patch\.object\(provider, "client", create=True\) as mock_client:',
    '# Create mock client and set it\n        mock_client = MagicMock()\n        provider._client = mock_client\n        if True:',
    content
)

# Write back
with open('autoarr/tests/unit/shared/llm/test_claude_provider.py', 'w') as f:
    f.write(content)

print("✅ Fixed ClaudeProvider tests to use _client")
