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
Unit tests for Web Search Service.

Following TDD (Red-Green-Refactor):
- These tests are written FIRST (Red phase)
- Implementation comes after (Green phase)
- Then we refactor for quality (Refactor phase)
"""

import json
import re
from typing import Any
from unittest.mock import AsyncMock

import pytest

from autoarr.api.services.web_search_service import (
    BestPractice,
    SearchQuery,
    SearchResult,
    WebSearchService,
)


class TestSearchQuery:
    """Test SearchQuery data model."""

    def test_search_query_creation(self) -> None:
        """Test creating a search query with all fields."""
        query = SearchQuery(
            query="SABnzbd best practices configuration",
            application="sabnzbd",
            max_results=10,
        )

        assert query.query == "SABnzbd best practices configuration"
        assert query.application == "sabnzbd"
        assert query.max_results == 10

    def test_search_query_defaults(self) -> None:
        """Test search query with default values."""
        query = SearchQuery(query="test query")

        assert query.query == "test query"
        assert query.application is None
        assert query.max_results == 10


class TestSearchResult:
    """Test SearchResult data model."""

    def test_search_result_creation(self) -> None:
        """Test creating a search result with all fields."""
        result = SearchResult(  # noqa: F841
            title="SABnzbd Best Practices",
            url="https://example.com/sabnzbd-guide",
            snippet="This is a guide to SABnzbd configuration...",
            relevance_score=0.95,
            source="example.com",
        )

        assert result.title == "SABnzbd Best Practices"
        assert result.url == "https://example.com/sabnzbd-guide"
        assert result.snippet == "This is a guide to SABnzbd configuration..."
        assert result.relevance_score == 0.95
        assert result.source == "example.com"

    def test_search_result_score_validation(self) -> None:
        """Test that relevance score is validated."""
        with pytest.raises(ValueError):
            SearchResult(
                title="Test",
                url="https://test.com",
                snippet="test",
                relevance_score=1.5,  # Invalid: should be 0.0-1.0
                source="test.com",
            )


class TestBestPractice:
    """Test BestPractice data model."""

    def test_best_practice_creation(self) -> None:
        """Test creating a best practice with all fields."""
        practice = BestPractice(
            application="sabnzbd",
            category="download",
            setting="incomplete_dir",
            recommendation="Use separate incomplete directory",
            explanation="Prevents corruption of complete downloads",
            priority="high",
            source_url="https://example.com/guide",
        )

        assert practice.application == "sabnzbd"
        assert practice.category == "download"
        assert practice.setting == "incomplete_dir"
        assert practice.recommendation == "Use separate incomplete directory"
        assert practice.priority == "high"
        assert practice.source_url == "https://example.com/guide"

    def test_best_practice_priority_validation(self) -> None:
        """Test that priority is validated."""
        with pytest.raises(ValueError):
            BestPractice(
                application="sabnzbd",
                category="download",
                setting="test",
                recommendation="test",
                explanation="test",
                priority="critical",  # Invalid: should be high/medium/low
                source_url="https://test.com",
            )


class TestBraveSearchClient:
    """Test Brave Search API integration."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, httpx_mock: Any) -> None:
        """Test that search returns results from Brave API."""
        # Arrange
        mock_response = {
            "web": {
                "results": [
                    {
                        "title": "SABnzbd Configuration Guide",
                        "url": "https://sabnzbd.org/wiki/configuration",
                        "description": "Complete guide to SABnzbd configuration",
                    },
                    {
                        "title": "SABnzbd Best Practices",
                        "url": "https://reddit.com/r/usenet/sabnzbd",
                        "description": "Community best practices for SABnzbd",
                    },
                ]
            }
        }

        # Mock matches any request to the Brave API regardless of query params
        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
            json=mock_response,
            status_code=200,
        )

        service = WebSearchService(brave_api_key="test_api_key")

        # Act
        query = SearchQuery(query="SABnzbd best practices", max_results=5)
        results = await service.search(query)

        # Assert
        assert len(results) == 2
        # Results are ranked, so order may vary based on relevance scores
        titles = [r.title for r in results]
        assert "SABnzbd Configuration Guide" in titles
        assert "SABnzbd Best Practices" in titles

    @pytest.mark.asyncio
    async def test_search_handles_api_errors(self, httpx_mock: Any) -> None:
        """Test that search handles API errors gracefully."""
        # Arrange
        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
            status_code=429,  # Rate limit exceeded
            json={"error": "Rate limit exceeded"},
        )

        service = WebSearchService(brave_api_key="test_api_key")

        # Act & Assert
        query = SearchQuery(query="test query")
        with pytest.raises(Exception) as exc_info:
            await service.search(query)

        assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self, httpx_mock: Any) -> None:
        """Test that search handles empty results gracefully."""
        # Arrange
        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
            json={"web": {"results": []}},
            status_code=200,
        )

        service = WebSearchService(brave_api_key="test_api_key")

        # Act
        query = SearchQuery(query="nonexistent query xyz123")
        results = await service.search(query)

        # Assert
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_includes_api_key_in_headers(self, httpx_mock: Any) -> None:
        """Test that API key is included in request headers."""
        # Arrange
        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
            json={"web": {"results": []}},
            status_code=200,
        )

        service = WebSearchService(brave_api_key="test_api_key_12345")

        # Act
        query = SearchQuery(query="test")
        await service.search(query)

        # Assert
        request = httpx_mock.get_request()
        assert request.headers["X-Subscription-Token"] == "test_api_key_12345"


