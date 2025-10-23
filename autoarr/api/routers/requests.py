"""
Content Request API Endpoints.

This module provides RESTful API endpoints for content requests,
allowing users to request movies and TV shows through natural language.
"""

import uuid
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from autoarr.api.database import ContentRequestRepository, get_database
from autoarr.api.services.content_integration import ContentIntegrationService
from autoarr.api.services.request_handler import (
    ContentClassification,
    ContentSearchResult,
    RequestHandler,
)

# Create router
router = APIRouter(prefix="/api/v1/requests", tags=["requests"])

# TODO: Add rate limiting with slowapi when implementing production features
# from slowapi import Limiter
# from slowapi.util import get_remote_address
# limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Request Models
# ============================================================================


class ContentRequestInput(BaseModel):
    """Input model for content request."""

    query: str = Field(..., description="Natural language content request", min_length=1)
    user_id: Optional[str] = Field(None, description="Optional user ID")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "query": "Add Dune Part 2 in 4K",
                "user_id": "user123",
            }
        }


class ContentRequestResponse(BaseModel):
    """Response model for content request."""

    id: int = Field(..., description="Request ID")
    correlation_id: str = Field(..., description="Unique correlation ID")
    query: str = Field(..., description="Original query")
    classification: ContentClassification = Field(..., description="Content classification")
    status: str = Field(..., description="Request status")
    search_results: Optional[List[ContentSearchResult]] = Field(
        None, description="Search results if available"
    )
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": 1,
                "correlation_id": "req_abc123",
                "query": "Add Dune Part 2 in 4K",
                "classification": {
                    "content_type": "movie",
                    "title": "Dune Part Two",
                    "year": 2024,
                    "quality": "4K",
                    "season": None,
                    "episode": None,
                    "confidence": 0.95,
                },
                "status": "submitted",
                "search_results": None,
                "created_at": "2025-01-15T10:30:00Z",
            }
        }


class RequestStatusResponse(BaseModel):
    """Response model for request status."""

    id: int = Field(..., description="Request ID")
    correlation_id: str = Field(..., description="Correlation ID")
    status: str = Field(..., description="Current status")
    external_id: Optional[str] = Field(None, description="External service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": 1,
                "correlation_id": "req_abc123",
                "status": "completed",
                "external_id": "radarr_123",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:35:00Z",
                "completed_at": "2025-01-15T10:35:00Z",
            }
        }


class RequestListResponse(BaseModel):
    """Response model for request list."""

    requests: List[RequestStatusResponse] = Field(..., description="List of requests")
    total: int = Field(..., description="Total number of requests")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "requests": [],
                "total": 0,
                "page": 1,
                "page_size": 10,
            }
        }


class ConfirmRequestInput(BaseModel):
    """Input model for confirming ambiguous request."""

    selected_result_index: int = Field(..., description="Index of selected search result", ge=0)
    quality_profile_id: Optional[int] = Field(None, description="Quality profile ID")
    root_folder: Optional[str] = Field(None, description="Root folder path")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "selected_result_index": 0,
                "quality_profile_id": 1,
                "root_folder": "/media/movies",
            }
        }


# ============================================================================
# Dependencies
# ============================================================================


async def get_request_handler() -> RequestHandler:
    """Get request handler instance."""
    # TODO: Initialize with LLM agent and web search service from dependencies
    return RequestHandler()


async def get_content_integration() -> ContentIntegrationService:
    """Get content integration service instance."""
    # TODO: Initialize with MCP orchestrator from dependencies
    from autoarr.api.dependencies import get_mcp_orchestrator

    orchestrator = get_mcp_orchestrator()
    return ContentIntegrationService(orchestrator)


async def get_request_repository() -> ContentRequestRepository:
    """Get content request repository instance."""
    db = get_database()
    return ContentRequestRepository(db)


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/content",
    response_model=ContentRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit content request",
    description="Submit a natural language request for movie or TV show content",
)
@limiter.limit("10/minute")
async def submit_content_request(
    request_input: ContentRequestInput,
    handler: RequestHandler = Depends(get_request_handler),
    repository: ContentRequestRepository = Depends(get_request_repository),
) -> ContentRequestResponse:
    """
    Submit a content request.

    This endpoint:
    1. Classifies the request (movie vs TV)
    2. Extracts metadata (title, year, quality, etc.)
    3. Stores the request in the database
    4. Returns the classification for user review

    Rate limit: 10 requests per minute per IP
    """
    try:
        # Classify the request
        classification = await handler.classify_content(request_input.query)

        # Generate unique correlation ID
        correlation_id = f"req_{uuid.uuid4().hex[:12]}"

        # Store in database
        db_request = await repository.create(
            correlation_id=correlation_id,
            query=request_input.query,
            content_type=classification.content_type,
            title=classification.title,
            status="submitted",
            user_id=request_input.user_id,
            year=classification.year,
            quality=classification.quality,
            season=classification.season,
            episode=classification.episode,
        )

        # Return response
        return ContentRequestResponse(
            id=db_request.id,
            correlation_id=db_request.correlation_id,
            query=db_request.query,
            classification=classification,
            status=db_request.status,
            search_results=None,
            created_at=db_request.created_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}",
        )


