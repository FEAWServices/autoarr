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

"""Tests for LLMProviderFactory with OpenRouter."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from autoarr.shared.llm.provider_factory import LLMProviderFactory


class TestLLMProviderFactory:
    """Tests for LLMProviderFactory with OpenRouter provider."""

    def setup_method(self):
        """Reset factory state before each test."""
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    def teardown_method(self):
        """Clean up environment variables after each test."""
        for key in [
            "LLM_PROVIDER",
            "OPENROUTER_API_KEY",
            "OPENROUTER_MODEL",
            "OPENROUTER_MAX_TOKENS",
            "OPENROUTER_TIMEOUT",
        ]:
            if key in os.environ:
                del os.environ[key]
        # Reset factory
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    @pytest.mark.asyncio
    async def test_create_provider_openrouter(self):
        """Test OpenRouter provider creation."""
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key"

        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        with patch.object(OpenRouterProvider, "is_available", new_callable=AsyncMock) as mock_avail:
            mock_avail.return_value = True

            provider = await LLMProviderFactory.create_provider(provider_name="openrouter")

            assert isinstance(provider, OpenRouterProvider)
            assert provider.api_key == "sk-or-test-key"

    @pytest.mark.asyncio
    async def test_openrouter_config_from_environment(self):
        """Test OpenRouter configuration from environment variables."""
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key-12345"
        os.environ["OPENROUTER_MODEL"] = "openai/gpt-4o"
        os.environ["OPENROUTER_MAX_TOKENS"] = "8192"
        os.environ["OPENROUTER_TIMEOUT"] = "120"

        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        with patch.object(OpenRouterProvider, "is_available", new_callable=AsyncMock) as mock_avail:
            mock_avail.return_value = True

            provider = await LLMProviderFactory.create_provider(provider_name="openrouter")

            assert provider.api_key == "sk-or-test-key-12345"
            assert provider.default_model == "openai/gpt-4o"
            assert provider.max_tokens == 8192
            assert provider.timeout == 120

    @pytest.mark.asyncio
    async def test_create_provider_default_is_openrouter(self):
        """Test that default provider is openrouter when no LLM_PROVIDER set."""
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key"

        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        with patch.object(OpenRouterProvider, "is_available", new_callable=AsyncMock) as mock_avail:
            mock_avail.return_value = True

            # Don't set LLM_PROVIDER - should default to openrouter
            provider = await LLMProviderFactory.create_provider()

            assert isinstance(provider, OpenRouterProvider)

    @pytest.mark.asyncio
    async def test_create_provider_no_key_raises(self):
        """Test error when no API key configured."""
        # Don't set any API key
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        with patch.object(OpenRouterProvider, "is_available", new_callable=AsyncMock) as mock_avail:
            mock_avail.return_value = False

            with pytest.raises(ValueError, match="No LLM providers available"):
                await LLMProviderFactory.create_provider()

    def test_list_providers_includes_openrouter(self):
        """Test that openrouter is in provider list."""
        providers = LLMProviderFactory.list_providers()

        assert "openrouter" in providers

    def test_claude_provider_not_registered(self):
        """Test that claude provider is no longer available."""
        providers = LLMProviderFactory.list_providers()

        assert "claude" not in providers


class TestLLMProviderFactoryConfiguration:
    """Tests for LLMProviderFactory configuration handling."""

    def setup_method(self):
        """Reset factory state before each test."""
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    def teardown_method(self):
        """Clean up environment after each test."""
        for key in [
            "LLM_PROVIDER",
            "OPENROUTER_API_KEY",
            "OPENROUTER_MODEL",
            "OPENROUTER_MAX_TOKENS",
            "OPENROUTER_TIMEOUT",
        ]:
            if key in os.environ:
                del os.environ[key]
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    @pytest.mark.asyncio
    async def test_openrouter_default_model(self):
        """Test OpenRouter default model when not specified."""
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key"
        # Don't set OPENROUTER_MODEL

        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        with patch.object(OpenRouterProvider, "is_available", new_callable=AsyncMock) as mock_avail:
            mock_avail.return_value = True

            provider = await LLMProviderFactory.create_provider(provider_name="openrouter")

            # Should use default Claude model via OpenRouter
            assert provider.default_model == "anthropic/claude-3.5-sonnet"


class TestLLMProviderRegistration:
    """Tests for LLMProviderFactory provider registration."""

    def setup_method(self):
        """Reset factory state before each test."""
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    def teardown_method(self):
        """Clean up registered providers."""
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    def test_list_registered_providers(self):
        """Test listing registered providers."""
        providers = LLMProviderFactory.list_providers()

        assert "openrouter" in providers
        assert len(providers) >= 1

    def test_register_custom_provider(self):
        """Test registering a custom provider."""
        from autoarr.shared.llm.base_provider import BaseLLMProvider

        class CustomProvider(BaseLLMProvider):
            provider_name = "custom"

            async def complete(self, *args, **kwargs):
                pass

            async def stream_complete(self, *args, **kwargs):
                pass

            async def is_available(self):
                return True

            async def health_check(self):
                return {}

        LLMProviderFactory.register_provider("custom", CustomProvider)

        providers = LLMProviderFactory.list_providers()
        assert "custom" in providers

    @pytest.mark.asyncio
    async def test_provider_info(self):
        """Test getting provider info."""
        os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key"

        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        with patch.object(
            OpenRouterProvider, "health_check", new_callable=AsyncMock
        ) as mock_health:
            mock_health.return_value = {
                "available": True,
                "provider": "openrouter",
                "models": ["anthropic/claude-3.5-sonnet"],
                "latency_ms": 100,
                "error": None,
            }

            info = await LLMProviderFactory.get_provider_info()

            assert "openrouter" in info
            assert info["openrouter"]["available"] is True
