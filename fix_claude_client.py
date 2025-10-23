#!/usr/bin/env python3
"""Fix ClaudeClient to be a wrapper around ClaudeProvider."""

# Read the file
with open('autoarr/api/services/llm_agent.py', 'r') as f:
    content = f.read()

# Find ClaudeClient class (from "class ClaudeClient:" to the next "class" or end of ClaudeClient)
start_marker = '# DEPRECATED: ClaudeClient has been migrated'
class_start = content.find(start_marker)
class_end = content.find('\n\nclass PromptTemplate:')

if class_start == -1 or class_end == -1:
    print("❌ Could not find ClaudeClient class boundaries")
    exit(1)

# New ClaudeClient implementation as a wrapper
new_claude_client = '''# DEPRECATED: ClaudeClient has been migrated to autoarr.shared.llm.ClaudeProvider
# This class is kept for backward compatibility only.
# New code should use LLMProviderFactory.create_provider() instead.

class ClaudeClient:
    """
    DEPRECATED: Compatibility wrapper around ClaudeProvider.

    This class is maintained for backward compatibility but is deprecated.
    New code should use autoarr.shared.llm.ClaudeProvider directly.

    Args:
        api_key: Anthropic API key
        model: Claude model to use (default: claude-3-5-sonnet-20241022)
        max_tokens: Maximum tokens in response
        max_retries: Maximum number of retries on rate limit (ignored)
        retry_delay: Initial retry delay in seconds (ignored, provider handles retries)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize Claude client (wraps ClaudeProvider)."""
        logger.warning(
            "ClaudeClient is deprecated. Use autoarr.shared.llm.ClaudeProvider instead."
        )

        from autoarr.shared.llm.claude_provider import ClaudeProvider

        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create ClaudeProvider instance
        self._provider = ClaudeProvider({
            "api_key": api_key,
            "default_model": model,
            "max_tokens": max_tokens,
            "max_retries": max_retries,
            "retry_delay": retry_delay,
        })

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Send a message to Claude API (via ClaudeProvider).

        Args:
            system_prompt: System prompt (role definition)
            user_message: User message (query/request)
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Dict with 'content' (response text) and 'usage' (token counts)
        """
        # Convert to LLMMessage format
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        # Call provider
        response = await self._provider.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=self.max_tokens,
        )

        # Convert back to old format for compatibility
        return {
            "content": response.content,
            "usage": {
                "input_tokens": response.usage.get("prompt_tokens", 0) if response.usage else 0,
                "output_tokens": response.usage.get("completion_tokens", 0) if response.usage else 0,
            }
        }

    async def close(self) -> None:
        """Close the API client."""
        if hasattr(self._provider, '__aexit__'):
            await self._provider.__aexit__(None, None, None)
'''

# Replace ClaudeClient section
new_content = content[:class_start] + new_claude_client + '\n' + content[class_end:]

# Write back
with open('autoarr/api/services/llm_agent.py', 'w') as f:
    f.write(new_content)

print("✅ Successfully replaced ClaudeClient with ClaudeProvider wrapper")
print("   - ClaudeClient now wraps ClaudeProvider")
print("   - Maintains backward compatibility")
print("   - No anthropic imports needed")
