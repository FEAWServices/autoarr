"""
Integration tests for LLM Agent service.

These tests verify the LLM Agent works end-to-end with real API calls
(mocked) and integrates properly with the Configuration Manager.

Note: These tests use mocking to avoid requiring a real API key.
For manual testing with real API, set ANTHROPIC_API_KEY environment variable.
"""

import json
import os
from unittest.mock import patch

import pytest

from autoarr.api.services.llm_agent import LLMAgent
from autoarr.api.services.models import Priority


class TestLLMAgentIntegration:
    """Integration tests for LLM Agent."""

    @pytest.mark.asyncio
    async def test_end_to_end_configuration_analysis(self) -> None:
        """Test complete flow from context to recommendation."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        context = {
            "app": "sabnzbd",
            "current_config": {
                "servers": 1,
                "incomplete_dir": "",
                "download_dir": "/downloads",
            },
            "best_practice": {
                "servers": "multiple for redundancy",
                "incomplete_dir": "separate from complete dir",
                "download_dir": "/downloads",
            },
        }

        # Mock response that looks like real Claude output
        mock_claude_response = {
            "content": json.dumps(
                {
                    "explanation": "Having multiple Usenet servers provides redundancy and improves download reliability. If one server is down or missing articles, the downloader can automatically fail over to another server. Additionally, using a separate incomplete directory prevents partially downloaded files from being processed by media management tools.",  # noqa: E501
                    "priority": "high",
                    "impact": "Single server creates a single point of failure. Without redundancy, failed downloads are more likely and manual intervention is required. Mixed complete/incomplete files can cause processing errors.",  # noqa: E501
                    "reasoning": "Redundant servers significantly improve download success rates, especially for older or less popular content. Separate directories prevent media tools from attempting to process incomplete files, which can cause crashes or corruption.",  # noqa: E501
                }
            ),
            "usage": {"input_tokens": 250, "output_tokens": 120},
        }

        with patch.object(agent.client, "send_message", return_value=mock_claude_response):
            # Act
            recommendation = await agent.analyze_configuration(context)

            # Assert
            assert recommendation is not None
            assert "redundancy" in recommendation.explanation.lower()
            assert recommendation.priority == Priority.HIGH
            assert "single point of failure" in recommendation.impact.lower()
            assert len(recommendation.reasoning) > 50

            # Verify token tracking
            stats = agent.get_token_usage_stats()
            assert stats["total_input_tokens"] == 250
            assert stats["total_output_tokens"] == 120
            assert stats["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_handles_medium_priority_recommendation(self) -> None:
        """Test handling of medium priority recommendations."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        context = {
            "app": "sonarr",
            "current_config": {"rename_episodes": False},
            "best_practice": {"rename_episodes": True},
        }

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Enabling episode renaming provides consistent file naming across your library, making it easier to organize and identify episodes.",  # noqa: E501
                    "priority": "medium",
                    "impact": "Inconsistent naming can make library browsing more difficult and may affect media player metadata matching.",  # noqa: E501
                    "reasoning": "While not critical to functionality, consistent naming improves user experience and media management.",  # noqa: E501
                }
            ),
            "usage": {"input_tokens": 150, "output_tokens": 80},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            recommendation = await agent.analyze_configuration(context)

            # Assert
            assert recommendation.priority == Priority.MEDIUM
            assert "consistent" in recommendation.explanation.lower()

    @pytest.mark.asyncio
    async def test_handles_low_priority_recommendation(self) -> None:
        """Test handling of low priority recommendations."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        context = {
            "app": "radarr",
            "current_config": {"enable_completed_download_handling": True},
            "best_practice": {"enable_completed_download_handling": True},
        }

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Your configuration already follows the best practice for completed download handling.",  # noqa: E501
                    "priority": "low",
                    "impact": "No impact - configuration is optimal.",
                    "reasoning": "This setting is correctly configured.",
                }
            ),
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            recommendation = await agent.analyze_configuration(context)

            # Assert
            assert recommendation.priority == Priority.LOW
            assert (
                "optimal" in recommendation.explanation.lower()
                or "best practice" in recommendation.explanation.lower()
            )

    @pytest.mark.asyncio
    async def test_multiple_analyses_track_usage_correctly(self) -> None:
        """Test that multiple analyses accumulate token usage."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        contexts = [
            {
                "app": "sabnzbd",
                "current_config": {"servers": 1},
                "best_practice": {"servers": "multiple"},
            },
            {
                "app": "sonarr",
                "current_config": {"monitoring": "none"},
                "best_practice": {"monitoring": "all"},
            },
            {
                "app": "radarr",
                "current_config": {"minimum_availability": "announced"},
                "best_practice": {"minimum_availability": "released"},
            },
        ]

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Test explanation",
                    "priority": "medium",
                    "impact": "Test impact",
                    "reasoning": "Test reasoning",
                }
            ),
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            for context in contexts:
                await agent.analyze_configuration(context)

            # Assert
            stats = agent.get_token_usage_stats()
            assert stats["total_input_tokens"] == 300  # 100 * 3
            assert stats["total_output_tokens"] == 150  # 50 * 3
            assert stats["total_requests"] == 3

    @pytest.mark.asyncio
    async def test_cost_estimation_accuracy(self) -> None:
        """Test that cost estimation calculates correctly."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        # Simulate 1M input tokens and 500K output tokens
        agent.token_tracker.record_usage(
            input_tokens=1_000_000,
            output_tokens=500_000,
        )

        # Act
        cost = agent.estimate_costs(
            input_cost_per_million=3.0,
            output_cost_per_million=15.0,
        )

        # Assert
        # 1M input @ $3/M = $3.00
        # 500K output @ $15/M = $7.50
        # Total = $10.50
        assert cost == pytest.approx(10.5, rel=0.01)

    @pytest.mark.asyncio
    async def test_handles_invalid_priority_gracefully(self) -> None:
        """Test that invalid priority defaults to medium."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple"},
        }

        # Response with invalid priority value
        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Test explanation",
                    "priority": "critical",  # Invalid - should default to medium
                    "impact": "Test impact",
                    "reasoning": "Test reasoning",
                }
            ),
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        with patch.object(agent.client, "send_message", return_value=mock_response):
            # Act
            recommendation = await agent.analyze_configuration(context)

            # Assert - Should default to medium for invalid priority
            assert recommendation.priority == Priority.MEDIUM

    @pytest.mark.asyncio
    async def test_prompt_includes_all_context(self) -> None:
        """Test that generated prompt includes all context information."""
        # Arrange
        agent = LLMAgent(api_key="test-key")

        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1, "speed_limit": ""},
            "best_practice": {
                "servers": "multiple",
                "speed_limit": "reasonable limit to prevent ISP throttling",
            },
        }

        mock_response = {
            "content": json.dumps(
                {
                    "explanation": "Test",
                    "priority": "medium",
                    "impact": "Test",
                    "reasoning": "Test",
                }
            ),
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

        captured_prompt = None

        async def capture_send_message(system_prompt, user_message, temperature=0.7):
            nonlocal captured_prompt
            captured_prompt = user_message
            return mock_response

        with patch.object(agent.client, "send_message", side_effect=capture_send_message):
            # Act
            await agent.analyze_configuration(context)

            # Assert
            assert captured_prompt is not None
            assert "sabnzbd" in captured_prompt.lower()
            assert "servers" in captured_prompt
            assert "speed_limit" in captured_prompt
            assert "multiple" in captured_prompt
            assert "throttling" in captured_prompt.lower()


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY environment variable for real API test",
)
class TestLLMAgentRealAPI:
    """Integration tests using real Claude API (requires API key)."""

    @pytest.mark.asyncio
    async def test_real_api_configuration_analysis(self) -> None:
        """Test with real Claude API (manual test only)."""
        # Arrange
        api_key = os.getenv("ANTHROPIC_API_KEY")
        agent = LLMAgent(api_key=api_key)

        context = {
            "app": "sabnzbd",
            "current_config": {"servers": 1},
            "best_practice": {"servers": "multiple for redundancy"},
        }

        # Act
        recommendation = await agent.analyze_configuration(context)

        # Assert
        assert recommendation is not None
        assert len(recommendation.explanation) > 20
        assert recommendation.priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        assert len(recommendation.impact) > 10
        assert len(recommendation.reasoning) > 10

        # Verify token usage was tracked
        stats = agent.get_token_usage_stats()
        assert stats["total_requests"] == 1
        assert stats["total_input_tokens"] > 0
        assert stats["total_output_tokens"] > 0

        # Print results for manual verification
        print("\n=== Real API Test Results ===")
        print(f"Explanation: {recommendation.explanation}")
        print(f"Priority: {recommendation.priority}")
        print(f"Impact: {recommendation.impact}")
        print(f"Reasoning: {recommendation.reasoning}")
        print(f"\nToken Usage: {stats}")
        print(f"Estimated Cost: ${agent.estimate_costs():.4f}")
