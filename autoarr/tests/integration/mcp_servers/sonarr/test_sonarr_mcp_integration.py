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
Integration tests for Sonarr MCP Protocol Compliance.

This module validates that the Sonarr MCP Server correctly implements
the Model Context Protocol and integrates properly with the client layer.

Test Coverage Strategy:
- MCP protocol message format validation
- Tool execution through MCP layer
- Error propagation through MCP layer
- End-to-end MCP request/response flow

Target Coverage: 10% of total test suite (E2E layer)
"""

import json

import pytest
from pytest_httpx import HTTPXMock

from autoarr.mcp_servers.mcp_servers.sonarr.client import SonarrClient
from autoarr.mcp_servers.mcp_servers.sonarr.server import SonarrMCPServer

# ============================================================================
# MCP Integration Test Fixtures
# ============================================================================


@pytest.fixture
async def sonarr_mcp_integration_client(httpx_mock: HTTPXMock):
    """Create Sonarr client with HTTP mocking for MCP integration tests."""
    client = SonarrClient(url="http://localhost:8989", api_key="test_mcp_api_key")  # noqa: F841
    yield client
    await client.close()


@pytest.fixture
def sonarr_mcp_server(sonarr_mcp_integration_client):
    """Create Sonarr MCP server for integration testing."""
    return SonarrMCPServer(client=sonarr_mcp_integration_client)


# ============================================================================
# End-to-End MCP Workflow Tests
# ============================================================================


class TestSonarrMCPEndToEnd:
    """End-to-end tests for complete MCP workflows."""

    @pytest.mark.asyncio
    async def test_complete_series_management_via_mcp(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_series_factory: callable,
    ) -> None:
        """
        Test complete series management through MCP tools.

        Workflow: List tools → Search series → Add series → Get series → Delete series
        """
        # Step 1: List available tools
        tools = sonarr_mcp_server._get_tools()

        assert len(tools) == 10
        tool_names = [t.name for t in tools]
        assert "sonarr_search_series" in tool_names
        assert "sonarr_add_series" in tool_names
        assert "sonarr_get_series_by_id" in tool_names
        assert "sonarr_delete_series" in tool_names

        # Step 2: Search for series via MCP
        search_results = [sonarr_series_factory(series_id=0, title="The Expanse", tvdb_id=280619)]
        httpx_mock.add_response(json=search_results)

        search_response = await sonarr_mcp_server._call_tool(
            "sonarr_search_series", {"term": "The Expanse"}
        )

        search_data = json.loads(search_response[0].text)
        assert search_data["success"] is True
        assert len(search_data["data"]) == 1
        tvdb_id = search_data["data"][0]["tvdbId"]

        # Step 3: Add series via MCP
        added_series = sonarr_series_factory(series_id=1, title="The Expanse", tvdb_id=tvdb_id)
        httpx_mock.add_response(status_code=201, json=added_series)

        add_response = await sonarr_mcp_server._call_tool(
            "sonarr_add_series",
            {
                "title": "The Expanse",
                "tvdb_id": tvdb_id,
                "quality_profile_id": 1,
                "root_folder_path": "/tv",
                "monitored": True,
                "season_folder": True,
            },
        )

        add_data = json.loads(add_response[0].text)
        assert add_data["success"] is True
        series_id = add_data["data"]["id"]

        # Step 4: Get series details via MCP
        httpx_mock.add_response(json=added_series)

        get_response = await sonarr_mcp_server._call_tool(
            "sonarr_get_series_by_id", {"series_id": series_id}
        )

        get_data = json.loads(get_response[0].text)
        assert get_data["success"] is True
        assert get_data["data"]["id"] == series_id

        # Step 5: Delete series via MCP
        httpx_mock.add_response(status_code=200, json={})

        delete_response = await sonarr_mcp_server._call_tool(
            "sonarr_delete_series", {"series_id": series_id, "delete_files": True}
        )

        delete_data = json.loads(delete_response[0].text)
        assert delete_data["success"] is True

    @pytest.mark.asyncio
    async def test_episode_search_workflow_via_mcp(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_episode_factory: callable,
        sonarr_command_factory: callable,
        sonarr_queue_factory: callable,
    ) -> None:
        """
        Test episode search and monitoring workflow through MCP.

        Workflow: Get episodes → Search episode → Check queue
        """
        series_id = 1

        # Step 1: Get episodes via MCP
        episodes = [
            sonarr_episode_factory(episode_id=i, series_id=series_id, has_file=False)
            for i in range(1, 4)
        ]
        httpx_mock.add_response(json=episodes)

        episodes_response = await sonarr_mcp_server._call_tool(
            "sonarr_get_episodes", {"series_id": series_id}
        )

        episodes_data = json.loads(episodes_response[0].text)
        assert episodes_data["success"] is True
        assert len(episodes_data["data"]) == 3
        episode_id = episodes_data["data"][0]["id"]

        # Step 2: Search for episode via MCP
        search_command = sonarr_command_factory(command_id=100, name="EpisodeSearch")
        httpx_mock.add_response(status_code=201, json=search_command)

        search_response = await sonarr_mcp_server._call_tool(
            "sonarr_search_episode", {"episode_id": episode_id}
        )

        search_data = json.loads(search_response[0].text)
        assert search_data["success"] is True
        assert search_data["data"]["id"] == 100

        # Step 3: Check queue via MCP
        queue = sonarr_queue_factory(records=1)
        httpx_mock.add_response(json=queue)

        queue_response = await sonarr_mcp_server._call_tool("sonarr_get_queue", {})

        queue_data = json.loads(queue_response[0].text)
        assert queue_data["success"] is True
        assert "records" in queue_data["data"]


# ============================================================================
# MCP Protocol Compliance Tests
# ============================================================================


class TestSonarrMCPProtocolCompliance:
    """Tests validating MCP protocol compliance."""

    @pytest.mark.asyncio
    async def test_mcp_response_format_compliance(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_series_factory: callable,
    ) -> None:
        """Test that all MCP responses follow protocol format."""
        mock_series = [sonarr_series_factory()]
        httpx_mock.add_response(json=mock_series)

        response = await sonarr_mcp_server._call_tool("sonarr_get_series", {})

        # MCP responses should be list of TextContent
        assert isinstance(response, list)
        assert len(response) > 0

        from mcp.types import TextContent

        assert all(isinstance(item, TextContent) for item in response)
        assert all(item.type == "text" for item in response)

        # Content should be valid JSON
        for item in response:
            data = json.loads(item.text)
            assert isinstance(data, dict)
            assert "success" in data

    @pytest.mark.asyncio
    async def test_tool_schema_validation_enforcement(
        self, httpx_mock: HTTPXMock, sonarr_mcp_server: SonarrMCPServer
    ) -> None:
        """Test that tool schemas are enforced."""
        # Try to call tool without required parameter
        response = await sonarr_mcp_server._call_tool(
            "sonarr_get_series_by_id", {}  # Missing required series_id
        )

        response_data = json.loads(response[0].text)
        assert response_data["success"] is False
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_error_responses_follow_mcp_format(
        self, httpx_mock: HTTPXMock, sonarr_mcp_server: SonarrMCPServer
    ) -> None:
        """Test that error responses follow MCP format."""
        # Trigger an error by calling unknown tool
        response = await sonarr_mcp_server._call_tool("unknown_tool", {})

        assert isinstance(response, list)
        assert len(response) == 1

        from mcp.types import TextContent

        assert isinstance(response[0], TextContent)

        error_data = json.loads(response[0].text)
        assert error_data["success"] is False
        assert "error" in error_data
        assert isinstance(error_data["error"], str)


# ============================================================================
# Error Propagation Tests
# ============================================================================


class TestSonarrMCPErrorPropagation:
    """Tests for error propagation through MCP layer."""

    @pytest.mark.asyncio
    async def test_client_error_propagates_through_mcp(
        self, httpx_mock: HTTPXMock, sonarr_mcp_server: SonarrMCPServer
    ) -> None:
        """Test that client errors propagate correctly through MCP layer."""
        # Mock 404 error
        httpx_mock.add_response(status_code=404, json={"message": "Series not found"})

        response = await sonarr_mcp_server._call_tool("sonarr_get_series_by_id", {"series_id": 999})

        response_data = json.loads(response[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "404" in response_data["error"] or "not found" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_validation_error_propagates_through_mcp(
        self, httpx_mock: HTTPXMock, sonarr_mcp_server: SonarrMCPServer
    ) -> None:
        """Test that validation errors propagate through MCP layer."""
        # Mock validation error from Sonarr
        httpx_mock.add_response(
            status_code=400,
            json={
                "message": "Validation failed",
                "errors": [{"propertyName": "tvdbId", "errorMessage": "Required"}],
            },
        )

        response = await sonarr_mcp_server._call_tool(
            "sonarr_add_series",
            {
                "title": "Test",
                "tvdb_id": None,  # Invalid
                "quality_profile_id": 1,
                "root_folder_path": "/tv",
            },
        )

        response_data = json.loads(response[0].text)
        assert response_data["success"] is False

    @pytest.mark.asyncio
    async def test_connection_error_propagates_through_mcp(
        self, httpx_mock: HTTPXMock, sonarr_mcp_server: SonarrMCPServer
    ) -> None:
        """Test that connection errors propagate through MCP layer."""
        from httpx import HTTPError

        httpx_mock.add_exception(HTTPError("Connection refused"))

        response = await sonarr_mcp_server._call_tool("sonarr_get_series", {})

        response_data = json.loads(response[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "connection" in response_data["error"].lower()


# ============================================================================
# Data Transformation Tests
# ============================================================================


class TestSonarrMCPDataTransformation:
    """Tests for data transformation through MCP layer."""

    @pytest.mark.asyncio
    async def test_complex_data_structures_preserved(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_series_factory: callable,
    ) -> None:
        """Test that complex data structures are preserved through MCP."""
        complex_series = sonarr_series_factory(series_id=1, title="Complex Series", season_count=5)
        httpx_mock.add_response(json=complex_series)

        response = await sonarr_mcp_server._call_tool("sonarr_get_series_by_id", {"series_id": 1})

        response_data = json.loads(response[0].text)
        series_data = response_data["data"]

        # Verify nested structures are intact
        assert "seasons" in series_data
        assert len(series_data["seasons"]) == 6
        assert "statistics" in series_data
        assert series_data["statistics"]["seasonCount"] == 5

    @pytest.mark.asyncio
    async def test_paginated_data_preserved(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_wanted_factory: callable,
    ) -> None:
        """Test that paginated data is preserved through MCP."""
        wanted_data = sonarr_wanted_factory(records=10, page=2, page_size=20)
        httpx_mock.add_response(json=wanted_data)

        response = await sonarr_mcp_server._call_tool(
            "sonarr_get_wanted", {"page": 2, "page_size": 20}
        )

        response_data = json.loads(response[0].text)
        result = response_data["data"]  # noqa: F841

        assert result["page"] == 2
        assert result["pageSize"] == 20
        assert result["totalRecords"] == 10
        assert len(result["records"]) == 10


# ============================================================================
# Calendar and Queue MCP Integration Tests
# ============================================================================


class TestSonarrMCPCalendarQueue:
    """Integration tests for calendar and queue through MCP."""

    @pytest.mark.asyncio
    async def test_calendar_retrieval_via_mcp(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_calendar_factory: callable,
    ) -> None:
        """Test calendar retrieval through MCP tools."""
        calendar_data = sonarr_calendar_factory(days=7, episodes_per_day=3)
        httpx_mock.add_response(json=calendar_data)

        response = await sonarr_mcp_server._call_tool(
            "sonarr_get_calendar", {"start_date": "2020-01-01", "end_date": "2020-01-07"}
        )

        response_data = json.loads(response[0].text)
        assert response_data["success"] is True
        assert len(response_data["data"]) == 21  # 7 days * 3 episodes

    @pytest.mark.asyncio
    async def test_wanted_episodes_via_mcp(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_wanted_factory: callable,
    ) -> None:
        """Test wanted/missing episodes retrieval through MCP."""
        wanted_data = sonarr_wanted_factory(records=15, include_series=True)
        httpx_mock.add_response(json=wanted_data)

        response = await sonarr_mcp_server._call_tool(
            "sonarr_get_wanted", {"page": 1, "page_size": 20}
        )

        response_data = json.loads(response[0].text)
        assert response_data["success"] is True
        assert len(response_data["data"]["records"]) == 15
        # Verify series info is included
        assert "series" in response_data["data"]["records"][0]


# ============================================================================
# Concurrent MCP Operations Tests
# ============================================================================


class TestSonarrMCPConcurrency:
    """Tests for concurrent MCP operations."""

    @pytest.mark.asyncio
    async def test_concurrent_mcp_tool_calls(
        self,
        httpx_mock: HTTPXMock,
        sonarr_mcp_server: SonarrMCPServer,
        sonarr_series_factory: callable,
        sonarr_queue_factory: callable,
        sonarr_wanted_factory: callable,
    ) -> None:
        """Test concurrent MCP tool execution."""
        import asyncio

        # Mock responses
        httpx_mock.add_response(json=[sonarr_series_factory()])
        httpx_mock.add_response(json=sonarr_queue_factory())
        httpx_mock.add_response(json=sonarr_wanted_factory())

        # Execute concurrent MCP tool calls
        results = await asyncio.gather(
            sonarr_mcp_server._call_tool("sonarr_get_series", {}),
            sonarr_mcp_server._call_tool("sonarr_get_queue", {}),
            sonarr_mcp_server._call_tool("sonarr_get_wanted", {}),
        )

        assert len(results) == 3
        for result in results:
            data = json.loads(result[0].text)
            assert data["success"] is True
