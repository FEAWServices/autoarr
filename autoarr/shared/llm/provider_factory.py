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

"""LLM Provider Factory for AutoArr."""

import logging
import os
from typing import Any, Dict, List, Optional, Type

from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances with fallback support.

    Supports multiple providers:
    - Ollama (default, free)
    - Claude (optional, free with API key)
    - Custom (premium only)
    """

    _providers: Dict[str, Type[BaseLLMProvider]] = {}
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize the factory with available providers."""
        if cls._initialized:
            return

        # Import providers lazily to avoid circular imports
        try:
            from .claude_provider import ClaudeProvider

            cls._providers["claude"] = ClaudeProvider
            logger.info("Registered ClaudeProvider")
        except ImportError as e:
            logger.debug(f"ClaudeProvider not available: {e}")

        try:
            from .ollama_provider import OllamaProvider

            cls._providers["ollama"] = OllamaProvider
            logger.info("Registered OllamaProvider")
        except ImportError as e:
            logger.debug(f"OllamaProvider not available: {e}")

        cls._initialized = True

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """
        Register a new provider (primarily for premium version or plugins).

        Args:
            name: Provider identifier (e.g., "custom", "openai")
            provider_class: Provider class implementing BaseLLMProvider
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    async def create_provider(
        cls,
        provider_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        fallback: bool = True,
    ) -> BaseLLMProvider:
        """
        Create a provider instance with automatic fallback logic.

        Args:
            provider_name: Specific provider to use (None = auto-select)
            config: Provider configuration (None = use environment)
            fallback: Whether to try fallback providers if first choice fails

        Returns:
            Configured and available LLMProvider instance

        Raises:
            ValueError: If no providers are available
        """
        cls.initialize()

        # Get provider preference from environment or parameter
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER", "ollama")

        # Determine fallback order
        fallback_order = cls._get_fallback_order(provider_name, fallback)

        # Try each provider in order
        for prov_name in fallback_order:
            if prov_name not in cls._providers:
                logger.warning(f"Provider '{prov_name}' not registered, skipping")
                continue

            try:
                logger.info(f"Attempting to initialize provider: {prov_name}")

                # Get provider-specific config
                prov_config = config or cls._get_provider_config(prov_name)

                # Instantiate provider
                provider = cls._providers[prov_name](prov_config)

                # Check if available
                if await provider.is_available():
                    logger.info(f"Successfully initialized provider: {prov_name}")
                    return provider
                else:
                    logger.warning(f"Provider '{prov_name}' unavailable")

            except Exception as e:
                logger.warning(f"Failed to initialize provider '{prov_name}': {e}")
                continue

        # No providers available
        raise ValueError(
            f"No LLM providers available. Tried: {fallback_order}. "
            f"Please configure at least one provider (Ollama or Claude)."
        )

    @classmethod
    def _get_fallback_order(cls, primary_provider: str, fallback: bool) -> List[str]:
        """
        Determine the order of providers to try.

        Args:
            primary_provider: User's preferred provider
            fallback: Whether to enable fallback

        Returns:
            Ordered list of provider names to try
        """
        if not fallback:
            return [primary_provider]

        # Get fallback order from environment or use default
        fallback_env = os.getenv("LLM_FALLBACK_ORDER")
        if fallback_env:
            return [p.strip() for p in fallback_env.split(",")]

        # Default fallback logic
        fallback_order = [primary_provider]

        # Add other providers as fallback
        if primary_provider != "ollama":
            fallback_order.append("ollama")
        if primary_provider != "claude" and os.getenv("CLAUDE_API_KEY"):
            fallback_order.append("claude")

        return fallback_order

    @classmethod
    def _get_provider_config(cls, provider_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider from environment.

        Args:
            provider_name: Provider identifier

        Returns:
            Configuration dictionary
        """
        if provider_name == "claude":
            return {
                "api_key": os.getenv("CLAUDE_API_KEY", ""),
                "default_model": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                "max_tokens": int(os.getenv("CLAUDE_MAX_TOKENS", "4096")),
                "timeout": int(os.getenv("CLAUDE_TIMEOUT", "60")),
            }

        elif provider_name == "ollama":
            return {
                "base_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
                "default_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
                "timeout": int(os.getenv("OLLAMA_TIMEOUT", "120")),
                "auto_download": os.getenv("OLLAMA_AUTO_DOWNLOAD", "true").lower() == "true",
            }

        return {}

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        Get list of registered provider names.

        Returns:
            List of provider identifiers
        """
        cls.initialize()
        return list(cls._providers.keys())

    @classmethod
    async def get_available_providers(cls) -> List[str]:
        """
        Get list of providers that are currently available.

        Returns:
            List of provider names that pass availability checks
        """
        cls.initialize()
        available = []

        for name, provider_class in cls._providers.items():
            try:
                config = cls._get_provider_config(name)
                provider = provider_class(config)
                if await provider.is_available():
                    available.append(name)
            except Exception:
                continue

        return available

    @classmethod
    async def get_provider_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get health check information for all providers.

        Returns:
            Dictionary mapping provider names to health check results
        """
        cls.initialize()
        info = {}

        for name, provider_class in cls._providers.items():
            try:
                config = cls._get_provider_config(name)
                provider = provider_class(config)
                info[name] = await provider.health_check()
            except Exception as e:
                info[name] = {
                    "status": "error",
                    "provider": name,
                    "error": str(e),
                }

        return info
