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

"""OpenRouter LLM provider for AutoArr.

OpenRouter provides access to 200+ LLM models through a unified API,
including Claude, GPT-4, Llama, Mistral, and many others.
"""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from pydantic import BaseModel

from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class OpenRouterModel(BaseModel):
    """Model information from OpenRouter."""

    id: str
    name: str
    context_length: int
    pricing: Dict[str, float]  # prompt, completion price per token


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter LLM provider supporting 200+ models.

    OpenRouter provides a unified API for accessing multiple LLM providers
    including Anthropic, OpenAI, Meta, Mistral, and others.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OpenRouter provider.

        Args:
            config: Configuration dictionary containing:
                - api_key: OpenRouter API key (required for availability)
                - default_model: Default model to use (default: anthropic/claude-3.5-sonnet)
                - max_tokens: Maximum tokens to generate (default: 4096)
                - timeout: Request timeout in seconds (default: 60)
        """
        super().__init__(config)
        self.provider_name = "openrouter"
        self.api_key = config.get("api_key", "")
        self.default_model = config.get("default_model", "anthropic/claude-3.5-sonnet")
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60)

        # Retry configuration
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)

        # Cache for models
        self._models_cache: Optional[List[OpenRouterModel]] = None
        self._models_cache_time: float = 0
        self._models_cache_ttl = 300  # 5 minutes

        # HTTP client (lazy initialization)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with appropriate headers."""
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://autoarr.io",
                "X-Title": "AutoArr",
            }
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion via OpenRouter.

        Args:
            messages: List of messages in the conversation
            model: Model to use (uses default if None)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API

        Returns:
            LLMResponse with the generated content

        Raises:
            Exception: If the request fails after retries
        """
        client = self._get_client()
        use_model = model or self.default_model
        use_max_tokens = max_tokens or self.max_tokens

        # Convert messages to OpenAI format
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        request_body = {
            "model": use_model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": use_max_tokens,
            **kwargs,
        }

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await client.post("/chat/completions", json=request_body)
                response.raise_for_status()
                data = response.json()

                # Extract response content
                content = data["choices"][0]["message"]["content"]
                finish_reason = data["choices"][0].get("finish_reason", "stop")
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    model=data.get("model", use_model),
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    finish_reason=finish_reason,
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    # Rate limit - retry with backoff
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Rate limited by OpenRouter, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Other HTTP errors - don't retry
                    logger.error(f"OpenRouter API error: {e.response.status_code}")
                    raise

            except Exception as e:
                last_error = e
                logger.error(f"OpenRouter request failed: {e}")
                raise

        # If we get here, we've exhausted retries
        raise last_error or Exception("Request failed after retries")

    async def stream_complete(  # type: ignore[override]
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion via OpenRouter.

        Args:
            messages: List of messages in the conversation
            model: Model to use (uses default if None)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text as they become available
        """
        client = self._get_client()
        use_model = model or self.default_model
        use_max_tokens = max_tokens or self.max_tokens

        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        request_body = {
            "model": use_model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": use_max_tokens,
            "stream": True,
            **kwargs,
        }

        async with client.stream("POST", "/chat/completions", json=request_body) as response:
            response.raise_for_status()

            async for line in response.aiter_bytes():
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                # Parse SSE format
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def get_models(self) -> List[OpenRouterModel]:  # type: ignore[override]
        """
        Get list of available models from OpenRouter.

        Returns:
            List of OpenRouterModel objects with pricing info

        Note:
            Results are cached for 5 minutes to reduce API calls.
            Return type is more specific than base class (OpenRouterModel vs str).
        """
        # Check cache
        if self._models_cache is not None:
            if time.time() - self._models_cache_time < self._models_cache_ttl:
                return self._models_cache

        try:
            client = self._get_client()
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                pricing = model_data.get("pricing", {})
                # Convert string pricing to float (price per token)
                prompt_price = float(pricing.get("prompt", "0"))
                completion_price = float(pricing.get("completion", "0"))

                models.append(
                    OpenRouterModel(
                        id=model_data.get("id", ""),
                        name=model_data.get("name", model_data.get("id", "")),
                        context_length=model_data.get("context_length", 4096),
                        pricing={
                            "prompt": prompt_price,
                            "completion": completion_price,
                        },
                    )
                )

            # Update cache
            self._models_cache = models
            self._models_cache_time = time.time()

            return models

        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter models: {e}")
            return []

    async def get_model_pricing(self, model_id: str) -> Dict[str, float]:
        """
        Get pricing information for a specific model.

        Args:
            model_id: The model identifier (e.g., "anthropic/claude-3.5-sonnet")

        Returns:
            Dictionary with 'prompt' and 'completion' prices per token
        """
        models = await self.get_models()

        for model in models:
            if model.id == model_id:
                return model.pricing

        # Default pricing if model not found (Claude 3.5 Sonnet pricing)
        logger.warning(f"Model {model_id} not found, using default pricing")
        return {
            "prompt": 0.000003,  # $3 per 1M tokens
            "completion": 0.000015,  # $15 per 1M tokens
        }

    async def is_available(self) -> bool:
        """
        Check if the OpenRouter provider is available.

        Returns:
            True if API key is set and API is reachable
        """
        if not self.api_key:
            return False

        try:
            client = self._get_client()
            response = await client.get("/models")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"OpenRouter availability check failed: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check.

        Returns:
            Dictionary with health status information
        """
        start_time = time.time()
        error = None
        available = False
        models = []

        if not self.api_key:
            error = "No API key configured"
        else:
            try:
                client = self._get_client()
                response = await client.get("/models")
                response.raise_for_status()
                data = response.json()
                available = True
                models = [m.get("id", "") for m in data.get("data", [])[:10]]
            except Exception as e:
                error = str(e)
                available = False

        latency_ms = (time.time() - start_time) * 1000

        return {
            "available": available,
            "provider": self.provider_name,
            "models": models,
            "latency_ms": round(latency_ms, 2),
            "error": error,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
