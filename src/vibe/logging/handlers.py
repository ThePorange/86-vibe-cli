"""Logging handler creation and lifecycle."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path

from vibe.logging.formatters import PlatformLogFormatter
from vibe.logging.levels import TRACE_LEVEL, parse_level

DEFAULT_MAX_BYTES = 1_048_576
DEFAULT_BACKUP_COUNT = 5

LOG_DIR_NAME = "logs"
PLATFORM_LOG_FILE = "platform.log"
ERROR_LOG_FILE = "error.log"
DEBUG_LOG_FILE = "debug.log"


@dataclass
class HandlerSet:
    """Managed logging handlers for the platform."""

    handlers: list[logging.Handler] = field(default_factory=list)

    def flush(self) -> None:
        """Flush all managed handlers."""
        for handler in self.handlers:
            handler.flush()

    def close(self) -> None:
        """Close all managed handlers."""
        for handler in self.handlers:
            handler.close()
        self.handlers.clear()


def log_directory(project_root: Path) -> Path:
    """Return the platform log directory path."""
    return project_root / ".86vibe" / LOG_DIR_NAME


def ensure_log_directory(project_root: Path) -> Path:
    """Create the platform log directory when required."""
    directory = log_directory(project_root)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_handlers(
    *,
    project_root: Path,
    console_enabled: bool,
    file_enabled: bool,
    debug_enabled: bool,
    rotation_enabled: bool,
    colored_console: bool,
    console_level: str,
    file_level: str,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> HandlerSet:
    """Create configured platform logging handlers."""
    handler_set = HandlerSet()
    log_dir = ensure_log_directory(project_root)

    if console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(parse_level(console_level))
        console_handler.setFormatter(PlatformLogFormatter(colored=colored_console))
        handler_set.handlers.append(console_handler)

    if file_enabled:
        platform_handler = _create_file_handler(
            log_dir / PLATFORM_LOG_FILE,
            level=file_level,
            rotation_enabled=rotation_enabled,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )
        handler_set.handlers.append(platform_handler)

        error_handler = _create_file_handler(
            log_dir / ERROR_LOG_FILE,
            level="ERROR",
            rotation_enabled=rotation_enabled,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )
        handler_set.handlers.append(error_handler)

    if debug_enabled and file_enabled:
        debug_handler = _create_file_handler(
            log_dir / DEBUG_LOG_FILE,
            level="DEBUG",
            rotation_enabled=rotation_enabled,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )
        handler_set.handlers.append(debug_handler)

    return handler_set


def _create_file_handler(
    path: Path,
    *,
    level: str,
    rotation_enabled: bool,
    max_bytes: int,
    backup_count: int,
) -> logging.Handler:
    if rotation_enabled:
        handler: logging.Handler = RotatingFileHandler(
            path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
    else:
        handler = logging.FileHandler(path, encoding="utf-8")

    handler.setLevel(parse_level(level))
    handler.setFormatter(PlatformLogFormatter(colored=False))
    return handler


def attach_handlers(logger: logging.Logger, handler_set: HandlerSet) -> None:
    """Attach managed handlers to a logger."""
    logger.handlers.clear()
    logger.setLevel(TRACE_LEVEL)
    logger.propagate = False
    for handler in handler_set.handlers:
        logger.addHandler(handler)
