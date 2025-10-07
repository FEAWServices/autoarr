"""
Database configuration and models for settings persistence.

This module provides SQLAlchemy models and database session management
for persisting application settings.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import Boolean, Float, String, create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger(__name__)


# ============================================================================
# Base Model
# ============================================================================


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# ============================================================================
# Settings Model
# ============================================================================


class ServiceSettings(Base):
    """Database model for service connection settings."""

    __tablename__ = "service_settings"

    service_name: Mapped[str] = mapped_column(String, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    url: Mapped[str] = mapped_column(String)
    api_key_or_token: Mapped[str] = mapped_column(String)
    timeout: Mapped[float] = mapped_column(Float, default=30.0)


# ============================================================================
# Database Engine
# ============================================================================


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str):
        """
        Initialize database connection.

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url

        # Convert sqlite:// to sqlite+aiosqlite:// for async support
        if database_url.startswith("sqlite://"):
            self.database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {},
        )
        self.session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.

        Yields:
            AsyncSession: Database session
        """
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# ============================================================================
# Global Database Instance
# ============================================================================

_database: Optional[Database] = None


def init_database(database_url: str) -> Database:
    """
    Initialize the global database instance.

    Args:
        database_url: Database connection URL

    Returns:
        Database: Database instance
    """
    global _database
    _database = Database(database_url)
    return _database


def get_database() -> Database:
    """
    Get the global database instance.

    Returns:
        Database: Database instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _database


# ============================================================================
# Settings Repository
# ============================================================================


class SettingsRepository:
    """Repository for settings database operations."""

    def __init__(self, db: Database):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db

    async def get_service_settings(self, service_name: str) -> Optional[ServiceSettings]:
        """
        Get settings for a specific service.

        Args:
            service_name: Service name (sabnzbd, sonarr, radarr, plex)

        Returns:
            ServiceSettings if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ServiceSettings).where(ServiceSettings.service_name == service_name)
            )
            return result.scalar_one_or_none()

    async def get_all_service_settings(self) -> dict[str, ServiceSettings]:
        """
        Get all service settings.

        Returns:
            Dictionary mapping service names to settings
        """
        async with self.db.session() as session:
            result = await session.execute(select(ServiceSettings))
            settings = result.scalars().all()
            return {s.service_name: s for s in settings}

    async def save_service_settings(
        self,
        service_name: str,
        enabled: bool,
        url: str,
        api_key_or_token: str,
        timeout: float = 30.0,
    ) -> ServiceSettings:
        """
        Save or update service settings.

        Args:
            service_name: Service name
            enabled: Whether service is enabled
            url: Service URL
            api_key_or_token: API key or token
            timeout: Request timeout

        Returns:
            Saved ServiceSettings
        """
        async with self.db.session() as session:
            # Try to get existing settings
            result = await session.execute(
                select(ServiceSettings).where(ServiceSettings.service_name == service_name)
            )
            settings = result.scalar_one_or_none()

            if settings:
                # Update existing
                settings.enabled = enabled
                settings.url = url
                settings.api_key_or_token = api_key_or_token
                settings.timeout = timeout
            else:
                # Create new
                settings = ServiceSettings(
                    service_name=service_name,
                    enabled=enabled,
                    url=url,
                    api_key_or_token=api_key_or_token,
                    timeout=timeout,
                )
                session.add(settings)

            await session.commit()
            await session.refresh(settings)
            return settings

    async def delete_service_settings(self, service_name: str) -> bool:
        """
        Delete service settings.

        Args:
            service_name: Service name

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ServiceSettings).where(ServiceSettings.service_name == service_name)
            )
            settings = result.scalar_one_or_none()

            if settings:
                await session.delete(settings)
                await session.commit()
                return True

            return False
