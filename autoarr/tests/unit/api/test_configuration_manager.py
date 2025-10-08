"""
Tests for Configuration Manager service.

This module tests the configuration auditing, recommendation generation,
and configuration application functionality.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from autoarr.api.database import AuditResultsRepository, BestPractice, BestPracticesRepository
from autoarr.api.services.configuration_manager import ConfigurationManager
from autoarr.api.services.models import (
    ApplyRecommendationRequest,
    Priority,
    RecommendationType,
)
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator


@pytest.fixture
def mock_orchestrator() -> AsyncMock:
    """Create a mock MCP Orchestrator."""
    orchestrator = AsyncMock(spec=MCPOrchestrator)
    return orchestrator


@pytest.fixture
def mock_best_practices_repo() -> AsyncMock:
    """Create a mock Best Practices Repository."""
    repo = AsyncMock(spec=BestPracticesRepository)
    return repo


@pytest.fixture
def mock_audit_repo() -> AsyncMock:
    """Create a mock Audit Results Repository."""
    repo = AsyncMock(spec=AuditResultsRepository)
    return repo


@pytest.fixture
def config_manager(
    mock_orchestrator: AsyncMock,
    mock_best_practices_repo: AsyncMock,
    mock_audit_repo: AsyncMock,
) -> ConfigurationManager:
    """Create a Configuration Manager instance with mocked dependencies."""
    return ConfigurationManager(mock_orchestrator, mock_best_practices_repo, mock_audit_repo)


class TestConfigurationManagerInitialization:
    """Test Configuration Manager initialization."""

    def test_initialization_with_valid_dependencies(
        self,
        mock_orchestrator: AsyncMock,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test that Configuration Manager initializes correctly."""
        manager = ConfigurationManager(mock_orchestrator, mock_best_practices_repo, mock_audit_repo)

        assert manager.orchestrator == mock_orchestrator
        assert manager.best_practices_repo == mock_best_practices_repo
        assert manager.audit_repo == mock_audit_repo

    def test_supported_applications(self, config_manager: ConfigurationManager) -> None:
        """Test that supported applications are defined."""
        expected_apps = ["sabnzbd", "sonarr", "radarr", "plex"]
        assert config_manager.SUPPORTED_APPS == expected_apps

    def test_priority_weights_defined(self, config_manager: ConfigurationManager) -> None:
        """Test that priority weights are properly defined."""
        assert Priority.HIGH in config_manager.PRIORITY_WEIGHTS
        assert Priority.MEDIUM in config_manager.PRIORITY_WEIGHTS
        assert Priority.LOW in config_manager.PRIORITY_WEIGHTS


class TestFetchConfiguration:
    """Test configuration fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_configuration_success(
        self, config_manager: ConfigurationManager, mock_orchestrator: AsyncMock
    ) -> None:
        """Test successful configuration fetch."""
        expected_config = {"setting1": "value1", "setting2": "value2"}
        mock_orchestrator.call_tool.return_value = expected_config

        config = await config_manager.fetch_configuration("sabnzbd")

        assert config == expected_config
        mock_orchestrator.call_tool.assert_called_once_with(
            server="sabnzbd", tool="get_config", params={}
        )

    @pytest.mark.asyncio
    async def test_fetch_configuration_unsupported_application(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test fetch configuration with unsupported application."""
        with pytest.raises(ValueError, match="Unsupported application"):
            await config_manager.fetch_configuration("invalid_app")

    @pytest.mark.asyncio
    async def test_fetch_configuration_orchestrator_error(
        self, config_manager: ConfigurationManager, mock_orchestrator: AsyncMock
    ) -> None:
        """Test fetch configuration when orchestrator raises error."""
        mock_orchestrator.call_tool.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await config_manager.fetch_configuration("sabnzbd")


