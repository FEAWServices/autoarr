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
API Path Contract Tests.

These tests verify that frontend API calls match backend route definitions.
This prevents mismatches between frontend and backend API paths that can
cause silent failures (404s, timeouts).

The test approach:
1. Parse the frontend TypeScript service files to extract API paths and methods
2. Compare against the registered FastAPI routes
3. Fail the test if any mismatch is found
"""

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Set

import pytest

from autoarr.api.main import app


class FrontendEndpoint(NamedTuple):
    """Represents an API endpoint called from the frontend."""

    path_pattern: str  # e.g., "/api/v1/requests/{id}/status"
    method: str  # e.g., "GET", "POST", "DELETE"
    source_file: str
    line_number: int


class BackendEndpoint(NamedTuple):
    """Represents an API endpoint defined in the backend."""

    path: str
    methods: Set[str]


def extract_frontend_endpoints(file_path: Path) -> List[FrontendEndpoint]:
    """
    Extract API endpoints from a TypeScript/JavaScript service file.

    Looks for fetch() calls and extracts the URL pattern and HTTP method.
    Supports multiple patterns:
    1. fetch(`${API_BASE_URL}/path`, { method: 'GET' })
    2. fetch(apiV1Url('/path'), { method: 'POST' })
    3. fetch(apiV1Url(`/path/${id}`), { method: 'DELETE' })
    """
    endpoints = []

    if not file_path.exists():
        return endpoints

    content = file_path.read_text()
    lines = content.split("\n")

    # Pattern to match fetch calls with template literals or string URLs
    # Matches: fetch(`${API_BASE_URL}/path`, { method: 'GET' })
    # Also matches: fetch(`${API_BASE_URL}/path/${variable}/action`, { method: 'POST' })
    fetch_pattern_template = re.compile(
        r"fetch\s*\(\s*`\$\{[^}]+\}(/[^`]+)`\s*,\s*\{[^}]*method:\s*['\"](\w+)['\"]",
        re.DOTALL,
    )

    # Pattern to match apiV1Url helper function calls
    # Matches: fetch(apiV1Url('/path'), { method: 'POST' })
    # Also matches: fetch(apiV1Url(`/path/${variable}`), { method: 'DELETE' })
    fetch_pattern_apiv1url = re.compile(
        r"fetch\s*\(\s*apiV1Url\s*\(\s*['\"`]([^'\"`)]+)['\"`]\s*\)\s*,\s*\{[^}]*method:\s*['\"](\w+)['\"]",
        re.DOTALL,
    )

    # Pattern for apiV1Url with template literals containing variables
    # Matches: fetch(apiV1Url(`/requests/${requestId}/status`), { method: 'GET' })
    fetch_pattern_apiv1url_template = re.compile(
        r"fetch\s*\(\s*apiV1Url\s*\(\s*`([^`]+)`\s*\)\s*,\s*\{[^}]*method:\s*['\"](\w+)['\"]",
        re.DOTALL,
    )

    # Pattern for GET requests without explicit method (defaults to GET)
    # Matches: fetch(apiV1Url('/chat/topics'));
    fetch_pattern_get_implicit = re.compile(
        r"fetch\s*\(\s*apiV1Url\s*\(\s*['\"`]([^'\"`)]+)['\"`]\s*\)\s*\)",
        re.DOTALL,
    )

    for i, line in enumerate(lines):
        # Look for fetch calls - may span multiple lines
        # Join current line with next few lines to catch multiline patterns
        chunk = "\n".join(lines[i : i + 8])

        # Try template literal pattern
        matches = fetch_pattern_template.findall(chunk)
        for path, method in matches:
            normalized_path = re.sub(r"\$\{(\w+)\}", r"{\1}", path)
            full_path = f"/api/v1{normalized_path}"
            endpoints.append(
                FrontendEndpoint(
                    path_pattern=full_path,
                    method=method.upper(),
                    source_file=str(file_path),
                    line_number=i + 1,
                )
            )

        # Try apiV1Url pattern with string literals
        matches = fetch_pattern_apiv1url.findall(chunk)
        for path, method in matches:
            normalized_path = re.sub(r"\$\{(\w+)\}", r"{\1}", path)
            full_path = f"/api/v1{normalized_path}"
            endpoints.append(
                FrontendEndpoint(
                    path_pattern=full_path,
                    method=method.upper(),
                    source_file=str(file_path),
                    line_number=i + 1,
                )
            )

        # Try apiV1Url pattern with template literals
        matches = fetch_pattern_apiv1url_template.findall(chunk)
        for path, method in matches:
            normalized_path = re.sub(r"\$\{(\w+)\}", r"{\1}", path)
            full_path = f"/api/v1{normalized_path}"
            endpoints.append(
                FrontendEndpoint(
                    path_pattern=full_path,
                    method=method.upper(),
                    source_file=str(file_path),
                    line_number=i + 1,
                )
            )

        # Try implicit GET pattern (no method specified)
        matches = fetch_pattern_get_implicit.findall(chunk)
        for path in matches:
            normalized_path = re.sub(r"\$\{(\w+)\}", r"{\1}", path)
            full_path = f"/api/v1{normalized_path}"
            endpoints.append(
                FrontendEndpoint(
                    path_pattern=full_path,
                    method="GET",
                    source_file=str(file_path),
                    line_number=i + 1,
                )
            )

    # Deduplicate (same endpoint might be matched multiple times due to overlap)
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = (ep.path_pattern, ep.method)
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)

    return unique_endpoints


def get_backend_endpoints() -> Dict[str, BackendEndpoint]:
    """
    Extract all registered API endpoints from the FastAPI app.

    Returns a dict mapping path patterns to BackendEndpoint objects.
    """
    endpoints = {}

    for route in app.routes:
        # Skip non-API routes (like static files, docs, etc.)
        if not hasattr(route, "path"):
            continue

        path = route.path

        # Get HTTP methods for this route
        methods = set()
        if hasattr(route, "methods"):
            methods = set(route.methods)

        # Normalize path parameters: convert {request_id} to {id} for comparison
        # This allows flexibility in parameter naming
        normalized_path = re.sub(r"\{[^}]+\}", "{id}", path)

        if normalized_path in endpoints:
            endpoints[normalized_path].methods.update(methods)
        else:
            endpoints[normalized_path] = BackendEndpoint(path=path, methods=methods)

    return endpoints


def normalize_path_for_comparison(path: str) -> str:
    """
    Normalize a path for comparison by replacing all path parameters with {id}.
    """
    return re.sub(r"\{[^}]+\}", "{id}", path)


class TestAPIPathContract:
    """Tests to verify frontend API calls match backend routes."""

    @pytest.fixture
    def frontend_service_files(self) -> List[Path]:
        """List of frontend service files that make API calls."""
        ui_services_dir = Path(__file__).parents[4] / "ui" / "src" / "services"
        return list(ui_services_dir.glob("*.ts"))

    @pytest.fixture
    def backend_endpoints(self) -> Dict[str, BackendEndpoint]:
        """Get all backend endpoints."""
        return get_backend_endpoints()

    def test_chat_service_endpoints_exist(self, backend_endpoints):
        """
        Verify all endpoints called by chat.ts exist in the backend.

        This is the critical test that would have caught the /request vs /requests bug.
        """
        # Path from test file: autoarr/tests/unit/api/test_api_path_contract.py
        # Need to go up 3 levels to autoarr/, then into ui/src/services/
        chat_service = Path(__file__).parents[3] / "ui" / "src" / "services" / "chat.ts"
        frontend_endpoints = extract_frontend_endpoints(chat_service)

        # Should have found at least some endpoints
        assert len(frontend_endpoints) > 0, (
            f"No endpoints found in {chat_service}. "
            "Check if the file exists and has fetch() calls."
        )

        missing_endpoints = []

        for fe_endpoint in frontend_endpoints:
            fe_normalized = normalize_path_for_comparison(fe_endpoint.path_pattern)

            # Find matching backend endpoint
            found = False
            for be_normalized, be_endpoint in backend_endpoints.items():
                be_normalized_compare = normalize_path_for_comparison(be_normalized)
                if fe_normalized == be_normalized_compare:
                    # Check method matches
                    if fe_endpoint.method in be_endpoint.methods:
                        found = True
                        break

            if not found:
                missing_endpoints.append(fe_endpoint)

        if missing_endpoints:
            error_msg = "Frontend calls endpoints that don't exist in backend:\n"
            for ep in missing_endpoints:
                error_msg += (
                    f"  - {ep.method} {ep.path_pattern}\n"
                    f"    (from {ep.source_file}:{ep.line_number})\n"
                )
            error_msg += "\nAvailable backend endpoints:\n"
            for path, ep in sorted(backend_endpoints.items()):
                error_msg += f"  - {', '.join(sorted(ep.methods))} {ep.path}\n"

            pytest.fail(error_msg)

    def test_requests_router_paths(self, backend_endpoints):
        """
        Verify the requests router has expected endpoints.

        This explicitly tests the paths that were misconfigured.
        """
        expected_paths = [
            ("/api/v1/requests/content", "POST"),
            ("/api/v1/requests/{id}/status", "GET"),
            ("/api/v1/requests/{id}/confirm", "POST"),
            ("/api/v1/requests/{id}", "DELETE"),
        ]

        for expected_path, expected_method in expected_paths:
            normalized = normalize_path_for_comparison(expected_path)
            found = False

            for be_path, be_endpoint in backend_endpoints.items():
                be_normalized = normalize_path_for_comparison(be_path)
                if be_normalized == normalized and expected_method in be_endpoint.methods:
                    found = True
                    break

            assert found, (
                f"Expected endpoint {expected_method} {expected_path} not found.\n"
                f"Available endpoints:\n"
                + "\n".join(
                    f"  {', '.join(sorted(ep.methods))} {ep.path}"
                    for ep in backend_endpoints.values()
                )
            )

    def test_settings_service_endpoints_exist(self, backend_endpoints):
        """Verify settings service endpoints exist."""
        settings_service = Path(__file__).parents[3] / "ui" / "src" / "services" / "settings.ts"

        if not settings_service.exists():
            pytest.skip("settings.ts not found")

        frontend_endpoints = extract_frontend_endpoints(settings_service)

        for fe_endpoint in frontend_endpoints:
            fe_normalized = normalize_path_for_comparison(fe_endpoint.path_pattern)

            found = False
            for be_normalized, be_endpoint in backend_endpoints.items():
                be_normalized_compare = normalize_path_for_comparison(be_normalized)
                if fe_normalized == be_normalized_compare:
                    if fe_endpoint.method in be_endpoint.methods:
                        found = True
                        break

            assert found, (
                f"Frontend endpoint {fe_endpoint.method} {fe_endpoint.path_pattern} "
                f"not found in backend (from {fe_endpoint.source_file}:{fe_endpoint.line_number})"
            )

    def test_no_singular_request_endpoint(self, backend_endpoints):
        """
        Explicitly test that there is no singular '/request' endpoint.

        This is a regression test for the bug where frontend used '/request'
        but backend used '/requests'.
        """
        for path in backend_endpoints.keys():
            assert "/request/" not in path or "/requests/" in path, (
                f"Found singular '/request/' in path: {path}. "
                "Use plural '/requests/' for consistency."
            )

    def test_frontend_uses_plural_requests(self):
        """
        Verify frontend chat service uses '/requests' (plural) not '/request'.

        Direct regex check on the source file as a belt-and-suspenders approach.
        """
        chat_service = Path(__file__).parents[3] / "ui" / "src" / "services" / "chat.ts"

        if not chat_service.exists():
            pytest.skip("chat.ts not found")

        content = chat_service.read_text()

        # Check for incorrect singular form (but not as part of 'requests')
        # Match /request/ but not /requests/
        singular_pattern = re.compile(r"/request/(?!s)")
        matches = singular_pattern.findall(content)

        assert len(matches) == 0, (
            f"Found {len(matches)} uses of '/request/' (singular) in chat.ts. "
            "Use '/requests/' (plural) to match backend routes."
        )


class TestHealthEndpointContract:
    """Verify health endpoint is accessible for ConnectionStatus component."""

    def test_health_endpoint_exists(self):
        """Verify /health endpoint exists for frontend connection checks."""
        backend_endpoints = get_backend_endpoints()

        found = False
        for path, endpoint in backend_endpoints.items():
            if path == "/health" and "GET" in endpoint.methods:
                found = True
                break

        assert found, (
            "Health endpoint GET /health not found. "
            "This is required for the ConnectionStatus component."
        )


class TestLogsEndpointContract:
    """Verify logs endpoints match what the Logs page expects."""

    def test_logs_endpoints_exist(self):
        """Verify all logs endpoints exist."""
        backend_endpoints = get_backend_endpoints()

        expected_endpoints = [
            ("/api/v1/logs", "GET"),
            ("/api/v1/logs", "DELETE"),
            ("/api/v1/logs/level", "GET"),
            ("/api/v1/logs/level", "PUT"),
        ]

        for expected_path, expected_method in expected_endpoints:
            found = False
            for path, endpoint in backend_endpoints.items():
                if path == expected_path and expected_method in endpoint.methods:
                    found = True
                    break

            assert found, (
                f"Expected endpoint {expected_method} {expected_path} not found. "
                "This is required for the Logs page."
            )
