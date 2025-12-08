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
Chat Agent Service for AutoArr.

This service provides an intelligent chat assistant that:
- Routes queries to appropriate topic handlers
- Uses Brave Search for live documentation retrieval (RAG)
- Generates context-aware responses about media automation tools
- Maintains knowledge about SABnzbd, Sonarr, Radarr, Plex, and AutoArr
- Uses tool/function calling to interact with connected services
"""

import json
import logging
import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Import tool provider system
from autoarr.api.services.tool_provider import ToolRegistry, get_tool_registry
from autoarr.shared.llm import BaseLLMProvider, LLMMessage, LLMProviderFactory, LLMResponseWithTools

logger = logging.getLogger(__name__)

# Maximum tool iterations to prevent infinite loops
MAX_TOOL_ITERATIONS = 10

# =============================================================================
# AGENT PERSONALITY & RESPONSES
# Add more variations here to make the agent more engaging!
# =============================================================================

# Greetings when user says hi/hello/etc
GREETING_RESPONSES = [
    "Hey there! 👋 Ready to help with your media setup. What can I do for you?",
    "Hi! I'm AutoArr's assistant - your friendly neighborhood media automation expert. What's up?",
    "Hello! Whether it's downloads, configs, or troubleshooting - I'm here to help!",
    "Hey! Got questions about Sonarr, Radarr, SABnzbd, or Plex? Fire away!",
    "Hi there! Ready to make your media automation dreams come true 🎬",
]

# Fun facts to sprinkle in responses
MEDIA_FUN_FACTS = [
    "💡 **Pro tip:** Quality profiles in Sonarr/Radarr let you auto-upgrade to better versions!",
    "💡 **Did you know?** SABnzbd can repair incomplete downloads using PAR2 files automatically.",
    "💡 **Fun fact:** The *arr stack started with Sonarr - originally called NzbDrone!",
    "💡 **Tip:** Custom formats in Radarr v3+ give you super fine-grained quality control.",
    "💡 **Did you know?** Plex Pass users get hardware transcoding - great for 4K content!",
    "💡 **Pro tip:** Use delay profiles to wait for better releases before downloading.",
    "💡 **Fun fact:** Usenet articles are spread across thousands of servers worldwide!",
]

# Encouraging messages for setup
SETUP_ENCOURAGEMENTS = [
    "You're doing great! 💪",
    "Nice progress! One step closer to media automation bliss.",
    "Getting there! Once set up, you'll wonder how you lived without it.",
    "Awesome! Your future self will thank you for setting this up.",
]

# Responses for when things go wrong
TROUBLESHOOT_INTROS = [
    "Hmm, let's figure this out together! 🔍",
    "No worries, issues happen - let's troubleshoot this!",
    "I see what's going on. Here's what might help:",
    "Ah, the classic troubleshooting adventure! Here's my diagnosis:",
]

# Celebratory messages for success
SUCCESS_MESSAGES = [
    "🎉 Nice! That should be working now.",
    "✨ Perfect! You're all set.",
    "👍 Done! You're good to go.",
    "🚀 Excellent! Everything looks great.",
]


def get_random_greeting() -> str:
    """Get a random greeting response."""
    return random.choice(GREETING_RESPONSES)


def get_random_fun_fact() -> str:
    """Get a random media-related fun fact."""
    return random.choice(MEDIA_FUN_FACTS)


def get_random_encouragement() -> str:
    """Get a random encouragement message."""
    return random.choice(SETUP_ENCOURAGEMENTS)


def get_random_troubleshoot_intro() -> str:
    """Get a random troubleshooting intro."""
    return random.choice(TROUBLESHOOT_INTROS)


def get_random_success() -> str:
    """Get a random success message."""
    return random.choice(SUCCESS_MESSAGES)


class QueryTopic(str, Enum):
    """Topics the chat agent can handle."""

    SABNZBD = "sabnzbd"
    SONARR = "sonarr"
    RADARR = "radarr"
    PLEX = "plex"
    AUTOARR = "autoarr"
    CONTENT_REQUEST = "content_request"
    GENERAL_MEDIA = "general_media"
    OFF_TOPIC = "off_topic"


class ChatIntent(str, Enum):
    """User intent classification."""

    HELP = "help"  # How do I...?, What is...?
    TROUBLESHOOT = "troubleshoot"  # Why isn't...?, Error with...
    CONFIGURE = "configure"  # How to set up..., Configure...
    STATUS = "status"  # Is X working?, Check status
    DOWNLOAD = "download"  # Download X, Get X
    SEARCH = "search"  # Find X, Look for X
    EXPLAIN = "explain"  # What does X do?, Explain X


@dataclass
class TopicClassification:
    """Result of topic classification."""

    topic: QueryTopic
    intent: ChatIntent
    confidence: float
    entities: Dict[str, Any]  # Extracted entities (service name, version, setting, etc.)
    needs_docs: bool  # Whether we should fetch documentation


@dataclass
class DocumentContext:
    """Retrieved documentation context."""

    source: str
    url: str
    content: str
    relevance: float


@dataclass
class ServiceStatus:
    """Status of a connected service."""

    name: str
    connected: bool
    healthy: bool
    version: Optional[str] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat agent."""

    message: str = Field(..., description="Response message")
    topic: str = Field(..., description="Detected topic")
    intent: str = Field(..., description="Detected intent")
    sources: List[Dict[str, str]] = Field(default_factory=list, description="Source URLs")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    confidence: float = Field(default=0.8, description="Response confidence")
    service_required: Optional[str] = Field(None, description="Service needed but not connected")
    setup_link: Optional[str] = Field(None, description="Link to setup the required service")


