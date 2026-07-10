"""CLI invocation smoke tests."""

from __future__ import annotations

import sys

from typer.testing import CliRunner

from vibe.cli.application import CLIApplication
from vibe.version import ARCHITECTURE_BASELINE, PLATFORM_NAME, PLATFORM_VERSION

runner = CliRunner()


def _app():
    return CLIApplication().create_app()


def test_version_command_outputs_required_fields() -> None:
    """Version command reports platform, architecture, and Python versions."""
    result = runner.invoke(_app(), ["version"])
    assert result.exit_code == 0
    assert PLATFORM_NAME in result.stdout
    assert PLATFORM_VERSION in result.stdout
    assert ARCHITECTURE_BASELINE in result.stdout
    assert sys.version.split()[0] in result.stdout


def test_top_level_help_is_available() -> None:
    """Top-level --help displays command groups."""
    result = runner.invoke(_app(), ["--help"])
    assert result.exit_code == 0
    assert "version" in result.stdout
    assert "init" in result.stdout


def test_deferred_command_reports_unavailable() -> None:
    """Deferred commands return runtime failure exit code."""
    result = runner.invoke(_app(), ["init"])
    assert result.exit_code == 5
    assert "Command unavailable" in (result.stdout + result.stderr)
    assert "IWP-004" in (result.stdout + result.stderr)
