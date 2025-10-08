"""
Request Handler Service for AutoArr.

This service provides intelligent content request processing including:
- NLP preprocessing and normalization
- Content classification (movie vs TV show)
- Metadata extraction from user queries
- Integration with LLM for intelligent classification
"""

import re
from typing import List, Optional

from pydantic import BaseModel, Field

from autoarr.api.services.llm_agent import LLMAgent
from autoarr.api.services.web_search_service import WebSearchService


class ContentRequest(BaseModel):
    """User content request model."""

    query: str = Field(..., description="User query string")
    user_id: Optional[str] = Field(None, description="User ID if multi-user")


class ContentClassification(BaseModel):
    """Content classification result model."""

    content_type: str = Field(..., description="Content type: movie or tv")
    title: str = Field(..., description="Extracted title")
    year: Optional[int] = Field(None, description="Extracted year")
    quality: Optional[str] = Field(None, description="Quality preference (4K, 1080p, etc.)")
    season: Optional[int] = Field(None, description="Season number for TV shows")
    episode: Optional[int] = Field(None, description="Episode number for TV shows")
    confidence: float = Field(..., description="Classification confidence (0.0-1.0)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "content_type": "movie",
                "title": "Dune",
                "year": 2021,
                "quality": "4K",
                "season": None,
                "episode": None,
                "confidence": 0.95,
            }
        }


class ContentSearchResult(BaseModel):
    """Content search result from TMDB."""

    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    imdb_id: Optional[str] = Field(None, description="IMDb ID")
    title: str = Field(..., description="Content title")
    year: int = Field(..., description="Release year")
    overview: str = Field(..., description="Content overview/description")
    poster_path: Optional[str] = Field(None, description="Poster image path")
    match_confidence: float = Field(..., description="Match confidence (0.0-1.0)")


