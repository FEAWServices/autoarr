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
LLM Agent Service for AutoArr - Updated to use LLMProviderFactory.

This service provides LLM-powered intelligent analysis and recommendations
using the pluggable LLM provider system (Ollama, Claude, or Custom).
"""

import json
import logging
from typing import Any, Dict, Optional

from autoarr.api.services.models import Priority
from autoarr.shared.llm import BaseLLMProvider, LLMMessage, LLMProviderFactory

logger = logging.getLogger(__name__)


# Note: Keeping existing helper classes from original llm_agent.py
# (PromptTemplate, StructuredOutputParser, TokenUsageTracker, LLMRecommendation)
# These will be imported from the original file for now, but should be
# kept in this module. For the migration, I'm only showing the updated LLMAgent class.


class LLMAgent:
    """
    LLM Agent for intelligent configuration analysis.

    Uses pluggable LLM providers (Ollama/Qwen by default, Claude optional)
    to analyze configurations, generate recommendations, and provide
    detailed explanations with context-aware priority assessment.

    Args:
        provider: Optional pre-configured LLM provider
        api_key: Optional API key for Claude (backward compatibility)
        model: Optional model name
        max_tokens: Maximum tokens in responses
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> None:
        """
        Initialize LLM agent.

        If provider is given, uses that. Otherwise creates one via factory.
        For backward compatibility, if api_key is provided, configures Claude.
        """
        self.max_tokens = max_tokens
        self.model = model
        self._provider = provider
        self._api_key = api_key

        # Will be initialized on first use
        self._initialized = False

        # Import helper classes from original module
        from autoarr.api.services.llm_agent import (
            StructuredOutputParser,
            TokenUsageTracker,
        )

        self.token_tracker = TokenUsageTracker()
        self.parser = StructuredOutputParser(
            required_fields=["explanation", "priority", "impact", "reasoning"]
        )

    async def _ensure_provider(self) -> BaseLLMProvider:
        """Lazy initialization of LLM provider."""
        if self._initialized and self._provider:
            return self._provider

        if self._provider is None:
            # Create provider via factory
            if self._api_key:
                # Backward compatibility: if API key provided, prefer Claude
                config = {
                    "api_key": self._api_key,
                    "default_model": self.model or "claude-3-5-sonnet-20241022",
                    "max_tokens": self.max_tokens,
                }
                from autoarr.shared.llm.claude_provider import ClaudeProvider

                self._provider = ClaudeProvider(config)
                logger.info("Initialized LLMAgent with ClaudeProvider (API key provided)")
            else:
                # Use factory with fallback chain (Ollama -> Claude if available)
                self._provider = await LLMProviderFactory.create_provider(
                    provider_name=None,  # Auto-select
                    config={"default_model": self.model} if self.model else None,
                )
                logger.info(f"Initialized LLMAgent with {self._provider.provider_name} provider")

        self._initialized = True
        return self._provider

    async def analyze_configuration(self, context: Dict[str, Any]) -> Any:
        """
        Analyze configuration and generate intelligent recommendation.

        Uses LLM to compare current configuration against best practices,
        assess priority based on impact, and generate detailed explanations.

        Args:
            context: Dict with keys:
                - app: Application name
                - current_config: Current configuration dict
                - best_practice: Best practice dict

        Returns:
            LLMRecommendation with explanation, priority, impact, and reasoning

        Raises:
            Exception: If LLM call fails or response cannot be parsed
        """
        # Import classes from original module
        from autoarr.api.services.llm_agent import LLMRecommendation, PromptTemplate

        # Ensure provider is ready
        provider = await self._ensure_provider()

        # Get prompt template
        template = PromptTemplate.configuration_analysis()

        # Render prompts
        system_prompt = template.render_system()
        user_message = template.render_user(
            app=context["app"],
            current_config=json.dumps(context["current_config"], indent=2),
            best_practice=json.dumps(context["best_practice"], indent=2),
        )

        # Create messages using new format
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        # Call LLM provider
        response = await provider.complete(
            messages=messages, temperature=0.7, max_tokens=self.max_tokens
        )

        # Track token usage
        if response.usage:
            self.token_tracker.record_usage(
                input_tokens=response.usage.get("prompt_tokens", 0),
                output_tokens=response.usage.get("completion_tokens", 0),
            )

        # Parse structured output
        parsed = self.parser.parse(response.content)

        # Validate and normalize priority
        priority_str = parsed["priority"].lower()
        if priority_str not in ["high", "medium", "low"]:
            priority_str = "medium"  # Default to medium if invalid

        # Create recommendation object
        recommendation = LLMRecommendation(
            explanation=parsed["explanation"],
            priority=Priority(priority_str),
            impact=parsed["impact"],
            reasoning=parsed["reasoning"],
        )

        return recommendation

    async def classify_content_request(self, query: str) -> Any:
        """
        Classify a content request and extract metadata.

        Determines if the request is for a movie or TV show and extracts
        relevant information like title, year, etc.

        Args:
            query: Natural language content request

        Returns:
            Classification dict with content_type, title, year, etc.
        """
        # Import classes from original module
        from autoarr.api.services.llm_agent import PromptTemplate

        # Ensure provider is ready
        provider = await self._ensure_provider()

        # Get prompt template
        template = PromptTemplate.content_classification()

        # Render prompts
        system_prompt = template.render_system()
        user_message = template.render_user(query=query)

        # Create messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        # Call LLM provider
        response = await provider.complete(messages=messages, temperature=0.3, max_tokens=500)

        # Track token usage
        if response.usage:
            self.token_tracker.record_usage(
                input_tokens=response.usage.get("prompt_tokens", 0),
                output_tokens=response.usage.get("completion_tokens", 0),
            )

        # Parse response (expecting JSON)
        try:
            classification = json.loads(response.content)
            return classification
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse classification response: {response.content}")
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Could not parse classification response")

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics and cost estimates."""
        return self.token_tracker.get_stats()

    async def close(self) -> None:
        """Close the LLM provider connection."""
        if self._provider and hasattr(self._provider, "__aexit__"):
            await self._provider.__aexit__(None, None, None)


# Migration helper: Create LLMAgent instances with new interface
async def create_llm_agent(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> LLMAgent:
    """
    Factory function to create LLMAgent with provider auto-selection.

    Args:
        api_key: Optional Claude API key (for backward compatibility)
        model: Optional model name
        max_tokens: Maximum tokens in responses

    Returns:
        Configured LLMAgent instance
    """
    return LLMAgent(api_key=api_key, model=model, max_tokens=max_tokens)
