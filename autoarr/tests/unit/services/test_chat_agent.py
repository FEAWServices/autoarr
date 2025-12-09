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
Unit tests for Chat Agent service.

This module tests the chat agent's ability to classify queries, generate responses,
fetch documentation, check service status, and handle tool calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoarr.api.services.chat_agent import (
    ChatAgent,
    ChatIntent,
    ChatResponse,
    QueryTopic,
    ServiceStatus,
    TopicClassification,
    get_random_encouragement,
    get_random_fun_fact,
    get_random_greeting,
    get_random_success,
    get_random_troubleshoot_intro,
)
from autoarr.shared.llm import LLMMessage, LLMResponse, LLMResponseWithTools, ToolCall


class TestRandomResponses:
    """Tests for random response generators."""

    def test_get_random_greeting_returns_string(self) -> None:
        """Test that random greeting returns a string."""
        greeting = get_random_greeting()
        assert isinstance(greeting, str)
        assert len(greeting) > 0

    def test_get_random_fun_fact_returns_string(self) -> None:
        """Test that random fun fact returns a string."""
        fact = get_random_fun_fact()
        assert isinstance(fact, str)
        assert len(fact) > 0

    def test_get_random_encouragement_returns_string(self) -> None:
        """Test that random encouragement returns a string."""
        encouragement = get_random_encouragement()
        assert isinstance(encouragement, str)
        assert len(encouragement) > 0

    def test_get_random_troubleshoot_intro_returns_string(self) -> None:
        """Test that random troubleshoot intro returns a string."""
        intro = get_random_troubleshoot_intro()
        assert isinstance(intro, str)
        assert len(intro) > 0

    def test_get_random_success_returns_string(self) -> None:
        """Test that random success message returns a string."""
        success = get_random_success()
        assert isinstance(success, str)
        assert len(success) > 0