@router.get(
    "/{request_id}/status",
    response_model=RequestStatusResponse,
    summary="Get request status",
    description="Get the current status of a content request",
)
async def get_request_status(
    request_id: int,
    repository: ContentRequestRepository = Depends(get_request_repository),
) -> RequestStatusResponse:
    """
    Get request status.

    Returns the current status of a content request including:
    - Current status (submitted, searching, downloading, completed, failed)
    - External service ID (Radarr/Sonarr)
    - Timestamps
    """
    db_request = await repository.get_by_id(request_id)

    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found",
        )

    return RequestStatusResponse(
        id=db_request.id,
        correlation_id=db_request.correlation_id,
        status=db_request.status,
        external_id=db_request.external_id,
        created_at=db_request.created_at,
        updated_at=db_request.updated_at,
        completed_at=db_request.completed_at,
    )


@router.get(
    "",
    response_model=RequestListResponse,
    summary="List content requests",
    description="Get a paginated list of content requests with optional filters",
)
async def list_requests(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    content_type: Optional[Literal["movie", "tv"]] = Query(
        None, description="Filter by content type"
    ),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    repository: ContentRequestRepository = Depends(get_request_repository),
) -> RequestListResponse:
    """
    List content requests.

    Returns a paginated list of content requests with optional filters:
    - Filter by user_id
    - Filter by content_type (movie/tv)
    - Filter by status
    - Pagination support
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get requests
        requests = await repository.get_all(
            user_id=user_id,
            content_type=content_type,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )

        # Get total count
        total = await repository.count(
            user_id=user_id,
            content_type=content_type,
            status=status_filter,
        )

        # Convert to response models
        request_responses = [
            RequestStatusResponse(
                id=req.id,
                correlation_id=req.correlation_id,
                status=req.status,
                external_id=req.external_id,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in requests
        ]

        return RequestListResponse(
            requests=request_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list requests: {str(e)}",
        )


@router.post(
    "/{request_id}/confirm",
    response_model=RequestStatusResponse,
    summary="Confirm and execute request",
    description="Confirm an ambiguous request and add content to Radarr/Sonarr",
)
async def confirm_request(
    request_id: int,
    confirm_input: ConfirmRequestInput,
    repository: ContentRequestRepository = Depends(get_request_repository),
    integration: ContentIntegrationService = Depends(get_content_integration),
) -> RequestStatusResponse:
    """
    Confirm and execute request.

    This endpoint:
    1. Retrieves the request from database
    2. Adds content to Radarr (movies) or Sonarr (TV shows)
    3. Updates request status
    4. Returns updated status
    """
    try:
        # Get request from database
        db_request = await repository.get_by_id(request_id)

        if not db_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found",
            )

        # Check if already processed
        if db_request.status not in ["submitted", "searching"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request already {db_request.status}",
            )

        # Add to appropriate service
        if db_request.content_type == "movie":
            if not db_request.tmdb_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TMDB ID required for movie",
                )

            result = await integration.add_movie_to_radarr(  # noqa: F841
                tmdb_id=db_request.tmdb_id,
                quality_profile_id=confirm_input.quality_profile_id or 1,
                root_folder=confirm_input.root_folder or "/movies",
                monitored=True,
                search_now=True,
                title=db_request.title,
                year=db_request.year,
            )

            external_id = f"radarr_{result.get('id')}"

        else:  # TV show
            if not db_request.tmdb_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TVDB ID required for TV show",
                )

            result = await integration.add_series_to_sonarr(  # noqa: F841
                tvdb_id=db_request.tmdb_id,  # TODO: Convert TMDB to TVDB
                quality_profile_id=confirm_input.quality_profile_id or 1,
                root_folder=confirm_input.root_folder or "/tv",
                monitored=True,
                search_now=True,
                title=db_request.title,
                season=db_request.season,
            )

            external_id = f"sonarr_{result.get('id')}"

        # Update status
        updated_request = await repository.update_status(
            request_id=request_id,
            status="searching",
            external_id=external_id,
        )

        return RequestStatusResponse(
            id=updated_request.id,
            correlation_id=updated_request.correlation_id,
            status=updated_request.status,
            external_id=updated_request.external_id,
            created_at=updated_request.created_at,
            updated_at=updated_request.updated_at,
            completed_at=updated_request.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm request: {str(e)}",
        )


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel request",
    description="Cancel a pending content request",
)
async def cancel_request(
    request_id: int,
    repository: ContentRequestRepository = Depends(get_request_repository),
) -> None:
    """
    Cancel request.

    Deletes a pending content request from the database.
    Note: This does not remove content already added to Radarr/Sonarr.
    """
    try:
        db_request = await repository.get_by_id(request_id)

        if not db_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found",
            )

        # Only allow cancellation of pending requests
        if db_request.status in ["completed", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel {db_request.status} request",
            )

        # Delete request
        deleted = await repository.delete(request_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete request",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel request: {str(e)}",
        )
