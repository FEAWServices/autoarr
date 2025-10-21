"""
Integration tests for Best Practices database operations.

Tests the complete flow from database creation to seeding to querying.
"""

import pytest

from autoarr.api.database import BestPracticesRepository, Database
from autoarr.api.seed_data import (get_best_practices_seed_data,
                                   seed_best_practices)


@pytest.fixture
async def test_db():
    """Create a test database with the best_practices table."""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()


@pytest.fixture
async def seeded_db(test_db):
    """Create and seed a test database."""
    count = await seed_best_practices(test_db)
    assert count > 0
    return test_db


class TestBestPracticesSeedData:
    """Test suite for seed data validation."""

    def test_seed_data_has_minimum_practices(self) -> None:
        """Test that seed data contains at least 20 practices."""
        practices = get_best_practices_seed_data()
        assert len(practices) >= 20

    def test_seed_data_covers_all_applications(self) -> None:
        """Test that seed data covers all 4 applications."""
        practices = get_best_practices_seed_data()
        applications = set(p["application"] for p in practices)

        assert "sabnzbd" in applications
        assert "sonarr" in applications
        assert "radarr" in applications
        assert "plex" in applications

    def test_seed_data_has_all_required_fields(self) -> None:
        """Test that all seed data entries have required fields."""
        practices = get_best_practices_seed_data()

        required_fields = [
            "application",
            "category",
            "setting_name",
            "setting_path",
            "recommended_value",
            "current_check_type",
            "explanation",
            "priority",
            "version_added",
            "enabled",
        ]

        for practice in practices:
            for field in required_fields:
                assert (
                    field in practice
                ), f"Missing field '{field}' in practice: {practice.get('setting_name', 'unknown')}"

    def test_seed_data_has_valid_priorities(self) -> None:
        """Test that all practices have valid priority levels."""
        practices = get_best_practices_seed_data()
        valid_priorities = {"critical", "high", "medium", "low"}

        for practice in practices:
            assert (
                practice["priority"] in valid_priorities
            ), f"Invalid priority '{practice['priority']}' in {practice['setting_name']}"

    def test_seed_data_has_valid_applications(self) -> None:
        """Test that all practices have valid application names."""
        practices = get_best_practices_seed_data()
        valid_applications = {"sabnzbd", "sonarr", "radarr", "plex"}

        for practice in practices:
            assert (
                practice["application"] in valid_applications
            ), f"Invalid application '{practice['application']}' in {practice['setting_name']}"

    def test_seed_data_has_minimum_per_application(self) -> None:
        """Test that each application has at least 5 practices."""
        practices = get_best_practices_seed_data()
        app_counts = {}

        for practice in practices:
            app = practice["application"]
            app_counts[app] = app_counts.get(app, 0) + 1

        for app in ["sabnzbd", "sonarr", "radarr", "plex"]:
            assert app_counts.get(app, 0) >= 5, f"Application '{app}' has less than 5 practices"


class TestBestPracticesDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_seed_practices_inserts_data(self, test_db: Database) -> None:
        """Test that seeding inserts practices into the database."""
        repository = BestPracticesRepository(test_db)

        # Initially empty
        count_before = await repository.count()
        assert count_before == 0

        # Seed database
        inserted_count = await seed_best_practices(test_db)
        assert inserted_count >= 20

        # Verify data inserted
        count_after = await repository.count()
        assert count_after == inserted_count

    @pytest.mark.asyncio
    async def test_query_by_application(self, seeded_db: Database) -> None:
        """Test querying practices by application."""
        repository = BestPracticesRepository(seeded_db)

        # Get SABnzbd practices
        sabnzbd_practices = await repository.get_by_application("sabnzbd")
        assert len(sabnzbd_practices) >= 5
        assert all(p.application == "sabnzbd" for p in sabnzbd_practices)

        # Get Sonarr practices
        sonarr_practices = await repository.get_by_application("sonarr")
        assert len(sonarr_practices) >= 5
        assert all(p.application == "sonarr" for p in sonarr_practices)

    @pytest.mark.asyncio
    async def test_query_by_priority(self, seeded_db: Database) -> None:
        """Test querying practices by priority."""
        repository = BestPracticesRepository(seeded_db)

        # Get critical practices
        critical_practices = await repository.get_by_priority(["critical"])
        assert len(critical_practices) >= 1
        assert all(p.priority == "critical" for p in critical_practices)

        # Get high and critical practices
        high_critical = await repository.get_by_priority(["critical", "high"])
        assert len(high_critical) > len(critical_practices)

    @pytest.mark.asyncio
    async def test_query_by_category(self, seeded_db: Database) -> None:
        """Test querying practices by application and category."""
        repository = BestPracticesRepository(seeded_db)

        # Get Sonarr media management practices
        practices = await repository.get_by_category("sonarr", "media_management")
        assert len(practices) >= 1
        assert all(p.application == "sonarr" for p in practices)
        assert all(p.category == "media_management" for p in practices)

    @pytest.mark.asyncio
    async def test_search_practices(self, seeded_db: Database) -> None:
        """Test searching practices by keyword."""
        repository = BestPracticesRepository(seeded_db)

        # Search for "rename"
        rename_practices = await repository.search("rename")
        assert len(rename_practices) >= 2  # Both Sonarr and Radarr have rename practices

        # Search for "https"
        https_practices = await repository.search("https")
        assert len(https_practices) >= 1

    @pytest.mark.asyncio
    async def test_filter_enabled_only(self, seeded_db: Database) -> None:
        """Test filtering to get only enabled practices."""
        repository = BestPracticesRepository(seeded_db)

        # All practices should be enabled by default
        all_practices = await repository.get_all()
        enabled_practices = await repository.get_all(enabled_only=True)

        assert len(all_practices) == len(enabled_practices)
        assert all(p.enabled for p in enabled_practices)

    @pytest.mark.asyncio
    async def test_update_and_query(self, seeded_db: Database) -> None:
        """Test updating a practice and querying it."""
        repository = BestPracticesRepository(seeded_db)

        # Get first practice
        practices = await repository.get_all()
        first_practice = practices[0]

        # Update it
        updated = await repository.update(first_practice.id, {"priority": "low"})
        assert updated is not None
        assert updated.priority == "low"

        # Query it again
        retrieved = await repository.get_by_id(first_practice.id)
        assert retrieved is not None
        assert retrieved.priority == "low"

    @pytest.mark.asyncio
    async def test_soft_delete(self, seeded_db: Database) -> None:
        """Test soft deleting (disabling) a practice."""
        repository = BestPracticesRepository(seeded_db)

        # Get first practice
        practices = await repository.get_all()
        first_practice = practices[0]
        practice_id = first_practice.id

        # Soft delete it
        result = await repository.soft_delete(practice_id)  # noqa: F841
        assert result is True

        # It should still exist but be disabled
        retrieved = await repository.get_by_id(practice_id)
        assert retrieved is not None
        assert retrieved.enabled is False

        # Should not appear in enabled-only queries
        enabled_practices = await repository.get_all(enabled_only=True)
        assert all(p.id != practice_id for p in enabled_practices)

    @pytest.mark.asyncio
    async def test_complex_filter(self, seeded_db: Database) -> None:
        """Test filtering with multiple criteria."""
        repository = BestPracticesRepository(seeded_db)

        # Filter: sabnzbd + high priority
        practices = await repository.filter(application="sabnzbd", priority="high")

        assert len(practices) >= 1
        assert all(p.application == "sabnzbd" for p in practices)
        assert all(p.priority == "high" for p in practices)

    @pytest.mark.asyncio
    async def test_pagination(self, seeded_db: Database) -> None:
        """Test paginated queries."""
        repository = BestPracticesRepository(seeded_db)

        # Get first page
        page1 = await repository.get_paginated(page=1, page_size=5)
        assert len(page1) == 5

        # Get second page
        page2 = await repository.get_paginated(page=2, page_size=5)
        assert len(page2) == 5

        # Pages should have different practices
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0


class TestBestPracticesResponseModels:
    """Test Pydantic response models with database data."""

    @pytest.mark.asyncio
    async def test_convert_db_model_to_response(self, seeded_db: Database) -> None:
        """Test converting database model to Pydantic response model."""
        from autoarr.api.models import BestPracticeResponse

        repository = BestPracticesRepository(seeded_db)
        practices = await repository.get_all()
        first_practice = practices[0]

        # Convert to response model
        response = BestPracticeResponse.model_validate(first_practice)

        assert response.id == first_practice.id
        assert response.application == first_practice.application
        assert response.setting_name == first_practice.setting_name
        assert response.priority == first_practice.priority
        assert response.created_at == first_practice.created_at
        assert response.updated_at == first_practice.updated_at

    @pytest.mark.asyncio
    async def test_list_response_model(self, seeded_db: Database) -> None:
        """Test BestPracticeListResponse model."""
        from autoarr.api.models import (BestPracticeListResponse,
                                        BestPracticeResponse)

        repository = BestPracticesRepository(seeded_db)
        practices = await repository.get_by_application("sabnzbd")

        # Convert to response models
        response_practices = [BestPracticeResponse.model_validate(p) for p in practices]

        # Create list response
        list_response = BestPracticeListResponse(
            practices=response_practices, total=len(response_practices)
        )

        assert list_response.total == len(practices)
        assert len(list_response.practices) == len(practices)
        assert all(isinstance(p, BestPracticeResponse) for p in list_response.practices)
