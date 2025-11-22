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
Settings API endpoints for managing application configuration.

This module provides endpoints for users to view and update configuration
settings through the API/UI without needing to edit .env files.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import get_settings
from ..database import SettingsRepository, get_database
from ..dependencies import get_orchestrator

if TYPE_CHECKING:
    from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependencies
# ============================================================================


async def get_settings_repo() -> SettingsRepository:
    """Get settings repository dependency."""
    try:
        db = get_database()
        return SettingsRepository(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Settings persistence disabled.",
        )


# ============================================================================
# Request/Response Models
# ============================================================================


class ServiceConnectionConfig(BaseModel):
    """Configuration for a single service connection."""

    enabled: bool = Field(default=True, description="Whether this service is enabled")
    url: str = Field(..., description="Service URL (e.g., http://localhost:8080)")
    api_key_or_token: str = Field(..., description="API key or authentication token", min_length=1)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0, description="Request timeout in seconds")


class ServiceConnectionConfigResponse(BaseModel):
    """Configuration response (hides sensitive data)."""

    enabled: bool
    url: str
    api_key_masked: str = Field(..., description="Masked API key for security")
    timeout: float
    status: str = Field(..., description="Connection status: connected, disconnected, error")
    last_check: Optional[str] = None


class AllServicesConfig(BaseModel):
    """Configuration for all services."""

    sabnzbd: Optional[ServiceConnectionConfig] = None
    sonarr: Optional[ServiceConnectionConfig] = None
    radarr: Optional[ServiceConnectionConfig] = None
    plex: Optional[ServiceConnectionConfig] = None


class AllServicesConfigResponse(BaseModel):
    """Response with all service configurations."""

    sabnzbd: Optional[ServiceConnectionConfigResponse] = None
    sonarr: Optional[ServiceConnectionConfigResponse] = None
    radarr: Optional[ServiceConnectionConfigResponse] = None
    plex: Optional[ServiceConnectionConfigResponse] = None


class TestConnectionRequest(BaseModel):
    """Request to test a service connection."""

    url: str
    api_key_or_token: str
    timeout: float = 30.0


class TestConnectionResponse(BaseModel):
    """Response from connection test."""

    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Helper Functions
