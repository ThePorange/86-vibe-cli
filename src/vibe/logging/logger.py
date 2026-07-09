"""Platform logger implementation."""

from __future__ import annotations

import logging
from typing import Any

from vibe.logging.correlation import get_correlation_id
from vibe.logging.levels import TRACE_LEVEL
from vibe.logging.redaction import redact_message, sanitize_mapping


class PlatformLogger:
    """Platform logger instance obtained from the Logging Service."""

    def __init__(self, name: str, logger: logging.Logger, minimum_level: int) -> None:
        """Initialize a platform logger.

        Args:
            name:
                Logical logger name.
            logger:
                Configured Python logger instance.
            minimum_level:
                Minimum logging level for this logger.
        """
        self._name = name
        self._logger = logger
        self._minimum_level = minimum_level

    def trace(self, message: str, **fields: Any) -> None:
        """Log a trace-level event."""
        self._log(TRACE_LEVEL, message, fields)

    def debug(self, message: str, **fields: Any) -> None:
        """Log a debug-level event."""
        self._log(logging.DEBUG, message, fields)

    def info(self, message: str, **fields: Any) -> None:
        """Log an info-level event."""
        self._log(logging.INFO, message, fields)

    def warning(self, message: str, **fields: Any) -> None:
        """Log a warning-level event."""
        self._log(logging.WARNING, message, fields)

    def error(self, message: str, **fields: Any) -> None:
        """Log an error-level event."""
        self._log(logging.ERROR, message, fields)

    def critical(self, message: str, **fields: Any) -> None:
        """Log a critical-level event."""
        self._log(logging.CRITICAL, message, fields)

    def exception(self, message: str, **fields: Any) -> None:
        """Log an exception with stack trace information."""
        extra = self._build_extra(fields)
        sanitized_message = redact_message(message)
        self._logger.exception(sanitized_message, extra=extra)

    def format_message(self, message: str, fields: dict[str, Any]) -> str:
        """Format a message and structured fields for diagnostics."""
        return self._format_message(message, fields)

    def _log(self, level: int, message: str, fields: dict[str, Any]) -> None:
        if level < self._minimum_level:
            return
        extra = self._build_extra(fields)
        sanitized_message = redact_message(message)
        self._logger.log(level, sanitized_message, extra=extra)

    def _build_extra(self, fields: dict[str, Any]) -> dict[str, Any]:
        sanitized = sanitize_mapping(fields)
        component = str(sanitized.pop("component", self._name))
        command = str(sanitized.pop("command", ""))
        correlation_id = get_correlation_id() or ""
        return {
            "component": component,
            "command": command,
            "correlation_id": correlation_id,
            "structured_fields": sanitized,
        }

    def _format_message(self, message: str, fields: dict[str, Any]) -> str:
        sanitized = sanitize_mapping(fields)
        if not sanitized:
            return redact_message(message)
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(sanitized.items()))
        return f"{redact_message(message)} ({rendered})"
