"""CLI application tests."""

from __future__ import annotations

import sys

from typer.testing import CliRunner

from vibe.cli.app import app
from vibe.version import ARCHITECTURE_BASELINE, PLATFORM_NAME, PLATFORM_VERSION

runner = CliRunner()


def test_version_command_outputs_required_fields() -> None:
    """Version command reports platform, architecture, and Python versions."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert PLATFORM_NAME in result.stdout
    assert PLATFORM_VERSION in result.stdout
    assert ARCHITECTURE_BASELINE in result.stdout
    assert sys.version.split()[0] in result.stdout


def test_help_command_is_available() -> None:
    """Help command displays usage information."""
    result = runner.invoke(app, ["help"])
    assert result.exit_code == 0
    assert "86-vibe platform command-line interface" in result.stdout


def test_top_level_help_is_available() -> None:
    """Top-level --help displays command groups."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "version" in result.stdout
    assert "init" in result.stdout


def test_placeholder_command_reports_not_implemented() -> None:
    """Placeholder commands return a non-zero exit code."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.stdout
