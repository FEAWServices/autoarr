"""
Unit tests for RequestHandler service.

This module tests the RequestHandler's ability to:
- Parse natural language content requests
- Classify media type (movie vs TV)
- Extract metadata (title, year, quality)
- Search TMDB, Radarr, and Sonarr
- Handle disambiguation
- Track request status
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic import APIError

from autoarr.api.services.request_handler import ParsedRequest, RequestHandler, SearchResult

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_agent():
    """Mock LLM agent for classification."""
    mock = MagicMock()
    mock.classify_media_type = AsyncMock(
        return_value={
            "media_type": "movie",
            "confidence": 0.95,
            "reasoning": "Based on TMDB results showing a 2010 film",
        }
    )
    return mock


@pytest.fixture
def mock_tmdb_client():
    """Mock TMDB client for searches."""
    mock = MagicMock()
    mock.search_movie = AsyncMock(
        return_value={
            "results": [
                {
                    "id": 27205,
                    "title": "Inception",
                    "release_date": "2010-07-16",
                    "overview": "A skilled thief...",
                    "vote_average": 8.8,
                }
            ]
        }
    )
    mock.search_tv = AsyncMock(
        return_value={
            "results": [
                {
                    "id": 1396,
                    "name": "Breaking Bad",
                    "first_air_date": "2008-01-20",
                    "overview": "A chemistry teacher...",
                    "vote_average": 9.5,
                }
            ]
        }
    )
    return mock


@pytest.fixture
def mock_orchestrator():
    """Mock MCP orchestrator for Radarr/Sonarr calls."""
    mock = MagicMock()
    mock.call_tool = AsyncMock(
        return_value={
            "tmdbId": 27205,
            "title": "Inception",
            "year": 2010,
            "monitored": False,
            "hasFile": False,
        }
    )
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock = MagicMock()
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def request_handler(mock_llm_agent, mock_tmdb_client, mock_orchestrator, mock_db_session):
    """Create RequestHandler with mocked dependencies."""
    handler = RequestHandler(
        llm_agent=mock_llm_agent,
        tmdb_client=mock_tmdb_client,
        orchestrator=mock_orchestrator,
        db_session=mock_db_session,
    )
    return handler


# ============================================================================
# Test Classes
# ============================================================================


class TestRequestHandlerInitialization:
    """Tests for RequestHandler initialization."""

    @pytest.mark.asyncio
    async def test_handler_initialization(
        self, mock_llm_agent, mock_tmdb_client, mock_orchestrator, mock_db_session
    ) -> None:
        """Test that RequestHandler initializes with correct dependencies."""
        # Arrange & Act
        handler = RequestHandler(
            llm_agent=mock_llm_agent,
            tmdb_client=mock_tmdb_client,
            orchestrator=mock_orchestrator,
            db_session=mock_db_session,
        )

        # Assert
        assert handler.llm_agent is not None
        assert handler.tmdb_client is not None
        assert handler.orchestrator is not None
        assert handler.db_session is not None


class TestNaturalLanguageParsing:
    """Tests for natural language request parsing."""

    @pytest.mark.asyncio
    async def test_parse_simple_movie_request(self, request_handler) -> None:
        """Test parsing simple movie request: 'Add Inception'."""
        # Arrange
        user_input = "Add Inception"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert isinstance(result, ParsedRequest)
        assert result.title == "Inception"
        assert result.media_type is None  # Will be inferred later
        assert result.year is None
        assert result.quality is None
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_parse_movie_with_year(self, request_handler) -> None:
        """Test parsing movie with year: 'Add The Matrix 1999'."""
        # Arrange
        user_input = "Add The Matrix 1999"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "The Matrix"
        assert result.year == 1999
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_parse_movie_with_year_in_parentheses(self, request_handler) -> None:
        """Test parsing movie with year in parentheses: 'The Matrix (1999)'."""
        # Arrange
        user_input = "The Matrix (1999)"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "The Matrix"
        assert result.year == 1999

    @pytest.mark.asyncio
    async def test_parse_movie_with_quality(self, request_handler) -> None:
        """Test parsing movie with quality: 'Add Inception in 4K'."""
        # Arrange
        user_input = "Add Inception in 4K"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Inception"
        assert result.quality in ["4K", "2160p", "Ultra-HD"]
        assert result.quality_profile_override is True

    @pytest.mark.asyncio
    async def test_parse_movie_with_1080p_quality(self, request_handler) -> None:
        """Test parsing movie with 1080p quality."""
        # Arrange
        user_input = "Add Inception 1080p"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Inception"
        assert result.quality in ["1080p", "HD-1080p"]

    @pytest.mark.asyncio
    async def test_parse_tv_show_request(self, request_handler) -> None:
        """Test parsing TV show request: 'Add Breaking Bad TV show'."""
        # Arrange
        user_input = "Add Breaking Bad TV show"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Breaking Bad"
        assert result.media_type == "tv"
        assert result.explicit_type is True

    @pytest.mark.asyncio
    async def test_parse_tv_show_with_series_keyword(self, request_handler) -> None:
        """Test parsing TV show with 'series' keyword."""
        # Arrange
        user_input = "Add the series Breaking Bad"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Breaking Bad"
        assert result.media_type == "tv"

    @pytest.mark.asyncio
    async def test_parse_movie_with_explicit_type(self, request_handler) -> None:
        """Test parsing with explicit movie type."""
        # Arrange
        user_input = "Add Fargo movie"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Fargo"
        assert result.media_type == "movie"
        assert result.explicit_type is True

    @pytest.mark.asyncio
    async def test_parse_request_with_special_characters(self, request_handler) -> None:
        """Test parsing request with special characters."""
        # Arrange
        user_input = "Add Spider-Man: No Way Home"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Spider-Man: No Way Home"
        assert ":" in result.title
        assert "-" in result.title

    @pytest.mark.asyncio
    async def test_parse_empty_request_raises_error(self, request_handler) -> None:
        """Test that empty request raises ValueError."""
        # Arrange
        user_input = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Request cannot be empty"):
            await request_handler.parse_request(user_input)

    @pytest.mark.asyncio
    async def test_parse_whitespace_only_request_raises_error(self, request_handler) -> None:
        """Test that whitespace-only request raises ValueError."""
        # Arrange
        user_input = "   \n  \t  "

        # Act & Assert
        with pytest.raises(ValueError, match="Request cannot be empty"):
            await request_handler.parse_request(user_input)

    @pytest.mark.asyncio
    async def test_parse_request_extracts_season_info(self, request_handler) -> None:
        """Test parsing TV show with season info."""
        # Arrange
        user_input = "Add Breaking Bad season 3"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Breaking Bad"
        assert result.media_type == "tv"
        assert result.season == 3
        assert result.monitor_specific_season is True

    @pytest.mark.asyncio
    async def test_parse_request_extracts_season_and_episode(self, request_handler) -> None:
        """Test parsing with season and episode."""
        # Arrange
        user_input = "Add Breaking Bad S03E13"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "Breaking Bad"
        assert result.season == 3
        assert result.episode == 13

    @pytest.mark.asyncio
    async def test_parse_handles_multiple_years_in_title(self, request_handler) -> None:
        """Test extraction when multiple years present in title."""
        # Arrange
        user_input = "2001: A Space Odyssey (1968)"

        # Act
        result = await request_handler.parse_request(user_input)

        # Assert
        assert result.title == "2001: A Space Odyssey"
        assert result.year == 1968  # Year in parentheses takes precedence

    @pytest.mark.asyncio
    async def test_parse_removes_common_prefixes(self, request_handler) -> None:
        """Test that common prefixes are removed from title."""
        # Arrange
        test_cases = [
            ("Add Inception", "Inception"),
            ("Get me The Matrix", "The Matrix"),
            ("Download Breaking Bad", "Breaking Bad"),
            ("Find Interstellar", "Interstellar"),
        ]

        # Act & Assert
        for user_input, expected_title in test_cases:
            result = await request_handler.parse_request(user_input)
            assert result.title == expected_title


class TestMediaTypeClassification:
    """Tests for movie vs TV classification."""

    @pytest.mark.asyncio
    async def test_classify_known_movie(self, request_handler, mock_tmdb_client) -> None:
        """Test classification of known movie title."""
        # Arrange
        mock_tmdb_client.search_multi = AsyncMock(
            return_value={
                "results": [
                    {
                        "id": 27205,
                        "media_type": "movie",
                        "title": "Inception",
                        "release_date": "2010-07-16",
                    }
                ]
            }
        )

        # Act
        media_type = await request_handler.classify_media_type("Inception")

        # Assert
        assert media_type == "movie"

    @pytest.mark.asyncio
    async def test_classify_known_tv_show(self, request_handler, mock_tmdb_client) -> None:
        """Test classification of known TV show."""
        # Arrange
        mock_tmdb_client.search_multi = AsyncMock(
            return_value={
                "results": [
                    {
                        "id": 1396,
                        "media_type": "tv",
                        "name": "Breaking Bad",
                        "first_air_date": "2008-01-20",
                    }
                ]
            }
        )

        # Act
        media_type = await request_handler.classify_media_type("Breaking Bad")

        # Assert
        assert media_type == "tv"

    @pytest.mark.asyncio
    async def test_classify_uses_llm_for_ambiguous(
        self, request_handler, mock_tmdb_client, mock_llm_agent
    ) -> None:
        """Test LLM is used for ambiguous titles."""
        # Arrange - Both movie and TV show exist
        mock_tmdb_client.search_multi = AsyncMock(
            return_value={
                "results": [
                    {
                        "id": 123,
                        "media_type": "movie",
                        "title": "Fargo",
                        "release_date": "1996-04-05",
                    },
                    {
                        "id": 456,
                        "media_type": "tv",
                        "name": "Fargo",
                        "first_air_date": "2014-04-15",
                    },
                ]
            }
        )

        # Act
        media_type = await request_handler.classify_media_type("Fargo")

        # Assert
        assert media_type == "movie"  # LLM mock returns "movie"
        mock_llm_agent.classify_media_type.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_handles_llm_failure(
        self, request_handler, mock_tmdb_client, mock_llm_agent
    ) -> None:
        """Test fallback when LLM classification fails."""
        # Arrange
        mock_tmdb_client.search_multi = AsyncMock(
            return_value={
                "results": [
                    {"id": 123, "media_type": "movie", "title": "Fargo"},
                    {"id": 456, "media_type": "tv", "name": "Fargo"},
                ]
            }
        )
        mock_llm_agent.classify_media_type = AsyncMock(
            side_effect=APIError("API Error", None, None)
        )

        # Act
        media_type = await request_handler.classify_media_type("Fargo")

        # Assert
        assert media_type == "movie"  # Falls back to preferring movies

    @pytest.mark.asyncio
    async def test_classify_respects_explicit_type(self, request_handler, mock_tmdb_client) -> None:
        """Test that explicit media type is respected."""
        # Arrange
        parsed_request = ParsedRequest(
            user_input="Add Fargo movie",
            title="Fargo",
            media_type="movie",
            explicit_type=True,
        )

        # Act
        media_type = await request_handler.classify_media_type("Fargo", parsed_request)

        # Assert
        assert media_type == "movie"
        # TMDB should not be called if type is explicit
        mock_tmdb_client.search_multi.assert_not_called()

    @pytest.mark.asyncio
    async def test_classify_caches_results(self, request_handler, mock_tmdb_client) -> None:
        """Test that classification results are cached."""
        # Arrange
        mock_tmdb_client.search_multi = AsyncMock(
            return_value={"results": [{"id": 27205, "media_type": "movie", "title": "Inception"}]}
        )

        # Act - Classify same title twice
        result1 = await request_handler.classify_media_type("Inception")
        result2 = await request_handler.classify_media_type("Inception")

        # Assert
        assert result1 == result2
        # TMDB should only be called once
        assert mock_tmdb_client.search_multi.call_count == 1


class TestSearchIntegration:
    """Tests for TMDB, Radarr, and Sonarr search integration."""

    @pytest.mark.asyncio
    async def test_search_movie_on_tmdb(self, request_handler, mock_tmdb_client) -> None:
        """Test searching for movie on TMDB."""
        # Arrange
        title = "Inception"

        # Act
        results = await request_handler.search_tmdb(title, media_type="movie")

        # Assert
        assert len(results) > 0
        assert results[0]["title"] == "Inception"
        assert results[0]["id"] == 27205
        mock_tmdb_client.search_movie.assert_called_once_with(query=title)

    @pytest.mark.asyncio
    async def test_search_tv_on_tmdb(self, request_handler, mock_tmdb_client) -> None:
        """Test searching for TV show on TMDB."""
        # Arrange
        title = "Breaking Bad"

        # Act
        results = await request_handler.search_tmdb(title, media_type="tv")

        # Assert
        assert len(results) > 0
        assert results[0]["name"] == "Breaking Bad"
        assert results[0]["id"] == 1396
        mock_tmdb_client.search_tv.assert_called_once_with(query=title)

    @pytest.mark.asyncio
    async def test_search_movie_on_radarr(self, request_handler, mock_orchestrator) -> None:
        """Test searching for movie on Radarr."""
        # Arrange
        tmdb_id = 27205

        # Act
        result = await request_handler.search_on_radarr(tmdb_id)

        # Assert
        assert result is not None
        assert result["tmdbId"] == 27205
        mock_orchestrator.call_tool.assert_called_once_with(
            "radarr",
            "search_movie",
            {"tmdb_id": tmdb_id},
        )

    @pytest.mark.asyncio
    async def test_search_tv_on_sonarr(self, request_handler, mock_orchestrator) -> None:
        """Test searching for TV show on Sonarr."""
        # Arrange
        tvdb_id = 81189

        # Act
        result = await request_handler.search_on_sonarr(tvdb_id)

        # Assert
        assert result is not None
        mock_orchestrator.call_tool.assert_called_once_with(
            "sonarr",
            "search_series",
            {"tvdb_id": tvdb_id},
        )

    @pytest.mark.asyncio
    async def test_search_handles_no_results(self, request_handler, mock_tmdb_client) -> None:
        """Test handling when no results found."""
        # Arrange
        mock_tmdb_client.search_movie = AsyncMock(return_value={"results": []})

        # Act
        results = await request_handler.search_tmdb("XYZ123NonExistent", media_type="movie")

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_tmdb_rate_limit(self, request_handler, mock_tmdb_client) -> None:
        """Test handling TMDB rate limiting."""
        # Arrange
        from httpx import HTTPStatusError, Request, Response

        response = Response(429, request=Request("GET", "http://test.com"))
        mock_tmdb_client.search_movie = AsyncMock(
            side_effect=HTTPStatusError("Rate limited", request=response.request, response=response)
        )

        # Act & Assert
        with pytest.raises(Exception, match="Rate limit"):
            await request_handler.search_tmdb("Inception", media_type="movie")

    @pytest.mark.asyncio
    async def test_search_combines_results(
        self, request_handler, mock_tmdb_client, mock_orchestrator
    ) -> None:
        """Test combining results from TMDB and Radarr."""
        # Arrange
        title = "Inception"

        # Act
        combined_results = await request_handler.search_all_sources(title, media_type="movie")

        # Assert
        assert "tmdb" in combined_results
        assert "radarr" in combined_results
        assert combined_results["tmdb"]["results"][0]["title"] == "Inception"


class TestDisambiguation:
    """Tests for handling multiple search results."""

    @pytest.mark.asyncio
    async def test_handle_multiple_matches(self, request_handler, mock_tmdb_client) -> None:
        """Test handling multiple search matches."""
        # Arrange
        mock_tmdb_client.search_movie = AsyncMock(
            return_value={
                "results": [
                    {"id": 1, "title": "Batman", "release_date": "1989-06-23"},
                    {"id": 2, "title": "Batman", "release_date": "1966-07-30"},
                    {"id": 3, "title": "Batman Begins", "release_date": "2005-06-15"},
                    {"id": 4, "title": "The Batman", "release_date": "2022-03-04"},
                    {"id": 5, "title": "Batman Returns", "release_date": "1992-06-19"},
                ]
            }
        )

        # Act
        results = await request_handler.handle_disambiguation("Batman", media_type="movie")

        # Assert
        assert len(results) <= 5
        assert all("title" in r for r in results)
        assert all("release_date" in r for r in results)

    @pytest.mark.asyncio
    async def test_auto_select_single_match(self, request_handler, mock_tmdb_client) -> None:
        """Test auto-selection when only one match."""
        # Arrange
        mock_tmdb_client.search_movie = AsyncMock(
            return_value={
                "results": [{"id": 27205, "title": "Inception", "release_date": "2010-07-16"}]
            }
        )

        # Act
        result = await request_handler.handle_disambiguation("Inception", media_type="movie")

        # Assert
        assert len(result) == 1
        assert result[0]["auto_selected"] is True


class TestRequestTracking:
    """Tests for content request database tracking."""

    @pytest.mark.asyncio
    async def test_create_content_request_record(self, request_handler, mock_db_session) -> None:
        """Test creating ContentRequest database record."""
        # Arrange
        user_input = "Add Inception"
        parsed_request = ParsedRequest(
            user_input=user_input,
            title="Inception",
            media_type="movie",
        )

        # Act
        request_id = await request_handler.create_request(parsed_request)

        # Assert
        assert request_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_request_status(self, request_handler, mock_db_session) -> None:
        """Test updating request status."""
        # Arrange
        request_id = 123
        new_status = "searching"

        # Act
        await request_handler.update_status(request_id, new_status)

        # Assert
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_request_progress(self, request_handler) -> None:
        """Test tracking request through lifecycle."""
        # Arrange
        request_id = 123
        statuses = ["pending", "searching", "found", "adding", "completed"]

        # Act & Assert
        for status in statuses:
            await request_handler.update_status(request_id, status)
            # Verify status history is tracked
            # This would check the database record's status_history field


class TestErrorHandling:
    """Tests for error handling in request processing."""

    @pytest.mark.asyncio
    async def test_handle_llm_api_error(self, request_handler, mock_llm_agent) -> None:
        """Test handling LLM API errors."""
        # Arrange
        mock_llm_agent.classify_media_type = AsyncMock(
            side_effect=APIError("API Error", None, None)
        )

        # Act - Should fall back to rule-based classification
        result = await request_handler.parse_request("Add Inception")

        # Assert
        assert result is not None
        assert result.title == "Inception"

    @pytest.mark.asyncio
    async def test_handle_tmdb_connection_error(self, request_handler, mock_tmdb_client) -> None:
        """Test handling TMDB connection errors."""
        # Arrange
        from httpx import ConnectError

        mock_tmdb_client.search_movie = AsyncMock(side_effect=ConnectError("Connection failed"))

        # Act & Assert
        with pytest.raises(Exception, match="Connection failed"):
            await request_handler.search_tmdb("Inception", media_type="movie")

    @pytest.mark.asyncio
    async def test_handle_mcp_orchestrator_error(self, request_handler, mock_orchestrator) -> None:
        """Test handling MCP orchestrator errors."""
        # Arrange
        mock_orchestrator.call_tool = AsyncMock(side_effect=Exception("MCP service unavailable"))

        # Act & Assert
        with pytest.raises(Exception, match="MCP service unavailable"):
            await request_handler.search_on_radarr(27205)


class TestPerformance:
    """Tests for request handler performance."""

    @pytest.mark.asyncio
    async def test_parse_request_performance(self, request_handler) -> None:
        """Test request parsing performance."""
        import time

        # Arrange
        user_input = "Add Inception"

        # Act
        start_time = time.time()
        await request_handler.parse_request(user_input)
        elapsed_time = time.time() - start_time

        # Assert - Should complete in < 100ms (without LLM)
        assert elapsed_time < 0.1

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, request_handler) -> None:
        """Test handling concurrent requests."""
        import asyncio

        # Arrange
        requests = [
            "Add Inception",
            "Add The Matrix",
            "Add Breaking Bad",
            "Add Interstellar",
            "Add Game of Thrones",
        ]

        # Act
        results = await asyncio.gather(*[request_handler.parse_request(req) for req in requests])

        # Assert
        assert len(results) == 5
        assert all(isinstance(r, ParsedRequest) for r in results)
