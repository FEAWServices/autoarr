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
parse structured responses, and track token usage using OpenRouter provider.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.api.services.llm_agent import (
    LLMAgent,
    PromptTemplate,
    StructuredOutputParser,
    TokenUsageTracker,
)
from autoarr.api.services.models import Priority


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


class TestLLMAgent:
    """Tests for LLM Agent service with OpenRouter provider."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self) -> None:
        """Test that agent initializes with correct dependencies."""
        # Arrange & Act
        agent = LLMAgent(api_key="sk-or-test-key")

        # Assert
        assert agent.token_tracker is not None
        assert agent.model == "anthropic/claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_agent_initialization_with_custom_model(self) -> None:
        """Test that agent accepts custom model."""
        # Arrange & Act
        agent = LLMAgent(api_key="sk-or-test-key", model="openai/gpt-4o")

        # Assert
        assert agent.model == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_analyze_configuration_generates_recommendation(self) -> None:
        """Test that agent generates contextual recommendation."""
        # Arrange
        from autoarr.shared.llm import LLMResponse

        agent = LLMAgent(api_key="sk-or-test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple for redundancy"},
        }

        mock_response = LLMResponse(
            content=json.dumps(
                {
                    "explanation": "Multiple servers provide redundancy and improve reliability",
                    "priority": "high",
                    "impact": "Better download reliability and reduced downtime",
                    "reasoning": "Single server creates single point of failure",
                }
            ),
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            model="anthropic/claude-3.5-sonnet",
            provider="openrouter",
        )

        with patch(
            "autoarr.shared.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.provider_name = "openrouter"
            mock_provider.complete = AsyncMock(return_value=mock_response)
            mock_provider_class.return_value = mock_provider

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
        from autoarr.shared.llm import LLMResponse

        agent = LLMAgent(api_key="sk-or-test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple"},
        }

        mock_response = LLMResponse(
            content=json.dumps(
                {
                    "explanation": "Test explanation",
                    "priority": "medium",
                    "impact": "Test impact",
                    "reasoning": "Test reasoning",
                }
            ),
            usage={"prompt_tokens": 150, "completion_tokens": 75},
            model="anthropic/claude-3.5-sonnet",
            provider="openrouter",
        )

        with patch(
            "autoarr.shared.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.provider_name = "openrouter"
            mock_provider.complete = AsyncMock(return_value=mock_response)
            mock_provider_class.return_value = mock_provider

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
        agent = LLMAgent(api_key="sk-or-test-key")
        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple"},
        }

        with patch(
            "autoarr.shared.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.provider_name = "openrouter"
            mock_provider.complete = AsyncMock(side_effect=Exception("API Error"))
            mock_provider_class.return_value = mock_provider

            # Act & Assert
            with pytest.raises(Exception, match="API Error"):
                await agent.analyze_configuration(context)

    @pytest.mark.asyncio
    async def test_get_token_usage_stats(self) -> None:
        """Test getting token usage statistics from agent."""
        # Arrange
        agent = LLMAgent(api_key="sk-or-test-key")
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
        agent = LLMAgent(api_key="sk-or-test-key")
        agent.token_tracker.record_usage(input_tokens=1_000_000, output_tokens=500_000)

        # Act
        cost = agent.estimate_costs()

        # Assert - Default pricing: $3/M input, $15/M output
        # 1M * $3 + 0.5M * $15 = $3 + $7.5 = $10.5
        assert cost == pytest.approx(10.5, rel=0.01)

    @pytest.mark.asyncio
    async def test_estimate_costs_with_model_pricing(self) -> None:
        """Test cost estimation with model-specific pricing from OpenRouter."""
        # Arrange
        agent = LLMAgent(api_key="sk-or-test-key")
        agent.token_tracker.record_usage(input_tokens=1_000_000, output_tokens=500_000)

        # OpenRouter pricing is per token, we store per million
        model_pricing = {
            "prompt": 1.0,  # $1 per million input tokens
            "completion": 5.0,  # $5 per million output tokens
        }

        # Act
        cost = agent.estimate_costs(model_pricing=model_pricing)

        # Assert - 1M * $1 + 0.5M * $5 = $1 + $2.5 = $3.5
        assert cost == pytest.approx(3.5, rel=0.01)