class TestChatAgentInitialization:
    """Tests for ChatAgent initialization."""

    def test_init_with_provider(self) -> None:
        """Test initialization with a provider."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider=mock_provider)
        assert agent._provider == mock_provider
        assert not agent._initialized

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        agent = ChatAgent(api_key="test-key")
        assert agent._api_key == "test-key"
        assert agent._model == "anthropic/claude-3.5-sonnet"

    def test_init_with_custom_model(self) -> None:
        """Test initialization with custom model."""
        agent = ChatAgent(api_key="test-key", model="custom-model")
        assert agent._model == "custom-model"

    def test_init_with_brave_api_key(self) -> None:
        """Test initialization with Brave API key."""
        agent = ChatAgent(brave_api_key="brave-key")
        assert agent._brave_api_key == "brave-key"

    def test_init_with_service_versions(self) -> None:
        """Test initialization with service versions."""
        versions = {"sonarr": "3.0.0", "radarr": "4.0.0"}
        agent = ChatAgent(service_versions=versions)
        assert agent._service_versions == versions

    def test_build_autoarr_knowledge(self) -> None:
        """Test that AutoArr knowledge base is built."""
        agent = ChatAgent()
        knowledge = agent._autoarr_knowledge
        assert "Configuration Audit" in knowledge
        assert "Natural Language Requests" in knowledge
        assert "Activity Monitoring" in knowledge


class TestQueryClassification:
    """Tests for query classification."""

    def test_classify_sabnzbd_query(self) -> None:
        """Test classification of SABnzbd query."""
        agent = ChatAgent()
        classification = agent.classify_query("How do I configure SABnzbd queue settings?")
        assert classification.topic == QueryTopic.SABNZBD
        assert classification.intent == ChatIntent.CONFIGURE
        assert classification.confidence > 0

    def test_classify_sonarr_query(self) -> None:
        """Test classification of Sonarr query."""
        agent = ChatAgent()
        classification = agent.classify_query("How to set up Sonarr quality profiles?")
        assert classification.topic == QueryTopic.SONARR
        assert classification.intent == ChatIntent.CONFIGURE

    def test_classify_radarr_query(self) -> None:
        """Test classification of Radarr query."""
        agent = ChatAgent()
        classification = agent.classify_query("What are Radarr custom formats?")
        assert classification.topic == QueryTopic.RADARR
        assert classification.intent in [ChatIntent.EXPLAIN, ChatIntent.HELP]

    def test_classify_plex_query(self) -> None:
        """Test classification of Plex query."""
        agent = ChatAgent()
        classification = agent.classify_query("How to enable Plex hardware transcoding?")
        assert classification.topic == QueryTopic.PLEX
        assert classification.intent == ChatIntent.CONFIGURE

    def test_classify_autoarr_query(self) -> None:
        """Test classification of AutoArr query."""
        agent = ChatAgent()
        classification = agent.classify_query("How do I run a config audit in AutoArr?")
        assert classification.topic == QueryTopic.AUTOARR
        assert classification.intent in [ChatIntent.HELP, ChatIntent.CONFIGURE]

    def test_classify_content_request(self) -> None:
        """Test classification of content request."""
        agent = ChatAgent()
        classification = agent.classify_query("Download The Matrix for me")
        assert classification.topic == QueryTopic.CONTENT_REQUEST
        assert classification.intent == ChatIntent.DOWNLOAD

    def test_classify_off_topic_query(self) -> None:
        """Test classification of off-topic query."""
        agent = ChatAgent()
        classification = agent.classify_query("What's the weather today?")
        assert classification.topic == QueryTopic.OFF_TOPIC
        assert classification.confidence < 0.5

    def test_classify_help_intent(self) -> None:
        """Test classification of help intent."""
        agent = ChatAgent()
        classification = agent.classify_query("How do I set up Sonarr?")
        assert classification.intent in [ChatIntent.HELP, ChatIntent.CONFIGURE]

    def test_classify_troubleshoot_intent(self) -> None:
        """Test classification of troubleshoot intent."""
        agent = ChatAgent()
        classification = agent.classify_query("SABnzbd not working")
        assert classification.intent == ChatIntent.TROUBLESHOOT

    def test_classify_status_intent(self) -> None:
        """Test classification of status intent."""
        agent = ChatAgent()
        classification = agent.classify_query("Is Sonarr connected?")
        assert classification.intent == ChatIntent.STATUS

    def test_classify_search_intent(self) -> None:
        """Test classification of search intent."""
        agent = ChatAgent()
        classification = agent.classify_query("Find The Office for me")
        assert classification.intent == ChatIntent.SEARCH

    def test_needs_docs_for_help_query(self) -> None:
        """Test that help queries need documentation."""
        agent = ChatAgent()
        classification = agent.classify_query("How do I configure SABnzbd?")
        assert classification.needs_docs is True

    def test_no_docs_for_off_topic(self) -> None:
        """Test that off-topic queries don't need docs."""
        agent = ChatAgent()
        classification = agent.classify_query("Hello!")
        assert classification.needs_docs is False


class TestEntityExtraction:
    """Tests for entity extraction."""

    def test_extract_version_number(self) -> None:
        """Test extraction of version number."""
        agent = ChatAgent()
        classification = agent.classify_query("How to use Sonarr v3.0.10?")
        assert "version" in classification.entities
        assert classification.entities["version"] == "3.0.10"

    def test_extract_quality_profile_feature(self) -> None:
        """Test extraction of quality profile feature."""
        agent = ChatAgent()
        classification = agent.classify_query("How do quality profiles work in Sonarr?")
        assert classification.entities.get("feature") == "quality_profile"

    def test_extract_sabnzbd_setting(self) -> None:
        """Test extraction of SABnzbd setting."""
        agent = ChatAgent()
        classification = agent.classify_query("What is article cache in SABnzbd?")
        assert classification.entities.get("setting") == "article_cache"


