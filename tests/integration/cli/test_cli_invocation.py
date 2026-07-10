"""CLI invocation integration tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vibe.cli.application import CLIApplication

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate CLI tests to a temporary project directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _app(project_dir: Path) -> object:
    return CLIApplication(project_root=project_dir).create_app()


def test_root_help(project_dir: Path) -> None:
    """Root help returns success without bootstrap."""
    result = runner.invoke(_app(project_dir), ["--help"])
    assert result.exit_code == 0
    assert "--diagnostic" in result.stdout
    assert "--output" in result.stdout
    assert "config" in result.stdout


def test_root_version_option(project_dir: Path) -> None:
    """Root --version returns success without bootstrap."""
    result = runner.invoke(_app(project_dir), ["--version"])
    assert result.exit_code == 0
    assert "86-vibe CLI" in result.stdout


def test_version_command(project_dir: Path) -> None:
    """Version command returns deterministic metadata."""
    result = runner.invoke(_app(project_dir), ["version"])
    assert result.exit_code == 0
    assert sys.version.split()[0] in result.stdout


def test_version_json_output(project_dir: Path) -> None:
    """Version command supports JSON output."""
    result = runner.invoke(_app(project_dir), ["--output", "json", "version"])
    payload = json.loads(result.stdout)
    assert payload["platform"] == "86-vibe"
    assert "cli_version" in payload


def test_unknown_command(project_dir: Path) -> None:
    """Unknown commands return a non-zero exit code."""
    result = runner.invoke(_app(project_dir), ["not-a-command"])
    assert result.exit_code != 0


def test_group_help(project_dir: Path) -> None:
    """Command groups expose help without bootstrap."""
    for group in ("config", "arch", "repository", "repo", "prompts", "prompt", "ai", "mcp"):
        result = runner.invoke(_app(project_dir), [group, "--help"])
        assert result.exit_code == 0, group
        assert group in result.stdout or "Commands" in result.stdout


def test_deferred_command_exit_code(project_dir: Path) -> None:
    """Deferred commands return runtime failure."""
    result = runner.invoke(_app(project_dir), ["init"])
    assert result.exit_code == 5
    assert "Command unavailable" in (result.stdout + result.stderr)
