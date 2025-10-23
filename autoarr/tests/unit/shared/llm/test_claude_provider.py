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

"""Tests for ClaudeProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from autoarr.shared.llm.claude_provider import ClaudeProvider
from autoarr.shared.llm.base_provider import LLMMessage


@pytest.fixture
def claude_config():
    """Create Claude configuration for testing."""
    return {
        "api_key": "test-api-key",
        "default_model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "max_retries": 3,
        "retry_delay": 1.0,
    }


@pytest.fixture
def provider(claude_config):
    """Create ClaudeProvider instance for testing."""
    return ClaudeProvider(claude_config)


class TestClaudeProviderInit:
    """Tests for ClaudeProvider initialization."""

    def test_init_with_api_key(self, claude_config):
        """Test initialization with API key."""
        provider = ClaudeProvider(claude_config)

        assert provider.provider_name == "claude"
        assert provider.api_key == "test-api-key"
        assert provider.default_model == "claude-3-5-sonnet-20241022"
        assert provider.max_tokens == 4096
        assert provider.max_retries == 3

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        provider = ClaudeProvider({})

        assert provider.api_key == ""
        assert provider.default_model == "claude-3-5-sonnet-20241022"

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        config = {
            "api_key": "test-key",
            "default_model": "claude-3-opus-20240229",
        }

        provider = ClaudeProvider(config)

        assert provider.default_model == "claude-3-opus-20240229"


class TestClaudeProviderComplete:
    """Tests for ClaudeProvider complete method."""

    @pytest.mark.asyncio
    async def test_complete_success(self, provider):
        """Test successful completion."""
        messages = [
            LLMMessage(role="system", content="You are helpful."),
            LLMMessage(role="user", content="Hello!"),
        ]

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Hi there!")]
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.stop_reason = "end_turn"
        mock_message.usage = MagicMock(
            input_tokens=10,
            output_tokens=5,
        )

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        provider._client = mock_client

        response = await provider.complete(messages=messages)

        assert response.content == "Hi there!"
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.provider == "claude"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5
        assert response.finish_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_complete_with_system_message(self, provider):
        """Test completion properly separates system messages."""
        messages = [
            LLMMessage(role="system", content="System prompt"),
            LLMMessage(role="user", content="User message"),
        ]

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.stop_reason = "end_turn"
        mock_message.usage = MagicMock(input_tokens=10, output_tokens=5)

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        provider._client = mock_client

        await provider.complete(messages=messages)

        # Verify system was passed separately
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "System prompt"
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_complete_with_multiple_system_messages(self, provider):
        """Test completion with multiple system messages."""
        messages = [
            LLMMessage(role="system", content="First system"),
            LLMMessage(role="system", content="Second system"),
            LLMMessage(role="user", content="User message"),
        ]

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.stop_reason = "end_turn"
        mock_message.usage = MagicMock(input_tokens=10, output_tokens=5)

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        provider._client = mock_client

        await provider.complete(messages=messages)

        # Verify system messages were joined
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "First system\n\nSecond system"

    @pytest.mark.asyncio
    async def test_complete_with_custom_model(self, provider):
        """Test completion with custom model."""
        messages = [LLMMessage(role="user", content="Test")]

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_message.model = "claude-3-opus-20240229"
        mock_message.stop_reason = "end_turn"
        mock_message.usage = MagicMock(input_tokens=10, output_tokens=5)

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        provider._client = mock_client

        response = await provider.complete(messages=messages, model="claude-3-opus-20240229")

        assert response.model == "claude-3-opus-20240229"
        # Verify request used custom model
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-opus-20240229"

    @pytest.mark.asyncio
    async def test_complete_with_temperature(self, provider):
        """Test completion with custom temperature."""
        messages = [LLMMessage(role="user", content="Test")]

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.stop_reason = "end_turn"
        mock_message.usage = MagicMock(input_tokens=10, output_tokens=5)

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        provider._client = mock_client

        await provider.complete(messages=messages, temperature=0.3)

        # Verify temperature in request
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_complete_handles_rate_limit(self, provider):
        """Test completion handles rate limit errors with retry."""
        from anthropic import RateLimitError

        messages = [LLMMessage(role="user", content="Test")]

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Response")]
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.stop_reason = "end_turn"
        mock_message.usage = MagicMock(input_tokens=10, output_tokens=5)

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        # Fail once with rate limit, then succeed
        mock_client.messages.create = AsyncMock(
            side_effect=[
                RateLimitError("Rate limit exceeded"),
                mock_message,
            ]
        )
        provider._client = mock_client

        response = await provider.complete(messages=messages)

        assert response.content == "Response"
        # Verify it was called twice (retry)
        assert mock_client.messages.create.call_count == 2


class TestClaudeProviderStream:
    """Tests for ClaudeProvider stream_complete method."""

    @pytest.mark.asyncio
    async def test_stream_complete_success(self, provider):
        """Test successful streaming completion."""
        messages = [LLMMessage(role="user", content="Count to 3")]

        # Mock streaming chunks
        mock_chunks = [
            MagicMock(type="content_block_delta", delta=MagicMock(text="1")),
            MagicMock(type="content_block_delta", delta=MagicMock(text=" 2")),
            MagicMock(type="content_block_delta", delta=MagicMock(text=" 3")),
            MagicMock(type="message_stop"),
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.stream = AsyncMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_stream()))
        )
        provider._client = mock_client

        chunks = []
        async for chunk in provider.stream_complete(messages=messages):
            chunks.append(chunk)

        assert chunks == ["1", " 2", " 3"]

    @pytest.mark.asyncio
    async def test_stream_complete_with_system_message(self, provider):
        """Test streaming with system message separation."""
        messages = [
            LLMMessage(role="system", content="System prompt"),
            LLMMessage(role="user", content="User message"),
        ]

        mock_chunks = [
            MagicMock(type="content_block_delta", delta=MagicMock(text="Response")),
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_stream_cm = AsyncMock()
        mock_stream_cm.__aenter__ = AsyncMock(return_value=mock_stream())
        mock_client.messages.stream = AsyncMock(return_value=mock_stream_cm)
        provider._client = mock_client

        chunks = []
        async for chunk in provider.stream_complete(messages=messages):
            chunks.append(chunk)

        # Verify system was passed separately
        call_kwargs = mock_client.messages.stream.call_args[1]
        assert call_kwargs["system"] == "System prompt"


class TestClaudeProviderAvailability:
    """Tests for ClaudeProvider availability checks."""

    @pytest.mark.asyncio
    async def test_is_available_with_api_key(self, provider):
        """Test availability check with API key configured."""
        available = await provider.is_available()

        assert available is True

    @pytest.mark.asyncio
    async def test_is_available_without_api_key(self):
        """Test availability check without API key."""
        provider = ClaudeProvider({})

        available = await provider.is_available()

        assert available is False

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test health check when provider is healthy."""
        health = await provider.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "claude"
        assert health["api_key_configured"] is True
        assert health["model"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self):
        """Test health check without API key."""
        provider = ClaudeProvider({})

        health = await provider.health_check()

        assert health["status"] == "unhealthy"
        assert health["api_key_configured"] is False


