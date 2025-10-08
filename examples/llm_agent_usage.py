"""
Example usage of the LLM Agent for configuration analysis.

This script demonstrates how to use the LLM Agent to analyze
application configurations and generate intelligent recommendations.

Requirements:
- ANTHROPIC_API_KEY environment variable set
- anthropic package installed (included in project dependencies)

Usage:
    python examples/llm_agent_usage.py
"""

import asyncio
import json
import os
from typing import Dict, Any

from autoarr.api.services.llm_agent import LLMAgent
from autoarr.api.services.models import Priority


async def example_basic_analysis() -> None:
    """Example 1: Basic configuration analysis."""
    print("=" * 70)
    print("Example 1: Basic Configuration Analysis")
    print("=" * 70)

    # Initialize agent
    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    agent = LLMAgent(api_key=api_key, max_tokens=4096)

    # Analyze SABnzbd server configuration
    context = {
        "app": "sabnzbd",
        "current_config": {"servers": 1},
        "best_practice": {"servers": "multiple for redundancy"},
    }

    print(f"\nContext:\n{json.dumps(context, indent=2)}")

    try:
        recommendation = await agent.analyze_configuration(context)

        print(f"\n{'=' * 70}")
        print("Recommendation:")
        print(f"{'=' * 70}")
        print(f"\nPriority: {recommendation.priority.value.upper()}")
        print(f"\nExplanation:\n{recommendation.explanation}")
        print(f"\nImpact:\n{recommendation.impact}")
        print(f"\nReasoning:\n{recommendation.reasoning}")

        # Show token usage
        stats = agent.get_token_usage_stats()
        print(f"\n{'=' * 70}")
        print("Token Usage:")
        print(f"{'=' * 70}")
        print(f"Input tokens:  {stats['total_input_tokens']:,}")
        print(f"Output tokens: {stats['total_output_tokens']:,}")
        print(f"Total tokens:  {stats['total_tokens']:,}")
        print(f"Estimated cost: ${agent.estimate_costs():.4f}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Set ANTHROPIC_API_KEY environment variable to run with real API")


async def example_multiple_analyses() -> None:
    """Example 2: Analyze multiple configurations and track costs."""
    print("\n\n" + "=" * 70)
    print("Example 2: Multiple Configuration Analyses")
    print("=" * 70)

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    agent = LLMAgent(api_key=api_key)

    # Multiple configurations to analyze
    configs = [
        {
            "app": "sabnzbd",
            "current_config": {"incomplete_dir": ""},
            "best_practice": {"incomplete_dir": "separate from complete dir"},
        },
        {
            "app": "sonarr",
            "current_config": {"rename_episodes": False},
            "best_practice": {"rename_episodes": True},
        },
        {
            "app": "radarr",
            "current_config": {"minimum_availability": "announced"},
            "best_practice": {"minimum_availability": "released"},
        },
    ]

    print(f"\nAnalyzing {len(configs)} configurations...")

    try:
        for i, context in enumerate(configs, 1):
            print(f"\n{'-' * 70}")
            print(f"Analysis {i}/{len(configs)}: {context['app']}")
            print(f"{'-' * 70}")

            recommendation = await agent.analyze_configuration(context)

            print(f"Priority: {recommendation.priority.value.upper()}")
            print(f"Summary: {recommendation.explanation[:100]}...")

        # Summary statistics
        stats = agent.get_token_usage_stats()
        cost = agent.estimate_costs()

        print(f"\n{'=' * 70}")
        print("Summary Statistics:")
        print(f"{'=' * 70}")
        print(f"Total analyses:        {stats['total_requests']}")
        print(f"Total tokens:          {stats['total_tokens']:,}")
        print(f"Avg tokens/analysis:   {stats['total_tokens'] / stats['total_requests']:.0f}")
        print(f"Total estimated cost:  ${cost:.4f}")
        print(f"Cost per analysis:     ${cost / stats['total_requests']:.4f}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Set ANTHROPIC_API_KEY environment variable to run with real API")


