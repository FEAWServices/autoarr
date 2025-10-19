"""
Database configuration and models for settings persistence.

This module provides SQLAlchemy models and database session management
for persisting application settings, best practices, and audit results.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger(__name__)


# ============================================================================
# Base Model
# ============================================================================


class Base(DeclarativeBase):
    """Base class for all database models."""


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
# Activity Log Model
# ============================================================================


class ActivityLog(Base):
    """
    Database model for activity log entries.

    Tracks all system activities including download failures, recovery attempts,
    configuration changes, and user requests. Supports correlation IDs for
    tracking related events and comprehensive filtering by service, type, severity,
    and date range.
    """

    __tablename__ = "activity_log"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Event identification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Content
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Correlation tracking
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Optional user tracking for future multi-user support
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_activity_log_service_timestamp", "service", "timestamp"),
        Index("ix_activity_log_severity_timestamp", "severity", "timestamp"),
        Index("ix_activity_log_event_type_timestamp", "event_type", "timestamp"),
    )


# ============================================================================
# Content Request Model
# ============================================================================


class ContentRequest(Base):
    """
    Database model for content requests.

    Tracks user requests for movies and TV shows through the system,
    including classification, status, and external service IDs.
    """

    __tablename__ = "content_requests"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Request correlation
    correlation_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )

    # User query
    query: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification result
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # movie or tv
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Request status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="submitted", index=True)

    # Optional fields
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    season: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    episode: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # External IDs
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    imdb_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    tvdb_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Media info
    poster_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Service integration IDs
    sonarr_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    radarr_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Optional user tracking for future multi-user support
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_content_requests_status_created", "status", "created_at"),
        Index("ix_content_requests_type_created", "content_type", "created_at"),
    )


# ============================================================================
# Recovery Attempts Model
# ============================================================================


class RecoveryAttempt(Base):
    """
    Database model for tracking download recovery attempts.

    Stores information about each retry attempt for failed downloads,
    including the strategy used, success/failure status, and timing.
    """

    __tablename__ = "recovery_attempts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Download identification
    download_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Service that initiated the download (sonarr, radarr)
    service: Mapped[str] = mapped_column(String(50), nullable=False)

    # Retry strategy used
    strategy: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status: pending, in_progress, success, failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================================================
# Content Request Repository
# ============================================================================


class ContentRequestRepository:
    """Repository for content request database operations."""

    def __init__(self, db: "Database"):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db

    async def create(
        self,
        correlation_id: str,
        query: str,
        content_type: str,
        title: str,
        status: str = "submitted",
        user_id: Optional[str] = None,
        year: Optional[int] = None,
        quality: Optional[str] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        poster_path: Optional[str] = None,
    ) -> ContentRequest:
        """
        Create a new content request.

        Args:
            correlation_id: Unique correlation ID
            query: User query
            content_type: Content type (movie/tv)
            title: Content title
            status: Request status
            user_id: Optional user ID
            year: Optional year
            quality: Optional quality preference
            season: Optional season number
            episode: Optional episode number
            tmdb_id: Optional TMDB ID
            imdb_id: Optional IMDb ID
            poster_path: Optional poster path

        Returns:
            Created ContentRequest
        """
        async with self.db.session() as session:
            request = ContentRequest(
                correlation_id=correlation_id,
                query=query,
                content_type=content_type,
                title=title,
                status=status,
                user_id=user_id,
                year=year,
                quality=quality,
                season=season,
                episode=episode,
                tmdb_id=tmdb_id,
                imdb_id=imdb_id,
                poster_path=poster_path,
            )
            session.add(request)
            await session.commit()
            await session.refresh(request)
            return request

    async def get_by_id(self, request_id: int) -> Optional[ContentRequest]:
        """
        Get a content request by ID.

        Args:
            request_id: Request ID

        Returns:
            ContentRequest if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
                select(ContentRequest).where(ContentRequest.id == request_id)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_correlation_id(self, correlation_id: str) -> Optional[ContentRequest]:
        """
        Get a content request by correlation ID.

        Args:
            correlation_id: Correlation ID

        Returns:
            ContentRequest if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
                select(ContentRequest).where(ContentRequest.correlation_id == correlation_id)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_all(
        self,
        user_id: Optional[str] = None,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContentRequest]:
        """
        Get all content requests with optional filters.

        Args:
            user_id: Optional user ID filter
            content_type: Optional content type filter
            status: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of ContentRequest instances
        """
        async with self.db.session() as session:
            query = select(ContentRequest)

            if user_id:
                query = query.where(ContentRequest.user_id == user_id)
            if content_type:
                query = query.where(ContentRequest.content_type == content_type)
            if status:
                query = query.where(ContentRequest.status == status)

            query = query.order_by(ContentRequest.created_at.desc()).limit(limit).offset(offset)

            result = await session.execute(query)  # noqa: F841
            return list(result.scalars().all())

    async def update_status(
        self,
        request_id: int,
        status: str,
        external_id: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[ContentRequest]:
        """
        Update request status.

        Args:
            request_id: Request ID
            status: New status
            external_id: Optional external service ID
            completed_at: Optional completion timestamp

        Returns:
            Updated ContentRequest if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
                select(ContentRequest).where(ContentRequest.id == request_id)
            )
            request = result.scalar_one_or_none()

            if request:
                request.status = status
                if external_id:
                    request.external_id = external_id
                if completed_at:
                    request.completed_at = completed_at
                elif status == "completed":
                    request.completed_at = datetime.utcnow()

                await session.commit()
                await session.refresh(request)
                return request  # type: ignore[no-any-return]

            return None

    async def update_metadata(
        self,
        request_id: int,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        poster_path: Optional[str] = None,
    ) -> Optional[ContentRequest]:
        """
        Update request metadata.

        Args:
            request_id: Request ID
            tmdb_id: Optional TMDB ID
            imdb_id: Optional IMDb ID
            poster_path: Optional poster path

        Returns:
            Updated ContentRequest if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
                select(ContentRequest).where(ContentRequest.id == request_id)
            )
            request = result.scalar_one_or_none()

            if request:
                if tmdb_id is not None:
                    request.tmdb_id = tmdb_id
                if imdb_id is not None:
                    request.imdb_id = imdb_id
                if poster_path is not None:
                    request.poster_path = poster_path

                await session.commit()
                await session.refresh(request)
                return request  # type: ignore[no-any-return]

            return None

    async def delete(self, request_id: int) -> bool:
        """
        Delete a content request.

        Args:
            request_id: Request ID

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
                select(ContentRequest).where(ContentRequest.id == request_id)
            )
            request = result.scalar_one_or_none()

            if request:
                await session.delete(request)
                await session.commit()
                return True

            return False

    async def count(
        self,
        user_id: Optional[str] = None,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Count content requests with optional filters.

        Args:
            user_id: Optional user ID filter
            content_type: Optional content type filter
            status: Optional status filter

        Returns:
            Count of matching requests
        """
        from sqlalchemy import func

        async with self.db.session() as session:
            query = select(func.count(ContentRequest.id))

            if user_id:
                query = query.where(ContentRequest.user_id == user_id)
            if content_type:
                query = query.where(ContentRequest.content_type == content_type)
            if status:
                query = query.where(ContentRequest.status == status)

            result = await session.execute(query)  # noqa: F841
            return result.scalar_one()  # type: ignore[no-any-return]


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

    async def init_db(self) -> None:
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

    async def close(self) -> None:
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
            result = await session.execute(  # noqa: F841
                select(ServiceSettings).where(ServiceSettings.service_name == service_name)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_all_service_settings(self) -> dict[str, ServiceSettings]:
        """
        Get all service settings.

        Returns:
            Dictionary mapping service names to settings
        """
        async with self.db.session() as session:
            result = await session.execute(select(ServiceSettings))  # noqa: F841
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
            result = await session.execute(  # noqa: F841
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
            return settings  # type: ignore[no-any-return]

    async def delete_service_settings(self, service_name: str) -> bool:
        """
        Delete service settings.

        Args:
            service_name: Service name

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
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
            result = await session.execute(  # noqa: F841
                select(BestPractice).where(BestPractice.id == practice_id)
            )
            return result.scalar_one_or_none()  # type: ignore[no-any-return]

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
            result = await session.execute(query)  # noqa: F841
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
            result = await session.execute(query)  # noqa: F841
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
            result = await session.execute(query)  # noqa: F841
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
            result = await session.execute(query)  # noqa: F841
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
            result = await session.execute(query)  # noqa: F841
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

            result = await session.execute(query)  # noqa: F841
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

            result = await session.execute(query)  # noqa: F841
            return result.scalar_one()  # type: ignore[no-any-return]

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
            result = await session.execute(  # noqa: F841
                select(BestPractice).where(BestPractice.id == practice_id)
            )
            practice = result.scalar_one_or_none()

            if practice:
                for key, value in data.items():
                    if hasattr(practice, key) and value is not None:
                        setattr(practice, key, value)

                await session.commit()
                await session.refresh(practice)
                return practice  # type: ignore[no-any-return]

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
            result = await session.execute(  # noqa: F841
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
        result = await self.update(practice_id, {"enabled": False})  # noqa: F841
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
            result = await session.execute(  # noqa: F841
                sql_delete(BestPractice).where(BestPractice.id.in_(practice_ids))
            )
            await session.commit()
            return result.rowcount  # type: ignore[no-any-return]

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
            result = await session.execute(query)  # noqa: F841
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
            result = AuditResult(  # noqa: F841
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
            result = await session.execute(query)  # noqa: F841
            return list(result.scalars().all())


# ============================================================================
# Activity Log Repository
# ============================================================================


class ActivityLogRepository:
    """
    Repository for activity log database operations.

    Provides comprehensive CRUD operations, filtering, searching, pagination,
    and statistics aggregation for activity logs.
    """

    def __init__(self, db: Database):
        """
        Initialize repository.

        Args:
            db: Database instance
        """
        self.db = db

    async def create_activity(
        self,
        service: str,
        event_type: str,
        severity: str,
        message: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> ActivityLog:
        """
        Create a new activity log entry.

        Args:
            service: Service name (e.g., "monitoring_service", "recovery_service")
            event_type: Event type (e.g., "download_failed", "recovery_attempted")
            severity: Severity level (info, warning, error, critical)
            message: Human-readable message
            correlation_id: Optional correlation ID for tracking related events
            metadata: Optional metadata dictionary
            user_id: Optional user ID for multi-user tracking
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Created ActivityLog instance
        """
        async with self.db.session() as session:
            activity = ActivityLog(
                service=service,
                event_type=event_type,
                severity=severity,
                message=message,
                correlation_id=correlation_id,
                event_metadata=metadata or {},
                user_id=user_id,
                timestamp=timestamp or datetime.utcnow(),
            )
            session.add(activity)
            await session.commit()
            await session.refresh(activity)
            return activity

    async def get_activity_by_id(self, activity_id: int) -> Optional[ActivityLog]:
        """
        Get an activity by ID.

        Args:
            activity_id: Activity ID

        Returns:
            ActivityLog if found, None otherwise
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ActivityLog).where(ActivityLog.id == activity_id)
            )  # noqa: F841
            return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_activities(
        self,
        service: Optional[str] = None,
        services: Optional[list[str]] = None,
        event_type: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        severity: Optional[str] = None,
        severities: Optional[list[str]] = None,
        min_severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        search_query: Optional[str] = None,
        order_by: str = "timestamp",
        order: str = "desc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[ActivityLog]:
        """
        Get activities with optional filters.

        Args:
            service: Filter by specific service
            services: Filter by multiple services
            event_type: Filter by specific event type
            event_types: Filter by multiple event types
            severity: Filter by specific severity
            severities: Filter by multiple severities
            min_severity: Filter by minimum severity level
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            correlation_id: Filter by correlation ID
            search_query: Search in message and metadata
            order_by: Field to order by (default: timestamp)
            order: Order direction (asc/desc, default: desc)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of ActivityLog instances
        """
        async with self.db.session() as session:
            query = select(ActivityLog)

            # Apply filters
            if service:
                query = query.where(ActivityLog.service == service)
            if services:
                query = query.where(ActivityLog.service.in_(services))
            if event_type:
                query = query.where(ActivityLog.event_type == event_type)
            if event_types:
                query = query.where(ActivityLog.event_type.in_(event_types))
            if severity:
                query = query.where(ActivityLog.severity == severity)
            if severities:
                query = query.where(ActivityLog.severity.in_(severities))
            if min_severity:
                # Map severity to numeric level for comparison
                severity_order = {"info": 0, "warning": 1, "error": 2, "critical": 3}
                min_level = severity_order.get(min_severity, 0)
                valid_severities = [s for s, l in severity_order.items() if l >= min_level]
                query = query.where(ActivityLog.severity.in_(valid_severities))
            if start_date:
                query = query.where(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.where(ActivityLog.timestamp <= end_date)
            if correlation_id:
                query = query.where(ActivityLog.correlation_id == correlation_id)
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.where(ActivityLog.message.ilike(search_pattern))

            # Apply ordering
            order_column = getattr(ActivityLog, order_by, ActivityLog.timestamp)
            if order.lower() == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)  # noqa: F841
            return list(result.scalars().all())

    async def count_activities(
        self,
        service: Optional[str] = None,
        services: Optional[list[str]] = None,
        event_type: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        severity: Optional[str] = None,
        severities: Optional[list[str]] = None,
        min_severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """
        Count activities with optional filters.

        Args:
            service: Filter by specific service
            services: Filter by multiple services
            event_type: Filter by specific event type
            event_types: Filter by multiple event types
            severity: Filter by specific severity
            severities: Filter by multiple severities
            min_severity: Filter by minimum severity level
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            correlation_id: Filter by correlation ID
            search_query: Search in message and metadata

        Returns:
            Count of matching activities
        """
        from sqlalchemy import func

        async with self.db.session() as session:
            query = select(func.count(ActivityLog.id))

            # Apply same filters as get_activities
            if service:
                query = query.where(ActivityLog.service == service)
            if services:
                query = query.where(ActivityLog.service.in_(services))
            if event_type:
                query = query.where(ActivityLog.event_type == event_type)
            if event_types:
                query = query.where(ActivityLog.event_type.in_(event_types))
            if severity:
                query = query.where(ActivityLog.severity == severity)
            if severities:
                query = query.where(ActivityLog.severity.in_(severities))
            if min_severity:
                severity_order = {"info": 0, "warning": 1, "error": 2, "critical": 3}
                min_level = severity_order.get(min_severity, 0)
                valid_severities = [s for s, l in severity_order.items() if l >= min_level]
                query = query.where(ActivityLog.severity.in_(valid_severities))
            if start_date:
                query = query.where(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.where(ActivityLog.timestamp <= end_date)
            if correlation_id:
                query = query.where(ActivityLog.correlation_id == correlation_id)
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.where(ActivityLog.message.ilike(search_pattern))

            result = await session.execute(query)  # noqa: F841
            return result.scalar_one()  # type: ignore[no-any-return]

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get activity statistics with aggregations.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with statistics
        """

        async with self.db.session() as session:
            # Build base query
            query = select(ActivityLog)
            if start_date:
                query = query.where(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.where(ActivityLog.timestamp <= end_date)

            # Get all matching activities
            result = await session.execute(query)  # noqa: F841
            activities = result.scalars().all()

            # Calculate statistics
            total_count = len(activities)
            by_type: dict[str, int] = {}
            by_service: dict[str, int] = {}
            by_severity: dict[str, int] = {}

            for activity in activities:
                by_type[activity.event_type] = by_type.get(activity.event_type, 0) + 1
                by_service[activity.service] = by_service.get(activity.service, 0) + 1
                by_severity[activity.severity] = by_severity.get(activity.severity, 0) + 1

            return {
                "total_count": total_count,
                "by_type": by_type,
                "by_service": by_service,
                "by_severity": by_severity,
            }

    async def get_trend(
        self,
        days: int = 7,
        event_type: Optional[str] = None,
        service: Optional[str] = None,
    ) -> dict[str, int]:
        """
        Get activity trend over time.

        Args:
            days: Number of days to include
            event_type: Optional event type filter
            service: Optional service filter

        Returns:
            Dictionary mapping dates (YYYY-MM-DD) to counts
        """
        from sqlalchemy import func

        async with self.db.session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = select(
                func.date(ActivityLog.timestamp).label("date"),
                func.count(ActivityLog.id).label("count"),
            ).where(ActivityLog.timestamp >= start_date)

            if event_type:
                query = query.where(ActivityLog.event_type == event_type)
            if service:
                query = query.where(ActivityLog.service == service)

            query = query.group_by(func.date(ActivityLog.timestamp))

            result = await session.execute(query)  # noqa: F841
            rows = result.all()

            return {str(row.date): row.count for row in rows}

    async def delete_old_activities(self, cutoff_date: datetime) -> int:
        """
        Delete activities older than cutoff date.

        Args:
            cutoff_date: Delete activities before this date

        Returns:
            Number of activities deleted
        """
        from sqlalchemy import delete as sql_delete

        async with self.db.session() as session:
            result = await session.execute(  # noqa: F841
                sql_delete(ActivityLog).where(ActivityLog.timestamp < cutoff_date)
            )
            await session.commit()
            return result.rowcount  # type: ignore[no-any-return]
