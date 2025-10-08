"""
Unit tests for Best Practices database models.

Following TDD (Red-Green-Refactor):
- These tests are written FIRST before implementation
- They define the expected behavior of the BestPractice model
- They should all FAIL initially until implementation is complete
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


@pytest.fixture
def sample_best_practice_data() -> dict:
    """Sample data for creating a best practice."""
    return {
        "application": "sabnzbd",
        "category": "downloads",
        "setting_name": "incomplete_dir",
        "setting_path": "misc.incomplete_dir",
        "recommended_value": '{"type": "not_empty", "description": "Separate directory"}',
        "current_check_type": "not_empty",
        "explanation": "Using a separate incomplete directory prevents issues",
        "priority": "high",
        "impact": "Incomplete downloads may be processed incorrectly",
        "documentation_url": "https://sabnzbd.org/wiki/configuration/",
        "version_added": "1.0.0",
        "enabled": True,
    }


class TestBestPracticePydanticModel:
    """Test suite for BestPractice Pydantic model validation."""

    def test_create_valid_best_practice(self, sample_best_practice_data: dict) -> None:
        """Test creating a valid best practice with all required fields."""
        from autoarr.api.models import BestPracticeBase

        practice = BestPracticeBase(**sample_best_practice_data)

        assert practice.application == "sabnzbd"
        assert practice.category == "downloads"
        assert practice.setting_name == "incomplete_dir"
        assert practice.priority == "high"
        assert practice.enabled is True

    def test_application_must_be_valid_service(self, sample_best_practice_data: dict) -> None:
        """Test that application must be one of the supported services."""
        from autoarr.api.models import BestPracticeBase

        # Valid applications
        for app in ["sabnzbd", "sonarr", "radarr", "plex"]:
            data = {**sample_best_practice_data, "application": app}
            practice = BestPracticeBase(**data)
            assert practice.application == app

        # Invalid application should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            invalid_data = {**sample_best_practice_data, "application": "invalid_app"}
            BestPracticeBase(**invalid_data)
        assert "application" in str(exc_info.value)

    def test_priority_must_be_valid_level(self, sample_best_practice_data: dict) -> None:
        """Test that priority must be one of the valid levels."""
        from autoarr.api.models import BestPracticeBase

        # Valid priorities
        for priority in ["critical", "high", "medium", "low"]:
            data = {**sample_best_practice_data, "priority": priority}
            practice = BestPracticeBase(**data)
            assert practice.priority == priority

        # Invalid priority should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            invalid_data = {**sample_best_practice_data, "priority": "urgent"}
            BestPracticeBase(**invalid_data)
        assert "priority" in str(exc_info.value)

    def test_check_type_must_be_valid(self, sample_best_practice_data: dict) -> None:
        """Test that current_check_type must be one of the valid types."""
        from autoarr.api.models import BestPracticeBase

        valid_types = [
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
        ]

        for check_type in valid_types:
            data = {**sample_best_practice_data, "current_check_type": check_type}
            practice = BestPracticeBase(**data)
            assert practice.current_check_type == check_type

    def test_required_fields_cannot_be_missing(self, sample_best_practice_data: dict) -> None:
        """Test that required fields raise ValidationError when missing."""
        from autoarr.api.models import BestPracticeBase

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
        ]

        for field in required_fields:
            data = sample_best_practice_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                BestPracticeBase(**data)
            assert field in str(exc_info.value)

    def test_optional_fields_can_be_none(self, sample_best_practice_data: dict) -> None:
        """Test that optional fields can be None or omitted."""
        from autoarr.api.models import BestPracticeBase

        # Remove optional fields
        data = sample_best_practice_data.copy()
        data.pop("impact", None)
        data.pop("documentation_url", None)

        practice = BestPracticeBase(**data)
        assert practice.impact is None
        assert practice.documentation_url is None

    def test_enabled_defaults_to_true(self) -> None:
        """Test that enabled field defaults to True if not provided."""
        from autoarr.api.models import BestPracticeBase

        data = {
            "application": "sabnzbd",
            "category": "downloads",
            "setting_name": "test",
            "setting_path": "test.path",
            "recommended_value": '{"type": "test"}',
            "current_check_type": "exists",
            "explanation": "Test explanation",
            "priority": "medium",
            "version_added": "1.0.0",
        }

        practice = BestPracticeBase(**data)
        assert practice.enabled is True

    def test_recommended_value_is_valid_json_string(self, sample_best_practice_data: dict) -> None:
        """Test that recommended_value must be a valid JSON string."""
        from autoarr.api.models import BestPracticeBase
        import json

        practice = BestPracticeBase(**sample_best_practice_data)

        # Should be able to parse as JSON
        parsed = json.loads(practice.recommended_value)
        assert isinstance(parsed, dict)
        assert "type" in parsed

    def test_best_practice_response_includes_timestamps(
        self, sample_best_practice_data: dict
    ) -> None:
        """Test that BestPracticeResponse includes id and timestamps."""
        from autoarr.api.models import BestPracticeResponse

        data = {
            **sample_best_practice_data,
            "id": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        practice = BestPracticeResponse(**data)
        assert practice.id == 1
        assert isinstance(practice.created_at, datetime)
        assert isinstance(practice.updated_at, datetime)


class TestBestPracticeCreate:
    """Test suite for BestPracticeCreate model."""

    def test_create_model_excludes_id_and_timestamps(self, sample_best_practice_data: dict) -> None:
        """Test that create model doesn't include id or timestamps."""
        from autoarr.api.models import BestPracticeCreate

        # Should not have id, created_at, updated_at in create model
        practice = BestPracticeCreate(**sample_best_practice_data)

        # Verify we can't access these fields
        assert not hasattr(practice, "id")
        assert not hasattr(practice, "created_at")
        assert not hasattr(practice, "updated_at")


