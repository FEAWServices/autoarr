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
Integration tests for Chat API endpoints.

Tests the complete flow from API endpoint through the ChatAgent service,
including topic classification, intent detection, and response generation.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from autoarr.api.services.chat_agent import ChatResponse, TopicClassification, QueryTopic, ChatIntent


@pytest.fixture
def mock_chat_response():
    """Create a default mock chat response."""
    return ChatResponse(
        message="This is a test response about SABnzbd configuration.",
        topic="sabnzbd",
        intent="help",
        sources=[],
        suggestions=["How to set up categories?", "Configure news servers"],
        confidence=0.85,
        service_required=None,
        setup_link=None,
    )


@pytest.fixture
def mock_classification():
    """Create a default mock classification."""
    return TopicClassification(
        topic=QueryTopic.SABNZBD,
        intent=ChatIntent.HELP,
        confidence=0.85,
        entities={},
        needs_docs=True,
    )


@pytest.fixture
async def test_app():
    """Create FastAPI app for testing."""
    from autoarr.api.main import app
    from autoarr.api.routers.chat import reset_chat_agent

    # Reset the chat agent singleton before each test
    reset_chat_agent()
    yield app


@pytest.mark.asyncio
class TestChatMessageEndpoint:
    """Integration tests for POST /api/v1/chat/message endpoint."""

    async def test_send_simple_help_message(self, test_app, mock_chat_response):
        """Test sending a simple help message about SABnzbd."""
        with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
            # Configure mock to return response as async coroutine
            mock_chat.return_value = mock_chat_response

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/chat/message",
                    json={"message": "How do I configure SABnzbd?"},
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "message" in data
                assert "topic" in data
                assert "intent" in data
                assert "confidence" in data
                assert "suggestions" in data
                assert "sources" in data

                # Verify message content
                assert data["message"] == mock_chat_response.message
                assert data["topic"] == mock_chat_response.topic
                assert isinstance(data["confidence"], float)
                assert 0.0 <= data["confidence"] <= 1.0

    async def test_send_message_with_conversation_history(self, test_app, mock_chat_response):
        """Test sending a message with conversation history for context."""
        with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
            mock_chat.return_value = mock_chat_response

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/chat/message",
                    json={
                        "message": "Can I set up multiple categories?",
                        "conversation_id": "conv_123",
                        "history": [
                            {"role": "user", "content": "How do I configure SABnzbd?"},
                            {"role": "assistant", "content": "SABnzbd is a Usenet..."},
                        ],
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "message" in data

                # Verify the chat agent was called with history
                mock_chat.assert_called_once()
                call_kwargs = mock_chat.call_args.kwargs
                assert "conversation_history" in call_kwargs
                assert call_kwargs["conversation_history"] is not None

    async def test_send_empty_message(self, test_app):
        """Test that empty messages are rejected."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/message",
                json={"message": ""},
            )

            # Should fail validation
            assert response.status_code == 422

    async def test_send_message_llm_error_handling(self, test_app):
        """Test handling of LLM errors with proper error messages."""
        with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
            # Configure mock to raise an error
            mock_chat.side_effect = Exception("429 Too Many Requests")

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/chat/message",
                    json={"message": "How do I configure SABnzbd?"},
                )

                assert response.status_code == 429
                data = response.json()
                assert "detail" in data
                assert "rate limit" in data["detail"].lower()

    async def test_content_request_detection(self, test_app):
        """Test that content requests are properly detected."""
        content_response = ChatResponse(
            message="I'll help you download The Matrix...",
            topic="content_request",
            intent="download",
            sources=[],
            suggestions=[],
            confidence=0.9,
            service_required="radarr",
            setup_link="/settings",
        )

        with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
            mock_chat.return_value = content_response

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/chat/message",
                    json={"message": "Download The Matrix"},
                )

                assert response.status_code == 200
                data = response.json()

                # Verify content request was detected
                assert data["is_content_request"] is True
                assert data["service_required"] == "radarr"


@pytest.mark.asyncio
class TestChatClassifyEndpoint:
    """Integration tests for POST /api/v1/chat/classify endpoint."""

    async def test_classify_sabnzbd_query(self, test_app, mock_classification):
        """Test classifying a SABnzbd-related query."""
        with patch("autoarr.api.services.chat_agent.ChatAgent.classify_query") as mock_classify:
            mock_classify.return_value = mock_classification

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/chat/classify",
                    json={"message": "How do I configure SABnzbd?"},
                )

                assert response.status_code == 200
                data = response.json()

                # Verify classification structure
                assert "topic" in data
                assert "intent" in data
                assert "confidence" in data
                assert "entities" in data
                assert "needs_docs" in data

                # Verify types
                assert isinstance(data["confidence"], float)
                assert isinstance(data["entities"], dict)
                assert isinstance(data["needs_docs"], bool)
                assert 0.0 <= data["confidence"] <= 1.0

    async def test_classify_content_request(self, test_app):
        """Test classifying a content download request."""
        content_classification = TopicClassification(
            topic=QueryTopic.CONTENT_REQUEST,
            intent=ChatIntent.DOWNLOAD,
            confidence=0.9,
            entities={"title": "The Matrix"},
            needs_docs=False,
        )

        with patch("autoarr.api.services.chat_agent.ChatAgent.classify_query") as mock_classify:
            mock_classify.return_value = content_classification

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/chat/classify",
                    json={"message": "Download The Matrix"},
                )

                assert response.status_code == 200
                data = response.json()

                assert data["topic"] == "content_request"
                assert data["intent"] == "download"

    async def test_classify_empty_message(self, test_app):
        """Test that empty messages are rejected during classification."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/classify",
                json={"message": ""},
            )

            # Should fail validation
            assert response.status_code == 422


