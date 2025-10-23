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
LLM Agent Service for AutoArr.

This service provides LLM-powered intelligent analysis and recommendations
using pluggable LLM providers (Ollama, Claude, or custom). It includes:
- LLM provider abstraction with automatic selection
- Prompt template system
- Structured output parsing
- Token usage tracking and cost estimation
- Configuration analysis and recommendation generation
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from autoarr.api.services.models import Priority
from autoarr.shared.llm import LLMProviderFactory, LLMMessage, BaseLLMProvider

logger = logging.getLogger(__name__)


# DEPRECATED: ClaudeClient has been migrated to autoarr.shared.llm.ClaudeProvider
# This class is kept for backward compatibility only.
# New code should use LLMProviderFactory.create_provider() instead.


class ClaudeClient:
    """
    DEPRECATED: Compatibility wrapper around ClaudeProvider.

    This class is maintained for backward compatibility but is deprecated.
    New code should use autoarr.shared.llm.ClaudeProvider directly.

    Args:
        api_key: Anthropic API key
        model: Claude model to use (default: claude-3-5-sonnet-20241022)
        max_tokens: Maximum tokens in response
        max_retries: Maximum number of retries on rate limit (ignored)
        retry_delay: Initial retry delay in seconds (ignored, provider handles retries)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize Claude client (wraps ClaudeProvider)."""
        logger.warning("ClaudeClient is deprecated. Use autoarr.shared.llm.ClaudeProvider instead.")

        from autoarr.shared.llm.claude_provider import ClaudeProvider

        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create ClaudeProvider instance
        self._provider = ClaudeProvider(
            {
                "api_key": api_key,
                "default_model": model,
                "max_tokens": max_tokens,
                "max_retries": max_retries,
                "retry_delay": retry_delay,
            }
        )

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Send a message to Claude API (via ClaudeProvider).

        Args:
            system_prompt: System prompt (role definition)
            user_message: User message (query/request)
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Dict with 'content' (response text) and 'usage' (token counts)
        """
        # Convert to LLMMessage format
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        # Call provider
        response = await self._provider.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=self.max_tokens,
        )

        # Convert back to old format for compatibility
        return {
            "content": response.content,
            "usage": {
                "input_tokens": response.usage.get("prompt_tokens", 0) if response.usage else 0,
                "output_tokens": (
                    response.usage.get("completion_tokens", 0) if response.usage else 0
                ),
            },
        }

    async def close(self) -> None:
        """Close the API client."""
        if hasattr(self._provider, "__aexit__"):
            await self._provider.__aexit__(None, None, None)


class PromptTemplate:
    """
    Template system for LLM prompts.

    Provides reusable prompt templates with variable substitution
    for consistent prompt engineering across different use cases.

    Args:
        name: Template name
        system_template: System prompt template with {variables}
        user_template: User message template with {variables}
    """

    def __init__(
        self,
        name: str,
        system_template: str,
        user_template: str,
    ) -> None:
        """Initialize prompt template."""
        self.name = name
        self.system_template = system_template
        self.user_template = user_template

    def render_system(self, **kwargs: Any) -> str:
        """
        Render system prompt with variables.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Rendered system prompt

        Raises:
            KeyError: If required variable is missing
        """
        return self.system_template.format(**kwargs)

    def render_user(self, **kwargs: Any) -> str:
        """
        Render user message with variables.

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Rendered user message

        Raises:
            KeyError: If required variable is missing
        """
        return self.user_template.format(**kwargs)

    @classmethod
    def configuration_analysis(cls) -> "PromptTemplate":
        """
        Get the configuration analysis template.

        This template is used for analyzing application configurations
        against best practices and generating recommendations.

        Returns:
            PromptTemplate for configuration analysis
        """
        system_template = (
            "You are an expert configuration analyst for media automation "
            "applications.\n"
            "Your role is to analyze application configurations, identify "
            "issues, and provide\nclear, actionable recommendations based on "
            "industry best practices.\n\n"
            "When analyzing configurations:\n"
            "1. Compare current settings against best practices\n"
            "2. Assess the severity and impact of any deviations\n"
            "3. Provide specific, actionable recommendations\n"
            "4. Explain the reasoning behind each recommendation\n"
            "5. Consider the user's technical level (assume intermediate)\n\n"
            "Return your analysis in JSON format with these fields:\n"
            "- explanation: Detailed explanation of the issue/recommendation\n"
            "- priority: Priority level (high, medium, or low)\n"
            "- impact: What happens if this recommendation is not followed\n"
            "- reasoning: Technical reasoning for the recommendation"
        )

        user_template = """Analyze the following configuration for {app}:

Current Configuration:
{current_config}

Best Practice:
{best_practice}

