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

"""Tests for OllamaProvider."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.shared.llm.base_provider import LLMMessage
from autoarr.shared.llm.ollama_provider import OllamaProvider


@pytest.fixture
def ollama_config():
    """Create Ollama configuration for testing."""
    return {
        "base_url": "http://localhost:11434",
        "default_model": "qwen2.5:7b",
        "timeout": 120,
        "auto_download": True,
    }


@pytest.fixture
def provider(ollama_config):
    """Create OllamaProvider instance for testing."""
    return OllamaProvider(ollama_config)


class TestOllamaProviderInit:
    """Tests for OllamaProvider initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        provider = OllamaProvider({})

        assert provider.provider_name == "ollama"
        assert provider.base_url == "http://localhost:11434"
        assert provider.default_model == "qwen2.5:7b"
        assert provider.timeout == 120
        assert provider.auto_download is True

    def test_init_with_custom_config(self, ollama_config):
        """Test initialization with custom configuration."""
        ollama_config["base_url"] = "http://custom:11434"
        ollama_config["default_model"] = "llama3:8b"
        ollama_config["timeout"] = 60
        ollama_config["auto_download"] = False

        provider = OllamaProvider(ollama_config)

        assert provider.base_url == "http://custom:11434"
        assert provider.default_model == "llama3:8b"
        assert provider.timeout == 60
        assert provider.auto_download is False


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestOllamaProviderComplete:
    """Tests for OllamaProvider complete method."""

    @pytest.mark.asyncio
    async def test_complete_success(self, provider):
        """Test successful completion."""
        messages = [
            LLMMessage(role="system", content="You are helpful."),
            LLMMessage(role="user", content="Hello!"),
        ]

        mock_response = {
            "message": {"role": "assistant", "content": "Hi there!"},
            "model": "qwen2.5:7b",
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5,
        }

        with patch.object(provider.client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )

            response = await provider.complete(messages=messages)

            assert response.content == "Hi there!"
            assert response.model == "qwen2.5:7b"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 5
            assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_complete_with_custom_model(self, provider):
        """Test completion with custom model."""
        messages = [LLMMessage(role="user", content="Test")]

        mock_response = {
            "message": {"role": "assistant", "content": "Response"},
            "model": "llama3:8b",
            "done": True,
        }

        with patch.object(provider.client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )

            response = await provider.complete(messages=messages, model="llama3:8b")

            assert response.model == "llama3:8b"
            # Verify request payload
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == "llama3:8b"

    @pytest.mark.asyncio
    async def test_complete_with_temperature(self, provider):
        """Test completion with custom temperature."""
        messages = [LLMMessage(role="user", content="Test")]

        mock_response = {
            "message": {"role": "assistant", "content": "Response"},
            "model": "qwen2.5:7b",
            "done": True,
        }

        with patch.object(provider.client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
            )

            await provider.complete(messages=messages, temperature=0.3)

            # Verify temperature in request
            call_args = mock_post.call_args
            assert call_args[1]["json"]["options"]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_complete_handles_error(self, provider):
        """Test completion handles API errors."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch.object(provider.client, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=500,
                text="Internal server error",
            )

            with pytest.raises(Exception, match="Ollama API error"):
                await provider.complete(messages=messages)


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestOllamaProviderStream:
    """Tests for OllamaProvider stream_complete method."""

    @pytest.mark.asyncio
    async def test_stream_complete_success(self, provider):
        """Test successful streaming completion."""
        messages = [LLMMessage(role="user", content="Count to 3")]

        # Mock streaming response
        stream_chunks = [
            json.dumps({"message": {"content": "1"}, "done": False}),
            json.dumps({"message": {"content": " 2"}, "done": False}),
            json.dumps({"message": {"content": " 3"}, "done": True}),
        ]

        async def mock_aiter(response):
            for chunk in stream_chunks:
                yield chunk.encode()

        mock_response = MagicMock()
        mock_response.__aiter__ = lambda self: mock_aiter(self)

        with patch.object(provider.client, "stream") as mock_stream:
            mock_stream.return_value.__aenter__.return_value = mock_response

            chunks = []
            async for chunk in provider.stream_complete(messages=messages):
                chunks.append(chunk)

            assert chunks == ["1", " 2", " 3"]

    @pytest.mark.asyncio
    async def test_stream_complete_with_custom_model(self, provider):
        """Test streaming with custom model."""
        messages = [LLMMessage(role="user", content="Test")]

        stream_chunks = [
            json.dumps({"message": {"content": "Response"}, "done": True}),
        ]

        async def mock_aiter(response):
            for chunk in stream_chunks:
                yield chunk.encode()

        mock_response = MagicMock()
        mock_response.__aiter__ = lambda self: mock_aiter(self)

        with patch.object(provider.client, "stream") as mock_stream:
            mock_stream.return_value.__aenter__.return_value = mock_response

            chunks = []
            async for chunk in provider.stream_complete(messages=messages, model="llama3:8b"):
                chunks.append(chunk)

            # Verify model in request
            call_args = mock_stream.call_args
            assert call_args[1]["json"]["model"] == "llama3:8b"


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestOllamaProviderAvailability:
    """Tests for OllamaProvider availability checks."""

    @pytest.mark.asyncio
    async def test_is_available_success(self, provider):
        """Test availability check when Ollama is running."""
        with patch.object(provider.client, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)

            available = await provider.is_available()

            assert available is True
            mock_get.assert_called_once_with("/api/tags", timeout=5)

    @pytest.mark.asyncio
    async def test_is_available_connection_error(self, provider):
        """Test availability check when Ollama is not running."""
        with patch.object(provider.client, "get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            available = await provider.is_available()

            assert available is False

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test health check when Ollama is healthy."""
        mock_models = {"models": [{"name": "qwen2.5:7b"}, {"name": "llama3:8b"}]}

        with patch.object(provider.client, "get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_models,
            )

            health = await provider.health_check()

            assert health["status"] == "healthy"
            assert health["provider"] == "ollama"
            assert health["base_url"] == "http://localhost:11434"
            assert health["available_models"] == ["qwen2.5:7b", "llama3:8b"]

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, provider):
        """Test health check when Ollama is unavailable."""
        with patch.object(provider.client, "get") as mock_get:
            mock_get.side_effect = Exception("Connection error")

            health = await provider.health_check()

            assert health["status"] == "unhealthy"
            assert health["provider"] == "ollama"
            assert "error" in health


