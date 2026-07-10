"""Stable CLI exit codes."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Canonical exit codes for the 86vibe CLI."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    CONFIGURATION_ERROR = 3
    VALIDATION_FAILURE = 4
    RUNTIME_FAILURE = 5
    EXTERNAL_SERVICE_FAILURE = 6
    INTERNAL_PLATFORM_ERROR = 7
    USER_CANCELLED = 130