@pytest.mark.asyncio
class TestChatTopicsEndpoint:
    """Integration tests for GET /api/v1/chat/topics endpoint."""

    async def test_get_supported_topics(self, test_app):
        """Test retrieving the list of supported topics."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.get("/api/v1/chat/topics")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "topics" in data
            assert "suggestions" in data

            # Verify topics list
            topics = data["topics"]
            assert len(topics) >= 4  # At least SABnzbd, Sonarr, Radarr, Plex

            # Verify each topic has required fields
            for topic in topics:
                assert "id" in topic
                assert "name" in topic
                assert "description" in topic
                assert "icon" in topic

            # Verify core topics are present
            topic_ids = {t["id"] for t in topics}
            assert "sabnzbd" in topic_ids
            assert "sonarr" in topic_ids
            assert "radarr" in topic_ids
            assert "plex" in topic_ids

            # Verify suggestions
            suggestions = data["suggestions"]
            assert len(suggestions) >= 3
            assert all(isinstance(s, str) for s in suggestions)


@pytest.mark.asyncio
class TestChatAgentIntegration:
    """Integration tests for ChatAgent service with API endpoints."""

    async def test_error_message_formatting(self, test_app):
        """Test that error messages are properly formatted and user-friendly."""
        error_scenarios = [
            ("401 Unauthorized", 401, "api key"),
            ("402 Payment Required", 402, "credits"),
            ("Some other error", 500, "failed"),
        ]

        for error_msg, expected_status, expected_content in error_scenarios:
            with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
                mock_chat.side_effect = Exception(error_msg)

                async with AsyncClient(app=test_app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/chat/message",
                        json={"message": "Test question"},
                    )

                    assert response.status_code == expected_status
                    data = response.json()
                    assert "detail" in data
                    assert expected_content in data["detail"].lower()

    async def test_chat_agent_with_different_query_types(self, test_app):
        """Test that different query types are handled appropriately."""
        query_scenarios = [
            ("How do I configure SABnzbd?", "sabnzbd", "help"),
            ("Why isn't Sonarr working?", "sonarr", "troubleshoot"),
            ("Configure Radarr quality profiles", "radarr", "configure"),
            ("Download The Matrix", "content_request", "download"),
        ]

        for query, expected_topic, expected_intent in query_scenarios:
            mock_response = ChatResponse(
                message=f"Response for {query}",
                topic=expected_topic,
                intent=expected_intent,
                sources=[],
                suggestions=[],
                confidence=0.85,
            )

            with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
                mock_chat.return_value = mock_response

                async with AsyncClient(app=test_app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/chat/message",
                        json={"message": query},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["topic"] == expected_topic
                    assert data["intent"] == expected_intent


@pytest.mark.asyncio
class TestChatEndpointValidation:
    """Integration tests for input validation and error handling."""

    async def test_message_length_validation(self, test_app):
        """Test that overly long messages are rejected."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Create a message longer than 2000 characters
            long_message = "a" * 2001

            response = await client.post(
                "/api/v1/chat/message",
                json={"message": long_message},
            )

            # Should fail validation
            assert response.status_code == 422

    async def test_invalid_conversation_history(self, test_app, mock_chat_response):
        """Test handling of invalid conversation history format."""
        with patch("autoarr.api.services.chat_agent.ChatAgent.chat_with_tools") as mock_chat:
            mock_chat.return_value = mock_chat_response

            async with AsyncClient(app=test_app, base_url="http://test") as client:
                # Invalid history format (not a list of dicts)
                response = await client.post(
                    "/api/v1/chat/message",
                    json={
                        "message": "Test",
                        "history": "invalid",
                    },
                )

                # Should fail validation
                assert response.status_code == 422
