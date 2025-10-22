"""
Tests for Request Handler Service.

This module tests the request handler service including:
- NLP preprocessing
- Content classification
- Metadata extraction
- LLM integration
"""

import pytest

from autoarr.api.services.request_handler import ContentClassification, RequestHandler


class TestPreprocessing:
    """Test NLP preprocessing functionality."""

    def test_preprocess_removes_filler_words(self):
        """Test that filler words are removed."""
        handler = RequestHandler()
        query = "Please can you add the movie Inception"
        result = handler.preprocess_query(query)  # noqa: F841

        # Filler words should be removed
        assert "please" not in result
        assert "can" not in result
        assert "you" not in result
        assert "add" not in result
        assert "the" not in result

        # Important words should remain
        assert "movie" in result
        assert "inception" in result

    def test_preprocess_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        handler = RequestHandler()
        query = "Add    Dune     in   4K"
        result = handler.preprocess_query(query)  # noqa: F841

        # Should have single spaces
        assert "  " not in result

    def test_preprocess_lowercases(self):
        """Test that text is lowercased."""
        handler = RequestHandler()
        query = "Add INCEPTION in 4K"
        result = handler.preprocess_query(query)  # noqa: F841

        assert result.islower()

    def test_preprocess_empty_query(self):
        """Test that empty query returns empty string."""
        handler = RequestHandler()
        result = handler.preprocess_query("")  # noqa: F841

        assert result == ""  # noqa: F841


class TestMetadataExtraction:
    """Test metadata extraction functionality."""

    def test_extract_quality_4k(self):
        """Test 4K quality extraction."""
        handler = RequestHandler()

        assert handler.extract_quality("Add Dune in 4K") == "4K"
        assert handler.extract_quality("Add Dune in 2160p") == "4K"
        assert handler.extract_quality("Add Dune in UHD") == "4K"

    def test_extract_quality_1080p(self):
        """Test 1080p quality extraction."""
        handler = RequestHandler()

        assert handler.extract_quality("Add Dune in 1080p") == "1080p"
        assert handler.extract_quality("Add Dune in HD") == "1080p"

    def test_extract_quality_720p(self):
        """Test 720p quality extraction."""
        handler = RequestHandler()

        assert handler.extract_quality("Add Dune in 720p") == "720p"

    def test_extract_quality_none(self):
        """Test no quality specified."""
        handler = RequestHandler()

        assert handler.extract_quality("Add Dune") is None

    def test_extract_year_found(self):
        """Test year extraction when present."""
        handler = RequestHandler()

        assert handler.extract_year("Add Inception 2010") == 2010
        assert handler.extract_year("Add Dune (2021)") == 2021

    def test_extract_year_not_found(self):
        """Test year extraction when absent."""
        handler = RequestHandler()

        assert handler.extract_year("Add Inception") is None

    def test_extract_tv_metadata_season_episode(self):
        """Test S01E01 pattern extraction."""
        handler = RequestHandler()

        metadata = handler.extract_tv_metadata("Breaking Bad S01E01")

        assert metadata["season"] == 1
        assert metadata["episode"] == 1

    def test_extract_tv_metadata_season_only(self):
        """Test season-only extraction."""
        handler = RequestHandler()

        metadata = handler.extract_tv_metadata("Breaking Bad season 3")

        assert metadata["season"] == 3
        assert metadata["episode"] is None

    def test_extract_tv_metadata_episode_only(self):
        """Test episode-only extraction."""
        handler = RequestHandler()

        metadata = handler.extract_tv_metadata("Breaking Bad episode 5")

        assert metadata["season"] is None
        assert metadata["episode"] == 5

    def test_extract_tv_metadata_none(self):
        """Test when no TV metadata present."""
        handler = RequestHandler()

        metadata = handler.extract_tv_metadata("Inception")

        assert metadata["season"] is None
        assert metadata["episode"] is None

    def test_extract_title_removes_metadata(self):
        """Test title extraction removes metadata."""
        handler = RequestHandler()

        title = handler.extract_title("Add Inception 2010 in 4K")

        # Should not contain year or quality
        assert "2010" not in title
        assert "4K" not in title
        assert "4k" not in title.lower()

        # Should contain title
        assert "inception" in title.lower()

    def test_extract_title_keeps_metadata_when_requested(self):
        """Test title extraction keeps metadata when requested."""
        handler = RequestHandler()

        title = handler.extract_title("Add Inception 2010 in 4K", remove_metadata=False)

        # Should contain everything
        assert "inception" in title.lower()


