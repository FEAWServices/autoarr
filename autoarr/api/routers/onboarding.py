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
Onboarding API endpoints for managing the setup wizard.

This module provides endpoints for tracking onboarding progress,
updating steps, and managing the premium waitlist.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator

from ..database import OnboardingStateRepository, PremiumWaitlistRepository, get_database

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


async def get_onboarding_repo() -> OnboardingStateRepository:
    """Get onboarding state repository dependency."""
    try:
        db = get_database()
        return OnboardingStateRepository(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Onboarding state persistence disabled.",
        )


async def get_waitlist_repo() -> PremiumWaitlistRepository:
    """Get premium waitlist repository dependency."""
    try:
        db = get_database()
        return PremiumWaitlistRepository(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Waitlist persistence disabled.",
        )


# ============================================================================
# Request/Response Models
# ============================================================================


class OnboardingStatusResponse(BaseModel):
    """Response containing onboarding status."""

    completed: bool = Field(..., description="Whether onboarding is complete")
    current_step: str = Field(..., description="Current step in the wizard")
    skipped_steps: List[str] = Field(default_factory=list, description="Steps that were skipped")
    ai_configured: bool = Field(..., description="Whether AI/LLM is configured")
    services_configured: List[str] = Field(
        default_factory=list, description="List of configured services"
    )
    banner_dismissed: bool = Field(..., description="Whether setup banner was dismissed")
    needs_onboarding: bool = Field(..., description="Whether user should be shown onboarding")


class UpdateStepRequest(BaseModel):
    """Request to update the current step."""

    step: str = Field(..., description="Step to set as current")

    @field_validator("step")
    @classmethod
    def validate_step(cls, v: str) -> str:
        valid_steps = ["welcome", "ai_setup", "service_selection", "service_config", "complete"]
        if v not in valid_steps:
            raise ValueError(f"Invalid step. Must be one of: {', '.join(valid_steps)}")
        return v


class SkipStepRequest(BaseModel):
    """Request to skip a step."""

    step: str = Field(..., description="Step to skip")

    @field_validator("step")
    @classmethod
    def validate_step(cls, v: str) -> str:
        valid_steps = ["welcome", "ai_setup", "service_selection", "service_config"]
        if v not in valid_steps:
            raise ValueError(f"Invalid step to skip. Must be one of: {', '.join(valid_steps)}")
        return v


class AddServiceRequest(BaseModel):
    """Request to add a configured service."""

    service: str = Field(..., description="Service name to add")

    @field_validator("service")
    @classmethod
    def validate_service(cls, v: str) -> str:
        valid_services = ["sabnzbd", "sonarr", "radarr", "plex"]
        if v.lower() not in valid_services:
            raise ValueError(f"Invalid service. Must be one of: {', '.join(valid_services)}")
        return v.lower()


class WaitlistSignupRequest(BaseModel):
    """Request to join the premium waitlist."""

    email: EmailStr = Field(..., description="Email address")
    source: Optional[str] = Field(default="onboarding", description="Signup source")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Optional[str]) -> Optional[str]:
        valid_sources = ["onboarding", "settings", "banner", "home"]
        if v and v not in valid_sources:
            return "other"
        return v


class WaitlistSignupResponse(BaseModel):
    """Response for waitlist signup."""

    success: bool
    message: str
    already_signed_up: bool = False


class WaitlistStatusResponse(BaseModel):
    """Response for checking waitlist status."""

    is_on_waitlist: bool
    email: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str


# ============================================================================
# Onboarding Endpoints
# ============================================================================


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> OnboardingStatusResponse:
    """
    Get the current onboarding status.

    Returns whether onboarding is complete, current step, and other state.
    """
    state = await repo.get_or_create_state()

    # Determine if user needs onboarding
    needs_onboarding = not state.completed and not state.banner_dismissed

    return OnboardingStatusResponse(
        completed=state.completed,
        current_step=state.current_step,
        skipped_steps=list(state.skipped_steps or []),
        ai_configured=state.ai_configured,
        services_configured=list(state.services_configured or []),
        banner_dismissed=state.banner_dismissed,
        needs_onboarding=needs_onboarding,
    )


