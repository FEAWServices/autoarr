"""
Unit tests for Configuration Manager service.

This module tests the Configuration Manager's ability to:
- Fetch configurations from MCP servers
- Compare configurations against best practices
- Generate prioritized recommendations
- Track audit history
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from autoarr.api.database import (
    AuditResultsRepository,
    BestPractice,
    BestPracticesRepository,
    Database,
)
from autoarr.api.services.configuration_manager import ConfigurationManager
from autoarr.api.services.models import (
    ApplyRecommendationRequest,
    Priority,
    RecommendationType,
)
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator


@pytest.fixture
def mock_database():
    """Create a mock database."""
    db = Mock(spec=Database)
    db.session = AsyncMock()
    return db


@pytest.fixture
def mock_best_practices_repo():
    """Create a mock best practices repository."""
    repo = Mock(spec=BestPracticesRepository)
    return repo


@pytest.fixture
def mock_audit_repo():
    """Create a mock audit results repository."""
    repo = Mock(spec=AuditResultsRepository)
    return repo


@pytest.fixture
def mock_orchestrator():
    """Create a mock MCP orchestrator."""
    orchestrator = Mock(spec=MCPOrchestrator)
    orchestrator.call_tool = AsyncMock()
    orchestrator.is_connected = AsyncMock(return_value=True)
    return orchestrator


@pytest.fixture
def configuration_manager(mock_orchestrator, mock_best_practices_repo, mock_audit_repo):
    """Create a Configuration Manager instance with mocked dependencies."""
    manager = ConfigurationManager(
        orchestrator=mock_orchestrator,
        best_practices_repo=mock_best_practices_repo,
        audit_repo=mock_audit_repo,
    )
    return manager


def create_best_practice(
    practice_id: int,
    application: str,
    category: str,
    setting_name: str,
    recommended_value: str,
    priority: str,
    explanation: str,
    impact: str,
    documentation_url: str = None,
) -> BestPractice:
    """Helper function to create BestPractice objects with correct schema."""
    return BestPractice(
        id=practice_id,
        application=application,
        category=category,
        setting_name=setting_name,
        setting_path=f"{category}.{setting_name}",
        recommended_value=recommended_value,
        current_check_type="not_empty",
        explanation=explanation,
        priority=priority,
        impact=impact,
        documentation_url=documentation_url,
        version_added="1.0.0",
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ============================================================================
# Tests for Fetching Configurations
# ============================================================================


@pytest.mark.asyncio
async def test_fetch_configuration_sabnzbd_success(configuration_manager, mock_orchestrator):
    """Test fetching configuration from SABnzbd."""
    # Arrange
    mock_config = {
        "download_dir": "/downloads/complete",
        "incomplete_dir": "/downloads/incomplete",
        "download_free": "10G",
        "refresh_rate": 0,
        "queue_complete": "",
    }
    mock_orchestrator.call_tool.return_value = mock_config

    # Act
    config = await configuration_manager.fetch_configuration("sabnzbd")

    # Assert
    assert config == mock_config
    mock_orchestrator.call_tool.assert_called_once_with(
        server="sabnzbd", tool="get_config", params={}
    )


@pytest.mark.asyncio
async def test_fetch_configuration_sonarr_success(configuration_manager, mock_orchestrator):
    """Test fetching configuration from Sonarr."""
    # Arrange
    mock_config = {
        "enableCompletedDownloadHandling": True,
        "autoRedownloadFailed": False,
        "removeFailedDownloads": True,
    }
    mock_orchestrator.call_tool.return_value = mock_config

    # Act
    config = await configuration_manager.fetch_configuration("sonarr")

    # Assert
    assert config == mock_config
    mock_orchestrator.call_tool.assert_called_once_with(
        server="sonarr", tool="get_config", params={}
    )


@pytest.mark.asyncio
async def test_fetch_configuration_invalid_application(configuration_manager):
    """Test fetching configuration with invalid application name."""
    # Act & Assert
    with pytest.raises(ValueError, match="Unsupported application"):
        await configuration_manager.fetch_configuration("invalid_app")


@pytest.mark.asyncio
async def test_fetch_configuration_connection_error(configuration_manager, mock_orchestrator):
    """Test handling connection errors when fetching configuration."""
    # Arrange
    mock_orchestrator.call_tool.side_effect = Exception("Connection failed")

    # Act & Assert
    with pytest.raises(Exception, match="Connection failed"):
        await configuration_manager.fetch_configuration("sabnzbd")


# ============================================================================
# Tests for Configuration Comparison
# ============================================================================


@pytest.mark.asyncio
async def test_compare_configuration_identifies_missing_setting(
    configuration_manager, mock_best_practices_repo
):
    """Test that comparison identifies missing required settings."""
    # Arrange
    current_config = {"download_dir": "/downloads"}
    best_practice = create_best_practice(
        practice_id=1,
        application="sabnzbd",
        category="downloads",
        setting_name="incomplete_dir",
        recommended_value="/downloads/incomplete",
        priority="high",
        explanation="Use separate incomplete directory to prevent corruption",
        impact="Risk of corrupted files being processed",
        documentation_url="https://sabnzbd.org/wiki/configuration/folders",
    )
    mock_best_practices_repo.get_by_application.return_value = [best_practice]

    # Act
    recommendations = await configuration_manager.compare_configuration("sabnzbd", current_config)

    # Assert
    assert len(recommendations) > 0
    assert any(r.setting == "incomplete_dir" for r in recommendations)
    assert any(r.type == RecommendationType.MISSING_SETTING for r in recommendations)


@pytest.mark.asyncio
async def test_compare_configuration_identifies_incorrect_value(
    configuration_manager, mock_best_practices_repo
):
    """Test that comparison identifies incorrect configuration values."""
    # Arrange
    current_config = {"refresh_rate": 0, "download_dir": "/downloads"}
    best_practice = BestPractice(
        id=2,
        application="sabnzbd",
        category="performance",
        setting_name="refresh_rate",
        setting_path="config.refresh_rate",
        current_check_type="not_empty",
        recommended_value="2",
        priority="medium",
        explanation="Set appropriate refresh rate",
        impact="Excessive server requests, potential rate limiting",
        documentation_url="https://sabnzbd.org/wiki/configuration/general",
        version_added="1.0.0",
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_best_practices_repo.get_by_application.return_value = [best_practice]

    # Act
    recommendations = await configuration_manager.compare_configuration("sabnzbd", current_config)

    # Assert
    assert len(recommendations) > 0
    refresh_rec = next((r for r in recommendations if r.setting == "refresh_rate"), None)
    assert refresh_rec is not None
    assert refresh_rec.current_value == 0
    assert refresh_rec.recommended_value == "2"


@pytest.mark.asyncio
async def test_compare_configuration_no_issues_found(
    configuration_manager, mock_best_practices_repo
):
    """Test comparison when configuration matches best practices."""
    # Arrange
    current_config = {
        "incomplete_dir": "/downloads/incomplete",
        "refresh_rate": 2,
    }
    best_practices = [
        BestPractice(
            id=2,
            application="sabnzbd",
            category="performance",
            setting_name="refresh_rate",
            setting_path="config.refresh_rate",
            current_check_type="not_empty",
            recommended_value="2",
            priority="medium",
            explanation="Set appropriate refresh rate",
            impact="Excessive requests",
            documentation_url=None,
            version_added="1.0.0",
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
    ]
    mock_best_practices_repo.get_by_application.return_value = best_practices

    # Act
    recommendations = await configuration_manager.compare_configuration("sabnzbd", current_config)

    # Assert
    assert len(recommendations) == 0


# ============================================================================
# Tests for Audit Application
# ============================================================================


@pytest.mark.asyncio
async def test_audit_identifies_non_optimal_settings(
    configuration_manager, mock_orchestrator, mock_best_practices_repo, mock_audit_repo
):
    """Test that audit identifies non-optimal settings (from BUILD-PLAN.md)."""
    # Arrange
    mock_config = {"download_dir": "/downloads", "incomplete_dir": ""}
    mock_orchestrator.call_tool.return_value = mock_config

    best_practice = BestPractice(
        id=1,
        application="sabnzbd",
        category="downloads",
        setting_name="incomplete_dir",
        setting_path="config.incomplete_dir",
        current_check_type="not_empty",
        recommended_value="/downloads/incomplete",
        priority="high",
        explanation="Use separate incomplete directory",
        impact="Risk of corrupted files being processed",
        documentation_url=None,
        version_added="1.0.0",
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_best_practices_repo.get_by_application.return_value = [best_practice]
    mock_audit_repo.save_audit_result.return_value = Mock()

    # Act
    audit = await configuration_manager.audit_application("sabnzbd", mock_config)

    # Assert
    assert len(audit.recommendations) > 0
    assert any("incomplete_dir" in r.setting for r in audit.recommendations)
    assert audit.issues_found > 0


@pytest.mark.asyncio
async def test_audit_calculates_health_score(
    configuration_manager, mock_orchestrator, mock_best_practices_repo, mock_audit_repo
):
    """Test that audit calculates overall health score."""
    # Arrange
    mock_config = {
        "download_dir": "/downloads",
        "incomplete_dir": "",
        "refresh_rate": 0,
    }
    mock_orchestrator.call_tool.return_value = mock_config

    best_practices = [
        BestPractice(
            id=2,
            application="sabnzbd",
            category="performance",
            setting_name="refresh_rate",
            setting_path="config.refresh_rate",
            current_check_type="not_empty",
            recommended_value="2",
            priority="medium",
            explanation="Set refresh rate",
            impact="Excessive requests",
            documentation_url=None,
            version_added="1.0.0",
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
    ]
    mock_best_practices_repo.get_by_application.return_value = best_practices
    mock_audit_repo.save_audit_result.return_value = Mock()

    # Act
    audit = await configuration_manager.audit_application("sabnzbd", mock_config)

    # Assert
    assert 0 <= audit.overall_health_score <= 100
    # With 2 issues out of 2 checks, score should be less than 100
    assert audit.overall_health_score < 100


@pytest.mark.asyncio
async def test_audit_categorizes_priorities(
    configuration_manager, mock_orchestrator, mock_best_practices_repo, mock_audit_repo
):
    """Test that audit correctly categorizes recommendation priorities."""
    # Arrange
    mock_config = {
        "download_dir": "/downloads",
        "incomplete_dir": "",
        "refresh_rate": 0,
        "queue_complete": "",
    }
    mock_orchestrator.call_tool.return_value = mock_config

    best_practices = [
        create_best_practice(
            practice_id=1,
            application="sabnzbd",
            category="downloads",
            setting_name="incomplete_dir",
            recommended_value="/downloads/incomplete",
            priority="high",
            explanation="Use separate incomplete directory",
            impact="Data corruption risk",
        ),
        create_best_practice(
            practice_id=2,
            application="sabnzbd",
            category="performance",
            setting_name="refresh_rate",
            recommended_value="2",
            priority="medium",
            explanation="Set refresh rate",
            impact="Higher server load",
        ),
        create_best_practice(
            practice_id=3,
            application="sabnzbd",
            category="notifications",
            setting_name="queue_complete",
            recommended_value="script",
            priority="low",
            explanation="Set completion notification",
            impact="No notifications",
        ),
    ]
    mock_best_practices_repo.get_by_application.return_value = best_practices
    mock_audit_repo.save_audit_result.return_value = Mock()

    # Act
    audit = await configuration_manager.audit_application("sabnzbd", mock_config)

    # Assert
    assert audit.high_priority_count >= 1
    assert audit.medium_priority_count >= 1
    assert audit.low_priority_count >= 1


@pytest.mark.asyncio
async def test_audit_saves_results_to_database(
    configuration_manager, mock_orchestrator, mock_best_practices_repo, mock_audit_repo
):
    """Test that audit saves results to the database."""
    # Arrange
    mock_config = {"download_dir": "/downloads"}
    mock_orchestrator.call_tool.return_value = mock_config
    mock_best_practices_repo.get_by_application.return_value = []
    mock_audit_repo.save_audit_result.return_value = Mock()

    # Act
    await configuration_manager.audit_application("sabnzbd", mock_config)

    # Assert
    mock_audit_repo.save_audit_result.assert_called_once()
    call_args = mock_audit_repo.save_audit_result.call_args
    assert call_args[1]["application"] == "sabnzbd"
    assert call_args[1]["total_checks"] >= 0
    assert "configuration_snapshot" in call_args[1]
    assert "recommendations" in call_args[1]


@pytest.mark.asyncio
async def test_audit_all_applications(
    configuration_manager, mock_orchestrator, mock_best_practices_repo, mock_audit_repo
):
    """Test auditing all applications."""
    # Arrange
    mock_orchestrator.call_tool.return_value = {"test": "config"}
    mock_best_practices_repo.get_by_application.return_value = []
    mock_audit_repo.save_audit_result.return_value = Mock()

    # Act
    results = await configuration_manager.audit_all_applications()

    # Assert
    assert len(results) == 4  # sabnzbd, sonarr, radarr, plex
    assert "sabnzbd" in results
    assert "sonarr" in results
    assert "radarr" in results
    assert "plex" in results


# ============================================================================
# Tests for Applying Recommendations
# ============================================================================


@pytest.mark.asyncio
async def test_apply_recommendation_dry_run(configuration_manager, mock_orchestrator):
    """Test applying a recommendation in dry-run mode."""
    # Arrange
    request = ApplyRecommendationRequest(
        application="sabnzbd",
        setting="incomplete_dir",
        value="/downloads/incomplete",
        dry_run=True,
    )
    mock_orchestrator.call_tool.return_value = {"success": True}

    # Act
    response = await configuration_manager.apply_recommendation(request)

    # Assert
    assert response.dry_run is True
    assert response.success is True
    assert "would be updated" in response.message.lower() or "dry run" in response.message.lower()


@pytest.mark.asyncio
async def test_apply_recommendation_actual(configuration_manager, mock_orchestrator):
    """Test actually applying a recommendation."""
    # Arrange
    request = ApplyRecommendationRequest(
        application="sabnzbd",
        setting="incomplete_dir",
        value="/downloads/incomplete",
        dry_run=False,
    )
    mock_orchestrator.call_tool.return_value = {"success": True}

    # Act
    response = await configuration_manager.apply_recommendation(request)

    # Assert
    assert response.dry_run is False
    assert response.success is True
    mock_orchestrator.call_tool.assert_called_with(
        server="sabnzbd",
        tool="set_config",
        params={"setting": "incomplete_dir", "value": "/downloads/incomplete"},
    )


@pytest.mark.asyncio
async def test_apply_recommendation_failure(configuration_manager, mock_orchestrator):
    """Test handling failure when applying a recommendation."""
    # Arrange
    request = ApplyRecommendationRequest(
        application="sabnzbd",
        setting="incomplete_dir",
        value="/downloads/incomplete",
        dry_run=False,
    )
    mock_orchestrator.call_tool.side_effect = Exception("Failed to update")

    # Act
    response = await configuration_manager.apply_recommendation(request)

    # Assert
    assert response.success is False
    assert "failed" in response.message.lower()


# ============================================================================
# Tests for Audit History
# ============================================================================


@pytest.mark.asyncio
async def test_get_audit_history(configuration_manager, mock_audit_repo):
    """Test retrieving audit history."""
    # Arrange
    from autoarr.api.database import AuditResult

    mock_results = [
        AuditResult(
            id=1,
            application="sabnzbd",
            timestamp=datetime.utcnow(),
            total_checks=5,
            issues_found=2,
            high_priority=1,
            medium_priority=1,
            low_priority=0,
            configuration_snapshot="{}",
            recommendations="[]",
        ),
    ]
    mock_audit_repo.get_audit_history.return_value = mock_results

    # Act
    history = await configuration_manager.get_audit_history("sabnzbd", limit=10)

    # Assert
    assert len(history) == 1
    assert history[0].application == "sabnzbd"
    mock_audit_repo.get_audit_history.assert_called_once_with("sabnzbd", 10)


# ============================================================================
# Tests for Priority Scoring
# ============================================================================


@pytest.mark.asyncio
async def test_recommendations_sorted_by_priority(
    configuration_manager, mock_orchestrator, mock_best_practices_repo, mock_audit_repo
):
    """Test that recommendations are sorted by priority (high first)."""
    # Arrange
    mock_config = {"setting1": "", "setting2": "", "setting3": ""}
    mock_orchestrator.call_tool.return_value = mock_config

    best_practices = [
        create_best_practice(
            practice_id=1,
            application="sabnzbd",
            category="test",
            setting_name="setting1",
            recommended_value="value1",
            priority="low",
            explanation="Low priority",
            impact="Minor",
        ),
        create_best_practice(
            practice_id=2,
            application="sabnzbd",
            category="test",
            setting_name="setting2",
            recommended_value="value2",
            priority="high",
            explanation="High priority",
            impact="Severe",
        ),
        create_best_practice(
            practice_id=3,
            application="sabnzbd",
            category="test",
            setting_name="setting3",
            recommended_value="value3",
            priority="medium",
            explanation="Medium priority",
            impact="Moderate",
        ),
    ]
    mock_best_practices_repo.get_by_application.return_value = best_practices
    mock_audit_repo.save_audit_result.return_value = Mock()

    # Act
    audit = await configuration_manager.audit_application("sabnzbd", mock_config)

    # Assert
    priorities = [r.priority for r in audit.recommendations]
    # High priority recommendations should come first
    high_index = priorities.index(Priority.HIGH)
    medium_index = priorities.index(Priority.MEDIUM)
    low_index = priorities.index(Priority.LOW)
    assert high_index < medium_index < low_index


# ============================================================================
# Tests for Common Misconfigurations
# ============================================================================


@pytest.mark.asyncio
async def test_detects_common_sabnzbd_misconfigurations(
    configuration_manager, mock_best_practices_repo
):
    """Test detection of common SABnzbd misconfigurations."""
    # Arrange
    # Simulating common misconfigurations
    current_config = {
        "incomplete_dir": "",  # Missing incomplete dir
        "download_free": "100M",  # Too low disk space warning
        "refresh_rate": 0,  # Refresh rate 0 causes excessive requests
        "queue_complete": "",  # No completion script
        "pre_script": "",  # No pre-processing script
    }

    best_practices = [
        create_best_practice(
            practice_id=1,
            application="sabnzbd",
            category="downloads",
            setting_name="incomplete_dir",
            recommended_value="/downloads/incomplete",
            priority="high",
            explanation="Use separate incomplete directory",
            impact="Data corruption risk",
        ),
        create_best_practice(
            practice_id=2,
            application="sabnzbd",
            category="storage",
            setting_name="download_free",
            recommended_value="10G",
            priority="medium",
            explanation="Set adequate free space requirement",
            impact="Failed downloads",
        ),
        create_best_practice(
            practice_id=3,
            application="sabnzbd",
            category="performance",
            setting_name="refresh_rate",
            recommended_value="2",
            priority="medium",
            explanation="Set appropriate refresh rate",
            impact="Excessive API calls",
        ),
    ]
    mock_best_practices_repo.get_by_application.return_value = best_practices

    # Act
    recommendations = await configuration_manager.compare_configuration("sabnzbd", current_config)

    # Assert
    # Should detect at least 3 misconfigurations
    assert len(recommendations) >= 3
    settings_checked = {r.setting for r in recommendations}
    assert "incomplete_dir" in settings_checked
    assert "download_free" in settings_checked
    assert "refresh_rate" in settings_checked


@pytest.mark.asyncio
async def test_detects_common_sonarr_misconfigurations(
    configuration_manager, mock_best_practices_repo
):
    """Test detection of common Sonarr misconfigurations."""
    # Arrange
    current_config = {
        "enableCompletedDownloadHandling": False,  # Should be enabled
        "autoRedownloadFailed": False,  # Should auto-retry
        "removeFailedDownloads": False,  # Should clean up
    }

    best_practices = [
        create_best_practice(
            practice_id=1,
            application="sonarr",
            category="downloads",
            setting_name="enableCompletedDownloadHandling",
            recommended_value="true",
            priority="high",
            explanation="Enable completed download handling",
            impact="Manual intervention required",
        ),
        create_best_practice(
            practice_id=2,
            application="sonarr",
            category="downloads",
            setting_name="autoRedownloadFailed",
            recommended_value="true",
            priority="high",
            explanation="Enable auto-redownload failed",
            impact="Missing episodes",
        ),
    ]
    mock_best_practices_repo.get_by_application.return_value = best_practices

    # Act
    recommendations = await configuration_manager.compare_configuration("sonarr", current_config)

    # Assert
    assert len(recommendations) >= 2
    settings_checked = {r.setting for r in recommendations}
    assert "enableCompletedDownloadHandling" in settings_checked
    assert "autoRedownloadFailed" in settings_checked
