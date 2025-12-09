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
WebSocket connection load testing.

Tests WebSocket connection handling, message throughput, and connection resilience.

To run:
    poetry run locust -f websocket_load_test.py --host=http://localhost:8088
"""

import json
import logging
import os
import time
from typing import Any, Dict

import websocket
from locust import User, between, task

logger = logging.getLogger(__name__)


# ============================================================================
# WebSocket Client with Locust Integration
# ============================================================================


class WebSocketClient:
    """Wrapper around websocket client for Locust integration."""

    def __init__(self, base_url: str) -> None:
        """Initialize WebSocket client."""
        # Convert HTTP URL to WebSocket URL
        if base_url.startswith("http://"):
            ws_url = base_url.replace("http://", "ws://")
        elif base_url.startswith("https://"):
            ws_url = base_url.replace("https://", "wss://")
        else:
            ws_url = f"ws://{base_url}"

        self.ws_url = ws_url
        self.endpoint = "/api/v1/ws"
        self.ws: websocket.WebSocket | None = None
        self.connected = False
        self.message_count = 0
        self.connection_time_ms = 0.0

    def connect(self) -> bool:
        """
        Connect to WebSocket endpoint.

        Returns:
            bool: True if connection successful
        """
        try:
            start_time = time.time()
            full_url = f"{self.ws_url}{self.endpoint}"

            self.ws = websocket.create_connection(
                full_url,
                timeout=10,
                ping_interval=30,
                ping_payload="ping",
            )

            self.connection_time_ms = (time.time() - start_time) * 1000
            self.connected = True
            logger.debug(f"WebSocket connected: {full_url} ({self.connection_time_ms:.2f}ms)")

            return True

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected = False
            return False

    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send message to WebSocket.

        Args:
            message: Message dictionary

        Returns:
            bool: True if send successful
        """
        if not self.connected or not self.ws:
            logger.error("WebSocket not connected")
            return False

        try:
            self.ws.send(json.dumps(message))
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            self.connected = False
            return False

    def receive_message(self, timeout: int = 5) -> Dict[str, Any] | None:
        """
        Receive message from WebSocket.

        Args:
            timeout: Receive timeout in seconds

        Returns:
            Received message or None if timeout
        """
        if not self.connected or not self.ws:
            return None

        try:
            self.ws.settimeout(timeout)
            message = self.ws.recv()
            return json.loads(message)
        except websocket.WebSocketTimeoutException:
            return None
        except Exception as e:
            logger.error(f"Failed to receive WebSocket message: {e}")
            self.connected = False
            return None

    def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
        self.connected = False


# ============================================================================
# WebSocket User Class
# ============================================================================


class WebSocketUser(User):
    """User that maintains WebSocket connection."""

    wait_time = between(5, 15)

    def __init__(self, environment: Any) -> None:
        """Initialize WebSocket user."""
        super().__init__(environment)

        # Get base URL from environment
        base_url = os.getenv("AUTOARR_BASE_URL", "http://localhost:8088")
        self.ws_client = WebSocketClient(base_url)

    def on_start(self) -> None:
        """Initialize user session - establish WebSocket connection."""
        logger.info("WebSocketUser starting - establishing connection")

        # Attempt connection with retries
        max_retries = 3
        for attempt in range(max_retries):
            if self.ws_client.connect():
                logger.info(f"WebSocket connected successfully on attempt {attempt + 1}")
                break
            else:
                logger.warning(
                    f"WebSocket connection attempt {attempt + 1} failed, " f"retrying..."
                )
                if attempt < max_retries - 1:
                    time.sleep(1)

    def on_stop(self) -> None:
        """Clean up user session."""
        logger.info("WebSocketUser stopping - closing connection")
        self.ws_client.disconnect()

    @task(10)
    def keep_connection_alive(self) -> None:
        """Keep connection alive by receiving server messages."""
        if not self.ws_client.connected:
            logger.warning("WebSocket disconnected, attempting to reconnect")
            self.ws_client.connect()
            return

        start_time = time.time()
        try:
            # Try to receive message with short timeout
            message = self.ws_client.receive_message(timeout=2)
            receive_time_ms = (time.time() - start_time) * 1000

            if message:
                logger.debug(f"Received message: {message}")
                # Record successful receive
                self.environment.events.request.fire(
                    request_type="websocket",
                    name="receive_message",
                    response_time=receive_time_ms,
                    response_length=len(json.dumps(message)),
                    exception=None,
                    context={},
                )
            else:
                # Timeout is normal if no messages being sent
                logger.debug("Receive timeout (no messages)")

        except Exception as e:
            logger.error(f"Error in keep_connection_alive: {e}")
            self.ws_client.disconnect()

    @task(5)
    def send_test_message(self) -> None:
        """Send test message to server."""
        if not self.ws_client.connected:
            logger.warning("WebSocket disconnected, skipping send")
            return

        message = {
            "type": "test",
            "message": "Test message from load test",
            "timestamp": time.time(),
        }

        start_time = time.time()
        try:
            if self.ws_client.send_message(message):
                send_time_ms = (time.time() - start_time) * 1000
                self.environment.events.request.fire(
                    request_type="websocket",
                    name="send_message",
                    response_time=send_time_ms,
                    response_length=len(json.dumps(message)),
                    exception=None,
                    context={},
                )
            else:
                self.environment.events.request.fire(
                    request_type="websocket",
                    name="send_message",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=0,
                    exception=Exception("Failed to send message"),
                    context={},
                )
        except Exception as e:
            self.environment.events.request.fire(
                request_type="websocket",
                name="send_message",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context={},
            )

    @task(3)
    def connection_stability_check(self) -> None:
        """Check if connection is still stable."""
        is_connected = self.ws_client.connected and (
            self.ws_client.ws is not None and self.ws_client.ws.connected is not False
        )

        # Record connectivity check
        self.environment.events.request.fire(
            request_type="websocket",
            name="connection_check",
            response_time=1.0,  # Instant check
            response_length=0,
            exception=None if is_connected else Exception("Connection lost"),
            context={"connected": is_connected},
        )


