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

"""
Unit tests for LLM Agent service.

This module tests the LLM Agent's ability to generate contextual recommendations,
parse structured responses, handle retries, and track token usage.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic import APIError, RateLimitError

from autoarr.api.services.llm_agent import (
    ClaudeClient,
    LLMAgent,
    PromptTemplate,
    StructuredOutputParser,
    TokenUsageTracker,
)
from autoarr.api.services.models import Priority


@pytest.mark.skip(
    reason="Old Claude client tests - replaced by provider system. See tests/unit/shared/llm/ for provider tests."
)
class TestClaudeClient:
    """Tests for Claude API client."""

    @pytest.mark.asyncio
    async def test_client_initialization(self) -> None:
        """Test that Claude client initializes with correct parameters."""
        # Arrange & Act
        client = ClaudeClient(  # noqa: F841
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
        )

        # Assert
        assert client.api_key == "test-key"
        assert client.model == "claude-3-5-sonnet-20241022"
        assert client.max_tokens == 4096

    @pytest.mark.asyncio
    async def test_client_uses_default_model(self) -> None:
        """Test that client uses default model when not specified."""
        # Arrange & Act
        client = ClaudeClient(api_key="test-key")  # noqa: F841

        # Assert
        assert client.model == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_send_message_success(self) -> None:
        """Test successful message sending to Claude API."""
        # Arrange
        client = ClaudeClient(api_key="test-key")  # noqa: F841
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)

        with patch("autoarr.api.services.llm_agent.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()  # noqa: F841
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            # Act
            response = await client.send_message(
                system_prompt="You are a helpful assistant.",
                user_message="Hello!",
            )

            # Assert
            assert response["content"] == "Test response"
            assert response["usage"]["input_tokens"] == 10
            assert response["usage"]["output_tokens"] == 20

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self) -> None:
        """Test that client retries on rate limit errors."""
        # Arrange
        client = ClaudeClient(api_key="test-key", max_retries=3, retry_delay=0.1)  # noqa: F841
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success after retry")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)

        # Create proper mock response and body for RateLimitError
        mock_error_response = MagicMock()
        mock_error_response.status_code = 429
        mock_error_body = {"type": "error", "error": {"type": "rate_limit_error"}}

        with patch("autoarr.api.services.llm_agent.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()  # noqa: F841
            # First call raises RateLimitError, second succeeds
            rate_limit_error = RateLimitError(
                "Rate limited", response=mock_error_response, body=mock_error_body
            )
            mock_client.messages.create = AsyncMock(side_effect=[rate_limit_error, mock_response])
            mock_anthropic.return_value = mock_client

            # Act
            response = await client.send_message(
                system_prompt="You are a helpful assistant.",
                user_message="Hello!",
            )

            # Assert
            assert response["content"] == "Success after retry"
            assert mock_client.messages.create.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self) -> None:
        """Test that retry delay increases exponentially."""
        # Arrange
        client = ClaudeClient(api_key="test-key", max_retries=3, retry_delay=0.1)  # noqa: F841

        # Create proper mock response and body for RateLimitError
        mock_error_response = MagicMock()
        mock_error_response.status_code = 429
        mock_error_body = {"type": "error", "error": {"type": "rate_limit_error"}}

        rate_limit_error = RateLimitError(
            "Rate limited", response=mock_error_response, body=mock_error_body
        )

        with patch("autoarr.api.services.llm_agent.AsyncAnthropic") as mock_anthropic:
            with patch("asyncio.sleep") as mock_sleep:
                mock_client = AsyncMock()  # noqa: F841
                mock_client.messages.create = AsyncMock(side_effect=rate_limit_error)
                mock_anthropic.return_value = mock_client

                # Act & Assert
                with pytest.raises(RateLimitError):
                    await client.send_message(system_prompt="Test", user_message="Test")

                # Verify exponential backoff: 0.1, 0.2, 0.4
                assert mock_sleep.call_count >= 2
                calls = [call[0][0] for call in mock_sleep.call_args_list]  # noqa: F841
                assert calls[0] == pytest.approx(0.1, rel=0.1)
                assert calls[1] == pytest.approx(0.2, rel=0.1)

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self) -> None:
        """Test that client raises error after max retries exceeded."""
        # Arrange
        client = ClaudeClient(api_key="test-key", max_retries=2, retry_delay=0.1)  # noqa: F841

        # Create proper mock response and body for RateLimitError
        mock_error_response = MagicMock()
        mock_error_response.status_code = 429
        mock_error_body = {"type": "error", "error": {"type": "rate_limit_error"}}

        rate_limit_error = RateLimitError(
            "Rate limited", response=mock_error_response, body=mock_error_body
        )

        with patch("autoarr.api.services.llm_agent.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()  # noqa: F841
            mock_client.messages.create = AsyncMock(side_effect=rate_limit_error)
            mock_anthropic.return_value = mock_client

            # Act & Assert
            with pytest.raises(RateLimitError):
                await client.send_message(system_prompt="Test", user_message="Test")

            # Should try initial + 2 retries = 3 total
            assert mock_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_handles_api_error(self) -> None:
        """Test that client handles API errors gracefully."""
        # Arrange
        client = ClaudeClient(api_key="test-key")  # noqa: F841

        # Create proper mock request for APIError
        mock_request = MagicMock()
        mock_error_body = {"type": "error", "error": {"message": "API Error"}}
        api_error = APIError("API Error", request=mock_request, body=mock_error_body)

        with patch("autoarr.api.services.llm_agent.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()  # noqa: F841
            mock_client.messages.create = AsyncMock(side_effect=api_error)
            mock_anthropic.return_value = mock_client

            # Act & Assert
            with pytest.raises(APIError):
                await client.send_message(system_prompt="Test", user_message="Test")


class TestPromptTemplate:
    """Tests for prompt template system."""

    def test_template_initialization(self) -> None:
        """Test that template initializes correctly."""
        # Arrange & Act
        template = PromptTemplate(
            name="test",
            system_template="You are {role}",
            user_template="Please analyze {content}",
        )

        # Assert
        assert template.name == "test"
        assert template.system_template == "You are {role}"
        assert template.user_template == "Please analyze {content}"

    def test_render_system_prompt(self) -> None:
        """Test rendering system prompt with variables."""
        # Arrange
        template = PromptTemplate(
            name="test",
            system_template="You are a {role} expert in {domain}.",
            user_template="Analyze this",
        )

        # Act
        rendered = template.render_system(role="configuration", domain="SABnzbd")

        # Assert
        assert rendered == "You are a configuration expert in SABnzbd."

    def test_render_user_prompt(self) -> None:
        """Test rendering user prompt with variables."""
        # Arrange
        template = PromptTemplate(
            name="test",
            system_template="You are an expert.",
            user_template="Analyze {app} with settings: {settings}",
        )

        # Act
        rendered = template.render_user(app="sabnzbd", settings="{'servers': 1}")

        # Assert
        assert rendered == "Analyze sabnzbd with settings: {'servers': 1}"

    def test_render_missing_variable_raises_error(self) -> None:
        """Test that missing variable raises KeyError."""
        # Arrange
        template = PromptTemplate(
            name="test",
            system_template="You are {role}",
            user_template="Test",
        )

        # Act & Assert
        with pytest.raises(KeyError):
            template.render_system()  # Missing 'role'

    def test_configuration_analysis_template(self) -> None:
        """Test the configuration analysis template."""
        # Arrange
        template = PromptTemplate.configuration_analysis()

        # Act
        system = template.render_system()
        user = template.render_user(
            app="sabnzbd",
            current_config=json.dumps({"servers": 1}),
            best_practice=json.dumps({"servers": "multiple for redundancy"}),
        )

        # Assert
        assert "configuration" in system.lower()
        assert "sabnzbd" in user
        assert "servers" in user


class TestStructuredOutputParser:
    """Tests for structured output parser."""

    def test_parse_valid_json(self) -> None:
        """Test parsing valid JSON response."""
        # Arrange
        parser = StructuredOutputParser()
        response = """Here's the analysis:

