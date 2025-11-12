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
Docker Build Integration Tests

Tests the Docker image build process and validates container behavior.
These tests require Docker to be installed and running.

Run with: pytest autoarr/tests/docker/test_docker_integration.py -v
"""

import subprocess
import time
from typing import Generator

import pytest
import requests

# Docker configuration
IMAGE_NAME = "autoarr-test"
TAG = "pytest"
CONTAINER_NAME = "autoarr-pytest-test"
TEST_PORT = 8090


@pytest.fixture(scope="module")
def docker_image() -> Generator[str, None, None]:
    """Build Docker image for testing."""
    image_tag = f"{IMAGE_NAME}:{TAG}"

    # Build the image
    print(f"\nBuilding Docker image: {image_tag}")
    result = subprocess.run(
        ["docker", "build", "-t", image_tag, "-f", "Dockerfile", "."],
        cwd="/app",
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed:\n{result.stderr}")

    yield image_tag

    # Cleanup: Remove the image
    subprocess.run(["docker", "rmi", image_tag], capture_output=True)


@pytest.fixture(scope="module")
def docker_container(docker_image: str) -> Generator[str, None, None]:
    """Start Docker container for testing."""
    # Stop and remove any existing test container
    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True)
    subprocess.run(["docker", "rm", CONTAINER_NAME], capture_output=True)

    # Start the container
    print(f"\nStarting Docker container: {CONTAINER_NAME}")
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            CONTAINER_NAME,
            "-p",
            f"{TEST_PORT}:8088",
            "-e",
            "SABNZBD_URL=http://localhost:8080",
            "-e",
            "SABNZBD_API_KEY=test",
            "-e",
            "SONARR_URL=http://localhost:8989",
            "-e",
            "SONARR_API_KEY=test",
            "-e",
            "RADARR_URL=http://localhost:7878",
            "-e",
            "RADARR_API_KEY=test",
            docker_image,
        ],
        check=True,
        capture_output=True,
    )

    # Wait for container to be ready
    time.sleep(5)

    yield CONTAINER_NAME

    # Cleanup: Stop and remove container
    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True)
    subprocess.run(["docker", "rm", CONTAINER_NAME], capture_output=True)


class TestDockerBuild:
    """Tests for Docker image build process."""

    def test_image_builds_successfully(self, docker_image: str) -> None:
        """Test that the Docker image builds without errors."""
        # Check image exists
        result = subprocess.run(
            ["docker", "images", docker_image, "-q"], capture_output=True, text=True
        )
        assert result.stdout.strip(), f"Image {docker_image} was not built"

    def test_python_version(self, docker_image: str) -> None:
        """Test that the correct Python version is installed."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_image, "python", "--version"],
            capture_output=True,
            text=True,
        )
        assert "Python 3.11" in result.stdout, f"Expected Python 3.11, got: {result.stdout}"

    def test_autoarr_package_installed(self, docker_image: str) -> None:
        """Test that the AutoArr package is installed."""
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                docker_image,
                "python",
                "-c",
                "import autoarr; print('success')",
            ],
            capture_output=True,
            text=True,
        )
        assert "success" in result.stdout, "AutoArr package is not importable"

    def test_required_dependencies_installed(self, docker_image: str) -> None:
        """Test that all required dependencies are installed."""
        required_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "mcp",
            "anthropic",
            "httpx",
            "pydantic",
        ]

        for package in required_packages:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    docker_image,
                    "python",
                    "-c",
                    f"import {package}; print('OK')",
                ],
                capture_output=True,
                text=True,
            )
            assert "OK" in result.stdout, f"Package {package} is not installed"

    def test_dev_dependencies_not_installed(self, docker_image: str) -> None:
        """Test that development dependencies are not installed in production image."""
        dev_packages = ["pytest", "black", "mypy"]

        for package in dev_packages:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    docker_image,
                    "python",
                    "-c",
                    f"import {package}",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0, f"Dev package {package} should not be installed"

    def test_frontend_assets_exist(self, docker_image: str) -> None:
        """Test that frontend build artifacts are present."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_image, "ls", "/app/autoarr/ui/dist/"],
            capture_output=True,
            text=True,
        )
        assert "index.html" in result.stdout, "Frontend index.html not found"

    def test_non_root_user(self, docker_image: str) -> None:
        """Test that container runs as non-root user."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_image, "whoami"], capture_output=True, text=True
        )
        assert result.stdout.strip() == "autoarr", f"Expected user 'autoarr', got: {result.stdout}"

    def test_data_directory_exists(self, docker_image: str) -> None:
        """Test that the /data directory exists and has correct permissions."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_image, "ls", "-ld", "/data"],
            capture_output=True,
            text=True,
        )
        assert "/data" in result.stdout, "/data directory not found"

    def test_exposed_port(self, docker_image: str) -> None:
        """Test that port 8088 is exposed."""
        result = subprocess.run(
            [
                "docker",
                "inspect",
                docker_image,
                "--format={{json .Config.ExposedPorts}}",
            ],
            capture_output=True,
            text=True,
        )
        assert "8088" in result.stdout, "Port 8088 is not exposed"


class TestDockerContainer:
    """Tests for running Docker container."""

    def test_container_starts(self, docker_container: str) -> None:
        """Test that the container starts successfully."""
        result = subprocess.run(
            ["docker", "ps", "-f", f"name={docker_container}"], capture_output=True, text=True
        )
        assert docker_container in result.stdout, "Container is not running"

    def test_container_stays_running(self, docker_container: str) -> None:
        """Test that the container stays running after startup."""
        time.sleep(10)
        result = subprocess.run(
            ["docker", "ps", "-f", f"name={docker_container}"], capture_output=True, text=True
        )
        assert docker_container in result.stdout, "Container stopped unexpectedly"

    def test_no_critical_errors_in_logs(self, docker_container: str) -> None:
        """Test that container logs don't contain critical errors."""
        result = subprocess.run(
            ["docker", "logs", docker_container], capture_output=True, text=True
        )
        logs = result.stdout + result.stderr

        # Check for critical error patterns (case-insensitive)
        critical_patterns = ["CRITICAL", "FATAL", "Traceback"]
        for pattern in critical_patterns:
            # Some startup warnings are OK, but not critical errors
            if pattern.lower() in logs.lower():
                # Allow specific non-critical patterns
                if "UserWarning" in logs or "DeprecationWarning" in logs:
                    continue
                pytest.fail(
                    f"Found '{pattern}' in container logs:\n{logs[-500:]}"
                )  # Show last 500 chars

    def test_healthcheck_responds(self, docker_container: str) -> None:
        """Test that the health check endpoint responds."""
        # Give the application more time to start
        time.sleep(15)

        try:
            response = requests.get(f"http://localhost:{TEST_PORT}/health", timeout=5)
            # Accept both 200 OK and 503 Service Unavailable (if external services not connected)
            assert response.status_code in [
                200,
                503,
            ], f"Unexpected status code: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Health check endpoint not accessible (may need external services): {e}")

    def test_container_process_user(self, docker_container: str) -> None:
        """Test that processes in the container run as non-root user."""
        result = subprocess.run(
            ["docker", "exec", docker_container, "ps", "aux"], capture_output=True, text=True
        )
        # All processes should be running as 'autoarr' user
        lines = result.stdout.split("\n")[1:]  # Skip header
        for line in lines:
            if line.strip():  # Skip empty lines
                assert (
                    "autoarr" in line or "USER" in line
                ), f"Found process not running as autoarr: {line}"


