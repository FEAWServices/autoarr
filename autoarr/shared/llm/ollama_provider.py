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

"""Ollama LLM Provider for AutoArr."""

import logging
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
import time

from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.

    Supports running models locally via Ollama:
    - Qwen 2.5 (recommended for free version)
    - Llama 3.1/3.2
    - Mistral
    - And many more

    Configuration:
        base_url: Ollama API URL (default: http://localhost:11434)
        default_model: Model to use (default: qwen2.5:7b)
        timeout: Request timeout in seconds (default: 120)
        auto_download: Auto-download models if not available (default: true)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "ollama"
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "qwen2.5:7b")
        self.timeout = config.get("timeout", 120)
        self.auto_download = config.get("auto_download", True)

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
        )

        logger.info(f"Initialized OllamaProvider: {self.base_url}, model: {self.default_model}")

    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a completion using Ollama."""
        model = model or self.default_model

        # Ensure model is available
        if self.auto_download:
            await self.ensure_model_available(model)

        # Convert messages to Ollama format
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        # Prepare request
        request_data = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens

        # Make request
        try:
            response = await self.client.post("/api/chat", json=request_data)
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data.get("message", {}).get("content", "")

            # Build usage stats
            usage = None
            if "prompt_eval_count" in data or "eval_count" in data:
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                }

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                usage=usage,
                finish_reason="stop" if data.get("done") else "length",
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Ollama request failed: {e.response.status_code}")

        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            raise

    async def stream_complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion using Ollama."""
        model = model or self.default_model

        # Ensure model is available
        if self.auto_download:
            await self.ensure_model_available(model)

        # Convert messages to Ollama format
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        # Prepare request
        request_data = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens

        # Stream request
        try:
            async with self.client.stream("POST", "/api/chat", json=request_data) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        import json

                        data = json.loads(line)

                        # Extract content chunk
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            if content:
                                yield content

                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming line: {line}")
                        continue

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama streaming error: {e.response.status_code}")
            raise Exception(f"Ollama streaming failed: {e.response.status_code}")

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = await self.client.get("/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Ollama."""
        start_time = time.time()
        health_data = {
            "available": False,
            "provider": self.provider_name,
            "models": [],
            "latency_ms": None,
            "error": None,
        }

        try:
            # Check if Ollama is running
            response = await self.client.get("/api/tags")
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]

                health_data["available"] = True
                health_data["models"] = models
                health_data["latency_ms"] = latency

                # Check if default model is available
                if self.default_model not in models:
                    health_data["warning"] = (
                        f"Default model '{self.default_model}' not found. "
                        f"Available models: {models}"
                    )
            else:
                health_data["error"] = f"HTTP {response.status_code}"

        except Exception as e:
            health_data["error"] = str(e)

        return health_data

    async def get_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to get Ollama models: {e}")
            return []

    async def ensure_model_available(self, model: str) -> bool:
        """
        Ensure a model is available, downloading if necessary.

        Args:
            model: Model name to check/download

        Returns:
            True if model is available, False otherwise
        """
        # Check if model is already available
        models = await self.get_models()
        if model in models:
            return True

        if not self.auto_download:
            logger.warning(f"Model '{model}' not available and auto_download is disabled")
            return False

        # Download the model
        logger.info(f"Downloading model '{model}' from Ollama...")

        try:
            request_data = {"name": model, "stream": False}

            response = await self.client.post(
                "/api/pull",
                json=request_data,
                timeout=httpx.Timeout(600),  # 10 minutes for download
            )

            if response.status_code == 200:
                logger.info(f"Successfully downloaded model '{model}'")
                return True
            else:
                logger.error(f"Failed to download model '{model}': {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error downloading model '{model}': {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
