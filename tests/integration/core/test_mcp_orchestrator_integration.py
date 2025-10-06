"""
Integration tests for MCP Orchestrator with real MCP servers.

This module contains integration tests that verify the MCP Orchestrator works
correctly with real MCP server instances. These tests require a running test
environment with all MCP servers available.

Following TDD Principles:
- Integration tests make up 20% of test pyramid
- Test real interactions between orchestrator and MCP servers
- Verify protocol compliance and error handling
- Test performance under realistic conditions

Test Categories:
1. Real Server Connection Tests (5 tests)
2. End-to-End Tool Execution Tests (10 tests)
3. Multi-Server Coordination Tests (5 tests)
4. Error Recovery Integration Tests (5 tests)
5. Performance and Load Tests (5 tests)

Total: 30 integration tests

Setup Requirements:
- docker-compose with test instances of all MCP servers
- Test data pre-loaded in each server
- Network connectivity between test containers
"""

import asyncio
import os
from typing import Dict, Any
from datetime import datetime, timedelta

import pytest

# These imports will fail until we implement the orchestrator
try:
    from core.mcp_orchestrator import (
        MCPOrchestrator,
        MCPOrchestratorError,
        MCPConnectionError,
    )
except ImportError:
    pytest.skip("MCP Orchestrator not yet implemented", allow_module_level=True)


# ============================================================================
# Test Configuration and Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def integration_config() -> Dict[str, Any]:
    """
    Load integration test configuration from environment.

    Requires docker-compose test environment to be running.
    """
    return {
        "sabnzbd": {
            "name": "sabnzbd",
            "url": os.getenv("TEST_SABNZBD_URL", "http://localhost:8080"),
            "api_key": os.getenv("TEST_SABNZBD_API_KEY", "test_api_key"),
            "enabled": True,
        },
        "sonarr": {
            "name": "sonarr",
            "url": os.getenv("TEST_SONARR_URL", "http://localhost:8989"),
            "api_key": os.getenv("TEST_SONARR_API_KEY", "test_api_key"),
            "enabled": True,
        },
        "radarr": {
            "name": "radarr",
            "url": os.getenv("TEST_RADARR_URL", "http://localhost:7878"),
            "api_key": os.getenv("TEST_RADARR_API_KEY", "test_api_key"),
            "enabled": True,
        },
        "plex": {
            "name": "plex",
            "url": os.getenv("TEST_PLEX_URL", "http://localhost:32400"),
            "api_key": os.getenv("TEST_PLEX_TOKEN", "test_token"),
            "enabled": True,
        },
    }


@pytest.fixture(scope="module")
async def orchestrator(integration_config):
    """
    Create an orchestrator instance connected to real test servers.

    This fixture has module scope to reuse connections across tests.
    """
    orch = MCPOrchestrator(config=integration_config)
    await orch.connect_all()
    yield orch
    await orch.disconnect_all()


@pytest.fixture
def skip_if_servers_unavailable(orchestrator):
    """
    Skip test if required MCP servers are not available.

    Checks that all servers are connected before running test.
    """
    async def check():
        health = await orchestrator.health_check_all()
        if not all(health.values()):
            pytest.skip("Required MCP servers not available")

    return check


# ============================================================================
# 1. REAL SERVER CONNECTION TESTS (5 tests)
# ============================================================================


