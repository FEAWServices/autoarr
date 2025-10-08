"""
Tests for Web Search Service.

This module tests the web search, content extraction, and best practices
extraction functionality.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from redis.asyncio import Redis

from autoarr.api.services.web_search_service import (
    BestPractice,
    SearchQuery,
    SearchResult,
    WebSearchService,
)


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    redis = AsyncMock(spec=Redis)
    return redis


@pytest.fixture
def web_search_service(mock_redis: AsyncMock) -> WebSearchService:
    """Create a Web Search Service instance with mocked dependencies."""
    return WebSearchService(
        brave_api_key="test_api_key",
        redis_client=mock_redis,
        cache_ttl=3600,
        best_practices_ttl=86400,
    )


@pytest.fixture
def web_search_service_no_cache() -> WebSearchService:
    """Create a Web Search Service instance without Redis."""
    return WebSearchService(
        brave_api_key="test_api_key",
        redis_client=None,
    )


class TestWebSearchServiceInitialization:
    """Test Web Search Service initialization."""

    def test_initialization_with_redis(self, mock_redis: AsyncMock) -> None:
        """Test initialization with Redis client."""
        service = WebSearchService(
            brave_api_key="test_key",
            redis_client=mock_redis,
        )

        assert service.brave_api_key == "test_key"
        assert service.redis_client == mock_redis

    def test_initialization_without_redis(self) -> None:
        """Test initialization without Redis client."""
        service = WebSearchService(brave_api_key="test_key")

        assert service.redis_client is None

    def test_authoritative_domains_defined(self) -> None:
        """Test that authoritative domains are defined for all applications."""
        service = WebSearchService(brave_api_key="test_key")

        expected_apps = ["sabnzbd", "sonarr", "radarr", "plex"]
        for app in expected_apps:
            assert app in service.AUTHORITATIVE_DOMAINS
            assert len(service.AUTHORITATIVE_DOMAINS[app]) > 0


class TestSearchModels:
    """Test Pydantic models for search."""

    def test_search_query_creation(self) -> None:
        """Test SearchQuery model creation."""
        query = SearchQuery(query="test query", application="sabnzbd", max_results=5)

        assert query.query == "test query"
        assert query.application == "sabnzbd"
        assert query.max_results == 5

    def test_search_query_defaults(self) -> None:
        """Test SearchQuery model default values."""
        query = SearchQuery(query="test")

        assert query.application is None
        assert query.max_results == 10

    def test_search_result_creation(self) -> None:
        """Test SearchResult model creation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            relevance_score=0.85,
            source="example.com",
        )

        assert result.title == "Test Title"
        assert result.relevance_score == 0.85

    def test_search_result_score_validation(self) -> None:
        """Test SearchResult relevance score validation."""
        # Valid scores
        SearchResult(
            title="Test",
            url="https://example.com",
            snippet="snippet",
            relevance_score=0.0,
            source="example.com",
        )

        SearchResult(
            title="Test",
            url="https://example.com",
            snippet="snippet",
            relevance_score=1.0,
            source="example.com",
        )

        # Invalid scores
        with pytest.raises(ValueError):
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="snippet",
                relevance_score=1.5,
                source="example.com",
            )

    def test_best_practice_creation(self) -> None:
        """Test BestPractice model creation."""
        practice = BestPractice(
            application="sabnzbd",
            category="performance",
            setting="cache_size",
            recommendation="1000MB",
            explanation="Improves performance",
            priority="high",
            source_url="https://example.com",
        )

        assert practice.application == "sabnzbd"
        assert practice.priority == "high"

    def test_best_practice_priority_validation(self) -> None:
        """Test BestPractice priority validation."""
        # Valid priorities
        for priority in ["high", "medium", "low"]:
            BestPractice(
                application="sabnzbd",
                category="test",
                setting="test",
                recommendation="test",
                explanation="test",
                priority=priority,
                source_url="https://example.com",
            )

        # Invalid priority
        with pytest.raises(ValueError):
            BestPractice(
                application="sabnzbd",
                category="test",
                setting="test",
                recommendation="test",
                explanation="test",
                priority="invalid",
                source_url="https://example.com",
            )


