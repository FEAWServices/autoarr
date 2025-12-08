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

"""Base LLM provider abstract interface for AutoArr."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Standard message format for all LLM providers."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None  # For assistant messages with tool calls
    tool_call_id: Optional[str] = None  # For tool result messages
    name: Optional[str] = None  # Tool name for tool result messages


class LLMResponse(BaseModel):
    """Standard response format for all LLM providers."""

    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    All LLM providers (Claude, Ollama, Custom) must implement this interface
    to ensure consistent behavior across AutoArr free and premium versions.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.provider_name: str = "base"
        self.available_models: List[str] = []

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.

        Args:
            messages: List of messages in the conversation
            model: Model name to use (uses default if None)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific additional parameters

        Returns:
            LLMResponse with the generated content

        Raises:
            Exception: If the provider is unavailable or request fails
        """
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion for the given messages.

        Args:
            messages: List of messages in the conversation
            model: Model name to use (uses default if None)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific additional parameters

        Yields:
            Chunks of generated text as they become available

        Raises:
            Exception: If the provider is unavailable or request fails
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.

        Returns:
            True if the provider can be used, False otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on the provider.

        Returns:
            Dictionary with health status:
            {
                "available": bool,
                "provider": str,
                "models": List[str],
                "latency_ms": Optional[float],
                "error": Optional[str]
            }
        """
        pass

    async def get_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model identifiers
        """
        return self.available_models
