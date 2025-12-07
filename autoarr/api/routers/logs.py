# Copyright (C) 2025 AutoArr Contributors
#
# This file is part of AutoArr.
#
# AutoArr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Logs API endpoints for viewing application logs in the UI.

This module provides endpoints for:
- Fetching recent logs from a circular buffer
- Streaming logs via WebSocket
- Clearing the log buffer
- Changing log level dynamically
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Log Buffer - Circular buffer to avoid memory issues
# ============================================================================

MAX_LOG_ENTRIES = 1000  # Keep last 1000 log entries in memory


class LogEntry(BaseModel):
    """A single log entry."""

    timestamp: str
    level: str
    logger_name: str
    message: str
    request_id: Optional[str] = None


class LogBuffer:
    """
    Circular buffer for storing recent log entries.

    This prevents memory issues by limiting the number of stored logs
    and provides efficient access for the UI.
    """

    def __init__(self, max_size: int = MAX_LOG_ENTRIES):
        self._buffer: Deque[LogEntry] = deque(maxlen=max_size)
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    def add(self, entry: LogEntry) -> None:
        """Add a log entry to the buffer."""
        self._buffer.append(entry)
        # Notify subscribers (non-blocking)
        for queue in self._subscribers:
            try:
                queue.put_nowait(entry)
            except asyncio.QueueFull:
                pass  # Drop if queue is full to prevent blocking

    def get_recent(
        self, limit: int = 100, level: Optional[str] = None, search: Optional[str] = None
    ) -> List[LogEntry]:
        """
        Get recent log entries with optional filtering.

        Args:
            limit: Maximum number of entries to return
            level: Filter by minimum log level (DEBUG, INFO, WARNING, ERROR)
            search: Filter by message content (case-insensitive)
        """
        level_order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        min_level = level_order.get(level.upper(), 0) if level else 0

        result = []
        for entry in reversed(self._buffer):
            # Filter by level
            entry_level = level_order.get(entry.level.upper(), 0)
            if entry_level < min_level:
                continue

            # Filter by search term
            if search and search.lower() not in entry.message.lower():
                continue

            result.append(entry)
            if len(result) >= limit:
                break

        return list(reversed(result))

    def clear(self) -> int:
        """Clear all log entries. Returns count of cleared entries."""
        count = len(self._buffer)
        self._buffer.clear()
        return count

    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to new log entries."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.append(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from log entries."""
        async with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)


# Global log buffer instance
_log_buffer = LogBuffer()


def get_log_buffer() -> LogBuffer:
    """Get the global log buffer instance."""
    return _log_buffer


# ============================================================================
# Custom Log Handler to capture logs
# ============================================================================


class BufferLogHandler(logging.Handler):
    """
    Custom logging handler that sends logs to the circular buffer.
    """

    def __init__(self, buffer: LogBuffer):
        super().__init__()
        self.buffer = buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Extract request ID if available
            request_id = getattr(record, "request_id", None)

            entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created).isoformat(),
                level=record.levelname,
                logger_name=record.name,
                message=self.format(record),
                request_id=request_id,
            )
            self.buffer.add(entry)
        except Exception:
            pass  # Don't let logging errors crash the app


def setup_log_buffer_handler() -> None:
    """
    Set up the buffer handler on the root logger.
    Call this during application startup.
    """
    handler = BufferLogHandler(_log_buffer)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.DEBUG)  # Capture all levels

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    logger.info("Log buffer handler initialized")


# ============================================================================
# Request/Response Models
# ============================================================================


class LogsResponse(BaseModel):
    """Response containing log entries."""

    logs: List[LogEntry]
    total_in_buffer: int
    returned_count: int


class ClearLogsResponse(BaseModel):
    """Response from clearing logs."""

    cleared_count: int
    message: str


