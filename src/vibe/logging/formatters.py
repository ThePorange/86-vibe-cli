"""Logging formatters."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from vibe.logging.redaction import redact_message, sanitize_mapping

_LEVEL_COLORS = {
    "TRACE": "\033[36m",
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}
_RESET_COLOR = "\033[0m"


class PlatformLogFormatter(logging.Formatter):
    """Deterministic platform log formatter for console and file output."""

    def __init__(self, *, colored: bool = False) -> None:
        super().__init__()
        self._colored = colored

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        level_name = record.levelname
        component = getattr(record, "component", "") or record.name.removeprefix("vibe.")
        command = getattr(record, "command", "")
        correlation_id = getattr(record, "correlation_id", "")
        message = redact_message(record.getMessage())
        structured_fields = sanitize_mapping(getattr(record, "structured_fields", {}))

        parts = [timestamp, level_name, component]
        if command:
            parts.append(command)
        parts.append(message)

        metadata: list[str] = []
        if correlation_id:
            metadata.append(f"correlation_id={correlation_id}")
        for key in sorted(structured_fields):
            metadata.append(f"{key}={structured_fields[key]}")
        if metadata:
            parts.append(" ".join(metadata))

        formatted = " ".join(parts)
        if record.exc_info and not self._colored:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            formatted = f"{formatted}\n{record.exc_text}"
        if self._colored:
            color = _LEVEL_COLORS.get(level_name, "")
            if color:
                return f"{color}{formatted}{_RESET_COLOR}"
        return formatted

    def formatException(self, ei: Any) -> str:
        formatted = super().formatException(ei)
        return redact_message(formatted)