# ============================================================================


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key for display.

    Args:
        api_key: The API key to mask

    Returns:
        Masked version showing only first/last 4 chars
    """
    if not api_key or len(api_key) < 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"


async def get_service_status(service_name: str, orchestrator: "MCPOrchestrator") -> str:
    """
    Get the current status of a service.

    Args:
        service_name: Name of the service
        orchestrator: MCP Orchestrator instance

    Returns:
        Status string: "connected", "disconnected", "error"
    """
    try:
        health = await orchestrator.health_check_all()
        service_health = health.get(service_name)

        if not service_health:
            return "disconnected"

        return "connected" if service_health.healthy else "error"
    except Exception as e:
        logger.error(f"Error checking {service_name} status: {e}")
        return "error"


# ============================================================================
# GET Endpoints
# ============================================================================


@router.get("", response_model=AllServicesConfigResponse)
@router.get("/", response_model=AllServicesConfigResponse)
async def get_all_settings(
    orchestrator: "MCPOrchestrator" = Depends(get_orchestrator),
    repo: SettingsRepository = Depends(get_settings_repo),
) -> AllServicesConfigResponse:
    """
    Get current configuration for all services.

    Returns masked API keys for security. Reads from database if available,
    falls back to environment variables.
    """
    settings = get_settings()

    # Try to get settings from database first
    db_settings = await repo.get_all_service_settings()

    # Helper to get setting (DB first, then env)
    def get_setting(
        service_name: str, env_enabled: bool, env_url: str, env_key: str, env_timeout: float
    ) -> tuple[bool, str, str, float]:
        db = db_settings.get(service_name)
        if db:
            return db.enabled, db.url, db.api_key_or_token, db.timeout
        return env_enabled, env_url, env_key, env_timeout

    # Get settings for each service
    sabn_enabled, sabn_url, sabn_key, sabn_timeout = get_setting(
        "sabnzbd",
        settings.sabnzbd_enabled,
        settings.sabnzbd_url,
        settings.sabnzbd_api_key,
        settings.sabnzbd_timeout,
    )
    son_enabled, son_url, son_key, son_timeout = get_setting(
        "sonarr",
        settings.sonarr_enabled,
        settings.sonarr_url,
        settings.sonarr_api_key,
        settings.sonarr_timeout,
    )
    rad_enabled, rad_url, rad_key, rad_timeout = get_setting(
        "radarr",
        settings.radarr_enabled,
        settings.radarr_url,
        settings.radarr_api_key,
        settings.radarr_timeout,
    )
    plex_enabled, plex_url, plex_key, plex_timeout = get_setting(
        "plex", settings.plex_enabled, settings.plex_url, settings.plex_token, settings.plex_timeout
    )

    # Get current connection statuses
    sabnzbd_status = await get_service_status("sabnzbd", orchestrator)
    sonarr_status = await get_service_status("sonarr", orchestrator)
    radarr_status = await get_service_status("radarr", orchestrator)
    plex_status = await get_service_status("plex", orchestrator)

    return AllServicesConfigResponse(
        sabnzbd=(
            ServiceConnectionConfigResponse(
                enabled=sabn_enabled,
                url=sabn_url,
                api_key_masked=mask_api_key(sabn_key),
                timeout=sabn_timeout,
                status=sabnzbd_status,
            )
            if sabn_enabled
            else None
        ),
        sonarr=(
            ServiceConnectionConfigResponse(
                enabled=son_enabled,
                url=son_url,
                api_key_masked=mask_api_key(son_key),
                timeout=son_timeout,
                status=sonarr_status,
            )
            if son_enabled
            else None
        ),
        radarr=(
            ServiceConnectionConfigResponse(
                enabled=rad_enabled,
                url=rad_url,
                api_key_masked=mask_api_key(rad_key),
                timeout=rad_timeout,
                status=radarr_status,
            )
            if rad_enabled
            else None
        ),
        plex=(
            ServiceConnectionConfigResponse(
                enabled=plex_enabled,
                url=plex_url,
                api_key_masked=mask_api_key(plex_key),
                timeout=plex_timeout,
                status=plex_status,
            )
            if plex_enabled
            else None
        ),
    )


@router.get("/{service}", response_model=ServiceConnectionConfigResponse)
async def get_service_settings(
    service: str, orchestrator: "MCPOrchestrator" = Depends(get_orchestrator)
) -> ServiceConnectionConfigResponse:
    """
    Get configuration for a specific service.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, plex)
    """
    settings = get_settings()
    service = service.lower()

    if service == "sabnzbd":
        service_status = await get_service_status("sabnzbd", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.sabnzbd_enabled,
            url=settings.sabnzbd_url,
            api_key_masked=mask_api_key(settings.sabnzbd_api_key),
            timeout=settings.sabnzbd_timeout,
            status=service_status,
        )
    elif service == "sonarr":
        service_status = await get_service_status("sonarr", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.sonarr_enabled,
            url=settings.sonarr_url,
            api_key_masked=mask_api_key(settings.sonarr_api_key),
            timeout=settings.sonarr_timeout,
            status=service_status,
        )
    elif service == "radarr":
        service_status = await get_service_status("radarr", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.radarr_enabled,
            url=settings.radarr_url,
            api_key_masked=mask_api_key(settings.radarr_api_key),
            timeout=settings.radarr_timeout,
            status=service_status,
        )
    elif service == "plex":
        service_status = await get_service_status("plex", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.plex_enabled,
            url=settings.plex_url,
            api_key_masked=mask_api_key(settings.plex_token),
            timeout=settings.plex_timeout,
            status=service_status,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not found. Valid services: sabnzbd, sonarr, radarr, plex",
        )


# ============================================================================
# PUT/POST Endpoints
# ============================================================================


@router.put("/{service}")
async def update_service_settings(
    service: str,
    config: ServiceConnectionConfig,
    orchestrator: "MCPOrchestrator" = Depends(get_orchestrator),
    repo: SettingsRepository = Depends(get_settings_repo),
) -> Dict[str, Any]:
    """
    Update configuration for a specific service.

    This endpoint updates the service configuration in the database and attempts to reconnect.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, plex)
        config: New configuration
    """
    service = service.lower()

    # Validate service name
    if service not in ["sabnzbd", "sonarr", "radarr", "plex"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not found. Valid services: sabnzbd, sonarr, radarr, plex",
        )

    # Save settings to database
    try:
        await repo.save_service_settings(
            service_name=service,
            enabled=config.enabled,
            url=config.url,
            api_key_or_token=config.api_key_or_token,
            timeout=config.timeout,
        )
        logger.info(f"Saved {service} settings to database")
    except Exception as e:
        logger.error(f"Failed to save {service} settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}",
        )

    # Update in-memory settings for immediate effect
    settings = get_settings()
    if service == "sabnzbd":
        settings.sabnzbd_enabled = config.enabled
        settings.sabnzbd_url = config.url
        settings.sabnzbd_api_key = config.api_key_or_token
        settings.sabnzbd_timeout = config.timeout
    elif service == "sonarr":
        settings.sonarr_enabled = config.enabled
        settings.sonarr_url = config.url
        settings.sonarr_api_key = config.api_key_or_token
        settings.sonarr_timeout = config.timeout
    elif service == "radarr":
        settings.radarr_enabled = config.enabled
        settings.radarr_url = config.url
        settings.radarr_api_key = config.api_key_or_token
        settings.radarr_timeout = config.timeout
    elif service == "plex":
        settings.plex_enabled = config.enabled
        settings.plex_url = config.url
        settings.plex_token = config.api_key_or_token
        settings.plex_timeout = config.timeout

    # Attempt to reconnect to the service
    try:
        if config.enabled:
            await orchestrator.reconnect(service)
            logger.info(f"Successfully reconnected to {service}")
        else:
            logger.info(f"Service {service} disabled")
    except Exception as e:
        logger.error(f"Failed to reconnect to {service}: {e}")
        # Don't fail the save if reconnect fails - settings are already saved
        logger.warning(f"Settings saved but reconnect failed: {str(e)}")

    return {
        "success": True,
        "message": f"Successfully updated and saved {service} configuration",
        "service": service,
    }


@router.post("/test/{service}", response_model=TestConnectionResponse)
async def test_service_connection(
    service: str, request: TestConnectionRequest
) -> TestConnectionResponse:
    """
    Test connection to a service without saving settings.

    Useful for validating credentials before saving.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, plex)
        request: Connection details to test
    """
    service = service.lower()

    try:
        # Import the appropriate client
        if service == "sabnzbd":
            from sabnzbd.client import SABnzbdClient

            async with await SABnzbdClient.create(
                url=request.url,
                api_key=request.api_key_or_token,
                timeout=request.timeout,
                validate_connection=True,
            ) as client:
                version = await client.get_version()
                return TestConnectionResponse(
                    success=True,
                    message="Successfully connected to SABnzbd",
                    details={"version": version.get("version", "unknown")},
                )

        elif service == "sonarr":
            from sonarr.client import SonarrClient

            async with await SonarrClient.create(
                url=request.url,
                api_key=request.api_key_or_token,
                timeout=request.timeout,
                validate_connection=True,
            ) as client:
                status_info = await client.get_system_status()
                return TestConnectionResponse(
                    success=True,
                    message="Successfully connected to Sonarr",
                    details={"version": status_info.get("version", "unknown")},
                )

        elif service == "radarr":
            from radarr.client import RadarrClient

            async with await RadarrClient.create(
                url=request.url,
                api_key=request.api_key_or_token,
                timeout=request.timeout,
                validate_connection=True,
            ) as client:
                status_info = await client.get_system_status()
                return TestConnectionResponse(
                    success=True,
                    message="Successfully connected to Radarr",
                    details={"version": status_info.get("version", "unknown")},
                )

        elif service == "plex":
            from plex.client import PlexClient

            async with await PlexClient.create(
                url=request.url,
                token=request.api_key_or_token,
                timeout=request.timeout,
                validate_connection=True,
            ) as client:
                identity = await client.get_server_identity()
                return TestConnectionResponse(
                    success=True,
                    message="Successfully connected to Plex",
                    details={
                        "version": identity.get("version", "unknown"),
                        "platform": identity.get("platform", "unknown"),
                    },
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service}' not found",
            )

    except Exception as e:
        logger.error(f"Connection test failed for {service}: {e}")
        return TestConnectionResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
            details={"error": str(e)},
        )


@router.post("/")
async def save_all_settings(
    config: AllServicesConfig,
    orchestrator: "MCPOrchestrator" = Depends(get_orchestrator),
    repo: SettingsRepository = Depends(get_settings_repo),
) -> Dict[str, Any]:
    """
    Save configuration for all services at once.

    This endpoint updates all service configurations in the database and in memory.

    Args:
        config: Configuration for all services
    """
    settings = get_settings()
    save_errors = []

    # Save each service configuration to database
    for service_name, service_config in [
        ("sabnzbd", config.sabnzbd),
        ("sonarr", config.sonarr),
        ("radarr", config.radarr),
        ("plex", config.plex),
    ]:
        if service_config:
            try:
                await repo.save_service_settings(
                    service_name=service_name,
                    enabled=service_config.enabled,
                    url=service_config.url,
                    api_key_or_token=service_config.api_key_or_token,
                    timeout=service_config.timeout,
                )
                logger.info(f"Saved {service_name} settings to database")
            except Exception as e:
                logger.error(f"Failed to save {service_name} settings: {e}")
                save_errors.append(f"{service_name}: {str(e)}")

    # Update in-memory settings for immediate effect
    if config.sabnzbd:
        settings.sabnzbd_enabled = config.sabnzbd.enabled
        settings.sabnzbd_url = config.sabnzbd.url
        settings.sabnzbd_api_key = config.sabnzbd.api_key_or_token
        settings.sabnzbd_timeout = config.sabnzbd.timeout

    if config.sonarr:
        settings.sonarr_enabled = config.sonarr.enabled
        settings.sonarr_url = config.sonarr.url
        settings.sonarr_api_key = config.sonarr.api_key_or_token
        settings.sonarr_timeout = config.sonarr.timeout

    if config.radarr:
        settings.radarr_enabled = config.radarr.enabled
        settings.radarr_url = config.radarr.url
        settings.radarr_api_key = config.radarr.api_key_or_token
        settings.radarr_timeout = config.radarr.timeout

    if config.plex:
        settings.plex_enabled = config.plex.enabled
        settings.plex_url = config.plex.url
        settings.plex_token = config.plex.api_key_or_token
        settings.plex_timeout = config.plex.timeout

    # Reconnect to enabled services
    reconnect_errors = []
    for service_name, service_config in [
        ("sabnzbd", config.sabnzbd),
        ("sonarr", config.sonarr),
        ("radarr", config.radarr),
        ("plex", config.plex),
    ]:
        if service_config and service_config.enabled:
            try:
                await orchestrator.reconnect(service_name)
                logger.info(f"Successfully reconnected to {service_name}")
            except Exception as e:
                logger.error(f"Failed to reconnect to {service_name}: {e}")
                reconnect_errors.append(f"{service_name}: {str(e)}")

    if save_errors or reconnect_errors:
        return {
            "success": False,
            "message": "Some operations failed",
            "save_errors": save_errors,
            "reconnect_errors": reconnect_errors,
        }

    return {
        "success": True,
        "message": "All settings saved and applied successfully",
    }


@router.post("/save-to-env")
async def save_settings_to_env() -> Dict[str, Any]:
    """
    Save current in-memory settings to .env file.

    WARNING: This will overwrite the .env file with current settings.
    """
    settings = get_settings()  # noqa: F841

    try:
        env_content = """# AutoArr Configuration