class LogLevelRequest(BaseModel):
    """Request to change log level."""

    level: str = Field(..., description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")


class LogLevelResponse(BaseModel):
    """Response from changing log level."""

    level: str
    message: str


# ============================================================================
# REST Endpoints
# ============================================================================


@router.get("", response_model=LogsResponse)
@router.get("/", response_model=LogsResponse)
async def get_logs(
    limit: int = 100,
    level: Optional[str] = None,
    search: Optional[str] = None,
) -> LogsResponse:
    """
    Get recent log entries.

    Args:
        limit: Maximum number of entries to return (default 100, max 500)
        level: Minimum log level filter (DEBUG, INFO, WARNING, ERROR)
        search: Search term to filter messages

    Returns:
        Recent log entries matching the filters
    """
    # Cap limit to prevent large responses
    limit = min(limit, 500)

    buffer = get_log_buffer()
    logs = buffer.get_recent(limit=limit, level=level, search=search)

    return LogsResponse(
        logs=logs,
        total_in_buffer=len(buffer._buffer),
        returned_count=len(logs),
    )


@router.delete("", response_model=ClearLogsResponse)
@router.delete("/", response_model=ClearLogsResponse)
async def clear_logs() -> ClearLogsResponse:
    """
    Clear all logs from the buffer.

    Returns:
        Count of cleared entries
    """
    buffer = get_log_buffer()
    count = buffer.clear()
    logger.info(f"Logs cleared: {count} entries removed")

    return ClearLogsResponse(
        cleared_count=count,
        message=f"Cleared {count} log entries",
    )


@router.get("/level", response_model=LogLevelResponse)
async def get_log_level() -> LogLevelResponse:
    """Get current log level."""
    root_logger = logging.getLogger()
    level_name = logging.getLevelName(root_logger.level)

    return LogLevelResponse(
        level=level_name,
        message=f"Current log level is {level_name}",
    )


@router.put("/level", response_model=LogLevelResponse)
async def set_log_level(request: LogLevelRequest) -> LogLevelResponse:
    """
    Change the application log level.

    Args:
        request: New log level

    Returns:
        Updated log level
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    level = request.level.upper()

    if level not in valid_levels:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Invalid log level. Must be one of: {', '.join(valid_levels)}",
        )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    logger.info(f"Log level changed to {level}")

    return LogLevelResponse(
        level=level,
        message=f"Log level changed to {level}",
    )


# ============================================================================
# WebSocket Endpoint for Real-time Streaming
# ============================================================================


@router.websocket("/stream")
async def stream_logs(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for streaming logs in real-time.

    Clients can send JSON messages to filter logs:
    - {"type": "set_level", "level": "INFO"} - Set minimum level filter
    - {"type": "set_search", "search": "error"} - Set search filter
    - {"type": "clear_filters"} - Clear all filters
    """
    await websocket.accept()

    buffer = get_log_buffer()
    queue = await buffer.subscribe()

    # Client filter state
    min_level = 0
    search_term: Optional[str] = None
    level_order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

    try:
        # Send initial batch of recent logs
        recent = buffer.get_recent(limit=50)
        for entry in recent:
            await websocket.send_json(entry.model_dump())

        # Create tasks for receiving and sending
        async def receive_commands() -> None:
            nonlocal min_level, search_term
            while True:
                try:
                    data = await websocket.receive_json()
                    msg_type = data.get("type")

                    if msg_type == "set_level":
                        level = data.get("level", "DEBUG").upper()
                        min_level = level_order.get(level, 0)
                    elif msg_type == "set_search":
                        search_term = data.get("search")
                    elif msg_type == "clear_filters":
                        min_level = 0
                        search_term = None
                except Exception:
                    break

        async def send_logs() -> None:
            while True:
                try:
                    entry: LogEntry = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Apply filters
                    entry_level = level_order.get(entry.level.upper(), 0)
                    if entry_level < min_level:
                        continue
                    if search_term and search_term.lower() not in entry.message.lower():
                        continue

                    await websocket.send_json(entry.model_dump())
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

        # Run both tasks concurrently
        receive_task = asyncio.create_task(receive_commands())
        send_task = asyncio.create_task(send_logs())

        done, pending = await asyncio.wait(
            [receive_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        await buffer.unsubscribe(queue)