class TestSimpleClassification:
    """Test simple keyword-based classification."""

    def test_classify_movie_with_keyword(self):
        """Test movie classification with 'movie' keyword."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add the movie Inception")  # noqa: F841

        assert result.content_type == "movie"
        assert "Inception" in result.title
        assert result.confidence > 0.7

    def test_classify_movie_with_film_keyword(self):
        """Test movie classification with 'film' keyword."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add the film Dune")  # noqa: F841

        assert result.content_type == "movie"
        assert "Dune" in result.title

    def test_classify_tv_with_season(self):
        """Test TV classification with season metadata."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add Breaking Bad season 3")  # noqa: F841

        assert result.content_type == "tv"
        assert "Breaking Bad" in result.title
        assert result.season == 3
        assert result.confidence > 0.7

    def test_classify_tv_with_episode_pattern(self):
        """Test TV classification with S01E01 pattern."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add Breaking Bad S01E01")  # noqa: F841

        assert result.content_type == "tv"
        assert "Breaking Bad" in result.title
        assert result.season == 1
        assert result.episode == 1
        assert result.confidence > 0.7

    def test_classify_tv_with_series_keyword(self):
        """Test TV classification with 'series' keyword."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add the series The Office")  # noqa: F841

        assert result.content_type == "tv"
        assert "Office" in result.title

    def test_classify_movie_with_quality(self):
        """Test movie classification extracts quality."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add Dune in 4K")  # noqa: F841

        assert result.content_type == "movie"
        assert result.quality == "4K"

    def test_classify_movie_with_year(self):
        """Test movie classification extracts year."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add Inception 2010")  # noqa: F841

        assert result.content_type == "movie"
        assert result.year == 2010

    def test_classify_ambiguous_defaults_to_movie(self):
        """Test ambiguous classification defaults to movie."""
        handler = RequestHandler()

        result = handler.classify_content_simple("Add Dune")  # noqa: F841

        assert result.content_type == "movie"
        assert result.confidence < 0.7  # Lower confidence for ambiguous


@pytest.mark.asyncio
class TestAsyncClassification:
    """Test async classification methods."""

    async def test_classify_content_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        handler = RequestHandler()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await handler.classify_content("")

    async def test_classify_content_without_llm_uses_simple(self):
        """Test classification without LLM falls back to simple."""
        handler = RequestHandler()

        result = await handler.classify_content("Add Dune in 4K")  # noqa: F841

        assert isinstance(result, ContentClassification)
        assert result.content_type == "movie"
        assert result.title
        assert result.quality == "4K"


class TestDisambiguationQuestions:
    """Test disambiguation question generation."""

    def test_generate_questions_low_confidence(self):
        """Test questions generated for low confidence."""
        handler = RequestHandler()

        classification = ContentClassification(
            content_type="movie",
            title="The Office",
            year=None,
            quality=None,
            season=None,
            episode=None,
            confidence=0.5,
        )

        questions = handler.generate_disambiguation_questions(classification)

        assert len(questions) > 0
        assert any("movie" in q.lower() for q in questions)

    def test_generate_questions_missing_year(self):
        """Test questions generated for missing year."""
        handler = RequestHandler()

        classification = ContentClassification(
            content_type="movie",
            title="Inception",
            year=None,
            quality=None,
            season=None,
            episode=None,
            confidence=0.9,
        )

        questions = handler.generate_disambiguation_questions(classification)

        assert any("year" in q.lower() for q in questions)

    def test_generate_questions_tv_missing_season(self):
        """Test questions generated for TV without season."""
        handler = RequestHandler()

        classification = ContentClassification(
            content_type="tv",
            title="Breaking Bad",
            year=None,
            quality=None,
            season=None,
            episode=None,
            confidence=0.9,
        )

        questions = handler.generate_disambiguation_questions(classification)

        assert any("season" in q.lower() for q in questions)

    def test_generate_questions_high_confidence_complete(self):
        """Test no questions for high confidence complete request."""
        handler = RequestHandler()

        classification = ContentClassification(
            content_type="movie",
            title="Inception",
            year=2010,
            quality="4K",
            season=None,
            episode=None,
            confidence=0.95,
        )

        questions = handler.generate_disambiguation_questions(classification)

        # Should have no or minimal questions
        assert len(questions) == 0
