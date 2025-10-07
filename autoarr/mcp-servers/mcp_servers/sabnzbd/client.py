"""
SABnzbd API Client.

This module provides an async HTTP client for interacting with the SABnzbd API.
It handles authentication, request formatting, response parsing, and error handling.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from httpx import AsyncClient, HTTPError, HTTPStatusError, Response


# Custom exceptions
class SABnzbdClientError(Exception):
    """Base exception for SABnzbd client errors."""

    pass


class SABnzbdConnectionError(SABnzbdClientError):
    """Exception raised when connection to SABnzbd fails."""

    pass


class SABnzbdClient:
    """
    Async client for SABnzbd API.

    This client provides methods to interact with SABnzbd's JSON API,
    handling authentication, request building, and response parsing.

    Attributes:
        url: Base URL of the SABnzbd instance
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
        Initialize the SABnzbd client.

        Args:
            url: Base URL of the SABnzbd instance (e.g., "http://localhost:8080")
            api_key: API key for authentication
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

    async def __aenter__(self) -> "SABnzbdClient":
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
    ) -> "SABnzbdClient":
        """
        Factory method to create and optionally validate a SABnzbd client.

        Args:
            url: Base URL of SABnzbd instance
            api_key: API key for authentication
            timeout: Request timeout in seconds
            validate_connection: If True, validates connection before returning

        Returns:
            Initialized SABnzbdClient instance

        Raises:
            SABnzbdConnectionError: If validation fails
            ValueError: If url or api_key is invalid
        """
        client = cls(url, api_key, timeout)
        if validate_connection:
            try:
                is_healthy = await client.health_check()
                if not is_healthy:
                    await client.close()
                    raise SABnzbdConnectionError("Failed to validate connection to SABnzbd")
            except Exception as e:
                await client.close()
                raise SABnzbdConnectionError(f"Connection validation failed: {e}")
        return client

    def _build_url(self, mode: str, **params: Any) -> str:
        """
        Build API URL with parameters.

        Args:
            mode: API mode (e.g., "queue", "history", "config")
            **params: Additional query parameters

        Returns:
            Complete API URL with query parameters
        """
        # Base API endpoint
        base = f"{self.url}/api"

        # Build query parameters
        query_params = {
            "mode": mode,
            "output": "json",
            "apikey": self.api_key,
        }

        # Add additional parameters
        for key, value in params.items():
            if value is not None:
                # Convert boolean to int for SABnzbd API
                if isinstance(value, bool):
                    query_params[key] = "1" if value else "0"
                else:
                    query_params[key] = str(value)

        # Build URL with query string
        from urllib.parse import urlencode

        query_string = urlencode(query_params)
        return f"{base}?{query_string}"

    async def _request(self, mode: str, max_retries: int = 3, **params: Any) -> Dict[str, Any]:
        """
        Make an API request to SABnzbd.

        Args:
            mode: API mode
            max_retries: Maximum number of retry attempts
            **params: Additional query parameters

        Returns:
            Parsed JSON response

        Raises:
            SABnzbdConnectionError: If connection fails
            SABnzbdClientError: If API returns an error
        """
        url = self._build_url(mode, **params)
        client = self._get_client()

        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                response = await client.get(url)

                # Check for HTTP errors
                if response.status_code == 401:
                    raise SABnzbdClientError("Unauthorized: Invalid API key")
                elif response.status_code == 503:
                    # Service unavailable - retry
                    last_error = SABnzbdClientError("Server unavailable (503)")
                    if attempt < max_retries - 1:
                        continue
                    raise SABnzbdClientError("Server unavailable after retries")
                elif response.status_code >= 500:
                    raise SABnzbdClientError(
                        f"Server error: SABnzbd returned status {response.status_code}"
                    )
                elif response.status_code >= 400:
                    raise SABnzbdClientError(
                        f"Client error: SABnzbd returned status {response.status_code}"
                    )

                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    raise SABnzbdClientError(f"Invalid JSON response: {e}")

                return data

            except HTTPError as e:
                last_error = e
                # Retry on connection errors
                if attempt < max_retries - 1:
                    continue
                raise SABnzbdConnectionError(f"Connection failed: {e}")

        # If we get here, all retries failed
        if last_error:
            raise SABnzbdConnectionError(
                f"Connection failed after {max_retries} attempts: {last_error}"
            )
        raise SABnzbdConnectionError(f"Connection failed after {max_retries} attempts")

    # ========================================================================
    # Queue Operations
    # ========================================================================

    async def get_queue(
        self,
        start: int = 0,
        limit: Optional[int] = None,
        nzo_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get the current download queue.

        Args:
            start: Start index for pagination (default: 0)
            limit: Maximum number of items to return (default: None for all)
            nzo_ids: Filter by specific NZO IDs (default: None)

        Returns:
            Queue data including status, speed, and download slots
        """
        params: Dict[str, Any] = {"start": start}

        if limit is not None:
            params["limit"] = limit

        if nzo_ids:
            params["nzo_ids"] = ",".join(nzo_ids)

        return await self._request("queue", **params)

    async def pause_queue(self) -> Dict[str, Any]:
        """
        Pause the download queue.

        Returns:
            Status response indicating success
        """
        return await self._request("pause")

    async def resume_queue(self) -> Dict[str, Any]:
        """
        Resume the download queue.

        Returns:
            Status response indicating success
        """
        return await self._request("resume")

    # ========================================================================
    # History Operations
    # ========================================================================

    async def get_history(
        self,
        start: int = 0,
        limit: Optional[int] = None,
        failed_only: bool = False,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get download history.

        Args:
            start: Start index for pagination (default: 0)
            limit: Maximum number of items to return (default: None for all)
            failed_only: Return only failed downloads (default: False)
            category: Filter by category (default: None)

        Returns:
            History data including completed and failed downloads
        """
        params: Dict[str, Any] = {"start": start}

        if limit is not None:
            params["limit"] = limit

        if failed_only:
            params["failed_only"] = 1

        if category:
            params["category"] = category

        return await self._request("history", **params)

    # ========================================================================
    # Download Management Operations
    # ========================================================================

    async def retry_download(self, nzo_id: str) -> Dict[str, Any]:
        """
        Retry a failed download.

        Args:
            nzo_id: The NZO ID of the failed download

        Returns:
            Action response with status and new NZO IDs

        Raises:
            ValueError: If nzo_id is empty
        """
        if not nzo_id or not nzo_id.strip():
            raise ValueError("nzo_id is required and cannot be empty")

        return await self._request("retry", value=nzo_id)

    async def delete_download(self, nzo_id: str, delete_files: bool = False) -> Dict[str, Any]:
        """
        Delete a download from the queue.

        Args:
            nzo_id: The NZO ID of the download to delete
            delete_files: Whether to delete downloaded files (default: False)

        Returns:
            Action response with status
        """
        params = {
            "name": "delete",
            "value": nzo_id,
        }

        if delete_files:
            params["del_files"] = 1

        return await self._request("queue", **params)

    async def pause_download(self, nzo_id: str) -> Dict[str, Any]:
        """
        Pause a specific download.

        Args:
            nzo_id: The NZO ID of the download to pause

        Returns:
            Action response with status
        """
        return await self._request("queue", name="pause", value=nzo_id)

    async def resume_download(self, nzo_id: str) -> Dict[str, Any]:
        """
        Resume a paused download.

        Args:
            nzo_id: The NZO ID of the download to resume

        Returns:
            Action response with status
        """
        return await self._request("queue", name="resume", value=nzo_id)

    # ========================================================================
    # Configuration Operations
    # ========================================================================

    async def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get SABnzbd configuration.

        Args:
            section: Specific config section to retrieve (default: None for all)

        Returns:
            Configuration data
        """
        params: Dict[str, Any] = {}

        if section:
            params["section"] = section

        return await self._request("get_config", **params)

    async def set_config(self, section: str, keyword: str, value: Any) -> Dict[str, Any]:
        """
        Set a configuration value.

        Args:
            section: Configuration section (e.g., "misc", "servers")
            keyword: Configuration key to set
            value: Value to set

        Returns:
            Status response indicating success

        Raises:
            ValueError: If section or keyword is empty
        """
        if not section or not section.strip():
            raise ValueError("section is required and cannot be empty")
        if not keyword or not keyword.strip():
            raise ValueError("keyword is required and cannot be empty")

        return await self._request(
            "set_config",
            section=section,
            keyword=keyword,
            value=value,
        )

    async def set_config_batch(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Batch update multiple configuration values.

        Args:
            config_updates: Dictionary of config paths to values
                           (e.g., {"misc.cache_limit": "1000M"})

        Returns:
            Status response indicating success
        """
        # Process each config update sequentially
        for key, value in config_updates.items():
            if "." in key:
                section, keyword = key.split(".", 1)
                await self.set_config(section, keyword, value)

        return {"status": True}

    # ========================================================================
    # Status and Information Operations
    # ========================================================================

    async def get_version(self) -> Dict[str, Any]:
        """
        Get SABnzbd version information.

        Returns:
            Version data
        """
        return await self._request("version")

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current SABnzbd status.

        Returns:
            Status data including version, uptime, and resource usage
        """
        # SABnzbd doesn't have a dedicated "status" mode, so we combine version
        # with fullstatus to get comprehensive status information
        # For simplicity, we'll use queue with specific parameters
        queue_data = await self._request("fullstatus")
        return queue_data

    async def health_check(self) -> bool:
        """
        Check if SABnzbd is accessible and responding.

        Returns:
            True if SABnzbd is healthy, False otherwise
        """
        try:
            await self.get_version()
            return True
        except Exception:
            return False