@pytest.mark.asyncio
class TestChatAgentProviderInit:
    """Tests for provider initialization."""

    async def test_ensure_provider_with_existing_provider(self) -> None:
        """Test that existing provider is returned."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider=mock_provider)
        agent._initialized = True
        provider = await agent._ensure_provider()
        assert provider == mock_provider

    async def test_ensure_provider_with_api_key(self) -> None:
        """Test provider creation with API key."""
        with patch(
            "autoarr.shared.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_openrouter_class:
            mock_provider = MagicMock()
            mock_openrouter_class.return_value = mock_provider
            agent = ChatAgent(api_key="test-key", model="test-model")
            provider = await agent._ensure_provider()
            assert provider == mock_provider
            assert agent._initialized is True

    async def test_ensure_provider_with_factory(self) -> None:
        """Test provider creation using factory."""
        with patch("autoarr.api.services.chat_agent.LLMProviderFactory") as mock_factory:
            mock_provider = MagicMock()
            mock_factory.create_provider = AsyncMock(return_value=mock_provider)
            agent = ChatAgent()
            provider = await agent._ensure_provider()
            assert provider == mock_provider
            mock_factory.create_provider.assert_called_once()

    async def test_ensure_web_search_with_brave_key(self) -> None:
        """Test web search initialization with Brave API key."""
        with patch("autoarr.api.services.web_search_service.WebSearchService") as mock_web_search:
            mock_search = MagicMock()
            mock_web_search.return_value = mock_search
            agent = ChatAgent(brave_api_key="brave-key")
            search = await agent._ensure_web_search()
            assert search == mock_search

    async def test_ensure_web_search_without_brave_key(self) -> None:
        """Test web search initialization without Brave API key."""
        agent = ChatAgent()
        search = await agent._ensure_web_search()
        assert search is None


@pytest.mark.asyncio
class TestChatMethod:
    """Tests for the main chat method."""

    async def test_chat_off_topic_returns_welcome(self) -> None:
        """Test that off-topic query returns welcome response."""
        with patch.object(ChatAgent, "_get_services_status") as mock_status:
            mock_status.return_value = {}
            with patch.object(ChatAgent, "_generate_welcome_response") as mock_welcome:
                mock_welcome.return_value = ChatResponse(
                    message="Welcome!",
                    topic=QueryTopic.OFF_TOPIC.value,
                    intent=ChatIntent.HELP.value,
                )
                agent = ChatAgent()
                response = await agent.chat("Hello!")
                assert response.topic == QueryTopic.OFF_TOPIC.value
                mock_status.assert_called_once()
                mock_welcome.assert_called_once()

    async def test_chat_content_request(self) -> None:
        """Test content request returns appropriate response."""
        agent = ChatAgent()
        response = await agent.chat("Download The Matrix")
        assert response.topic == QueryTopic.CONTENT_REQUEST.value
        assert "search" in response.message.lower()

    async def test_chat_with_conversation_history(self) -> None:
        """Test chat with conversation history."""
        with patch.object(ChatAgent, "_ensure_provider") as mock_provider_method:
            with patch.object(ChatAgent, "_get_services_status") as mock_services_status:
                # Mock SABnzbd as connected so the chat continues instead of returning setup response
                mock_services_status.return_value = {
                    "sabnzbd": ServiceStatus(name="sabnzbd", connected=True, healthy=True)
                }
                mock_llm = MagicMock()
                mock_llm.complete = AsyncMock(
                    return_value=LLMResponse(
                        content="SABnzbd is a download client.",
                        model="test-model",
                        provider="test-provider",
                    )
                )
                mock_provider_method.return_value = mock_llm
                agent = ChatAgent()
                history = [{"role": "user", "content": "What is SABnzbd?"}]
                response = await agent.chat(
                    "Tell me more about SABnzbd", conversation_history=history
                )
                assert response.message == "SABnzbd is a download client."
                # Verify history was passed to LLM
                call_args = mock_llm.complete.call_args
                if call_args:
                    messages = call_args.kwargs.get("messages", [])
                    # Should have system + history + new message
                    assert len(messages) >= 2

    async def test_chat_with_autoarr_knowledge(self) -> None:
        """Test that AutoArr queries use internal knowledge."""
        with patch.object(ChatAgent, "_ensure_provider") as mock_provider_method:
            mock_llm = MagicMock()
            mock_llm.complete = AsyncMock(
                return_value=LLMResponse(
                    content="Config audit helps...",
                    model="test-model",
                    provider="test-provider",
                )
            )
            mock_provider_method.return_value = mock_llm
            agent = ChatAgent()
            response = await agent.chat("What is config audit in AutoArr?")
            assert response.topic == QueryTopic.AUTOARR.value
            # Verify knowledge was included in context
            call_args = mock_llm.complete.call_args
            if call_args:
                messages = call_args.kwargs.get("messages", [])
                user_messages = [m.content for m in messages if m.role == "user"]
                assert any("AutoArr Documentation" in msg for msg in user_messages)

    async def test_chat_generates_suggestions(self) -> None:
        """Test that suggestions are generated."""
        with patch.object(ChatAgent, "_ensure_provider") as mock_provider_method:
            mock_llm = MagicMock()
            mock_llm.complete = AsyncMock(
                return_value=LLMResponse(
                    content="SABnzbd info...", model="test-model", provider="test-provider"
                )
            )
            mock_provider_method.return_value = mock_llm
            agent = ChatAgent()
            response = await agent.chat("How do I configure SABnzbd?")
            assert len(response.suggestions) > 0
            assert any("sabnzbd" in s.lower() for s in response.suggestions)


@pytest.mark.asyncio
class TestServiceStatus:
    """Tests for service status checking."""

    async def test_get_services_status_all_connected(self) -> None:
        """Test getting status when all services are connected."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Mock health responses
            mock_health_response = MagicMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {
                "circuit_breaker_state": "closed",
                "healthy": True,
            }
            mock_client.get.return_value = mock_health_response

            agent = ChatAgent()
            status = await agent._get_services_status()

            assert "sabnzbd" in status
            assert status["sabnzbd"].connected is True
            assert status["sabnzbd"].healthy is True

    async def test_get_services_status_unconfigured(self) -> None:
        """Test getting status when services are unconfigured."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Mock health response showing unconfigured
            mock_health_response = MagicMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {
                "circuit_breaker_state": "unconfigured",
                "healthy": False,
            }

            # Mock settings response showing configured
            mock_settings_response = MagicMock()
            mock_settings_response.status_code = 200
            mock_settings_response.json.return_value = {
                "enabled": True,
                "url": "http://localhost:8080",
                "status": "connected",
            }

            async def mock_get(url, **kwargs):
                if "health" in url:
                    return mock_health_response
                elif "settings" in url:
                    return mock_settings_response
                return mock_health_response

            mock_client.get = mock_get

            agent = ChatAgent()
            status = await agent._get_services_status()

            assert "sabnzbd" in status

    async def test_get_services_status_error(self) -> None:
        """Test handling of service status check errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Mock exception
            mock_client.get.side_effect = Exception("Connection failed")

            agent = ChatAgent()
            status = await agent._get_services_status()

            assert "sabnzbd" in status
            assert status["sabnzbd"].connected is False
            assert status["sabnzbd"].error is not None


