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
Chat API Endpoints.

This module provides the chat API for the intelligent assistant
that helps users with media automation tasks.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from autoarr.api.services.chat_agent import ChatAgent, ChatResponse, QueryTopic

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ChatMessageInput(BaseModel):
    """Input model for chat message."""

    message: str = Field(..., description="User's message", min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    history: Optional[List[Dict[str, str]]] = Field(
        None, description="Optional conversation history"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "message": "How do I configure quality profiles in Sonarr?",
                "conversation_id": "conv_123",
                "history": [
                    {"role": "user", "content": "What is Sonarr?"},
                    {"role": "assistant", "content": "Sonarr is a TV show automation tool..."},
                ],
            }
        }


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""

    message: str = Field(..., description="Assistant's response")
    topic: str = Field(..., description="Detected topic")
    intent: str = Field(..., description="Detected intent")
    sources: List[Dict[str, str]] = Field(default_factory=list, description="Source URLs")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    confidence: float = Field(..., description="Response confidence")
    is_content_request: bool = Field(
        default=False, description="Whether this is a content download request"
    )
    service_required: Optional[str] = Field(
        None, description="Service name that needs to be connected"
    )
    setup_link: Optional[str] = Field(None, description="Link to settings page for service setup")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "message": "Quality profiles in Sonarr define the quality settings...",
                "topic": "sonarr",
                "intent": "help",
                "sources": [
                    {"title": "Servarr Wiki", "url": "https://wiki.servarr.com/sonarr/..."}
                ],
                "suggestions": [
                    "How to create a custom quality profile?",
                    "What are release profiles?",
                ],
                "confidence": 0.85,
                "is_content_request": False,
                "service_required": None,
                "setup_link": None,
            }
        }


class TopicClassificationResponse(BaseModel):
    """Response model for topic classification."""

    topic: str = Field(..., description="Detected topic")
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., description="Classification confidence")
    entities: Dict = Field(default_factory=dict, description="Extracted entities")
    needs_docs: bool = Field(..., description="Whether documentation lookup is needed")


# ============================================================================
# Dependencies
# ============================================================================

# Global chat agent instance (lazily initialized)
_chat_agent: Optional[ChatAgent] = None
_chat_agent_config_hash: Optional[str] = None


def _get_config_hash(api_key: Optional[str], model: str) -> str:
    """Create a hash of the config to detect changes."""
    import hashlib

    config_str = f"{api_key or ''}:{model}"
    return hashlib.md5(config_str.encode(), usedforsecurity=False).hexdigest()  # nosec B324


def reset_chat_agent() -> None:
    """Reset the chat agent singleton (call when LLM settings change)."""
    global _chat_agent, _chat_agent_config_hash
    _chat_agent = None
    _chat_agent_config_hash = None


