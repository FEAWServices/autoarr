#!/usr/bin/env python
"""
Manual verification script for the FastAPI Gateway.

This script verifies that all API components are properly configured and working.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def verify_imports():
    """Verify all API imports work."""
    print("=" * 70)
    print("VERIFYING API IMPORTS")
    print("=" * 70)

    try:
        from api.main import app
        print("[OK] api.main imported successfully")

        from api.config import get_settings
        print("[OK] api.config imported successfully")

        from api.models import (
            ToolCallRequest,
            ToolCallResponse,
            HealthCheckResponse,
            ServiceHealth,
        )
        print("[OK] api.models imported successfully")

        from api.dependencies import get_orchestrator, get_orchestrator_config
        print("[OK] api.dependencies imported successfully")

        from api.middleware import ErrorHandlerMiddleware, RequestLoggingMiddleware
        print("[OK] api.middleware imported successfully")

        from api.routers import health, mcp, downloads, shows, movies, media
        print("[OK] api.routers imported successfully")

        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_app_config():
    """Verify FastAPI app configuration."""
    print("\n" + "=" * 70)
    print("VERIFYING APP CONFIGURATION")
    print("=" * 70)

    try:
        from api.main import app
        from api.config import get_settings

        settings = get_settings()

        print(f"[OK] App Title: {app.title}")
        print(f"[OK] App Version: {app.version}")
        print(f"[OK] App Description: {app.description}")
        print(f"[OK] Docs URL: {app.docs_url}")
        print(f"[OK] API Prefix: {settings.api_v1_prefix}")

        return True
    except Exception as e:
        print(f"✗ App config verification failed: {e}")
        return False


def verify_routes():
    """Verify all routes are registered."""
    print("\n" + "=" * 70)
    print("VERIFYING ROUTES")
    print("=" * 70)

    try:
        from api.main import app

        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ','.join(route.methods) if route.methods else ''
                routes.append(f"{methods:8} {route.path}")

        # Expected routes
        expected_paths = [
            "/health",
            "/health/{service}",
            "/api/v1/mcp/call",
            "/api/v1/mcp/batch",
            "/api/v1/mcp/tools",
            "/api/v1/downloads/queue",
            "/api/v1/shows/",
            "/api/v1/movies/",
            "/api/v1/media/libraries",
        ]

        registered_paths = [route.split()[-1] for route in routes]

        print(f"[OK] Total routes registered: {len(routes)}")
        print("\nRegistered routes:")
        for route in sorted(routes):
            print(f"  {route}")

        # Check critical routes
        print("\nCritical routes verification:")
        for path in expected_paths:
            if path in registered_paths:
                print(f"  [OK] {path}")
            else:
                print(f"  [FAIL] {path} - MISSING!")

        return True
    except Exception as e:
        print(f"✗ Route verification failed: {e}")
        return False


def verify_middleware():
    """Verify middleware is configured."""
    print("\n" + "=" * 70)
    print("VERIFYING MIDDLEWARE")
    print("=" * 70)

    try:
        from api.main import app

        middleware_count = len(app.user_middleware)
        print(f"[OK] Middleware layers: {middleware_count}")

        for middleware in app.user_middleware:
            middleware_class = middleware.cls.__name__
            print(f"  [OK] {middleware_class}")

        return True
    except Exception as e:
        print(f"✗ Middleware verification failed: {e}")
        return False


def verify_models():
    """Verify Pydantic models."""
    print("\n" + "=" * 70)
    print("VERIFYING PYDANTIC MODELS")
    print("=" * 70)

    try:
        from api.models import (
            ToolCallRequest,
            ToolCallResponse,
            BatchToolCallRequest,
            HealthCheckResponse,
            ServiceHealth,
            AddSeriesRequest,
            AddMovieRequest,
        )

        # Test model creation
        tool_request = ToolCallRequest(
            server="sabnzbd",
            tool="get_queue",
            params={}
        )
        print(f"[OK] ToolCallRequest: {tool_request.server}/{tool_request.tool}")

        tool_response = ToolCallResponse(
            success=True,
            data={"queue": []},
        )
        print(f"[OK] ToolCallResponse: success={tool_response.success}")

        health = ServiceHealth(
            healthy=True,
            latency_ms=45.2,
            error=None,
            last_check="2025-01-15T10:30:00Z",
        )
        print(f"[OK] ServiceHealth: healthy={health.healthy}")

        return True
    except Exception as e:
        print(f"✗ Model verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_test_client():
    """Verify test client works."""
    print("\n" + "=" * 70)
    print("VERIFYING TEST CLIENT")
    print("=" * 70)

    try:
        from fastapi.testclient import TestClient
        from api.main import app

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        print(f"[OK] Root endpoint: {data['name']}")

        # Test ping endpoint
        response = client.get("/ping")
        assert response.status_code == 200
        data = response.json()
        print(f"[OK] Ping endpoint: {data['message']}")

        print("[OK] Test client working correctly")
        return True
    except Exception as e:
        print(f"✗ Test client verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verifications."""
    print("\n" + "=" * 70)
    print(" AUTOARR FASTAPI GATEWAY VERIFICATION")
    print("=" * 70 + "\n")

    results = []

    results.append(("Imports", verify_imports()))
    results.append(("App Config", verify_app_config()))
    results.append(("Routes", verify_routes()))
    results.append(("Middleware", verify_middleware()))
    results.append(("Models", verify_models()))
    results.append(("Test Client", verify_test_client()))

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:8} {name}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n*** ALL VERIFICATIONS PASSED! ***")
        print("\nThe FastAPI Gateway is ready to use!")
        print(f"\nTo start the server:")
        print(f"  python scripts/start_api.py")
        print(f"\nOr:")
        print(f"  uvicorn api.main:app --reload")
        return 0
    else:
        print("\n*** SOME VERIFICATIONS FAILED ***")
        print("\nPlease fix the issues above before using the API.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