# ============================================================================
# WebSocket Stress Test User
# ============================================================================


class WebSocketStressUser(User):
    """User that stresses WebSocket with rapid messages."""

    wait_time = between(0.1, 0.5)  # Very short wait time

    def __init__(self, environment: Any) -> None:
        """Initialize stress test user."""
        super().__init__(environment)
        base_url = os.getenv("AUTOARR_BASE_URL", "http://localhost:8088")
        self.ws_client = WebSocketClient(base_url)

    def on_start(self) -> None:
        """Connect on start."""
        self.ws_client.connect()

    def on_stop(self) -> None:
        """Disconnect on stop."""
        self.ws_client.disconnect()

    @task
    def stress_with_rapid_messages(self) -> None:
        """Send rapid messages to stress the connection."""
        if not self.ws_client.connected:
            if not self.ws_client.connect():
                return

        message = {
            "type": "stress_test",
            "message": "Stress test message",
            "sequence": self.ws_client.message_count,
        }

        start_time = time.time()
        try:
            self.ws_client.send_message(message)
            response_time = (time.time() - start_time) * 1000

            # Try to receive response
            self.ws_client.receive_message(timeout=1)

            self.environment.events.request.fire(
                request_type="websocket",
                name="stress_message",
                response_time=response_time,
                response_length=len(json.dumps(message)),
                exception=None,
                context={},
            )
        except Exception as e:
            self.environment.events.request.fire(
                request_type="websocket",
                name="stress_message",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
                context={},
            )


# ============================================================================
# Long Connection User
# ============================================================================


class LongConnectionUser(User):
    """User that maintains a single long-lived connection."""

    wait_time = between(10, 30)

    def __init__(self, environment: Any) -> None:
        """Initialize long connection user."""
        super().__init__(environment)
        base_url = os.getenv("AUTOARR_BASE_URL", "http://localhost:8088")
        self.ws_client = WebSocketClient(base_url)

    def on_start(self) -> None:
        """Connect on start."""
        if not self.ws_client.connect():
            raise Exception("Failed to establish WebSocket connection")

    def on_stop(self) -> None:
        """Disconnect on stop."""
        self.ws_client.disconnect()

    @task
    def periodic_check(self) -> None:
        """Periodically check connection and receive messages."""
        if not self.ws_client.connected:
            logger.warning("Connection lost, attempting to reconnect")
            if self.ws_client.connect():
                logger.info("Reconnection successful")
            else:
                logger.error("Reconnection failed")
                return

        # Receive any available messages
        message = self.ws_client.receive_message(timeout=5)
        self.environment.events.request.fire(
            request_type="websocket",
            name="long_connection_receive",
            response_time=1.0,
            response_length=len(json.dumps(message)) if message else 0,
            exception=None,
            context={"has_message": message is not None},
        )
