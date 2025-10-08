"""
Demonstration of the Intelligent Recommendation Engine.

This script shows how to use the Intelligent Recommendation Engine to generate
LLM-powered configuration recommendations with detailed explanations, impact
analysis, and implementation guidance.

Note: This requires a valid Anthropic API key set in the environment variable
ANTHROPIC_API_KEY or passed directly to the engine.
"""

import asyncio
import json
import os
from typing import Dict, Any

from autoarr.api.services.intelligent_recommendation_engine import (
    IntelligentRecommendationEngine,
)


async def demonstrate_basic_recommendation() -> None:
    """Demonstrate basic recommendation generation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Recommendation (SABnzbd Server Configuration)")
    print("=" * 80 + "\n")

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")

    # Initialize engine
    engine = IntelligentRecommendationEngine(api_key=api_key)

    # Current configuration (suboptimal)
    current_config = {
        "servers": 1,  # Only one server configured
    }

    # Best practice information
    best_practice = {
        "setting": "servers",
        "recommendation": "Configure at least 2-3 servers from different providers for redundancy",
        "priority": "high",
    }

    print("Current Configuration:")
    print(json.dumps(current_config, indent=2))
    print("\nBest Practice:")
    print(json.dumps(best_practice, indent=2))
    print("\n" + "-" * 80)
    print("Generating LLM-powered recommendation...")
    print("-" * 80 + "\n")

    try:
        # Generate recommendation
        recommendation = await engine.generate_recommendation(
            application="sabnzbd",
            current_config=current_config,
            best_practice_data=best_practice,
        )

        # Display results
        print(f"Application: {recommendation.application}")
        print(f"Setting: {recommendation.setting}")
        print(f"Priority: {recommendation.priority.value.upper()}")
        print(f"\nCurrent Value: {recommendation.current_value}")
        print(f"Recommended Value: {recommendation.recommended_value}")
        print(f"\n{'Why is this important?'}")
        print(f"{recommendation.explanation}")
        print(f"\n{'What happens if not fixed?'}")
        print(f"{recommendation.impact}")
        print(f"\n{'How to implement:'}")
        print(f"{recommendation.reasoning}")

        # Show token usage
        stats = engine.get_token_usage_stats()
        print(f"\n{'Token Usage:'}")
        print(f"  Input tokens: {stats['total_input_tokens']}")
        print(f"  Output tokens: {stats['total_output_tokens']}")
        print(f"  Total tokens: {stats['total_tokens']}")

        # Estimate cost
        cost = engine.estimate_costs()
        print(f"  Estimated cost: ${cost:.4f}")

    except Exception as e:
        print(f"Error generating recommendation: {e}")
    finally:
        await engine.close()


async def demonstrate_security_recommendation() -> None:
    """Demonstrate security-focused recommendation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Security Recommendation (SSL Verification)")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    engine = IntelligentRecommendationEngine(api_key=api_key)

    current_config = {
        "ssl_verify": False,  # SSL verification disabled (insecure!)
    }

    best_practice = {
        "setting": "ssl_verify",
        "recommendation": "Enable SSL verification for secure connections",
        "priority": "high",
        "category": "security",
    }

    print("Current Configuration:")
    print(json.dumps(current_config, indent=2))
    print("\nBest Practice:")
    print(json.dumps(best_practice, indent=2))
    print("\n" + "-" * 80)
    print("Generating security recommendation...")
    print("-" * 80 + "\n")

    try:
        recommendation = await engine.generate_recommendation(
            application="sabnzbd",
            current_config=current_config,
            best_practice_data=best_practice,
        )

        print(f"Priority: {recommendation.priority.value.upper()} ⚠️")
        print(f"\n{recommendation.explanation}")
        print(f"\nSecurity Impact:")
        print(f"{recommendation.impact}")
        print(f"\nTechnical Details:")
        print(f"{recommendation.reasoning}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.close()


async def demonstrate_batch_recommendations() -> None:
    """Demonstrate generating multiple recommendations efficiently."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Batch Recommendations (Multiple Settings)")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    engine = IntelligentRecommendationEngine(api_key=api_key)

    configurations = [
        {
            "name": "servers",
            "current": {"servers": 1},
            "best_practice": {
                "setting": "servers",
                "recommendation": "multiple servers",
            },
        },
        {
            "name": "article_cache",
            "current": {"article_cache": "100M"},
            "best_practice": {
                "setting": "article_cache",
                "recommendation": "500M or higher",
            },
        },
        {
            "name": "direct_unpack",
            "current": {"direct_unpack": False},
            "best_practice": {
                "setting": "direct_unpack",
                "recommendation": "true",
            },
        },
    ]

    print(f"Analyzing {len(configurations)} configuration settings...")
    print("-" * 80 + "\n")

    try:
        recommendations = []
        for config in configurations:
            recommendation = await engine.generate_recommendation(
                application="sabnzbd",
                current_config=config["current"],
                best_practice_data=config["best_practice"],
            )
            recommendations.append(recommendation)

        # Summary
        print(f"Generated {len(recommendations)} recommendations:\n")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.setting.upper()}")
            print(f"   Priority: {rec.priority.value.upper()}")
            print(f"   Current: {rec.current_value}")
            print(f"   Recommended: {rec.recommended_value}")
            print(f"   Brief: {rec.explanation[:100]}...")
            print()

        # Total token usage
        stats = engine.get_token_usage_stats()
        cost = engine.estimate_costs()
        print(f"Total Usage:")
        print(f"  Requests: {stats['total_requests']}")
        print(f"  Total tokens: {stats['total_tokens']}")
        print(f"  Estimated cost: ${cost:.4f}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.close()


async def demonstrate_with_web_search() -> None:
    """Demonstrate recommendation with web search context."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Recommendation with Web Search Context")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    engine = IntelligentRecommendationEngine(api_key=api_key)

    current_config = {
        "incomplete_dir": "",  # Not configured
    }

    best_practice = {
        "setting": "incomplete_dir",
        "recommendation": "Set separate incomplete directory",
    }

    # Simulate web search findings
    web_search_data = {
        "query": "sabnzbd incomplete directory best practices",
        "results": [
            {
                "title": "SABnzbd Configuration Guide",
                "snippet": (
                    "Using a separate incomplete directory prevents issues "
                    "with partially downloaded files"
                ),
                "url": "https://sabnzbd.org/wiki/configuration/folders",
            },
            {
                "title": "Optimize SABnzbd Downloads",
                "snippet": (
                    "Incomplete files should be kept separate to avoid "
                    "confusion with complete downloads"
                ),
                "url": "https://example.com/sabnzbd-optimization",
            },
        ],
    }

    print("Current Configuration:")
    print(json.dumps(current_config, indent=2))
    print("\nWeb Search Findings:")
    print(f"  - {web_search_data['results'][0]['title']}")
    print(f"  - {web_search_data['results'][1]['title']}")
    print("\n" + "-" * 80)
    print("Generating recommendation with web search context...")
    print("-" * 80 + "\n")

    try:
        recommendation = await engine.generate_recommendation(
            application="sabnzbd",
            current_config=current_config,
            best_practice_data=best_practice,
            web_search_data=web_search_data,
        )

        print(f"Recommendation: {recommendation.setting}")
        print(f"Priority: {recommendation.priority.value.upper()}")
        print(f"\n{recommendation.explanation}")
        print(f"\nSource References:")
        if recommendation.source_references:
            for url in recommendation.source_references:
                print(f"  - {url}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.close()


async def demonstrate_with_audit_history() -> None:
    """Demonstrate recommendation with historical audit context."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Recommendation with Audit History")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "demo-key")
    engine = IntelligentRecommendationEngine(api_key=api_key)

    current_config = {"servers": 1}

    best_practice = {
        "setting": "servers",
        "recommendation": "multiple servers",
    }

    # Historical audit data showing this was recommended before
    audit_history = [
        {
            "timestamp": "2025-09-01T10:00:00Z",
            "recommendations": 5,
            "applied": 3,
            "note": "Server redundancy recommendation not applied",
        },
        {
            "timestamp": "2025-10-01T10:00:00Z",
            "recommendations": 4,
            "applied": 2,
            "note": "Server redundancy recommendation not applied",
        },
    ]

    print("Current Configuration:")
    print(json.dumps(current_config, indent=2))
    print("\nAudit History:")
    for audit in audit_history:
        print(f"  - {audit['timestamp']}: {audit['note']}")
    print("\n" + "-" * 80)
    print("Generating recommendation with audit history...")
    print("-" * 80 + "\n")

    try:
        recommendation = await engine.generate_recommendation(
            application="sabnzbd",
            current_config=current_config,
            best_practice_data=best_practice,
            audit_history=audit_history,
        )

        print(f"Priority: {recommendation.priority.value.upper()}")
        print(f"\n{recommendation.explanation}")
        print(f"\nNote: This recommendation has appeared in {len(audit_history)} previous audits.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.close()


async def main() -> None:
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("INTELLIGENT RECOMMENDATION ENGINE DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo shows the LLM-powered recommendation engine in action.")
    print("The engine generates detailed explanations, impact analysis, and")
    print("implementation guidance for configuration recommendations.")
    print("\nNote: These examples use mocked data. In production, the engine")
    print("would connect to real applications and use actual Claude API.")
    print("=" * 80)

    # Run all examples
    await demonstrate_basic_recommendation()
    await demonstrate_security_recommendation()
    await demonstrate_batch_recommendations()
    await demonstrate_with_web_search()
    await demonstrate_with_audit_history()

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Basic recommendation generation")
    print("  ✓ Security-focused analysis")
    print("  ✓ Batch processing multiple recommendations")
    print("  ✓ Web search context integration")
    print("  ✓ Historical audit data consideration")
    print("  ✓ Token usage tracking and cost estimation")
    print("\nFor more information, see:")
    print("  - /app/autoarr/api/services/intelligent_recommendation_engine.py")
    print("  - /app/autoarr/tests/unit/services/test_intelligent_recommendation_engine.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Note: This demo uses mocked LLM responses for demonstration purposes
    # In production, set ANTHROPIC_API_KEY environment variable
    print("\nWARNING: This demo requires ANTHROPIC_API_KEY to be set.")
    print("Without a valid API key, the examples will show error messages.")
    print("To run with real LLM responses:")
    print("  export ANTHROPIC_API_KEY='your-api-key-here'")
    print("  python examples/intelligent_recommendation_demo.py\n")

    asyncio.run(main())
