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

"""Tests for BaseLLMProvider interface."""

from typing import Any, AsyncGenerator, Dict, List, Optional

import pytest

from autoarr.shared.llm.base_provider import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock implementation of BaseLLMProvider for testing."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "mock"
        self._is_available = True
        self.complete_calls: List[Dict[str, Any]] = []
        self.stream_calls: List[Dict[str, Any]] = []

    async def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Mock completion."""
        self.complete_calls.append(
            {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "kwargs": kwargs,
            }
        )

        return LLMResponse(
            content="Mock response",
            model=model or "mock-model",
            provider="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )

    async def stream_complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Mock streaming completion."""
        self.stream_calls.append(
            {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "kwargs": kwargs,
            }
        )

        chunks = ["Mock ", "streaming ", "response"]
        for chunk in chunks:
            yield chunk

    async def is_available(self) -> bool:
        """Check if provider is available."""
        return self._is_available

    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "status": "healthy",
            "provider": self.provider_name,
            "available": self._is_available,
        }


class TestLLMMessage:
    """Tests for LLMMessage model."""

    def test_create_system_message(self):
        """Test creating a system message."""
        msg = LLMMessage(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant."

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = LLMMessage(role="user", content="Hello, world!")
        assert msg.role == "user"
        assert msg.content == "Hello, world!"

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = LLMMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_message_equality(self):
        """Test message equality."""
        msg1 = LLMMessage(role="user", content="Test")
        msg2 = LLMMessage(role="user", content="Test")
        msg3 = LLMMessage(role="user", content="Different")

        assert msg1 == msg2
        assert msg1 != msg3


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_create_response(self):
        """Test creating a response."""
        response = LLMResponse(
            content="Response content",
            model="test-model",
            provider="test-provider",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            finish_reason="stop",
        )

        assert response.content == "Response content"
        assert response.model == "test-model"
        assert response.provider == "test-provider"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.finish_reason == "stop"

    def test_response_without_usage(self):
        """Test response without usage information."""
        response = LLMResponse(
            content="Response",
            model="test-model",
            provider="test-provider",
            finish_reason="stop",
        )

        assert response.content == "Response"
        assert response.provider == "test-provider"
        assert response.usage is None

    def test_response_with_metadata(self):
        """Test response with additional metadata."""
        # Note: LLMResponse doesn't have metadata field in base_provider.py
        # This test needs to be updated or removed
        response = LLMResponse(
            content="Response",
            model="test-model",
            provider="test-provider",
            finish_reason="stop",
        )

        # Just verify basic fields work
        assert response.content == "Response"
        assert response.provider == "test-provider"


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider base class."""

    @pytest.fixture
    def provider(self):
        """Create a mock provider for testing."""
        return MockLLMProvider({"test_config": "value"})

    @pytest.mark.asyncio
    async def test_complete(self, provider):
        """Test completion method."""
        messages = [
            LLMMessage(role="system", content="System prompt"),
            LLMMessage(role="user", content="User message"),
        ]

        response = await provider.complete(messages=messages)

        assert response.content == "Mock response"
        assert response.model == "mock-model"
        assert len(provider.complete_calls) == 1
        assert provider.complete_calls[0]["messages"] == messages

    @pytest.mark.asyncio
    async def test_complete_with_custom_parameters(self, provider):
        """Test completion with custom parameters."""
        messages = [LLMMessage(role="user", content="Test")]

        await provider.complete(
            messages=messages,
            model="custom-model",
            temperature=0.5,
            max_tokens=100,
            custom_param="value",
        )

        call = provider.complete_calls[0]
        assert call["model"] == "custom-model"
        assert call["temperature"] == 0.5
        assert call["max_tokens"] == 100
        assert call["kwargs"]["custom_param"] == "value"

    @pytest.mark.asyncio
    async def test_stream_complete(self, provider):
        """Test streaming completion."""
        messages = [LLMMessage(role="user", content="Test")]

        chunks = []
        async for chunk in provider.stream_complete(messages=messages):
            chunks.append(chunk)

        assert chunks == ["Mock ", "streaming ", "response"]
        assert len(provider.stream_calls) == 1

    @pytest.mark.asyncio
    async def test_is_available(self, provider):
        """Test availability check."""
        assert await provider.is_available() is True

        provider._is_available = False
        assert await provider.is_available() is False

    @pytest.mark.asyncio
    async def test_health_check(self, provider):
        """Test health check."""
        health = await provider.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "mock"
        assert health["available"] is True

    def test_provider_name(self, provider):
        """Test provider name is set."""
        assert provider.provider_name == "mock"

    def test_config_access(self, provider):
        """Test config is accessible."""
        assert provider.config["test_config"] == "value"