class TestRedisCache:
    """Test Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_stores_search_results(self) -> None:
        """Test that search results are cached in Redis."""
        # Arrange
        mock_redis = AsyncMock()
        service = WebSearchService(
            brave_api_key="test_key", redis_client=mock_redis, cache_ttl=3600
        )

        results = [
            SearchResult(
                title="Test",
                url="https://test.com",
                snippet="test",
                relevance_score=0.9,
                source="test.com",
            )
        ]

        # Generate proper cache key
        cache_key = service._get_cache_key("search", "test_query")

        # Act
        await service._cache_results(cache_key, results)

        # Assert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("search:")  # Cache key
        assert call_args[0][1] == 3600  # TTL
        # Verify the cached data contains our results
        cached_data = json.loads(call_args[0][2])
        assert len(cached_data) == 1
        assert cached_data[0]["title"] == "Test"

    @pytest.mark.asyncio
    async def test_cache_retrieves_cached_results(self) -> None:
        """Test that cached results are retrieved from Redis."""
        # Arrange
        mock_redis = AsyncMock()
        cached_data = [
            {
                "title": "Cached Result",
                "url": "https://cached.com",
                "snippet": "cached snippet",
                "relevance_score": 0.95,
                "source": "cached.com",
            }
        ]
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        service = WebSearchService(brave_api_key="test_key", redis_client=mock_redis)

        # Act
        results = await service._get_cached_results("test_query")

        # Assert
        assert results is not None
        assert len(results) == 1
        assert results[0].title == "Cached Result"
        assert results[0].url == "https://cached.com"
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_returns_none_for_cache_miss(self) -> None:
        """Test that cache miss returns None."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        service = WebSearchService(brave_api_key="test_key", redis_client=mock_redis)

        # Act
        results = await service._get_cached_results("nonexistent_query")

        # Assert
        assert results is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_uses_cache_when_available(self, httpx_mock: Any) -> None:
        """Test that search uses cached results when available."""
        # Arrange
        mock_redis = AsyncMock()
        cached_data = [
            {
                "title": "Cached Result",
                "url": "https://cached.com",
                "snippet": "cached",
                "relevance_score": 0.9,
                "source": "cached.com",
            }
        ]
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        service = WebSearchService(brave_api_key="test_key", redis_client=mock_redis)

        # Act
        query = SearchQuery(query="test query")
        results = await service.search(query)

        # Assert
        assert len(results) == 1
        assert results[0].title == "Cached Result"
        # Verify no HTTP request was made (cache hit)
        assert len(httpx_mock.get_requests()) == 0

    @pytest.mark.asyncio
    async def test_cache_invalidation(self) -> None:
        """Test that cache can be invalidated."""
        # Arrange
        mock_redis = AsyncMock()
        service = WebSearchService(brave_api_key="test_key", redis_client=mock_redis)

        # Act
        await service.invalidate_cache("test_query")

        # Assert
        mock_redis.delete.assert_called_once()
        # Cache key starts with "search:" and includes MD5 hash
        cache_key = mock_redis.delete.call_args[0][0]
        assert cache_key.startswith("search:")
        assert len(cache_key.split(":")[1]) == 32  # MD5 hash is 32 chars

    @pytest.mark.asyncio
    async def test_best_practices_cache_has_longer_ttl(self) -> None:
        """Test that best practices are cached with longer TTL (7 days)."""
        # Arrange
        mock_redis = AsyncMock()
        service = WebSearchService(
            brave_api_key="test_key",
            redis_client=mock_redis,
            cache_ttl=86400,  # 24 hours for search results
            best_practices_ttl=604800,  # 7 days for best practices
        )

        best_practices = [
            BestPractice(
                application="sabnzbd",
                category="download",
                setting="incomplete_dir",
                recommendation="Use separate directory",
                explanation="Prevents corruption",
                priority="high",
                source_url="https://test.com",
            )
        ]

        # Act
        await service._cache_best_practices("sabnzbd", best_practices)

        # Assert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 604800  # 7 days in seconds