class TestBestPracticeUpdate:
    """Test suite for BestPracticeUpdate model."""

    def test_update_model_all_fields_optional(self) -> None:
        """Test that all fields are optional in update model."""
        from autoarr.api.models import BestPracticeUpdate

        # Should be able to create with no fields
        practice = BestPracticeUpdate()
        assert practice is not None

        # Should be able to update just priority
        practice = BestPracticeUpdate(priority="low")
        assert practice.priority == "low"

        # Should be able to update just enabled
        practice = BestPracticeUpdate(enabled=False)
        assert practice.enabled is False

    def test_update_validates_values_when_provided(self) -> None:
        """Test that update model validates values when they are provided."""
        from autoarr.api.models import BestPracticeUpdate

        # Invalid priority should raise error
        with pytest.raises(ValidationError):
            BestPracticeUpdate(priority="invalid")

        # Invalid application should raise error
        with pytest.raises(ValidationError):
            BestPracticeUpdate(application="invalid_app")


class TestBestPracticeQueryModels:
    """Test suite for query and filter models."""

    def test_best_practice_filter_model(self) -> None:
        """Test BestPracticeFilter model for querying."""
        from autoarr.api.models import BestPracticeFilter

        # All fields optional
        filter_model = BestPracticeFilter()
        assert filter_model is not None

        # Can filter by application
        filter_model = BestPracticeFilter(application="sabnzbd")
        assert filter_model.application == "sabnzbd"

        # Can filter by multiple criteria
        filter_model = BestPracticeFilter(
            application="sonarr", category="quality", priority="high", enabled=True
        )
        assert filter_model.application == "sonarr"
        assert filter_model.category == "quality"
        assert filter_model.priority == "high"
        assert filter_model.enabled is True

    def test_best_practice_list_response(self) -> None:
        """Test BestPracticeListResponse model."""
        from autoarr.api.models import BestPracticeListResponse, BestPracticeResponse

        practices = [
            BestPracticeResponse(
                id=1,
                application="sabnzbd",
                category="downloads",
                setting_name="test",
                setting_path="test.path",
                recommended_value='{"type": "test"}',
                current_check_type="exists",
                explanation="Test",
                priority="high",
                version_added="1.0.0",
                enabled=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]

        response = BestPracticeListResponse(practices=practices, total=1)
        assert response.total == 1
        assert len(response.practices) == 1
        assert response.practices[0].id == 1
