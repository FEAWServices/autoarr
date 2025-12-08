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

"""Tests for LLM settings API endpoints and database model."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from autoarr.api.database import Database, LLMSettings, LLMSettingsRepository


class TestLLMSettingsModel:
    """Tests for LLMSettings database model."""

    def test_llm_settings_model_exists(self):
        """Test that LLMSettings model can be instantiated."""
        # SQLAlchemy defaults only apply when inserting to DB
        # So we just verify the model can be created with explicit values
        settings = LLMSettings(
            id=1,
            enabled=True,
            provider="openrouter",
            api_key="",
            selected_model="anthropic/claude-3.5-sonnet",
            max_tokens=4096,
            timeout=60.0,
        )

        assert settings.enabled is True
        assert settings.provider == "openrouter"
        assert settings.api_key == ""
        assert settings.selected_model == "anthropic/claude-3.5-sonnet"
        assert settings.max_tokens == 4096
        assert settings.timeout == 60.0

    def test_llm_settings_custom_values(self):
        """Test creating LLM settings with custom values."""
        settings = LLMSettings(
            id=1,
            enabled=False,
            provider="openrouter",
            api_key="sk-or-test-key",
            selected_model="openai/gpt-4o",
            max_tokens=8192,
            timeout=120.0,
        )

        assert settings.enabled is False
        assert settings.api_key == "sk-or-test-key"
        assert settings.selected_model == "openai/gpt-4o"
        assert settings.max_tokens == 8192
        assert settings.timeout == 120.0


class TestLLMSettingsRepository:
    """Tests for LLMSettingsRepository."""

    @pytest.fixture
    async def db(self, tmp_path):
        """Create a test database."""
        db_path = tmp_path / "test.db"
        db = Database(f"sqlite+aiosqlite:///{db_path}")
        await db.init_db()
        yield db

    @pytest.fixture
    def repo(self, db):
        """Create a repository instance."""
        return LLMSettingsRepository(db)

    @pytest.mark.asyncio
    async def test_get_settings_returns_none_when_not_set(self, repo):
        """Test getting settings when none exist."""
        settings = await repo.get_settings()

        # Should return None or create default settings
        # depending on implementation choice
        assert settings is None or isinstance(settings, LLMSettings)

    @pytest.mark.asyncio
    async def test_save_llm_settings(self, repo):
        """Test saving LLM settings to database."""
        settings = await repo.save_settings(
            enabled=True,
            api_key="sk-or-test-key-12345",
            selected_model="anthropic/claude-3.5-sonnet",
            max_tokens=4096,
            timeout=60.0,
        )

        assert settings.enabled is True
        assert settings.api_key == "sk-or-test-key-12345"
        assert settings.selected_model == "anthropic/claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_update_llm_settings(self, repo):
        """Test updating existing LLM settings."""
        # First save
        await repo.save_settings(
            enabled=True,
            api_key="sk-or-old-key",
            selected_model="anthropic/claude-3.5-sonnet",
            max_tokens=4096,
            timeout=60.0,
        )

        # Update
        settings = await repo.save_settings(
            enabled=False,
            api_key="sk-or-new-key",
            selected_model="openai/gpt-4o",
            max_tokens=8192,
            timeout=120.0,
        )

        assert settings.enabled is False
        assert settings.api_key == "sk-or-new-key"
        assert settings.selected_model == "openai/gpt-4o"
        assert settings.max_tokens == 8192

    @pytest.mark.asyncio
    async def test_get_settings_after_save(self, repo):
        """Test retrieving settings after saving."""
        await repo.save_settings(
            enabled=True,
            api_key="sk-or-test-key",
            selected_model="anthropic/claude-3.5-sonnet",
            max_tokens=4096,
            timeout=60.0,
        )

        settings = await repo.get_settings()

        assert settings is not None
        assert settings.api_key == "sk-or-test-key"


class TestLLMSettingsEndpoints:
    """Tests for LLM settings API endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        return MagicMock()

    @pytest.fixture
    def mock_llm_repo(self):
        """Create a mock LLM settings repository."""
        repo = MagicMock(spec=LLMSettingsRepository)
        return repo

    @pytest.mark.asyncio
    async def test_get_llm_settings(self, mock_llm_repo):
        """Test GET /api/v1/settings/llm endpoint."""
        from autoarr.api.routers.settings import get_llm_settings

        # Mock settings
        mock_settings = LLMSettings(
            enabled=True,
            api_key="sk-or-test-key-12345",
            selected_model="anthropic/claude-3.5-sonnet",
            max_tokens=4096,
            timeout=60.0,
        )
        mock_llm_repo.get_settings = AsyncMock(return_value=mock_settings)

        # Mock the provider for models
        with patch("autoarr.api.routers.settings.OpenRouterProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.get_models = AsyncMock(return_value=[])
            mock_provider.is_available = AsyncMock(return_value=True)
            mock_provider_class.return_value = mock_provider

            response = await get_llm_settings(llm_repo=mock_llm_repo)

            assert response.enabled is True
            assert response.provider == "openrouter"
            # API key should be masked (format: first4...last4)
            assert "..." in response.api_key_masked or response.api_key_masked == "****"
            assert response.selected_model == "anthropic/claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_get_llm_settings_masked_api_key(self, mock_llm_repo):
        """Test that API key is masked in response."""
        from autoarr.api.routers.settings import mask_api_key

        # Test masking
        masked = mask_api_key("sk-or-v1-abcdefghijklmnop")
        assert masked.startswith("sk-o")
        assert masked.endswith("mnop")
        assert "****" in masked or "..." in masked

    @pytest.mark.asyncio
    async def test_put_llm_settings(self, mock_llm_repo):
        """Test PUT /api/v1/settings/llm endpoint."""
        from autoarr.api.routers.settings import LLMConfig, update_llm_settings

        mock_llm_repo.save_settings = AsyncMock(
            return_value=LLMSettings(
                enabled=True,
                api_key="sk-or-new-key",
                selected_model="openai/gpt-4o",
                max_tokens=8192,
                timeout=120.0,
            )
        )

        config = LLMConfig(
            enabled=True,
            api_key="sk-or-new-key",
            selected_model="openai/gpt-4o",
            max_tokens=8192,
            timeout=120.0,
        )

        response = await update_llm_settings(config=config, llm_repo=mock_llm_repo)

        assert response.success is True
        mock_llm_repo.save_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_llm_models(self, mock_llm_repo):
        """Test GET /api/v1/settings/llm/models endpoint."""
        from autoarr.api.routers.settings import get_llm_models
        from autoarr.shared.llm.openrouter_provider import OpenRouterModel

        mock_models = [
            OpenRouterModel(
                id="anthropic/claude-3.5-sonnet",
                name="Claude 3.5 Sonnet",
                context_length=200000,
                pricing={"prompt": 0.000003, "completion": 0.000015},
            ),
            OpenRouterModel(
                id="openai/gpt-4o",
                name="GPT-4o",
                context_length=128000,
                pricing={"prompt": 0.000005, "completion": 0.000015},
            ),
        ]

        # Mock repository returning settings with API key
        mock_settings = LLMSettings(
            enabled=True,
            api_key="sk-or-test-key",
            selected_model="anthropic/claude-3.5-sonnet",
            max_tokens=4096,
            timeout=60.0,
        )
        mock_llm_repo.get_settings = AsyncMock(return_value=mock_settings)

        with patch("autoarr.api.routers.settings.OpenRouterProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.get_models = AsyncMock(return_value=mock_models)
            mock_provider_class.return_value = mock_provider

            models = await get_llm_models(llm_repo=mock_llm_repo)

            assert len(models) == 2
            assert models[0].id == "anthropic/claude-3.5-sonnet"
            assert models[0].prompt_price == 0.000003

    @pytest.mark.asyncio
    async def test_test_llm_connection_success(self, mock_llm_repo):
        """Test POST /api/v1/settings/test/llm endpoint - success."""
        from autoarr.api.routers.settings import TestLLMConnectionRequest, test_llm_connection

        with patch("autoarr.api.routers.settings.OpenRouterProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.is_available = AsyncMock(return_value=True)
            mock_provider_class.return_value = mock_provider

            request = TestLLMConnectionRequest(api_key="sk-or-valid-key")
            response = await test_llm_connection(request=request)

            assert response.success is True
            assert "Connected" in response.message or response.message == ""

    @pytest.mark.asyncio
    async def test_test_llm_connection_failure(self, mock_llm_repo):
        """Test POST /api/v1/settings/test/llm endpoint - failure."""
        from autoarr.api.routers.settings import TestLLMConnectionRequest, test_llm_connection

        with patch("autoarr.api.routers.settings.OpenRouterProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.is_available = AsyncMock(return_value=False)
            mock_provider_class.return_value = mock_provider

            request = TestLLMConnectionRequest(api_key="sk-or-invalid-key")
            response = await test_llm_connection(request=request)

            assert response.success is False


class TestLLMRouteOrdering:
    """Tests to ensure LLM routes are not caught by /{service} catch-all route.

    This is a regression test for the bug where /llm was matched by /{service}
    resulting in 'Service llm not found' error.
    """

    @pytest.mark.asyncio
    async def test_llm_routes_come_before_service_routes(self):
        """Verify that /llm routes are defined before /{service} routes."""
        from autoarr.api.routers.settings import router

        # Get all routes from the router
        routes = list(router.routes)
        route_paths = [r.path for r in routes if hasattr(r, "path")]

        # Find indices of key routes
        llm_index = None
        service_param_index = None

        for i, path in enumerate(route_paths):
            if path == "/llm" and llm_index is None:
                llm_index = i
            if path == "/{service}" and service_param_index is None:
                service_param_index = i

        # LLM routes must come before /{service} routes
        assert llm_index is not None, "/llm route not found"
        assert service_param_index is not None, "/{service} route not found"
        assert llm_index < service_param_index, (
            f"/llm route (index {llm_index}) must come before "
            f"/{{service}} route (index {service_param_index})"
        )

    @pytest.mark.asyncio
    async def test_llm_models_route_comes_before_service_routes(self):
        """Verify that /llm/models route is defined before /{service} routes."""
        from autoarr.api.routers.settings import router

        routes = list(router.routes)
        route_paths = [r.path for r in routes if hasattr(r, "path")]

        llm_models_index = None
        service_param_index = None

        for i, path in enumerate(route_paths):
            if path == "/llm/models" and llm_models_index is None:
                llm_models_index = i
            if path == "/{service}" and service_param_index is None:
                service_param_index = i

        assert llm_models_index is not None, "/llm/models route not found"
        assert service_param_index is not None, "/{service} route not found"
        assert llm_models_index < service_param_index, (
            f"/llm/models route (index {llm_models_index}) must come before "
            f"/{{service}} route (index {service_param_index})"
        )

    @pytest.mark.asyncio
    async def test_test_llm_route_comes_before_test_service_routes(self):
        """Verify that /test/llm route is defined before /test/{service} routes."""
        from autoarr.api.routers.settings import router

        routes = list(router.routes)
        route_paths = [r.path for r in routes if hasattr(r, "path")]

        test_llm_index = None
        test_service_param_index = None

        for i, path in enumerate(route_paths):
            if path == "/test/llm" and test_llm_index is None:
                test_llm_index = i
            if path == "/test/{service}" and test_service_param_index is None:
                test_service_param_index = i

        assert test_llm_index is not None, "/test/llm route not found"
        assert test_service_param_index is not None, "/test/{service} route not found"
        assert test_llm_index < test_service_param_index, (
            f"/test/llm route (index {test_llm_index}) must come before "
            f"/test/{{service}} route (index {test_service_param_index})"
        )