class ChatAgent:
    """
    Intelligent Chat Agent for media automation assistance.

    This agent provides contextual help about:
    - SABnzbd: Download management, configuration, troubleshooting
    - Sonarr: TV show management, quality profiles, indexers
    - Radarr: Movie management, quality profiles, indexers
    - Plex: Media server, libraries, transcoding
    - AutoArr: This application's features and configuration

    It uses Brave Search to fetch live documentation based on the user's
    configured service versions or latest available.
    """

    # Topic detection keywords
    TOPIC_KEYWORDS = {
        QueryTopic.SABNZBD: [
            "sabnzbd",
            "sab",
            "nzb",
            "usenet",
            "download client",
            "incomplete",
            "complete folder",
            "article cache",
            "direct unpack",
            "par2",
            "unrar",
            "queue",
            "history",
            "sabnzbd.org",
        ],
        QueryTopic.SONARR: [
            "sonarr",
            "tv show",
            "series",
            "episode",
            "season",
            "quality profile",
            "indexer",
            "release profile",
            "wanted",
            "calendar",
            "activity",
            "servarr",
        ],
        QueryTopic.RADARR: [
            "radarr",
            "movie",
            "film",
            "cinema",
            "quality profile",
            "indexer",
            "custom format",
            "wanted",
            "discover",
            "servarr",
        ],
        QueryTopic.PLEX: [
            "plex",
            "media server",
            "library",
            "transcode",
            "direct play",
            "direct stream",
            "plex pass",
            "metadata",
            "collections",
            "playlists",
        ],
        QueryTopic.AUTOARR: [
            "autoarr",
            "this app",
            "this application",
            "this tool",
            "config audit",
            "configuration audit",
            "settings",
            "activity log",
            "chat",
            "assistant",
        ],
        QueryTopic.CONTENT_REQUEST: [
            "download",
            "get me",
            "find me",
            "add",
            "request",
            "want to watch",
            "looking for",
        ],
    }

    # Intent detection patterns
    INTENT_PATTERNS = {
        ChatIntent.HELP: [
            r"how (?:do|can|to)",
            r"what (?:is|are|does)",
            r"explain",
            r"tell me about",
            r"help with",
        ],
        ChatIntent.TROUBLESHOOT: [
            r"(?:why|not) working",
            r"error",
            r"problem",
            r"issue",
            r"failed",
            r"can't",
            r"doesn't",
            r"broken",
        ],
        ChatIntent.CONFIGURE: [
            r"(?:how to )?(?:set up|setup|configure|config)",
            r"settings? for",
            r"change",
            r"enable",
            r"disable",
        ],
        ChatIntent.STATUS: [
            r"(?:is|are) .* (?:working|running|connected)",
            r"check (?:status|connection)",
            r"status of",
        ],
        ChatIntent.DOWNLOAD: [
            r"download",
            r"get (?:me )?",
            r"add",
            r"request",
        ],
        ChatIntent.SEARCH: [
            r"find",
            r"search",
            r"look for",
            r"looking for",
        ],
        ChatIntent.EXPLAIN: [
            r"what (?:is|does)",
            r"explain",
            r"meaning of",
            r"purpose of",
        ],
    }

    # Service documentation URLs
    DOC_URLS = {
        QueryTopic.SABNZBD: "wiki.sabnzbd.org",
        QueryTopic.SONARR: "wiki.servarr.com/sonarr",
        QueryTopic.RADARR: "wiki.servarr.com/radarr",
        QueryTopic.PLEX: "support.plex.tv",
        QueryTopic.AUTOARR: None,  # Internal knowledge
    }

    # System prompt for the chat agent
    # Note: This is a multi-line string literal - line length is checked per logical line
    SYSTEM_PROMPT = (  # noqa: E501
        "You are AutoArr Assistant, an expert helper for home media automation.\n\n"
        "You have deep knowledge of:\n"
        "- **SABnzbd**: Usenet download client - queue, config, troubleshooting\n"
        "- **Sonarr**: TV show automation - series management, quality profiles\n"
        "- **Radarr**: Movie automation - movie management, quality profiles\n"
        "- **Plex**: Media server - libraries, playback, transcoding, metadata\n"
        "- **AutoArr**: Configuration audit, natural language requests, monitoring\n\n"
        "IMPORTANT CONSTRAINTS:\n"
        "1. ONLY answer questions about media automation and AutoArr\n"
        "2. For off-topic questions, politely redirect to media automation topics\n"
        "3. Be concise but thorough - provide actionable answers\n"
        "4. When documentation is provided, use it for accurate advice\n"
        "5. Always cite sources when using retrieved documentation\n"
        "6. If unsure, say so and suggest checking official documentation\n\n"
        "RESPONSE FORMAT:\n"
        "- Start with a direct answer to the question\n"
        "- Provide step-by-step instructions when applicable\n"
        "- Include relevant settings/configuration values\n"
        "- End with a helpful follow-up suggestion if appropriate\n"
        "- Keep responses focused and under 500 words unless more detail is needed"
    )

    # System prompt for agent mode with tool use
    # Note: E501 suppressed for this multi-line string constant
    SYSTEM_PROMPT_WITH_TOOLS = (  # noqa: E501
        "You are AutoArr Assistant with direct access to service APIs.\n\n"
        "You can USE TOOLS to interact with:\n"
        "- **SABnzbd**: Check queue, pause/resume downloads, view history, retry\n"
        "- **Sonarr**: Manage TV shows (coming soon)\n"
        "- **Radarr**: Manage movies (coming soon)\n"
        "- **Plex**: Manage media server (coming soon)\n\n"
        "TOOL USAGE GUIDELINES:\n"
        "1. USE TOOLS when the user asks about:\n"
        "   - Current download status -> sabnzbd_get_queue or sabnzbd_get_status\n"
        "   - Download history -> sabnzbd_get_history\n"
        "   - Pausing/resuming downloads -> sabnzbd_pause_queue/resume_queue\n"
        "   - Retrying failed downloads -> sabnzbd_retry_download\n"
        "   - Configuration values -> sabnzbd_get_config\n"
        "   - Changing settings -> sabnzbd_set_config\n\n"
        "2. DO NOT use tools for:\n"
        "   - General questions about how features work (answer from knowledge)\n"
        "   - Off-topic questions (politely redirect)\n"
        "   - Hypothetical scenarios\n\n"
        "3. After using tools:\n"
        "   - Summarize the results in a user-friendly way\n"
        "   - Don't dump raw JSON - extract key information\n"
        "   - Highlight important values (speeds, progress, errors)\n\n"
        "CONSTRAINTS:\n"
        "- ONLY answer questions about media automation\n"
        "- For off-topic questions, politely redirect\n"
        "- If a tool fails, explain the error and suggest solutions\n"
        "- Never expose API keys or sensitive configuration"
    )

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        brave_api_key: Optional[str] = None,
        service_versions: Optional[Dict[str, str]] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        """
        Initialize chat agent.

        Args:
            provider: Optional pre-configured LLM provider
            api_key: Optional OpenRouter API key
            model: Optional model name
            brave_api_key: Optional Brave Search API key for docs retrieval
            service_versions: Optional dict of service versions user has configured
            tool_registry: Optional tool registry for service tools
        """
        self._provider = provider
        self._api_key = api_key
        self._model = model or "anthropic/claude-3.5-sonnet"
        self._brave_api_key = brave_api_key
        self._service_versions = service_versions or {}
        self._initialized = False
        self._web_search = None
        self._tool_registry = tool_registry
        self._tools_initialized = False

        # AutoArr internal knowledge base
        self._autoarr_knowledge = self._build_autoarr_knowledge()

    def _build_autoarr_knowledge(self) -> str:
        """Build internal knowledge about AutoArr."""
        return """
## AutoArr Features

### Configuration Audit
- Analyzes SABnzbd, Sonarr, Radarr, and Plex configurations
- Compares settings against best practices
- Provides prioritized recommendations (High/Medium/Low)
- Accessible via Settings > Config Audit

### Natural Language Requests
- Request movies or TV shows by typing naturally
- Example: "Download Dune Part Two in 4K"
- Automatically classifies content type (movie vs TV)
- Searches configured services for matches

### Activity Monitoring
- Real-time activity feed
- WebSocket-based live updates
- Tracks downloads, searches, and system events

### Settings
- Configure service connections (SABnzbd, Sonarr, Radarr, Plex)
- LLM configuration (OpenRouter API)
- Application settings (log level, timezone)
- Run setup wizard to reconfigure

### Troubleshooting AutoArr
- Check Settings page for service connection status
- View Logs page for detailed error messages
- Ensure API keys are correct and services are reachable
- Default ports: SABnzbd (8080), Sonarr (8989), Radarr (7878), Plex (32400)
"""

    async def _ensure_provider(self) -> BaseLLMProvider:
        """Lazy initialization of LLM provider."""
        if self._initialized and self._provider:
            return self._provider

        if self._provider is None:
            if self._api_key:
                from autoarr.shared.llm.openrouter_provider import OpenRouterProvider

                config = {
                    "api_key": self._api_key,
                    "default_model": self._model,
                    "max_tokens": 2048,
                }
                self._provider = OpenRouterProvider(config)
            else:
                self._provider = await LLMProviderFactory.create_provider(
                    provider_name="openrouter",
                    config={"default_model": self._model} if self._model else None,
                )

        self._initialized = True
        return self._provider

    async def _ensure_web_search(self):
        """Lazy initialization of web search service."""
        if self._web_search is not None:
            return self._web_search

        if self._brave_api_key:
            from autoarr.api.services.web_search_service import WebSearchService

            self._web_search = WebSearchService(brave_api_key=self._brave_api_key)

        return self._web_search

    def classify_query(self, query: str) -> TopicClassification:
        """
        Classify query by topic and intent.

        Uses keyword matching and pattern detection for fast,
        deterministic classification without LLM call.

        Args:
            query: User's query string

        Returns:
            TopicClassification with topic, intent, and extracted entities
        """
        query_lower = query.lower()

        # Detect topic
        topic_scores: Dict[QueryTopic, float] = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                topic_scores[topic] = score

        # Determine primary topic
        if topic_scores:
            topic = max(topic_scores, key=topic_scores.get)
            confidence = min(topic_scores[topic] / 3, 1.0)  # Normalize
        else:
            topic = QueryTopic.OFF_TOPIC
            confidence = 0.3

        # Detect intent
        intent = ChatIntent.HELP  # Default
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent = intent_type
                    break

        # Extract entities
        entities = self._extract_entities(query, topic)

        # Determine if we need documentation
        needs_docs = topic not in [QueryTopic.OFF_TOPIC, QueryTopic.CONTENT_REQUEST] and intent in [
            ChatIntent.HELP,
            ChatIntent.TROUBLESHOOT,
            ChatIntent.CONFIGURE,
            ChatIntent.EXPLAIN,
        ]

        return TopicClassification(
            topic=topic,
            intent=intent,
            confidence=confidence,
            entities=entities,
            needs_docs=needs_docs,
        )

    def _extract_entities(self, query: str, topic: QueryTopic) -> Dict[str, Any]:
        """Extract relevant entities from query."""
        entities = {}
        query_lower = query.lower()

        # Extract version numbers
        version_match = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", query)
        if version_match:
            entities["version"] = version_match.group(1)

        # Extract setting names (snake_case or camelCase)
        setting_match = re.search(r"\b([a-z]+(?:_[a-z]+)+|[a-z]+(?:[A-Z][a-z]+)+)\b", query)
        if setting_match:
            entities["setting"] = setting_match.group(1)

        # Topic-specific extraction
        if topic == QueryTopic.SONARR:
            # Extract quality profile mentions
            if "quality profile" in query_lower:
                entities["feature"] = "quality_profile"
        elif topic == QueryTopic.SABNZBD:
            # Extract SABnzbd-specific settings
            for setting in ["article_cache", "direct_unpack", "par2", "queue"]:
                if setting.replace("_", " ") in query_lower or setting in query_lower:
                    entities["setting"] = setting

        return entities

    async def _fetch_documentation(
        self, topic: QueryTopic, query: str, entities: Dict[str, Any]
    ) -> List[DocumentContext]:
        """
        Fetch relevant documentation using Brave Search.

        Args:
            topic: Detected topic
            query: Original user query
            entities: Extracted entities

        Returns:
            List of DocumentContext with retrieved docs
        """
        web_search = await self._ensure_web_search()
        if not web_search:
            return []

        # Build search query
        service_name = topic.value
        version = entities.get("version") or self._service_versions.get(service_name)
        setting = entities.get("setting", "")

        # Construct targeted search
        if topic == QueryTopic.AUTOARR:
            # No external search for AutoArr - use internal knowledge
            return []

        search_terms = [service_name]
        if version:
            search_terms.append(f"v{version}")
        if setting:
            search_terms.append(setting)

        # Add key terms from original query (filtered)
        stop_words = {"how", "do", "i", "the", "a", "an", "to", "in", "is", "what", "why", "can"}
        query_terms = [w for w in query.lower().split() if w not in stop_words and len(w) > 2]
        search_terms.extend(query_terms[:3])  # Add up to 3 relevant terms

        search_query = " ".join(search_terms)

        # Prefer official documentation
        doc_domain = self.DOC_URLS.get(topic)
        if doc_domain:
            search_query = f"site:{doc_domain} {search_query}"

        try:
            from autoarr.api.services.web_search_service import SearchQuery

            results = await web_search.search(
                SearchQuery(
                    query=search_query,
                    application=service_name,
                    max_results=3,
                )
            )

            docs = []
            for result in results[:3]:
                # Try to extract content from top results
                try:
                    content = await web_search.extract_content(result.url)
                    # Truncate content to avoid token limits
                    content = content[:2000] if len(content) > 2000 else content

                    docs.append(
                        DocumentContext(
                            source=result.source,
                            url=result.url,
                            content=content,
                            relevance=result.relevance_score,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to extract content from {result.url}: {e}")
                    # Use snippet as fallback
                    docs.append(
                        DocumentContext(
                            source=result.source,
                            url=result.url,
                            content=result.snippet,
                            relevance=result.relevance_score,
                        )
                    )

            return docs

        except Exception as e:
            logger.error(f"Documentation fetch failed: {e}")
            return []

    async def chat(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        check_services: bool = True,
    ) -> ChatResponse:
        """
        Process a chat query and generate response.

        Args:
            query: User's query
            conversation_history: Optional previous messages for context
            check_services: Whether to check if required services are connected

        Returns:
            ChatResponse with message, sources, and suggestions
        """
        # Step 1: Classify the query
        classification = self.classify_query(query)
        logger.info(
            f"Query classified: topic={classification.topic}, intent={classification.intent}"
        )

        # Step 2: Handle off-topic/greeting queries with service-aware response
        if classification.topic == QueryTopic.OFF_TOPIC:
            # Get current service status to provide contextual help
            services_status = await self._get_services_status()
            return await self._generate_welcome_response(services_status)

        # Step 3: Check service connectivity for service-specific topics
        if check_services and classification.topic in self.TOPIC_TO_SERVICE:
            service_name = self.TOPIC_TO_SERVICE[classification.topic]
            services_status = await self._get_services_status()
            service_status = services_status.get(service_name)

            if service_status and not service_status.connected:
                # Service not connected - suggest setup
                logger.info(f"Service {service_name} not connected, suggesting setup")
                return self._generate_service_setup_response(classification.topic, service_status)

        # Step 4: Handle content requests differently (existing flow)
        if classification.topic == QueryTopic.CONTENT_REQUEST:
            return ChatResponse(
                message=(
                    "I can help you find that content! Let me search for it.\n\n"
                    "Just type what you're looking for, like:\n"
                    '- "Download Dune Part Two in 4K"\n'
                    '- "Get me The Office season 3"'
                ),
                topic=classification.topic.value,
                intent=classification.intent.value,
                suggestions=[],
                confidence=classification.confidence,
            )

        # Step 5: Fetch relevant documentation
        docs = []
        if classification.needs_docs:
            docs = await self._fetch_documentation(
                classification.topic,
                query,
                classification.entities,
            )

        # Step 6: Build context for LLM
        context_parts = []

        # Add AutoArr knowledge if relevant
        if classification.topic == QueryTopic.AUTOARR:
            context_parts.append(f"## AutoArr Documentation\n{self._autoarr_knowledge}")

        # Add retrieved documentation
        if docs:
            context_parts.append("## Retrieved Documentation")
            for doc in docs:
                context_parts.append(f"### Source: {doc.source} ({doc.url})\n{doc.content}")

        # Add service version context
        if classification.topic.value in self._service_versions:
            version = self._service_versions[classification.topic.value]
            context_parts.append(f"\nUser's {classification.topic.value} version: {version}")

        context = "\n\n".join(context_parts) if context_parts else ""

        # Step 7: Generate response with LLM
        provider = await self._ensure_provider()

        user_message = query
        if context:
            user_message = f"""User Question: {query}

---
CONTEXT (use this to provide accurate answers):
{context}
---

Please answer the user's question using the context above when relevant."""

        messages = [
            LLMMessage(role="system", content=self.SYSTEM_PROMPT),
        ]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                messages.append(
                    LLMMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    )
                )

        messages.append(LLMMessage(role="user", content=user_message))

        response = await provider.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        # Step 8: Build response with sources
        sources = [{"title": doc.source, "url": doc.url} for doc in docs]

        # Generate follow-up suggestions based on topic
        suggestions = self._generate_suggestions(classification.topic, classification.intent)

        return ChatResponse(
            message=response.content,
            topic=classification.topic.value,
            intent=classification.intent.value,
            sources=sources,
            suggestions=suggestions,
            confidence=classification.confidence,
        )

    def _generate_suggestions(self, topic: QueryTopic, intent: ChatIntent) -> List[str]:
        """Generate contextual follow-up suggestions."""
        suggestions_map = {
            QueryTopic.SABNZBD: [
                "How to optimize SABnzbd download speed?",
                "What is article cache in SABnzbd?",
                "How to configure direct unpack?",
            ],
            QueryTopic.SONARR: [
                "How do quality profiles work?",
                "How to add an indexer to Sonarr?",
                "What are release profiles?",
            ],
            QueryTopic.RADARR: [
                "How to use custom formats?",
                "How to configure quality profiles?",
                "What is the Discover feature?",
            ],
            QueryTopic.PLEX: [
                "How to enable hardware transcoding?",
                "How to organize my library?",
                "What is Direct Play vs Transcoding?",
            ],
            QueryTopic.AUTOARR: [
                "How to run a config audit?",
                "How to connect my services?",
                "What can I do with chat?",
            ],
        }

        return suggestions_map.get(topic, [])[:3]

    # Map topics to service names
    TOPIC_TO_SERVICE = {
        QueryTopic.SABNZBD: "sabnzbd",
        QueryTopic.SONARR: "sonarr",
        QueryTopic.RADARR: "radarr",
        QueryTopic.PLEX: "plex",
    }

    # Service display names and descriptions
    SERVICE_INFO = {
        "sabnzbd": {
            "name": "SABnzbd",
            "description": "Usenet download client",
            "default_port": 8080,
        },
        "sonarr": {
            "name": "Sonarr",
            "description": "TV show automation",
            "default_port": 8989,
        },
        "radarr": {
            "name": "Radarr",
            "description": "Movie automation",
            "default_port": 7878,
        },
        "plex": {
            "name": "Plex",
            "description": "Media server",
            "default_port": 32400,
        },
    }

    async def _get_services_status(self) -> Dict[str, ServiceStatus]:
        """
        Check which services are connected and healthy.

        This checks both:
        1. The health endpoint (for live connection status)
        2. The settings API (for configured services that may not be loaded in orchestrator yet)

        Returns:
            Dict mapping service name to ServiceStatus
        """
        import httpx

        services_status: Dict[str, ServiceStatus] = {}

        async with httpx.AsyncClient() as client:
            for service_name in ["sabnzbd", "sonarr", "radarr", "plex"]:
                try:
                    # First check health endpoint
                    health_response = await client.get(
                        f"http://localhost:8088/health/{service_name}",
                        timeout=5.0,
                    )

                    if health_response.status_code == 200:
                        health_data = health_response.json()
                        is_connected = health_data.get("circuit_breaker_state") != "unconfigured"
                        is_healthy = health_data.get("healthy", False)

                        # If health says not configured, also check settings API
                        # (settings may be saved but orchestrator not reloaded)
                        if not is_connected:
                            try:
                                settings_response = await client.get(
                                    f"http://localhost:8088/api/v1/settings/{service_name}",
                                    timeout=5.0,
                                )
                                if settings_response.status_code == 200:
                                    settings_data = settings_response.json()
                                    # Service is configured if enabled and has URL
                                    if settings_data.get("enabled") and settings_data.get("url"):
                                        is_connected = True
                                        # Check status from settings
                                        is_healthy = settings_data.get("status") == "connected"
                            except Exception:
                                pass  # Fall back to health check result

                        services_status[service_name] = ServiceStatus(
                            name=service_name,
                            connected=is_connected,
                            healthy=is_healthy,
                            error=health_data.get("error") if not is_healthy else None,
                        )
                    else:
                        services_status[service_name] = ServiceStatus(
                            name=service_name,
                            connected=False,
                            healthy=False,
                            error=f"Health check returned {health_response.status_code}",
                        )
                except Exception as e:
                    logger.debug(f"Failed to check {service_name} status: {e}")
                    services_status[service_name] = ServiceStatus(
                        name=service_name,
                        connected=False,
                        healthy=False,
                        error=str(e),
                    )

        return services_status

    def _generate_service_setup_response(
        self, topic: QueryTopic, service_status: ServiceStatus
    ) -> ChatResponse:
        """Generate a helpful response when a required service is not connected."""
        service_name = self.TOPIC_TO_SERVICE.get(topic)
        if not service_name:
            return None

        service_info = self.SERVICE_INFO.get(service_name, {})
        display_name = service_info.get("name", service_name.capitalize())
        default_port = service_info.get("default_port", "")

        message = (
            f"I'd love to help you with {display_name}, "
            "but it's not connected to AutoArr yet.\n\n"
            f"**To set up {display_name}:**\n"
            "1. Go to **Settings** in the sidebar\n"
            f"2. Find the **{display_name}** section\n"
            f"3. Enter your {display_name} URL "
            f"(usually `http://localhost:{default_port}`)\n"
            f"4. Add your API key (found in {display_name}'s settings)\n"
            "5. Click **Test Connection** to verify\n\n"
            "Once connected, I can help you with:\n"
            "- Configuration questions and best practices\n"
            "- Troubleshooting issues\n"
            "- Understanding features and settings"
        )

        return ChatResponse(
            message=message,
            topic=topic.value,
            intent=ChatIntent.CONFIGURE.value,
            suggestions=[
                f"How do I find my {display_name} API key?",
                "What services does AutoArr support?",
                "How to run a configuration audit?",
            ],
            confidence=0.95,
            service_required=service_name,
            setup_link="/settings",
        )

    async def _generate_welcome_response(
        self, services_status: Dict[str, ServiceStatus]
    ) -> ChatResponse:
        """Generate a context-aware welcome response based on connected services."""
        # Categorize services into three groups:
        # - configured_healthy: settings saved AND service reachable
        # - configured_unhealthy: settings saved but service not reachable
        # - not_configured: no settings saved
        configured_services = []  # (name, display_name, is_healthy)
        not_configured_services = []  # (name, display_name)

        for service_name, status in services_status.items():
            service_info = self.SERVICE_INFO.get(service_name, {})
            display_name = service_info.get("name", service_name.capitalize())
            if status.connected:
                # Service is configured (settings saved)
                configured_services.append((service_name, display_name, status.healthy))
            else:
                not_configured_services.append((service_name, display_name))

        # Build context-aware message and suggestions
        suggestions = []

        # Check for unhealthy configured services
        unhealthy_services = [(n, d) for n, d, h in configured_services if not h]
        healthy_services = [(n, d) for n, d, h in configured_services if h]

        if not configured_services:
            # No services configured - guide to setup with random greeting
            greetings = [
                "Hey! Looks like you're just getting started",
                "Welcome! Looks like it's your first time here",
                "Hi there! I see we're starting fresh",
                "Hello! Ready to set up your media automation empire?",
            ]
            message = (
                f"{random.choice(greetings)} - no services are connected yet.\n\n"
                "**Let's get you set up!** Head to Settings and connect your first service:\n\n"
                "- **Sonarr** - For TV show automation (port 8989)\n"
                "- **Radarr** - For movie automation (port 7878)\n"
                "- **SABnzbd** - For download management (port 8080)\n"
                "- **Plex** - For your media server (port 32400)\n\n"
                "Once you've connected a service, I can help you configure it, "
                "troubleshoot issues, and even download content for you!\n\n"
                f"{get_random_fun_fact()}"
            )
            suggestions = [
                "How do I connect Sonarr?",
                "What's the best service to start with?",
                "How do I find my API key?",
            ]
            return ChatResponse(
                message=message,
                topic=QueryTopic.OFF_TOPIC.value,
                intent=ChatIntent.CONFIGURE.value,
                suggestions=suggestions,
                confidence=0.95,
                service_required="sonarr",  # Suggest starting with Sonarr
                setup_link="/settings",
            )

        elif len(configured_services) == len(services_status) and not unhealthy_services:
            # All services configured AND healthy - full capabilities!
            connected_names = ", ".join([name for _, name in healthy_services])
            celebrations = [
                f"You're all set up with {connected_names} - nice! 🎉",
                f"Full stack achieved! {connected_names} all running smoothly 🚀",
                f"Look at you! {connected_names} all connected and ready to go 💪",
                f"The dream setup! {connected_names} - you've got the complete arsenal ✨",
            ]
            message = (
                f"{random.choice(celebrations)}\n\n"
                "**Here's what I can help with:**\n\n"
                "🎬 **Download content** - Just say what you want, like "
                '"Download The Bear" or "Get me Dune Part Two in 4K"\n\n'
                "⚙️ **Manage your setup** - Ask about quality profiles, indexers, "
                "or get a config audit to optimize your settings\n\n"
                "🔧 **Troubleshoot** - Having issues? Tell me what's going wrong "
                "and I'll help you fix it\n\n"
                f"{get_random_fun_fact()}"
            )
            suggestions = [
                "Download a movie for me",
                "Run a config audit",
                "What are the best quality settings?",
            ]

        else:
            # Some services configured (might have unhealthy ones)
            configured_names = ", ".join([name for _, name, _ in configured_services])

            intros = [
                f"You've got **{configured_names}** configured",
                f"Nice! **{configured_names}** in the mix",
                f"Good start! **{configured_names}** ready to go",
            ]
            message = random.choice(intros)

            # Note about unhealthy services
            if unhealthy_services:
                unhealthy_list = ", ".join([name for _, name in unhealthy_services])
                message += (
                    f" (though {unhealthy_list} can't be reached right now - check the connection)"
                )
            message += "!\n\n"

            # Add suggestions based on what's configured
            if any(s[0] in ["sonarr", "radarr"] for s, _, _ in configured_services):
                if healthy_services:
                    message += (
                        "🎬 **Download content** - Tell me what movie or show you want, "
                        'like "Get me Severance" or "Download Oppenheimer"\n\n'
                    )
                    suggestions.append("Download a movie for me")

            # Suggest what they could add
            if not_configured_services:
                missing_list = " or ".join([name for _, name in not_configured_services[:2]])
                message += (
                    f"🔌 **Expand your setup** - Connect {missing_list} "
                    "to unlock more features!\n\n"
                )
                suggestions.append(f"How do I connect {not_configured_services[0][1]}?")

            message += "💬 **Get help** - Ask me anything about configuring your services\n\n"
            message += get_random_fun_fact()
            suggestions.append("Run a config audit")

        return ChatResponse(
            message=message,
            topic=QueryTopic.OFF_TOPIC.value,
            intent=ChatIntent.HELP.value,
            suggestions=suggestions[:3],  # Limit to 3 suggestions
            confidence=0.9,
        )

    async def close(self) -> None:
        """Close resources."""
        if self._provider and hasattr(self._provider, "close"):
            await self._provider.close()
        if self._web_search:
            await self._web_search.close()

    # =========================================================================
    # TOOL INTEGRATION METHODS
    # =========================================================================

    async def _ensure_tools(self) -> ToolRegistry:
        """
        Ensure tool registry is initialized with all providers.

        Returns:
            Initialized ToolRegistry instance
        """
        if self._tools_initialized and self._tool_registry:
            return self._tool_registry

        # Get or create registry
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()

        # Register SABnzbd provider if not already registered
        if "sabnzbd" not in self._tool_registry.providers:
            from autoarr.api.services.tool_providers import SABnzbdToolProvider

            provider = SABnzbdToolProvider()
            self._tool_registry.register_provider(provider)

        # Initialize the registry (fetches service info/versions)
        await self._tool_registry.initialize()
        self._tools_initialized = True

        return self._tool_registry

    async def chat_with_tools(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        max_iterations: int = MAX_TOOL_ITERATIONS,
    ) -> ChatResponse:
        """
        Process a chat query with tool/function calling support.

        This method implements an agentic loop that:
        1. Sends the query to the LLM with available tools
        2. If the LLM wants to use tools, executes them
        3. Sends tool results back to the LLM
        4. Repeats until the LLM provides a final response

        Args:
            query: User's query
            conversation_history: Optional previous messages for context
            max_iterations: Maximum tool call iterations (default: 10)

        Returns:
            ChatResponse with message, sources, and suggestions
        """
        # Step 1: Classify the query to check if it's something we should handle
        classification = self.classify_query(query)
        logger.info(
            f"Query classified: topic={classification.topic}, intent={classification.intent}"
        )

        # Step 2: Handle off-topic queries without tools
        if classification.topic == QueryTopic.OFF_TOPIC:
            services_status = await self._get_services_status()
            return await self._generate_welcome_response(services_status)

        # Step 3: Initialize tools and provider
        registry = await self._ensure_tools()
        provider = await self._ensure_provider()

        # Step 4: Get available tools in OpenAI format
        available_tools = await registry.get_available_tools()
        tools_openai = registry.get_tools_openai_format(available_tools)

        if not tools_openai:
            # No tools available - fall back to regular chat
            logger.info("No tools available, using regular chat")
            return await self.chat(query, conversation_history)

        logger.info(f"Available tools: {[t['function']['name'] for t in tools_openai]}")

        # Step 5: Build initial messages
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=self.SYSTEM_PROMPT_WITH_TOOLS),
        ]

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append(
                    LLMMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    )
                )

        messages.append(LLMMessage(role="user", content=query))

        # Step 6: Agentic tool loop
        tool_results_for_response: List[Dict[str, Any]] = []
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            logger.debug(f"Tool iteration {iterations}/{max_iterations}")

            # Call LLM with tools
            try:
                # Check if provider has tool support
                if not hasattr(provider, "complete_with_tools"):
                    logger.warning(
                        "Provider doesn't support tool calling, falling back to regular chat"
                    )
                    return await self.chat(query, conversation_history)

                response: LLMResponseWithTools = await provider.complete_with_tools(
                    messages=messages,
                    tools=tools_openai,
                    temperature=0.7,
                    max_tokens=1024,
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return ChatResponse(
                    message=f"I encountered an error while processing your request: {str(e)}",
                    topic=classification.topic.value,
                    intent=classification.intent.value,
                    confidence=0.3,
                )

            # Check if LLM wants to use tools
            if response.tool_calls:
                logger.info(f"LLM requested {len(response.tool_calls)} tool calls")

                # Add assistant message with tool calls to history
                assistant_msg = LLMMessage(role="assistant", content=response.content or "")
                # Store tool calls in message for context
                assistant_msg.tool_calls = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in response.tool_calls
                ]
                messages.append(assistant_msg)

                # Execute each tool call
                for tool_call in response.tool_calls:
                    logger.info(
                        f"Executing tool: {tool_call.name} with args: {tool_call.arguments}"
                    )

                    result = await registry.execute_tool(tool_call.name, tool_call.arguments)

                    # Store result for final response metadata
                    tool_results_for_response.append(
                        {
                            "tool": tool_call.name,
                            "success": result.success,
                            "data": result.data if result.success else None,
                            "error": result.error if not result.success else None,
                        }
                    )

                    # Add tool result message
                    tool_result_content = json.dumps(result.to_dict(), default=str)
                    tool_msg = LLMMessage(
                        role="tool",
                        content=tool_result_content,
                    )
                    tool_msg.tool_call_id = tool_call.id
                    tool_msg.name = tool_call.name
                    messages.append(tool_msg)

                # Continue the loop to let LLM process tool results
                continue

            # No tool calls - LLM is done, return final response
            break

        # Step 7: Build final response
        final_message = response.content if response else "I couldn't generate a response."

        # Generate suggestions based on topic
        suggestions = self._generate_suggestions(classification.topic, classification.intent)

        return ChatResponse(
            message=final_message,
            topic=classification.topic.value,
            intent=classification.intent.value,
            sources=[],  # Tools don't produce URL sources
            suggestions=suggestions,
            confidence=classification.confidence,
        )