Please provide a detailed analysis and recommendation."""

        return cls(
            name="configuration_analysis",
            system_template=system_template,
            user_template=user_template,
        )

    @classmethod
    def content_classification(cls) -> "PromptTemplate":
        """
        Get the content classification template.

        This template is used for classifying user content requests
        (movie vs TV show) and extracting metadata.

        Returns:
            PromptTemplate for content classification
        """
        system_template = (
            "You are a media content classifier for a home media "
            "automation system.\n"
            "Your role is to analyze user requests for movies or TV shows "
            "and extract key metadata.\n\n"
            "When analyzing requests:\n"
            "1. Determine if this is a movie or TV show request\n"
            "2. Extract the title (clean, without metadata)\n"
            "3. Identify the year if mentioned\n"
            "4. Identify quality preferences (4K, 1080p, etc.) if mentioned\n"
            "5. For TV shows, extract season and episode numbers if mentioned\n"
            "6. Provide a confidence score (0.0-1.0) based on clarity\n\n"
            "Return your analysis in JSON format with these fields:\n"
            "- content_type: Either 'movie' or 'tv'\n"
            "- title: The extracted title (without year, quality, or episode info)\n"
            "- year: Release year as integer (or null)\n"
            "- quality: Quality preference like '4K', '1080p', etc. (or null)\n"
            "- season: Season number as integer for TV shows (or null)\n"
            "- episode: Episode number as integer for TV shows (or null)\n"
            "- confidence: Confidence score from 0.0 to 1.0"
        )

        user_template = """User request: "{query}"

Please classify this request and extract all metadata."""

        return cls(
            name="content_classification",
            system_template=system_template,
            user_template=user_template,
        )


class StructuredOutputParser:
    """
    Parser for structured LLM outputs.

    Extracts and validates JSON responses from LLM outputs,
    handling markdown code blocks and ensuring required fields exist.

    Args:
        required_fields: List of required fields in parsed output
    """

    def __init__(self, required_fields: Optional[List[str]] = None) -> None:
        """Initialize output parser."""
        self.required_fields = required_fields or []

    def parse(self, response: str) -> Dict[str, Any]:
        """
        Parse structured output from LLM response.

        Extracts JSON from markdown code blocks or raw JSON strings,
        and validates that required fields are present.

        Args:
            response: LLM response text

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If JSON is invalid or required fields are missing
        """
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to parse the entire response as JSON
            json_str = response.strip()

        # If still empty, raise error
        if not json_str:
            raise ValueError("Response contains no parseable JSON content")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from response: {str(e)}")

        # Validate required fields
        for field in self.required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return data


class TokenUsageTracker:
    """
    Tracker for LLM token usage and cost estimation.

    Tracks input and output tokens across multiple requests
    and provides statistics and cost estimates.
    """

    def __init__(self) -> None:
        """Initialize token usage tracker."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        """
        Record token usage from a request.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Dict with total tokens, requests, and averages
        """
        total_tokens = self.total_input_tokens + self.total_output_tokens

        avg_input = self.total_input_tokens / self.total_requests if self.total_requests > 0 else 0
        avg_output = (
            self.total_output_tokens / self.total_requests if self.total_requests > 0 else 0
        )

        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": total_tokens,
            "total_requests": self.total_requests,
            "avg_input_tokens_per_request": avg_input,
            "avg_output_tokens_per_request": avg_output,
        }

    def estimate_cost(
        self,
        input_cost_per_million: float = 3.0,
        output_cost_per_million: float = 15.0,
    ) -> float:
        """
        Estimate cost based on token usage.

        Default pricing is for Claude 3.5 Sonnet:
        - Input: $3 per million tokens
        - Output: $15 per million tokens

        Args:
            input_cost_per_million: Cost per million input tokens
            output_cost_per_million: Cost per million output tokens

        Returns:
            Estimated cost in dollars
        """
        input_cost = (self.total_input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (self.total_output_tokens / 1_000_000) * output_cost_per_million
        return input_cost + output_cost

    def reset(self) -> None:
        """Reset all usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0


class LLMRecommendation(BaseModel):
    """LLM-generated recommendation."""

    explanation: str = Field(..., description="Detailed explanation")
    priority: Priority = Field(..., description="Priority level")
    impact: str = Field(..., description="Impact of not following recommendation")
    reasoning: str = Field(..., description="Technical reasoning")