# Generated by Settings API

# SABnzbd Configuration
SABNZBD_URL={settings.sabnzbd_url}
SABNZBD_API_KEY={settings.sabnzbd_api_key}
SABNZBD_ENABLED={str(settings.sabnzbd_enabled).lower()}
SABNZBD_TIMEOUT={settings.sabnzbd_timeout}

# Sonarr Configuration
SONARR_URL={settings.sonarr_url}
SONARR_API_KEY={settings.sonarr_api_key}
SONARR_ENABLED={str(settings.sonarr_enabled).lower()}
SONARR_TIMEOUT={settings.sonarr_timeout}

# Radarr Configuration
RADARR_URL={settings.radarr_url}
RADARR_API_KEY={settings.radarr_api_key}
RADARR_ENABLED={str(settings.radarr_enabled).lower()}
RADARR_TIMEOUT={settings.radarr_timeout}

# Plex Configuration
PLEX_URL={settings.plex_url}
PLEX_TOKEN={settings.plex_token}
PLEX_ENABLED={str(settings.plex_enabled).lower()}
PLEX_TIMEOUT={settings.plex_timeout}

# Application Configuration
APP_ENV={settings.app_env}
LOG_LEVEL={settings.log_level}
SECRET_KEY={settings.secret_key}
"""

        # Write to .env file
        with open(".env", "w") as f:
            f.write(env_content)

        logger.info("Settings saved to .env file")
        return {
            "success": True,
            "message": "Settings saved to .env file successfully",
        }

    except Exception as e:
        logger.error(f"Failed to save settings to .env: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}",
        )


# ============================================================================
# SERVICE DISCOVERY ENDPOINT
# ============================================================================


class DiscoveredService(BaseModel):
    """Auto-discovered service."""

    type: str
    url: str
    name: str


@router.get("/discover", response_model=list[DiscoveredService])
async def discover_services() -> list[DiscoveredService]:
    """
    Auto-discover services on the local network.

    Scans common ports for SABnzbd, Sonarr, Radarr, and Plex.

    Returns:
        List of discovered services
    """
    import asyncio

    import httpx

    discovered = []

    # Common ports to scan
    scan_targets = [
        ("sabnzbd", 8080),
        ("sabnzbd", 9090),
        ("sonarr", 8989),
        ("radarr", 7878),
        ("plex", 32400),
    ]

    async def check_service(service_type: str, port: int):
        """Check if a service is running on localhost:port."""
        url = f"http://localhost:{port}"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Try to access the service
                if service_type in ["sonarr", "radarr"]:
                    response = await client.get(f"{url}/api/v3/system/status")
                elif service_type == "plex":
                    response = await client.get(f"{url}/web")
                else:  # sabnzbd
                    response = await client.get(f"{url}/api?mode=version")

                if response.status_code in [200, 401, 403]:
                    # Service is responding (even if authentication required)
                    discovered.append(
                        DiscoveredService(
                            type=service_type,
                            url=url,
                            name=f"{service_type.title()} ({port})",
                        )
                    )
        except Exception:
            pass  # Service not found on this port

    # Scan all targets concurrently
    await asyncio.gather(*[check_service(stype, port) for stype, port in scan_targets])

    return discovered


# ============================================================================
# LICENSE MANAGEMENT ENDPOINTS (Premium)
# ============================================================================


class LicenseActivateRequest(BaseModel):
    """Request to activate a license."""

    license_key: str = Field(..., pattern="^AUTOARR-[A-Z0-9]{5}(-[A-Z0-9]{5}){4}$")


class LicenseActivateResponse(BaseModel):
    """License activation response."""

    valid: bool
    error: Optional[str] = None
    license: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None


@router.get("/license/current")
async def get_current_license() -> Dict[str, Any]:
    """
    Get the current active license.

    Returns:
        Current license and validation status
    """
    try:
        from pathlib import Path

        # Load license from file
        license_path = Path("data/license.json")

        if not license_path.exists():
            return {"license": None, "validation": None}

        import json

        with open(license_path) as f:
            license_data = json.load(f)

        # TODO: Implement actual license validation using validator from autoarr-paid
        validation_result = {
            "valid": True,
            "validation_type": "offline",
            "validated_at": datetime.utcnow().isoformat(),
            "days_until_expiry": 30,
        }

        return {"license": license_data, "validation": validation_result}

    except Exception as e:
        logger.error(f"Failed to get current license: {e}")
        return {"license": None, "validation": None}


@router.post("/license/activate", response_model=LicenseActivateResponse)
async def activate_license(
    request: LicenseActivateRequest,
) -> LicenseActivateResponse:
    """
    Activate a license key.

    Args:
        request: License activation request

    Returns:
        License activation result
    """
    try:
        from pathlib import Path

        # TODO: Implement actual license validation via license server
        # For now, return a mock response
        # Validate license format
        if not request.license_key.startswith("AUTOARR-"):
            return LicenseActivateResponse(valid=False, error="Invalid license key format")

        # Mock license data
        license_data = {
            "license_key": request.license_key,
            "tier": "professional",
            "customer_id": "customer_123",
            "customer_email": "user@example.com",
            "issued_at": "2025-01-01T00:00:00Z",
            "expires_at": "2026-01-01T00:00:00Z",
            "features": {
                "autonomous_recovery": True,
                "enhanced_monitoring": True,
                "custom_model": True,
                "priority_support": True,
                "advanced_analytics": True,
                "multi_instance": False,
                "max_concurrent_downloads": 50,
                "max_monitored_items": 1000,
            },
            "grace_period_days": 7,
        }

        validation_result = {
            "valid": True,
            "validation_type": "online",
            "validated_at": datetime.utcnow().isoformat(),
            "days_until_expiry": 365,
        }

        # Save license to file
        license_path = Path("data/license.json")
        license_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(license_path, "w") as f:
            json.dump(license_data, f, indent=2)

        return LicenseActivateResponse(
            valid=True, license=license_data, validation=validation_result
        )

    except Exception as e:
        logger.error(f"License activation failed: {e}")
        return LicenseActivateResponse(valid=False, error=str(e))


@router.post("/license/deactivate")
async def deactivate_license() -> Dict[str, str]:
    """
    Deactivate the current license.

    Returns:
        Confirmation message
    """
    try:
        from pathlib import Path

        license_path = Path("data/license.json")

        if license_path.exists():
            license_path.unlink()

        return {"message": "License deactivated successfully"}

    except Exception as e:
        logger.error(f"License deactivation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate license: {str(e)}",
        )


# ============================================================================
# PREMIUM CONFIGURATION ENDPOINTS
# ============================================================================


class PremiumConfigResponse(BaseModel):
    """Premium configuration."""

    recovery: Dict[str, Any]
    monitoring: Dict[str, Any]
    analytics: Dict[str, Any]


@router.get("/premium/config", response_model=PremiumConfigResponse)
async def get_premium_config() -> PremiumConfigResponse:
    """
    Get premium feature configuration.

    Returns:
        Current premium configuration
    """
    try:
        from pathlib import Path

        config_path = Path("data/premium_config.json")

        if not config_path.exists():
            # Return default config
            return PremiumConfigResponse(
                recovery={
                    "enabled": False,
                    "max_retry_attempts": 3,
                    "retry_strategies": ["immediate", "exponential_backoff"],
                    "quality_cascade_enabled": False,
                    "quality_cascade_order": ["1080p", "720p"],
                    "alternative_search_enabled": False,
                    "indexer_failover_enabled": False,
                    "predictive_failure_detection": False,
                },
                monitoring={
                    "enabled": False,
                    "health_check_interval": 300,
                    "pattern_detection_enabled": False,
                    "predictive_analysis_enabled": False,
                    "notification_threshold": "high",
                    "detailed_metrics_enabled": False,
                },
                analytics={
                    "enabled": False,
                    "retention_days": 30,
                    "success_rate_tracking": False,
                    "performance_metrics": False,
                    "trend_analysis": False,
                },
            )

        import json

        with open(config_path) as f:
            config = json.load(f)

        return PremiumConfigResponse(**config)

    except Exception as e:
        logger.error(f"Failed to get premium config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get premium config: {str(e)}",
        )


@router.put("/premium/config", response_model=PremiumConfigResponse)
async def update_premium_config(config: PremiumConfigResponse) -> PremiumConfigResponse:
    """
    Update premium feature configuration.

    Args:
        config: New premium configuration

    Returns:
        Updated configuration
    """
    try:
        from pathlib import Path

        config_path = Path("data/premium_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(config_path, "w") as f:
            json.dump(config.dict(), f, indent=2)

        logger.info("Premium configuration updated")

        return config

    except Exception as e:
        logger.error(f"Failed to update premium config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update premium config: {str(e)}",
        )
