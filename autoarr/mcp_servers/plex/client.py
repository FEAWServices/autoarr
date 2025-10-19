"""
Plex API Client.

This module provides an async HTTP client for interacting with the Plex Media Server API.
It handles authentication via X-Plex-Token header, request formatting, response parsing,
and error handling.
"""

import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from httpx import AsyncClient, HTTPError


# Custom exceptions
class PlexClientError(Exception):
    """Base exception for Plex client errors."""


class PlexConnectionError(PlexClientError):
    """Exception raised when connection to Plex fails."""


class PlexClient:
    """
    Async client for Plex Media Server API.

    This client provides methods to interact with Plex's API,
    handling authentication via X-Plex-Token header, request building, and response parsing.

    Attributes:
        url: Base URL of the Plex Media Server instance
        token: Plex authentication token
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        url: str,
        token: str,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Plex client.

        Args:
            url: Base URL of the Plex instance (e.g., "http://localhost:32400")
            token: Plex authentication token (X-Plex-Token)
            timeout: Request timeout in seconds (default: 30.0)

        Raises:
            ValueError: If url or token is empty
        """
        if not url or not url.strip():
            raise ValueError("URL is required and cannot be empty")
        if not token or not token.strip():
            raise ValueError("Token is required and cannot be empty")

        # Normalize URL (remove trailing slash)
        self.url = url.rstrip("/")
        self.token = token
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

    async def __aenter__(self) -> "PlexClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @classmethod
    async def create(
        cls,
        url: str,
        token: str,
        timeout: float = 30.0,
        validate_connection: bool = False,
    ) -> "PlexClient":
        """
        Factory method to create and optionally validate a Plex client.

        Args:
            url: Base URL of Plex instance
            token: Plex authentication token
            timeout: Request timeout in seconds
            validate_connection: If True, validates connection before returning

        Returns:
            Initialized PlexClient instance

        Raises:
            PlexConnectionError: If validation fails
            ValueError: If url or token is invalid
        """
        client = cls(url, token, timeout)  # noqa: F841
        if validate_connection:
            try:
                is_healthy = await client.health_check()
                if not is_healthy:
                    await client.close()
                    raise PlexConnectionError("Failed to validate connection to Plex")
            except Exception as e:
                await client.close()
                raise PlexConnectionError(f"Connection validation failed: {e}")
        return client

    def _build_url(self, endpoint: str, **params: Any) -> str:
        """
        Build API URL with parameters.

        Args:
            endpoint: API endpoint (e.g., "library/sections", "status/sessions")
            **params: Query parameters

        Returns:
            Complete API URL with query parameters
        """
        # Remove leading slash if present
        endpoint = endpoint.lstrip("/")

        # Base URL with endpoint
        base = f"{self.url}/{endpoint}"

        # Build query parameters (if any)
        if params:
            # Filter out None values
            filtered_params = {k: v for k, v in params.items() if v is not None}

            # Convert boolean to int for Plex API
            for key, value in filtered_params.items():
                if isinstance(value, bool):
                    filtered_params[key] = 1 if value else 0

            if filtered_params:
                query_string = urlencode(filtered_params)
                return f"{base}?{query_string}"

        return base

    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers including Plex token.

        Returns:
            Dictionary of headers with X-Plex-Token
        """
        return {
            "X-Plex-Token": self.token,
            "Accept": "application/json",
        }

    def _parse_xml_to_dict(self, xml_element: ET.Element) -> Dict[str, Any]:
        """
        Parse XML element to dictionary.

        Args:
            xml_element: XML element to parse

        Returns:
            Dictionary representation of XML
        """
        result = dict(xml_element.attrib)  # noqa: F841

        # Add children
        children = list(xml_element)
        if children:
            # Group children by tag
            children_dict: Dict[str, List[Any]] = {}
            for child in children:
                child_data = self._parse_xml_to_dict(child)
                tag = child.tag
                if tag not in children_dict:
                    children_dict[tag] = []
                children_dict[tag].append(child_data)

            # Add children to result
            for tag, items in children_dict.items():
                # If only one item, don't use a list
                result[tag] = items if len(items) > 1 else items[0]

        return result

    async def _request(  # noqa: C901
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        json_data: Optional[Dict[str, Any]] = None,
        parse_xml: bool = False,
        **params: Any,
    ) -> Any:
        """
        Make an API request to Plex.

        Args:
            method: HTTP method (GET, POST, DELETE, PUT)
            endpoint: API endpoint
            max_retries: Maximum number of retry attempts
            json_data: JSON data for POST/PUT requests
            parse_xml: If True, parse XML response to dict
            **params: Query parameters

        Returns:
            Parsed JSON response, XML dict, or empty dict

        Raises:
            PlexConnectionError: If connection fails
            PlexClientError: If API returns an error
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
                    raise PlexClientError("Unauthorized: Invalid Plex token (401)")
                elif response.status_code == 404:
                    raise PlexClientError("Not found (404): Resource not found")
                elif response.status_code == 503:
                    # Service unavailable - retry
                    last_error = PlexClientError("Server unavailable (503)")
                    if attempt < max_retries - 1:
                        continue
                    raise PlexClientError("Server unavailable after retries (503)")
                elif response.status_code >= 500:
                    raise PlexClientError(
                        f"Server error: Plex returned status {response.status_code}"
                    )
                elif response.status_code >= 400:
                    raise PlexClientError(
                        f"Client error: Plex returned status {response.status_code}"
                    )

                # Parse response
                if response.status_code == 200 or response.status_code == 201:
                    try:
                        if not response.text:
                            return {}

                        # Check content type
                        content_type = response.headers.get("content-type", "")

                        if "application/json" in content_type:
                            return response.json()
                        elif (
                            "application/xml" in content_type
                            or "text/xml" in content_type
                            or parse_xml
                        ):
                            # Parse XML to dict
                            root = ET.fromstring(response.text)
                            return self._parse_xml_to_dict(root)
                        else:
                            # Try JSON first, fall back to XML
                            try:
                                return response.json()
                            except json.JSONDecodeError:
                                try:
                                    root = ET.fromstring(response.text)
                                    return self._parse_xml_to_dict(root)
                                except ET.ParseError:
                                    raise PlexClientError(
                                        f"Invalid response format: {response.text[:100]}"
                                    )
                    except (json.JSONDecodeError, ET.ParseError) as e:
                        raise PlexClientError(f"Invalid response: {e}")

                return {}

            except HTTPError as e:
                last_error = e
                # Retry on connection errors
                if attempt < max_retries - 1:
                    continue
                raise PlexConnectionError(f"Connection failed: {e}")

        # If we get here, all retries failed
        if last_error:
            raise PlexConnectionError(
                f"Connection failed after {max_retries} attempts: {last_error}"
            )
        raise PlexConnectionError(f"Connection failed after {max_retries} attempts")

    # ========================================================================
    # System Operations
    # ========================================================================

    async def get_server_identity(self) -> Dict[str, Any]:
        """
        Get Plex server identity and information.

        Returns:
            Server identity data including version, platform, and capabilities
        """
        return await self._request("GET", "/")

    async def health_check(self) -> bool:
        """
        Check if Plex is accessible and responding.

        Returns:
            True if Plex is healthy, False otherwise
        """
        try:
            await self.get_server_identity()
            return True
        except Exception:
            return False

    # ========================================================================
    # Library Operations
    # ========================================================================

    async def get_libraries(self) -> List[Dict[str, Any]]:
        """
        Get all Plex library sections.

        Returns:
            List of library dictionaries with metadata
        """
        result = await self._request("GET", "library/sections")  # noqa: F841

        # Extract Directory list from MediaContainer
        if "MediaContainer" in result:
            directories = result["MediaContainer"].get("Directory", [])
            # Ensure it's a list
            if isinstance(directories, dict):
                return [directories]
            return directories if isinstance(directories, list) else []

        # Fallback: check for Directory key directly
        directories = result.get("Directory", [])
        if isinstance(directories, dict):
            return [directories]
        return directories if isinstance(directories, list) else []

    async def get_library_items(
        self,
        library_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all items in a specific library.

        Args:
            library_id: The library section ID
            limit: Maximum number of items to return (optional)
            offset: Number of items to skip (optional)

        Returns:
            List of media item dictionaries
        """
        params = {}
        if limit is not None:
            params["X-Plex-Container-Size"] = limit
        if offset is not None:
            params["X-Plex-Container-Start"] = offset

        result = await self._request(
            "GET", f"library/sections/{library_id}/all", **params
        )  # noqa: F841

        # Extract Metadata or Video list from MediaContainer
        if "MediaContainer" in result:
            # Try different possible keys
            for key in ["Metadata", "Video", "Directory", "Track"]:
                items = result["MediaContainer"].get(key, [])
                if items:
                    if isinstance(items, dict):
                        return [items]
                    return items if isinstance(items, list) else []

        return []

    async def get_recently_added(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recently added content across all libraries.

        Args:
            limit: Maximum number of items to return (default: None)

        Returns:
            List of recently added media items
        """
        params = {}
        if limit is not None:
            params["X-Plex-Container-Size"] = limit

        result = await self._request("GET", "library/recentlyAdded", **params)  # noqa: F841

        # Extract Metadata or Video list from MediaContainer
        if "MediaContainer" in result:
            for key in ["Metadata", "Video", "Directory", "Track"]:
                items = result["MediaContainer"].get(key, [])
                if items:
                    if isinstance(items, dict):
                        return [items]
                    return items if isinstance(items, list) else []

        return []

    async def get_on_deck(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get On Deck items (continue watching).

        Args:
            limit: Maximum number of items to return (default: None)

        Returns:
            List of On Deck media items
        """
        params = {}
        if limit is not None:
            params["X-Plex-Container-Size"] = limit

        result = await self._request("GET", "library/onDeck", **params)  # noqa: F841

        # Extract Video or Metadata list from MediaContainer
        if "MediaContainer" in result:
            for key in ["Video", "Metadata"]:
                items = result["MediaContainer"].get(key, [])
                if items:
                    if isinstance(items, dict):
                        return [items]
                    return items if isinstance(items, list) else []

        return []

    async def refresh_library(self, library_id: str) -> Dict[str, Any]:
        """
        Trigger a library refresh/scan.

        Args:
            library_id: The library section ID to refresh

        Returns:
            Response indicating success
        """
        await self._request("GET", f"library/sections/{library_id}/refresh")
        return {"success": True, "library_id": library_id}

    # ========================================================================
    # Playback and Session Operations
    # ========================================================================

    async def get_sessions(self) -> List[Dict[str, Any]]:
        """
        Get currently playing sessions.

        Returns:
            List of active session dictionaries
        """
        result = await self._request("GET", "status/sessions")  # noqa: F841

        # Extract Metadata or Video list from MediaContainer
        if "MediaContainer" in result:
            for key in ["Metadata", "Video", "Track"]:
                items = result["MediaContainer"].get(key, [])
                if items:
                    if isinstance(items, dict):
                        return [items]
                    return items if isinstance(items, list) else []

        return []

    async def get_history(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get watch history.

        Args:
            limit: Maximum number of items to return (optional)
            offset: Number of items to skip (optional)

        Returns:
            List of history records
        """
        params = {}
        if limit is not None:
            params["X-Plex-Container-Size"] = limit
        if offset is not None:
            params["X-Plex-Container-Start"] = offset

        result = await self._request("GET", "status/sessions/history/all", **params)  # noqa: F841

        # Extract Metadata or Video list from MediaContainer
        if "MediaContainer" in result:
            for key in ["Metadata", "Video", "Track"]:
                items = result["MediaContainer"].get(key, [])
                if items:
                    if isinstance(items, dict):
                        return [items]
                    return items if isinstance(items, list) else []

        return []

    # ========================================================================
    # Search Operations
    # ========================================================================

    async def search(
        self,
        query: str,
        limit: Optional[int] = None,
        section_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for content across libraries or within a specific library.

        Args:
            query: Search query string
            limit: Maximum number of results to return (optional)
            section_id: Limit search to specific library section (optional)

        Returns:
            List of search result dictionaries
        """
        params = {"query": query}

        if limit is not None:
            params["limit"] = limit

        if section_id is not None:
            params["sectionId"] = section_id

        result = await self._request("GET", "search", **params)  # noqa: F841

        # Extract Metadata or results from MediaContainer
        if "MediaContainer" in result:
            for key in ["Metadata", "Video", "Directory", "Track"]:
                items = result["MediaContainer"].get(key, [])
                if items:
                    if isinstance(items, dict):
                        return [items]
                    return items if isinstance(items, list) else []

        return []