class LLMAgent:
    """
    LLM Agent for intelligent configuration analysis.

    This agent uses Claude to analyze configurations, generate
    recommendations, and provide detailed explanations with
    context-aware priority assessment.

    Args:
        api_key: Anthropic API key
        model: Claude model to use
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

        Args:
            provider: Optional pre-configured LLM provider
            api_key: Optional API key for Claude (backward compatibility)
            model: Optional model name
            max_tokens: Maximum tokens in responses
        """
        self.max_tokens = max_tokens
        self.model = model
        self._provider = provider
        self._api_key = api_key
        self._initialized = False

        self.token_tracker = TokenUsageTracker()
        self.parser = StructuredOutputParser(
            required_fields=["explanation", "priority", "impact", "reasoning"]
        )

    async def _ensure_provider(self) -> BaseLLMProvider:
        """Lazy initialization of LLM provider."""
        if self._initialized and self._provider:
            return self._provider

        if self._provider is None:
            if self._api_key:
                # Backward compatibility: if API key provided, use Claude
                logger.info("Using Claude provider (API key provided)")
                from autoarr.shared.llm.claude_provider import ClaudeProvider

                config = {
                    "api_key": self._api_key,
                    "default_model": self.model or "claude-3-5-sonnet-20241022",
                    "max_tokens": self.max_tokens,
                }
                self._provider = ClaudeProvider(config)
            else:
                # Use factory (Ollama by default, Claude if key in env)
                logger.info("Auto-selecting LLM provider via factory")
                self._provider = await LLMProviderFactory.create_provider(
                    provider_name=None,  # Auto-select
                    config={"default_model": self.model} if self.model else None,
                )

        self._initialized = True
        logger.info(f"LLMAgent using {self._provider.provider_name} provider")
        return self._provider

    async def analyze_configuration(self, context: Dict[str, Any]) -> LLMRecommendation:
        """
        Analyze configuration and generate intelligent recommendation.

        Uses Claude to compare current configuration against best practices,
        assess priority based on impact, and generate detailed explanations.

        Args:
            context: Dict with keys:
                - app: Application name
                - current_config: Current configuration dict
                - best_practice: Best practice dict

        Returns:
            LLMRecommendation with explanation, priority, impact, and reasoning

        Raises:
            APIError: If Claude API call fails
            ValueError: If response cannot be parsed
        """
        # Get prompt template
        template = PromptTemplate.configuration_analysis()

        # Render prompts
        system_prompt = template.render_system()
        user_message = template.render_user(
            app=context["app"],
            current_config=json.dumps(context["current_config"], indent=2),
            best_practice=json.dumps(context["best_practice"], indent=2),
        )

        # Get provider
        provider = await self._ensure_provider()

        # Create messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        # Send to LLM provider
        response = await provider.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=self.max_tokens,
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

        Uses Claude to intelligently determine if the request is for a movie
        or TV show, and extracts relevant metadata like title, year, quality, etc.

        Args:
            query: User's content request

        Returns:
            ContentClassification with extracted metadata

        Raises:
            APIError: If Claude API call fails
            ValueError: If response cannot be parsed
        """
        # Import here to avoid circular dependency
        from autoarr.api.services.request_handler import ContentClassification

        # Get prompt template
        template = PromptTemplate.content_classification()

        # Render prompts
        system_prompt = template.render_system()
        user_message = template.render_user(query=query)

        # Send to Claude
        response = await self.client.send_message(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.3,  # Lower temperature for more consistent classification
        )

        # Track token usage
        usage = response["usage"]
        self.token_tracker.record_usage(
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )

        # Parse structured output
        classification_parser = StructuredOutputParser(
            required_fields=["content_type", "title", "confidence"]
        )
        parsed = classification_parser.parse(response["content"])

        # Validate content type
        content_type = parsed["content_type"].lower()
        if content_type not in ["movie", "tv"]:
            raise ValueError(f"Invalid content type: {content_type}")

        # Validate confidence
        confidence = float(parsed["confidence"])
        if not 0.0 <= confidence <= 1.0:
            confidence = 0.5  # Default to medium confidence if invalid

        # Create classification object
        classification = ContentClassification(
            content_type=content_type,
            title=parsed["title"],
            year=parsed.get("year"),
            quality=parsed.get("quality"),
            season=parsed.get("season"),
            episode=parsed.get("episode"),
            confidence=confidence,
        )

        return classification

    def get_token_usage_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics.

        Returns:
            Dict with token usage stats
        """
        return self.token_tracker.get_stats()

    def estimate_costs(
        self,
        input_cost_per_million: float = 3.0,
        output_cost_per_million: float = 15.0,
    ) -> float:
        """
        Estimate costs based on token usage.

        Args:
            input_cost_per_million: Cost per million input tokens
            output_cost_per_million: Cost per million output tokens

        Returns:
            Estimated cost in dollars
        """
        return self.token_tracker.estimate_cost(
            input_cost_per_million=input_cost_per_million,
            output_cost_per_million=output_cost_per_million,
        )

    async def close(self) -> None:
        """Close LLM client and cleanup resources."""
        await self.client.close()
