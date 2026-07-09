"""Platform log level definitions and conversion."""

from __future__ import annotations

import logging

from vibe.logging.exceptions import LoggerConfigurationError

TRACE_LEVEL = 5
LEVEL_NAMES = ("TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_NAME_TO_LEVEL: dict[str, int] = {
    "TRACE": TRACE_LEVEL,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def register_trace_level() -> None:
    """Register the platform TRACE level with the logging module."""
    logging.addLevelName(TRACE_LEVEL, "TRACE")


def parse_level(level_name: str) -> int:
    """Convert a platform level name to a numeric logging level.

    Args:
        level_name:
            Platform log level name.

    Returns:
        Numeric logging level.

    Raises:
        LoggerConfigurationError:
            When the level name is not supported.
    """
    normalized = level_name.strip().upper()
    if normalized not in _NAME_TO_LEVEL:
        allowed = ", ".join(LEVEL_NAMES)
        raise LoggerConfigurationError(
            f"Unsupported logging level '{level_name}'. Expected: {allowed}"
        )
    return _NAME_TO_LEVEL[normalized]


def level_name(level: int) -> str:
    """Return the platform level name for a numeric logging level."""
    if level <= TRACE_LEVEL:
        return "TRACE"
    return logging.getLevelName(level)
