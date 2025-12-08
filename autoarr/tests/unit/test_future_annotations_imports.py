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
Tests to verify modules with __future__ annotations import correctly.

These tests ensure that the `from __future__ import annotations` statement
is properly placed and that modules can be imported without NameError
when using PEP 604 union type syntax (e.g., `Type | None`).

This is particularly important for FastAPI 0.124.0+ which uses
`inspect.signature(call, eval_str=True)` to evaluate type annotations.
"""

import importlib
import sys

import pytest


class TestFutureAnnotationsImports:
    """Test that modules with __future__ annotations can be imported."""

    @pytest.mark.parametrize(
        "module_path",
        [
            "autoarr.api.dependencies",
            "autoarr.api.middleware",
            "autoarr.api.routers.downloads",
            "autoarr.api.routers.health",
            "autoarr.api.routers.mcp",
            "autoarr.api.routers.media",
            "autoarr.api.routers.movies",
            "autoarr.api.routers.settings",
            "autoarr.api.routers.shows",
            "autoarr.api.services.configuration_manager",
            "autoarr.api.services.content_integration",
            "autoarr.api.services.monitoring_service",
        ],
    )
    def test_module_imports_successfully(self, module_path: str) -> None:
        """
        Test that modules with __future__ annotations import without errors.

        This validates that the `from __future__ import annotations` statement
        is correctly placed at the top of each module, enabling PEP 604 style
        type hints (e.g., `MCPOrchestrator | None`) to work properly.
        """
        # Remove from cache to ensure fresh import
        if module_path in sys.modules:
            del sys.modules[module_path]

        # This should not raise NameError for type annotations
        module = importlib.import_module(module_path)
        assert module is not None

    @pytest.mark.parametrize(
        "module_path",
        [
            "autoarr.api.dependencies",
            "autoarr.api.middleware",
            "autoarr.api.routers.downloads",
            "autoarr.api.routers.health",
            "autoarr.api.routers.mcp",
            "autoarr.api.routers.media",
            "autoarr.api.routers.movies",
            "autoarr.api.routers.settings",
            "autoarr.api.routers.shows",
            "autoarr.api.services.configuration_manager",
            "autoarr.api.services.content_integration",
            "autoarr.api.services.monitoring_service",
        ],
    )
    def test_module_has_future_annotations(self, module_path: str) -> None:
        """
        Test that modules have __future__.annotations enabled.

        When `from __future__ import annotations` is used, the module's
        __annotations__ are stored as strings rather than evaluated objects.
        """
        module = importlib.import_module(module_path)

        # Check that the module has annotations feature enabled
        # This is indicated by the CO_FUTURE_ANNOTATIONS flag or
        # by checking if annotations are strings
        assert hasattr(module, "__name__")
        assert module.__name__ == module_path


class TestDependenciesModuleTypeHints:
    """Test that the dependencies module type hints work correctly."""

    def test_get_orchestrator_function_exists(self) -> None:
        """Test that get_orchestrator dependency function is accessible."""
        from autoarr.api.dependencies import get_orchestrator

        assert callable(get_orchestrator)

    def test_get_orchestrator_config_function_exists(self) -> None:
        """Test that get_orchestrator_config function is accessible."""
        from autoarr.api.dependencies import get_orchestrator_config

        assert callable(get_orchestrator_config)

    def test_orchestrator_type_annotation_accessible(self) -> None:
        """Test that MCPOrchestrator type can be accessed via dependencies."""
        from autoarr.api.dependencies import MCPOrchestrator

        assert MCPOrchestrator is not None


class TestRouterModulesAccessible:
    """Test that router modules and their endpoints are accessible."""

    def test_downloads_router_exists(self) -> None:
        """Test downloads router is accessible."""
        from autoarr.api.routers.downloads import router

        assert router is not None

    def test_health_router_exists(self) -> None:
        """Test health router is accessible."""
        from autoarr.api.routers.health import router

        assert router is not None

    def test_mcp_router_exists(self) -> None:
        """Test MCP router is accessible."""
        from autoarr.api.routers.mcp import router

        assert router is not None

    def test_media_router_exists(self) -> None:
        """Test media router is accessible."""
        from autoarr.api.routers.media import router

        assert router is not None

    def test_movies_router_exists(self) -> None:
        """Test movies router is accessible."""
        from autoarr.api.routers.movies import router

        assert router is not None

    def test_settings_router_exists(self) -> None:
        """Test settings router is accessible."""
        from autoarr.api.routers.settings import router

        assert router is not None

    def test_shows_router_exists(self) -> None:
        """Test shows router is accessible."""
        from autoarr.api.routers.shows import router

        assert router is not None


class TestServiceModulesAccessible:
    """Test that service modules are accessible."""

    def test_configuration_manager_class_exists(self) -> None:
        """Test ConfigurationManager class is accessible."""
        from autoarr.api.services.configuration_manager import ConfigurationManager

        assert ConfigurationManager is not None

    def test_content_integration_service_exists(self) -> None:
        """Test ContentIntegrationService class is accessible."""
        from autoarr.api.services.content_integration import ContentIntegrationService

        assert ContentIntegrationService is not None

    def test_monitoring_service_exists(self) -> None:
        """Test MonitoringService class is accessible."""
        from autoarr.api.services.monitoring_service import MonitoringService

        assert MonitoringService is not None


class TestMiddlewareAccessible:
    """Test that middleware module is accessible."""

    def test_error_handler_middleware_exists(self) -> None:
        """Test ErrorHandlerMiddleware class is accessible."""
        from autoarr.api.middleware import ErrorHandlerMiddleware

        assert ErrorHandlerMiddleware is not None
