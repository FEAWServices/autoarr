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
from unittest.mock import patch

import pytest

from autoarr.shared.llm.claude_provider import ClaudeProvider
from autoarr.shared.llm.provider_factory import LLMProviderFactory


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestLLMProviderFactory:
    """Tests for LLMProviderFactory."""

    def teardown_method(self):
        """Clean up environment variables after each test."""
        for key in ["LLM_PROVIDER", "CLAUDE_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

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


class TestLLMProviderFactoryConfiguration:
    """Tests for LLMProviderFactory configuration handling."""

    def teardown_method(self):
        """Clean up environment after each test."""
        for key in ["LLM_PROVIDER", "CLAUDE_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.asyncio
    async def test_claude_config_from_environment(self):
        """Test Claude configuration from environment."""
        os.environ["CLAUDE_API_KEY"] = "test-api-key"
        os.environ["CLAUDE_MODEL"] = "claude-3-opus-20240229"

        with patch.object(ClaudeProvider, "is_available", return_value=True):
            provider = await LLMProviderFactory.create_provider(provider_name="claude")

            assert provider.api_key == "test-api-key"
            assert provider.default_model == "claude-3-opus-20240229"


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


class TestLLMProviderRegistration:
    """Tests for LLMProviderFactory provider registration."""

    def teardown_method(self):
        """Clean up registered providers."""
        # Reset to default providers
        LLMProviderFactory._providers = {}
        LLMProviderFactory._initialized = False

    def test_list_registered_providers(self):
        """Test listing registered providers."""
        providers = LLMProviderFactory.list_providers()

        assert "claude" in providers
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

    def test_register_duplicate_provider_name(self):
        """Test registering a provider with duplicate name logs warning."""
        # Registering claude again should log a warning but work
        LLMProviderFactory.register_provider("claude", ClaudeProvider)

        # Should still work
        providers = LLMProviderFactory.list_providers()
        assert "claude" in providers