```json
{
    "explanation": "Multiple servers provide redundancy",
    "priority": "high",
    "impact": "Better reliability"
}
```
"""

        # Act
        result = parser.parse(response)  # noqa: F841

        # Assert
        assert result["explanation"] == "Multiple servers provide redundancy"
        assert result["priority"] == "high"
        assert result["impact"] == "Better reliability"

    def test_parse_json_without_markdown(self) -> None:
        """Test parsing JSON without markdown code blocks."""
        # Arrange
        parser = StructuredOutputParser()
        response = '{"explanation": "Test", "priority": "medium"}'

        # Act
        result = parser.parse(response)  # noqa: F841

        # Assert
        assert result["explanation"] == "Test"
        assert result["priority"] == "medium"

    def test_parse_invalid_json_raises_error(self) -> None:
        """Test that invalid JSON raises ValueError."""
        # Arrange
        parser = StructuredOutputParser()
        response = "This is not JSON"

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parser.parse(response)

    def test_validate_required_fields(self) -> None:
        """Test validation of required fields."""
        # Arrange
        parser = StructuredOutputParser(required_fields=["explanation", "priority"])
        response = '{"explanation": "Test", "priority": "high"}'

        # Act
        result = parser.parse(response)  # noqa: F841

        # Assert
        assert "explanation" in result
        assert "priority" in result

    def test_validate_missing_required_field_raises_error(self) -> None:
        """Test that missing required field raises ValueError."""
        # Arrange
        parser = StructuredOutputParser(required_fields=["explanation", "priority"])
        response = '{"explanation": "Test"}'  # Missing 'priority'

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field"):
            parser.parse(response)


class TestTokenUsageTracker:
    """Tests for token usage tracker."""

    def test_tracker_initialization(self) -> None:
        """Test tracker initializes with zero usage."""
        # Arrange & Act
        tracker = TokenUsageTracker()

        # Assert
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert tracker.total_requests == 0

    def test_record_usage(self) -> None:
        """Test recording token usage."""
        # Arrange
        tracker = TokenUsageTracker()

        # Act
        tracker.record_usage(input_tokens=100, output_tokens=50)

        # Assert
        assert tracker.total_input_tokens == 100
        assert tracker.total_output_tokens == 50
        assert tracker.total_requests == 1

    def test_record_multiple_requests(self) -> None:
        """Test recording multiple requests."""
        # Arrange
        tracker = TokenUsageTracker()

        # Act
        tracker.record_usage(input_tokens=100, output_tokens=50)
        tracker.record_usage(input_tokens=200, output_tokens=75)

        # Assert
        assert tracker.total_input_tokens == 300
        assert tracker.total_output_tokens == 125
        assert tracker.total_requests == 2

    def test_get_stats(self) -> None:
        """Test getting usage statistics."""
        # Arrange
        tracker = TokenUsageTracker()
        tracker.record_usage(input_tokens=1000, output_tokens=500)
        tracker.record_usage(input_tokens=2000, output_tokens=1000)

        # Act
        stats = tracker.get_stats()

        # Assert
        assert stats["total_input_tokens"] == 3000
        assert stats["total_output_tokens"] == 1500
        assert stats["total_tokens"] == 4500
        assert stats["total_requests"] == 2
        assert stats["avg_input_tokens_per_request"] == 1500
        assert stats["avg_output_tokens_per_request"] == 750

    def test_get_stats_no_requests(self) -> None:
        """Test stats when no requests have been made."""
        # Arrange
        tracker = TokenUsageTracker()

        # Act
        stats = tracker.get_stats()

        # Assert
        assert stats["total_tokens"] == 0
        assert stats["avg_input_tokens_per_request"] == 0
        assert stats["avg_output_tokens_per_request"] == 0

    def test_estimate_cost(self) -> None:
        """Test cost estimation based on token usage."""
        # Arrange
        tracker = TokenUsageTracker()
        tracker.record_usage(input_tokens=1_000_000, output_tokens=500_000)

        # Act
        cost = tracker.estimate_cost(
            input_cost_per_million=3.0,  # $3 per million input tokens
            output_cost_per_million=15.0,  # $15 per million output tokens
        )

        # Assert
        # 1M input @ $3/M = $3, 500k output @ $15/M = $7.50, total = $10.50
        assert cost == pytest.approx(10.5, rel=0.01)

    def test_reset_stats(self) -> None:
        """Test resetting usage statistics."""
        # Arrange
        tracker = TokenUsageTracker()
        tracker.record_usage(input_tokens=100, output_tokens=50)

        # Act
        tracker.reset()

        # Assert
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert tracker.total_requests == 0


@pytest.mark.skip(
    reason="Old LLMAgent tests - tests old implementation with client attribute. "
    "New implementation uses provider system. See tests/unit/shared/llm/ for provider tests."
)
class TestLLMAgent:
    """Tests for LLM Agent service."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self) -> None:
        """Test that agent initializes with correct dependencies."""
        # Arrange & Act
        agent = LLMAgent(api_key="test-key")

        # Assert
        assert agent.client is not None
        assert agent.token_tracker is not None

    @pytest.mark.asyncio
    async def test_analyze_configuration_generates_recommendation(self) -> None:
        """Test that agent generates contextual recommendation."""
        # Arrange
        agent = LLMAgent(api_key="test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple for redundancy"},
        }

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Having multiple servers provides redundancy and improves download reliability",  # noqa: E501
                    "priority": "high",
                    "impact": "Better download reliability and reduced downtime",
                    "reasoning": "Single server creates single point of failure",
                }
            ),
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            recommendation = await agent.analyze_configuration(context)

            # Assert
            assert "multiple servers" in recommendation.explanation.lower()
            assert recommendation.priority == Priority.HIGH
            assert "reliability" in recommendation.impact.lower()

    @pytest.mark.asyncio
    async def test_analyze_configuration_tracks_token_usage(self) -> None:
        """Test that token usage is tracked during analysis."""
        # Arrange
        agent = LLMAgent(api_key="test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple"},
        }

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Test explanation",
                    "priority": "medium",
                    "impact": "Test impact",
                    "reasoning": "Test reasoning",
                }
            ),
            "usage": {"input_tokens": 150, "output_tokens": 75},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            await agent.analyze_configuration(context)

            # Assert
            stats = agent.get_token_usage_stats()
            assert stats["total_input_tokens"] == 150
            assert stats["total_output_tokens"] == 75
            assert stats["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_analyze_configuration_handles_api_error(self) -> None:
        """Test that agent handles API errors gracefully."""
        # Arrange
        agent = LLMAgent(api_key="test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple"},
        }

        # Create proper mock request for APIError
        mock_request = MagicMock()
        mock_error_body = {"type": "error", "error": {"message": "API Error"}}
        api_error = APIError("API Error", request=mock_request, body=mock_error_body)

        with patch.object(agent.client, "send_message", side_effect=api_error):
            # Act & Assert
            with pytest.raises(APIError):
                await agent.analyze_configuration(context)

    @pytest.mark.asyncio
    async def test_analyze_configuration_validates_priority(self) -> None:
        """Test that priority values are validated."""
        # Arrange
        agent = LLMAgent(api_key="test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple"},
        }

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Test",
                    "priority": "medium",
                    "impact": "Test impact",
                    "reasoning": "Test",
                }
            ),
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            recommendation = await agent.analyze_configuration(context)

            # Assert
            assert recommendation.priority in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_get_token_usage_stats(self) -> None:
        """Test getting token usage statistics from agent."""
        # Arrange
        agent = LLMAgent(api_key="test-key")
        agent.token_tracker.record_usage(input_tokens=500, output_tokens=250)

        # Act
        stats = agent.get_token_usage_stats()

        # Assert
        assert stats["total_input_tokens"] == 500
        assert stats["total_output_tokens"] == 250
        assert stats["total_tokens"] == 750

    @pytest.mark.asyncio
    async def test_estimate_costs(self) -> None:
        """Test cost estimation for LLM usage."""
        # Arrange
        agent = LLMAgent(api_key="test-key")
        agent.token_tracker.record_usage(input_tokens=1_000_000, output_tokens=500_000)

        # Act
        cost = agent.estimate_costs()

        # Assert
        assert cost > 0
        assert isinstance(cost, (int, float))
