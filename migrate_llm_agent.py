#!/usr/bin/env python3
"""Script to migrate llm_agent.py to use LLMProviderFactory."""

import re

# Read original file
with open('autoarr/api/services/llm_agent.py', 'r') as f:
    content = f.read()

# Update docstring
content = content.replace(
    """using Claude API. It includes:
- Claude API client with retry logic""",
    """using pluggable LLM providers (Ollama, Claude, or custom). It includes:
- LLM provider abstraction with automatic selection"""
)

# Update imports - remove anthropic, add LLM providers
old_imports = """import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from anthropic import APIError, AsyncAnthropic, RateLimitError
from pydantic import BaseModel, Field

from autoarr.api.services.models import Priority"""

new_imports = """import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from autoarr.api.services.models import Priority
from autoarr.shared.llm import LLMProviderFactory, LLMMessage, BaseLLMProvider

logger = logging.getLogger(__name__)"""

content = content.replace(old_imports, new_imports)

# Find ClaudeClient class and mark as deprecated
claude_client_start = content.find('class ClaudeClient:')
claude_client_end = content.find('\n\nclass PromptTemplate:')

if claude_client_start != -1 and claude_client_end != -1:
    # Add deprecation notice before ClaudeClient
    deprecation_notice = '''

# DEPRECATED: ClaudeClient has been migrated to autoarr.shared.llm.ClaudeProvider
# This class is kept for backward compatibility only.
# New code should use LLMProviderFactory.create_provider() instead.

'''
    content = content[:claude_client_start] + deprecation_notice + content[claude_client_start:]

# Find and update LLMAgent class
llm_agent_init = '''    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ) -> None:
        """Initialize LLM agent."""
        self.client = ClaudeClient(  # noqa: F841
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
        )
        self.token_tracker = TokenUsageTracker()
        self.parser = StructuredOutputParser(
            required_fields=["explanation", "priority", "impact", "reasoning"]
        )'''

llm_agent_init_new = '''    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> None:
        """
        Initialize LLM agent.

        Args:
            provider: Optional pre-configured LLM provider
            api_key: Optional API key for Claude (backward compatibility)
            model: Optional model name
            max_tokens: Maximum tokens in responses
        """
        self.max_tokens = max_tokens
        self.model = model
        self._provider = provider
        self._api_key = api_key
        self._initialized = False

        self.token_tracker = TokenUsageTracker()
        self.parser = StructuredOutputParser(
            required_fields=["explanation", "priority", "impact", "reasoning"]
        )

    async def _ensure_provider(self) -> BaseLLMProvider:
        """Lazy initialization of LLM provider."""
        if self._initialized and self._provider:
            return self._provider

        if self._provider is None:
            if self._api_key:
                # Backward compatibility: if API key provided, use Claude
                logger.info("Using Claude provider (API key provided)")
                from autoarr.shared.llm.claude_provider import ClaudeProvider
                config = {
                    "api_key": self._api_key,
                    "default_model": self.model or "claude-3-5-sonnet-20241022",
                    "max_tokens": self.max_tokens,
                }
                self._provider = ClaudeProvider(config)
            else:
                # Use factory (Ollama by default, Claude if key in env)
                logger.info("Auto-selecting LLM provider via factory")
                self._provider = await LLMProviderFactory.create_provider(
                    provider_name=None,  # Auto-select
                    config={"default_model": self.model} if self.model else None,
                )

        self._initialized = True
        logger.info(f"LLMAgent using {self._provider.provider_name} provider")
        return self._provider'''

content = content.replace(llm_agent_init, llm_agent_init_new)

# Update analyze_configuration method
old_analyze = '''        # Send to Claude
        response = await self.client.send_message(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,
        )

        # Track token usage
        usage = response["usage"]
        self.token_tracker.record_usage(
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )

        # Parse structured output
        parsed = self.parser.parse(response["content"])'''

new_analyze = '''        # Get provider
        provider = await self._ensure_provider()

        # Create messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        # Send to LLM provider
        response = await provider.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=self.max_tokens,
        )

        # Track token usage
        if response.usage:
            self.token_tracker.record_usage(
                input_tokens=response.usage.get("prompt_tokens", 0),
                output_tokens=response.usage.get("completion_tokens", 0),
            )

        # Parse structured output
        parsed = self.parser.parse(response.content)'''

content = content.replace(old_analyze, new_analyze)

# Write updated file
with open('autoarr/api/services/llm_agent.py', 'w') as f:
    f.write(content)

print("✅ Successfully migrated llm_agent.py to use LLMProviderFactory")
print("   - Updated imports (removed anthropic, added LLMProviderFactory)")
print("   - Marked ClaudeClient as deprecated")
print("   - Updated LLMAgent to use provider system")
print("   - Maintained backward compatibility with api_key parameter")
