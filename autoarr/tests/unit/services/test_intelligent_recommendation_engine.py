"""
Unit tests for Intelligent Recommendation Engine.

This module tests the recommendation engine's ability to aggregate context,
assess priorities using LLM, and generate detailed explanations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from autoarr.api.services.intelligent_recommendation_engine import (
    ContextBuilder, IntelligentRecommendationEngine, PriorityAssessor,
    RecommendationContext)
from autoarr.api.services.llm_agent import LLMRecommendation
from autoarr.api.services.models import Priority


class TestContextBuilder:
    """Tests for context building functionality."""

    @pytest.mark.asyncio
    async def test_build_context_aggregates_configuration(self) -> None:
        """Test that context builder aggregates current configuration."""
        # Arrange
        builder = ContextBuilder()
        mock_config = {"servers": 1, "incomplete_dir": "/downloads/incomplete"}

        # Act
        context = await builder.build_context(
            application="sabnzbd",
            current_config=mock_config,
            best_practice_data=None,
            audit_history=None,
        )

        # Assert
        assert context.application == "sabnzbd"
        assert context.current_config == mock_config
        assert context.current_config["servers"] == 1

    @pytest.mark.asyncio
    async def test_build_context_includes_best_practices(self) -> None:
        """Test that context includes best practices data."""
        # Arrange
        builder = ContextBuilder()
        best_practice = {
            "setting": "servers",
            "recommendation": "Use multiple servers for redundancy",
            "priority": "high",
        }

        # Act
        context = await builder.build_context(
            application="sabnzbd",
            current_config={"servers": 1},
            best_practice_data=best_practice,
            audit_history=None,
        )

        # Assert
        assert context.best_practice_data is not None
        assert context.best_practice_data["setting"] == "servers"
        assert "redundancy" in context.best_practice_data["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_build_context_includes_audit_history(self) -> None:
        """Test that context includes historical audit data."""
        # Arrange
        builder = ContextBuilder()
        audit_history = [
            {
                "timestamp": "2025-10-01T10:00:00Z",
                "recommendations": 5,
                "applied": 2,
            },
            {
                "timestamp": "2025-10-07T10:00:00Z",
                "recommendations": 3,
                "applied": 1,
            },
        ]

        # Act
        context = await builder.build_context(
            application="sabnzbd",
            current_config={"servers": 1},
            best_practice_data=None,
            audit_history=audit_history,
        )

        # Assert
        assert context.audit_history is not None
        assert len(context.audit_history) == 2
        assert context.audit_history[0]["recommendations"] == 5

    @pytest.mark.asyncio
    async def test_build_context_includes_web_search_data(self) -> None:
        """Test that context includes web search findings."""
        # Arrange
        builder = ContextBuilder()
        web_search_data = {
            "query": "sabnzbd best practices servers",
            "results": [
                {
                    "title": "SABnzbd Server Configuration",
                    "snippet": "Configure multiple servers for better reliability",
                    "url": "https://sabnzbd.org/wiki/configuration/servers",
                }
            ],
        }

        # Act
        context = await builder.build_context(
            application="sabnzbd",
            current_config={"servers": 1},
            best_practice_data=None,
            audit_history=None,
            web_search_data=web_search_data,
        )

        # Assert
        assert context.web_search_data is not None
        assert len(context.web_search_data["results"]) == 1
        assert "reliability" in context.web_search_data["results"][0]["snippet"].lower()

    @pytest.mark.asyncio
    async def test_context_has_timestamp(self) -> None:
        """Test that built context includes timestamp."""
        # Arrange
        builder = ContextBuilder()

        # Act
        context = await builder.build_context(
            application="sabnzbd",
            current_config={"servers": 1},
        )

        # Assert
        assert context.timestamp is not None
        assert isinstance(context.timestamp, datetime)


class TestPriorityAssessor:
    """Tests for LLM-based priority assessment."""

    @pytest.mark.asyncio
    async def test_assess_priority_uses_llm_for_analysis(self) -> None:
        """Test that priority assessor uses LLM to determine priority."""
        # Arrange
        mock_llm_agent = AsyncMock()
        mock_recommendation = LLMRecommendation(
            explanation="Multiple servers provide redundancy and prevent downtime",
            priority=Priority.HIGH,
            impact="Single server failure will stop all downloads",
            reasoning="Redundancy is critical for continuous operation",
        )
        mock_llm_agent.analyze_configuration.return_value = mock_recommendation

        assessor = PriorityAssessor(llm_agent=mock_llm_agent)
        context = RecommendationContext(
            application="sabnzbd",
            current_config={"servers": 1},
            best_practice_data={"servers": "multiple for redundancy"},
            timestamp=datetime.utcnow(),
        )

        # Act
        priority = await assessor.assess_priority(context)

        # Assert
        assert priority == Priority.HIGH
        mock_llm_agent.analyze_configuration.assert_called_once()

    @pytest.mark.asyncio
    async def test_assess_priority_considers_security_issues(self) -> None:
        """Test that security issues are prioritized as HIGH."""
        # Arrange
        mock_llm_agent = AsyncMock()
        mock_recommendation = LLMRecommendation(
            explanation="SSL verification should always be enabled for security",
            priority=Priority.HIGH,
            impact="Without SSL verification, connections are vulnerable to MITM attacks",
            reasoning="Security vulnerabilities pose immediate risk",
        )
        mock_llm_agent.analyze_configuration.return_value = mock_recommendation

        assessor = PriorityAssessor(llm_agent=mock_llm_agent)
        context = RecommendationContext(
            application="sabnzbd",
            current_config={"ssl_verify": False},
            best_practice_data={"ssl_verify": True},
            timestamp=datetime.utcnow(),
        )

        # Act
        priority = await assessor.assess_priority(context)

        # Assert
        assert priority == Priority.HIGH

    @pytest.mark.asyncio
    async def test_assess_priority_handles_performance_issues(self) -> None:
        """Test that performance issues are typically MEDIUM priority."""
        # Arrange
        mock_llm_agent = AsyncMock()
        mock_recommendation = LLMRecommendation(
            explanation="Increasing cache size improves download performance",
            priority=Priority.MEDIUM,
            impact="Slower downloads and more disk I/O",
            reasoning="Performance can be improved but system still functions",
        )
        mock_llm_agent.analyze_configuration.return_value = mock_recommendation

        assessor = PriorityAssessor(llm_agent=mock_llm_agent)
        context = RecommendationContext(
            application="sabnzbd",
            current_config={"article_cache": "100M"},
            best_practice_data={"article_cache": "500M"},
            timestamp=datetime.utcnow(),
        )

        # Act
        priority = await assessor.assess_priority(context)

        # Assert
        assert priority == Priority.MEDIUM

    @pytest.mark.asyncio
    async def test_assess_priority_handles_low_priority_cosmetic(self) -> None:
        """Test that cosmetic/nice-to-have issues are LOW priority."""
        # Arrange
        mock_llm_agent = AsyncMock()
        mock_recommendation = LLMRecommendation(
            explanation="Setting a custom download folder name is purely organizational",
            priority=Priority.LOW,
            impact="Minimal impact, just organizational preference",
            reasoning="Nice-to-have improvement with no functional impact",
        )
        mock_llm_agent.analyze_configuration.return_value = mock_recommendation

        assessor = PriorityAssessor(llm_agent=mock_llm_agent)
        context = RecommendationContext(
            application="sabnzbd",
            current_config={"folder_rename": False},
            best_practice_data={"folder_rename": True},
            timestamp=datetime.utcnow(),
        )

        # Act
        priority = await assessor.assess_priority(context)

        # Assert
        assert priority == Priority.LOW


class TestIntelligentRecommendationEngine:
    """Tests for the main Intelligent Recommendation Engine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self) -> None:
        """Test that engine initializes with required dependencies."""
        # Arrange & Act
        engine = IntelligentRecommendationEngine(api_key="test-key")

        # Assert
        assert engine.context_builder is not None
        assert engine.priority_assessor is not None
        assert engine.llm_agent is not None

    @pytest.mark.asyncio
    async def test_generate_recommendation_builds_context(self) -> None:
        """Test that recommendation generation builds comprehensive context."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation="Test explanation",
            priority=Priority.MEDIUM,
            impact="Test impact",
            reasoning="Test reasoning",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={"servers": "multiple"},
            )

            # Assert
            assert recommendation is not None
            assert recommendation.application == "sabnzbd"

    @pytest.mark.asyncio
    async def test_generate_recommendation_includes_llm_explanation(self) -> None:
        """Test that generated recommendation includes LLM explanation."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation="Multiple servers provide redundancy and improve reliability",
            priority=Priority.HIGH,
            impact="Single point of failure without redundancy",
            reasoning="Redundancy is essential for continuous operation",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={"servers": "multiple for redundancy"},
            )

            # Assert
            assert "redundancy" in recommendation.explanation.lower()
            assert "reliability" in recommendation.explanation.lower()

    @pytest.mark.asyncio
    async def test_generate_recommendation_includes_impact_analysis(self) -> None:
        """Test that recommendation includes 'what happens if not fixed' analysis."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation="SSL verification prevents MITM attacks",
            priority=Priority.HIGH,
            impact="Without SSL, attackers can intercept and modify downloads",
            reasoning="Security is paramount",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"ssl_verify": False},
                best_practice_data={"ssl_verify": True},
            )

            # Assert
            assert recommendation.impact is not None
            assert (
                "intercept" in recommendation.impact.lower()
                or "attack" in recommendation.impact.lower()
            )

    @pytest.mark.asyncio
    async def test_generate_recommendation_includes_implementation_steps(self) -> None:
        """Test that recommendation includes how to implement the change."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation="Multiple servers improve reliability",
            priority=Priority.HIGH,
            impact="Single point of failure",
            reasoning="Redundancy is important",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={"servers": "multiple"},
            )

            # Assert
            assert recommendation.reasoning is not None
            assert len(recommendation.reasoning) > 0

    @pytest.mark.asyncio
    async def test_generate_recommendation_handles_web_search_integration(self) -> None:
        """Test that engine can incorporate web search findings."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        web_search_data = {
            "query": "sabnzbd servers best practices",
            "results": [
                {
                    "title": "SABnzbd Configuration",
                    "snippet": "Use multiple servers from different providers",
                    "url": "https://sabnzbd.org/wiki",
                }
            ],
        }

        mock_llm_recommendation = LLMRecommendation(
            explanation="Multiple servers from different providers ensure reliability",
            priority=Priority.HIGH,
            impact="Limited reliability with single server",
            reasoning="Diversification prevents single provider issues",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={"servers": "multiple"},
                web_search_data=web_search_data,
            )

            # Assert
            assert recommendation is not None
            # Recommendation should consider web search findings

    @pytest.mark.asyncio
    async def test_generate_multiple_recommendations_efficiently(self) -> None:
        """Test that engine can generate multiple recommendations efficiently."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        configurations = [
            {"setting": "servers", "current": 1, "best_practice": "multiple"},
            {"setting": "ssl_verify", "current": False, "best_practice": True},
            {"setting": "article_cache", "current": "100M", "best_practice": "500M"},
        ]

        mock_llm_recommendation = LLMRecommendation(
            explanation="Test explanation",
            priority=Priority.MEDIUM,
            impact="Test impact",
            reasoning="Test reasoning",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            recommendations = []
            for config in configurations:
                rec = await engine.generate_recommendation(
                    application="sabnzbd",
                    current_config={config["setting"]: config["current"]},
                    best_practice_data={config["setting"]: config["best_practice"]},
                )
                recommendations.append(rec)

            # Assert
            assert len(recommendations) == 3
            assert all(
                rec.priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
                for rec in recommendations
            )

    @pytest.mark.asyncio
    async def test_performance_within_acceptable_limits(self) -> None:
        """Test that recommendation generation completes within 5 seconds."""
        # Arrange
        import time

        engine = IntelligentRecommendationEngine(api_key="test-key")

        mock_llm_recommendation = LLMRecommendation(
            explanation="Test explanation",
            priority=Priority.MEDIUM,
            impact="Test impact",
            reasoning="Test reasoning",
        )

        with patch.object(
            engine.llm_agent, "analyze_configuration", return_value=mock_llm_recommendation
        ):
            # Act
            start_time = time.time()
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config={"servers": 1},
                best_practice_data={"servers": "multiple"},
            )
            elapsed_time = time.time() - start_time

            # Assert
            assert recommendation is not None
            assert elapsed_time < 5.0, f"Recommendation took {elapsed_time}s, should be < 5s"

    @pytest.mark.asyncio
    async def test_get_token_usage_stats(self) -> None:
        """Test that engine exposes LLM token usage statistics."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        # Act
        stats = engine.get_token_usage_stats()

        # Assert
        assert "total_input_tokens" in stats
        assert "total_output_tokens" in stats
        assert "total_requests" in stats
        assert "total_tokens" in stats

    @pytest.mark.asyncio
    async def test_estimate_costs(self) -> None:
        """Test that engine can estimate LLM costs."""
        # Arrange
        engine = IntelligentRecommendationEngine(api_key="test-key")

        # Simulate some token usage
        engine.llm_agent.token_tracker.record_usage(input_tokens=1000, output_tokens=500)

        # Act
        cost = engine.estimate_costs()

        # Assert
        assert cost > 0
        assert isinstance(cost, (int, float))
