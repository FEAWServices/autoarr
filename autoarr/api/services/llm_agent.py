"""
LLM Agent Service for AutoArr.

This service provides LLM-powered intelligent analysis and recommendations
using Claude API. It includes:
- Claude API client with retry logic
- Prompt template system
- Structured output parsing
- Token usage tracking and cost estimation
- Configuration analysis and recommendation generation
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from anthropic import APIError, AsyncAnthropic, RateLimitError
from pydantic import BaseModel, Field

from autoarr.api.services.models import Priority


class ClaudeClient:
    """
    Claude API client with retry logic and error handling.

    This client handles communication with the Anthropic Claude API,
    including automatic retries with exponential backoff for rate limits.

    Args:
        api_key: Anthropic API key
        model: Claude model to use (default: claude-3-5-sonnet-20241022)
        max_tokens: Maximum tokens in response
        max_retries: Maximum number of retries on rate limit
        retry_delay: Initial retry delay in seconds (doubles on each retry)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize Claude client."""
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[AsyncAnthropic] = None

    @property
    def client(self) -> AsyncAnthropic:
        """Get or create the Anthropic client."""
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Send a message to Claude API with retry logic.

        This method automatically retries on rate limit errors with
        exponential backoff. Other API errors are raised immediately.

        Args:
            system_prompt: System prompt (role definition)
            user_message: User message (query/request)
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Dict with 'content' (response text) and 'usage' (token counts)

        Raises:
            RateLimitError: If rate limit exceeded after all retries
            APIError: If other API error occurs
        """
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count <= self.max_retries:
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )

                # Extract response content and usage
                content = response.content[0].text
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }

                return {"content": content, "usage": usage}

            except RateLimitError as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    raise e

                # Exponential backoff
                await asyncio.sleep(current_delay)
                current_delay *= 2

            except APIError:
                # Don't retry on other API errors
                raise

    async def close(self) -> None:
        """Close the API client."""
        if self._client is not None:
            await self._client.close()


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
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ) -> None:
        """Initialize LLM agent."""
        self.client = ClaudeClient(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
        )
        self.token_tracker = TokenUsageTracker()
        self.parser = StructuredOutputParser(
            required_fields=["explanation", "priority", "impact", "reasoning"]
        )

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

        # Send to Claude
        response = await self.client.send_message(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,
        )

        # Track token usage
        usage = response["usage"]
        self.token_tracker.record_usage(
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )

        # Parse structured output
        parsed = self.parser.parse(response["content"])

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