async def get_chat_agent() -> ChatAgent:
    """Get or create chat agent instance."""
    global _chat_agent, _chat_agent_config_hash

    # Get configuration from settings via repository
    from autoarr.api.database import LLMSettingsRepository, get_database

    try:
        db = get_database()
        llm_repo = LLMSettingsRepository(db)
        llm_settings = await llm_repo.get_settings()
    except RuntimeError:
        # Database not available, use defaults
        llm_settings = None

    # Get service versions for context
    service_versions = {}
    try:
        # TODO: Fetch actual versions from connected services
        pass
    except Exception:
        pass

    # Extract settings or use defaults
    api_key = None
    model = "anthropic/claude-3.5-sonnet"
    if llm_settings and llm_settings.enabled:
        api_key = llm_settings.api_key if llm_settings.api_key else None
        model = llm_settings.selected_model

    # Check if config has changed - if so, recreate the agent
    new_config_hash = _get_config_hash(api_key, model)
    if _chat_agent is None or _chat_agent_config_hash != new_config_hash:
        _chat_agent = ChatAgent(
            api_key=api_key,
            model=model,
            brave_api_key=None,  # Brave search not yet implemented in settings
            service_versions=service_versions,
        )
        _chat_agent_config_hash = new_config_hash

    return _chat_agent


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Send chat message",
    description="Send a message to the AutoArr assistant and get a response",
)
async def send_message(
    input_data: ChatMessageInput,
    agent: ChatAgent = Depends(get_chat_agent),
) -> ChatMessageResponse:
    """
    Send a chat message.

    This endpoint:
    1. Classifies the query topic and intent
    2. Retrieves relevant documentation if needed
    3. Generates a contextual response
    4. Returns suggestions for follow-up questions

    Topics supported:
    - SABnzbd: Download client configuration and troubleshooting
    - Sonarr: TV show automation
    - Radarr: Movie automation
    - Plex: Media server
    - AutoArr: This application's features
    - Content requests: Downloading specific content
    """
    try:
        logger.info(f"Chat request received: '{input_data.message[:50]}...' (truncated)")

        # Use chat_with_tools for full agentic experience with tool calling
        # This allows the LLM to interact with connected services like SABnzbd
        response = await agent.chat_with_tools(
            query=input_data.message,
            conversation_history=input_data.history,
        )

        logger.info(f"Chat response generated: topic={response.topic}, intent={response.intent}")

        # Check if this is a content request that should use the legacy flow
        is_content_request = response.topic == QueryTopic.CONTENT_REQUEST.value

        return ChatMessageResponse(
            message=response.message,
            topic=response.topic,
            intent=response.intent,
            sources=response.sources,
            suggestions=response.suggestions,
            confidence=response.confidence,
            is_content_request=is_content_request,
            service_required=response.service_required,
            setup_link=response.setup_link,
        )

    except Exception as e:
        error_str = str(e)
        logger.error(f"Chat error: {e}", exc_info=True)

        # Provide user-friendly error messages for common issues
        if "429" in error_str or "Too Many Requests" in error_str:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Rate limit exceeded. You're using a free AI model with strict limits. "
                    "Please wait 60 seconds and try again, or switch to a paid model in "
                    "Settings > AI Settings for higher limits."
                ),
            )
        elif "401" in error_str or "Unauthorized" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Invalid API key. Please check your OpenRouter API key in "
                    "Settings > AI Settings. You can get a free key at openrouter.ai/keys"
                ),
            )
        elif "402" in error_str or "Payment Required" in error_str:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    "Insufficient credits on your OpenRouter account. "
                    "Add credits at openrouter.ai or switch to a free model like "
                    "'google/gemini-2.0-flash-exp:free' in Settings > AI Settings."
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {error_str}",
        )


@router.post(
    "/classify",
    response_model=TopicClassificationResponse,
    summary="Classify query topic",
    description="Classify a query without generating a full response (for routing)",
)
async def classify_query(
    input_data: ChatMessageInput,
    agent: ChatAgent = Depends(get_chat_agent),
) -> TopicClassificationResponse:
    """
    Classify a query's topic and intent.

    This is a lightweight endpoint for determining how to route a query
    without generating a full response. Useful for:
    - Deciding whether to use chat or content request flow
    - Pre-fetching relevant documentation
    - UI routing decisions
    """
    try:
        classification = agent.classify_query(input_data.message)

        return TopicClassificationResponse(
            topic=classification.topic.value,
            intent=classification.intent.value,
            confidence=classification.confidence,
            entities=classification.entities,
            needs_docs=classification.needs_docs,
        )

    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify query: {str(e)}",
        )


@router.get(
    "/topics",
    summary="Get supported topics",
    description="Get list of topics the chat assistant can help with",
)
async def get_topics() -> Dict:
    """
    Get supported topics.

    Returns the list of topics and their descriptions that the
    chat assistant can provide help with.
    """
    return {
        "topics": [
            {
                "id": "sabnzbd",
                "name": "SABnzbd",
                "description": "Usenet download client - queue, config, troubleshooting",
                "icon": "download",
            },
            {
                "id": "sonarr",
                "name": "Sonarr",
                "description": "TV show automation - series management, quality profiles, indexers",
                "icon": "tv",
            },
            {
                "id": "radarr",
                "name": "Radarr",
                "description": "Movie automation - management, quality profiles, formats",
                "icon": "film",
            },
            {
                "id": "plex",
                "name": "Plex",
                "description": "Media server - libraries, playback, transcoding, metadata",
                "icon": "server",
            },
            {
                "id": "autoarr",
                "name": "AutoArr",
                "description": "This application - configuration audit, chat, activity monitoring",
                "icon": "sparkles",
            },
        ],
        "suggestions": [
            "How do I configure SABnzbd?",
            "What are quality profiles in Sonarr?",
            "How to set up Radarr custom formats?",
            "How to enable hardware transcoding in Plex?",
            "How to run a config audit?",
        ],
    }
