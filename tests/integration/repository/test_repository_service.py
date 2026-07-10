"""Repository integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.helpers.repository import create_cli_repository
from vibe.bootstrap.service import BootstrapService
from vibe.cli.application import CLIApplication
from vibe.registry import SERVICE_NAME_REPOSITORY

runner = CliRunner()


def test_bootstrap_registers_repository_service(cli_repo: Path) -> None:
    service = BootstrapService(project_root=cli_repo)
    result = service.initialize()
    assert result.service_registry.contains(SERVICE_NAME_REPOSITORY)
    record = result.lifecycle_manager.get_service(SERVICE_NAME_REPOSITORY)
    assert record.state.value == "ready"
    service.shutdown()


def test_repository_service_integration(cli_repo: Path) -> None:
    service = BootstrapService(project_root=cli_repo)
    service.initialize()
    repository = service.repository_service
    assert repository.is_initialized
    assert repository.metadata().repository_type.value == "cli"
    service.shutdown()


def test_repo_status_cli(cli_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(cli_repo)
    app = CLIApplication(project_root=cli_repo).create_app()
    result = runner.invoke(app, ["repo", "status"])
    assert result.exit_code == 0
    assert "Repository:" in result.stdout


def test_repo_status_json(cli_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(cli_repo)
    app = CLIApplication(project_root=cli_repo).create_app()
    result = runner.invoke(app, ["--output", "json", "repo", "status"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "status" in payload
    assert "metadata" in payload


def test_repo_validate_cli(cli_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(cli_repo)
    app = CLIApplication(project_root=cli_repo).create_app()
    result = runner.invoke(app, ["repo", "validate"])
    assert result.exit_code in {0, 4}


def test_repo_docs_cli(platform_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(platform_repo)
    app = CLIApplication(project_root=platform_repo).create_app()
    result = runner.invoke(app, ["repo", "docs"])
    assert result.exit_code == 0
    assert "DOC-001" in result.stdout or "documents" in result.stdout.lower()


def test_doctor_includes_repository(cli_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(cli_repo)
    app = CLIApplication(project_root=cli_repo).create_app()
    result = runner.invoke(app, ["doctor"])
    assert "repository" in result.stdout.lower()
