"""Repository service unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.repository import create_cli_repository
from vibe.configuration.service import ConfigurationService
from vibe.logging.service import LoggingService
from vibe.repository.errors import (
    ArtifactNotFoundError,
    InvalidRepositoryPathError,
    RepositoryNotFoundError,
    RepositoryNotInitializedError,
)
from vibe.repository.models import RepositoryType, ValidationStatus
from vibe.repository.service import RepositoryService


def test_initialize_discovers_cli_repository(cli_repo: Path) -> None:
    configuration = ConfigurationService(project_root=cli_repo)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=cli_repo)
    logging.initialize()
    service = RepositoryService(configuration, logging, project_root=cli_repo)
    service.initialize()
    metadata = service.metadata()
    assert metadata.repository_type == RepositoryType.CLI
    service.shutdown()


def test_initialize_fails_without_git(tmp_path: Path) -> None:
    configuration = ConfigurationService(project_root=tmp_path)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=tmp_path)
    logging.initialize()
    service = RepositoryService(configuration, logging, project_root=tmp_path)
    with pytest.raises(RepositoryNotFoundError):
        service.initialize()


def test_artifact_read_write_and_exists(repository_service: RepositoryService) -> None:
    assert repository_service.exists("README.md") is True
    content = repository_service.read("README.md")
    assert content.startswith("#")
    result = repository_service.write("generated.txt", "hello")
    assert result.bytes_written == 5
    assert repository_service.read("generated.txt") == "hello"


def test_list_is_deterministic(repository_service: RepositoryService) -> None:
    repository_service.write("b.txt", "b")
    repository_service.write("a.txt", "a")
    entries = repository_service.list(".")
    assert entries == tuple(sorted(entries))


def test_operations_require_initialization(cli_repo: Path) -> None:
    configuration = ConfigurationService(project_root=cli_repo)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=cli_repo)
    logging.initialize()
    service = RepositoryService(configuration, logging, project_root=cli_repo)
    with pytest.raises(RepositoryNotInitializedError):
        service.read("README.md")


def test_refresh_updates_metadata(repository_service: RepositoryService) -> None:
    before = repository_service.metadata()
    after = repository_service.refresh()
    assert after.identifier == before.identifier


def test_validate_reports_valid_cli_repository(repository_service: RepositoryService) -> None:
    result = repository_service.validate()
    assert result.status in {ValidationStatus.VALID, ValidationStatus.WARNING}


def test_rejects_traversal_on_read(repository_service: RepositoryService) -> None:
    with pytest.raises(InvalidRepositoryPathError):
        repository_service.read("../outside.txt")


def test_missing_artifact(repository_service: RepositoryService) -> None:
    with pytest.raises(ArtifactNotFoundError):
        repository_service.read("missing.txt")


def test_open_switches_repository(cli_repo: Path, tmp_path: Path) -> None:
    other = create_cli_repository(tmp_path / "other")
    configuration = ConfigurationService(project_root=cli_repo)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=cli_repo)
    logging.initialize()
    service = RepositoryService(configuration, logging, project_root=cli_repo)
    service.initialize()
    metadata = service.open(other)
    assert metadata.root == other.resolve()
