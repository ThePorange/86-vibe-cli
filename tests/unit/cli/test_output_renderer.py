"""Output renderer tests."""

from __future__ import annotations

import io
import json

import pytest

from vibe.cli.errors import CLIErrorCategory, CLIOutputError
from vibe.cli.output.renderer import OutputRenderer
from vibe.cli.output.serializers import serialize_value


def test_text_info_output() -> None:
    """Renderer writes informational text to stdout."""
    stdout = io.StringIO()
    renderer = OutputRenderer(stdout=stdout)
    renderer.info("hello")
    assert "hello" in stdout.getvalue()


def test_error_output_uses_stderr() -> None:
    """Renderer writes errors to stderr in text mode."""
    stderr = io.StringIO()
    renderer = OutputRenderer(stderr=stderr)
    renderer.error("failed")
    assert "failed" in stderr.getvalue()


def test_json_output_is_deterministic() -> None:
    """JSON output uses stable key ordering."""
    stdout = io.StringIO()
    renderer = OutputRenderer(mode="json", stdout=stdout)
    renderer.json({"z": 1, "a": 2})
    assert stdout.getvalue() == '{\n  "a": 2,\n  "z": 1\n}\n'


def test_json_error_payload() -> None:
    """JSON errors are written to stderr."""
    stderr = io.StringIO()
    renderer = OutputRenderer(mode="json", stderr=stderr)
    renderer.render_error(
        category=CLIErrorCategory.CONFIG_ERROR,
        message="Unable to load configuration",
    )
    payload = json.loads(stderr.getvalue())
    assert payload["success"] is False
    assert payload["error"]["category"] == "CONFIG_ERROR"


def test_unsupported_serialization_raises() -> None:
    """Unsupported values raise CLIOutputError."""
    with pytest.raises(CLIOutputError):
        serialize_value(object())


def test_no_color_disables_styling() -> None:
    """NO_COLOR produces plain output without ANSI codes."""
    stdout = io.StringIO()
    renderer = OutputRenderer(stdout=stdout)
    renderer.success("ok")
    assert "\x1b[" not in stdout.getvalue()
