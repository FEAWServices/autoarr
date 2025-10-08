"""
Web Search Service for AutoArr.

This service provides web search capabilities using Brave Search API,
content extraction from web pages, and best practices extraction.

Features:
- Brave Search API integration
- Redis caching for search results and best practices
- HTML/Markdown content extraction
- Best practices extraction and categorization
- Search result scoring and ranking
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator
from redis.asyncio import Redis


class SearchQuery(BaseModel):
    """Search query model."""

    query: str = Field(..., description="Search query string")
    application: Optional[str] = Field(
        default=None, description="Target application (sabnzbd, sonarr, radarr, plex)"
    )
    max_results: int = Field(default=10, description="Maximum number of results to return")


class SearchResult(BaseModel):
    """Search result model."""

    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="Result snippet/description")
    relevance_score: float = Field(..., description="Relevance score (0.0-1.0)")
    source: str = Field(..., description="Source domain")

    @field_validator("relevance_score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Validate relevance score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")
        return v


class BestPractice(BaseModel):
    """Best practice recommendation model."""

    application: str = Field(..., description="Target application")
    category: str = Field(..., description="Category (download, security, performance, etc.)")
    setting: str = Field(..., description="Setting name")
    recommendation: str = Field(..., description="Recommended value or action")
    explanation: str = Field(..., description="Why this is a best practice")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    source_url: str = Field(..., description="Source URL for this recommendation")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is one of the allowed values."""
        allowed = ["high", "medium", "low"]
        if v.lower() not in allowed:
            raise ValueError(f"Priority must be one of {allowed}, got {v}")
        return v.lower()


