"""Repository security tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from vibe.repository.errors import InvalidRepositoryPathError, WriteFailureError
from vibe.repository.paths import PathPolicy


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Symlink creation requires elevated privileges on Windows.")
    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    outside.mkdir()
    repo.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    os.symlink(outside, repo / "escape")
    policy = PathPolicy(repo)
    with pytest.raises(InvalidRepositoryPathError):
        policy.resolve("escape/secret.txt")


def test_write_rejects_symlink_target(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Symlink creation requires elevated privileges on Windows.")
    from vibe.configuration.service import ConfigurationService
    from vibe.logging.service import LoggingService
    from tests.helpers.repository import create_cli_repository
    from vibe.repository.service import RepositoryService

    repo = create_cli_repository(tmp_path / "repo")
    target = repo / "target.txt"
    target.write_text("old", encoding="utf-8")
    link = repo / "link.txt"
    os.symlink(target, link)
    configuration = ConfigurationService(project_root=repo)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=repo)
    logging.initialize()
    service = RepositoryService(configuration, logging, project_root=repo)
    service.initialize()
    with pytest.raises(WriteFailureError):
        service.write("link.txt", "new")