class TestCompareConfiguration:
    """Test configuration comparison functionality."""

    @pytest.mark.asyncio
    async def test_compare_configuration_with_matching_values(
        self, config_manager: ConfigurationManager, mock_best_practices_repo: AsyncMock
    ) -> None:
        """Test comparison when all values match best practices."""
        current_config = {
            "setting1": "recommended_value",
            "setting2": "recommended_value",
        }

        practice1 = Mock(spec=BestPractice)
        practice1.setting_name = "setting1"
        practice1.recommended_value = "recommended_value"
        practice1.priority = "high"
        practice1.category = "test"

        practice2 = Mock(spec=BestPractice)
        practice2.setting_name = "setting2"
        practice2.recommended_value = "recommended_value"
        practice2.priority = "medium"
        practice2.category = "test"

        mock_best_practices_repo.get_by_application.return_value = [practice1, practice2]

        recommendations = await config_manager.compare_configuration("sabnzbd", current_config)

        assert len(recommendations) == 0

    @pytest.mark.asyncio
    async def test_compare_configuration_with_incorrect_value(
        self, config_manager: ConfigurationManager, mock_best_practices_repo: AsyncMock
    ) -> None:
        """Test comparison when value doesn't match recommendation."""
        current_config = {"setting1": "wrong_value"}

        practice = Mock(spec=BestPractice)
        practice.setting_name = "setting1"
        practice.recommended_value = "correct_value"
        practice.priority = "high"
        practice.category = "test"
        practice.explanation = "Test explanation"
        practice.impact = "Test impact"
        practice.documentation_url = "https://example.com"

        mock_best_practices_repo.get_by_application.return_value = [practice]

        recommendations = await config_manager.compare_configuration("sabnzbd", current_config)

        assert len(recommendations) == 1
        assert recommendations[0].setting == "setting1"
        assert recommendations[0].current_value == "wrong_value"
        assert recommendations[0].recommended_value == "correct_value"
        assert recommendations[0].type == RecommendationType.INCORRECT_VALUE

    @pytest.mark.asyncio
    async def test_compare_configuration_with_missing_setting(
        self, config_manager: ConfigurationManager, mock_best_practices_repo: AsyncMock
    ) -> None:
        """Test comparison when setting is missing."""
        current_config = {}

        practice = Mock(spec=BestPractice)
        practice.setting_name = "missing_setting"
        practice.recommended_value = "value"
        practice.priority = "critical"
        practice.category = "test"
        practice.explanation = "Test explanation"
        practice.impact = "Test impact"
        practice.documentation_url = None

        mock_best_practices_repo.get_by_application.return_value = [practice]

        recommendations = await config_manager.compare_configuration("sabnzbd", current_config)

        assert len(recommendations) == 1
        assert recommendations[0].type == RecommendationType.MISSING_SETTING
        assert recommendations[0].current_value is None

    @pytest.mark.asyncio
    async def test_compare_configuration_priority_sorting(
        self, config_manager: ConfigurationManager, mock_best_practices_repo: AsyncMock
    ) -> None:
        """Test that recommendations are sorted by priority."""
        current_config = {}

        practice_low = Mock(spec=BestPractice)
        practice_low.setting_name = "low_priority"
        practice_low.recommended_value = "value"
        practice_low.priority = "low"
        practice_low.category = "test"
        practice_low.explanation = "Low"
        practice_low.impact = "Low impact"
        practice_low.documentation_url = None

        practice_high = Mock(spec=BestPractice)
        practice_high.setting_name = "high_priority"
        practice_high.recommended_value = "value"
        practice_high.priority = "high"
        practice_high.category = "test"
        practice_high.explanation = "High"
        practice_high.impact = "High impact"
        practice_high.documentation_url = None

        practice_medium = Mock(spec=BestPractice)
        practice_medium.setting_name = "medium_priority"
        practice_medium.recommended_value = "value"
        practice_medium.priority = "medium"
        practice_medium.category = "test"
        practice_medium.explanation = "Medium"
        practice_medium.impact = "Medium impact"
        practice_medium.documentation_url = None

        mock_best_practices_repo.get_by_application.return_value = [
            practice_low,
            practice_high,
            practice_medium,
        ]

        recommendations = await config_manager.compare_configuration("sabnzbd", current_config)

        assert len(recommendations) == 3
        assert recommendations[0].priority == Priority.HIGH
        assert recommendations[1].priority == Priority.MEDIUM
        assert recommendations[2].priority == Priority.LOW


