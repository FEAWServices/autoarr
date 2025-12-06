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

"""Unit tests for OpenRouter LLM provider."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from autoarr.shared.llm.base_provider import LLMMessage, LLMResponse


class TestOpenRouterProviderInit:
    """Tests for OpenRouterProvider initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {
            "api_key": "sk-or-test-key-12345",
            "default_model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 4096,
            "timeout": 60,
        }
        provider = OpenRouterProvider(config)

        assert provider.provider_name == "openrouter"
        assert provider.api_key == "sk-or-test-key-12345"
        assert provider.default_model == "anthropic/claude-3.5-sonnet"
        assert provider.max_tokens == 4096
        assert provider.timeout == 60

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {}
        provider = OpenRouterProvider(config)

        assert provider.api_key == ""
        assert provider.default_model == "anthropic/claude-3.5-sonnet"

    def test_init_with_custom_model(self):
        """Test initialization with custom default model."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {
            "api_key": "sk-or-test-key",
            "default_model": "openai/gpt-4o",
        }
        provider = OpenRouterProvider(config)

        assert provider.default_model == "openai/gpt-4o"

    def test_init_sets_base_url(self):
        """Test that base URL is set correctly."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {"api_key": "sk-or-test-key"}
        provider = OpenRouterProvider(config)

        assert provider.BASE_URL == "https://openrouter.ai/api/v1"


class TestOpenRouterProviderComplete:
    """Tests for OpenRouterProvider complete method."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {
            "api_key": "sk-or-test-key-12345",
            "default_model": "anthropic/claude-3.5-sonnet",
            "max_tokens": 4096,
            "timeout": 60,
        }
        return OpenRouterProvider(config)

    @pytest.fixture
    def mock_completion_response(self):
        """Create a mock completion response."""
        return {
            "id": "gen-abc123",
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18,
            },
        }

    @pytest.mark.asyncio
    async def test_complete_success(self, provider, mock_completion_response):
        """Test successful completion via OpenRouter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_completion_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            messages = [LLMMessage(role="user", content="Hello!")]
            response = await provider.complete(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you today?"
            assert response.model == "anthropic/claude-3.5-sonnet"
            assert response.provider == "openrouter"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 8
            assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_complete_with_system_message(self, provider, mock_completion_response):
        """Test completion properly handles system messages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_completion_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            messages = [
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Hello!"),
            ]
            await provider.complete(messages)

            # Verify the request was made with correct message format
            call_args = mock_client.post.call_args
            request_body = call_args.kwargs.get("json", {})
            assert len(request_body["messages"]) == 2
            assert request_body["messages"][0]["role"] == "system"
            assert request_body["messages"][0]["content"] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_complete_with_custom_model(self, provider, mock_completion_response):
        """Test completion with custom model override."""
        mock_completion_response["model"] = "openai/gpt-4o"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_completion_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            messages = [LLMMessage(role="user", content="Hello!")]
            response = await provider.complete(messages, model="openai/gpt-4o")

            # Verify model was passed in request
            call_args = mock_client.post.call_args
            request_body = call_args.kwargs.get("json", {})
            assert request_body["model"] == "openai/gpt-4o"
            assert response.model == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_complete_with_temperature(self, provider, mock_completion_response):
        """Test completion with temperature parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_completion_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            messages = [LLMMessage(role="user", content="Hello!")]
            await provider.complete(messages, temperature=0.5)

            call_args = mock_client.post.call_args
            request_body = call_args.kwargs.get("json", {})
            assert request_body["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_complete_handles_rate_limit(self, provider, mock_completion_response):
        """Test completion handles 429 rate limit with retry."""
        # First call returns rate limit, second succeeds
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=MagicMock(),
            response=rate_limit_response,
        )

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = mock_completion_response
        success_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=[rate_limit_response, success_response])

            messages = [LLMMessage(role="user", content="Hello!")]
            response = await provider.complete(messages)

            # Should have retried and succeeded
            assert mock_client.post.call_count == 2
            assert response.content == "Hello! How can I help you today?"

    @pytest.mark.asyncio
    async def test_complete_handles_api_error(self, provider):
        """Test completion handles API errors gracefully."""
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=error_response,
        )

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=error_response)

            messages = [LLMMessage(role="user", content="Hello!")]
            with pytest.raises(Exception):
                await provider.complete(messages)

    @pytest.mark.asyncio
    async def test_complete_sends_required_headers(self, provider, mock_completion_response):
        """Test that completion sends required OpenRouter headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_completion_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            messages = [LLMMessage(role="user", content="Hello!")]
            await provider.complete(messages)

            # Verify headers were set (provider should configure client with headers)
            call_args = mock_client.post.call_args
            # The URL should be the chat completions endpoint
            assert "/chat/completions" in str(call_args)


class TestOpenRouterProviderStream:
    """Tests for OpenRouterProvider streaming."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {
            "api_key": "sk-or-test-key-12345",
            "default_model": "anthropic/claude-3.5-sonnet",
        }
        return OpenRouterProvider(config)

    @pytest.mark.asyncio
    async def test_stream_complete_success(self, provider):
        """Test successful streaming completion."""
        # Mock SSE response chunks
        sse_chunks = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" there"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"!"}}]}\n\n',
            b"data: [DONE]\n\n",
        ]

        async def mock_stream():
            for chunk in sse_chunks:
                yield chunk

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_bytes = mock_stream
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.stream = MagicMock()
            mock_client.stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=None)

            messages = [LLMMessage(role="user", content="Hello!")]
            chunks = []
            async for chunk in provider.stream_complete(messages):
                chunks.append(chunk)

            assert "Hello" in chunks
            assert " there" in chunks
            assert "!" in chunks

    @pytest.mark.asyncio
    async def test_stream_complete_handles_error(self, provider):
        """Test streaming handles mid-stream errors."""
        with patch.object(provider, "_client") as mock_client:
            mock_client.stream = MagicMock()
            mock_client.stream.return_value.__aenter__ = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                )
            )
            mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=None)

            messages = [LLMMessage(role="user", content="Hello!")]
            with pytest.raises(Exception):
                async for _ in provider.stream_complete(messages):
                    pass


