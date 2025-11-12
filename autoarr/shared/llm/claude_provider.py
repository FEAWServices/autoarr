# Copyright (C) 2025 AutoArr Contributors
#
# This file is part of AutoArr.
#
# AutoArr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AutoArr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Claude LLM Provider for AutoArr."""

import asyncio
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from anthropic import APIError, AsyncAnthropic, RateLimitError

from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """
    Claude provider for high-quality LLM inference.

    Uses Anthropic's Claude API (Sonnet, Opus, Haiku models).
    Supports both free (with API key) and premium versions.

    Configuration:
        api_key: Anthropic API key (required)
        default_model: Model to use (default: claude-3-5-sonnet-20241022)
        max_tokens: Maximum tokens to generate (default: 4096)
        max_retries: Retry attempts on rate limit (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1.0)
        timeout: Request timeout in seconds (default: 60)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "claude"

        # Configuration
        self.api_key = config.get("api_key", "")
        self.default_model = config.get("default_model", "claude-3-5-sonnet-20241022")
        self.max_tokens = config.get("max_tokens", 4096)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.timeout = config.get("timeout", 60)

        # Available models
        self.available_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

        # Client (lazy initialization)
        self._client: Optional[AsyncAnthropic] = None

        logger.info(f"Initialized ClaudeProvider: model={self.default_model}")

    @property
    def client(self) -> AsyncAnthropic:
        """Get or create the Anthropic client."""
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key, timeout=self.timeout)
        return self._client

    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a completion using Claude."""
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens

        # Separate system messages from user/assistant messages
        system_messages = [m.content for m in messages if m.role == "system"]
        conversation = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ["user", "assistant"]
        ]

        # Combine system messages
        system_prompt = "\n\n".join(system_messages) if system_messages else None

        # Retry logic for rate limits
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count <= self.max_retries:
            try:
                # Make API request
                request_kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": conversation,
                }

                if system_prompt:
                    request_kwargs["system"] = system_prompt

                response = await self.client.messages.create(**request_kwargs)

                # Extract response
                content = response.content[0].text

                # Build usage stats
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }

                return LLMResponse(
                    content=content,
                    model=model,
                    provider=self.provider_name,
                    usage=usage,
                    finish_reason=response.stop_reason or "stop",
                )

            except RateLimitError as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error(f"Claude rate limit exceeded after {self.max_retries} retries")
                    raise Exception(f"Claude rate limit exceeded: {e}")

                # Exponential backoff
                logger.warning(
                    f"Claude rate limit hit, retrying in {current_delay}s "
                    f"(attempt {retry_count}/{self.max_retries})"
                )
                await asyncio.sleep(current_delay)
                current_delay *= 2

            except APIError as e:
                logger.error(f"Claude API error: {e}")
                raise Exception(f"Claude API error: {e}")

            except Exception as e:
                logger.error(f"Unexpected Claude error: {e}")
                raise

    async def stream_complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion using Claude."""
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens

        # Separate system messages from user/assistant messages
        system_messages = [m.content for m in messages if m.role == "system"]
        conversation = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ["user", "assistant"]
        ]

        # Combine system messages
        system_prompt = "\n\n".join(system_messages) if system_messages else None

        try:
            # Make streaming request
            request_kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": conversation,
            }

            if system_prompt:
                request_kwargs["system"] = system_prompt

            async with self.client.messages.stream(**request_kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

        except APIError as e:
            logger.error(f"Claude streaming error: {e}")
            raise Exception(f"Claude streaming error: {e}")

        except Exception as e:
            logger.error(f"Unexpected Claude streaming error: {e}")
            raise

    async def is_available(self) -> bool:
        """Check if Claude is available (API key is set)."""
        if not self.api_key:
            logger.debug("Claude API key not set")
            return False

        # Quick validation - try to list models
        try:
            # Just check if we can create a client (doesn't make actual API call)
            client = AsyncAnthropic(api_key=self.api_key)
            await client.close()
            return True
        except Exception as e:
            logger.debug(f"Claude not available: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Claude API."""
        start_time = time.time()
        health_data = {
            "available": False,
            "provider": self.provider_name,
            "models": self.available_models,
            "latency_ms": None,
            "error": None,
        }

        if not self.api_key:
            health_data["error"] = "API key not configured"
            return health_data

        try:
            # Make a minimal test request
            test_messages = [LLMMessage(role="user", content="Hello")]

            response = await self.complete(messages=test_messages, temperature=0, max_tokens=5)

            latency = (time.time() - start_time) * 1000

            health_data["available"] = True
            health_data["latency_ms"] = latency
            health_data["test_response"] = response.content[:50]

        except Exception as e:
            health_data["error"] = str(e)

        return health_data

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client is not None:
            await self._client.close()