class WebSearchService:
    """
    Web Search Service for finding and extracting best practices.

    This service integrates with Brave Search API to find relevant documentation
    and best practices for media automation applications. It includes:
    - Search result caching (24 hours)
    - Best practices caching (7 days)
    - Content extraction from HTML/Markdown
    - Intelligent result ranking
    - Rate limit handling

    Args:
        brave_api_key: Brave Search API key
        redis_client: Optional Redis client for caching
        cache_ttl: Cache TTL for search results in seconds (default: 24 hours)
        best_practices_ttl: Cache TTL for best practices in seconds (default: 7 days)
    """

    # Authoritative domains for each application
    AUTHORITATIVE_DOMAINS = {
        "sabnzbd": ["sabnzbd.org", "github.com/sabnzbd"],
        "sonarr": ["sonarr.tv", "wiki.servarr.com", "github.com/sonarr"],
        "radarr": ["radarr.video", "wiki.servarr.com", "github.com/radarr"],
        "plex": ["plex.tv", "support.plex.tv", "forums.plex.tv"],
    }

    # Category keywords for classification
    CATEGORY_KEYWORDS = {
        "download": [
            "download",
            "incomplete",
            "complete",
            "queue",
            "article_cache",
            "direct_unpack",
        ],
        "security": ["ssl", "https", "api_key", "authentication", "encryption", "secure"],
        "performance": [
            "cache",
            "speed",
            "performance",
            "optimization",
            "threads",
            "connections",
        ],
        "storage": ["path", "directory", "folder", "storage", "disk", "space"],
        "network": ["server", "host", "port", "proxy", "dns", "connection"],
    }

    # Priority keywords
    PRIORITY_KEYWORDS = {
        "high": ["critical", "important", "must", "required", "essential", "security"],
        "medium": ["recommended", "should", "suggested", "better", "improve"],
        "low": ["optional", "consider", "may", "can", "nice to have"],
    }

    def __init__(
        self,
        brave_api_key: str,
        redis_client: Optional[Redis] = None,
        cache_ttl: int = 86400,  # 24 hours
        best_practices_ttl: int = 604800,  # 7 days
    ) -> None:
        """Initialize the Web Search Service."""
        self.brave_api_key = brave_api_key
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.best_practices_ttl = best_practices_ttl
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

        # HTTP client for API requests
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search for content using Brave Search API.

        This method:
        1. Checks cache for existing results
        2. If not cached, calls Brave Search API
        3. Scores and ranks results
        4. Caches results for future use

        Args:
            query: SearchQuery object with query string and parameters

        Returns:
            List of SearchResult objects, ranked by relevance

        Raises:
            Exception: If API returns error (rate limit, authentication, etc.)
        """
        # Check cache first
        cache_key = self._get_cache_key("search", query.query)
        cached_results = await self._get_cached_results(cache_key)

        if cached_results is not None:
            return cached_results

        # Call Brave Search API
        headers = {
            "X-Subscription-Token": self.brave_api_key,
            "Accept": "application/json",
        }

        params = {
            "q": query.query,
            "count": query.max_results,
        }

        try:
            response = await self.http_client.get(self.base_url, headers=headers, params=params)

            if response.status_code == 429:
                raise Exception("Rate limit exceeded. Please try again later.")

            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")

            data = response.json()

            # Parse results
            results = []
            web_results = data.get("web", {}).get("results", [])

            for item in web_results:
                # Extract domain from URL
                parsed_url = urlparse(item["url"])
                source = parsed_url.netloc.replace("www.", "")

                result = SearchResult(
                    title=item.get("title", ""),
                    url=item["url"],
                    snippet=item.get("description", ""),
                    relevance_score=0.0,  # Will be calculated
                    source=source,
                )

                # Calculate relevance score
                result.relevance_score = self._calculate_relevance_score(result, query)
                results.append(result)

            # Rank results
            ranked_results = self.rank_results(results, max_results=query.max_results)

            # Cache results
            await self._cache_results(cache_key, ranked_results)

            return ranked_results

        except httpx.RequestError as e:
            raise Exception(f"Network error: {str(e)}")

    def _calculate_relevance_score(self, result: SearchResult, query: SearchQuery) -> float:
        """
        Calculate relevance score for a search result.

        Scoring factors:
        - Keyword matches in title (40%)
        - Keyword matches in snippet (30%)
        - Source authority (20%)
        - URL quality (10%)

        Args:
            result: SearchResult to score
            query: Original search query

        Returns:
            Float score between 0.0 and 1.0
        """
        score = 0.0
        query_terms = query.query.lower().split()

        # Title match (40%)
        title_lower = result.title.lower()
        title_matches = sum(1 for term in query_terms if term in title_lower)
        title_score = min(title_matches / len(query_terms), 1.0) * 0.4

        # Snippet match (30%)
        snippet_lower = result.snippet.lower()
        snippet_matches = sum(1 for term in query_terms if term in snippet_lower)
        snippet_score = min(snippet_matches / len(query_terms), 1.0) * 0.3

        # Source authority (20%)
        authority_score = 0.0
        if query.application:
            authoritative_domains = self.AUTHORITATIVE_DOMAINS.get(query.application, [])
            if any(domain in result.source for domain in authoritative_domains):
                authority_score = 0.2
            elif "github.com" in result.source or "stackoverflow.com" in result.source:
                authority_score = 0.15
            elif "reddit.com" in result.source:
                authority_score = 0.1

        # URL quality (10%)
        url_lower = result.url.lower()
        url_matches = sum(1 for term in query_terms if term in url_lower)
        url_score = min(url_matches / len(query_terms), 1.0) * 0.1

        score = title_score + snippet_score + authority_score + url_score

        return round(score, 3)

    def rank_results(
        self, results: List[SearchResult], max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Rank search results by relevance score.

        Args:
            results: List of SearchResult objects
            max_results: Optional limit on number of results to return

        Returns:
            Sorted list of SearchResult objects (highest score first)
        """
        # Sort by relevance score (descending)
        sorted_results = sorted(results, key=lambda r: r.relevance_score, reverse=True)

        # Limit results if specified
        if max_results is not None:
            sorted_results = sorted_results[:max_results]

        return sorted_results

    async def extract_content(self, url: str) -> str:
        """
        Extract text content from a URL.

        This method:
        1. Fetches the page content
        2. Parses HTML and extracts text
        3. Removes scripts, styles, and navigation
        4. Returns clean text content

        Args:
            url: URL to extract content from

        Returns:
            Extracted text content

        Raises:
            Exception: If URL cannot be fetched
        """
        try:
            response = await self.http_client.get(url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "html" in content_type:
                return self._parse_html(response.text)
            elif "markdown" in content_type or url.endswith(".md"):
                return self._parse_markdown(response.text)
            else:
                # Try to parse as HTML anyway
                return self._parse_html(response.text)

        except httpx.RequestError as e:
            raise Exception(f"Failed to fetch URL {url}: {str(e)}")

    def _parse_html(self, html: str) -> str:
        """
        Parse HTML content and extract text.

        Args:
            html: HTML content string

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def _parse_markdown(self, markdown: str) -> str:
        """
        Parse Markdown content.

        For now, this just returns the raw markdown as it's already readable.
        In the future, we could convert to HTML first or do more sophisticated parsing.

        Args:
            markdown: Markdown content string

        Returns:
            Cleaned markdown text
        """
        # Remove code blocks but keep their content
        text = re.sub(r"```[\w]*\n(.*?)```", r"\1", markdown, flags=re.DOTALL)

        # Remove inline code markers
        text = text.replace("`", "")

        return text.strip()

    async def extract_best_practices(
        self, content: str, application: str, source_url: str
    ) -> List[BestPractice]:
        """
        Extract best practices from content.

        This method uses pattern matching and NLP techniques to identify
        configuration recommendations in documentation.

        Args:
            content: Text content to analyze
            application: Target application name
            source_url: Source URL for attribution

        Returns:
            List of BestPractice objects
        """
        practices = []

        # Split content into sections/paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        current_category = "general"

        for para in paragraphs:
            # Check if this is a category header
            category = self._identify_category(para)
            if category:
                current_category = category
                continue

            # Look for recommendation patterns
            recommendations = self._extract_recommendations(para, current_category)

            for rec in recommendations:
                practice = BestPractice(
                    application=application,
                    category=current_category,
                    setting=rec["setting"],
                    recommendation=rec["recommendation"],
                    explanation=rec.get("explanation", rec["recommendation"]),
                    priority=rec["priority"],
                    source_url=source_url,
                )
                practices.append(practice)

        return practices

    def _identify_category(self, text: str) -> Optional[str]:
        """
        Identify category from text.

        Args:
            text: Text to analyze

        Returns:
            Category name or None
        """
        text_lower = text.lower()

        # Check if this looks like a header (short, ends with colon, etc.)
        if len(text) < 100 and (":" in text or text.isupper() or text.endswith("#")):
            for category, keywords in self.CATEGORY_KEYWORDS.items():
                if any(keyword in text_lower for keyword in keywords):
                    return category

        return None

    def _extract_recommendations(self, text: str, category: str) -> List[Dict[str, str]]:
        """
        Extract recommendations from text.

        Args:
            text: Text to analyze
            category: Current category

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        text_lower = text.lower()

        # Pattern 1: "Set X to Y"
        set_pattern = re.compile(
            r"(?:set|configure|use)\s+([a-z_]+(?:_[a-z]+)*)\s+(?:to|as|=)\s+([^\n.,;]+)",
            re.IGNORECASE,
        )

        for match in set_pattern.finditer(text):
            setting = match.group(1)
            value = match.group(2).strip()

            recommendations.append(
                {
                    "setting": setting,
                    "recommendation": f"Set {setting} to {value}",
                    "priority": self._determine_priority(text_lower),
                }
            )

        # Pattern 2: "Enable X" or "Disable Y"
        enable_pattern = re.compile(
            r"(?:enable|disable|turn on|turn off|activate|deactivate)\s+([a-z_]+(?:_[a-z]+)*)",
            re.IGNORECASE,
        )

        for match in enable_pattern.finditer(text):
            setting = match.group(1)
            action = match.group(0).split()[0].lower()

            recommendations.append(
                {
                    "setting": setting,
                    "recommendation": f"{action.capitalize()} {setting}",
                    "priority": self._determine_priority(text_lower),
                }
            )

        # Pattern 3: List items that might be recommendations
        if text.strip().startswith("-") or text.strip().startswith("*"):
            # This is a list item
            # Try to extract setting name from common patterns
            words = text.split()
            if len(words) > 2:
                # Look for setting-like words (lowercase with underscores)
                for word in words:
                    if "_" in word and word.replace("_", "").isalnum():
                        recommendations.append(
                            {
                                "setting": word,
                                "recommendation": text.strip().lstrip("-*").strip(),
                                "priority": self._determine_priority(text_lower),
                            }
                        )
                        break

        return recommendations

    def _determine_priority(self, text: str) -> str:
        """
        Determine priority level from text.

        Args:
            text: Text to analyze

        Returns:
            Priority level (high, medium, low)
        """
        text_lower = text.lower()

        # Check for high priority keywords
        for keyword in self.PRIORITY_KEYWORDS["high"]:
            if keyword in text_lower:
                return "high"

        # Check for medium priority keywords
        for keyword in self.PRIORITY_KEYWORDS["medium"]:
            if keyword in text_lower:
                return "medium"

        # Default to medium if no clear indicators
        return "medium"

    async def _get_cached_results(self, cache_key: str) -> Optional[List[SearchResult]]:
        """
        Get cached search results from Redis.

        Args:
            cache_key: Cache key

        Returns:
            List of SearchResult objects or None if not cached
        """
        if self.redis_client is None:
            return None

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data is None:
                return None

            # Deserialize from JSON
            data = json.loads(cached_data)
            return [SearchResult(**item) for item in data]

        except Exception:
            # If cache read fails, return None to trigger fresh search
            return None

    async def _cache_results(self, cache_key: str, results: List[SearchResult]) -> None:
        """
        Cache search results in Redis.

        Args:
            cache_key: Cache key
            results: List of SearchResult objects to cache
        """
        if self.redis_client is None:
            return

        try:
            # Serialize to JSON
            data = [result.model_dump() for result in results]
            serialized = json.dumps(data)

            # Store with TTL
            await self.redis_client.setex(cache_key, self.cache_ttl, serialized)

        except Exception:
            # If cache write fails, continue without caching
            pass

    async def _cache_best_practices(self, cache_key: str, practices: List[BestPractice]) -> None:
        """
        Cache best practices in Redis with longer TTL.

        Args:
            cache_key: Cache key
            practices: List of BestPractice objects to cache
        """
        if self.redis_client is None:
            return

        try:
            # Serialize to JSON
            data = [practice.model_dump() for practice in practices]
            serialized = json.dumps(data)

            # Store with longer TTL (7 days)
            await self.redis_client.setex(cache_key, self.best_practices_ttl, serialized)

        except Exception:
            pass

    async def invalidate_cache(self, query: str) -> None:
        """
        Invalidate cache for a specific query.

        Args:
            query: Query string to invalidate
        """
        if self.redis_client is None:
            return

        cache_key = self._get_cache_key("search", query)
        try:
            await self.redis_client.delete(cache_key)
        except Exception:
            pass

    def _get_cache_key(self, prefix: str, value: str) -> str:
        """
        Generate cache key.

        Args:
            prefix: Key prefix (e.g., "search", "best_practices")
            value: Value to hash

        Returns:
            Cache key string
        """
        # Use hash to keep keys consistent length
        value_hash = hashlib.md5(value.encode()).hexdigest()
        return f"{prefix}:{value_hash}"

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.close()
