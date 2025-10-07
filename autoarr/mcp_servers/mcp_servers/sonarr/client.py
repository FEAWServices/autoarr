"""
Sonarr API Client.

This module provides an async HTTP client for interacting with the Sonarr API v3.
It handles authentication via X-Api-Key header, request formatting, response parsing,
and error handling.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import httpx
from httpx import AsyncClient, HTTPError, HTTPStatusError, Response


# Custom exceptions
class SonarrClientError(Exception):
    """Base exception for Sonarr client errors."""

    pass


class SonarrConnectionError(SonarrClientError):
    """Exception raised when connection to Sonarr fails."""

    pass


class SonarrClient:
    """
    Async client for Sonarr API v3.

    This client provides methods to interact with Sonarr's REST API,
    handling authentication via X-Api-Key header, request building, and response parsing.

    Attributes:
        url: Base URL of the Sonarr instance
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
        Initialize the Sonarr client.

        Args:
            url: Base URL of the Sonarr instance (e.g., "http://localhost:8989")
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
            self._client = AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "SonarrClient":
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
    ) -> "SonarrClient":
        """
        Factory method to create and optionally validate a Sonarr client.

        Args:
            url: Base URL of Sonarr instance
            api_key: API key for authentication
            timeout: Request timeout in seconds
            validate_connection: If True, validates connection before returning

        Returns:
            Initialized SonarrClient instance

        Raises:
            SonarrConnectionError: If validation fails
            ValueError: If url or api_key is invalid
        """
        client = cls(url, api_key, timeout)
        if validate_connection:
            try:
                is_healthy = await client.health_check()
                if not is_healthy:
                    await client.close()
                    raise SonarrConnectionError("Failed to validate connection to Sonarr")
            except Exception as e:
                await client.close()
                raise SonarrConnectionError(f"Connection validation failed: {e}")
        return client

    def _build_url(self, endpoint: str, **params: Any) -> str:
        """
        Build API URL with parameters.

        Args:
            endpoint: API endpoint (e.g., "series", "episode")
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

            # Convert boolean to lowercase string for Sonarr API
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

    async def _request(
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        json_data: Optional[Dict[str, Any]] = None,
        **params: Any,
    ) -> Any:
        """
        Make an API request to Sonarr.

        Args:
            method: HTTP method (GET, POST, DELETE, PUT)
            endpoint: API endpoint
            max_retries: Maximum number of retry attempts
            json_data: JSON data for POST/PUT requests
            **params: Query parameters

        Returns:
            Parsed JSON response or empty dict

        Raises:
            SonarrConnectionError: If connection fails
            SonarrClientError: If API returns an error
        """
        url = self._build_url(endpoint, **params)
        headers = self._get_headers()
        client = self._get_client()

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
                    raise SonarrClientError("Unauthorized: Invalid API key (401)")
                elif response.status_code == 404:
                    raise SonarrClientError(f"Not found (404): Resource not found")
                elif response.status_code == 503:
                    # Service unavailable - retry
                    last_error = SonarrClientError("Server unavailable (503)")
                    if attempt < max_retries - 1:
                        continue
                    raise SonarrClientError("Server unavailable after retries (503)")
                elif response.status_code >= 500:
                    raise SonarrClientError(
                        f"Server error: Sonarr returned status {response.status_code}"
                    )
                elif response.status_code >= 400:
                    raise SonarrClientError(
                        f"Client error: Sonarr returned status {response.status_code}"
                    )

                # Parse JSON response (or return empty dict for 200 with no content)
                if response.status_code == 200 or response.status_code == 201:
                    try:
                        if response.text:
                            return response.json()
                        else:
                            return {}
                    except json.JSONDecodeError as e:
                        raise SonarrClientError(f"Invalid JSON response: {e}")

                return {}

            except HTTPError as e:
                last_error = e
                # Retry on connection errors
                if attempt < max_retries - 1:
                    continue
                raise SonarrConnectionError(f"Connection failed: {e}")

        # If we get here, all retries failed
        if last_error:
            raise SonarrConnectionError(
                f"Connection failed after {max_retries} attempts: {last_error}"
            )
        raise SonarrConnectionError(f"Connection failed after {max_retries} attempts")

    # ========================================================================
    # System Operations
    # ========================================================================

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get Sonarr system status and version information.

        Returns:
            System status data including version, OS, and configuration
        """
        return await self._request("GET", "system/status")

    async def health_check(self) -> bool:
        """
        Check if Sonarr is accessible and responding.

        Returns:
            True if Sonarr is healthy, False otherwise
        """
        try:
            await self.get_system_status()
            return True
        except Exception:
            return False

    # ========================================================================
    # Series Operations
    # ========================================================================

    async def get_series(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all TV series from Sonarr.

        Args:
            limit: Maximum number of series to return (optional)
            page: Page number for pagination (optional)

        Returns:
            List of series dictionaries
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page

        return await self._request("GET", "series", **params)

    async def get_series_by_id(self, series_id: int) -> Dict[str, Any]:
        """
        Get a specific TV series by ID.

        Args:
            series_id: The series ID

        Returns:
            Series dictionary

        Raises:
            SonarrClientError: If series not found (404)
        """
        return await self._request("GET", f"series/{series_id}")

    async def search_series(self, term: str) -> List[Dict[str, Any]]:
        """
        Search for TV series via TVDB lookup.

        Args:
            term: Search term (series title or tvdb:id)

        Returns:
            List of series search results from TVDB
        """
        return await self._request("GET", "series/lookup", term=term)

    async def add_series(self, series_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new TV series to Sonarr.

        Args:
            series_data: Series data including:
                - tvdbId: TVDB ID (required)
                - title: Series title (required)
                - qualityProfileId: Quality profile ID (required)
                - rootFolderPath: Root folder path (required)
                - seasonFolder: Use season folders (optional, default: True)
                - monitored: Monitor series (optional, default: True)
                - addOptions: Additional options (optional)

        Returns:
            Added series data

        Raises:
            ValueError: If required fields are missing
            SonarrClientError: If add fails (400, 500, etc.)
        """
        # Validate required fields
        if "tvdbId" not in series_data:
            raise ValueError("tvdbId is required to add a series")
        if "rootFolderPath" not in series_data:
            raise ValueError("rootFolderPath is required to add a series")

        return await self._request("POST", "series", json_data=series_data)

    async def delete_series(
        self,
        series_id: int,
        delete_files: bool = False,
        add_import_exclusion: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Delete a TV series from Sonarr.

        Args:
            series_id: The series ID to delete
            delete_files: Whether to delete series files (default: False)
            add_import_exclusion: Add to import exclusion list (optional)

        Returns:
            Empty dict on success
        """
        params = {}
        if delete_files:
            params["deleteFiles"] = "true"
        if add_import_exclusion is not None:
            params["addImportExclusion"] = "true" if add_import_exclusion else "false"

        return await self._request("DELETE", f"series/{series_id}", **params)

    # ========================================================================
    # Episode Operations
    # ========================================================================

    async def get_episodes(
        self,
        series_id: int,
        season_number: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get episodes for a TV series.

        Args:
            series_id: The series ID
            season_number: Filter by season number (optional)

        Returns:
            List of episode dictionaries
        """
        params = {"seriesId": series_id}
        if season_number is not None:
            params["seasonNumber"] = season_number

        return await self._request("GET", "episode", **params)

    async def get_episode_by_id(self, episode_id: int) -> Dict[str, Any]:
        """
        Get a specific episode by ID.

        Args:
            episode_id: The episode ID

        Returns:
            Episode dictionary
        """
        return await self._request("GET", f"episode/{episode_id}")

    async def search_episode(self, episode_id: int) -> Dict[str, Any]:
        """
        Trigger a search for a specific episode.

        Args:
            episode_id: The episode ID to search for

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "episodeIds": [episode_id],
        }
        return await self._execute_command("EpisodeSearch", command_data)

    # ========================================================================
    # Command Operations
    # ========================================================================

    async def _execute_command(
        self, command_name: str, command_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a Sonarr command.

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

    async def search_series_command(self, series_id: int) -> Dict[str, Any]:
        """
        Trigger a search for all episodes in a series.

        Args:
            series_id: The series ID to search

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "seriesId": series_id,
        }
        return await self._execute_command("SeriesSearch", command_data)

    async def refresh_series(self, series_id: int) -> Dict[str, Any]:
        """
        Refresh series information from TVDB.

        Args:
            series_id: The series ID to refresh

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "seriesId": series_id,
        }
        return await self._execute_command("RefreshSeries", command_data)

    async def rescan_series(self, series_id: int) -> Dict[str, Any]:
        """
        Rescan series files on disk.

        Args:
            series_id: The series ID to rescan

        Returns:
            Command object with command ID and status
        """
        command_data = {
            "seriesId": series_id,
        }
        return await self._execute_command("RescanSeries", command_data)

    # ========================================================================
    # Calendar, Queue, and Wanted Operations
    # ========================================================================

    async def get_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming episodes from the calendar.

        Args:
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)

        Returns:
            List of upcoming episode dictionaries
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
        include_series: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get missing/wanted episodes.

        Args:
            page: Page number for pagination (optional)
            page_size: Page size for pagination (optional)
            include_series: Include series information (optional)

        Returns:
            Wanted/missing episodes data with pagination info
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if include_series is not None:
            params["includeSeries"] = include_series

        return await self._request("GET", "wanted/missing", **params)
