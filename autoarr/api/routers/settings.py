"""
Settings API endpoints for managing application configuration.

This module provides endpoints for users to view and update configuration
settings through the API/UI without needing to edit .env files.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import get_settings
from ..database import get_database, SettingsRepository
from ..dependencies import get_orchestrator

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


async def get_service_status(service_name: str, orchestrator) -> str:
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


@router.get("/", response_model=AllServicesConfigResponse)
async def get_all_settings(
    orchestrator=Depends(get_orchestrator), repo: SettingsRepository = Depends(get_settings_repo)
):
    """
    Get current configuration for all services.

    Returns masked API keys for security. Reads from database if available,
    falls back to environment variables.
    """
    settings = get_settings()

    # Try to get settings from database first
    db_settings = await repo.get_all_service_settings()

    # Helper to get setting (DB first, then env)
    def get_setting(service_name: str, env_enabled, env_url, env_key, env_timeout):
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
async def get_service_settings(service: str, orchestrator=Depends(get_orchestrator)):
    """
    Get configuration for a specific service.

    Args:
        service: Service name (sabnzbd, sonarr, radarr, plex)
    """
    settings = get_settings()
    service = service.lower()

    if service == "sabnzbd":
        status = await get_service_status("sabnzbd", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.sabnzbd_enabled,
            url=settings.sabnzbd_url,
            api_key_masked=mask_api_key(settings.sabnzbd_api_key),
            timeout=settings.sabnzbd_timeout,
            status=status,
        )
    elif service == "sonarr":
        status = await get_service_status("sonarr", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.sonarr_enabled,
            url=settings.sonarr_url,
            api_key_masked=mask_api_key(settings.sonarr_api_key),
            timeout=settings.sonarr_timeout,
            status=status,
        )
    elif service == "radarr":
        status = await get_service_status("radarr", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.radarr_enabled,
            url=settings.radarr_url,
            api_key_masked=mask_api_key(settings.radarr_api_key),
            timeout=settings.radarr_timeout,
            status=status,
        )
    elif service == "plex":
        status = await get_service_status("plex", orchestrator)
        return ServiceConnectionConfigResponse(
            enabled=settings.plex_enabled,
            url=settings.plex_url,
            api_key_masked=mask_api_key(settings.plex_token),
            timeout=settings.plex_timeout,
            status=status,
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
    orchestrator=Depends(get_orchestrator),
    repo: SettingsRepository = Depends(get_settings_repo),
):
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
            await orchestrator.reconnect_server(service)
            logger.info(f"Successfully reconnected to {service}")
        else:
            logger.info(f"Service {service} disabled")
    except Exception as e:
        logger.error(f"Failed to reconnect to {service}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Settings saved but failed to connect: {str(e)}",
        )

    return {
        "success": True,
        "message": f"Successfully updated and saved {service} configuration",
        "service": service,
    }


@router.post("/test/{service}", response_model=TestConnectionResponse)
async def test_service_connection(service: str, request: TestConnectionRequest):
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
                    message=f"Successfully connected to SABnzbd",
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
                    message=f"Successfully connected to Sonarr",
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
                    message=f"Successfully connected to Radarr",
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
                    message=f"Successfully connected to Plex",
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
    orchestrator=Depends(get_orchestrator),
    repo: SettingsRepository = Depends(get_settings_repo),
):
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
                await orchestrator.reconnect_server(service_name)
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
async def save_settings_to_env():
    """
    Save current in-memory settings to .env file.

    WARNING: This will overwrite the .env file with current settings.
    """
    settings = get_settings()

    try:
        env_content = f"""# AutoArr Configuration
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
