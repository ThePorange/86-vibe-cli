"""Repository classification tests."""

from __future__ import annotations

from pathlib import Path

from tests.helpers.repository import create_example_repository
from vibe.repository.classification import classify_repository
from vibe.repository.models import RepositoryType


def test_classifies_platform_repository(platform_repo: Path) -> None:
    repository_type, reason = classify_repository(platform_repo)
    assert repository_type == RepositoryType.PLATFORM
    assert reason


def test_classifies_cli_repository(cli_repo: Path) -> None:
    repository_type, _ = classify_repository(cli_repo)
    assert repository_type == RepositoryType.CLI


def test_classifies_example_repository(tmp_path: Path) -> None:
    repo = create_example_repository(tmp_path / "example")
    repository_type, _ = classify_repository(repo)
    assert repository_type == RepositoryType.EXAMPLE


def test_unknown_repository(tmp_path: Path) -> None:
    repository_type, _ = classify_repository(tmp_path)
    assert repository_type == RepositoryType.UNKNOWN
