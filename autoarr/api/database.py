"""
Database configuration and models for settings persistence.

This module provides SQLAlchemy models and database session management
for persisting application settings, best practices, and audit results.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine, select
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
# Best Practices Model
# ============================================================================


class BestPractice(Base):
    """
    Database model for best practice recommendations.

    Stores configuration best practices for SABnzbd, Sonarr, Radarr, and Plex.
    Each practice includes the setting details, recommended values, validation logic,
    and metadata about why the practice is important.
    """

    __tablename__ = "best_practices"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Application and categorization
    application: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Setting identification
    setting_name: Mapped[str] = mapped_column(String(200), nullable=False)
    setting_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Recommended configuration
    recommended_value: Mapped[str] = mapped_column(Text, nullable=False)
    current_check_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Documentation and explanation
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Versioning
    version_added: Mapped[str] = mapped_column(String(50), nullable=False)
    version_updated: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ============================================================================
# Audit Results Model
# ============================================================================


class AuditResult(Base):
    """Database model for configuration audit results."""

    __tablename__ = "audit_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    total_checks: Mapped[int] = mapped_column(Integer, nullable=False)
    issues_found: Mapped[int] = mapped_column(Integer, nullable=False)
    high_priority: Mapped[int] = mapped_column(Integer, default=0)
    medium_priority: Mapped[int] = mapped_column(Integer, default=0)
    low_priority: Mapped[int] = mapped_column(Integer, default=0)
    configuration_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[str] = mapped_column(Text, nullable=False)


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


# ============================================================================
# Best Practices Repository
# ============================================================================


class BestPracticesRepository:
    """
    Repository for best practices database operations.

    Provides comprehensive CRUD operations, filtering, searching, and bulk
    operations for managing configuration best practices.
    """

    def __init__(self, db: Database):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db

    async def create(self, data: dict) -> BestPractice:
        """
        Create a new best practice.

        Args:
            data: Dictionary containing best practice fields

        Returns:
            Created BestPractice instance
        """
        async with self.db.session() as session:
            practice = BestPractice(**data)
            session.add(practice)
            await session.commit()
            await session.refresh(practice)
            return practice

    async def get_by_id(self, practice_id: int) -> Optional[BestPractice]:
        """
        Get a best practice by ID.

        Args:
            practice_id: Best practice ID

        Returns:
            BestPractice if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(BestPractice).where(BestPractice.id == practice_id)
            )
            return result.scalar_one_or_none()

    async def get_all(self, enabled_only: bool = False) -> list[BestPractice]:
        """
        Get all best practices.

        Args:
            enabled_only: If True, only return enabled practices

        Returns:
            List of BestPractice instances
        """
        async with self.db.session() as session:
            query = select(BestPractice)
            if enabled_only:
                query = query.where(BestPractice.enabled)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_by_application(
        self, application: str, enabled_only: bool = False
    ) -> list[BestPractice]:
        """
        Get best practices for a specific application.

        Args:
            application: Application name (sabnzbd, sonarr, radarr, plex)
            enabled_only: If True, only return enabled practices

        Returns:
            List of BestPractice instances
        """
        async with self.db.session() as session:
            query = select(BestPractice).where(BestPractice.application == application)
            if enabled_only:
                query = query.where(BestPractice.enabled)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_by_category(
        self, application: str, category: str, enabled_only: bool = False
    ) -> list[BestPractice]:
        """
        Get best practices for a specific application and category.

        Args:
            application: Application name
            category: Category name
            enabled_only: If True, only return enabled practices

        Returns:
            List of BestPractice instances
        """
        async with self.db.session() as session:
            query = select(BestPractice).where(
                BestPractice.application == application, BestPractice.category == category
            )
            if enabled_only:
                query = query.where(BestPractice.enabled)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_by_priority(
        self, priorities: list[str], enabled_only: bool = False
    ) -> list[BestPractice]:
        """
        Get best practices by priority levels.

        Args:
            priorities: List of priority levels (critical, high, medium, low)
            enabled_only: If True, only return enabled practices

        Returns:
            List of BestPractice instances
        """
        async with self.db.session() as session:
            query = select(BestPractice).where(BestPractice.priority.in_(priorities))
            if enabled_only:
                query = query.where(BestPractice.enabled)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def search(self, keyword: str, enabled_only: bool = False) -> list[BestPractice]:
        """
        Search best practices by keyword in name, explanation, or category.

        Args:
            keyword: Search keyword
            enabled_only: If True, only return enabled practices

        Returns:
            List of matching BestPractice instances
        """
        async with self.db.session() as session:
            search_pattern = f"%{keyword.lower()}%"
            query = select(BestPractice).where(
                (BestPractice.setting_name.ilike(search_pattern))
                | (BestPractice.explanation.ilike(search_pattern))
                | (BestPractice.category.ilike(search_pattern))
            )
            if enabled_only:
                query = query.where(BestPractice.enabled)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def filter(
        self,
        application: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> list[BestPractice]:
        """
        Filter best practices by multiple criteria.

        Args:
            application: Optional application filter
            category: Optional category filter
            priority: Optional priority filter
            enabled: Optional enabled status filter

        Returns:
            List of filtered BestPractice instances
        """
        async with self.db.session() as session:
            query = select(BestPractice)

            if application:
                query = query.where(BestPractice.application == application)
            if category:
                query = query.where(BestPractice.category == category)
            if priority:
                query = query.where(BestPractice.priority == priority)
            if enabled is not None:
                query = query.where(BestPractice.enabled == enabled)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def count(self, application: Optional[str] = None, enabled_only: bool = False) -> int:
        """
        Count best practices with optional filters.

        Args:
            application: Optional application filter
            enabled_only: If True, only count enabled practices

        Returns:
            Count of matching practices
        """
        from sqlalchemy import func

        async with self.db.session() as session:
            query = select(func.count(BestPractice.id))

            if application:
                query = query.where(BestPractice.application == application)
            if enabled_only:
                query = query.where(BestPractice.enabled)

            result = await session.execute(query)
            return result.scalar_one()

    async def update(self, practice_id: int, data: dict) -> Optional[BestPractice]:
        """
        Update an existing best practice.

        Args:
            practice_id: Best practice ID
            data: Dictionary containing fields to update

        Returns:
            Updated BestPractice if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(BestPractice).where(BestPractice.id == practice_id)
            )
            practice = result.scalar_one_or_none()

            if practice:
                for key, value in data.items():
                    if hasattr(practice, key) and value is not None:
                        setattr(practice, key, value)

                await session.commit()
                await session.refresh(practice)
                return practice

            return None

    async def delete(self, practice_id: int) -> bool:
        """
        Delete a best practice permanently.

        Args:
            practice_id: Best practice ID

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(BestPractice).where(BestPractice.id == practice_id)
            )
            practice = result.scalar_one_or_none()

            if practice:
                await session.delete(practice)
                await session.commit()
                return True

            return False

    async def soft_delete(self, practice_id: int) -> bool:
        """
        Soft delete a best practice by disabling it.

        Args:
            practice_id: Best practice ID

        Returns:
            True if disabled, False if not found
        """
        result = await self.update(practice_id, {"enabled": False})
        return result is not None

    async def bulk_create(self, practices_data: list[dict]) -> list[BestPractice]:
        """
        Create multiple best practices at once.

        Args:
            practices_data: List of dictionaries containing practice data

        Returns:
            List of created BestPractice instances
        """
        async with self.db.session() as session:
            practices = [BestPractice(**data) for data in practices_data]
            session.add_all(practices)
            await session.commit()

            # Refresh all practices to get IDs and timestamps
            for practice in practices:
                await session.refresh(practice)

            return practices

    async def bulk_delete(self, practice_ids: list[int]) -> int:
        """
        Delete multiple best practices by IDs.

        Args:
            practice_ids: List of practice IDs to delete

        Returns:
            Number of practices deleted
        """
        from sqlalchemy import delete as sql_delete

        async with self.db.session() as session:
            result = await session.execute(
                sql_delete(BestPractice).where(BestPractice.id.in_(practice_ids))
            )
            await session.commit()
            return result.rowcount

    async def get_paginated(
        self, page: int = 1, page_size: int = 10, enabled_only: bool = False
    ) -> list[BestPractice]:
        """
        Get paginated best practices.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            enabled_only: If True, only return enabled practices

        Returns:
            List of BestPractice instances for the requested page
        """
        async with self.db.session() as session:
            offset = (page - 1) * page_size
            query = select(BestPractice)

            if enabled_only:
                query = query.where(BestPractice.enabled)

            query = query.offset(offset).limit(page_size)
            result = await session.execute(query)
            return list(result.scalars().all())