class TestClaudeProviderContext:
    """Tests for ClaudeProvider context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, provider):
        """Test async context manager lifecycle."""
        async with provider as p:
            assert p is provider
            assert provider._client is not None

        # Client should be closed after exit
        assert provider._client is None

    @pytest.mark.asyncio
    async def test_context_manager_multiple_uses(self, provider):
        """Test context manager can be used multiple times."""
        async with provider:
            client1 = provider._client

        async with provider:
            client2 = provider._client

        # Different client instances
        assert client1 is not client2


class TestClaudeProviderErrorHandling:
    """Tests for ClaudeProvider error handling."""

    @pytest.mark.asyncio
    async def test_complete_handles_api_error(self, provider):
        """Test completion handles API errors."""
        from anthropic import APIError

        messages = [LLMMessage(role="user", content="Test")]

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=APIError("API error"))
        provider._client = mock_client

        with pytest.raises(Exception, match="Claude API error"):
            await provider.complete(messages=messages)

    @pytest.mark.asyncio
    async def test_complete_max_retries_exceeded(self, provider):
        """Test completion fails after max retries."""
        from anthropic import RateLimitError

        provider.max_retries = 2
        messages = [LLMMessage(role="user", content="Test")]

        # Create mock client and set it
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_client.messages.create = AsyncMock(side_effect=RateLimitError("Rate limit exceeded"))
        provider._client = mock_client

        with pytest.raises(Exception, match="Rate limit"):
            await provider.complete(messages=messages)

        # Should have tried max_retries + 1 times
        assert mock_client.messages.create.call_count == 3
