"""CLI bootstrap integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from vibe.bootstrap.state import BootstrapState
from vibe.cli.application import CLIApplication

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate CLI tests to a temporary project directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_operational_command_bootstraps_and_shuts_down(project_dir: Path) -> None:
    """Deferred commands initialize and shut down bootstrap."""
    application = CLIApplication(project_root=project_dir)
    app = application.create_app()
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 5
    assert application.bootstrap_service.state == BootstrapState.STOPPED


def test_config_show_bootstraps(project_dir: Path) -> None:
    """Configuration show initializes platform services."""
    application = CLIApplication(project_root=project_dir)
    app = application.create_app()
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert application.bootstrap_service.state == BootstrapState.STOPPED
