"""
Tests for seed data module.

This module tests the seed data generation and database seeding functionality.
"""

import json

import pytest

from autoarr.api import seed_data
from autoarr.api.database import Database, BestPracticesRepository


class TestSeedDataGeneration:
    """Test seed data generation functions."""

    def test_get_best_practices_seed_data_returns_list(self) -> None:
        """Test that get_best_practices_seed_data returns a list."""
        data = seed_data.get_best_practices_seed_data()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_best_practices_seed_data_contains_all_applications(self) -> None:
        """Test that seed data includes all supported applications."""
        data = seed_data.get_best_practices_seed_data()
        applications = {practice["application"] for practice in data}

        expected_apps = {"sabnzbd", "sonarr", "radarr", "plex"}
        assert applications == expected_apps

    def test_get_best_practices_seed_data_has_required_fields(self) -> None:
        """Test that each practice has all required fields."""
        data = seed_data.get_best_practices_seed_data()

        required_fields = {
            "application",
            "category",
            "setting_name",
            "setting_path",
            "recommended_value",
            "current_check_type",
            "explanation",
            "priority",
            "documentation_url",
            "version_added",
            "enabled",
        }

        for practice in data:
            assert required_fields.issubset(
                practice.keys()
            ), f"Practice {practice.get('setting_name')} missing required fields"

    def test_get_best_practices_seed_data_valid_json_recommended_values(self) -> None:
        """Test that all recommended_value fields contain valid JSON."""
        data = seed_data.get_best_practices_seed_data()

        for practice in data:
            recommended_value = practice["recommended_value"]
            try:
                json.loads(recommended_value)
            except json.JSONDecodeError:
                pytest.fail(
                    f"Invalid JSON in recommended_value for {practice['setting_name']}: "
                    f"{recommended_value}"
                )

    def test_get_best_practices_seed_data_valid_priorities(self) -> None:
        """Test that all priorities are valid."""
        data = seed_data.get_best_practices_seed_data()
        valid_priorities = {"critical", "high", "medium", "low"}

        for practice in data:
            assert (
                practice["priority"] in valid_priorities
            ), f"Invalid priority '{practice['priority']}' for {practice['setting_name']}"

    def test_get_best_practices_seed_data_valid_check_types(self) -> None:
        """Test that all check types are valid."""
        data = seed_data.get_best_practices_seed_data()
        valid_check_types = {
            "equals",
            "not_equals",
            "contains",
            "not_contains",
            "greater_than",
            "less_than",
            "in_range",
            "regex",
            "exists",
            "not_empty",
            "boolean",
            "custom",
        }

        for practice in data:
            assert practice["current_check_type"] in valid_check_types, (
                f"Invalid check type '{practice['current_check_type']}' "
                f"for {practice['setting_name']}"
            )

    def test_get_best_practices_seed_data_has_documentation_urls(self) -> None:
        """Test that all practices have documentation URLs."""
        data = seed_data.get_best_practices_seed_data()

        for practice in data:
            assert practice[
                "documentation_url"
            ], f"Missing documentation URL for {practice['setting_name']}"
            assert practice["documentation_url"].startswith(
                "http"
            ), f"Invalid documentation URL for {practice['setting_name']}"

    def test_get_best_practices_seed_data_has_explanations(self) -> None:
        """Test that all practices have meaningful explanations."""
        data = seed_data.get_best_practices_seed_data()

        for practice in data:
            explanation = practice["explanation"]
            assert (
                len(explanation) > 50
            ), f"Explanation too short for {practice['setting_name']}: {explanation}"