@pytest.mark.asyncio
class TestServiceSetupResponse:
    """Tests for service setup response generation."""

    async def test_generate_service_setup_response_sabnzbd(self) -> None:
        """Test generating setup response for SABnzbd."""
        agent = ChatAgent()
        service_status = ServiceStatus(name="sabnzbd", connected=False, healthy=False)
        response = agent._generate_service_setup_response(QueryTopic.SABNZBD, service_status)
        assert response is not None
        assert "SABnzbd" in response.message
        assert "Settings" in response.message
        assert response.service_required == "sabnzbd"
        assert response.setup_link == "/settings"

    async def test_generate_service_setup_response_invalid_topic(self) -> None:
        """Test generating setup response for invalid topic."""
        agent = ChatAgent()
        service_status = ServiceStatus(name="test", connected=False, healthy=False)
        response = agent._generate_service_setup_response(QueryTopic.OFF_TOPIC, service_status)
        assert response is None


@pytest.mark.asyncio
class TestWelcomeResponse:
    """Tests for welcome response generation."""

    async def test_welcome_no_services_configured(self) -> None:
        """Test welcome response when no services are configured."""
        agent = ChatAgent()
        status = {
            "sabnzbd": ServiceStatus(name="sabnzbd", connected=False, healthy=False),
            "sonarr": ServiceStatus(name="sonarr", connected=False, healthy=False),
            "radarr": ServiceStatus(name="radarr", connected=False, healthy=False),
            "plex": ServiceStatus(name="plex", connected=False, healthy=False),
        }
        response = await agent._generate_welcome_response(status)
        assert "no services are connected" in response.message.lower()
        assert response.service_required is not None
        assert response.setup_link == "/settings"

    async def test_welcome_all_services_configured_healthy(self) -> None:
        """Test welcome response when all services are configured and healthy."""
        agent = ChatAgent()
        status = {
            "sabnzbd": ServiceStatus(name="sabnzbd", connected=True, healthy=True),
            "sonarr": ServiceStatus(name="sonarr", connected=True, healthy=True),
            "radarr": ServiceStatus(name="radarr", connected=True, healthy=True),
            "plex": ServiceStatus(name="plex", connected=True, healthy=True),
        }
        response = await agent._generate_welcome_response(status)
        # Should show celebration and features
        message_lower = response.message.lower()
        assert any(
            keyword in message_lower
            for keyword in ["all set", "full stack", "dream setup", "complete", "achieved"]
        )
        assert "download" in message_lower

    async def test_welcome_some_services_configured(self) -> None:
        """Test welcome response when some services are configured."""
        agent = ChatAgent()
        status = {
            "sabnzbd": ServiceStatus(name="sabnzbd", connected=True, healthy=True),
            "sonarr": ServiceStatus(name="sonarr", connected=True, healthy=True),
            "radarr": ServiceStatus(name="radarr", connected=False, healthy=False),
            "plex": ServiceStatus(name="plex", connected=False, healthy=False),
        }
        response = await agent._generate_welcome_response(status)
        message_lower = response.message.lower()
        # Should mention services and offer download capability
        assert "configured" in message_lower or "set" in message_lower or "mix" in message_lower
        assert len(response.suggestions) > 0

    async def test_welcome_with_unhealthy_services(self) -> None:
        """Test welcome response with unhealthy services."""
        agent = ChatAgent()
        status = {
            "sabnzbd": ServiceStatus(name="sabnzbd", connected=True, healthy=False),
            "sonarr": ServiceStatus(name="sonarr", connected=True, healthy=True),
            "radarr": ServiceStatus(name="radarr", connected=False, healthy=False),
            "plex": ServiceStatus(name="plex", connected=False, healthy=False),
        }
        response = await agent._generate_welcome_response(status)
        assert "can't be reached" in response.message.lower() or "check" in response.message.lower()