class TestSearch:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_with_cache_hit(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test search with cached results."""
        cached_results = [
            {
                "title": "Cached Result",
                "url": "https://example.com",
                "snippet": "Cached",
                "relevance_score": 0.9,
                "source": "example.com",
            }
        ]
        mock_redis.get.return_value = json.dumps(cached_results)

        query = SearchQuery(query="test query")
        results = await web_search_service.search(query)

        assert len(results) == 1
        assert results[0].title == "Cached Result"
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_without_cache(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test search without cached results."""
        mock_redis.get.return_value = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Test Result",
                        "url": "https://example.com/test",
                        "description": "Test description",
                    }
                ]
            }
        }

        with patch.object(web_search_service.http_client, "get", return_value=mock_response):
            query = SearchQuery(query="test query", max_results=5)
            results = await web_search_service.search(query)

            assert len(results) > 0
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_rate_limit_error(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test search with rate limit error."""
        mock_redis.get.return_value = None

        mock_response = Mock()
        mock_response.status_code = 429

        with patch.object(web_search_service.http_client, "get", return_value=mock_response):
            query = SearchQuery(query="test")

            with pytest.raises(Exception, match="Rate limit exceeded"):
                await web_search_service.search(query)

    @pytest.mark.asyncio
    async def test_search_api_error(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test search with API error."""
        mock_redis.get.return_value = None

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(web_search_service.http_client, "get", return_value=mock_response):
            query = SearchQuery(query="test")

            with pytest.raises(Exception, match="API error"):
                await web_search_service.search(query)

    @pytest.mark.asyncio
    async def test_search_network_error(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test search with network error."""
        mock_redis.get.return_value = None

        with patch.object(
            web_search_service.http_client,
            "get",
            side_effect=httpx.RequestError("Connection failed"),
        ):
            query = SearchQuery(query="test")

            with pytest.raises(Exception, match="Network error"):
                await web_search_service.search(query)


class TestRelevanceScoring:
    """Test relevance score calculation."""

    def test_calculate_relevance_score_exact_match(
        self, web_search_service: WebSearchService
    ) -> None:
        """Test relevance score with exact title match."""
        result = SearchResult(
            title="sabnzbd configuration best practices",
            url="https://sabnzbd.org/config",
            snippet="configuration guide",
            relevance_score=0.0,
            source="sabnzbd.org",
        )

        query = SearchQuery(query="sabnzbd configuration", application="sabnzbd")
        score = web_search_service._calculate_relevance_score(result, query)

        # Should have high score due to title match and authoritative domain
        assert score > 0.5

    def test_calculate_relevance_score_authoritative_domain(
        self, web_search_service: WebSearchService
    ) -> None:
        """Test relevance score boost for authoritative domain."""
        result = SearchResult(
            title="SABnzbd Guide",
            url="https://sabnzbd.org/wiki",
            snippet="Official guide",
            relevance_score=0.0,
            source="sabnzbd.org",
        )

        query = SearchQuery(query="sabnzbd", application="sabnzbd")
        score = web_search_service._calculate_relevance_score(result, query)

        # Should get authority boost
        assert score >= 0.2

    def test_calculate_relevance_score_no_match(self, web_search_service: WebSearchService) -> None:
        """Test relevance score with no keyword matches."""
        result = SearchResult(
            title="Unrelated Content",
            url="https://example.com",
            snippet="Nothing relevant",
            relevance_score=0.0,
            source="example.com",
        )

        query = SearchQuery(query="sabnzbd configuration")
        score = web_search_service._calculate_relevance_score(result, query)

        assert score == 0.0


class TestRankResults:
    """Test result ranking."""

    def test_rank_results_by_score(self, web_search_service: WebSearchService) -> None:
        """Test that results are ranked by relevance score."""
        results = [
            SearchResult(
                title="Low", url="https://a.com", snippet="", relevance_score=0.3, source="a.com"
            ),
            SearchResult(
                title="High", url="https://b.com", snippet="", relevance_score=0.9, source="b.com"
            ),
            SearchResult(
                title="Medium",
                url="https://c.com",
                snippet="",
                relevance_score=0.6,
                source="c.com",
            ),
        ]

        ranked = web_search_service.rank_results(results)

        assert ranked[0].relevance_score == 0.9
        assert ranked[1].relevance_score == 0.6
        assert ranked[2].relevance_score == 0.3

    def test_rank_results_with_limit(self, web_search_service: WebSearchService) -> None:
        """Test ranking with max_results limit."""
        results = [
            SearchResult(
                title=f"Result {i}",
                url=f"https://example.com/{i}",
                snippet="",
                relevance_score=float(i) / 10,
                source="example.com",
            )
            for i in range(10)
        ]

        ranked = web_search_service.rank_results(results, max_results=3)

        assert len(ranked) == 3


class TestContentExtraction:
    """Test content extraction functionality."""

    @pytest.mark.asyncio
    async def test_extract_content_html(self, web_search_service: WebSearchService) -> None:
        """Test extracting content from HTML."""
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Title</h1>
                    <p>This is the main content.</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_content
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = Mock()

        with patch.object(web_search_service.http_client, "get", return_value=mock_response):
            content = await web_search_service.extract_content("https://example.com")

            assert "Title" in content
            assert "main content" in content
            assert "Navigation" not in content  # nav should be removed
            assert "Footer" not in content  # footer should be removed

    @pytest.mark.asyncio
    async def test_extract_content_markdown(self, web_search_service: WebSearchService) -> None:
        """Test extracting content from Markdown."""
        markdown_content = """
        # Heading

        This is markdown content with `inline code`.

        ```python
        def test():
            pass
        ```
        """

        mock_response = Mock()
        mock_response.text = markdown_content
        mock_response.headers = {"content-type": "text/markdown"}
        mock_response.raise_for_status = Mock()

        with patch.object(web_search_service.http_client, "get", return_value=mock_response):
            content = await web_search_service.extract_content("https://example.com/page.md")

            assert "Heading" in content
            assert "markdown content" in content

    @pytest.mark.asyncio
    async def test_extract_content_network_error(
        self, web_search_service: WebSearchService
    ) -> None:
        """Test content extraction with network error."""
        with patch.object(
            web_search_service.http_client,
            "get",
            side_effect=httpx.RequestError("Connection failed"),
        ):
            with pytest.raises(Exception, match="Failed to fetch URL"):
                await web_search_service.extract_content("https://example.com")


class TestBestPracticesExtraction:
    """Test best practices extraction."""

    @pytest.mark.asyncio
    async def test_extract_best_practices_set_pattern(
        self, web_search_service: WebSearchService
    ) -> None:
        """Test extracting best practices with 'set X to Y' pattern."""
        content = """
        Configuration Guide

        Set article_cache to 1000MB for optimal performance.
        Configure ssl to true for secure connections.
        """

        practices = await web_search_service.extract_best_practices(
            content, "sabnzbd", "https://example.com"
        )

        assert len(practices) > 0
        setting_names = {p.setting for p in practices}
        assert "article_cache" in setting_names or "ssl" in setting_names

    @pytest.mark.asyncio
    async def test_extract_best_practices_enable_pattern(
        self, web_search_service: WebSearchService
    ) -> None:
        """Test extracting best practices with enable/disable pattern."""
        content = """
        Security Settings

        Enable https_encryption for all connections.
        Disable unsafe_mode to prevent vulnerabilities.
        """

        practices = await web_search_service.extract_best_practices(
            content, "sabnzbd", "https://example.com"
        )

        assert len(practices) > 0

    def test_identify_category(self, web_search_service: WebSearchService) -> None:
        """Test category identification from text."""
        # Test download category
        category = web_search_service._identify_category("Download Configuration:")
        assert category == "download"

        # Test security category
        category = web_search_service._identify_category("SSL and Security Settings")
        assert category == "security"

        # Test performance category
        category = web_search_service._identify_category("Cache Optimization")
        assert category == "performance"

        # Test non-category text
        category = web_search_service._identify_category(
            "This is a long paragraph without category keywords"
        )
        assert category is None

    def test_determine_priority(self, web_search_service: WebSearchService) -> None:
        """Test priority determination from text."""
        # High priority
        priority = web_search_service._determine_priority("This is critical for security")
        assert priority == "high"

        # Medium priority
        priority = web_search_service._determine_priority("This is recommended for performance")
        assert priority == "medium"

        # Default to medium
        priority = web_search_service._determine_priority("Configure this setting")
        assert priority == "medium"


class TestCaching:
    """Test caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_results_success(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test successful caching of results."""
        results = [
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="",
                relevance_score=0.8,
                source="example.com",
            )
        ]

        cache_key = "test_key"
        await web_search_service._cache_results(cache_key, results)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == cache_key
        assert call_args[0][1] == web_search_service.cache_ttl

    @pytest.mark.asyncio
    async def test_cache_results_no_redis(
        self, web_search_service_no_cache: WebSearchService
    ) -> None:
        """Test caching when Redis is not available."""
        results = [
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="",
                relevance_score=0.8,
                source="example.com",
            )
        ]

        # Should not raise error
        await web_search_service_no_cache._cache_results("test_key", results)

    @pytest.mark.asyncio
    async def test_get_cached_results_success(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test retrieving cached results."""
        cached_data = [
            {
                "title": "Cached",
                "url": "https://example.com",
                "snippet": "Test",
                "relevance_score": 0.9,
                "source": "example.com",
            }
        ]
        mock_redis.get.return_value = json.dumps(cached_data)

        results = await web_search_service._get_cached_results("test_key")

        assert results is not None
        assert len(results) == 1
        assert results[0].title == "Cached"

    @pytest.mark.asyncio
    async def test_get_cached_results_cache_miss(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test cache miss."""
        mock_redis.get.return_value = None

        results = await web_search_service._get_cached_results("test_key")

        assert results is None

    @pytest.mark.asyncio
    async def test_invalidate_cache(
        self, web_search_service: WebSearchService, mock_redis: AsyncMock
    ) -> None:
        """Test cache invalidation."""
        await web_search_service.invalidate_cache("test query")

        mock_redis.delete.assert_called_once()

    def test_get_cache_key(self, web_search_service: WebSearchService) -> None:
        """Test cache key generation."""
        key1 = web_search_service._get_cache_key("search", "test query")
        key2 = web_search_service._get_cache_key("search", "test query")
        key3 = web_search_service._get_cache_key("search", "different query")

        # Same input should generate same key
        assert key1 == key2

        # Different input should generate different key
        assert key1 != key3

        # Key should have prefix
        assert key1.startswith("search:")


class TestHTMLParsing:
    """Test HTML parsing functionality."""

    def test_parse_html_removes_scripts(self, web_search_service: WebSearchService) -> None:
        """Test that script tags are removed."""
        html = """
        <html>
            <body>
                <p>Content</p>
                <script>alert('test');</script>
                <p>More content</p>
            </body>
        </html>
        """

        text = web_search_service._parse_html(html)

        assert "Content" in text
        assert "More content" in text
        assert "alert" not in text

    def test_parse_html_removes_navigation(self, web_search_service: WebSearchService) -> None:
        """Test that navigation elements are removed."""
        html = """
        <html>
            <body>
                <nav>Navigation Menu</nav>
                <main>Main Content</main>
            </body>
        </html>
        """

        text = web_search_service._parse_html(html)

        assert "Main Content" in text
        assert "Navigation Menu" not in text

    def test_parse_html_cleans_whitespace(self, web_search_service: WebSearchService) -> None:
        """Test that excessive whitespace is cleaned."""
        html = """
        <html>
            <body>
                <p>Line   1</p>


                <p>Line   2</p>
            </body>
        </html>
        """

        text = web_search_service._parse_html(html)

        # Should not have excessive blank lines
        assert "\n\n\n" not in text


class TestMarkdownParsing:
    """Test Markdown parsing functionality."""

    def test_parse_markdown_removes_code_blocks(self, web_search_service: WebSearchService) -> None:
        """Test that code block markers are removed."""
        markdown = """
        # Heading

        ```python
        def test():
            pass
        ```

        More content
        """

        text = web_search_service._parse_markdown(markdown)

        assert "Heading" in text
        assert "More content" in text
        assert "```" not in text

    def test_parse_markdown_removes_inline_code(self, web_search_service: WebSearchService) -> None:
        """Test that inline code markers are removed."""
        markdown = "This is `inline code` in text"

        text = web_search_service._parse_markdown(markdown)

        assert "inline code" in text
        assert "`" not in text


class TestClose:
    """Test resource cleanup."""

    @pytest.mark.asyncio
    async def test_close_cleanup(self, web_search_service: WebSearchService) -> None:
        """Test that close cleans up resources."""
        with patch.object(web_search_service.http_client, "aclose") as mock_close:
            with patch.object(web_search_service.redis_client, "close") as mock_redis_close:
                await web_search_service.close()

                mock_close.assert_called_once()
                mock_redis_close.assert_called_once()