@router.put("/step", response_model=SuccessResponse)
async def update_current_step(
    request: UpdateStepRequest,
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """
    Update the current step in the onboarding wizard.

    Valid steps: welcome, ai_setup, service_selection, service_config, complete
    """
    await repo.update_step(request.step)
    return SuccessResponse(message=f"Step updated to: {request.step}")


@router.post("/skip-step", response_model=SuccessResponse)
async def skip_step(
    request: SkipStepRequest,
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """
    Mark a step as skipped.

    The user can skip certain steps but will see a reminder banner.
    """
    await repo.skip_step(request.step)
    return SuccessResponse(message=f"Step skipped: {request.step}")


@router.post("/ai-configured", response_model=SuccessResponse)
async def mark_ai_configured(
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """Mark AI/LLM as configured."""
    await repo.set_ai_configured(True)
    return SuccessResponse(message="AI marked as configured")


@router.post("/add-service", response_model=SuccessResponse)
async def add_configured_service(
    request: AddServiceRequest,
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """Add a service to the list of configured services."""
    await repo.add_configured_service(request.service)
    return SuccessResponse(message=f"Service added: {request.service}")


@router.post("/complete", response_model=SuccessResponse)
async def complete_onboarding(
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """Mark onboarding as complete."""
    await repo.complete_onboarding()
    return SuccessResponse(message="Onboarding completed successfully")


@router.post("/skip", response_model=SuccessResponse)
async def skip_onboarding(
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """
    Skip the entire onboarding process.

    The user will see a persistent reminder banner.
    """
    await repo.skip_onboarding()
    return SuccessResponse(message="Onboarding skipped. You can restart it from Settings.")


@router.post("/dismiss-banner", response_model=SuccessResponse)
async def dismiss_banner(
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """Dismiss the setup reminder banner."""
    await repo.dismiss_banner()
    return SuccessResponse(message="Banner dismissed")


@router.post("/reset", response_model=SuccessResponse)
async def reset_onboarding(
    repo: OnboardingStateRepository = Depends(get_onboarding_repo),
) -> SuccessResponse:
    """
    Reset onboarding to initial state.

    Useful for re-running the setup wizard from Settings.
    """
    await repo.reset_onboarding()
    return SuccessResponse(message="Onboarding reset. Wizard will start from the beginning.")


# ============================================================================
# Premium Waitlist Endpoints
# ============================================================================


@router.post("/waitlist", response_model=WaitlistSignupResponse)
async def join_waitlist(
    request: WaitlistSignupRequest,
    repo: PremiumWaitlistRepository = Depends(get_waitlist_repo),
) -> WaitlistSignupResponse:
    """
    Join the premium waitlist.

    Users will be notified when AutoArr Premium becomes available.
    """
    try:
        await repo.add_email(str(request.email), request.source)
        return WaitlistSignupResponse(
            success=True,
            message="You're on the list! We'll notify you when Premium is available.",
            already_signed_up=False,
        )
    except ValueError:
        # Email already exists
        return WaitlistSignupResponse(
            success=True,
            message="You're already on the waitlist!",
            already_signed_up=True,
        )


@router.get("/waitlist/check", response_model=WaitlistStatusResponse)
async def check_waitlist_status(
    email: str,
    repo: PremiumWaitlistRepository = Depends(get_waitlist_repo),
) -> WaitlistStatusResponse:
    """Check if an email is already on the waitlist."""
    # Validate email format
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format",
        )

    is_on_waitlist = await repo.is_on_waitlist(email)
    return WaitlistStatusResponse(
        is_on_waitlist=is_on_waitlist,
        email=email if is_on_waitlist else None,
    )
