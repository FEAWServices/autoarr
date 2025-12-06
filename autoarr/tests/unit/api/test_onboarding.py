"""Unit tests for onboarding API models and repository logic."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from autoarr.api.database import OnboardingState, OnboardingStateRepository, PremiumWaitlist


class TestOnboardingStateModel:
    """Test cases for OnboardingState SQLAlchemy model."""

    def test_model_fields(self):
        """OnboardingState should have all expected fields."""
        state = OnboardingState(
            id=1,
            completed=True,
            current_step="complete",
            ai_configured=True,
            services_configured=["sabnzbd", "sonarr"],
            skipped_steps=["ai_setup"],
            banner_dismissed=True,
            completed_at=datetime.now(),
        )
        assert state.completed is True
        assert state.current_step == "complete"
        assert state.ai_configured is True
        assert state.services_configured == ["sabnzbd", "sonarr"]
        assert state.skipped_steps == ["ai_setup"]
        assert state.banner_dismissed is True
        assert state.completed_at is not None

    def test_model_with_defaults(self):
        """OnboardingState should use default values when explicitly set."""
        state = OnboardingState(
            id=1,
            completed=False,
            current_step="welcome",
            ai_configured=False,
            services_configured=[],
            skipped_steps=[],
            banner_dismissed=False,
        )
        assert state.completed is False
        assert state.current_step == "welcome"
        assert state.ai_configured is False
        assert state.services_configured == []
        assert state.skipped_steps == []
        assert state.banner_dismissed is False


class TestOnboardingStateRepository:
    """Test cases for OnboardingStateRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_db(self, mock_session):
        """Create a mock database with session context manager."""
        from contextlib import asynccontextmanager

        db = MagicMock()

        @asynccontextmanager
        async def mock_session_context():
            yield mock_session

        db.session = mock_session_context
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository with mock database."""
        return OnboardingStateRepository(mock_db)

    async def test_get_or_create_state_returns_existing(self, repository, mock_session):
        """get_or_create_state should return existing state if found."""
        existing_state = OnboardingState(id=1, completed=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.get_or_create_state()

        assert result.completed is True
        mock_session.add.assert_not_called()

    async def test_get_or_create_state_creates_new(self, repository, mock_session):
        """get_or_create_state should create new state if none exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_or_create_state()

        assert result.completed is False
        assert result.current_step == "welcome"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_update_step(self, repository, mock_session):
        """update_step should update the current_step field."""
        existing_state = OnboardingState(id=1, current_step="welcome")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.update_step("ai_setup")

        assert result.current_step == "ai_setup"
        mock_session.commit.assert_called_once()

    async def test_skip_step(self, repository, mock_session):
        """skip_step should add step to skipped_steps list."""
        existing_state = OnboardingState(id=1, skipped_steps=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.skip_step("ai_setup")

        assert "ai_setup" in result.skipped_steps
        mock_session.commit.assert_called_once()

    async def test_skip_step_idempotent(self, repository, mock_session):
        """skip_step should not duplicate steps."""
        existing_state = OnboardingState(id=1, skipped_steps=["ai_setup"])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.skip_step("ai_setup")

        assert result.skipped_steps.count("ai_setup") == 1

    async def test_set_ai_configured(self, repository, mock_session):
        """set_ai_configured should update ai_configured field."""
        existing_state = OnboardingState(id=1, ai_configured=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.set_ai_configured(True)

        assert result.ai_configured is True
        mock_session.commit.assert_called_once()

    async def test_add_configured_service(self, repository, mock_session):
        """add_configured_service should add service to list."""
        existing_state = OnboardingState(id=1, services_configured=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.add_configured_service("sabnzbd")

        assert "sabnzbd" in result.services_configured
        mock_session.commit.assert_called_once()

    async def test_add_configured_service_idempotent(self, repository, mock_session):
        """add_configured_service should not duplicate services."""
        existing_state = OnboardingState(id=1, services_configured=["sabnzbd"])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.add_configured_service("sabnzbd")

        assert result.services_configured.count("sabnzbd") == 1

    async def test_complete_onboarding(self, repository, mock_session):
        """complete_onboarding should set completed and timestamp."""
        existing_state = OnboardingState(id=1, completed=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.complete_onboarding()

        assert result.completed is True
        assert result.completed_at is not None
        mock_session.commit.assert_called_once()

    async def test_dismiss_banner(self, repository, mock_session):
        """dismiss_banner should update banner_dismissed field."""
        existing_state = OnboardingState(id=1, banner_dismissed=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.dismiss_banner()

        assert result.banner_dismissed is True
        mock_session.commit.assert_called_once()

    async def test_reset_onboarding(self, repository, mock_session):
        """reset_onboarding should restore all fields to defaults."""
        existing_state = OnboardingState(
            id=1,
            completed=True,
            current_step="complete",
            ai_configured=True,
            services_configured=["sabnzbd"],
            skipped_steps=["ai_setup"],
            banner_dismissed=True,
            completed_at=datetime.now(),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.reset_onboarding()

        assert result.completed is False
        assert result.current_step == "welcome"
        assert result.ai_configured is False
        assert result.services_configured == []
        assert result.skipped_steps == []
        assert result.banner_dismissed is False
        assert result.completed_at is None
        mock_session.commit.assert_called_once()

    async def test_skip_onboarding(self, repository, mock_session):
        """skip_onboarding should mark all steps as skipped."""
        existing_state = OnboardingState(id=1, completed=False, skipped_steps=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_session.execute.return_value = mock_result

        result = await repository.skip_onboarding()

        assert result.completed is True
        assert "welcome" in result.skipped_steps
        assert "ai_setup" in result.skipped_steps
        assert "service_selection" in result.skipped_steps
        assert "service_config" in result.skipped_steps
        mock_session.commit.assert_called_once()


class TestPremiumWaitlistModel:
    """Test cases for PremiumWaitlist SQLAlchemy model."""

    def test_waitlist_entry_fields(self):
        """PremiumWaitlist should have expected fields."""
        entry = PremiumWaitlist(
            email="test@example.com",
            source="onboarding",
        )
        assert entry.email == "test@example.com"
        assert entry.source == "onboarding"

    def test_waitlist_default_source(self):
        """PremiumWaitlist should have default source if not provided."""
        entry = PremiumWaitlist(email="test@example.com")
        assert entry.source is None or entry.source == ""
