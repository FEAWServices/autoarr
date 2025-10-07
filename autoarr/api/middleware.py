"""
Custom middleware for the FastAPI Gateway.

This module provides middleware for error handling, logging, and request processing.
"""

import logging
import time
from datetime import datetime
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from shared.core.exceptions import (
    CircuitBreakerOpenError,
    MCPConnectionError,
    MCPOrchestratorError,
    MCPTimeoutError,
    MCPToolError,
)
from starlette.middleware.base import BaseHTTPMiddleware

from .models import ErrorResponse

# Configure logger
logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling MCP-specific errors and returning proper responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any errors.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response (either from handler or error response)
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_error(request, exc)

    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle an error and return appropriate JSON response.

        Args:
            request: The incoming request
            exc: The exception that was raised

        Returns:
            JSONResponse: Error response
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        path = str(request.url.path)

        # Handle MCP-specific errors
        if isinstance(exc, MCPConnectionError):
            error_response = ErrorResponse(
                error="Service Unavailable",
                detail=str(exc),
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        elif isinstance(exc, MCPTimeoutError):
            error_response = ErrorResponse(
                error="Request Timeout",
                detail=str(exc),
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_504_GATEWAY_TIMEOUT

        elif isinstance(exc, CircuitBreakerOpenError):
            error_response = ErrorResponse(
                error="Service Temporarily Unavailable",
                detail=str(exc),
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        elif isinstance(exc, MCPToolError):
            error_response = ErrorResponse(
                error="Tool Execution Failed",
                detail=str(exc),
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_400_BAD_REQUEST

        elif isinstance(exc, MCPOrchestratorError):
            error_response = ErrorResponse(
                error="Orchestrator Error",
                detail=str(exc),
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        elif isinstance(exc, ValueError):
            error_response = ErrorResponse(
                error="Invalid Request",
                detail=str(exc),
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_400_BAD_REQUEST

        else:
            # Generic error handling
            logger.exception("Unhandled error in request processing")
            error_response = ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred",
                timestamp=timestamp,
                path=path,
            )
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(),
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging incoming requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the handler
        """
        # Log request
        request_id = request.headers.get("X-Request-ID", "N/A")
        logger.info(f"Request started: {request.method} {request.url.path} [ID: {request_id}]")

        # Track timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[Status: {response.status_code}] [Duration: {duration:.3f}s] [ID: {request_id}]"
        )

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response


async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """
    Add security headers to all responses.

    Args:
        request: The incoming request
        call_next: The next middleware or route handler

    Returns:
        Response: The response with security headers added
    """
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response
