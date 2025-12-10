import pytest_asyncio

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
Unit tests for Best Practices Repository.

Following TDD (Red-Green-Refactor):
- These tests are written FIRST before implementation
- They define the expected behavior of the BestPracticesRepository
- They should all FAIL initially until implementation is complete
"""

import json
from typing import AsyncGenerator

import pytest


@pytest_asyncio.fixture
async def test_database() -> AsyncGenerator:
    """Create a test database instance."""
    from autoarr.api.database import Database

    # Use in-memory SQLite for testing
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()

    yield db

    await db.close()


@pytest_asyncio.fixture
async def best_practices_repository(test_database):
    """Create a BestPracticesRepository instance."""
    from autoarr.api.database import BestPracticesRepository

    return BestPracticesRepository(test_database)


@pytest_asyncio.fixture
def sample_practice_data() -> dict:
    """Sample best practice data for testing."""
    return {
        "application": "sabnzbd",
        "category": "downloads",
        "setting_name": "incomplete_dir",
        "setting_path": "misc.incomplete_dir",
        "recommended_value": json.dumps(
            {"type": "not_empty", "description": "Separate directory for incomplete downloads"}
        ),
        "current_check_type": "not_empty",
        "explanation": "Using a separate incomplete directory prevents issues",
        "priority": "high",
        "impact": "Incomplete downloads may be processed incorrectly",
        "documentation_url": "https://sabnzbd.org/wiki/configuration/",
        "version_added": "1.0.0",
        "enabled": True,
    }


class TestBestPracticesRepositoryCreate:
    """Test suite for creating best practices."""

    @pytest.mark.asyncio
    async def test_create_best_practice(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test creating a new best practice."""
        practice = await best_practices_repository.create(sample_practice_data)

        assert practice.id is not None
        assert practice.application == "sabnzbd"
        assert practice.category == "downloads"
        assert practice.setting_name == "incomplete_dir"
        assert practice.priority == "high"
        assert practice.enabled is True
        assert practice.created_at is not None
        assert practice.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_practice_returns_with_id(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test that created practice has an auto-generated ID."""
        practice = await best_practices_repository.create(sample_practice_data)

        assert isinstance(practice.id, int)
        assert practice.id > 0

    @pytest.mark.asyncio
    async def test_create_practice_with_optional_fields(self, best_practices_repository) -> None:
        """Test creating practice with minimal required fields."""
        minimal_data = {
            "application": "sonarr",
            "category": "quality",
            "setting_name": "test_setting",
            "setting_path": "test.path",
            "recommended_value": '{"type": "boolean", "value": true}',
            "current_check_type": "equals",
            "explanation": "Test explanation",
            "priority": "medium",
            "version_added": "1.0.0",
        }

        practice = await best_practices_repository.create(minimal_data)

        assert practice.id is not None
        assert practice.impact is None
        assert practice.documentation_url is None
        assert practice.enabled is True  # Default value

    @pytest.mark.asyncio
    async def test_create_multiple_practices(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test creating multiple practices with different IDs."""
        practice1 = await best_practices_repository.create(sample_practice_data)

        data2 = {**sample_practice_data, "setting_name": "download_dir"}
        practice2 = await best_practices_repository.create(data2)

        assert practice1.id != practice2.id
        assert practice2.id == practice1.id + 1


class TestBestPracticesRepositoryRead:
    """Test suite for reading best practices."""

    @pytest.mark.asyncio
    async def test_get_by_id_existing_practice(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test getting a practice by ID that exists."""
        created = await best_practices_repository.create(sample_practice_data)

        retrieved = await best_practices_repository.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.application == created.application
        assert retrieved.setting_name == created.setting_name

    @pytest.mark.asyncio
    async def test_get_by_id_non_existing_practice(self, best_practices_repository) -> None:
        """Test getting a practice by ID that doesn't exist."""
        retrieved = await best_practices_repository.get_by_id(99999)

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_all_practices(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test getting all practices."""
        # Create multiple practices
        await best_practices_repository.create(sample_practice_data)

        data2 = {**sample_practice_data, "application": "sonarr", "category": "quality"}
        await best_practices_repository.create(data2)

        data3 = {**sample_practice_data, "application": "radarr", "category": "quality"}
        await best_practices_repository.create(data3)

        practices = await best_practices_repository.get_all()

        assert len(practices) == 3
        assert any(p.application == "sabnzbd" for p in practices)
        assert any(p.application == "sonarr" for p in practices)
        assert any(p.application == "radarr" for p in practices)

    @pytest.mark.asyncio
    async def test_get_by_application(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test filtering practices by application."""
        # Create practices for different applications
        await best_practices_repository.create(sample_practice_data)

        sonarr_data = {**sample_practice_data, "application": "sonarr"}
        await best_practices_repository.create(sonarr_data)

        await best_practices_repository.create(sonarr_data)  # Another sonarr practice

        # Get only SABnzbd practices
        sabnzbd_practices = await best_practices_repository.get_by_application("sabnzbd")
        assert len(sabnzbd_practices) == 1
        assert all(p.application == "sabnzbd" for p in sabnzbd_practices)

        # Get only Sonarr practices
        sonarr_practices = await best_practices_repository.get_by_application("sonarr")
        assert len(sonarr_practices) == 2
        assert all(p.application == "sonarr" for p in sonarr_practices)

    @pytest.mark.asyncio
    async def test_get_by_category(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test filtering practices by application and category."""
        # Create practices in different categories
        await best_practices_repository.create(sample_practice_data)  # downloads

        quality_data = {**sample_practice_data, "category": "quality"}
        await best_practices_repository.create(quality_data)

        # Get by category
        practices = await best_practices_repository.get_by_category("sabnzbd", "downloads")

        assert len(practices) == 1
        assert practices[0].category == "downloads"

    @pytest.mark.asyncio
    async def test_get_by_priority(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test filtering practices by priority."""
        # Create practices with different priorities
        await best_practices_repository.create(sample_practice_data)  # high

        medium_data = {**sample_practice_data, "priority": "medium"}
        await best_practices_repository.create(medium_data)

        critical_data = {**sample_practice_data, "priority": "critical"}
        await best_practices_repository.create(critical_data)

        # Get high priority practices
        high_practices = await best_practices_repository.get_by_priority(["high", "critical"])

        assert len(high_practices) == 2
        assert all(p.priority in ["high", "critical"] for p in high_practices)

    @pytest.mark.asyncio
    async def test_get_enabled_only(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test filtering to get only enabled practices."""
        # Create enabled and disabled practices
        await best_practices_repository.create(sample_practice_data)

        disabled_data = {**sample_practice_data, "enabled": False}
        await best_practices_repository.create(disabled_data)

        # Get only enabled
        enabled_practices = await best_practices_repository.get_all(enabled_only=True)

        assert len(enabled_practices) == 1
        assert all(p.enabled for p in enabled_practices)

    @pytest.mark.asyncio
    async def test_search_practices(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test searching practices by keyword."""
        await best_practices_repository.create(sample_practice_data)

        performance_data = {
            **sample_practice_data,
            "category": "performance",
            "setting_name": "cache_limit",
            "explanation": "Increase cache for better performance",
        }
        await best_practices_repository.create(performance_data)

        # Search for "incomplete"
        results = await best_practices_repository.search("incomplete")
        assert len(results) >= 1
        assert any("incomplete" in p.setting_name.lower() for p in results)

        # Search for "performance"
        results = await best_practices_repository.search("performance")
        assert len(results) >= 1
        assert any("performance" in p.category.lower() for p in results)

    @pytest.mark.asyncio
    async def test_count_practices(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test counting practices with filters."""
        # Create multiple practices
        await best_practices_repository.create(sample_practice_data)

        sonarr_data = {**sample_practice_data, "application": "sonarr"}
        await best_practices_repository.create(sonarr_data)

        # Count all
        total = await best_practices_repository.count()
        assert total == 2

        # Count by application
        sabnzbd_count = await best_practices_repository.count(application="sabnzbd")
        assert sabnzbd_count == 1


class TestBestPracticesRepositoryUpdate:
    """Test suite for updating best practices."""

    @pytest.mark.asyncio
    async def test_update_practice(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test updating an existing practice."""
        created = await best_practices_repository.create(sample_practice_data)

        update_data = {"priority": "critical", "explanation": "Updated explanation"}

        updated = await best_practices_repository.update(created.id, update_data)

        assert updated is not None
        assert updated.id == created.id
        assert updated.priority == "critical"
        assert updated.explanation == "Updated explanation"
        assert updated.application == created.application  # Unchanged fields stay same

    @pytest.mark.asyncio
    async def test_update_sets_updated_at_timestamp(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test that updating a practice updates the updated_at timestamp."""
        created = await best_practices_repository.create(sample_practice_data)
        original_updated_at = created.updated_at

        # Small delay to ensure timestamp changes
        import asyncio

        await asyncio.sleep(0.1)

        updated = await best_practices_repository.update(created.id, {"priority": "low"})

        assert updated.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_non_existing_practice(self, best_practices_repository) -> None:
        """Test updating a practice that doesn't exist."""
        result = await best_practices_repository.update(99999, {"priority": "low"})  # noqa: F841

        assert result is None

    @pytest.mark.asyncio
    async def test_partial_update(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test updating only specific fields."""
        created = await best_practices_repository.create(sample_practice_data)

        # Update only enabled field
        updated = await best_practices_repository.update(created.id, {"enabled": False})

        assert updated.enabled is False
        assert updated.priority == created.priority  # Other fields unchanged
        assert updated.explanation == created.explanation


class TestBestPracticesRepositoryDelete:
    """Test suite for deleting best practices."""

    @pytest.mark.asyncio
    async def test_delete_practice(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test deleting an existing practice."""
        created = await best_practices_repository.create(sample_practice_data)

        result = await best_practices_repository.delete(created.id)  # noqa: F841

        assert result is True

        # Verify it's deleted
        retrieved = await best_practices_repository.get_by_id(created.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_non_existing_practice(self, best_practices_repository) -> None:
        """Test deleting a practice that doesn't exist."""
        result = await best_practices_repository.delete(99999)  # noqa: F841

        assert result is False

    @pytest.mark.asyncio
    async def test_soft_delete_disables_practice(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test soft delete (disabling) a practice."""
        created = await best_practices_repository.create(sample_practice_data)

        result = await best_practices_repository.soft_delete(created.id)  # noqa: F841

        assert result is True

        # Verify it's disabled but still exists
        retrieved = await best_practices_repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.enabled is False


class TestBestPracticesRepositoryBulkOperations:
    """Test suite for bulk operations."""

    @pytest.mark.asyncio
    async def test_bulk_create(self, best_practices_repository, sample_practice_data: dict) -> None:
        """Test creating multiple practices at once."""
        practices_data = [
            sample_practice_data,
            {**sample_practice_data, "setting_name": "setting2"},
            {**sample_practice_data, "setting_name": "setting3"},
        ]

        created_practices = await best_practices_repository.bulk_create(practices_data)

        assert len(created_practices) == 3
        assert all(p.id is not None for p in created_practices)
        assert all(p.created_at is not None for p in created_practices)

    @pytest.mark.asyncio
    async def test_bulk_delete(self, best_practices_repository, sample_practice_data: dict) -> None:
        """Test deleting multiple practices by IDs."""
        practice1 = await best_practices_repository.create(sample_practice_data)
        practice2 = await best_practices_repository.create(
            {**sample_practice_data, "setting_name": "setting2"}
        )

        deleted_count = await best_practices_repository.bulk_delete([practice1.id, practice2.id])

        assert deleted_count == 2

        # Verify they're deleted
        assert await best_practices_repository.get_by_id(practice1.id) is None
        assert await best_practices_repository.get_by_id(practice2.id) is None


class TestBestPracticesRepositoryComplexQueries:
    """Test suite for complex filtering and queries."""

    @pytest.mark.asyncio
    async def test_filter_with_multiple_criteria(
        self, best_practices_repository, sample_practice_data: dict
    ) -> None:
        """Test filtering with multiple criteria."""
        # Create various practices
        await best_practices_repository.create(sample_practice_data)

        await best_practices_repository.create(
            {**sample_practice_data, "priority": "low", "category": "performance"}
        )

        await best_practices_repository.create(
            {**sample_practice_data, "application": "sonarr", "priority": "high"}
        )

        # Filter: sabnzbd + high priority + downloads category
        results = await best_practices_repository.filter(
            application="sabnzbd", category="downloads", priority="high"
        )

        assert len(results) == 1
        assert results[0].application == "sabnzbd"
        assert results[0].category == "downloads"
        assert results[0].priority == "high"

    @pytest.mark.asyncio
    async def test_pagination(self, best_practices_repository, sample_practice_data: dict) -> None:
        """Test paginating results."""
        # Create 5 practices
        for i in range(5):
            await best_practices_repository.create(
                {**sample_practice_data, "setting_name": f"setting{i}"}
            )

        # Get first page (2 items)
        page1 = await best_practices_repository.get_paginated(page=1, page_size=2)

        assert len(page1) == 2

        # Get second page
        page2 = await best_practices_repository.get_paginated(page=2, page_size=2)

        assert len(page2) == 2

        # Verify no overlap
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_ordering(self, best_practices_repository, sample_practice_data: dict) -> None:
        """Test that we can retrieve practices and filter by priority."""
        # Create practices with different priorities
        await best_practices_repository.create({**sample_practice_data, "priority": "low"})
        await best_practices_repository.create({**sample_practice_data, "priority": "critical"})
        await best_practices_repository.create({**sample_practice_data, "priority": "high"})

        # Get all practices
        all_practices = await best_practices_repository.get_all()
        assert len(all_practices) == 3

        # Verify we can get by priority
        critical_practices = await best_practices_repository.get_by_priority(["critical"])
        assert len(critical_practices) == 1
        assert critical_practices[0].priority == "critical"
