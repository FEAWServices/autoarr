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
Integration tests for Intelligent Recommendation Engine.

These tests verify the full end-to-end workflow of the recommendation engine,
including interaction with real (mocked) LLM responses and data sources.
"""

from unittest.mock import patch

import pytest

from autoarr.api.services.intelligent_recommendation_engine import IntelligentRecommendationEngine
from autoarr.api.services.llm_agent import LLMRecommendation
from autoarr.api.services.models import Priority


@pytest.mark.integration
class TestIntelligentRecommendationIntegration:
    """Integration tests for the full recommendation workflow."""

    @pytest.mark.asyncio
    async def test_full_recommendation_workflow(self) -> None:
        """Test complete workflow from context building to recommendation generation."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        # Mock LLM response
        mock_llm_recommendation = LLMRecommendation(
            explanation=(
                "Having multiple Usenet servers configured provides redundancy "
                "and improves download reliability. If one server is down or missing "
                "articles, SABnzbd can automatically fall back to alternative servers."
            ),
            priority=Priority.HIGH,
            impact=(
                "Without multiple servers, you have a single point of failure. "
                "If your primary server goes down or doesn't have the articles you need, "
                "downloads will fail completely rather than falling back to alternatives."
            ),
            reasoning=(
                "Redundancy is a fundamental best practice in any distributed system. "
                "Different Usenet servers have different retention periods and article "
                "availability. Configuring multiple servers from different providers "
                "maximizes your chances of successful downloads."
            ),
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={
                    "setting": "servers",
                    "recommendation": "Configure at least 2-3 servers from different providers",
                    "priority": "high",
                },
                audit_history=[
                    {
                        "timestamp": "2025-10-01T10:00:00Z",
                        "recommendations": 5,
                        "applied": 2,
                    }
                ],
            )

            # Assert
            assert recommendation is not None
            assert recommendation.application == "sabnzbd"
            assert recommendation.setting == "servers"
            assert recommendation.priority == Priority.HIGH
            assert "redundancy" in recommendation.explanation.lower()
            assert "fail" in recommendation.impact.lower()
            assert len(recommendation.reasoning) > 50

    @pytest.mark.asyncio
    async def test_recommendation_with_web_search_context(self) -> None:
        """Test recommendation generation with web search findings included."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        web_search_data = {
            "query": "sabnzbd ssl verification best practices",
            "results": [
                {
                    "title": "SABnzbd Security Best Practices",
                    "snippet": "Always enable SSL verification to prevent man-in-the-middle attacks",  # noqa: E501
                    "url": "https://sabnzbd.org/wiki/advanced/ssl-certs",
                },
                {
                    "title": "Securing Your Usenet Downloads",
                    "snippet": "SSL verification is critical for secure downloads",
                    "url": "https://example.com/usenet-security",
                },
            ],
        }

        mock_llm_recommendation = LLMRecommendation(
            explanation=(
                "SSL verification prevents man-in-the-middle attacks by validating "
                "that you're connecting to the legitimate server. Without it, attackers "
                "could intercept and potentially modify your downloads."
            ),
            priority=Priority.HIGH,
            impact=(
                "Disabling SSL verification leaves your downloads vulnerable to "
                "interception and modification. Attackers on your network could "
                "inject malicious content or monitor your download activity."
            ),
            reasoning=(
                "SSL/TLS certificate verification is a fundamental security practice. "
                "While it might be tempting to disable it to avoid certificate errors, "
                "this completely undermines the security that SSL/TLS provides."
            ),
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"ssl_verify": False},
                best_practice_data={
                    "setting": "ssl_verify",
                    "recommendation": "true",
                    "priority": "high",
                },
                web_search_data=web_search_data,
            )

            # Assert
            assert recommendation is not None
            assert recommendation.priority == Priority.HIGH
            assert (
                "ssl" in recommendation.explanation.lower()
                or "security" in recommendation.explanation.lower()
            )
            assert recommendation.source_references is not None
            assert len(recommendation.source_references) > 0
            assert "sabnzbd.org" in recommendation.source_references[0]

    @pytest.mark.asyncio
    async def test_multiple_recommendations_batch_processing(self) -> None:
        """Test generating multiple recommendations efficiently in batch."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        configs_to_check = [
            {
                "name": "servers",
                "current": {"servers": 1},
                "best_practice": {
                    "setting": "servers",
                    "recommendation": "multiple servers",
                },
                "priority": Priority.HIGH,
            },
            {
                "name": "ssl_verify",
                "current": {"ssl_verify": False},
                "best_practice": {
                    "setting": "ssl_verify",
                    "recommendation": "true",
                },
                "priority": Priority.HIGH,
            },
            {
                "name": "article_cache",
                "current": {"article_cache": "100M"},
                "best_practice": {
                    "setting": "article_cache",
                    "recommendation": "500M or higher",
                },
                "priority": Priority.MEDIUM,
            },
        ]

        # Mock different LLM responses for each config
        def create_mock_llm_response(priority: Priority, setting: str) -> LLMRecommendation:
            return LLMRecommendation(
                explanation=f"This setting ({setting}) should be optimized for better performance",
                priority=priority,
                impact="Suboptimal configuration may lead to issues",
                reasoning=f"Best practices recommend optimizing {setting}",
            )

        mock_responses = [
            create_mock_llm_response(config["priority"], config["name"])
            for config in configs_to_check
        ]

        with patch.object(engine.llm_agent, "analyze_configuration", side_effect=mock_responses):
            # Act
            recommendations = []
            for config in configs_to_check:
                rec = await engine.generate_recommendation(
                    application="sabnzbd",
                    current_config=config["current"],
                    best_practice_data=config["best_practice"],
                )
                recommendations.append(rec)

            # Assert
            assert len(recommendations) == 3
            assert recommendations[0].priority == Priority.HIGH
            assert recommendations[1].priority == Priority.HIGH
            assert recommendations[2].priority == Priority.MEDIUM

            # Verify all have required fields
            for rec in recommendations:
                assert rec.explanation
                assert rec.impact
                assert rec.reasoning
                assert rec.priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]

    @pytest.mark.asyncio
    async def test_token_usage_tracking_across_requests(self) -> None:
        """Test that token usage is correctly tracked across multiple requests."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation="Test explanation",
            priority=Priority.MEDIUM,
            impact="Test impact",
            reasoning="Test reasoning",
        )

        # Simulate token usage for each request
        engine.llm_agent.token_tracker.record_usage(input_tokens=100, output_tokens=50)
        engine.llm_agent.token_tracker.record_usage(input_tokens=150, output_tokens=75)

        # Act
        stats = engine.get_token_usage_stats()
        cost = engine.estimate_costs()

        # Assert
        assert stats["total_input_tokens"] == 250
        assert stats["total_output_tokens"] == 125
        assert stats["total_requests"] == 2
        assert cost > 0

    @pytest.mark.asyncio
    async def test_priority_assessment_for_security_issue(self) -> None:
        """Test that security issues are correctly identified as HIGH priority."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation=(
                "Enabling authentication prevents unauthorized access to SABnzbd's "
                "web interface and API. Without it, anyone on your network can "
                "control your downloads, view history, and modify settings."
            ),
            priority=Priority.HIGH,
            impact=(
                "Critical security vulnerability. Unauthorized users could access "
                "sensitive information, modify downloads, or use SABnzbd as an "
                "attack vector into your network."
            ),
            reasoning=(
                "Authentication is a fundamental security control. The web interface "
                "provides full control over SABnzbd, making authentication essential "
                "for any network-accessible installation."
            ),
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"api_key": "", "username": "", "password": ""},
                best_practice_data={
                    "setting": "authentication",
                    "recommendation": "Configure API key and web interface password",
                    "priority": "high",
                },
            )

            # Assert
            assert recommendation.priority == Priority.HIGH
            assert (
                "security" in recommendation.explanation.lower()
                or "authentication" in recommendation.explanation.lower()
                or "unauthorized" in recommendation.explanation.lower()
            )
            assert (
                "critical" in recommendation.impact.lower()
                or "vulnerability" in recommendation.impact.lower()
            )

    @pytest.mark.asyncio
    async def test_priority_assessment_for_cosmetic_issue(self) -> None:
        """Test that cosmetic issues are correctly identified as LOW priority."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation=(
                "Enabling folder rename makes download organization slightly cleaner "
                "by standardizing folder names. This is purely an organizational preference "
                "with no functional impact."
            ),
            priority=Priority.LOW,
            impact=(
                "Minimal impact. Downloads will work perfectly fine without folder "
                "renaming. This only affects how folders are named in your file system."
            ),
            reasoning=(
                "This is a nice-to-have feature for organization but doesn't affect "
                "download success, security, or performance in any meaningful way."
            ),
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"folder_rename": False},
                best_practice_data={
                    "setting": "folder_rename",
                    "recommendation": "true",
                    "priority": "low",
                },
            )

            # Assert
            assert recommendation.priority == Priority.LOW
            assert (
                "minimal" in recommendation.impact.lower()
                or "organizational" in recommendation.explanation.lower()
                or "nice" in recommendation.reasoning.lower()
            )

    @pytest.mark.asyncio
    async def test_recommendation_with_audit_history_context(self) -> None:
        """Test that historical audit data provides useful context."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-integration-key")

        # Provide audit history showing this recommendation was previously ignored
        audit_history = [
            {
                "timestamp": "2025-09-01T10:00:00Z",
                "recommendations": 5,
                "applied": 3,
                "setting": "servers",
                "status": "ignored",
            },
            {
                "timestamp": "2025-10-01T10:00:00Z",
                "recommendations": 4,
                "applied": 2,
                "setting": "servers",
                "status": "ignored",
            },
        ]

        mock_llm_recommendation = LLMRecommendation(
            explanation=(
                "This recommendation appears in multiple audits but hasn't been applied. "
                "Multiple servers provide essential redundancy for reliable downloads."
            ),
            priority=Priority.HIGH,
            impact="Continued single point of failure risk",
            reasoning="Repeated recommendation indicates persistent suboptimal configuration",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={
                    "setting": "servers",
                    "recommendation": "multiple servers",
                },
                audit_history=audit_history,
            )

            # Assert
            assert recommendation is not None
            assert recommendation.priority == Priority.HIGH
            # The LLM should consider the audit history in its analysis
