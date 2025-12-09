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
Unit tests for Configuration Manager service.

This module tests the configuration manager's ability to audit configurations,
manage recommendations, and apply configuration changes.
"""

import pytest

from autoarr.api.services.config_manager import (
    ConfigurationManager,
    get_config_manager_instance,
    reset_config_manager,
)


@pytest.fixture
def config_manager():
    """Provide a fresh ConfigurationManager instance for each test."""
    reset_config_manager()
    return ConfigurationManager()


class TestConfigurationManagerInitialization:
    """Tests for ConfigurationManager initialization."""

    def test_init_creates_empty_storage(self, config_manager):
        """Test that initialization creates empty storage structures."""
        assert len(config_manager._recommendations) == 0
        assert len(config_manager._audit_history) == 0
        assert config_manager._next_recommendation_id == 1


@pytest.mark.asyncio
class TestAuditConfiguration:
    """Tests for configuration auditing."""

    async def test_audit_single_service(self, config_manager):
        """Test auditing a single service."""
        result = await config_manager.audit_configuration(["sabnzbd"])

        assert "audit_id" in result
        assert result["audit_id"].startswith("audit_")
        assert "timestamp" in result
        assert result["services"] == ["sabnzbd"]
        assert result["total_recommendations"] == 1
        assert len(result["recommendations"]) == 1
        assert result["web_search_used"] is False

    async def test_audit_multiple_services(self, config_manager):
        """Test auditing multiple services."""
        result = await config_manager.audit_configuration(["sabnzbd", "sonarr", "radarr"])

        assert result["services"] == ["sabnzbd", "sonarr", "radarr"]
        assert result["total_recommendations"] == 3
        assert len(result["recommendations"]) == 3

    async def test_audit_with_web_search(self, config_manager):
        """Test auditing with web search enabled."""
        result = await config_manager.audit_configuration(["sonarr"], include_web_search=True)

        assert result["web_search_used"] is True
        assert result["recommendations"][0]["source"] == "web_search"

    async def test_audit_without_web_search(self, config_manager):
        """Test auditing without web search."""
        result = await config_manager.audit_configuration(["sonarr"], include_web_search=False)

        assert result["web_search_used"] is False
        assert result["recommendations"][0]["source"] == "database"

    async def test_audit_invalid_service_raises_error(self, config_manager):
        """Test that invalid service name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid service 'invalid'"):
            await config_manager.audit_configuration(["invalid"])

    async def test_audit_empty_services_raises_error(self, config_manager):
        """Test that empty services list raises ValueError."""
        with pytest.raises(ValueError, match="At least one service must be specified"):
            await config_manager.audit_configuration([])

    async def test_audit_stores_recommendations(self, config_manager):
        """Test that audit stores recommendations."""
        await config_manager.audit_configuration(["sabnzbd"])

        assert len(config_manager._recommendations) == 1
        assert 1 in config_manager._recommendations

    async def test_audit_stores_history(self, config_manager):
        """Test that audit stores history."""
        await config_manager.audit_configuration(["sabnzbd"])

        assert len(config_manager._audit_history) == 1
        audit = config_manager._audit_history[0]
        assert "audit_id" in audit
        assert "timestamp" in audit
        assert audit["services"] == ["sabnzbd"]

    async def test_recommendation_has_required_fields(self, config_manager):
        """Test that recommendations have all required fields."""
        result = await config_manager.audit_configuration(["sabnzbd"])
        rec = result["recommendations"][0]

        assert "id" in rec
        assert "service" in rec
        assert "category" in rec
        assert "priority" in rec
        assert "title" in rec
        assert "description" in rec
        assert "current_value" in rec
        assert "recommended_value" in rec
        assert "impact" in rec
        assert "source" in rec
        assert "applied" in rec
        assert "applied_at" in rec

    async def test_recommendation_ids_increment(self, config_manager):
        """Test that recommendation IDs increment correctly."""
        await config_manager.audit_configuration(["sabnzbd"])
        await config_manager.audit_configuration(["sonarr"])

        assert 1 in config_manager._recommendations
        assert 2 in config_manager._recommendations


