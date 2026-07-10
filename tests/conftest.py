"""Shared repository test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.repository import create_cli_repository, create_platform_repository
from vibe.configuration.service import ConfigurationService
from vibe.logging.service import LoggingService
from vibe.repository.service import RepositoryService


@pytest.fixture
def cli_repo(tmp_path: Path) -> Path:
    """Temporary CLI repository."""
    return create_cli_repository(tmp_path / "cli-repo")


@pytest.fixture
def platform_repo(tmp_path: Path) -> Path:
    """Temporary platform repository."""
    return create_platform_repository(tmp_path / "platform-repo")


@pytest.fixture
def repository_service(cli_repo: Path) -> RepositoryService:
    """Initialized repository service against a CLI repository."""
    configuration = ConfigurationService(project_root=cli_repo)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=cli_repo)
    logging.initialize()
    service = RepositoryService(configuration, logging, project_root=cli_repo)
    service.initialize()
    return service