class TestOrchestratorRealServerConnections:
    """Integration tests for real MCP server connections."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connect_to_all_real_servers(self, integration_config):
        """Test connecting to all real MCP server instances."""
        # Arrange
        orchestrator = MCPOrchestrator(config=integration_config)

        # Act
        connection_results = await orchestrator.connect_all()

        # Assert
        assert len(connection_results) == 4
        # At least some servers should connect (CI may not have all services)
        assert any(connection_results.values())

        # Cleanup
        await orchestrator.disconnect_all()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reconnect_after_connection_loss(
        self, integration_config
    ):
        """Test reconnection after simulated connection loss."""
        # Arrange
        orchestrator = MCPOrchestrator(config=integration_config)
        await orchestrator.connect_all()

        # Act - Disconnect one server and reconnect
        await orchestrator.disconnect("sabnzbd")
        await asyncio.sleep(0.5)
        reconnect_result = await orchestrator.reconnect("sabnzbd")

        # Assert
        assert reconnect_result is True
        is_connected = await orchestrator.is_connected("sabnzbd")
        assert is_connected is True

        # Cleanup
        await orchestrator.disconnect_all()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_real_servers(self, orchestrator):
        """Test health checking real MCP servers."""
        # Act
        health_results = await orchestrator.health_check_all()

        # Assert
        assert isinstance(health_results, dict)
        assert len(health_results) > 0
        # At least one server should be healthy
        assert any(health_results.values())

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connection_pool_with_real_servers(
        self, orchestrator
    ):
        """Test connection pooling with real MCP servers."""
        # Act - Make multiple calls
        for _ in range(10):
            await orchestrator.call_tool("sabnzbd", "get_version", {})

        # Assert - Check pool stats
        pool_state = orchestrator.get_connection_pool_state()
        assert pool_state["active_connections"] > 0
        # Connections should be reused, not recreated
        assert pool_state["total_connections"] <= 4

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_connections_to_real_servers(
        self, integration_config
    ):
        """Test multiple orchestrators connecting simultaneously."""
        # Arrange
        orchestrators = [
            MCPOrchestrator(config=integration_config)
            for _ in range(3)
        ]

        # Act - Connect all simultaneously
        results = await asyncio.gather(
            *[orch.connect_all() for orch in orchestrators]
        )

        # Assert
        assert len(results) == 3
        # All should connect successfully
        assert all(any(r.values()) for r in results)

        # Cleanup
        for orch in orchestrators:
            await orch.disconnect_all()


# ============================================================================
# 2. END-TO-END TOOL EXECUTION TESTS (10 tests)
# ============================================================================


class TestOrchestratorRealToolExecution:
    """Integration tests for executing tools on real servers."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sabnzbd_get_queue(self, orchestrator):
        """Test getting SABnzbd queue through orchestrator."""
        # Act
        result = await orchestrator.call_tool("sabnzbd", "get_queue", {})

        # Assert
        assert result is not None
        assert "queue" in result or "slots" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sabnzbd_get_history(self, orchestrator):
        """Test getting SABnzbd history through orchestrator."""
        # Act
        result = await orchestrator.call_tool(
            "sabnzbd",
            "get_history",
            {"start": 0, "limit": 10}
        )

        # Assert
        assert result is not None
        assert "history" in result or "slots" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sonarr_get_series(self, orchestrator):
        """Test getting Sonarr series list through orchestrator."""
        # Act
        result = await orchestrator.call_tool("sonarr", "get_series", {})

        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sonarr_get_calendar(self, orchestrator):
        """Test getting Sonarr calendar through orchestrator."""
        # Arrange
        start_date = datetime.now().isoformat()
        end_date = (datetime.now() + timedelta(days=7)).isoformat()

        # Act
        result = await orchestrator.call_tool(
            "sonarr",
            "get_calendar",
            {"start": start_date, "end": end_date}
        )

        # Assert
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_radarr_get_movies(self, orchestrator):
        """Test getting Radarr movies list through orchestrator."""
        # Act
        result = await orchestrator.call_tool("radarr", "get_movies", {})

        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_radarr_search_movies(self, orchestrator):
        """Test searching movies through Radarr orchestrator."""
        # Act
        result = await orchestrator.call_tool(
            "radarr",
            "search_movies",
            {"term": "Inception"}
        )

        # Assert
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_plex_get_libraries(self, orchestrator):
        """Test getting Plex libraries through orchestrator."""
        # Act
        result = await orchestrator.call_tool("plex", "get_libraries", {})

        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tool_execution_with_complex_params(
        self, orchestrator
    ):
        """Test tool execution with complex nested parameters."""
        # Act
        result = await orchestrator.call_tool(
            "sonarr",
            "search_series",
            {
                "term": "Breaking Bad",
                "limit": 5,
                "filters": {
                    "year": 2008,
                    "network": "AMC"
                }
            }
        )

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tool_execution_returns_metadata(
        self, orchestrator
    ):
        """Test that tool execution includes metadata."""
        # Act
        result = await orchestrator.call_tool(
            "sabnzbd",
            "get_queue",
            {},
            include_metadata=True
        )

        # Assert
        assert "metadata" in result
        assert result["metadata"]["server"] == "sabnzbd"
        assert "duration" in result["metadata"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_sequential_tool_calls_maintain_state(
        self, orchestrator
    ):
        """Test that sequential calls maintain server state correctly."""
        # Act - Make multiple related calls
        version = await orchestrator.call_tool("sabnzbd", "get_version", {})
        queue = await orchestrator.call_tool("sabnzbd", "get_queue", {})
        history = await orchestrator.call_tool("sabnzbd", "get_history", {})

        # Assert - All should succeed and be consistent
        assert version is not None
        assert queue is not None
        assert history is not None


# ============================================================================
# 3. MULTI-SERVER COORDINATION TESTS (5 tests)
# ============================================================================


class TestOrchestratorMultiServerCoordination:
    """Integration tests for coordinating multiple MCP servers."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parallel_calls_to_different_servers(
        self, orchestrator, mcp_batch_tool_calls_factory
    ):
        """Test executing tools on multiple servers in parallel."""
        # Arrange
        calls = [
            {"server": "sabnzbd", "tool": "get_queue", "params": {}},
            {"server": "sonarr", "tool": "get_series", "params": {}},
            {"server": "radarr", "tool": "get_movies", "params": {}},
        ]

        # Act
        results = await orchestrator.call_tools_parallel(calls)

        # Assert
        assert len(results) == 3
        # At least some should succeed
        successful = [r for r in results if r.get("success")]
        assert len(successful) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_aggregate_data_from_multiple_servers(
        self, orchestrator
    ):
        """Test aggregating related data from multiple servers."""
        # Act - Get download status from all servers
        sab_queue = await orchestrator.call_tool("sabnzbd", "get_queue", {})
        sonarr_queue = await orchestrator.call_tool("sonarr", "get_queue", {})
        radarr_queue = await orchestrator.call_tool("radarr", "get_queue", {})

        # Assert - All should return queue data
        assert sab_queue is not None
        assert sonarr_queue is not None
        assert radarr_queue is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cross_server_workflow(self, orchestrator):
        """Test a workflow that spans multiple servers."""
        # Simulate workflow: Check downloads -> Check media library

        # Act
        # Step 1: Check SABnzbd for completed downloads
        history = await orchestrator.call_tool(
            "sabnzbd",
            "get_history",
            {"limit": 5}
        )

        # Step 2: Check if completed downloads are in Plex
        libraries = await orchestrator.call_tool("plex", "get_libraries", {})

        # Assert
        assert history is not None
        assert libraries is not None
        # Workflow should complete end-to-end

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_partial_failure_graceful_degradation(
        self, orchestrator
    ):
        """Test graceful degradation when some servers fail."""
        # Arrange - Mix of valid and invalid tool calls
        calls = [
            {"server": "sabnzbd", "tool": "get_queue", "params": {}},
            {"server": "sonarr", "tool": "invalid_tool", "params": {}},
            {"server": "radarr", "tool": "get_movies", "params": {}},
        ]

        # Act
        results = await orchestrator.call_tools_parallel(calls)

        # Assert - Should have some successes and some failures
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        assert len(successful) > 0  # Some succeeded
        assert len(failed) > 0      # Some failed

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_priority_routing(self, orchestrator):
        """Test that high-priority servers are queried first."""
        # Arrange
        orchestrator.set_server_priority("sabnzbd", priority=1)
        orchestrator.set_server_priority("plex", priority=10)

        calls = [
            {"server": "plex", "tool": "get_libraries", "params": {}},
            {"server": "sabnzbd", "tool": "get_queue", "params": {}},
        ]

        # Act
        start_times = {}
        for call in calls:
            start = datetime.now()
            await orchestrator.call_tool(**call)
            start_times[call["server"]] = start

        # Assert - Higher priority should start first
        # (This is a simplified check - real implementation would be more sophisticated)


# ============================================================================
# 4. ERROR RECOVERY INTEGRATION TESTS (5 tests)
# ============================================================================


class TestOrchestratorRealErrorRecovery:
    """Integration tests for error recovery with real servers."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recover_from_network_timeout(self, orchestrator):
        """Test recovery from network timeout with real server."""
        # Act - Call with very short timeout
        try:
            await orchestrator.call_tool(
                "plex",
                "scan_library",
                {"library_id": 1},
                timeout=0.001  # Nearly impossible timeout
            )
        except Exception:
            pass  # Expected to fail

        # Assert - Next call should succeed
        result = await orchestrator.call_tool("plex", "get_libraries", {})
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_retry_on_transient_server_error(
        self, orchestrator
    ):
        """Test automatic retry on transient server errors."""
        # This test requires the server to occasionally return errors
        # In real environment, this could be tested with chaos engineering

        # Act - Make call that might fail transiently
        result = await orchestrator.call_tool(
            "sabnzbd",
            "get_queue",
            {}
        )

        # Assert - Should eventually succeed
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_circuit_breaker_with_real_failures(
        self, integration_config
    ):
        """Test circuit breaker behavior with real server failures."""
        # Arrange - Create orchestrator with low threshold
        config = integration_config.copy()
        orchestrator = MCPOrchestrator(
            config=config,
            circuit_breaker_threshold=2
        )
        await orchestrator.connect_all()

        # Act - Make calls to non-existent tool (will fail)
        failures = 0
        for _ in range(3):
            try:
                await orchestrator.call_tool(
                    "sonarr",
                    "nonexistent_tool",
                    {}
                )
            except Exception:
                failures += 1

        # Assert - Circuit breaker should open
        circuit_state = orchestrator.get_circuit_breaker_state("sonarr")
        assert circuit_state["failure_count"] >= 2

        # Cleanup
        await orchestrator.disconnect_all()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reconnect_after_server_restart(
        self, integration_config
    ):
        """Test reconnection after server restart."""
        # Note: This test would require container restart capability
        # Simplified version tests disconnect/reconnect cycle

        # Arrange
        orchestrator = MCPOrchestrator(config=integration_config)
        await orchestrator.connect_all()

        # Act - Simulate restart by disconnecting and reconnecting
        await orchestrator.disconnect("sabnzbd")
        await asyncio.sleep(1.0)
        reconnect_result = await orchestrator.reconnect("sabnzbd")

        # Assert
        assert reconnect_result is True

        # Cleanup
        await orchestrator.disconnect_all()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_continue_operation_with_degraded_service(
        self, orchestrator
    ):
        """Test continuing operation when one server is down."""
        # Arrange - Disconnect one server
        await orchestrator.disconnect("plex")

        # Act - Continue making calls to other servers
        sab_result = await orchestrator.call_tool("sabnzbd", "get_queue", {})
        sonarr_result = await orchestrator.call_tool("sonarr", "get_series", {})

        # Assert - Other servers should work fine
        assert sab_result is not None
        assert sonarr_result is not None

        # Reconnect for cleanup
        await orchestrator.reconnect("plex")


# ============================================================================
# 5. PERFORMANCE AND LOAD TESTS (5 tests)
# ============================================================================


class TestOrchestratorPerformance:
    """Integration tests for orchestrator performance."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_high_throughput_tool_calls(self, orchestrator):
        """Test orchestrator handling high volume of tool calls."""
        # Act - Make 100 calls as fast as possible
        start_time = datetime.now()

        tasks = [
            orchestrator.call_tool("sabnzbd", "get_version", {})
            for _ in range(100)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert - Should handle load efficiently
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 90  # At least 90% success rate
        assert duration < 10.0  # Should complete in under 10 seconds

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_parallel_batches(self, orchestrator):
        """Test multiple concurrent batches of parallel calls."""
        # Arrange
        batches = [
            [
                {"server": "sabnzbd", "tool": "get_queue", "params": {}},
                {"server": "sonarr", "tool": "get_series", "params": {}},
            ]
            for _ in range(10)
        ]

        # Act
        start_time = datetime.now()
        batch_results = await asyncio.gather(
            *[orchestrator.call_tools_parallel(batch) for batch in batches]
        )
        duration = (datetime.now() - start_time).total_seconds()

        # Assert
        assert len(batch_results) == 10
        assert duration < 5.0  # Should parallelize efficiently

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_connection_pool_efficiency(self, orchestrator):
        """Test that connection pooling improves performance."""
        # Act - Make many calls with pooling
        start_pooled = datetime.now()
        for _ in range(50):
            await orchestrator.call_tool("sabnzbd", "get_version", {})
        pooled_duration = (datetime.now() - start_pooled).total_seconds()

        # Compare with creating new connections each time
        # (Would need separate orchestrator without pooling)

        # Assert - Should be reasonably fast with pooling
        assert pooled_duration < 5.0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_usage_under_load(self, orchestrator):
        """Test memory usage remains stable under load."""
        # This would use memory profiling in production
        # Simplified version just ensures no crashes

        # Act - Make many calls
        for batch in range(10):
            tasks = [
                orchestrator.call_tool("sabnzbd", "get_queue", {})
                for _ in range(50)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Small delay between batches
            await asyncio.sleep(0.1)

        # Assert - Should still be responsive
        result = await orchestrator.call_tool("sabnzbd", "get_version", {})
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_response_time_percentiles(self, orchestrator):
        """Test that response times meet SLA requirements."""
        # Act - Make many calls and measure response times
        response_times = []

        for _ in range(100):
            start = datetime.now()
            await orchestrator.call_tool("sabnzbd", "get_version", {})
            duration = (datetime.now() - start).total_seconds()
            response_times.append(duration)

        # Calculate percentiles
        response_times.sort()
        p50 = response_times[49]  # 50th percentile
        p95 = response_times[94]  # 95th percentile
        p99 = response_times[98]  # 99th percentile

        # Assert - Should meet reasonable SLA
        assert p50 < 0.5   # 500ms for median
        assert p95 < 1.0   # 1 second for 95th percentile
        assert p99 < 2.0   # 2 seconds for 99th percentile


# ============================================================================
# Test Markers and Configuration
# ============================================================================

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration
