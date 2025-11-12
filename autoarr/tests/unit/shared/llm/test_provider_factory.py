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

"""Tests for LLMProviderFactory."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from autoarr.shared.llm.claude_provider import ClaudeProvider
from autoarr.shared.llm.ollama_provider import OllamaProvider
from autoarr.shared.llm.provider_factory import LLMProviderFactory


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestLLMProviderFactory:
    """Tests for LLMProviderFactory."""

    def teardown_method(self):
        """Clean up environment variables after each test."""
        for key in ["LLM_PROVIDER", "CLAUDE_API_KEY", "OLLAMA_URL"]:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_create_provider_default_ollama(self):
        """Test default provider creation (Ollama)."""
        with patch.object(OllamaProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider()

            assert isinstance(provider, OllamaProvider)
            assert provider.provider_name == "ollama"

    @pytest.mark.asyncio
    async def test_create_provider_explicit_ollama(self):
        """Test explicit Ollama provider creation."""
        with patch.object(OllamaProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(provider_name="ollama")

            assert isinstance(provider, OllamaProvider)

    @pytest.mark.asyncio
    async def test_create_provider_explicit_claude(self):
        """Test explicit Claude provider creation."""
        os.environ["CLAUDE_API_KEY"] = "test-key"

        with patch.object(ClaudeProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(provider_name="claude")

            assert isinstance(provider, ClaudeProvider)

    @pytest.mark.asyncio
    async def test_create_provider_from_environment(self):
        """Test provider creation from environment variable."""
        os.environ["LLM_PROVIDER"] = "claude"
        os.environ["CLAUDE_API_KEY"] = "test-key"

        with patch.object(ClaudeProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider()

            assert isinstance(provider, ClaudeProvider)

    @pytest.mark.asyncio
    async def test_create_provider_with_custom_config(self):
        """Test provider creation with custom configuration."""
        config = {
            "base_url": "http://custom:11434",
            "default_model": "llama3:8b",
        }

        with patch.object(OllamaProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(
                provider_name="ollama",
                config=config,
            )

            assert isinstance(provider, OllamaProvider)
            assert provider.base_url == "http://custom:11434"
            assert provider.default_model == "llama3:8b"

    @pytest.mark.asyncio
    async def test_create_provider_with_fallback(self):
        """Test provider creation with fallback when first choice unavailable."""
        os.environ["CLAUDE_API_KEY"] = "test-key"

        # Ollama unavailable, Claude available
        with (
            patch.object(OllamaProvider, "is_available", return_value=False),
            patch.object(ClaudeProvider, "is_available", return_value=True),
        ):

            provider = await LLMProviderFactory.create_provider(
                provider_name="ollama",  # Request Ollama
                fallback=True,  # But allow fallback
            )

            # Should fall back to Claude
            assert isinstance(provider, ClaudeProvider)

    @pytest.mark.asyncio
    async def test_create_provider_no_fallback(self):
        """Test provider creation without fallback."""
        # Ollama unavailable
        with patch.object(OllamaProvider, "is_available", return_value=False):

            with pytest.raises(RuntimeError, match="not available"):
                await LLMProviderFactory.create_provider(
                    provider_name="ollama",
                    fallback=False,  # No fallback
                )

    @pytest.mark.asyncio
    async def test_create_provider_all_unavailable(self):
        """Test provider creation when all providers unavailable."""
        # Both providers unavailable
        with (
            patch.object(OllamaProvider, "is_available", return_value=False),
            patch.object(ClaudeProvider, "is_available", return_value=False),
        ):

            with pytest.raises(RuntimeError, match="No LLM provider available"):
                await LLMProviderFactory.create_provider()

    @pytest.mark.asyncio
    async def test_get_available_providers(self):
        """Test getting list of available providers."""
        os.environ["CLAUDE_API_KEY"] = "test-key"

        # Ollama available, Claude available
        with (
            patch.object(OllamaProvider, "is_available", return_value=True),
            patch.object(ClaudeProvider, "is_available", return_value=True),
        ):

            providers = await LLMProviderFactory.get_available_providers()

            assert "ollama" in providers
            assert "claude" in providers
            assert len(providers) == 2

    @pytest.mark.asyncio
    async def test_get_available_providers_partial(self):
        """Test getting available providers when some unavailable."""
        os.environ["CLAUDE_API_KEY"] = "test-key"

        # Only Ollama available
        with (
            patch.object(OllamaProvider, "is_available", return_value=True),
            patch.object(ClaudeProvider, "is_available", return_value=False),
        ):

            providers = await LLMProviderFactory.get_available_providers()

            assert "ollama" in providers
            assert "claude" not in providers
            assert len(providers) == 1

    @pytest.mark.asyncio
    async def test_get_provider_info(self):
        """Test getting provider information."""
        os.environ["CLAUDE_API_KEY"] = "test-key"

        # Mock health checks
        ollama_health = {
            "status": "healthy",
            "provider": "ollama",
            "available_models": ["qwen2.5:7b"],
        }
        claude_health = {
            "status": "healthy",
            "provider": "claude",
            "model": "claude-3-5-sonnet-20241022",
        }

        with (
            patch.object(OllamaProvider, "is_available", return_value=True),
            patch.object(ClaudeProvider, "is_available", return_value=True),
            patch.object(OllamaProvider, "health_check", return_value=ollama_health),
            patch.object(ClaudeProvider, "health_check", return_value=claude_health),
        ):

            info = await LLMProviderFactory.get_provider_info()

            assert "ollama" in info
            assert "claude" in info
            assert info["ollama"]["status"] == "healthy"
            assert info["claude"]["status"] == "healthy"


class TestLLMProviderFactoryConfiguration:
    """Tests for LLMProviderFactory configuration handling."""

    def teardown_method(self):
        """Clean up environment after each test."""
        for key in ["LLM_PROVIDER", "CLAUDE_API_KEY", "OLLAMA_URL"]:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_ollama_config_from_environment(self):
        """Test Ollama configuration from environment."""
        os.environ["OLLAMA_URL"] = "http://custom:11434"
        os.environ["OLLAMA_MODEL"] = "llama3:8b"

        with patch.object(OllamaProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(provider_name="ollama")

            assert provider.base_url == "http://custom:11434"
            assert provider.default_model == "llama3:8b"

    @pytest.mark.asyncio
    async def test_claude_config_from_environment(self):
        """Test Claude configuration from environment."""
        os.environ["CLAUDE_API_KEY"] = "test-api-key"
        os.environ["CLAUDE_MODEL"] = "claude-3-opus-20240229"

        with patch.object(ClaudeProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(provider_name="claude")

            assert provider.api_key == "test-api-key"
            assert provider.default_model == "claude-3-opus-20240229"

    @pytest.mark.asyncio
    async def test_config_precedence_explicit_over_environment(self):
        """Test explicit config takes precedence over environment."""
        os.environ["OLLAMA_URL"] = "http://env:11434"

        config = {"base_url": "http://explicit:11434"}

        with patch.object(OllamaProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(
                provider_name="ollama",
                config=config,
            )

            # Explicit config should override environment
            assert provider.base_url == "http://explicit:11434"


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestLLMProviderFactoryEdgeCases:
    """Tests for LLMProviderFactory edge cases."""

    def teardown_method(self):
        """Clean up environment after each test."""
        for key in ["LLM_PROVIDER", "CLAUDE_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_invalid_provider_name(self):
        """Test creation with invalid provider name."""
        with pytest.raises(ValueError, match="Unknown provider"):
            await LLMProviderFactory.create_provider(provider_name="invalid")

    @pytest.mark.asyncio
    async def test_create_provider_caching(self):
        """Test that repeated calls can create new instances."""
        with patch.object(OllamaProvider, "is_available", return_value=True):
            provider1 = await LLMProviderFactory.create_provider()
            provider2 = await LLMProviderFactory.create_provider()

            # Should be different instances
            assert provider1 is not provider2
            assert isinstance(provider1, OllamaProvider)
            assert isinstance(provider2, OllamaProvider)

    @pytest.mark.asyncio
    async def test_fallback_order_respects_preference(self):
        """Test fallback order respects original preference."""
        os.environ["CLAUDE_API_KEY"] = "test-key"

        # Request Claude first (even though Ollama available)
        with (
            patch.object(OllamaProvider, "is_available", return_value=True),
            patch.object(ClaudeProvider, "is_available", return_value=True),
        ):

            provider = await LLMProviderFactory.create_provider(provider_name="claude")

            # Should get Claude since it was requested and available
            assert isinstance(provider, ClaudeProvider)


class TestLLMProviderRegistration:
    """Tests for LLMProviderFactory provider registration."""

    def teardown_method(self):
        """Clean up registered providers."""
        # Reset to default providers
        from autoarr.shared.llm.provider_factory import LLMProviderFactory

        LLMProviderFactory._providers = {
            "ollama": OllamaProvider,
            "claude": ClaudeProvider,
        }

    def test_list_registered_providers(self):
        """Test listing registered providers."""
        providers = LLMProviderFactory.list_providers()

        assert "ollama" in providers
        assert "claude" in providers
        assert len(providers) == 2

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

    def test_register_duplicate_provider_name(self):
        """Test registering a provider with duplicate name logs warning."""
        # Registering ollama again should log a warning but work
        LLMProviderFactory.register_provider("ollama", OllamaProvider)

        # Should still work
        providers = LLMProviderFactory.list_providers()
        assert "ollama" in providers
