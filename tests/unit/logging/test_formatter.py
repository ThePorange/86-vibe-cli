"""Formatter unit tests."""

from __future__ import annotations

import logging

from vibe.logging.formatters import PlatformLogFormatter


def test_formatter_produces_iso8601_utc_timestamp() -> None:
    """Formatted output includes an ISO-8601 UTC timestamp."""
    formatter = PlatformLogFormatter()
    record = logging.LogRecord(
        name="vibe.cli",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Repository initialized successfully",
        args=(),
        exc_info=None,
    )
    record.created = 1_752_079_971
    record.component = "cli.init"
    record.command = ""
    record.correlation_id = ""
    record.structured_fields = {}
    formatted = formatter.format(record)
    assert formatted.startswith("2025-07-09T")
    assert "INFO cli.init Repository initialized successfully" in formatted


def test_formatter_includes_structured_metadata_in_deterministic_order() -> None:
    """Structured metadata is rendered in sorted order."""
    formatter = PlatformLogFormatter()
    record = logging.LogRecord(
        name="vibe.cli",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Prompt loaded",
        args=(),
        exc_info=None,
    )
    record.component = "cli"
    record.command = "doctor"
    record.correlation_id = "corr-1"
    record.structured_fields = {"duration_ms": 14, "repository": "86-vibe-platform"}
    formatted = formatter.format(record)
    assert "correlation_id=corr-1" in formatted
    assert formatted.index("duration_ms=14") < formatted.index("repository=86-vibe-platform")
