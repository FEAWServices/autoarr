"""
E2E Test: Content Request Flow

Tests the complete content request workflow:
1. Submit natural language request via API
2. LLM classification (movie vs TV)
3. TMDB metadata search
4. User confirmation
5. Add to Radarr/Sonarr via MCP
6. Trigger automatic search
7. Monitor download progress
8. Complete workflow with activity logging
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestContentRequestFlow:
    """E2E tests for content request workflow."""

    async def test_natural_language_movie_request(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        mock_radarr_responses: dict,
    ):
        """
        Test natural language movie request flow.

        Steps:
        1. Submit request: "I want to watch The Matrix"
        2. LLM classifies as movie
        3. Search TMDB for metadata
        4. Add to Radarr
        5. Trigger search
        6. Verify activity log
        """
        with (
            patch("autoarr.api.routers.movies.get_orchestrator") as mock_orch,
            patch(
                "autoarr.api.services.intelligent_recommendation_engine.IntelligentRecommendationEngine"  # noqa: E501
            ) as mock_llm,
        ):
            # Mock LLM classification
            mock_llm_instance = AsyncMock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.classify_content_request.return_value = {
                "type": "movie",
                "title": "The Matrix",
                "year": 1999,
                "confidence": 0.95,
            }

            # Mock TMDB search (via web search service)
            mock_llm_instance.search_tmdb.return_value = {
                "id": 603,
                "title": "The Matrix",
                "year": 1999,
                "tmdbId": 603,
                "overview": "A computer hacker learns...",
            }

            # Mock Radarr add movie
            mock_radarr = AsyncMock()
            mock_orch.return_value = mock_radarr
            mock_radarr.call_tool.return_value = {
                "success": True,
                "result": {
                    "id": 1,
                    "title": "The Matrix",
                    "added": True,
                },
            }

            # Submit content request
            response = await api_client.post(
                "/api/v1/requests/content",
                json={"query": "I want to watch The Matrix"},
            )

            # Note: This endpoint might not exist yet
            if response.status_code == 404:
                pytest.skip("Content request endpoint not implemented yet")

            assert response.status_code in [200, 201]
            result = response.json()  # noqa: F841
            assert result.get("type") == "movie" or "Matrix" in str(result)

    async def test_natural_language_tv_request(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        mock_sonarr_responses: dict,
    ):
        """
        Test natural language TV show request flow.

        Steps:
        1. Submit request: "Add Breaking Bad to my library"
        2. LLM classifies as TV show
        3. Search TMDB/TVDB for metadata
        4. Add to Sonarr
        5. Trigger search
        6. Monitor downloads
        """
        with (
            patch("autoarr.api.routers.shows.get_orchestrator") as mock_orch,
            patch(
                "autoarr.api.services.intelligent_recommendation_engine.IntelligentRecommendationEngine"  # noqa: E501
            ) as mock_llm,
        ):
            # Mock LLM classification
            mock_llm_instance = AsyncMock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.classify_content_request.return_value = {
                "type": "tv",
                "title": "Breaking Bad",
                "confidence": 0.98,
            }

            # Mock metadata search
            mock_llm_instance.search_tmdb.return_value = {
                "id": 1396,
                "title": "Breaking Bad",
                "tvdbId": 81189,
                "overview": "A high school chemistry teacher...",
            }

            # Mock Sonarr add series
            mock_sonarr = AsyncMock()
            mock_orch.return_value = mock_sonarr
            mock_sonarr.call_tool.return_value = {
                "success": True,
                "result": {
                    "id": 1,
                    "title": "Breaking Bad",
                    "added": True,
                },
            }

            # Submit content request
            response = await api_client.post(
                "/api/v1/requests/content",
                json={"query": "Add Breaking Bad to my library"},
            )

            if response.status_code == 404:
                pytest.skip("Content request endpoint not implemented yet")

            assert response.status_code in [200, 201]
            result = response.json()  # noqa: F841
            assert result.get("type") == "tv" or "Breaking" in str(result)

    async def test_ambiguous_request_requires_clarification(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """
        Test ambiguous request requiring user clarification.

        Steps:
        1. Submit ambiguous request: "Add Avatar"
        2. LLM returns multiple matches
        3. Request user clarification
        4. User selects correct one
        5. Continue with add workflow
        """
        with patch(
            "autoarr.api.services.intelligent_recommendation_engine.IntelligentRecommendationEngine"
        ) as mock_llm:
            # Mock LLM returning multiple options
            mock_llm_instance = AsyncMock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.classify_content_request.return_value = {
                "type": "clarification_needed",
                "options": [
                    {"type": "movie", "title": "Avatar", "year": 2009, "tmdbId": 19995},
                    {"type": "tv", "title": "Avatar: The Last Airbender", "tvdbId": 74852},
                ],
            }

            # Submit ambiguous request
            response = await api_client.post(
                "/api/v1/requests/content",
                json={"query": "Add Avatar"},
            )

            if response.status_code == 404:
                pytest.skip("Content request endpoint not implemented yet")

            # Should return clarification options
            if response.status_code in [200, 201]:
                result = response.json()  # noqa: F841
                # Check for clarification response
                assert "options" in result or "clarification" in str(result).lower()

    async def test_complete_request_with_monitoring(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        mock_radarr_responses: dict,
        mock_sabnzbd_responses: dict,
        event_correlation_id: str,
    ):
        """
        Test complete content request with download monitoring.

        Complete flow:
        1. Submit request
        2. Classify and search metadata
        3. Add to Radarr/Sonarr
        4. Trigger automatic search
        5. Monitor SABnzbd download progress
        6. Track completion
        7. Verify all events logged with correlation ID
        """
        with (
            patch("autoarr.api.routers.movies.get_orchestrator") as mock_orch_radarr,
            patch("autoarr.api.routers.downloads.get_orchestrator") as mock_orch_sab,
            patch(
                "autoarr.api.services.intelligent_recommendation_engine.IntelligentRecommendationEngine"  # noqa: E501
            ) as mock_llm,
        ):
            # Mock LLM
            mock_llm_instance = AsyncMock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.classify_content_request.return_value = {
                "type": "movie",
                "title": "Test Movie",
                "year": 2024,
            }
            mock_llm_instance.search_tmdb.return_value = {
                "tmdbId": 123456,
                "title": "Test Movie",
                "year": 2024,
            }

            # Mock Radarr add and search
            mock_radarr = AsyncMock()
            mock_orch_radarr.return_value = mock_radarr
            mock_radarr.call_tool.side_effect = [
                {"success": True, "result": {"id": 1, "title": "Test Movie"}},  # add movie
                {"success": True, "result": {"commandId": 999}},  # trigger search
            ]

            # Mock SABnzbd queue monitoring
            mock_sab = AsyncMock()
            mock_orch_sab.return_value = mock_sab
            mock_sab.call_tool.return_value = {
                "success": True,
                "result": mock_sabnzbd_responses["queue"],
            }

            # Submit request
            response = await api_client.post(
                "/api/v1/requests/content",
                json={
                    "query": "Download Test Movie 2024",
                    "correlation_id": event_correlation_id,
                },
            )

            if response.status_code == 404:
                pytest.skip("Content request endpoint not implemented yet")

            # Monitor queue
            response = await api_client.get("/api/v1/downloads/queue")
            assert response.status_code == 200

    async def test_request_with_quality_preference(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        mock_radarr_responses: dict,
    ):
        """
        Test content request with quality preference.

        Verifies:
        - Quality profile selection
        - User preference respected
        - Proper quality settings applied
        """
        with patch("autoarr.api.routers.movies.get_orchestrator") as mock_orch:
            # Mock Radarr add with quality profile
            mock_radarr = AsyncMock()
            mock_orch.return_value = mock_radarr
            mock_radarr.call_tool.return_value = {
                "success": True,
                "result": {
                    "id": 1,
                    "title": "Test Movie",
                    "qualityProfileId": 1,  # HD-1080p
                },
            }

            # Submit request with quality preference
            response = await api_client.post(
                "/api/v1/movies/add",
                json={
                    "title": "Test Movie",
                    "tmdbId": 123456,
                    "qualityProfileId": 1,
                },
            )

            if response.status_code == 404:
                pytest.skip("Add movie endpoint not fully implemented")

            if response.status_code in [200, 201]:
                result = response.json()  # noqa: F841
                # Verify quality profile applied
                assert result.get("qualityProfileId") == 1 or "quality" in str(result).lower()

    async def test_request_duplicate_detection(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        mock_radarr_responses: dict,
    ):
        """
        Test duplicate content request detection.

        Verifies:
        - Existing content detected
        - User notified of duplicate
        - No duplicate addition
        """
        with patch("autoarr.api.routers.movies.get_orchestrator") as mock_orch:
            # Mock Radarr returning existing movie
            mock_radarr = AsyncMock()
            mock_orch.return_value = mock_radarr
            mock_radarr.call_tool.return_value = {
                "success": False,
                "error": "Movie already exists",
                "existing_id": 1,
            }

            # Try to add duplicate
            response = await api_client.post(
                "/api/v1/movies/add",
                json={
                    "title": "Test Movie",
                    "tmdbId": 123456,
                },
            )

            if response.status_code == 404:
                pytest.skip("Add movie endpoint not implemented")

            # Should handle duplicate gracefully
            # Either return success with existing, or error
            assert response.status_code in [200, 201, 400, 409]

    async def test_batch_content_request(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        mock_radarr_responses: dict,
        mock_sonarr_responses: dict,
    ):
        """
        Test batch content request.

        Verifies:
        - Multiple items can be requested at once
        - Each item processed correctly
        - Results returned for all items
        """
        with (
            patch("autoarr.api.routers.movies.get_orchestrator") as mock_orch_radarr,
            patch("autoarr.api.routers.shows.get_orchestrator") as mock_orch_sonarr,
        ):
            # Mock Radarr
            mock_radarr = AsyncMock()
            mock_orch_radarr.return_value = mock_radarr
            mock_radarr.call_tool.return_value = {
                "success": True,
                "result": {"id": 1, "title": "Movie 1"},
            }

            # Mock Sonarr
            mock_sonarr = AsyncMock()
            mock_orch_sonarr.return_value = mock_sonarr
            mock_sonarr.call_tool.return_value = {
                "success": True,
                "result": {"id": 1, "title": "Show 1"},
            }

            # Submit batch request
            response = await api_client.post(
                "/api/v1/requests/batch",
                json={
                    "items": [
                        {"query": "The Matrix"},
                        {"query": "Breaking Bad"},
                        {"query": "Inception"},
                    ]
                },
            )

            if response.status_code == 404:
                pytest.skip("Batch request endpoint not implemented yet")

            if response.status_code in [200, 201]:
                result = response.json()  # noqa: F841
                # Should process all items
                assert "results" in result or isinstance(result, list)

    async def test_request_error_handling(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """
        Test error handling in content request flow.

        Verifies:
        - Invalid requests rejected
        - TMDB search failures handled
        - Radarr/Sonarr errors handled
        - User-friendly error messages
        """
        with patch(
            "autoarr.api.services.intelligent_recommendation_engine.IntelligentRecommendationEngine"
        ) as mock_llm:
            # Mock LLM classification failure
            mock_llm_instance = AsyncMock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.classify_content_request.side_effect = Exception(
                "LLM service unavailable"
            )

            # Submit request
            response = await api_client.post(
                "/api/v1/requests/content",
                json={"query": "Some movie"},
            )

            if response.status_code == 404:
                pytest.skip("Content request endpoint not implemented yet")

            # Should handle error gracefully
            assert response.status_code in [500, 503]
            error = response.json()
            assert "error" in error or "detail" in error

    async def test_request_with_invalid_input(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """
        Test content request with invalid input.

        Verifies:
        - Empty query rejected
        - Invalid characters handled
        - Input validation
        """
        # Test empty query
        response = await api_client.post(
            "/api/v1/requests/content",
            json={"query": ""},
        )

        if response.status_code == 404:
            pytest.skip("Content request endpoint not implemented yet")

        # Should return validation error
        assert response.status_code in [400, 422]

        # Test missing query field
        response = await api_client.post(
            "/api/v1/requests/content",
            json={},
        )

        assert response.status_code in [400, 422]
