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
Unit tests for the SABnzbd Tool Provider.

Tests version-aware tool filtering and execution for SABnzbd API operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.api.services.tool_providers.sabnzbd_provider import SABnzbdToolProvider

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_sabnzbd_client():
    """Create a mock SABnzbd client."""
    client = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    client.get_version = AsyncMock(return_value={"version": "4.2.0"})
    client.get_queue = AsyncMock(return_value={"queue": {"slots": [], "paused": False}})
    client.get_history = AsyncMock(return_value={"history": {"slots": []}})
    client.get_status = AsyncMock(
        return_value={
            "speed": "10.5 M",
            "diskspace1": "500 G",
            "paused": False,
        }
    )
    client.pause_queue = AsyncMock(return_value={"status": True})
    client.resume_queue = AsyncMock(return_value={"status": True})
    client.pause_download = AsyncMock(return_value={"status": True})
    client.resume_download = AsyncMock(return_value={"status": True})
    client.retry_download = AsyncMock(return_value={"status": True})
    client.delete_download = AsyncMock(return_value={"status": True})
    client.get_config = AsyncMock(return_value={"misc": {"bandwidth_max": 0}})
    client.set_config = AsyncMock(return_value={"status": True})
    return client


@pytest.fixture
def provider_with_client(mock_sabnzbd_client):
    """Create a SABnzbd tool provider with a mock client."""
    provider = SABnzbdToolProvider(client=mock_sabnzbd_client)
    provider._version = "4.2.0"
    provider._connected = True
    return provider


# =============================================================================
# Service Name Tests
# =============================================================================


class TestSABnzbdToolProviderBasics:
    """Basic tests for SABnzbd tool provider."""

    def test_service_name(self):
        """Test that service name is correct."""
        provider = SABnzbdToolProvider()
        assert provider.service_name == "sabnzbd"


# =============================================================================
# Version-Aware Tool Tests
# =============================================================================


class TestSABnzbdVersionAwareTools:
    """Tests for version-aware tool filtering."""

    def test_get_tools_sabnzbd_2x(self):
        """Test tools available for SABnzbd 2.x."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="2.3.5")

        tool_names = [t.name for t in tools]

        # Core tools should be available
        assert "sabnzbd_get_queue" in tool_names
        assert "sabnzbd_get_history" in tool_names
        assert "sabnzbd_get_status" in tool_names
        assert "sabnzbd_pause_queue" in tool_names
        assert "sabnzbd_resume_queue" in tool_names
        assert "sabnzbd_retry_download" in tool_names
        assert "sabnzbd_get_config" in tool_names
        assert "sabnzbd_set_config" in tool_names

        # SABnzbd 3.x+ tools should NOT be available
        assert "sabnzbd_set_direct_unpack" not in tool_names
        assert "sabnzbd_set_propagation_delay" not in tool_names

        # SABnzbd 4.x+ tools should NOT be available
        assert "sabnzbd_set_deobfuscate" not in tool_names

    def test_get_tools_sabnzbd_3x(self):
        """Test tools available for SABnzbd 3.x."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="3.5.0")

        tool_names = [t.name for t in tools]

        # Core tools should be available
        assert "sabnzbd_get_queue" in tool_names
        assert "sabnzbd_get_history" in tool_names

        # SABnzbd 3.x+ tools should be available
        assert "sabnzbd_set_direct_unpack" in tool_names
        assert "sabnzbd_set_propagation_delay" in tool_names

        # SABnzbd 4.x+ tools should NOT be available
        assert "sabnzbd_set_deobfuscate" not in tool_names

    def test_get_tools_sabnzbd_4x(self):
        """Test tools available for SABnzbd 4.x."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="4.2.0")

        tool_names = [t.name for t in tools]

        # All core tools should be available
        assert "sabnzbd_get_queue" in tool_names
        assert "sabnzbd_get_history" in tool_names
        assert "sabnzbd_pause_queue" in tool_names
        assert "sabnzbd_resume_queue" in tool_names

        # SABnzbd 3.x+ tools should be available
        assert "sabnzbd_set_direct_unpack" in tool_names
        assert "sabnzbd_set_propagation_delay" in tool_names

        # SABnzbd 4.x+ tools should be available
        assert "sabnzbd_set_deobfuscate" in tool_names

    def test_get_tools_returns_correct_tool_count_2x(self):
        """Test correct number of tools for SABnzbd 2.x."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="2.0.0")

        # Core tools only (no 3.x or 4.x features)
        # 23 tools available since SABnzbd 2.0
        assert len(tools) == 23

    def test_get_tools_returns_correct_tool_count_3x(self):
        """Test correct number of tools for SABnzbd 3.x."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="3.0.0")

        # Core tools (23) + 3.x features (2) = 25 tools
        assert len(tools) == 25

    def test_get_tools_returns_correct_tool_count_4x(self):
        """Test correct number of tools for SABnzbd 4.x."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="4.0.0")

        # Core tools (23) + 3.x features (2) + 4.x features (1) = 26 tools
        assert len(tools) == 26


