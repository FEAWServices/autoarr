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
Configuration settings for the FastAPI Gateway.

This module defines all configuration settings using Pydantic Settings,
loading values from environment variables and .env files.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ============================================================================
    # Server Settings
    # ============================================================================

    host: str = "0.0.0.0"
    port: int = 8088
    reload: bool = False
    workers: int = 1

    # ============================================================================
    # Application Settings
    # ============================================================================

    app_name: str = "AutoArr API"
    app_version: str = "1.0.0"
    app_description: str = "Intelligent media automation orchestrator"
    app_env: str = "development"
    log_level: str = "INFO"

    # ============================================================================
    # Security Settings
    # ============================================================================

    secret_key: str = "dev_secret_key_change_in_production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # ============================================================================
    # SABnzbd Settings
    # ============================================================================

    sabnzbd_url: str = "http://localhost:8080"
    sabnzbd_api_key: str = ""
    sabnzbd_enabled: bool = True
    sabnzbd_timeout: float = 30.0

    # ============================================================================
    # Sonarr Settings
    # ============================================================================

    sonarr_url: str = "http://localhost:8989"
    sonarr_api_key: str = ""
    sonarr_enabled: bool = True
    sonarr_timeout: float = 30.0

    # ============================================================================
    # Radarr Settings
    # ============================================================================

    radarr_url: str = "http://localhost:7878"
    radarr_api_key: str = ""
    radarr_enabled: bool = True
    radarr_timeout: float = 30.0

    # ============================================================================
    # Plex Settings
    # ============================================================================

    plex_url: str = "http://localhost:32400"
    plex_token: str = ""
    plex_enabled: bool = True
    plex_timeout: float = 30.0

    # ============================================================================
    # Database Settings (for future use)
    # ============================================================================

    database_url: Optional[str] = None

    # ============================================================================
    # Redis Settings (for future use)
    # ============================================================================

    redis_url: Optional[str] = None

    # ============================================================================
    # MCP Orchestrator Settings
    # ============================================================================

    max_concurrent_requests: int = 10
    default_tool_timeout: float = 30.0
    max_retries: int = 3
    auto_reconnect: bool = True
    keepalive_interval: float = 30.0
    health_check_interval: int = 60
    health_check_failure_threshold: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    circuit_breaker_success_threshold: int = 3
    max_parallel_calls: int = 10
    parallel_timeout: Optional[float] = None

    # ============================================================================
    # API Settings
    # ============================================================================

    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # Model configuration
    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Validate security settings for production environment."""
        if self.app_env == "production":
            if self.secret_key == "dev_secret_key_change_in_production":
                raise ValueError(
                    "SECRET_KEY environment variable must be set to a secure random "
                    "value in production. Generate one using: "
                    "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
