"""
Pydantic models for Configuration Audit API.

This module defines request and response models for the configuration audit endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Configuration Audit Models
# ============================================================================


class ConfigAuditRequest(BaseModel):
    """Request model for configuration audit."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "services": ["sabnzbd", "sonarr"],
                "include_web_search": True,
            }
        }
    )

    services: List[str] = Field(..., description="List of services to audit", min_length=1)
    include_web_search: bool = Field(
        False, description="Whether to use web search for latest best practices"
    )


class Recommendation(BaseModel):
    """Configuration recommendation model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "service": "sabnzbd",
                "category": "performance",
                "priority": "high",
                "title": "Increase article cache",
                "description": "Current cache is too small for optimal performance",
                "current_value": "100M",
                "recommended_value": "500M",
                "impact": "Improved download speed",
                "applied": False,
            }
        }
    )

    id: int = Field(..., description="Recommendation ID")
    service: str = Field(..., description="Service name")
    category: str = Field(..., description="Category (performance, security, best_practices)")
    priority: str = Field(..., description="Priority (high, medium, low)")
    title: str = Field(..., description="Brief title")
    description: str = Field(..., description="Detailed description")
    current_value: Optional[str] = Field(None, description="Current configuration value")
    recommended_value: str = Field(..., description="Recommended value")
    impact: str = Field(..., description="Impact description")
    source: Optional[str] = Field(None, description="Source of recommendation")
    applied: bool = Field(False, description="Whether recommendation has been applied")
    applied_at: Optional[str] = Field(None, description="ISO timestamp when applied")


class DetailedRecommendation(Recommendation):
    """Detailed recommendation with explanation and references."""

    explanation: str = Field(..., description="Detailed explanation of the recommendation")
    references: List[str] = Field(
        default_factory=list, description="Reference URLs and documentation"
    )


class ConfigAuditResponse(BaseModel):
    """Response model for configuration audit."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audit_id": "audit_123",
                "timestamp": "2025-10-08T10:00:00Z",
                "services": ["sabnzbd"],
                "recommendations": [],
                "total_recommendations": 0,
                "web_search_used": False,
            }
        }
    )

    audit_id: str = Field(..., description="Unique audit identifier")
    timestamp: str = Field(..., description="ISO timestamp of audit")
    services: List[str] = Field(..., description="Services that were audited")
    recommendations: List[Recommendation] = Field(..., description="List of recommendations")
    total_recommendations: int = Field(..., description="Total number of recommendations")
    web_search_used: Optional[bool] = Field(False, description="Whether web search was used")


class RecommendationsListResponse(BaseModel):
    """Response model for listing recommendations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendations": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
            }
        }
    )

    recommendations: List[Recommendation] = Field(..., description="List of recommendations")
    total: int = Field(..., description="Total number of recommendations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class ApplyConfigRequest(BaseModel):
    """Request model for applying configuration changes."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendation_ids": [1, 2, 3],
                "dry_run": False,
            }
        }
    )

    recommendation_ids: List[int] = Field(
        ..., description="List of recommendation IDs to apply", min_length=1
    )
    dry_run: bool = Field(False, description="If true, simulate without making changes")


class ApplyResult(BaseModel):
    """Result of applying a single recommendation."""

    recommendation_id: int = Field(..., description="Recommendation ID")
    success: bool = Field(..., description="Whether the application was successful")
    message: str = Field(..., description="Result message")
    service: Optional[str] = Field(None, description="Service name")
    applied_at: Optional[str] = Field(None, description="ISO timestamp when applied")
    dry_run: Optional[bool] = Field(None, description="Whether this was a dry run")


class ApplyConfigResponse(BaseModel):
    """Response model for applying configuration changes."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [],
                "total_requested": 0,
                "total_successful": 0,
                "total_failed": 0,
                "dry_run": False,
            }
        }
    )

    results: List[ApplyResult] = Field(..., description="Results for each recommendation")
    total_requested: int = Field(..., description="Total number of recommendations requested")
    total_successful: int = Field(..., description="Number of successful applications")
    total_failed: int = Field(..., description="Number of failed applications")
    dry_run: Optional[bool] = Field(False, description="Whether this was a dry run")


class AuditHistoryItem(BaseModel):
    """Single audit history item."""

    audit_id: str = Field(..., description="Audit identifier")
    timestamp: str = Field(..., description="ISO timestamp of audit")
    services: List[str] = Field(..., description="Services audited")
    total_recommendations: int = Field(..., description="Total recommendations generated")
    applied_recommendations: int = Field(..., description="Number of applied recommendations")
    web_search_used: bool = Field(False, description="Whether web search was used")


class AuditHistoryResponse(BaseModel):
    """Response model for audit history."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audits": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
            }
        }
    )

    audits: List[AuditHistoryItem] = Field(..., description="List of audit history items")
    total: int = Field(..., description="Total number of audits")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
