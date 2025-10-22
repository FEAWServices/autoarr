"""
Content Integration Service for AutoArr.

This service provides integration with Sonarr and Radarr for adding
movies and TV shows to the media management system.
"""

from typing import Any, Dict, Optional

from autoarr.shared.core.mcp_orchestrator import MCPOrchestrator


class ContentIntegrationError(Exception):
    """Base exception for content integration errors."""


class ContentAlreadyExistsError(ContentIntegrationError):
    """Exception raised when content already exists in the library."""


class ServiceUnavailableError(ContentIntegrationError):
    """Exception raised when the service is unavailable."""


class ContentIntegrationService:
    """
    Content Integration Service for Radarr and Sonarr.

    This service handles adding movies to Radarr and TV shows to Sonarr
    using the MCP orchestrator for service communication.

    Args:
        mcp_orchestrator: MCP orchestrator instance
    """

    def __init__(self, mcp_orchestrator: MCPOrchestrator) -> None:
        """Initialize content integration service."""
        self.orchestrator = mcp_orchestrator

    async def add_movie_to_radarr(
        self,
        tmdb_id: int,
        quality_profile_id: int,
        root_folder: str,
        monitored: bool = True,
        search_now: bool = True,
        title: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a movie to Radarr.

        Args:
            tmdb_id: TMDB ID of the movie
            quality_profile_id: Quality profile ID to use
            root_folder: Root folder path for the movie
            monitored: Whether to monitor the movie
            search_now: Whether to start searching immediately
            title: Optional movie title (for error messages)
            year: Optional movie year (for error messages)

        Returns:
            Dict with movie details from Radarr

        Raises:
            ContentAlreadyExistsError: If movie already exists
            ServiceUnavailableError: If Radarr is unavailable
            ContentIntegrationError: If add operation fails
        """
        try:
            # First, check if movie already exists
            lookup_result = await self.orchestrator.call_tool(  # noqa: F841
                server="radarr",
                tool="lookup_movie",
                params={"tmdb_id": tmdb_id},
            )

            if not lookup_result:
                raise ContentIntegrationError(
                    f"Movie not found in TMDB database: {title or tmdb_id}"
                )

            # Check if already in library
            check_result = await self.orchestrator.call_tool(  # noqa: F841
                server="radarr",
                tool="get_movies",
                params={},
            )

            if check_result:
                existing_movies = check_result.get("movies", [])
                for movie in existing_movies:
                    if movie.get("tmdbId") == tmdb_id:
                        raise ContentAlreadyExistsError(
                            f"Movie '{movie.get('title')}' already exists in Radarr"
                        )

            # Add movie to Radarr
            add_result = await self.orchestrator.call_tool(  # noqa: F841
                server="radarr",
                tool="add_movie",
                params={
                    "tmdb_id": tmdb_id,
                    "quality_profile_id": quality_profile_id,
                    "root_folder_path": root_folder,
                    "monitored": monitored,
                    "search_for_movie": search_now,
                },
            )

            if not add_result:
                raise ContentIntegrationError("Failed to add movie to Radarr")

            return add_result

        except ContentAlreadyExistsError:
            # Re-raise as-is
            raise
        except Exception as e:
            if "unavailable" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(f"Radarr service unavailable: {str(e)}")
            raise ContentIntegrationError(f"Failed to add movie to Radarr: {str(e)}")

    async def add_series_to_sonarr(
        self,
        tvdb_id: int,
        quality_profile_id: int,
        root_folder: str,
        season_folder: bool = True,
        monitored: bool = True,
        search_now: bool = True,
        title: Optional[str] = None,
        season: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a TV series to Sonarr.

        Args:
            tvdb_id: TVDB ID of the series
            quality_profile_id: Quality profile ID to use
            root_folder: Root folder path for the series
            season_folder: Whether to use season folders
            monitored: Whether to monitor the series
            search_now: Whether to start searching immediately
            title: Optional series title (for error messages)
            season: Optional specific season to monitor

        Returns:
            Dict with series details from Sonarr

        Raises:
            ContentAlreadyExistsError: If series already exists
            ServiceUnavailableError: If Sonarr is unavailable
            ContentIntegrationError: If add operation fails
        """
        try:
            # First, lookup series in TVDB
            lookup_result = await self.orchestrator.call_tool(  # noqa: F841
                server="sonarr",
                tool="lookup_series",
                params={"term": f"tvdb:{tvdb_id}"},
            )

            if not lookup_result or not lookup_result.get("series"):
                raise ContentIntegrationError(
                    f"Series not found in TVDB database: {title or tvdb_id}"
                )

            # Check if already in library
            check_result = await self.orchestrator.call_tool(  # noqa: F841
                server="sonarr",
                tool="get_series",
                params={},
            )

            if check_result:
                existing_series = check_result.get("series", [])
                for series in existing_series:
                    if series.get("tvdbId") == tvdb_id:
                        raise ContentAlreadyExistsError(
                            f"Series '{series.get('title')}' already exists in Sonarr"
                        )

            # Add series to Sonarr
            add_result = await self.orchestrator.call_tool(  # noqa: F841
                server="sonarr",
                tool="add_series",
                params={
                    "tvdb_id": tvdb_id,
                    "quality_profile_id": quality_profile_id,
                    "root_folder_path": root_folder,
                    "season_folder": season_folder,
                    "monitored": monitored,
                    "search_for_missing_episodes": search_now,
                },
            )

            if not add_result:
                raise ContentIntegrationError("Failed to add series to Sonarr")

            return add_result

        except ContentAlreadyExistsError:
            # Re-raise as-is
            raise
        except Exception as e:
            if "unavailable" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(f"Sonarr service unavailable: {str(e)}")
            raise ContentIntegrationError(f"Failed to add series to Sonarr: {str(e)}")

    async def get_radarr_quality_profiles(self) -> list[Dict[str, Any]]:
        """
        Get available quality profiles from Radarr.

        Returns:
            List of quality profile dictionaries

        Raises:
            ServiceUnavailableError: If Radarr is unavailable
            ContentIntegrationError: If operation fails
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="radarr",
                tool="get_quality_profiles",
                params={},
            )

            if not result:
                raise ContentIntegrationError("Failed to get Radarr quality profiles")

            return result.get("profiles", [])

        except Exception as e:
            if "unavailable" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(f"Radarr service unavailable: {str(e)}")
            raise ContentIntegrationError(f"Failed to get Radarr quality profiles: {str(e)}")

    async def get_sonarr_quality_profiles(self) -> list[Dict[str, Any]]:
        """
        Get available quality profiles from Sonarr.

        Returns:
            List of quality profile dictionaries

        Raises:
            ServiceUnavailableError: If Sonarr is unavailable
            ContentIntegrationError: If operation fails
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="sonarr",
                tool="get_quality_profiles",
                params={},
            )

            if not result:
                raise ContentIntegrationError("Failed to get Sonarr quality profiles")

            return result.get("profiles", [])

        except Exception as e:
            if "unavailable" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(f"Sonarr service unavailable: {str(e)}")
            raise ContentIntegrationError(f"Failed to get Sonarr quality profiles: {str(e)}")

    async def get_radarr_root_folders(self) -> list[Dict[str, Any]]:
        """
        Get available root folders from Radarr.

        Returns:
            List of root folder dictionaries

        Raises:
            ServiceUnavailableError: If Radarr is unavailable
            ContentIntegrationError: If operation fails
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="radarr",
                tool="get_root_folders",
                params={},
            )

            if not result:
                raise ContentIntegrationError("Failed to get Radarr root folders")

            return result.get("folders", [])

        except Exception as e:
            if "unavailable" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(f"Radarr service unavailable: {str(e)}")
            raise ContentIntegrationError(f"Failed to get Radarr root folders: {str(e)}")

    async def get_sonarr_root_folders(self) -> list[Dict[str, Any]]:
        """
        Get available root folders from Sonarr.

        Returns:
            List of root folder dictionaries

        Raises:
            ServiceUnavailableError: If Sonarr is unavailable
            ContentIntegrationError: If operation fails
        """
        try:
            result = await self.orchestrator.call_tool(  # noqa: F841
                server="sonarr",
                tool="get_root_folders",
                params={},
            )

            if not result:
                raise ContentIntegrationError("Failed to get Sonarr root folders")

            return result.get("folders", [])

        except Exception as e:
            if "unavailable" in str(e).lower() or "connection" in str(e).lower():
                raise ServiceUnavailableError(f"Sonarr service unavailable: {str(e)}")
            raise ContentIntegrationError(f"Failed to get Sonarr root folders: {str(e)}")