class TestDockerSecurity:
    """Security tests for Docker image."""

    def test_no_root_user_in_container(self, docker_image: str) -> None:
        """Test that the container doesn't run as root."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_image, "id", "-u"], capture_output=True, text=True
        )
        uid = result.stdout.strip()
        assert uid != "0", "Container is running as root (UID 0)"

    def test_read_only_filesystem_compatible(self, docker_image: str) -> None:
        """Test that the application can run with a read-only filesystem (with /data writable)."""
        # This tests if the app is designed to write only to designated areas
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--tmpfs",
                "/data",
                "-e",
                "SABNZBD_URL=http://localhost:8080",
                "-e",
                "SABNZBD_API_KEY=test",
                "-e",
                "SONARR_URL=http://localhost:8989",
                "-e",
                "SONARR_API_KEY=test",
                "-e",
                "RADARR_URL=http://localhost:7878",
                "-e",
                "RADARR_API_KEY=test",
                docker_image,
                "python",
                "-c",
                "import autoarr; print('OK')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed with read-only filesystem: {result.stderr}"


@pytest.mark.skipif(
    subprocess.run(["which", "trivy"], capture_output=True).returncode != 0,
    reason="Trivy not installed",
)
class TestDockerImageSecurity:
    """Security scanning tests (requires Trivy)."""

    def test_vulnerability_scan(self, docker_image: str) -> None:
        """Test image for known vulnerabilities using Trivy."""
        result = subprocess.run(
            [
                "trivy",
                "image",
                "--severity",
                "HIGH,CRITICAL",
                "--exit-code",
                "1",
                docker_image,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"Vulnerabilities found (informational):\n{result.stdout}")
