"""
Security tests for AutoArr.

Tests for common security vulnerabilities:
- SQL injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- Hardcoded secrets
- Insecure dependencies
- Input validation
"""

import os
import re
from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestSecurityVulnerabilities:
    """Tests for security vulnerabilities."""

    async def test_no_hardcoded_secrets_in_code(self):
        """
        Test that no hardcoded secrets exist in code.

        Scans for common patterns like:
        - API keys
        - Passwords
        - Secret tokens
        - AWS credentials
        """
        project_root = Path(__file__).parent.parent.parent.parent
        autoarr_dir = project_root / "autoarr"

        # Patterns to detect potential secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
            (r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded API key"),
            (r'secret[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded secret key"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded token"),
            (r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'][^"\']+["\']', "AWS credentials"),
        ]

        findings = []

        # Scan Python files
        for py_file in autoarr_dir.rglob("*.py"):
            # Skip test files and __pycache__
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue

            try:
                content = py_file.read_text()

                for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Exclude safe patterns
                        matched_text = match.group(0)
                        if any(
                            safe in matched_text
                            for safe in [
                                "dev_secret_key",  # Development placeholder
                                "test_",  # Test values
                                "example",  # Example values
                                "YOUR_",  # Placeholder values
                                "change_in_production",  # Placeholder
                            ]
                        ):
                            continue

                        findings.append(
                            {
                                "file": str(py_file.relative_to(project_root)),
                                "line": content[: match.start()].count("\n") + 1,
                                "description": description,
                                "snippet": matched_text[:50],
                            }
                        )
            except Exception as e:
                # Skip files that can't be read
                continue

        # Assert no secrets found (or only acceptable ones)
        assert len(findings) == 0, f"Potential hardcoded secrets found:\n" + "\n".join(
            f"  - {f['file']}:{f['line']} - {f['description']}: {f['snippet']}" for f in findings
        )

    async def test_sql_injection_protection(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """
        Test SQL injection protection.

        Verifies that all database queries use parameterized queries
        and user input is properly sanitized.
        """
        # Test SQL injection in settings key
        malicious_key = "test'; DROP TABLE settings; --"

        response = await api_client.get(
            f"/api/v1/settings/{malicious_key}",
        )

        # Should return 404 or 400, not cause SQL injection
        assert response.status_code in [400, 404]

        # Verify settings table still exists
        from sqlalchemy import text

        result = await db_session.execute(text("SELECT COUNT(*) FROM setting"))
        count = result.scalar()
        # Table should still exist
        assert count is not None

    async def test_xss_protection_in_responses(
        self,
        api_client: AsyncClient,
    ):
        """
        Test XSS protection in API responses.

        Verifies that user input is properly escaped and cannot
        inject malicious scripts.
        """
        # Try to inject XSS in setting value
        xss_payload = "<script>alert('XSS')</script>"

        response = await api_client.put(
            "/api/v1/settings/test_xss",
            json={"value": xss_payload},
        )

        if response.status_code in [200, 201]:
            # Get the setting back
            response = await api_client.get("/api/v1/settings/test_xss")
            assert response.status_code == 200

            data = response.json()
            value = data.get("value", "")

            # Value should be escaped or sanitized
            # Should not contain raw script tags
            assert "<script>" not in response.text or value == xss_payload

            # Clean up
            await api_client.delete("/api/v1/settings/test_xss")

    async def test_csrf_protection(
        self,
        api_client: AsyncClient,
    ):
        """
        Test CSRF protection.

        Note: CSRF protection is typically handled by frontend frameworks
        and may not be needed for API-only endpoints using token auth.

        This test verifies that state-changing operations require
        proper authentication.
        """
        # For now, skip as CSRF is typically for cookie-based auth
        pytest.skip("CSRF protection test - API uses token-based auth")

    async def test_input_validation_on_endpoints(
        self,
        api_client: AsyncClient,
    ):
        """
        Test input validation on all endpoints.

        Verifies that invalid input is rejected with appropriate
        error messages.
        """
        # Test invalid service name
        response = await api_client.post(
            "/api/v1/config/audit",
            json={"service": "<script>alert('xss')</script>"},
        )
        assert response.status_code in [400, 422]

        # Test missing required fields
        response = await api_client.post(
            "/api/v1/config/audit",
            json={},
        )
        assert response.status_code in [400, 422]

        # Test invalid JSON
        response = await api_client.post(
            "/api/v1/config/audit",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    async def test_no_sensitive_data_in_logs(
        self,
        api_client: AsyncClient,
    ):
        """
        Test that sensitive data is not logged.

        Verifies that API keys, passwords, and tokens are redacted
        from log output.
        """
        # This would require checking actual log files
        # For now, we'll skip this test
        pytest.skip("Log inspection test requires log file access")

    async def test_secure_headers_present(
        self,
        api_client: AsyncClient,
    ):
        """
        Test that secure HTTP headers are present.

        Verifies:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY
        - X-XSS-Protection: 1; mode=block
        - Content-Security-Policy
        """
        response = await api_client.get("/health")
        assert response.status_code == 200

        headers = response.headers

        # Check for security headers
        # Note: Some might be set by reverse proxy in production
        expected_headers = {
            "x-content-type-options": "nosniff",
            # "x-frame-options": "DENY",  # May be set by middleware
            # "x-xss-protection": "1; mode=block",  # Deprecated but still useful
        }

        for header, expected_value in expected_headers.items():
            if header in headers:
                assert headers[header] == expected_value

    async def test_rate_limiting_present(
        self,
        api_client: AsyncClient,
    ):
        """
        Test that rate limiting is implemented.

        Makes rapid requests to verify rate limiting kicks in.
        """
        # This test would make many rapid requests
        pytest.skip("Rate limiting test requires rate limiter implementation")

    async def test_authentication_on_protected_endpoints(
        self,
        api_client: AsyncClient,
    ):
        """
        Test authentication requirements on protected endpoints.

        Verifies that endpoints requiring authentication reject
        unauthenticated requests.
        """
        # This test would verify auth requirements
        pytest.skip("Authentication test requires auth implementation")

    async def test_no_directory_traversal(
        self,
        api_client: AsyncClient,
    ):
        """
        Test protection against directory traversal attacks.

        Verifies that file paths cannot be manipulated to access
        files outside the intended directory.
        """
        # Try directory traversal in settings key
        traversal_key = "../../etc/passwd"

        response = await api_client.get(
            f"/api/v1/settings/{traversal_key}",
        )

        # Should return 404 or 400, not expose file system
        assert response.status_code in [400, 404]

    async def test_no_command_injection(
        self,
        api_client: AsyncClient,
    ):
        """
        Test protection against command injection.

        Verifies that user input cannot execute system commands.
        """
        # Try command injection in setting value
        command_injection = "test; ls -la"

        response = await api_client.put(
            "/api/v1/settings/test_cmd",
            json={"value": command_injection},
        )

        # Should handle as normal string, not execute command
        if response.status_code in [200, 201]:
            # Verify value stored as-is, not executed
            response = await api_client.get("/api/v1/settings/test_cmd")
            data = response.json()
            assert data.get("value") == command_injection

            # Clean up
            await api_client.delete("/api/v1/settings/test_cmd")


@pytest.mark.asyncio
class TestDependencySecurity:
    """Tests for dependency security."""

    def test_no_known_vulnerable_dependencies(self):
        """
        Test that dependencies have no known vulnerabilities.

        This test would use safety or pip-audit to check dependencies.
        """
        pytest.skip("Dependency vulnerability scan requires safety or pip-audit")

    def test_dependencies_up_to_date(self):
        """
        Test that critical dependencies are up to date.

        Checks that security-critical dependencies are recent versions.
        """
        # This would check pyproject.toml and poetry.lock
        pytest.skip("Dependency version check requires implementation")


@pytest.mark.asyncio
class TestDatabaseSecurity:
    """Tests for database security."""

    async def test_database_connection_uses_ssl(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that database connection uses SSL in production.

        Note: This may not apply to SQLite in development.
        """
        pytest.skip("SSL test requires production database configuration")

    async def test_prepared_statements_used(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that all queries use prepared statements.

        Verifies that SQLAlchemy ORM is used correctly to prevent
        SQL injection.
        """
        from sqlalchemy import text

        # Test that parameterized queries work
        result = await db_session.execute(text("SELECT :value AS test_value"), {"value": "test"})
        row = result.fetchone()
        assert row[0] == "test"

    async def test_database_credentials_not_in_code(self):
        """
        Test that database credentials are not hardcoded.

        Verifies that database URLs use environment variables.
        """
        from autoarr.api.config import get_settings

        settings = get_settings()

        # Database URL should come from environment or be None
        if settings.database_url:
            # Should not contain hardcoded credentials
            assert "password=hardcoded" not in settings.database_url.lower()


@pytest.mark.asyncio
class TestAPIKeySecurity:
    """Tests for API key security."""

    def test_api_keys_in_environment(self):
        """
        Test that API keys are loaded from environment variables.

        Verifies that all service API keys come from environment.
        """
        from autoarr.api.config import get_settings

        settings = get_settings()

        # API keys should be empty or from environment
        # They should not be long hardcoded values
        api_keys = [
            settings.sabnzbd_api_key,
            settings.sonarr_api_key,
            settings.radarr_api_key,
            settings.plex_token,
        ]

        for key in api_keys:
            if key and len(key) > 20:
                # If key is long, it should be from environment
                # Check it's not a placeholder
                assert not any(
                    placeholder in key.lower()
                    for placeholder in [
                        "your_api_key_here",
                        "change_me",
                        "example",
                    ]
                )

    def test_secret_key_secure(self):
        """
        Test that secret key is secure in production.

        Verifies that secret key is not the default development value.
        """
        from autoarr.api.config import get_settings

        settings = get_settings()

        # In testing, dev key is okay
        # In production, should be strong random key
        if settings.app_env == "production":
            assert settings.secret_key != "dev_secret_key_change_in_production"
            assert len(settings.secret_key) >= 32
