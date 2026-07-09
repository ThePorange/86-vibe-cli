"""Log level unit tests."""

from __future__ import annotations

import logging

import pytest

from vibe.logging.exceptions import LoggerConfigurationError
from vibe.logging.levels import TRACE_LEVEL, level_name, parse_level, register_trace_level


def test_trace_level_is_lower_than_debug() -> None:
    """TRACE is lower severity than DEBUG."""
    assert TRACE_LEVEL < logging.DEBUG


def test_parse_level_supports_all_platform_levels() -> None:
    """All platform levels convert to numeric values."""
    assert parse_level("TRACE") == TRACE_LEVEL
    assert parse_level("DEBUG") == logging.DEBUG
    assert parse_level("INFO") == logging.INFO
    assert parse_level("WARNING") == logging.WARNING
    assert parse_level("ERROR") == logging.ERROR
    assert parse_level("CRITICAL") == logging.CRITICAL


def test_parse_level_rejects_unknown_values() -> None:
    """Unknown level names raise configuration errors."""
    with pytest.raises(LoggerConfigurationError):
        parse_level("VERBOSE")


def test_register_trace_level_sets_name() -> None:
    """TRACE is registered with the logging module."""
    register_trace_level()
    assert logging.getLevelName(TRACE_LEVEL) == "TRACE"
    assert level_name(TRACE_LEVEL) == "TRACE"