class TestContentExtraction:
    """Test HTML/Markdown content extraction."""

    @pytest.mark.asyncio
    async def test_extract_content_from_url(self, httpx_mock: Any) -> None:
        """Test extracting content from a URL."""
        # Arrange
        html_content = """
        <html>
            <body>
                <article>
                    <h1>SABnzbd Best Practices</h1>
                    <p>Use separate incomplete directory for better performance.</p>
                    <p>Enable SSL for secure connections.</p>
                </article>
            </body>
        </html>
        """

        httpx_mock.add_response(
            url="https://example.com/guide",
            text=html_content,
            status_code=200,
        )

        service = WebSearchService(brave_api_key="test_key")

        # Act
        content = await service.extract_content("https://example.com/guide")

        # Assert
        assert "SABnzbd Best Practices" in content
        assert "incomplete directory" in content
        assert "SSL" in content

    @pytest.mark.asyncio
    async def test_extract_content_handles_markdown(self) -> None:
        """Test extracting content from Markdown."""
        # Arrange
        markdown_content = """
        # SABnzbd Configuration

        ## Best Practices

        - Use separate incomplete directory
        - Enable SSL encryption
        - Set proper article cache
        """

        service = WebSearchService(brave_api_key="test_key")

        # Act
        content = service._parse_markdown(markdown_content)

        # Assert
        assert "SABnzbd Configuration" in content
        assert "Best Practices" in content
        assert "incomplete directory" in content
        assert "SSL encryption" in content

    @pytest.mark.asyncio
    async def test_extract_content_cleans_html(self, httpx_mock: Any) -> None:
        """Test that HTML extraction removes scripts and styles."""
        # Arrange
        html_content = """
        <html>
            <head>
                <script>alert('test');</script>
                <style>.test { color: red; }</style>
            </head>
            <body>
                <script>console.log('test');</script>
                <article>
                    <p>Actual content here.</p>
                </article>
                <footer>Copyright 2025</footer>
            </body>
        </html>
        """

        httpx_mock.add_response(
            url="https://example.com/page",
            text=html_content,
            status_code=200,
        )

        service = WebSearchService(brave_api_key="test_key")

        # Act
        content = await service.extract_content("https://example.com/page")

        # Assert
        assert "Actual content here" in content
        assert "alert" not in content
        assert "console.log" not in content
        assert ".test { color: red; }" not in content