# =============================================================================
# Tool Definition Tests
# =============================================================================


class TestSABnzbdToolDefinitions:
    """Tests for tool definition properties."""

    def test_tools_have_correct_service_name(self):
        """Test all tools have correct service name."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="4.0.0")

        for tool in tools:
            assert tool.service == "sabnzbd"

    def test_tools_have_descriptions(self):
        """Test all tools have descriptions."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="4.0.0")

        for tool in tools:
            assert tool.description
            assert len(tool.description) > 10

    def test_tools_have_valid_parameters(self):
        """Test all tools have valid parameter schemas."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="4.0.0")

        for tool in tools:
            assert "type" in tool.parameters
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters

    def test_required_parameters_are_specified(self):
        """Test tools with required parameters specify them correctly."""
        provider = SABnzbdToolProvider()
        tools = provider.get_tools(version="4.0.0")

        # Find tools that require nzo_id
        nzo_tools = [
            t
            for t in tools
            if t.name
            in [
                "sabnzbd_pause_download",
                "sabnzbd_resume_download",
                "sabnzbd_retry_download",
                "sabnzbd_delete_download",
            ]
        ]

        for tool in nzo_tools:
            assert "nzo_id" in tool.parameters.get("required", [])


# =============================================================================
# Tool Execution Tests
# =============================================================================


class TestSABnzbdToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_get_queue(self, provider_with_client, mock_sabnzbd_client):
        """Test executing get_queue tool."""
        result = await provider_with_client.execute("sabnzbd_get_queue", {"start": 0, "limit": 10})

        assert result.success is True
        mock_sabnzbd_client.get_queue.assert_called_once_with(start=0, limit=10)

    @pytest.mark.asyncio
    async def test_execute_get_history(self, provider_with_client, mock_sabnzbd_client):
        """Test executing get_history tool."""
        result = await provider_with_client.execute(
            "sabnzbd_get_history",
            {"start": 0, "limit": 20, "failed_only": True, "category": "movies"},
        )

        assert result.success is True
        mock_sabnzbd_client.get_history.assert_called_once_with(
            start=0, limit=20, failed_only=True, category="movies"
        )

    @pytest.mark.asyncio
    async def test_execute_get_status(self, provider_with_client, mock_sabnzbd_client):
        """Test executing get_status tool."""
        result = await provider_with_client.execute("sabnzbd_get_status", {})

        assert result.success is True
        mock_sabnzbd_client.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_pause_queue(self, provider_with_client, mock_sabnzbd_client):
        """Test executing pause_queue tool."""
        result = await provider_with_client.execute("sabnzbd_pause_queue", {})

        assert result.success is True
        mock_sabnzbd_client.pause_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_resume_queue(self, provider_with_client, mock_sabnzbd_client):
        """Test executing resume_queue tool."""
        result = await provider_with_client.execute("sabnzbd_resume_queue", {})

        assert result.success is True
        mock_sabnzbd_client.resume_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_pause_download(self, provider_with_client, mock_sabnzbd_client):
        """Test executing pause_download tool."""
        result = await provider_with_client.execute(
            "sabnzbd_pause_download", {"nzo_id": "SABnzbd_nzo_abc123"}
        )

        assert result.success is True
        mock_sabnzbd_client.pause_download.assert_called_once_with("SABnzbd_nzo_abc123")

    @pytest.mark.asyncio
    async def test_execute_resume_download(self, provider_with_client, mock_sabnzbd_client):
        """Test executing resume_download tool."""
        result = await provider_with_client.execute(
            "sabnzbd_resume_download", {"nzo_id": "SABnzbd_nzo_abc123"}
        )

        assert result.success is True
        mock_sabnzbd_client.resume_download.assert_called_once_with("SABnzbd_nzo_abc123")

    @pytest.mark.asyncio
    async def test_execute_retry_download(self, provider_with_client, mock_sabnzbd_client):
        """Test executing retry_download tool."""
        result = await provider_with_client.execute(
            "sabnzbd_retry_download", {"nzo_id": "SABnzbd_nzo_failed123"}
        )

        assert result.success is True
        mock_sabnzbd_client.retry_download.assert_called_once_with("SABnzbd_nzo_failed123")

    @pytest.mark.asyncio
    async def test_execute_delete_download(self, provider_with_client, mock_sabnzbd_client):
        """Test executing delete_download tool."""
        result = await provider_with_client.execute(
            "sabnzbd_delete_download",
            {"nzo_id": "SABnzbd_nzo_abc123", "delete_files": True},
        )

        assert result.success is True
        mock_sabnzbd_client.delete_download.assert_called_once_with(
            "SABnzbd_nzo_abc123", delete_files=True
        )

    @pytest.mark.asyncio
    async def test_execute_get_config(self, provider_with_client, mock_sabnzbd_client):
        """Test executing get_config tool."""
        result = await provider_with_client.execute("sabnzbd_get_config", {"section": "misc"})

        assert result.success is True
        mock_sabnzbd_client.get_config.assert_called_once_with(section="misc")

    @pytest.mark.asyncio
    async def test_execute_set_config(self, provider_with_client, mock_sabnzbd_client):
        """Test executing set_config tool."""
        result = await provider_with_client.execute(
            "sabnzbd_set_config",
            {"section": "misc", "keyword": "bandwidth_max", "value": "50M"},
        )

        assert result.success is True
        mock_sabnzbd_client.set_config.assert_called_once_with("misc", "bandwidth_max", "50M")

    @pytest.mark.asyncio
    async def test_execute_set_direct_unpack(self, provider_with_client, mock_sabnzbd_client):
        """Test executing set_direct_unpack tool (3.x+)."""
        result = await provider_with_client.execute("sabnzbd_set_direct_unpack", {"enabled": True})

        assert result.success is True
        mock_sabnzbd_client.set_config.assert_called_once_with("misc", "direct_unpack", "1")

    @pytest.mark.asyncio
    async def test_execute_set_propagation_delay(self, provider_with_client, mock_sabnzbd_client):
        """Test executing set_propagation_delay tool (3.x+)."""
        result = await provider_with_client.execute(
            "sabnzbd_set_propagation_delay", {"minutes": 30}
        )

        assert result.success is True
        mock_sabnzbd_client.set_config.assert_called_once_with("misc", "propagation_delay", "30")

    @pytest.mark.asyncio
    async def test_execute_set_deobfuscate(self, provider_with_client, mock_sabnzbd_client):
        """Test executing set_deobfuscate tool (4.x+)."""
        result = await provider_with_client.execute("sabnzbd_set_deobfuscate", {"enabled": False})

        assert result.success is True
        mock_sabnzbd_client.set_config.assert_called_once_with(
            "misc", "deobfuscate_final_filenames", "0"
        )


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestSABnzbdErrorHandling:
    """Tests for error handling in the provider."""

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, provider_with_client):
        """Test executing an unknown tool returns error."""
        result = await provider_with_client.execute("sabnzbd_nonexistent_tool", {})

        assert result.success is False
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_missing_required_parameter(self, provider_with_client):
        """Test executing tool without required parameters."""
        result = await provider_with_client.execute("sabnzbd_pause_download", {})

        assert result.success is False
        assert "nzo_id" in result.error.lower() or "required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_without_client(self):
        """Test executing tool without client configured."""
        provider = SABnzbdToolProvider()
        result = await provider.execute("sabnzbd_get_queue", {})

        assert result.success is False
        assert "not configured" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_propagation_delay_invalid_range(self, provider_with_client):
        """Test propagation delay validates range."""
        result = await provider_with_client.execute(
            "sabnzbd_set_propagation_delay", {"minutes": 2000}  # > 1440
        )

        assert result.success is False
        assert "minutes" in result.error.lower()


# =============================================================================
# Service Info Tests
# =============================================================================


class TestSABnzbdServiceInfo:
    """Tests for service info retrieval."""

    @pytest.mark.asyncio
    async def test_is_available_with_client(self, provider_with_client, mock_sabnzbd_client):
        """Test is_available returns True when client is healthy."""
        result = await provider_with_client.is_available()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_without_client(self):
        """Test is_available returns False without client."""
        provider = SABnzbdToolProvider()
        result = await provider.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_service_info_with_client(self, provider_with_client, mock_sabnzbd_client):
        """Test get_service_info returns complete info."""
        info = await provider_with_client.get_service_info()

        assert info.name == "sabnzbd"
        assert info.connected is True
        assert info.healthy is True
        assert info.version == "4.2.0"
        assert "queue" in info.capabilities
        assert "history" in info.capabilities

    @pytest.mark.asyncio
    async def test_get_service_info_without_client(self):
        """Test get_service_info without client."""
        provider = SABnzbdToolProvider()
        info = await provider.get_service_info()

        assert info.name == "sabnzbd"
        assert info.connected is False
        assert info.healthy is False
