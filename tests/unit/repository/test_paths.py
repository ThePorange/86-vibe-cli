"""Repository path policy tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe.repository.errors import InvalidRepositoryPathError
from vibe.repository.paths import PathPolicy


@pytest.fixture
def policy(tmp_path: Path) -> PathPolicy:
    (tmp_path / "inside.txt").write_text("ok", encoding="utf-8")
    return PathPolicy(tmp_path)


def test_valid_relative_path(policy: PathPolicy) -> None:
    resolved = policy.resolve("inside.txt")
    assert resolved.relative == "inside.txt"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "../../outside.txt",
        "nested/../../outside.txt",
        "/etc/passwd",
    ],
)
def test_rejects_escape_paths(policy: PathPolicy, path: str) -> None:
    with pytest.raises(InvalidRepositoryPathError):
        policy.resolve(path)


def test_rejects_git_internals(policy: PathPolicy) -> None:
    git_dir = policy.root / ".git"
    git_dir.mkdir()
    with pytest.raises(InvalidRepositoryPathError):
        policy.resolve(".git/config")