class TestBestPracticesExtraction:
    """Test extraction of best practices from content."""

    @pytest.mark.asyncio
    async def test_extract_best_practices_from_content(self) -> None:
        """Test extracting best practices from text content."""
        # Arrange
        content = """
        SABnzbd Configuration Best Practices

        Download Settings:
        - Set incomplete_dir to a separate directory to prevent corruption
        - Use multiple servers for redundancy
        - Enable SSL for security

        Performance:
        - Set article_cache to at least 500M for better performance
        - Enable direct_unpack for faster extraction
        """

        service = WebSearchService(brave_api_key="test_key")

        # Act
        practices = await service.extract_best_practices(
            content=content, application="sabnzbd", source_url="https://example.com/guide"
        )

        # Assert
        assert len(practices) > 0
        # Check for expected practices
        incomplete_dir_practice = next(
            (p for p in practices if "incomplete_dir" in p.setting.lower()), None
        )
        assert incomplete_dir_practice is not None
        assert incomplete_dir_practice.application == "sabnzbd"
        assert "separate directory" in incomplete_dir_practice.recommendation.lower()

    @pytest.mark.asyncio
    async def test_extract_best_practices_assigns_priority(self) -> None:
        """Test that best practices are assigned priority levels."""
        # Arrange
        content = """
        Critical: Enable SSL for security
        Important: Set article_cache for performance
        Optional: Enable logging for debugging
        """

        service = WebSearchService(brave_api_key="test_key")

        # Act
        practices = await service.extract_best_practices(
            content=content, application="sabnzbd", source_url="https://example.com"
        )

        # Assert
        assert len(practices) > 0
        # Verify priorities are assigned
        priorities = [p.priority for p in practices]
        assert "high" in priorities or "medium" in priorities or "low" in priorities

    @pytest.mark.asyncio
    async def test_extract_best_practices_categorizes_settings(self) -> None:
        """Test that best practices are categorized properly."""
        # Arrange
        content = """
        Download Configuration:
        - Set download_dir to /downloads
        - Set incomplete_dir to /incomplete

        Security Settings:
        - Enable SSL
        - Use API key authentication

        Performance Tuning:
        - Set article_cache to 500M
        - Enable direct_unpack
        """

        service = WebSearchService(brave_api_key="test_key")

        # Act
        practices = await service.extract_best_practices(
            content=content, application="sabnzbd", source_url="https://example.com"
        )

        # Assert
        # Should extract some best practices
        assert len(practices) > 0
        # All practices should have a category (even if it's 'general')
        assert all(p.category for p in practices)
        # Should have valid application
        assert all(p.application == "sabnzbd" for p in practices)


class TestSearchResultScoring:
    """Test search result relevance scoring and ranking."""

    def test_score_result_by_keyword_relevance(self) -> None:
        """Test that results are scored based on keyword relevance."""
        # Arrange
        service = WebSearchService(brave_api_key="test_key")
        query = SearchQuery(query="SABnzbd configuration best practices")

        result_high_relevance = SearchResult(
            title="SABnzbd Configuration Best Practices Guide",
            url="https://sabnzbd.org/wiki/configuration",
            snippet="Complete guide to SABnzbd configuration and best practices",
            relevance_score=0.0,  # Will be calculated
            source="sabnzbd.org",
        )

        result_low_relevance = SearchResult(
            title="Download Manager Overview",
            url="https://example.com/downloads",
            snippet="Various download managers available",
            relevance_score=0.0,
            source="example.com",
        )

        # Act
        score_high = service._calculate_relevance_score(result_high_relevance, query)
        score_low = service._calculate_relevance_score(result_low_relevance, query)

        # Assert
        assert score_high > score_low
        assert 0.0 <= score_high <= 1.0
        assert 0.0 <= score_low <= 1.0

    def test_score_result_by_source_authority(self) -> None:
        """Test that results from authoritative sources score higher."""
        # Arrange
        service = WebSearchService(brave_api_key="test_key")
        query = SearchQuery(query="SABnzbd configuration", application="sabnzbd")

        official_source = SearchResult(
            title="Configuration Guide",
            url="https://sabnzbd.org/wiki/configuration",
            snippet="Official SABnzbd configuration guide",
            relevance_score=0.0,
            source="sabnzbd.org",
        )

        third_party_source = SearchResult(
            title="Configuration Guide",
            url="https://randomsite.com/sabnzbd-guide",
            snippet="SABnzbd configuration guide",
            relevance_score=0.0,
            source="randomsite.com",
        )

        # Act
        score_official = service._calculate_relevance_score(official_source, query)
        score_third_party = service._calculate_relevance_score(third_party_source, query)

        # Assert
        # Official source should score higher due to domain authority
        assert score_official > score_third_party

    def test_rank_results_by_score(self) -> None:
        """Test that results are ranked by relevance score."""
        # Arrange
        service = WebSearchService(brave_api_key="test_key")

        results = [
            SearchResult(
                title="Result C",
                url="https://c.com",
                snippet="test",
                relevance_score=0.5,
                source="c.com",
            ),
            SearchResult(
                title="Result A",
                url="https://a.com",
                snippet="test",
                relevance_score=0.9,
                source="a.com",
            ),
            SearchResult(
                title="Result B",
                url="https://b.com",
                snippet="test",
                relevance_score=0.7,
                source="b.com",
            ),
        ]

        # Act
        ranked = service.rank_results(results)

        # Assert
        assert len(ranked) == 3
        assert ranked[0].title == "Result A"  # Highest score (0.9)
        assert ranked[1].title == "Result B"  # Medium score (0.7)
        assert ranked[2].title == "Result C"  # Lowest score (0.5)

    def test_rank_results_limits_to_max_results(self) -> None:
        """Test that ranking respects max_results parameter."""
        # Arrange
        service = WebSearchService(brave_api_key="test_key")

        results = [
            SearchResult(
                title=f"Result {i}",
                url=f"https://{i}.com",
                snippet="test",
                relevance_score=1.0 - (i * 0.1),
                source=f"{i}.com",
            )
            for i in range(10)
        ]

        # Act
        ranked = service.rank_results(results, max_results=5)

        # Assert
        assert len(ranked) == 5
        # Should return top 5 results
        assert all(r.relevance_score >= 0.5 for r in ranked)