# ============================================================================
# Audit Results Repository
# ============================================================================


class AuditResultsRepository:
    """Repository for audit results database operations."""

    def __init__(self, db: Database):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db

    async def save_audit_result(
        self,
        application: str,
        total_checks: int,
        issues_found: int,
        high_priority: int,
        medium_priority: int,
        low_priority: int,
        configuration_snapshot: str,
        recommendations: str,
    ) -> AuditResult:
        """
        Save an audit result.

        Args:
            application: Application name
            total_checks: Total number of checks performed
            issues_found: Number of issues found
            high_priority: Number of high priority issues
            medium_priority: Number of medium priority issues
            low_priority: Number of low priority issues
            configuration_snapshot: JSON snapshot of configuration
            recommendations: JSON array of recommendations

        Returns:
            Saved AuditResult
        """
        async with self.db.session() as session:
            result = AuditResult(
                application=application,
                total_checks=total_checks,
                issues_found=issues_found,
                high_priority=high_priority,
                medium_priority=medium_priority,
                low_priority=low_priority,
                configuration_snapshot=configuration_snapshot,
                recommendations=recommendations,
            )
            session.add(result)
            await session.commit()
            await session.refresh(result)
            return result

    async def get_audit_history(self, application: str, limit: int = 10) -> list[AuditResult]:
        """
        Get audit history for an application.

        Args:
            application: Application name
            limit: Maximum number of results

        Returns:
            List of audit results ordered by timestamp descending
        """
        async with self.db.session() as session:
            query = (
                select(AuditResult)
                .where(AuditResult.application == application)
                .order_by(AuditResult.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
