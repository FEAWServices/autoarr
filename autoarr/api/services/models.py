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
Data models for configuration management service.

This module defines Pydantic models used by the Configuration Manager
for recommendations, audit results, and configuration comparisons.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Priority levels for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationType(str, Enum):
    """Types of recommendations."""

    MISSING_SETTING = "missing_setting"
    INCORRECT_VALUE = "incorrect_value"
    SUBOPTIMAL_VALUE = "suboptimal_value"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


class Recommendation(BaseModel):
    """A configuration recommendation."""

    setting: str = Field(..., description="Configuration setting name")
    current_value: Optional[Any] = Field(None, description="Current value")
    recommended_value: Any = Field(..., description="Recommended value")
    priority: Priority = Field(..., description="Recommendation priority")
    type: RecommendationType = Field(..., description="Type of recommendation")
    description: str = Field(..., description="Brief description of the issue")
    reasoning: str = Field(..., description="Why this change is recommended")
    impact: str = Field(..., description="Impact of not following this recommendation")
    category: str = Field(..., description="Category (downloads, quality, monitoring, etc.)")
    source_url: Optional[str] = Field(None, description="Source documentation URL")

    model_config = {"use_enum_values": True}


class ConfigurationAudit(BaseModel):
    """Result of a configuration audit."""

    application: str = Field(..., description="Application name (sabnzbd, sonarr, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Audit timestamp")
    total_checks: int = Field(..., description="Total number of checks performed")
    issues_found: int = Field(..., description="Number of issues found")
    high_priority_count: int = Field(0, description="Number of high priority issues")
    medium_priority_count: int = Field(0, description="Number of medium priority issues")
    low_priority_count: int = Field(0, description="Number of low priority issues")
    recommendations: List[Recommendation] = Field(
        default_factory=list, description="List of recommendations"
    )
    configuration_snapshot: Dict[str, Any] = Field(
        ..., description="Snapshot of current configuration"
    )
    overall_health_score: float = Field(
        ..., ge=0, le=100, description="Overall health score (0-100)"
    )


class AuditSummary(BaseModel):
    """Summary of audit results for display."""

    application: str = Field(..., description="Application name")
    timestamp: datetime = Field(..., description="Audit timestamp")
    issues_found: int = Field(..., description="Total issues found")
    high_priority_count: int = Field(..., description="High priority issues")
    medium_priority_count: int = Field(..., description="Medium priority issues")
    low_priority_count: int = Field(..., description="Low priority issues")
    health_score: float = Field(..., description="Health score 0-100")


class ApplyRecommendationRequest(BaseModel):
    """Request to apply a recommendation."""

    application: str = Field(..., description="Application name")
    setting: str = Field(..., description="Setting to update")
    value: Any = Field(..., description="New value to apply")
    dry_run: bool = Field(False, description="If True, simulate without applying")


class ApplyRecommendationResponse(BaseModel):
    """Response from applying a recommendation."""

    success: bool = Field(..., description="Whether the operation succeeded")
    setting: str = Field(..., description="Setting that was updated")
    previous_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Any = Field(..., description="New value")
    message: str = Field(..., description="Status message")
    dry_run: bool = Field(False, description="Whether this was a dry run")
