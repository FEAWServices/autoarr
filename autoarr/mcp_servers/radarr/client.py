"""
Radarr API Client.

This module provides an async HTTP client for interacting with the Radarr API v3.
It handles authentication via X-Api-Key header, request formatting, response parsing,
and error handling.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from httpx import AsyncClient, HTTPError


# Custom exceptions
class RadarrClientError(Exception):
    """Base exception for Radarr client errors."""


class RadarrConnectionError(RadarrClientError):
    """Exception raised when connection to Radarr fails."""


class RadarrClient:
    """
    Async client for Radarr API v3.

    This client provides methods to interact with Radarr's REST API,
    handling authentication via X-Api-Key header, request building, and response parsing.

    Attributes:
        url: Base URL of the Radarr instance
        api_key: API key for authentication
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Radarr client.

        Args:
            url: Base URL of the Radarr instance (e.g., "http://localhost:7878")
            api_key: API key for authentication (X-Api-Key header)
            timeout: Request timeout in seconds (default: 30.0)

        Raises:
            ValueError: If url or api_key is empty
        """
        if not url or not url.strip():
            raise ValueError("URL is required and cannot be empty")
        if not api_key or not api_key.strip():
            raise ValueError("API key is required and cannot be empty")

        # Normalize URL (remove trailing slash)
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # Create HTTP client
        self._client: Optional[AsyncClient] = None

    def _get_client(self) -> AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = AsyncClient(timeout=self.timeout)  # noqa: F841
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None  # noqa: F841

    async def __aenter__(self) -> "RadarrClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @classmethod
    async def create(
        cls,
        url: str,
        api_key: str,
        timeout: float = 30.0,
        validate_connection: bool = False,
    ) -> "RadarrClient":
        """
        Factory method to create and optionally validate a Radarr client.

        Args:
            url: Base URL of Radarr instance
            api_key: API key for authentication
            timeout: Request timeout in seconds
            validate_connection: If True, validates connection before returning

        Returns:
            Initialized RadarrClient instance

        Raises:
            RadarrConnectionError: If validation fails
            ValueError: If url or api_key is invalid
        """
        client = cls(url, api_key, timeout)  # noqa: F841
        if validate_connection:
            try:
                is_healthy = await client.health_check()
                if not is_healthy:
                    await client.close()
                    raise RadarrConnectionError("Failed to validate connection to Radarr")
            except Exception as e:
                await client.close()
                raise RadarrConnectionError(f"Connection validation failed: {e}")
        return client

    def _build_url(self, endpoint: str, **params: Any) -> str:
        """
        Build API URL with parameters.

        Args:
            endpoint: API endpoint (e.g., "movie", "command")
            **params: Query parameters

        Returns:
            Complete API URL with query parameters
        """
        # Base API v3 endpoint
        base = f"{self.url}/api/v3/{endpoint}"

        # Build query parameters (if any)
        if params:
            # Filter out None values
            filtered_params = {k: v for k, v in params.items() if v is not None}

            # Convert boolean to lowercase string for Radarr API
            for key, value in filtered_params.items():
                if isinstance(value, bool):
                    filtered_params[key] = str(value).lower()

            if filtered_params:
                query_string = urlencode(filtered_params)
                return f"{base}?{query_string}"

        return base

    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers including API key.

        Returns:
            Dictionary of headers with X-Api-Key
        """
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(  # noqa: C901
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        json_data: Optional[Dict[str, Any]] = None,
        **params: Any,
    ) -> Any:
        """
        Make an API request to Radarr.

        Args:
            method: HTTP method (GET, POST, DELETE, PUT)
            endpoint: API endpoint
            max_retries: Maximum number of retry attempts
            json_data: JSON data for POST/PUT requests
            **params: Query parameters

        Returns:
            Parsed JSON response or empty dict

        Raises:
            RadarrConnectionError: If connection fails
            RadarrClientError: If API returns an error
        """
        url = self._build_url(endpoint, **params)
        headers = self._get_headers()
        client = self._get_client()  # noqa: F841

        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check for HTTP errors
                if response.status_code == 401:
                    raise RadarrClientError("Unauthorized: Invalid API key (401)")
                elif response.status_code == 404:
                    raise RadarrClientError("Not found (404): Resource not found")
                elif response.status_code == 503:
                    # Service unavailable - retry
                    last_error = RadarrClientError("Server unavailable (503)")
                    if attempt < max_retries - 1:
                        continue
                    raise RadarrClientError("Server unavailable after retries (503)")
                elif response.status_code >= 500:
                    raise RadarrClientError(
                        f"Server error: Radarr returned status {response.status_code}"
                    )
                elif response.status_code >= 400:
                    raise RadarrClientError(
                        f"Client error: Radarr returned status {response.status_code}"
                    )

                # Parse JSON response (or return empty dict for 200 with no content)
                if response.status_code == 200 or response.status_code == 201:
                    try:
                        if response.text:
                            return response.json()
                        else:
                            return {}
                    except json.JSONDecodeError as e:
                        raise RadarrClientError(f"Invalid JSON response: {e}")

                return {}

            except HTTPError as e:
                last_error = e
                # Retry on connection errors
                if attempt < max_retries - 1:
                    continue
                raise RadarrConnectionError(f"Connection failed: {e}")

        # If we get here, all retries failed
        if last_error:
            raise RadarrConnectionError(
                f"Connection failed after {max_retries} attempts: {last_error}"
            )
        raise RadarrConnectionError(f"Connection failed after {max_retries} attempts")

    # ========================================================================
    # System Operations
    # ========================================================================

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get Radarr system status and version information.

        Returns:
            System status data including version, OS, and configuration
        """
        return await self._request("GET", "system/status")

    async def health_check(self) -> bool:
        """
        Check if Radarr is accessible and responding.

        Returns:
            True if Radarr is healthy, False otherwise
        """
        try:
            await self.get_system_status()
            return True
        except Exception:
            return False

    # ========================================================================
    # Movie Operations
    # ========================================================================

    async def get_movies(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all movies from Radarr.

        Args:
            limit: Maximum number of movies to return (optional)
            page: Page number for pagination (optional)

        Returns:
            List of movie dictionaries
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page

        return await self._request("GET", "movie", **params)

    async def get_movie_by_id(self, movie_id: int) -> Dict[str, Any]:
        """
        Get a specific movie by ID.

        Args:
            movie_id: The movie ID

        Returns:
            Movie dictionary

        Raises:
            RadarrClientError: If movie not found (404)
        """
        return await self._request("GET", f"movie/{movie_id}")

    async def search_movie_lookup(self, term: str) -> List[Dict[str, Any]]:
        """
        Search for movies via TMDb lookup.

        Args:
            term: Search term (movie title or tmdb:id or imdb:id)

        Returns:
            List of movie search results from TMDb
        """
        return await self._request("GET", "movie/lookup", term=term)

    async def add_movie(self, movie_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new movie to Radarr.

        Args:
            movie_data: Movie data including:
                - tmdbId: TMDb ID (required)
                - title: Movie title (required)
                - qualityProfileId: Quality profile ID (required)
                - rootFolderPath: Root folder path (required)
                - monitored: Monitor movie (optional, default: True)
                - minimumAvailability: Minimum availability (optional)
                - addOptions: Additional options (optional)

        Returns:
            Added movie data

        Raises:
            ValueError: If required fields are missing
            RadarrClientError: If add fails (400, 500, etc.)
        """
        # Validate required fields
        if "tmdbId" not in movie_data:
            raise ValueError("tmdbId is required to add a movie")
        if "rootFolderPath" not in movie_data:
            raise ValueError("rootFolderPath is required to add a movie")

        return await self._request("POST", "movie", json_data=movie_data)

    async def delete_movie(
        self,
        movie_id: int,
        delete_files: bool = False,
        add_import_exclusion: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Delete a movie from Radarr.

        Args:
            movie_id: The movie ID to delete
            delete_files: Whether to delete movie files (default: False)
            add_import_exclusion: Add to import exclusion list (optional)

        Returns:
            Empty dict on success
        """
        params = {}
        if delete_files:
            params["deleteFiles"] = "true"
        if add_import_exclusion is not None:
            params["addImportExclusion"] = "true" if add_import_exclusion else "false"

        return await self._request("DELETE", f"movie/{movie_id}", **params)

    # ========================================================================
    # Command Operations
    # ========================================================================

    async def _execute_command(
        self, command_name: str, command_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a Radarr command.

        Args:
            command_name: The command name
            command_data: Command parameters (additional parameters beyond 'name')

        Returns:
            Command response with ID and status
        """
        # Merge command name with additional parameters
        payload = {"name": command_name, **command_data}
        return await self._request("POST", "command", json_data=payload)

    async def get_command(self, command_id: int) -> Dict[str, Any]:
        """
        Get command status by ID.

        Args:
            command_id: The command ID

        Returns:
            Command object with status and progress
        """
        return await self._request("GET", f"command/{command_id}")

    async def search_movie(self, movie_id: int) -> Dict[str, Any]:
        """
        Trigger a search for a specific movie.

        Args:
            movie_id: The movie ID to search for

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "movieIds": [movie_id],
        }
        return await self._execute_command("MoviesSearch", command_data)

    async def refresh_movie(self, movie_id: int) -> Dict[str, Any]:
        """
        Refresh movie information from TMDb.

        Args:
            movie_id: The movie ID to refresh

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "movieId": movie_id,
        }
        return await self._execute_command("RefreshMovie", command_data)

    async def rescan_movie(self, movie_id: int) -> Dict[str, Any]:
        """
        Rescan movie files on disk.

        Args:
            movie_id: The movie ID to rescan

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "movieId": movie_id,
        }
        return await self._execute_command("RescanMovie", command_data)

    # ========================================================================
    # Calendar, Queue, and Wanted Operations
    # ========================================================================

    async def get_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming movie releases from the calendar.

        Args:
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)

        Returns:
            List of upcoming movie dictionaries
        """
        params = {}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        return await self._request("GET", "calendar", **params)

    async def get_queue(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get the download queue.

        Args:
            page: Page number for pagination (optional)
            page_size: Page size for pagination (optional)

        Returns:
            Queue data with records and pagination info
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size

        return await self._request("GET", "queue", **params)

    async def get_wanted_missing(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get missing/wanted movies.

        Args:
            page: Page number for pagination (optional)
            page_size: Page size for pagination (optional)

        Returns:
            Wanted/missing movies data with pagination info
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size

        return await self._request("GET", "wanted/missing", **params)
