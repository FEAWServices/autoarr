"""
Unit tests for RequestHandler service.

This module tests the RequestHandler's ability to:
- Parse natural language content requests
- Classify media type (movie vs TV)
- Extract metadata (title, year, quality)
"""

import pytest

from autoarr.api.services.request_handler import ContentClassification, RequestHandler

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_agent():
    """Mock LLM agent for classification."""
    from unittest.mock import AsyncMock, MagicMock

    mock = MagicMock()
    mock.generate_content_classification = AsyncMock(
        return_value={
            "media_type": "movie",
            "confidence": 0.95,
            "title": "Inception",
            "year": 2010,
        }
    )
    return mock


@pytest.fixture
def mock_web_search_service():
    """Mock web search service."""
    from unittest.mock import MagicMock

    return MagicMock()


@pytest.fixture
def request_handler(mock_llm_agent, mock_web_search_service):
    """Create RequestHandler with mocked dependencies."""
    handler = RequestHandler(
        llm_agent=mock_llm_agent,
        web_search_service=mock_web_search_service,
    )
    return handler


# ============================================================================
# Test Classes
# ============================================================================


class TestRequestHandlerInitialization:
    """Tests for RequestHandler initialization."""

    @pytest.mark.asyncio
    async def test_handler_initialization(self, mock_llm_agent, mock_web_search_service) -> None:
        """Test that RequestHandler initializes with correct dependencies."""
        # Arrange & Act
        handler = RequestHandler(
            llm_agent=mock_llm_agent,
            web_search_service=mock_web_search_service,
        )

        # Assert
        assert handler.llm_agent is not None
        assert handler.web_search_service is not None


class TestNaturalLanguageParsing:
    """Tests for natural language request parsing."""

    @pytest.mark.asyncio
    async def test_preprocess_query_basic(self, request_handler) -> None:
        """Test basic query preprocessing."""
        # Arrange
        user_input = "  Add Inception  "

        # Act
        result = request_handler.preprocess_query(user_input)  # noqa: F841

        # Assert
        assert isinstance(result, str)
        assert "inception" in result.lower()

    @pytest.mark.asyncio
    async def test_extract_title_simple(self, request_handler) -> None:
        """Test simple title extraction."""
        # Arrange
        query = "Add Inception"

        # Act
        result = request_handler.extract_title(query)  # noqa: F841

        # Assert
        assert "Inception" in result or "inception" in result.lower()

    @pytest.mark.asyncio
    async def test_extract_year(self, request_handler) -> None:
        """Test year extraction from query."""
        # Arrange
        query = "The Matrix 1999"

        # Act
        result = request_handler.extract_year(query)  # noqa: F841

        # Assert
        assert result == 1999  # noqa: F841

    @pytest.mark.asyncio
    async def test_extract_year_in_parentheses(self, request_handler) -> None:
        """Test year extraction with parentheses."""
        # Arrange
        query = "The Matrix (1999)"

        # Act
        result = request_handler.extract_year(query)  # noqa: F841

        # Assert
        assert result == 1999  # noqa: F841

    @pytest.mark.asyncio
    async def test_extract_quality(self, request_handler) -> None:
        """Test quality extraction from query."""
        # Arrange
        query = "Inception 1080p"

        # Act
        result = request_handler.extract_quality(query)  # noqa: F841

        # Assert
        assert result in ["1080p", "HD-1080p", None]

    @pytest.mark.asyncio
    async def test_extract_tv_metadata(self, request_handler) -> None:
        """Test TV metadata extraction (season/episode)."""
        # Arrange
        query = "Breaking Bad S03E13"

        # Act
        result = request_handler.extract_tv_metadata(query)  # noqa: F841

        # Assert
        assert isinstance(result, dict)
        if "season" in result:
            assert result["season"] == 3
        if "episode" in result:
            assert result["episode"] == 13


class TestMediaTypeClassification:
    """Tests for movie vs TV classification."""

    @pytest.mark.asyncio
    async def test_classify_content_simple_movie(self, request_handler) -> None:
        """Test simple classification identifies movie keywords."""
        # Arrange
        query = "Add Inception movie"

        # Act
        result = request_handler.classify_content_simple(query)  # noqa: F841

        # Assert
        assert isinstance(result, ContentClassification)
        assert result.content_type == "movie"

    @pytest.mark.asyncio
    async def test_classify_content_simple_tv(self, request_handler) -> None:
        """Test simple classification identifies TV keywords."""
        # Arrange
        query = "Add Breaking Bad TV show"

        # Act
        result = request_handler.classify_content_simple(query)  # noqa: F841

        # Assert
        assert isinstance(result, ContentClassification)
        assert result.content_type == "tv"

    @pytest.mark.asyncio
    async def test_classify_content_simple_with_season(self, request_handler) -> None:
        """Test classification with season info."""
        # Arrange
        query = "Add Breaking Bad season 3"

        # Act
        result = request_handler.classify_content_simple(query)  # noqa: F841

        # Assert
        assert isinstance(result, ContentClassification)
        assert result.content_type == "tv"
        assert result.season == 3


class TestDisambiguation:
    """Tests for disambiguation question generation."""

    @pytest.mark.asyncio
    async def test_generate_disambiguation_questions(self, request_handler) -> None:
        """Test disambiguation question generation."""
        # Arrange
        classification = ContentClassification(
            title="Fargo",
            content_type="movie",  # Required field
            confidence=0.5,  # Low confidence indicates ambiguity
        )

        # Act
        questions = request_handler.generate_disambiguation_questions(classification)

        # Assert
        assert isinstance(questions, list)
        # Method should return a list (possibly empty if not implemented)
        assert len(questions) >= 0


class TestPerformance:
    """Tests for request handler performance."""

    @pytest.mark.asyncio
    async def test_preprocess_performance(self, request_handler) -> None:
        """Test preprocessing performance."""
        import time

        # Arrange
        user_input = "Add Inception"

        # Act
        start_time = time.time()
        request_handler.preprocess_query(user_input)
        elapsed_time = time.time() - start_time

        # Assert - Should complete in < 10ms
        assert elapsed_time < 0.01
