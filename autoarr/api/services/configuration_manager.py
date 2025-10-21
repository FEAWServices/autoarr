"""
Configuration Manager Service.

This service handles configuration auditing, comparison against best practices,
and generation of recommendations for improving application configurations.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from autoarr.api.database import (AuditResultsRepository, BestPractice,
                                  BestPracticesRepository)
from autoarr.api.services.models import (ApplyRecommendationRequest,
                                         ApplyRecommendationResponse,
                                         AuditSummary, ConfigurationAudit,
                                         Priority, Recommendation,
                                         RecommendationType)
from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Manages configuration auditing and recommendations.

    This service:
    - Fetches current configurations from MCP servers
    - Compares configurations against best practices
    - Generates prioritized recommendations
    - Applies configuration changes (with dry-run support)
    - Tracks audit history
    """

    # Supported applications
    SUPPORTED_APPS = ["sabnzbd", "sonarr", "radarr", "plex"]

    # Priority weights for health score calculation
    PRIORITY_WEIGHTS = {
        Priority.HIGH: 10,
        Priority.MEDIUM: 5,
        Priority.LOW: 2,
    }

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        best_practices_repo: BestPracticesRepository,
        audit_repo: AuditResultsRepository,
    ):
        """
        Initialize Configuration Manager.

        Args:
            orchestrator: MCP Orchestrator for communicating with services
            best_practices_repo: Repository for best practices data
            audit_repo: Repository for audit results
        """
        self.orchestrator = orchestrator
        self.best_practices_repo = best_practices_repo
        self.audit_repo = audit_repo

    async def fetch_configuration(self, application: str) -> Dict[str, Any]:
        """
        Fetch current configuration from an application via MCP.

        Args:
            application: Application name (sabnzbd, sonarr, radarr, plex)

        Returns:
            Dictionary containing current configuration

        Raises:
            ValueError: If application is not supported
            Exception: If fetching configuration fails
        """
        if application not in self.SUPPORTED_APPS:
            raise ValueError(f"Unsupported application: {application}")

        logger.info(f"Fetching configuration for {application}")

        # Call the get_config tool on the MCP server
        config = await self.orchestrator.call_tool(
            server=application,
            tool="get_config",
            params={},
        )

        logger.debug(f"Fetched configuration for {application}: {config}")
        return config

    async def compare_configuration(
        self, application: str, current_config: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Compare current configuration against best practices.

        Args:
            application: Application name
            current_config: Current configuration dictionary

        Returns:
            List of recommendations for improvements
        """
        logger.info(f"Comparing configuration for {application}")

        # Fetch best practices for this application
        best_practices = await self.best_practices_repo.get_by_application(
            application, enabled_only=True
        )

        recommendations: List[Recommendation] = []

        for practice in best_practices:
            recommendation = self._check_setting(practice, current_config)
            if recommendation:
                recommendations.append(recommendation)

        # Sort recommendations by priority (high -> medium -> low)
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        recommendations.sort(key=lambda r: priority_order[r.priority])

        logger.info(f"Found {len(recommendations)} recommendations for {application}")
        return recommendations

    def _check_setting(
        self, practice: BestPractice, current_config: Dict[str, Any]
    ) -> Optional[Recommendation]:
        """
        Check a single setting against a best practice.

        Args:
            practice: Best practice to check against
            current_config: Current configuration

        Returns:
            Recommendation if setting doesn't match, None if it matches
        """
        setting_name = practice.setting_name
        current_value = current_config.get(setting_name)

        # Determine recommendation type and if action is needed
        recommendation_type = None
        needs_recommendation = False

        if setting_name not in current_config:
            # Setting is completely missing
            recommendation_type = RecommendationType.MISSING_SETTING
            needs_recommendation = True
        elif current_value is None or current_value == "":
            # Setting exists but is empty/null
            recommendation_type = RecommendationType.MISSING_SETTING
            needs_recommendation = True
        else:
            # Setting exists with a value - compare it
            # Normalize for comparison
            current_str = str(current_value).strip().lower()
            recommended_str = str(practice.recommended_value).strip().lower()

            if current_str != recommended_str:
                # Values don't match
                recommendation_type = RecommendationType.INCORRECT_VALUE
                needs_recommendation = True

        if not needs_recommendation:
            return None

        # Create recommendation
        return Recommendation(
            setting=setting_name,
            current_value=current_value,
            recommended_value=practice.recommended_value,
            priority=Priority(practice.priority),
            type=recommendation_type,
            description=practice.explanation,
            reasoning=practice.explanation,  # Use explanation for both
            impact=practice.impact or "No impact information available",
            category=practice.category,
            source_url=practice.documentation_url,
        )

    async def audit_application(
        self, application: str, config: Optional[Dict[str, Any]] = None
    ) -> ConfigurationAudit:
        """
        Perform a complete audit of an application's configuration.

        Args:
            application: Application name
            config: Optional pre-fetched configuration (for testing)

        Returns:
            ConfigurationAudit with recommendations and health score
        """
        logger.info(f"Starting audit for {application}")

        # Fetch configuration if not provided
        if config is None:
            config = await self.fetch_configuration(application)

        # Get recommendations
        recommendations = await self.compare_configuration(application, config)

        # Count issues by priority
        high_count = sum(1 for r in recommendations if r.priority == Priority.HIGH)
        medium_count = sum(1 for r in recommendations if r.priority == Priority.MEDIUM)
        low_count = sum(1 for r in recommendations if r.priority == Priority.LOW)

        # Get total number of checks (best practices)
        best_practices = await self.best_practices_repo.get_by_application(
            application, enabled_only=True
        )
        total_checks = len(best_practices)

        # Calculate health score
        health_score = self._calculate_health_score(total_checks, recommendations)

        # Create audit result
        audit = ConfigurationAudit(
            application=application,
            timestamp=datetime.utcnow(),
            total_checks=total_checks,
            issues_found=len(recommendations),
            high_priority_count=high_count,
            medium_priority_count=medium_count,
            low_priority_count=low_count,
            recommendations=recommendations,
            configuration_snapshot=config,
            overall_health_score=health_score,
        )

        # Save audit result to database
        await self._save_audit_result(audit)

        logger.info(
            f"Audit complete for {application}: "
            f"{len(recommendations)} issues found, "
            f"health score: {health_score:.1f}"
        )

        return audit

    def _calculate_health_score(
        self, total_checks: int, recommendations: List[Recommendation]
    ) -> float:
        """
        Calculate overall health score (0-100).

        Score calculation:
        - Start with 100
        - Subtract weighted points for each issue based on priority
        - High priority: -10 points
        - Medium priority: -5 points
        - Low priority: -2 points
        - Minimum score is 0

        Args:
            total_checks: Total number of checks performed
            recommendations: List of recommendations (issues found)

        Returns:
            Health score between 0 and 100
        """
        if total_checks == 0:
            return 100.0

        # Calculate penalty points
        penalty = sum(self.PRIORITY_WEIGHTS[rec.priority] for rec in recommendations)

        # Calculate score (100 - penalty, minimum 0)
        score = max(0, 100 - penalty)

        return float(score)

    async def _save_audit_result(self, audit: ConfigurationAudit) -> None:
        """
        Save audit result to database.

        Args:
            audit: ConfigurationAudit to save
        """
        try:
            # Convert recommendations to JSON
            recommendations_json = json.dumps([rec.model_dump() for rec in audit.recommendations])

            # Convert config snapshot to JSON
            config_json = json.dumps(audit.configuration_snapshot)

            await self.audit_repo.save_audit_result(
                application=audit.application,
                total_checks=audit.total_checks,
                issues_found=audit.issues_found,
                high_priority=audit.high_priority_count,
                medium_priority=audit.medium_priority_count,
                low_priority=audit.low_priority_count,
                configuration_snapshot=config_json,
                recommendations=recommendations_json,
            )
            logger.debug(f"Saved audit result for {audit.application}")
        except Exception as e:
            logger.error(f"Failed to save audit result: {e}")
            # Don't fail the audit if saving fails

    async def audit_all_applications(self) -> Dict[str, ConfigurationAudit]:
        """
        Audit all supported applications.

        Returns:
            Dictionary mapping application names to audit results
        """
        logger.info("Starting audit of all applications")

        results = {}
        for app in self.SUPPORTED_APPS:
            try:
                audit = await self.audit_application(app)
                results[app] = audit
            except Exception as e:
                logger.error(f"Failed to audit {app}: {e}")
                # Continue with other applications
                continue

        logger.info(f"Completed audit of {len(results)} applications")
        return results

    async def apply_recommendation(
        self, request: ApplyRecommendationRequest
    ) -> ApplyRecommendationResponse:
        """
        Apply a configuration recommendation.

        Args:
            request: Request containing setting to apply

        Returns:
            Response indicating success or failure
        """
        logger.info(
            f"Applying recommendation for {request.application}: "
            f"{request.setting} = {request.value} (dry_run={request.dry_run})"
        )

        if request.application not in self.SUPPORTED_APPS:
            return ApplyRecommendationResponse(
                success=False,
                setting=request.setting,
                previous_value=None,
                new_value=request.value,
                message=f"Unsupported application: {request.application}",
                dry_run=request.dry_run,
            )

        try:
            if request.dry_run:
                # Dry run - just validate
                return ApplyRecommendationResponse(
                    success=True,
                    setting=request.setting,
                    previous_value=None,
                    new_value=request.value,
                    message=f"Dry run: {request.setting} would be updated to {request.value}",
                    dry_run=True,
                )

            # Actually apply the configuration
            result = await self.orchestrator.call_tool(  # noqa: F841
                server=request.application,
                tool="set_config",
                params={
                    "setting": request.setting,
                    "value": request.value,
                },
            )

            return ApplyRecommendationResponse(
                success=True,
                setting=request.setting,
                previous_value=None,  # Could fetch this before applying
                new_value=request.value,
                message=f"Successfully updated {request.setting}",
                dry_run=False,
            )

        except Exception as e:
            logger.error(f"Failed to apply recommendation: {e}")
            return ApplyRecommendationResponse(
                success=False,
                setting=request.setting,
                previous_value=None,
                new_value=request.value,
                message=f"Failed to apply: {str(e)}",
                dry_run=request.dry_run,
            )

    async def get_audit_history(self, application: str, limit: int = 10) -> List[AuditSummary]:
        """
        Get audit history for an application.

        Args:
            application: Application name
            limit: Maximum number of results to return

        Returns:
            List of audit summaries ordered by timestamp (newest first)
        """
        logger.info(f"Fetching audit history for {application} (limit={limit})")

        audit_results = await self.audit_repo.get_audit_history(application, limit)

        summaries = [
            AuditSummary(
                application=result.application,
                timestamp=result.timestamp,
                issues_found=result.issues_found,
                high_priority_count=result.high_priority,
                medium_priority_count=result.medium_priority,
                low_priority_count=result.low_priority,
                health_score=(
                    self._calculate_health_score(
                        result.total_checks, []  # We don't need full recommendations for summary
                    )
                    if result.total_checks > 0
                    else 100.0
                ),
            )
            for result in audit_results
        ]

        return summaries