class TestWebSearchServiceIntegration:
    """Integration tests for the complete Web Search Service."""

    @pytest.mark.asyncio
    async def test_search_and_extract_workflow(self, httpx_mock: Any) -> None:
        """Test complete workflow: search -> extract -> parse best practices."""
        # Arrange
        # Mock search API
        search_response = {
            "web": {
                "results": [
                    {
                        "title": "SABnzbd Best Practices",
                        "url": "https://sabnzbd.org/wiki/configuration",
                        "description": "Official configuration guide",
                    }
                ]
            }
        }

        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
            json=search_response,
            status_code=200,
        )

        # Mock content extraction
        content_html = """
        <article>
            <h1>SABnzbd Best Practices</h1>
            <p>Set incomplete_dir to /incomplete for better organization</p>
            <p>Enable SSL for secure connections</p>
        </article>
        """

        httpx_mock.add_response(
            method="GET",
            url="https://sabnzbd.org/wiki/configuration",
            text=content_html,
            status_code=200,
        )

        service = WebSearchService(brave_api_key="test_key")

        # Act
        # Step 1: Search
        query = SearchQuery(query="SABnzbd best practices", application="sabnzbd")
        search_results = await service.search(query)

        # Step 2: Extract content from top result
        content = await service.extract_content(search_results[0].url)

        # Step 3: Parse best practices
        best_practices = await service.extract_best_practices(
            content=content, application="sabnzbd", source_url=search_results[0].url
        )

        # Assert
        assert len(search_results) > 0
        assert "SABnzbd" in content
        assert len(best_practices) > 0
        assert any("incomplete_dir" in bp.setting.lower() for bp in best_practices)

    @pytest.mark.asyncio
    async def test_search_for_multiple_applications(self, httpx_mock: Any) -> None:
        """Test searching for best practices for different applications."""
        # Arrange
        applications = ["sabnzbd", "sonarr", "radarr", "plex"]

        for app in applications:
            httpx_mock.add_response(
                method="GET",
                url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
                json={
                    "web": {
                        "results": [
                            {
                                "title": f"{app.title()} Best Practices",
                                "url": f"https://{app}.org/guide",
                                "description": f"Guide for {app}",
                            }
                        ]
                    }
                },
                status_code=200,
            )

        service = WebSearchService(brave_api_key="test_key")

        # Act & Assert
        for app in applications:
            query = SearchQuery(query=f"{app} best practices configuration", application=app)
            results = await service.search(query)

            assert len(results) > 0
            assert app.lower() in results[0].title.lower()

    @pytest.mark.asyncio
    async def test_handles_rate_limiting_gracefully(self, httpx_mock: Any) -> None:
        """Test that service handles rate limiting with proper error messages."""
        # Arrange
        httpx_mock.add_response(
            method="GET",
            url=re.compile(r"https://api\.search\.brave\.com/res/v1/web/search.*"),
            status_code=429,
            json={"error": "Too many requests"},
        )

        service = WebSearchService(brave_api_key="test_key")

        # Act & Assert
        query = SearchQuery(query="test")
        with pytest.raises(Exception) as exc_info:
            await service.search(query)

        assert "rate" in str(exc_info.value).lower() or "429" in str(exc_info.value)