async def example_priority_filtering() -> None:
    """Example 3: Analyze and filter by priority level."""
    print("\n\n" + "=" * 70)
    print("Example 3: Priority-Based Filtering")
    print("=" * 70)

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    agent = LLMAgent(api_key=api_key)

    # Analyze multiple settings
    configs = [
        {
            "name": "Server redundancy",
            "context": {
                "app": "sabnzbd",
                "current_config": {"servers": 1},
                "best_practice": {"servers": "multiple"},
            },
        },
        {
            "name": "Episode renaming",
            "context": {
                "app": "sonarr",
                "current_config": {"rename_episodes": False},
                "best_practice": {"rename_episodes": True},
            },
        },
        {
            "name": "Download handling",
            "context": {
                "app": "radarr",
                "current_config": {"enable_completed_download_handling": True},
                "best_practice": {"enable_completed_download_handling": True},
            },
        },
    ]

    high_priority = []
    medium_priority = []
    low_priority = []

    print("\nAnalyzing configurations...")

    try:
        for config in configs:
            recommendation = await agent.analyze_configuration(config["context"])

            result = {
                "name": config["name"],
                "app": config["context"]["app"],
                "priority": recommendation.priority,
                "explanation": recommendation.explanation,
            }

            if recommendation.priority == Priority.HIGH:
                high_priority.append(result)
            elif recommendation.priority == Priority.MEDIUM:
                medium_priority.append(result)
            else:
                low_priority.append(result)

        # Display by priority
        print(f"\n{'=' * 70}")
        print(f"HIGH PRIORITY ({len(high_priority)} issues)")
        print(f"{'=' * 70}")
        for item in high_priority:
            print(f"\n{item['name']} ({item['app']})")
            print(f"  {item['explanation'][:80]}...")

        print(f"\n{'=' * 70}")
        print(f"MEDIUM PRIORITY ({len(medium_priority)} issues)")
        print(f"{'=' * 70}")
        for item in medium_priority:
            print(f"\n{item['name']} ({item['app']})")
            print(f"  {item['explanation'][:80]}...")

        print(f"\n{'=' * 70}")
        print(f"LOW PRIORITY ({len(low_priority)} issues)")
        print(f"{'=' * 70}")
        for item in low_priority:
            print(f"\n{item['name']} ({item['app']})")
            print(f"  {item['explanation'][:80]}...")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Set ANTHROPIC_API_KEY environment variable to run with real API")


async def example_token_tracking() -> None:
    """Example 4: Track token usage and estimate costs."""
    print("\n\n" + "=" * 70)
    print("Example 4: Token Usage Tracking and Cost Estimation")
    print("=" * 70)

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    agent = LLMAgent(api_key=api_key)

    # Simulate different usage patterns
    print("\nSimulating different usage patterns...")

    patterns = [
        {
            "name": "Single configuration audit (4 apps)",
            "analyses": 4,
            "avg_input_tokens": 150,
            "avg_output_tokens": 80,
        },
        {
            "name": "Daily monitoring (4 apps, 1x/day, 30 days)",
            "analyses": 120,
            "avg_input_tokens": 150,
            "avg_output_tokens": 80,
        },
        {
            "name": "Hourly checks (4 apps, 24x/day, 30 days)",
            "analyses": 2880,
            "avg_input_tokens": 150,
            "avg_output_tokens": 80,
        },
    ]

    for pattern in patterns:
        # Reset tracker for each pattern
        agent.token_tracker.reset()

        # Simulate token usage
        for _ in range(pattern["analyses"]):
            agent.token_tracker.record_usage(
                input_tokens=pattern["avg_input_tokens"],
                output_tokens=pattern["avg_output_tokens"],
            )

        stats = agent.get_token_usage_stats()
        cost = agent.estimate_costs()

        print(f"\n{'-' * 70}")
        print(f"Pattern: {pattern['name']}")
        print(f"{'-' * 70}")
        print(f"Analyses:      {stats['total_requests']:,}")
        print(f"Total tokens:  {stats['total_tokens']:,}")
        print(f"Estimated cost: ${cost:.2f}")
        print(f"Cost/analysis: ${cost / stats['total_requests']:.4f}")


async def main() -> None:
    """Run all examples."""
    print("\n🤖 LLM Agent Usage Examples")
    print("=" * 70)
    print("\nThese examples demonstrate the LLM Agent capabilities:")
    print("1. Basic configuration analysis")
    print("2. Multiple analyses with cost tracking")
    print("3. Priority-based filtering")
    print("4. Token usage and cost estimation")
    print("\n" + "=" * 70)

    # Run examples
    await example_basic_analysis()
    await example_multiple_analyses()
    await example_priority_filtering()
    await example_token_tracking()

    print("\n\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