@pytest.mark.asyncio
class TestGetRecommendations:
    """Tests for getting recommendations."""

    async def test_get_all_recommendations(self, config_manager):
        """Test getting all recommendations."""
        await config_manager.audit_configuration(["sabnzbd", "sonarr"])

        result = await config_manager.get_recommendations()

        assert result["total"] == 2
        assert len(result["recommendations"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 10

    async def test_get_recommendations_filter_by_service(self, config_manager):
        """Test filtering recommendations by service."""
        await config_manager.audit_configuration(["sabnzbd", "sonarr"])

        result = await config_manager.get_recommendations(service="sabnzbd")

        assert result["total"] == 1
        assert result["recommendations"][0]["service"] == "sabnzbd"

    async def test_get_recommendations_filter_by_priority(self, config_manager):
        """Test filtering recommendations by priority."""
        await config_manager.audit_configuration(["sabnzbd"])

        result = await config_manager.get_recommendations(priority="medium")

        assert result["total"] == 1
        assert result["recommendations"][0]["priority"] == "medium"

    async def test_get_recommendations_filter_by_category(self, config_manager):
        """Test filtering recommendations by category."""
        await config_manager.audit_configuration(["sabnzbd"])

        result = await config_manager.get_recommendations(category="performance")

        assert result["total"] == 1
        assert result["recommendations"][0]["category"] == "performance"

    async def test_get_recommendations_pagination(self, config_manager):
        """Test pagination of recommendations."""
        # Create 15 recommendations
        await config_manager.audit_configuration(["sabnzbd"] * 15)

        # Get first page
        page1 = await config_manager.get_recommendations(page=1, page_size=10)
        assert len(page1["recommendations"]) == 10
        assert page1["total"] == 15

        # Get second page
        page2 = await config_manager.get_recommendations(page=2, page_size=10)
        assert len(page2["recommendations"]) == 5
        assert page2["total"] == 15

    async def test_get_recommendations_empty(self, config_manager):
        """Test getting recommendations when none exist."""
        result = await config_manager.get_recommendations()

        assert result["total"] == 0
        assert len(result["recommendations"]) == 0


@pytest.mark.asyncio
class TestGetRecommendationById:
    """Tests for getting specific recommendation."""

    async def test_get_existing_recommendation(self, config_manager):
        """Test getting an existing recommendation by ID."""
        await config_manager.audit_configuration(["sabnzbd"])

        rec = await config_manager.get_recommendation_by_id(1)

        assert rec is not None
        assert rec["id"] == 1
        assert rec["service"] == "sabnzbd"
        assert "explanation" in rec
        assert "references" in rec

    async def test_get_nonexistent_recommendation(self, config_manager):
        """Test getting a non-existent recommendation."""
        rec = await config_manager.get_recommendation_by_id(999)

        assert rec is None

    async def test_get_recommendation_has_additional_fields(self, config_manager):
        """Test that detailed view has additional fields."""
        await config_manager.audit_configuration(["sabnzbd"])

        rec = await config_manager.get_recommendation_by_id(1)

        assert "explanation" in rec
        assert "references" in rec
        assert isinstance(rec["references"], list)


@pytest.mark.asyncio
class TestApplyRecommendations:
    """Tests for applying recommendations."""

    async def test_apply_single_recommendation(self, config_manager):
        """Test applying a single recommendation."""
        await config_manager.audit_configuration(["sabnzbd"])

        result = await config_manager.apply_recommendations([1])

        assert result["total_requested"] == 1
        assert result["total_successful"] == 1
        assert result["total_failed"] == 0
        assert result["dry_run"] is False
        assert len(result["results"]) == 1
        assert result["results"][0]["success"] is True
        assert result["results"][0]["applied_at"] is not None

    async def test_apply_multiple_recommendations(self, config_manager):
        """Test applying multiple recommendations."""
        await config_manager.audit_configuration(["sabnzbd", "sonarr"])

        result = await config_manager.apply_recommendations([1, 2])

        assert result["total_requested"] == 2
        assert result["total_successful"] == 2
        assert result["total_failed"] == 0

    async def test_apply_nonexistent_recommendation(self, config_manager):
        """Test applying a non-existent recommendation."""
        result = await config_manager.apply_recommendations([999])

        assert result["total_requested"] == 1
        assert result["total_successful"] == 0
        assert result["total_failed"] == 1
        assert result["results"][0]["success"] is False
        assert result["results"][0]["message"] == "Recommendation not found"

    async def test_apply_dry_run(self, config_manager):
        """Test applying recommendations in dry run mode."""
        await config_manager.audit_configuration(["sabnzbd"])

        result = await config_manager.apply_recommendations([1], dry_run=True)

        assert result["dry_run"] is True
        assert result["total_successful"] == 0  # Dry run doesn't count as successful
        assert result["results"][0]["success"] is True
        assert result["results"][0]["dry_run"] is True
        assert result["results"][0]["applied_at"] is None

    async def test_apply_empty_list_raises_error(self, config_manager):
        """Test that empty recommendation list raises ValueError."""
        with pytest.raises(ValueError, match="At least one recommendation ID must be specified"):
            await config_manager.apply_recommendations([])

    async def test_apply_updates_recommendation_status(self, config_manager):
        """Test that applying updates the recommendation status."""
        await config_manager.audit_configuration(["sabnzbd"])

        # Check initial status
        rec_before = config_manager._recommendations[1]
        assert rec_before["applied"] is False
        assert rec_before["applied_at"] is None

        # Apply recommendation
        await config_manager.apply_recommendations([1])

        # Check updated status
        rec_after = config_manager._recommendations[1]
        assert rec_after["applied"] is True
        assert rec_after["applied_at"] is not None

    async def test_apply_mixed_success_and_failure(self, config_manager):
        """Test applying mix of valid and invalid recommendations."""
        await config_manager.audit_configuration(["sabnzbd"])

        result = await config_manager.apply_recommendations([1, 999])

        assert result["total_requested"] == 2
        assert result["total_successful"] == 1
        assert result["total_failed"] == 1


@pytest.mark.asyncio
class TestGetAuditHistory:
    """Tests for getting audit history."""

    async def test_get_audit_history(self, config_manager):
        """Test getting audit history."""
        await config_manager.audit_configuration(["sabnzbd"])
        await config_manager.audit_configuration(["sonarr"])

        result = await config_manager.get_audit_history()

        assert result["total"] == 2
        assert len(result["audits"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 10

    async def test_audit_history_sorted_by_timestamp(self, config_manager):
        """Test that audit history is sorted by timestamp (most recent first)."""
        audit1 = await config_manager.audit_configuration(["sabnzbd"])
        audit2 = await config_manager.audit_configuration(["sonarr"])

        result = await config_manager.get_audit_history()

        # Most recent should be first
        assert result["audits"][0]["audit_id"] == audit2["audit_id"]
        assert result["audits"][1]["audit_id"] == audit1["audit_id"]

    async def test_audit_history_pagination(self, config_manager):
        """Test pagination of audit history."""
        # Create 15 audits
        for _ in range(15):
            await config_manager.audit_configuration(["sabnzbd"])

        # Get first page
        page1 = await config_manager.get_audit_history(page=1, page_size=10)
        assert len(page1["audits"]) == 10
        assert page1["total"] == 15

        # Get second page
        page2 = await config_manager.get_audit_history(page=2, page_size=10)
        assert len(page2["audits"]) == 5
        assert page2["total"] == 15

    async def test_audit_history_empty(self, config_manager):
        """Test getting audit history when empty."""
        result = await config_manager.get_audit_history()

        assert result["total"] == 0
        assert len(result["audits"]) == 0


class TestSingletonFunctions:
    """Tests for singleton management functions."""

    def test_get_config_manager_instance_creates_singleton(self):
        """Test that get_config_manager_instance creates singleton."""
        reset_config_manager()

        instance1 = get_config_manager_instance()
        instance2 = get_config_manager_instance()

        assert instance1 is instance2

    def test_reset_config_manager_clears_singleton(self):
        """Test that reset_config_manager clears the singleton."""
        instance1 = get_config_manager_instance()
        reset_config_manager()
        instance2 = get_config_manager_instance()

        assert instance1 is not instance2

    def test_singleton_persists_data(self):
        """Test that singleton persists data across calls."""
        reset_config_manager()
        manager = get_config_manager_instance()
        manager._next_recommendation_id = 100

        # Get the same instance
        same_manager = get_config_manager_instance()
        assert same_manager._next_recommendation_id == 100