class RequestHandler:
    """
    Request Handler for processing content requests.

    This handler uses NLP techniques and LLM integration to intelligently
    classify and extract metadata from user content requests.

    Args:
        llm_agent: Optional LLM agent for intelligent classification
        web_search_service: Optional web search service for metadata lookup
    """

    # Common filler words to remove during preprocessing
    FILLER_WORDS = {
        "please",
        "can",
        "you",
        "could",
        "would",
        "like",
        "want",
        "need",
        "get",
        "add",
        "download",
        "find",
        "me",
        "the",
        "a",
        "an",
    }

    # Quality indicators
    QUALITY_PATTERNS = {
        r"\b4k\b": "4K",
        r"\b2160p\b": "4K",
        r"\buhd\b": "4K",
        r"\b1080p\b": "1080p",
        r"\b720p\b": "720p",
        r"\b480p\b": "480p",
        r"\bhd\b": "1080p",
    }

    # TV show patterns
    TV_PATTERNS = [
        r"s(\d{1,2})e(\d{1,2})",  # S01E01
        r"season\s+(\d{1,2})",  # season 1
        r"episode\s+(\d{1,3})",  # episode 5
    ]

    # Movie/TV keywords
    MOVIE_KEYWORDS = {"movie", "film", "cinema"}
    TV_KEYWORDS = {"series", "show", "season", "episode", "tv"}

    def __init__(
        self,
        llm_agent: Optional[LLMAgent] = None,
        web_search_service: Optional[WebSearchService] = None,
    ) -> None:
        """Initialize request handler."""
        self.llm_agent = llm_agent
        self.web_search_service = web_search_service

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess and normalize user query.

        Removes filler words, normalizes whitespace, and lowercases.

        Args:
            query: Raw user query

        Returns:
            Preprocessed query string
        """
        # Convert to lowercase
        processed = query.lower().strip()

        # Remove extra whitespace
        processed = re.sub(r"\s+", " ", processed)

        # Remove filler words (but keep them in a separate list for context)
        words = processed.split()
        filtered_words = [w for w in words if w not in self.FILLER_WORDS]

        # If we filtered everything out, return original (minus filler)
        if not filtered_words:
            return processed

        return " ".join(filtered_words)

    def extract_quality(self, query: str) -> Optional[str]:
        """
        Extract quality preference from query.

        Args:
            query: User query

        Returns:
            Quality string or None if not found
        """
        query_lower = query.lower()

        for pattern, quality in self.QUALITY_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                return quality

        return None

    def extract_year(self, query: str) -> Optional[int]:
        """
        Extract year from query.

        Args:
            query: User query

        Returns:
            Year as integer or None if not found
        """
        # Look for 4-digit year (1900-2099)
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", query)
        if year_match:
            return int(year_match.group(1))

        return None

    def extract_tv_metadata(self, query: str) -> dict:
        """
        Extract TV show metadata (season/episode).

        Args:
            query: User query

        Returns:
            Dict with season and episode numbers (if found)
        """
        metadata = {"season": None, "episode": None}

        query_lower = query.lower()

        # Try S01E01 pattern
        match = re.search(r"s(\d{1,2})e(\d{1,2})", query_lower, re.IGNORECASE)
        if match:
            metadata["season"] = int(match.group(1))
            metadata["episode"] = int(match.group(2))
            return metadata

        # Try season number
        match = re.search(r"season\s+(\d{1,2})", query_lower)
        if match:
            metadata["season"] = int(match.group(1))

        # Try episode number
        match = re.search(r"episode\s+(\d{1,3})", query_lower)
        if match:
            metadata["episode"] = int(match.group(1))

        return metadata

    def extract_title(self, query: str, remove_metadata: bool = True) -> str:
        """
        Extract title from query by removing metadata patterns.

        Args:
            query: User query
            remove_metadata: Whether to remove metadata patterns

        Returns:
            Extracted title string
        """
        title = query

        if remove_metadata:
            # Remove quality indicators
            for pattern in self.QUALITY_PATTERNS.keys():
                title = re.sub(pattern, "", title, flags=re.IGNORECASE)

            # Remove TV patterns
            for pattern in self.TV_PATTERNS:
                title = re.sub(pattern, "", title, flags=re.IGNORECASE)

            # Remove year
            title = re.sub(r"\b(19\d{2}|20\d{2})\b", "", title)

            # Remove common request phrases
            title = re.sub(r"\b(add|download|get|find|the|new)\b", "", title, flags=re.IGNORECASE)

        # Clean up whitespace
        title = re.sub(r"\s+", " ", title).strip()

        return title

    def classify_content_simple(self, query: str) -> ContentClassification:
        """
        Simple keyword-based content classification.

        This is a fallback method that doesn't require LLM.

        Args:
            query: User query

        Returns:
            ContentClassification result
        """
        query_lower = query.lower()

        # Extract metadata
        quality = self.extract_quality(query)
        year = self.extract_year(query)
        tv_metadata = self.extract_tv_metadata(query)
        title = self.extract_title(query)

        # Determine content type
        content_type = "movie"  # Default
        confidence = 0.6  # Lower confidence for simple classification

        # Check for TV indicators
        has_tv_metadata = tv_metadata["season"] is not None or tv_metadata["episode"] is not None
        has_tv_keywords = any(keyword in query_lower for keyword in self.TV_KEYWORDS)

        # Check for movie indicators
        has_movie_keywords = any(keyword in query_lower for keyword in self.MOVIE_KEYWORDS)

        if has_tv_metadata or has_tv_keywords:
            content_type = "tv"
            confidence = 0.8 if has_tv_metadata else 0.7
        elif has_movie_keywords:
            content_type = "movie"
            confidence = 0.75

        return ContentClassification(
            content_type=content_type,
            title=title,
            year=year,
            quality=quality,
            season=tv_metadata["season"],
            episode=tv_metadata["episode"],
            confidence=confidence,
        )

    async def classify_content(self, query: str) -> ContentClassification:
        """
        Classify content request using LLM (if available) or simple classification.

        This is the main classification method that should be used.

        Args:
            query: User query

        Returns:
            ContentClassification result

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Preprocess query
        processed_query = self.preprocess_query(query)

        # If LLM agent is available, use it
        if self.llm_agent:
            try:
                return await self.classify_content_llm(query)
            except Exception:
                # Fall back to simple classification if LLM fails
                pass

        # Fall back to simple classification
        return self.classify_content_simple(query)

    async def classify_content_llm(self, query: str) -> ContentClassification:
        """
        Classify content using LLM for intelligent classification.

        Args:
            query: User query

        Returns:
            ContentClassification result

        Raises:
            Exception: If LLM classification fails
        """
        if not self.llm_agent:
            raise ValueError("LLM agent not configured")

        # Use LLM to classify
        classification = await self.llm_agent.classify_content_request(query)

        return classification

    def generate_disambiguation_questions(self, classification: ContentClassification) -> List[str]:
        """
        Generate clarifying questions for ambiguous classifications.

        Args:
            classification: Content classification result

        Returns:
            List of clarifying questions
        """
        questions = []

        if classification.confidence < 0.7:
            # Low confidence overall
            questions.append(
                f"Did you mean the {classification.content_type} '{classification.title}'?"
            )

        if classification.year is None:
            questions.append(f"Which year was '{classification.title}' released?")

        if classification.content_type == "tv" and classification.season is None:
            questions.append(f"Which season of '{classification.title}' would you like?")

        return questions