class TestGenerateSuggestions:
    """Tests for suggestion generation."""

    def test_generate_suggestions_sabnzbd(self) -> None:
        """Test generating suggestions for SABnzbd."""
        agent = ChatAgent()
        suggestions = agent._generate_suggestions(QueryTopic.SABNZBD, ChatIntent.HELP)
        assert len(suggestions) == 3
        assert any("SABnzbd" in s for s in suggestions)

    def test_generate_suggestions_sonarr(self) -> None:
        """Test generating suggestions for Sonarr."""
        agent = ChatAgent()
        suggestions = agent._generate_suggestions(QueryTopic.SONARR, ChatIntent.HELP)
        assert len(suggestions) == 3
        assert any("quality profile" in s.lower() for s in suggestions)

    def test_generate_suggestions_autoarr(self) -> None:
        """Test generating suggestions for AutoArr."""
        agent = ChatAgent()
        suggestions = agent._generate_suggestions(QueryTopic.AUTOARR, ChatIntent.HELP)
        assert len(suggestions) == 3
        assert any("config audit" in s.lower() for s in suggestions)


@pytest.mark.asyncio
class TestDocumentationFetching:
    """Tests for documentation fetching."""

    async def test_fetch_documentation_without_brave_key(self) -> None:
        """Test that no docs are fetched without Brave API key."""
        agent = ChatAgent()
        docs = await agent._fetch_documentation(QueryTopic.SABNZBD, "test query", {})
        assert docs == []

    async def test_fetch_documentation_autoarr_returns_empty(self) -> None:
        """Test that AutoArr docs return empty (uses internal knowledge)."""
        agent = ChatAgent(brave_api_key="test-key")
        docs = await agent._fetch_documentation(QueryTopic.AUTOARR, "test query", {})
        assert docs == []

    async def test_fetch_documentation_with_web_search(self) -> None:
        """Test fetching documentation with web search."""
        mock_search = MagicMock()
        mock_result = MagicMock()
        mock_result.source = "SABnzbd Wiki"
        mock_result.url = "https://wiki.sabnzbd.org/test"
        mock_result.snippet = "Test content"
        mock_result.relevance_score = 0.9
        mock_search.search = AsyncMock(return_value=[mock_result])
        mock_search.extract_content = AsyncMock(return_value="Full content")

        agent = ChatAgent(brave_api_key="test-key")
        agent._web_search = mock_search
        docs = await agent._fetch_documentation(
            QueryTopic.SABNZBD, "How to configure queue?", {"version": "3.0"}
        )

        assert len(docs) == 1
        assert docs[0].source == "SABnzbd Wiki"
        assert docs[0].url == "https://wiki.sabnzbd.org/test"
        assert docs[0].content == "Full content"

    async def test_fetch_documentation_extract_content_fails(self) -> None:
        """Test handling when content extraction fails."""
        mock_search = MagicMock()
        mock_result = MagicMock()
        mock_result.source = "SABnzbd Wiki"
        mock_result.url = "https://wiki.sabnzbd.org/test"
        mock_result.snippet = "Test snippet"
        mock_result.relevance_score = 0.9
        mock_search.search = AsyncMock(return_value=[mock_result])
        mock_search.extract_content = AsyncMock(side_effect=Exception("Failed"))

        agent = ChatAgent(brave_api_key="test-key")
        agent._web_search = mock_search
        docs = await agent._fetch_documentation(QueryTopic.SABNZBD, "test", {})

        # Should fallback to snippet
        assert len(docs) == 1
        assert docs[0].content == "Test snippet"