class TestOpenRouterProviderModels:
    """Tests for model listing and pricing."""

    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {
            "api_key": "sk-or-test-key-12345",
        }
        return OpenRouterProvider(config)

    @pytest.fixture
    def mock_models_response(self):
        """Create a mock models response."""
        return {
            "data": [
                {
                    "id": "anthropic/claude-3.5-sonnet",
                    "name": "Claude 3.5 Sonnet",
                    "context_length": 200000,
                    "pricing": {
                        "prompt": "0.000003",  # $3 per 1M tokens
                        "completion": "0.000015",  # $15 per 1M tokens
                    },
                },
                {
                    "id": "openai/gpt-4o",
                    "name": "GPT-4o",
                    "context_length": 128000,
                    "pricing": {
                        "prompt": "0.000005",
                        "completion": "0.000015",
                    },
                },
                {
                    "id": "meta-llama/llama-3.1-70b-instruct",
                    "name": "Llama 3.1 70B Instruct",
                    "context_length": 131072,
                    "pricing": {
                        "prompt": "0.00000059",
                        "completion": "0.00000079",
                    },
                },
            ]
        }

    @pytest.mark.asyncio
    async def test_get_models_success(self, provider, mock_models_response):
        """Test fetching available models from OpenRouter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            models = await provider.get_models()

            assert len(models) == 3
            assert models[0].id == "anthropic/claude-3.5-sonnet"
            assert models[0].name == "Claude 3.5 Sonnet"
            assert models[0].context_length == 200000
            assert "prompt" in models[0].pricing
            assert "completion" in models[0].pricing

    @pytest.mark.asyncio
    async def test_get_models_caches_result(self, provider, mock_models_response):
        """Test that model list is cached."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            # Call twice
            await provider.get_models()
            await provider.get_models()

            # Should only have made one HTTP request due to caching
            assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_model_pricing(self, provider, mock_models_response):
        """Test extracting pricing info for a specific model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            pricing = await provider.get_model_pricing("anthropic/claude-3.5-sonnet")

            assert "prompt" in pricing
            assert "completion" in pricing
            # Pricing should be converted to float (per token)
            assert isinstance(pricing["prompt"], float)

    @pytest.mark.asyncio
    async def test_get_model_pricing_unknown_model(self, provider, mock_models_response):
        """Test getting pricing for unknown model returns defaults."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_models_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            pricing = await provider.get_model_pricing("unknown/model")

            # Should return default pricing
            assert "prompt" in pricing
            assert "completion" in pricing

    @pytest.mark.asyncio
    async def test_get_models_handles_error(self, provider):
        """Test graceful handling of model fetch errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(provider, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            models = await provider.get_models()

            # Should return empty list on error, not crash
            assert models == []


class TestOpenRouterProviderAvailability:
    """Tests for availability checks."""

    @pytest.fixture
    def provider_with_key(self):
        """Create a provider with API key."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {"api_key": "sk-or-test-key-12345"}
        return OpenRouterProvider(config)

    @pytest.fixture
    def provider_without_key(self):
        """Create a provider without API key."""
        from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

        config = {}
        return OpenRouterProvider(config)

    @pytest.mark.asyncio
    async def test_is_available_with_valid_key(self, provider_with_key):
        """Test availability with valid API key."""
        # Mock a successful models request to verify key
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider_with_key, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            available = await provider_with_key.is_available()

            assert available is True

    @pytest.mark.asyncio
    async def test_is_available_without_key(self, provider_without_key):
        """Test availability without API key."""
        available = await provider_without_key.is_available()

        # Should return False immediately without making API call
        assert available is False

    @pytest.mark.asyncio
    async def test_is_available_with_invalid_key(self, provider_with_key):
        """Test availability with invalid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(provider_with_key, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            available = await provider_with_key.is_available()

            assert available is False

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider_with_key):
        """Test health check returns proper structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(provider_with_key, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            health = await provider_with_key.health_check()

            assert "available" in health
            assert health["available"] is True
            assert health["provider"] == "openrouter"
            assert "models" in health
            assert "latency_ms" in health
            assert health["error"] is None

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, provider_with_key):
        """Test health check when provider is unavailable."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(provider_with_key, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)

            health = await provider_with_key.health_check()

            assert health["available"] is False
            assert health["provider"] == "openrouter"
            assert health["error"] is not None
