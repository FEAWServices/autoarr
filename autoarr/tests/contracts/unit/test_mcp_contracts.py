"""
Contract tests for MCP server data flows.

These tests validate that:
1. MCP tool inputs match expected schemas
2. MCP tool outputs match expected schemas
3. Data transformations preserve required fields
4. Error responses follow the contract
"""

import pytest

from autoarr.tests.contracts.fixtures.schemas import (
    MCP_TOOL_CALL_SCHEMA,
    MCP_TOOL_RESULT_SCHEMA,
    RADARR_MOVIE_RESPONSE_SCHEMA,
    RADARR_QUALITY_PROFILE_SCHEMA,
    SABNZBD_CONFIG_RESPONSE_SCHEMA,
    SABNZBD_HISTORY_RESPONSE_SCHEMA,
    SABNZBD_QUEUE_RESPONSE_SCHEMA,
    SONARR_QUALITY_PROFILE_SCHEMA,
    SONARR_ROOT_FOLDER_SCHEMA,
    SONARR_SERIES_RESPONSE_SCHEMA,
    validate_schema,
)


class TestMCPToolCallContract:
    """Test MCP tool call schema compliance."""

    def test_valid_tool_call_with_arguments(self):
        """Tool call with arguments should be valid."""
        tool_call = {"name": "get_queue", "arguments": {"limit": 10}}
        is_valid, errors = validate_schema(tool_call, MCP_TOOL_CALL_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_tool_call_without_arguments(self):
        """Tool call without arguments should be valid."""
        tool_call = {"name": "get_status"}
        is_valid, errors = validate_schema(tool_call, MCP_TOOL_CALL_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_tool_call_missing_name(self):
        """Tool call without name should fail."""
        tool_call = {"arguments": {"limit": 10}}
        is_valid, errors = validate_schema(tool_call, MCP_TOOL_CALL_SCHEMA)
        assert not is_valid
        assert any("name" in e for e in errors)


class TestMCPToolResultContract:
    """Test MCP tool result schema compliance."""

    def test_valid_text_result(self):
        """Text result should be valid."""
        result = {"content": [{"type": "text", "text": "Success"}], "isError": False}
        is_valid, errors = validate_schema(result, MCP_TOOL_RESULT_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_error_result(self):
        """Error result should be valid."""
        result = {"content": [{"type": "text", "text": "Error occurred"}], "isError": True}
        is_valid, errors = validate_schema(result, MCP_TOOL_RESULT_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_result_missing_content(self):
        """Result without content should fail."""
        result = {"isError": False}
        is_valid, errors = validate_schema(result, MCP_TOOL_RESULT_SCHEMA)
        assert not is_valid


class TestSABnzbdContracts:
    """Test SABnzbd API response contracts."""

    def test_valid_queue_response(self):
        """Valid queue response should pass validation."""
        response = {
            "queue": {
                "slots": [
                    {
                        "nzo_id": "SABnzbd_nzo_abc123",
                        "filename": "Test.Download.S01E01.720p",
                        "status": "Downloading",
                        "percentage": "45",
                        "timeleft": "0:15:30",
                        "mb": "1500.00",
                        "mbleft": "825.00",
                    }
                ],
                "status": "Downloading",
                "speed": "5.2 M",
                "paused": False,
            }
        }
        is_valid, errors = validate_schema(response, SABNZBD_QUEUE_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_empty_queue_response(self):
        """Empty queue response should be valid."""
        response = {"queue": {"slots": [], "status": "Idle", "speed": "0 B", "paused": False}}
        is_valid, errors = validate_schema(response, SABNZBD_QUEUE_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_queue_missing_slots(self):
        """Queue response without slots should fail."""
        response = {"queue": {"status": "Idle", "speed": "0 B"}}
        is_valid, errors = validate_schema(response, SABNZBD_QUEUE_RESPONSE_SCHEMA)
        assert not is_valid

    def test_valid_history_response(self):
        """Valid history response should pass validation."""
        response = {
            "history": {
                "slots": [
                    {
                        "nzo_id": "SABnzbd_nzo_xyz789",
                        "name": "Completed.Download.S01E02",
                        "status": "Completed",
                        "fail_message": "",
                        "completed": 1699999999,
                    }
                ]
            }
        }
        is_valid, errors = validate_schema(response, SABNZBD_HISTORY_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_history_with_failed_download(self):
        """History with failed download should be valid."""
        response = {
            "history": {
                "slots": [
                    {
                        "nzo_id": "SABnzbd_nzo_fail123",
                        "name": "Failed.Download",
                        "status": "Failed",
                        "fail_message": "Repair failed, not enough repair blocks",
                        "completed": 1699999999,
                    }
                ]
            }
        }
        is_valid, errors = validate_schema(response, SABNZBD_HISTORY_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_config_response(self):
        """Valid config response should pass validation."""
        response = {
            "config": {
                "misc": {"cache_limit": "1G", "bandwidth_max": "0"},
                "servers": [{"name": "server1", "host": "news.example.com"}],
                "categories": [{"name": "tv", "dir": "/downloads/tv"}],
            }
        }
        is_valid, errors = validate_schema(response, SABNZBD_CONFIG_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"


class TestSonarrContracts:
    """Test Sonarr API response contracts."""

    def test_valid_series_response(self):
        """Valid series response should pass validation."""
        response = [
            {
                "id": 1,
                "title": "Breaking Bad",
                "tvdbId": 81189,
                "path": "/tv/Breaking Bad",
                "qualityProfileId": 1,
                "monitored": True,
                "seasonFolder": True,
            }
        ]
        is_valid, errors = validate_schema(response, SONARR_SERIES_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_empty_series_response(self):
        """Empty series list should be valid."""
        response = []
        is_valid, errors = validate_schema(response, SONARR_SERIES_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_series_missing_required(self):
        """Series without required fields should fail."""
        response = [{"title": "No ID Series"}]
        is_valid, errors = validate_schema(response, SONARR_SERIES_RESPONSE_SCHEMA)
        assert not is_valid

    def test_valid_quality_profiles(self):
        """Valid quality profiles should pass validation."""
        response = [
            {"id": 1, "name": "HD-1080p", "upgradeAllowed": True, "cutoff": 7},
            {"id": 2, "name": "Any", "upgradeAllowed": False, "cutoff": 1},
        ]
        is_valid, errors = validate_schema(response, SONARR_QUALITY_PROFILE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_root_folders(self):
        """Valid root folders should pass validation."""
        response = [
            {"id": 1, "path": "/tv", "freeSpace": 500000000000},
            {"id": 2, "path": "/anime", "freeSpace": 250000000000},
        ]
        is_valid, errors = validate_schema(response, SONARR_ROOT_FOLDER_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"


class TestRadarrContracts:
    """Test Radarr API response contracts."""

    def test_valid_movie_response(self):
        """Valid movie response should pass validation."""
        response = [
            {
                "id": 1,
                "title": "The Matrix",
                "tmdbId": 603,
                "path": "/movies/The Matrix (1999)",
                "qualityProfileId": 1,
                "monitored": True,
                "hasFile": True,
            }
        ]
        is_valid, errors = validate_schema(response, RADARR_MOVIE_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_valid_empty_movie_response(self):
        """Empty movie list should be valid."""
        response = []
        is_valid, errors = validate_schema(response, RADARR_MOVIE_RESPONSE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"

    def test_invalid_movie_missing_required(self):
        """Movie without required fields should fail."""
        response = [{"title": "No ID Movie"}]
        is_valid, errors = validate_schema(response, RADARR_MOVIE_RESPONSE_SCHEMA)
        assert not is_valid

    def test_valid_quality_profiles(self):
        """Valid quality profiles should pass validation."""
        response = [
            {"id": 1, "name": "HD-1080p", "upgradeAllowed": True, "cutoff": 7},
            {"id": 2, "name": "Ultra-HD", "upgradeAllowed": True, "cutoff": 19},
        ]
        is_valid, errors = validate_schema(response, RADARR_QUALITY_PROFILE_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"


class TestDataFlowContracts:
    """Test data flow between services maintains contracts."""

    def test_sabnzbd_queue_slot_to_internal_model(self):
        """SABnzbd queue slot should contain all fields needed for internal model."""
        # This tests that SABnzbd response fields map to our internal model
        sabnzbd_slot = {
            "nzo_id": "SABnzbd_nzo_abc123",
            "filename": "Test.Download.S01E01.720p",
            "status": "Downloading",
            "percentage": "45",
            "timeleft": "0:15:30",
            "mb": "1500.00",
            "mbleft": "825.00",
        }

        # Verify all required internal model fields can be extracted
        internal_fields = {
            "id": sabnzbd_slot["nzo_id"],
            "name": sabnzbd_slot["filename"],
            "status": sabnzbd_slot["status"],
            "progress": float(sabnzbd_slot["percentage"]),
            "size_mb": float(sabnzbd_slot["mb"]),
            "remaining_mb": float(sabnzbd_slot["mbleft"]),
        }

        assert internal_fields["id"] is not None
        assert internal_fields["name"] is not None
        assert 0 <= internal_fields["progress"] <= 100

    def test_sonarr_series_to_content_result(self):
        """Sonarr series should contain all fields needed for content result."""
        sonarr_series = {
            "id": 1,
            "title": "Breaking Bad",
            "tvdbId": 81189,
            "year": 2008,
            "overview": "A chemistry teacher diagnosed with cancer...",
            "path": "/tv/Breaking Bad",
        }

        # Verify content result fields can be extracted
        content_result = {
            "id": sonarr_series["tvdbId"],
            "title": sonarr_series["title"],
            "year": sonarr_series.get("year"),
            "overview": sonarr_series.get("overview", ""),
        }

        assert content_result["id"] is not None
        assert content_result["title"] is not None

    def test_radarr_movie_to_content_result(self):
        """Radarr movie should contain all fields needed for content result."""
        radarr_movie = {
            "id": 1,
            "title": "The Matrix",
            "tmdbId": 603,
            "year": 1999,
            "overview": "A computer programmer discovers...",
            "path": "/movies/The Matrix (1999)",
        }

        # Verify content result fields can be extracted
        content_result = {
            "id": radarr_movie["tmdbId"],
            "title": radarr_movie["title"],
            "year": radarr_movie.get("year"),
            "overview": radarr_movie.get("overview", ""),
        }

        assert content_result["id"] is not None
        assert content_result["title"] is not None


class TestErrorContracts:
    """Test error response contracts."""

    def test_mcp_error_result_format(self):
        """MCP error results should follow standard format."""
        error_result = {
            "content": [{"type": "text", "text": "Error: Service unavailable"}],
            "isError": True,
        }
        is_valid, errors = validate_schema(error_result, MCP_TOOL_RESULT_SCHEMA)
        assert is_valid, f"Validation errors: {errors}"
        assert error_result["isError"] is True

    def test_error_result_contains_message(self):
        """Error results must contain an error message."""
        error_result = {
            "content": [{"type": "text", "text": "Connection timeout after 30s"}],
            "isError": True,
        }
        assert len(error_result["content"]) > 0
        assert error_result["content"][0]["text"]
