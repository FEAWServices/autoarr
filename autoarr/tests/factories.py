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
Test Data Factories for Sprint 7-8.

Provides reusable factory functions for creating test data objects
with sensible defaults and easy customization. Follows the Factory pattern
for maintainable, composable test data generation.

Usage:
    # Create a simple movie request
    request = ContentRequestFactory.create()

    # Create with custom values
    request = ContentRequestFactory.create(
        title="The Matrix",
        year=1999,
        status="completed"
    )

    # Create a batch
    requests = ContentRequestFactory.create_batch(count=10)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from fastapi import WebSocket

# ============================================================================
# ContentRequest Factory
# ============================================================================


class ContentRequestFactory:
    """Factory for creating ContentRequest test data."""

    @staticmethod
    def create(
        id: Optional[int] = None,
        user_input: str = "Add Inception",
        media_type: Optional[str] = None,
        title: Optional[str] = "Inception",
        year: Optional[int] = 2010,
        quality: Optional[str] = None,
        status: str = "pending",
        search_results: Optional[List[Dict[str, Any]]] = None,
        selected_result_id: Optional[str] = None,
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a ContentRequest test object.

        Args:
            id: Request ID (default: 1)
            user_input: Original user input text
            media_type: "movie" or "tv" (default: "movie")
            title: Content title
            year: Release year
            quality: Quality profile
            status: Request status
            search_results: List of search results
            selected_result_id: ID of selected result
            error_message: Error message if failed
            created_at: Creation timestamp
            updated_at: Last update timestamp
            **kwargs: Additional fields

        Returns:
            Dictionary representing a ContentRequest
        """
        return {
            "id": id or 1,
            "user_input": user_input,
            "media_type": media_type or "movie",
            "title": title,
            "year": year,
            "quality": quality,
            "status": status,
            "search_results": search_results or [],
            "selected_result_id": selected_result_id,
            "error_message": error_message,
            "created_at": created_at or datetime.now(timezone.utc),
            "updated_at": updated_at or datetime.now(timezone.utc),
            **kwargs,
        }

    @staticmethod
    def create_batch(count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Create multiple ContentRequest objects.

        Args:
            count: Number of requests to create
            **kwargs: Common fields for all requests

        Returns:
            List of ContentRequest dictionaries
        """
        return [ContentRequestFactory.create(id=i, **kwargs) for i in range(1, count + 1)]

    @staticmethod
    def create_movie_request(**kwargs) -> Dict[str, Any]:
        """Create a movie request with sensible defaults."""
        defaults = {
            "media_type": "movie",
            "title": "Inception",
            "year": 2010,
        }
        return ContentRequestFactory.create(**{**defaults, **kwargs})

    @staticmethod
    def create_tv_request(**kwargs) -> Dict[str, Any]:
        """Create a TV show request with sensible defaults."""
        defaults = {
            "media_type": "tv",
            "title": "Breaking Bad",
            "year": 2008,
        }
        return ContentRequestFactory.create(**{**defaults, **kwargs})

    @staticmethod
    def create_pending_request(**kwargs) -> Dict[str, Any]:
        """Create a pending request."""
        return ContentRequestFactory.create(status="pending", **kwargs)

    @staticmethod
    def create_completed_request(**kwargs) -> Dict[str, Any]:
        """Create a completed request."""
        return ContentRequestFactory.create(status="completed", **kwargs)

    @staticmethod
    def create_failed_request(error: str = "TMDB API error", **kwargs) -> Dict[str, Any]:
        """Create a failed request with error message."""
        return ContentRequestFactory.create(status="failed", error_message=error, **kwargs)


# ============================================================================
# Search Result Factory
# ============================================================================


class SearchResultFactory:
    """Factory for creating search result test data."""

    @staticmethod
    def create_tmdb_movie_result(
        tmdb_id: int = 27205,
        title: str = "Inception",
        year: int = 2010,
        overview: str = "A skilled thief who enters the dreams of others...",
        poster_path: str = "/path/to/poster.jpg",
        vote_average: float = 8.8,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a TMDB movie search result.

        Args:
            tmdb_id: TMDB ID
            title: Movie title
            year: Release year
            overview: Movie overview/description
            poster_path: Path to poster image
            vote_average: TMDB rating (0-10)
            **kwargs: Additional fields

        Returns:
            Dictionary representing a TMDB movie result
        """
        return {
            "id": tmdb_id,
            "title": title,
            "release_date": f"{year}-07-16",
            "overview": overview,
            "poster_path": poster_path,
            "backdrop_path": "/path/to/backdrop.jpg",
            "vote_average": vote_average,
            "vote_count": 25000,
            "popularity": 85.5,
            "media_type": "movie",
            "adult": False,
            "original_language": "en",
            **kwargs,
        }

    @staticmethod
    def create_tmdb_tv_result(
        tmdb_id: int = 1396,
        name: str = "Breaking Bad",
        first_air_date: str = "2008-01-20",
        overview: str = "A chemistry teacher diagnosed with cancer...",
        poster_path: str = "/path/to/poster.jpg",
        vote_average: float = 9.5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a TMDB TV search result.

        Args:
            tmdb_id: TMDB ID
            name: TV show name
            first_air_date: First air date (ISO format)
            overview: Show overview
            poster_path: Path to poster
            vote_average: TMDB rating
            **kwargs: Additional fields

        Returns:
            Dictionary representing a TMDB TV result
        """
        return {
            "id": tmdb_id,
            "name": name,
            "original_name": name,
            "first_air_date": first_air_date,
            "overview": overview,
            "poster_path": poster_path,
            "backdrop_path": "/path/to/backdrop.jpg",
            "vote_average": vote_average,
            "vote_count": 15000,
            "popularity": 95.2,
            "media_type": "tv",
            "origin_country": ["US"],
            "original_language": "en",
            **kwargs,
        }

    @staticmethod
    def create_radarr_result(
        tmdb_id: int = 27205,
        title: str = "Inception",
        year: int = 2010,
        monitored: bool = False,
        has_file: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a Radarr search result.

        Args:
            tmdb_id: TMDB ID
            title: Movie title
            year: Release year
            monitored: Whether movie is monitored
            has_file: Whether movie file exists
            **kwargs: Additional fields

        Returns:
            Dictionary representing a Radarr result
        """
        return {
            "tmdbId": tmdb_id,
            "title": title,
            "year": year,
            "monitored": monitored,
            "hasFile": has_file,
            "status": "released",
            "runtime": 148,
            "sizeOnDisk": 8589934592 if has_file else 0,
            "qualityProfileId": 1,
            "path": f"/movies/{title} ({year})",
            **kwargs,
        }

    @staticmethod
    def create_sonarr_result(
        tvdb_id: int = 81189,
        title: str = "Breaking Bad",
        year: int = 2008,
        monitored: bool = False,
        season_count: int = 5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a Sonarr search result.

        Args:
            tvdb_id: TVDB ID
            title: Series title
            year: First air year
            monitored: Whether series is monitored
            season_count: Number of seasons
            **kwargs: Additional fields

        Returns:
            Dictionary representing a Sonarr result
        """
        return {
            "tvdbId": tvdb_id,
            "title": title,
            "year": year,
            "monitored": monitored,
            "seasonCount": season_count,
            "status": "ended",
            "overview": "A chemistry teacher...",
            "network": "AMC",
            "qualityProfileId": 1,
            "path": f"/tv/{title}",
            **kwargs,
        }

    @staticmethod
    def create_batch_tmdb_movies(count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple TMDB movie results."""
        movies = [
            ("Inception", 27205, 2010, 8.8),
            ("The Matrix", 603, 1999, 8.7),
            ("Interstellar", 157336, 2014, 8.6),
            ("The Dark Knight", 155, 2008, 9.0),
            ("Pulp Fiction", 680, 1994, 8.9),
        ]
        return [
            SearchResultFactory.create_tmdb_movie_result(title=t, tmdb_id=i, year=y, vote_average=r)
            for t, i, y, r in movies[:count]
        ]


# ============================================================================
# WebSocket Event Factory
# ============================================================================


class WebSocketEventFactory:
    """Factory for creating WebSocket event test data."""

    @staticmethod
    def create(
        event_type: str = "request.created",
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a WebSocket event.

        Args:
            event_type: Event type (e.g., "request.created")
            data: Event data payload
            timestamp: Event timestamp
            correlation_id: Correlation ID for tracing
            **kwargs: Additional fields

        Returns:
            Dictionary representing a WebSocket event
        """
        return {
            "type": event_type,
            "data": data or {},
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            **kwargs,
        }

    @staticmethod
    def create_request_created_event(request_id: int, **kwargs) -> Dict[str, Any]:
        """Create a request.created event."""
        return WebSocketEventFactory.create(
            event_type="request.created",
            data={
                "request_id": request_id,
                "title": "Inception",
                "media_type": "movie",
                "status": "pending",
            },
            **kwargs,
        )

    @staticmethod
    def create_request_status_event(
        request_id: int, status: str, message: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Create a request status change event.

        Args:
            request_id: Request ID
            status: New status
            message: Optional status message
            **kwargs: Additional fields

        Returns:
            WebSocket event dictionary
        """
        return WebSocketEventFactory.create(
            event_type="request.status_changed",
            data={
                "request_id": request_id,
                "status": status,
                "message": message or f"Request {status}",
            },
            **kwargs,
        )

    @staticmethod
    def create_download_progress_event(
        download_id: str, progress: int, speed: str = "10.5 MB/s", **kwargs
    ) -> Dict[str, Any]:
        """Create a download.progress event."""
        return WebSocketEventFactory.create(
            event_type="download.progress",
            data={
                "download_id": download_id,
                "progress": progress,
                "speed": speed,
                "eta": "2 minutes",
            },
            **kwargs,
        )

    @staticmethod
    def create_system_notification_event(
        level: str = "info", message: str = "System notification", **kwargs
    ) -> Dict[str, Any]:
        """Create a system notification event."""
        return WebSocketEventFactory.create(
            event_type="system.notification",
            data={
                "level": level,
                "message": message,
            },
            **kwargs,
        )


# ============================================================================
# Mock WebSocket Factory
# ============================================================================


class MockWebSocketFactory:
    """Factory for creating mock WebSocket connections."""

    @staticmethod
    def create(connection_id: Optional[str] = None, state: str = "CONNECTED") -> MagicMock:
        """
        Create a mock WebSocket connection.

        Args:
            connection_id: Optional connection ID
            state: Connection state (CONNECTED, DISCONNECTED)

        Returns:
            Mock WebSocket object
        """
        ws = MagicMock(spec=WebSocket)
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_text = AsyncMock(return_value='{"type": "ping"}')
        ws.receive_json = AsyncMock(return_value={"type": "ping"})
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        ws.client_state = MagicMock()
        ws.client_state.name = state
        ws.connection_id = connection_id or str(uuid.uuid4())

        return ws

    @staticmethod
    def create_batch(count: int = 5) -> List[MagicMock]:
        """Create multiple mock WebSocket connections."""
        return [MockWebSocketFactory.create() for _ in range(count)]

    @staticmethod
    def create_failing_websocket(error_message: str = "Connection lost") -> MagicMock:
        """Create a mock WebSocket that raises errors on send."""
        ws = MockWebSocketFactory.create(state="DISCONNECTED")
        ws.send_json = AsyncMock(side_effect=RuntimeError(error_message))
        return ws


# ============================================================================
# LLM Response Factory
# ============================================================================


class LLMResponseFactory:
    """Factory for creating mock LLM responses."""

    @staticmethod
    def create_classification_response(
        media_type: str = "movie",
        confidence: float = 0.95,
        reasoning: str = "Based on TMDB results showing a film from 2010",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create LLM media type classification response.

        Args:
            media_type: Classified type ("movie" or "tv")
            confidence: Confidence score (0.0-1.0)
            reasoning: Classification reasoning
            **kwargs: Additional fields

        Returns:
            Dictionary representing LLM response
        """
        return {
            "content": json_dumps(
                {
                    "media_type": media_type,
                    "confidence": confidence,
                    "reasoning": reasoning,
                }
            ),
            "usage": {
                "input_tokens": 150,
                "output_tokens": 50,
            },
            **kwargs,
        }

    @staticmethod
    def create_disambiguation_response(
        selected_option: int = 0,
        reasoning: str = "Most popular and recent release",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create LLM disambiguation response."""
        return {
            "content": json_dumps(
                {
                    "selected_option": selected_option,
                    "reasoning": reasoning,
                }
            ),
            "usage": {
                "input_tokens": 200,
                "output_tokens": 75,
            },
            **kwargs,
        }

    @staticmethod
    def create_parsing_response(
        title: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        quality: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create LLM request parsing response."""
        return {
            "content": json_dumps(
                {
                    "title": title,
                    "media_type": media_type,
                    "year": year,
                    "quality": quality,
                }
            ),
            "usage": {
                "input_tokens": 100,
                "output_tokens": 40,
            },
            **kwargs,
        }


# ============================================================================
# Parsed Request Factory
# ============================================================================


class ParsedRequestFactory:
    """Factory for creating ParsedRequest objects."""

    @staticmethod
    def create(
        user_input: str = "Add Inception",
        title: str = "Inception",
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        quality: Optional[str] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        explicit_type: bool = False,
        quality_profile_override: bool = False,
        confidence: float = 0.9,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a ParsedRequest object.

        Args:
            user_input: Original user input
            title: Extracted title
            media_type: Extracted media type
            year: Extracted year
            quality: Extracted quality
            season: Season number (TV only)
            episode: Episode number (TV only)
            explicit_type: Whether type was explicitly stated
            quality_profile_override: Whether quality should override default
            confidence: Parsing confidence score
            **kwargs: Additional fields

        Returns:
            Dictionary representing ParsedRequest
        """
        return {
            "user_input": user_input,
            "title": title,
            "media_type": media_type,
            "year": year,
            "quality": quality,
            "season": season,
            "episode": episode,
            "explicit_type": explicit_type,
            "quality_profile_override": quality_profile_override,
            "confidence": confidence,
            **kwargs,
        }

    @staticmethod
    def create_movie_request(**kwargs) -> Dict[str, Any]:
        """Create a movie ParsedRequest."""
        defaults = {
            "title": "Inception",
            "media_type": "movie",
            "year": 2010,
        }
        return ParsedRequestFactory.create(**{**defaults, **kwargs})

    @staticmethod
    def create_tv_request(**kwargs) -> Dict[str, Any]:
        """Create a TV ParsedRequest."""
        defaults = {
            "title": "Breaking Bad",
            "media_type": "tv",
            "year": 2008,
        }
        return ParsedRequestFactory.create(**{**defaults, **kwargs})


# ============================================================================
# Helper Functions
# ============================================================================


def json_dumps(obj: Dict[str, Any]) -> str:
    """JSON serialize an object, handling datetime objects."""
    import json

    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    return json.dumps(obj, cls=DateTimeEncoder)


def create_timestamp(days_ago: int = 0, hours_ago: int = 0, minutes_ago: int = 0) -> datetime:
    """
    Create a timestamp relative to now.

    Args:
        days_ago: Number of days in the past
        hours_ago: Number of hours in the past
        minutes_ago: Number of minutes in the past

    Returns:
        datetime object
    """
    return datetime.now(timezone.utc) - timedelta(
        days=days_ago, hours=hours_ago, minutes=minutes_ago
    )