class TestAuditApplication:
    """Test application auditing functionality."""

    @pytest.mark.asyncio
    async def test_audit_application_with_no_issues(
        self,
        config_manager: ConfigurationManager,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test audit when configuration has no issues."""
        config = {"setting1": "value1"}

        practice = Mock(spec=BestPractice)
        practice.setting_name = "setting1"
        practice.recommended_value = "value1"
        mock_best_practices_repo.get_by_application.return_value = [practice]

        audit = await config_manager.audit_application("sabnzbd", config=config)

        assert audit.application == "sabnzbd"
        assert audit.total_checks == 1
        assert audit.issues_found == 0
        assert audit.overall_health_score == 100.0
        mock_audit_repo.save_audit_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_application_with_issues(
        self,
        config_manager: ConfigurationManager,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test audit when configuration has issues."""
        config = {}

        practice_high = Mock(spec=BestPractice)
        practice_high.setting_name = "critical_setting"
        practice_high.recommended_value = "value"
        practice_high.priority = "high"
        practice_high.category = "test"
        practice_high.explanation = "Critical"
        practice_high.impact = "High impact"
        practice_high.documentation_url = None

        practice_medium = Mock(spec=BestPractice)
        practice_medium.setting_name = "important_setting"
        practice_medium.recommended_value = "value"
        practice_medium.priority = "medium"
        practice_medium.category = "test"
        practice_medium.explanation = "Important"
        practice_medium.impact = "Medium impact"
        practice_medium.documentation_url = None

        mock_best_practices_repo.get_by_application.return_value = [
            practice_high,
            practice_medium,
        ]

        audit = await config_manager.audit_application("sabnzbd", config=config)

        assert audit.application == "sabnzbd"
        assert audit.total_checks == 2
        assert audit.issues_found == 2
        assert audit.high_priority_count == 1
        assert audit.medium_priority_count == 1
        assert audit.low_priority_count == 0
        assert audit.overall_health_score < 100.0

    @pytest.mark.asyncio
    async def test_audit_application_health_score_calculation(
        self,
        config_manager: ConfigurationManager,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test health score calculation."""
        config = {}

        practice = Mock(spec=BestPractice)
        practice.setting_name = "setting"
        practice.recommended_value = "value"
        practice.priority = "high"
        practice.category = "test"
        practice.explanation = "Test"
        practice.impact = "Impact"
        practice.documentation_url = None

        mock_best_practices_repo.get_by_application.return_value = [practice]

        audit = await config_manager.audit_application("sabnzbd", config=config)

        # High priority = -10 points, so score should be 90
        assert audit.overall_health_score == 90.0

    @pytest.mark.asyncio
    async def test_audit_application_saves_to_database(
        self,
        config_manager: ConfigurationManager,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test that audit results are saved to database."""
        config = {"setting": "value"}
        mock_best_practices_repo.get_by_application.return_value = []

        await config_manager.audit_application("sabnzbd", config=config)

        mock_audit_repo.save_audit_result.assert_called_once()
        call_kwargs = mock_audit_repo.save_audit_result.call_args.kwargs
        assert call_kwargs["application"] == "sabnzbd"
        assert call_kwargs["total_checks"] == 0
        assert call_kwargs["issues_found"] == 0


class TestCalculateHealthScore:
    """Test health score calculation."""

    def test_calculate_health_score_perfect(self, config_manager: ConfigurationManager) -> None:
        """Test health score calculation with no issues."""
        score = config_manager._calculate_health_score(10, [])
        assert score == 100.0

    def test_calculate_health_score_with_high_priority(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test health score calculation with high priority issues."""
        from autoarr.api.services.models import Recommendation, Priority, RecommendationType

        recommendations = [
            Recommendation(
                setting="test",
                current_value=None,
                recommended_value="value",
                priority=Priority.HIGH,
                type=RecommendationType.MISSING_SETTING,
                description="Test",
                reasoning="Test",
                impact="Test",
                category="test",
            )
        ]

        score = config_manager._calculate_health_score(10, recommendations)
        assert score == 90.0  # 100 - 10 (high priority weight)

    def test_calculate_health_score_minimum_zero(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test that health score doesn't go below zero."""
        from autoarr.api.services.models import Recommendation, Priority, RecommendationType

        # Create 15 high priority issues (15 * 10 = 150 points)
        recommendations = [
            Recommendation(
                setting=f"test{i}",
                current_value=None,
                recommended_value="value",
                priority=Priority.HIGH,
                type=RecommendationType.MISSING_SETTING,
                description="Test",
                reasoning="Test",
                impact="Test",
                category="test",
            )
            for i in range(15)
        ]

        score = config_manager._calculate_health_score(20, recommendations)
        assert score == 0.0


class TestApplyRecommendation:
    """Test configuration application functionality."""

    @pytest.mark.asyncio
    async def test_apply_recommendation_dry_run(self, config_manager: ConfigurationManager) -> None:
        """Test applying recommendation in dry-run mode."""
        request = ApplyRecommendationRequest(
            application="sabnzbd", setting="test_setting", value="test_value", dry_run=True
        )

        response = await config_manager.apply_recommendation(request)

        assert response.success is True
        assert response.dry_run is True
        assert response.setting == "test_setting"
        assert "Dry run" in response.message

    @pytest.mark.asyncio
    async def test_apply_recommendation_unsupported_application(
        self, config_manager: ConfigurationManager
    ) -> None:
        """Test applying recommendation to unsupported application."""
        request = ApplyRecommendationRequest(
            application="invalid", setting="test", value="value", dry_run=False
        )

        response = await config_manager.apply_recommendation(request)

        assert response.success is False
        assert "Unsupported application" in response.message

    @pytest.mark.asyncio
    async def test_apply_recommendation_success(
        self, config_manager: ConfigurationManager, mock_orchestrator: AsyncMock
    ) -> None:
        """Test successful recommendation application."""
        request = ApplyRecommendationRequest(
            application="sabnzbd", setting="test_setting", value="new_value", dry_run=False
        )

        mock_orchestrator.call_tool.return_value = {"success": True}

        response = await config_manager.apply_recommendation(request)

        assert response.success is True
        assert response.dry_run is False
        assert response.new_value == "new_value"
        mock_orchestrator.call_tool.assert_called_once_with(
            server="sabnzbd",
            tool="set_config",
            params={"setting": "test_setting", "value": "new_value"},
        )

    @pytest.mark.asyncio
    async def test_apply_recommendation_orchestrator_error(
        self, config_manager: ConfigurationManager, mock_orchestrator: AsyncMock
    ) -> None:
        """Test applying recommendation when orchestrator fails."""
        request = ApplyRecommendationRequest(
            application="sabnzbd", setting="test", value="value", dry_run=False
        )

        mock_orchestrator.call_tool.side_effect = Exception("Connection failed")

        response = await config_manager.apply_recommendation(request)

        assert response.success is False
        assert "Failed to apply" in response.message


class TestGetAuditHistory:
    """Test audit history retrieval."""

    @pytest.mark.asyncio
    async def test_get_audit_history_success(
        self, config_manager: ConfigurationManager, mock_audit_repo: AsyncMock
    ) -> None:
        """Test successful audit history retrieval."""
        mock_result = Mock()
        mock_result.application = "sabnzbd"
        mock_result.timestamp = datetime.utcnow()
        mock_result.total_checks = 10
        mock_result.issues_found = 3
        mock_result.high_priority = 1
        mock_result.medium_priority = 2
        mock_result.low_priority = 0

        mock_audit_repo.get_audit_history.return_value = [mock_result]

        summaries = await config_manager.get_audit_history("sabnzbd", limit=10)

        assert len(summaries) == 1
        assert summaries[0].application == "sabnzbd"
        assert summaries[0].issues_found == 3
        mock_audit_repo.get_audit_history.assert_called_once_with("sabnzbd", 10)

    @pytest.mark.asyncio
    async def test_get_audit_history_empty(
        self, config_manager: ConfigurationManager, mock_audit_repo: AsyncMock
    ) -> None:
        """Test audit history retrieval with no results."""
        mock_audit_repo.get_audit_history.return_value = []

        summaries = await config_manager.get_audit_history("sabnzbd")

        assert len(summaries) == 0


class TestAuditAllApplications:
    """Test auditing all applications."""

    @pytest.mark.asyncio
    async def test_audit_all_applications_success(
        self,
        config_manager: ConfigurationManager,
        mock_orchestrator: AsyncMock,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test successful audit of all applications."""
        mock_orchestrator.call_tool.return_value = {"setting": "value"}
        mock_best_practices_repo.get_by_application.return_value = []

        results = await config_manager.audit_all_applications()

        assert len(results) == 4  # sabnzbd, sonarr, radarr, plex
        assert "sabnzbd" in results
        assert "sonarr" in results
        assert "radarr" in results
        assert "plex" in results

    @pytest.mark.asyncio
    async def test_audit_all_applications_partial_failure(
        self,
        config_manager: ConfigurationManager,
        mock_orchestrator: AsyncMock,
        mock_best_practices_repo: AsyncMock,
        mock_audit_repo: AsyncMock,
    ) -> None:
        """Test audit of all applications when some fail."""

        # Make sonarr fail
        async def mock_call_tool(server, tool, params):
            if server == "sonarr":
                raise Exception("Connection failed")
            return {"setting": "value"}

        mock_orchestrator.call_tool.side_effect = mock_call_tool
        mock_best_practices_repo.get_by_application.return_value = []

        results = await config_manager.audit_all_applications()

        # Should continue despite sonarr failure
        assert len(results) == 3  # sabnzbd, radarr, plex
        assert "sabnzbd" in results
        assert "sonarr" not in results
        assert "radarr" in results
        assert "plex" in results
