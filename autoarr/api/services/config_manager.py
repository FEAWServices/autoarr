"""
Configuration Manager Service.

This service manages configuration audits, recommendations, and application of
configuration changes. This is a mock implementation that will be replaced
with the actual ConfigurationManager from Task 3.2.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class ConfigurationManager:
    """
    Configuration Manager for auditing and applying configuration recommendations.

    This is a mock implementation. The actual implementation will integrate with:
    - Best Practices Database (Task 3.1)
    - Web Search Service (Task 3.3)
    - Service-specific configuration APIs
    """

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        # In-memory storage for recommendations (will be replaced with database)
        self._recommendations: Dict[int, Dict[str, Any]] = {}
        self._audit_history: List[Dict[str, Any]] = []
        self._next_recommendation_id = 1

    async def audit_configuration(
        self, services: List[str], include_web_search: bool = False
    ) -> Dict[str, Any]:
        """
        Audit configuration for specified services.

        Args:
            services: List of service names to audit
            include_web_search: Whether to use web search for latest best practices

        Returns:
            Dict containing audit results and recommendations

        Raises:
            ValueError: If invalid service name provided
        """
        # Validate service names
        valid_services = ["sabnzbd", "sonarr", "radarr", "plex"]
        for service in services:
            if service not in valid_services:
                raise ValueError(
                    f"Invalid service '{service}'. Must be one of: {', '.join(valid_services)}"
                )

        if not services:
            raise ValueError("At least one service must be specified")

        # Generate unique audit ID
        audit_id = f"audit_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Mock: Generate sample recommendations
        # In real implementation, this would:
        # 1. Fetch current configuration from each service
        # 2. Compare against best practices database
        # 3. Optionally search web for latest recommendations
        # 4. Generate actionable recommendations

        recommendations = []
        for service in services:
            # Store recommendation
            rec_id = self._next_recommendation_id
            self._next_recommendation_id += 1

            recommendation = {
                "id": rec_id,
                "service": service,
                "category": "performance",
                "priority": "medium",
                "title": f"Sample recommendation for {service}",
                "description": f"This is a mock recommendation for {service}",
                "current_value": "default",
                "recommended_value": "optimized",
                "impact": "Improved performance",
                "source": "web_search" if include_web_search else "database",
                "applied": False,
                "applied_at": None,
            }

            self._recommendations[rec_id] = recommendation
            recommendations.append(recommendation)

        # Store audit history
        audit_record = {
            "audit_id": audit_id,
            "timestamp": timestamp,
            "services": services,
            "total_recommendations": len(recommendations),
            "applied_recommendations": 0,
            "web_search_used": include_web_search,
        }
        self._audit_history.append(audit_record)

        return {
            "audit_id": audit_id,
            "timestamp": timestamp,
            "services": services,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "web_search_used": include_web_search,
        }

    async def get_recommendations(
        self,
        service: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Get list of recommendations with optional filtering.

        Args:
            service: Filter by service name
            priority: Filter by priority level
            category: Filter by category
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dict containing recommendations list with pagination info
        """
        # Filter recommendations
        filtered = list(self._recommendations.values())

        if service:
            filtered = [r for r in filtered if r["service"] == service]
        if priority:
            filtered = [r for r in filtered if r["priority"] == priority]
        if category:
            filtered = [r for r in filtered if r["category"] == category]

        # Pagination
        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = filtered[start_idx:end_idx]

        return {
            "recommendations": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_recommendation_by_id(self, recommendation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific recommendation.

        Args:
            recommendation_id: Recommendation ID

        Returns:
            Detailed recommendation or None if not found
        """
        recommendation = self._recommendations.get(recommendation_id)
        if not recommendation:
            return None

        # Add detailed fields for the detailed view
        return {
            **recommendation,
            "explanation": f"Detailed explanation for recommendation {recommendation_id}",
            "references": [
                "https://example.com/docs/best-practices",
                "https://example.com/guides/optimization",
            ],
        }

    async def apply_recommendations(
        self, recommendation_ids: List[int], dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply configuration recommendations.

        Args:
            recommendation_ids: List of recommendation IDs to apply
            dry_run: If True, simulate without making actual changes

        Returns:
            Dict containing results for each recommendation

        Raises:
            ValueError: If recommendation_ids is empty
        """
        if not recommendation_ids:
            raise ValueError("At least one recommendation ID must be specified")

        results = []
        successful = 0
        failed = 0

        for rec_id in recommendation_ids:
            recommendation = self._recommendations.get(rec_id)

            if not recommendation:
                results.append(
                    {
                        "recommendation_id": rec_id,
                        "success": False,
                        "message": "Recommendation not found",
                        "service": None,
                        "applied_at": None,
                        "dry_run": dry_run,
                    }
                )
                failed += 1
                continue

            # In real implementation, this would:
            # 1. Connect to the service
            # 2. Apply the configuration change
            # 3. Verify the change was successful
            # 4. Update the recommendation status

            if dry_run:
                results.append(
                    {
                        "recommendation_id": rec_id,
                        "success": True,
                        "message": "Dry run: Would apply this recommendation",
                        "service": recommendation["service"],
                        "applied_at": None,
                        "dry_run": True,
                    }
                )
            else:
                # Mock successful application
                applied_at = datetime.utcnow().isoformat() + "Z"
                recommendation["applied"] = True
                recommendation["applied_at"] = applied_at

                results.append(
                    {
                        "recommendation_id": rec_id,
                        "success": True,
                        "message": "Configuration applied successfully",
                        "service": recommendation["service"],
                        "applied_at": applied_at,
                        "dry_run": False,
                    }
                )
                successful += 1

        return {
            "results": results,
            "total_requested": len(recommendation_ids),
            "total_successful": successful if not dry_run else 0,
            "total_failed": failed,
            "dry_run": dry_run,
        }

    async def get_audit_history(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Get audit history with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dict containing audit history with pagination info
        """
        # Sort by timestamp descending (most recent first)
        sorted_audits = sorted(self._audit_history, key=lambda x: x["timestamp"], reverse=True)

        # Pagination
        total = len(sorted_audits)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = sorted_audits[start_idx:end_idx]

        return {
            "audits": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
        }


# Singleton instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager_instance() -> ConfigurationManager:
    """
    Get or create the singleton ConfigurationManager instance.

    Returns:
        ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def reset_config_manager() -> None:
    """Reset the singleton instance (for testing)."""
    global _config_manager
    _config_manager = None