@pytest.mark.asyncio
class TestToolIntegration:
    """Tests for tool integration methods."""

    async def test_ensure_tools_with_existing_registry(self) -> None:
        """Test that existing registry is returned."""
        mock_registry = MagicMock()
        mock_registry.providers = {"sabnzbd": MagicMock()}
        mock_registry.initialize = AsyncMock()
        agent = ChatAgent(tool_registry=mock_registry)
        agent._tools_initialized = True
        registry = await agent._ensure_tools()
        assert registry == mock_registry

    async def test_ensure_tools_creates_registry(self) -> None:
        """Test that registry is created if not provided."""
        with patch("autoarr.api.services.chat_agent.get_tool_registry") as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.providers = {}
            mock_registry.initialize = AsyncMock()
            mock_registry.register_provider = MagicMock()
            mock_get_registry.return_value = mock_registry

            with patch("autoarr.api.services.tool_providers.SABnzbdToolProvider") as mock_provider:
                mock_provider_instance = MagicMock()
                mock_provider.return_value = mock_provider_instance

                agent = ChatAgent()
                registry = await agent._ensure_tools()

                assert registry == mock_registry
                mock_registry.register_provider.assert_called_once()
                mock_registry.initialize.assert_called_once()

    async def test_chat_with_tools_off_topic(self) -> None:
        """Test that off-topic queries return welcome without tools."""
        with patch.object(ChatAgent, "_get_services_status") as mock_status:
            mock_status.return_value = {}
            with patch.object(ChatAgent, "_generate_welcome_response") as mock_welcome:
                mock_welcome.return_value = ChatResponse(
                    message="Welcome!",
                    topic=QueryTopic.OFF_TOPIC.value,
                    intent=ChatIntent.HELP.value,
                )
                agent = ChatAgent()
                response = await agent.chat_with_tools("Hello!")
                assert response.topic == QueryTopic.OFF_TOPIC.value

    async def test_chat_with_tools_no_tools_available(self) -> None:
        """Test fallback to regular chat when no tools available."""
        with patch.object(ChatAgent, "_ensure_tools") as mock_ensure_tools:
            mock_registry = MagicMock()
            mock_registry.get_available_tools = AsyncMock(return_value=[])
            mock_registry.get_tools_openai_format = MagicMock(return_value=[])
            mock_ensure_tools.return_value = mock_registry

            with patch.object(ChatAgent, "chat") as mock_chat:
                mock_chat.return_value = ChatResponse(
                    message="Response",
                    topic=QueryTopic.SABNZBD.value,
                    intent=ChatIntent.HELP.value,
                )
                with patch.object(ChatAgent, "_ensure_provider") as mock_ensure_provider:
                    mock_provider = MagicMock()
                    mock_ensure_provider.return_value = mock_provider
                    agent = ChatAgent()
                    response = await agent.chat_with_tools("What is SABnzbd?")
                    mock_chat.assert_called_once()

    async def test_chat_with_tools_llm_response_without_tools(self) -> None:
        """Test chat with tools when LLM responds without calling tools."""
        with patch.object(ChatAgent, "_ensure_tools") as mock_ensure_tools:
            mock_registry = MagicMock()
            mock_registry.get_available_tools = AsyncMock(return_value=["sabnzbd_get_queue"])
            mock_registry.get_tools_openai_format = MagicMock(
                return_value=[
                    {
                        "type": "function",
                        "function": {"name": "sabnzbd_get_queue", "parameters": {}},
                    }
                ]
            )
            mock_ensure_tools.return_value = mock_registry

            with patch.object(ChatAgent, "_ensure_provider") as mock_ensure_provider:
                mock_provider = MagicMock()
                mock_provider.complete_with_tools = AsyncMock(
                    return_value=LLMResponseWithTools(
                        content="The queue is empty.",
                        model="test-model",
                        provider="test-provider",
                        model_name="test",
                        tool_calls=None,
                    )
                )
                mock_ensure_provider.return_value = mock_provider

                agent = ChatAgent()
                response = await agent.chat_with_tools("What's in the queue?")
                assert response.message == "The queue is empty."

    async def test_chat_with_tools_provider_no_tool_support(self) -> None:
        """Test fallback when provider doesn't support tools."""
        with patch.object(ChatAgent, "_ensure_tools") as mock_ensure_tools:
            mock_registry = MagicMock()
            mock_registry.get_available_tools = AsyncMock(return_value=["sabnzbd_get_queue"])
            mock_registry.get_tools_openai_format = MagicMock(
                return_value=[{"type": "function", "function": {"name": "sabnzbd_get_queue"}}]
            )
            mock_ensure_tools.return_value = mock_registry

            with patch.object(ChatAgent, "_ensure_provider") as mock_ensure_provider:
                mock_provider = MagicMock(spec=[])  # No complete_with_tools method
                mock_ensure_provider.return_value = mock_provider

                with patch.object(ChatAgent, "chat") as mock_chat:
                    mock_chat.return_value = ChatResponse(
                        message="Response",
                        topic=QueryTopic.SABNZBD.value,
                        intent=ChatIntent.STATUS.value,
                    )
                    agent = ChatAgent()
                    response = await agent.chat_with_tools("Check queue")
                    mock_chat.assert_called_once()


@pytest.mark.asyncio
class TestCloseMethod:
    """Tests for close method."""

    async def test_close_with_provider_close(self) -> None:
        """Test closing when provider has close method."""
        mock_provider = MagicMock()
        mock_provider.close = AsyncMock()
        agent = ChatAgent(provider=mock_provider)
        await agent.close()
        mock_provider.close.assert_called_once()

    async def test_close_without_provider_close(self) -> None:
        """Test closing when provider has no close method."""
        mock_provider = MagicMock(spec=[])  # No close method
        agent = ChatAgent(provider=mock_provider)
        await agent.close()  # Should not raise

    async def test_close_with_web_search(self) -> None:
        """Test closing with web search initialized."""
        mock_web_search = MagicMock()
        mock_web_search.close = AsyncMock()
        agent = ChatAgent()
        agent._web_search = mock_web_search
        await agent.close()
        mock_web_search.close.assert_called_once()
