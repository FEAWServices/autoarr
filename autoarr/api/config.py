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

    host: str = "0.0.0.0"  # nosec B104 - Intentional for container networking
    port: int = 8088
    reload: bool = False
    workers: int = 1

    # ============================================================================
    # Application Settings
    # ============================================================================

    app_name: str = "AutoArr API"
    app_version: str = "0.8.0"
    app_description: str = "Intelligent media automation orchestrator"
    app_env: str = "development"
    log_level: str = "INFO"

    # ============================================================================
    # Security Settings
    # ============================================================================

    secret_key: str = "dev_secret_key_change_in_production"
    # Note: These accept comma-separated strings from .env (e.g., "http://a,http://b")
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:9080"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def get_cors_methods(self) -> List[str]:
        """Get CORS methods as a list."""
        return [m.strip() for m in self.cors_allow_methods.split(",") if m.strip()]

    def get_cors_headers(self) -> List[str]:
        """Get CORS headers as a list."""
        return [h.strip() for h in self.cors_allow_headers.split(",") if h.strip()]

    # ============================================================================
    # Rate Limiting Settings
    # ============================================================================

    # Enable/disable rate limiting
    rate_limit_enabled: bool = True

    # Default rate limits (requests per minute)
    rate_limit_default: str = "100/minute"  # General endpoints
    rate_limit_health: str = "60/minute"  # Health check endpoints
    rate_limit_config_audit: str = "20/minute"  # Configuration audit (LLM-heavy)
    rate_limit_content_request: str = "20/minute"  # Content requests (LLM + search)
    rate_limit_llm: str = "10/minute"  # Direct LLM endpoints
    rate_limit_downloads: str = "100/minute"  # Download operations
    rate_limit_media: str = "100/minute"  # Media queries

    # Rate limit storage backend (memory or redis)
    rate_limit_storage: str = "memory"  # Use "redis" if redis_url is configured

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