class TestApplicationSpecificPractices:
    """Test application-specific practices."""

    def test_sabnzbd_practices_count(self) -> None:
        """Test that SABnzbd has expected number of practices."""
        data = seed_data.get_best_practices_seed_data()
        sabnzbd_practices = [p for p in data if p["application"] == "sabnzbd"]
        assert len(sabnzbd_practices) >= 5

    def test_sonarr_practices_count(self) -> None:
        """Test that Sonarr has expected number of practices."""
        data = seed_data.get_best_practices_seed_data()
        sonarr_practices = [p for p in data if p["application"] == "sonarr"]
        assert len(sonarr_practices) >= 5

    def test_radarr_practices_count(self) -> None:
        """Test that Radarr has expected number of practices."""
        data = seed_data.get_best_practices_seed_data()
        radarr_practices = [p for p in data if p["application"] == "radarr"]
        assert len(radarr_practices) >= 5

    def test_plex_practices_count(self) -> None:
        """Test that Plex has expected number of practices."""
        data = seed_data.get_best_practices_seed_data()
        plex_practices = [p for p in data if p["application"] == "plex"]
        assert len(plex_practices) >= 5

    def test_sabnzbd_has_security_practices(self) -> None:
        """Test that SABnzbd includes security-related practices."""
        data = seed_data.get_best_practices_seed_data()
        sabnzbd_practices = [p for p in data if p["application"] == "sabnzbd"]

        categories = {p["category"] for p in sabnzbd_practices}
        assert "security" in categories

    def test_all_applications_have_high_priority_practices(self) -> None:
        """Test that each application has at least one high or critical priority practice."""
        data = seed_data.get_best_practices_seed_data()

        for app in ["sabnzbd", "sonarr", "radarr", "plex"]:
            app_practices = [p for p in data if p["application"] == app]
            high_priority_practices = [
                p for p in app_practices if p["priority"] in ("critical", "high")
            ]
            assert len(high_priority_practices) > 0, f"{app} has no high/critical practices"


@pytest.mark.asyncio
class TestSeedBestPractices:
    """Test database seeding function."""

    async def test_seed_best_practices_inserts_practices(self, tmp_path: str) -> None:
        """Test that seed_best_practices inserts practices into database."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        count = await seed_data.seed_best_practices(db)

        # Verify insertion
        assert count > 0
        repo = BestPracticesRepository(db)
        all_practices = await repo.get_all()
        assert len(all_practices) == count

        await db.close()

    async def test_seed_best_practices_creates_valid_database_records(self, tmp_path: str) -> None:
        """Test that seeded practices are valid database records."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        await seed_data.seed_best_practices(db)

        # Retrieve and validate
        repo = BestPracticesRepository(db)
        practices = await repo.get_all()

        for practice in practices:
            assert practice.id > 0
            assert practice.application
            assert practice.setting_name
            assert practice.priority
            assert practice.created_at
            assert practice.updated_at

        await db.close()

    async def test_seed_best_practices_by_application(self, tmp_path: str) -> None:
        """Test that practices can be retrieved by application."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        await seed_data.seed_best_practices(db)

        # Test retrieval by application
        repo = BestPracticesRepository(db)

        for app in ["sabnzbd", "sonarr", "radarr", "plex"]:
            app_practices = await repo.get_by_application(app)
            assert len(app_practices) > 0
            assert all(p.application == app for p in app_practices)

        await db.close()

    async def test_seed_best_practices_enabled_filter(self, tmp_path: str) -> None:
        """Test that enabled filter works on seeded practices."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        await seed_data.seed_best_practices(db)

        # All practices should be enabled by default
        repo = BestPracticesRepository(db)
        enabled_practices = await repo.get_all(enabled_only=True)
        all_practices = await repo.get_all(enabled_only=False)

        assert len(enabled_practices) == len(all_practices)
        assert all(p.enabled for p in enabled_practices)

        await db.close()


@pytest.mark.asyncio
class TestSeedDataIntegration:
    """Integration tests for seed data with repository methods."""

    async def test_filter_by_category(self, tmp_path: str) -> None:
        """Test filtering seeded practices by category."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        await seed_data.seed_best_practices(db)

        # Filter by category
        repo = BestPracticesRepository(db)
        media_management_practices = await repo.filter(category="media_management")

        assert len(media_management_practices) > 0
        assert all(p.category == "media_management" for p in media_management_practices)

        await db.close()

    async def test_filter_by_priority(self, tmp_path: str) -> None:
        """Test filtering seeded practices by priority."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        await seed_data.seed_best_practices(db)

        # Filter by priority
        repo = BestPracticesRepository(db)
        critical_practices = await repo.get_by_priority(["critical"], enabled_only=True)

        assert len(critical_practices) > 0
        assert all(p.priority == "critical" for p in critical_practices)

        await db.close()

    async def test_search_functionality(self, tmp_path: str) -> None:
        """Test search functionality on seeded practices."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite:///{db_path}")
        await db.init_db()

        # Seed practices
        await seed_data.seed_best_practices(db)

        # Search for practices
        repo = BestPracticesRepository(db)
        transcoding_practices = await repo.search("transcoding")

        assert len(transcoding_practices) > 0
        # Verify search matches
        for practice in transcoding_practices:
            text_to_search = (
                f"{practice.setting_name} {practice.explanation} {practice.category}".lower()
            )
            assert "transcoding" in text_to_search

        await db.close()
