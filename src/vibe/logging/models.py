"""Structured logging models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration resolved from the Configuration Service."""

    level: str = "INFO"
    console: bool = True
    file: bool = True
    debug: bool = False
    rotation: bool = True
    colored: bool = True
    console_level: str = "INFO"
    file_level: str = "DEBUG"


@dataclass(frozen=True)
class LogEvent:
    """Immutable structured log event representation."""

    timestamp: str
    level: str
    logger_name: str
    message: str
    component: str = ""
    command: str = ""
    correlation_id: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