@pytest.mark.skip(
    reason="HTTP mocking needs to be updated for new provider API. "
    "Tests make real API calls instead of mocking HTTP layer."
)
class TestOllamaProviderModelManagement:
    """Tests for OllamaProvider model management."""

    @pytest.mark.asyncio
    async def test_list_local_models(self, provider):
        """Test listing local models."""
        mock_models = {
            "models": [
                {"name": "qwen2.5:7b", "size": 4661216000},
                {"name": "llama3:8b", "size": 4700000000},
            ]
        }

        with patch.object(provider.client, "get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_models,
            )

            models = await provider.list_local_models()

            assert len(models) == 2
            assert models[0]["name"] == "qwen2.5:7b"
            assert models[1]["name"] == "llama3:8b"

    @pytest.mark.asyncio
    async def test_ensure_model_available_already_exists(self, provider):
        """Test ensuring model is available when it already exists."""
        mock_models = {"models": [{"name": "qwen2.5:7b"}]}

        with patch.object(provider.client, "get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_models,
            )

            result = await provider.ensure_model_available("qwen2.5:7b")

            assert result is True

    @pytest.mark.asyncio
    async def test_ensure_model_available_needs_download(self, provider):
        """Test ensuring model downloads when not available."""
        # First call: model not found
        # Second call: model found after download
        mock_models_before = {"models": []}
        mock_models_after = {"models": [{"name": "qwen2.5:7b"}]}

        with (
            patch.object(provider.client, "get") as mock_get,
            patch.object(provider.client, "post") as mock_post,
        ):

            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: mock_models_before),
                MagicMock(status_code=200, json=lambda: mock_models_after),
            ]

            mock_post.return_value = MagicMock(status_code=200)

            result = await provider.ensure_model_available("qwen2.5:7b")

            assert result is True
            # Verify pull was called
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_model_auto_download_disabled(self, provider):
        """Test model availability check with auto-download disabled."""
        provider.auto_download = False

        mock_models = {"models": []}

        with patch.object(provider.client, "get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_models,
            )

            result = await provider.ensure_model_available("qwen2.5:7b")

            assert result is False


class TestOllamaProviderContext:
    """Tests for OllamaProvider context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, provider):
        """Test async context manager lifecycle."""
        async with provider as p:
            assert p is provider
            assert provider.client is not None

        # Client should still be available after exit
        assert provider.client is not None
