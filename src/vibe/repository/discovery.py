"""Repository discovery."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from vibe.repository.errors import RepositoryAccessDeniedError, RepositoryNotFoundError


def discover_git_root(start_path: Path) -> Path:
    """Discover the Git repository root from a starting path.

    Args:
        start_path:
            Directory used to begin discovery.

    Returns:
        Canonical absolute repository root.

    Raises:
        RepositoryNotFoundError:
            When no Git repository can be discovered.
        RepositoryAccessDeniedError:
            When the candidate repository is inaccessible.
    """
    current = start_path.resolve()
    if not current.exists():
        raise RepositoryNotFoundError(f"Discovery path does not exist: {start_path}")

    if not current.is_dir():
        current = current.parent

    visited: set[Path] = set()
    while True:
        if current in visited:
            break
        visited.add(current)
        git_dir = current / ".git"
        if git_dir.exists():
            if not _is_accessible(current):
                raise RepositoryAccessDeniedError("Repository root is not accessible.")
            return current.resolve()

        parent = current.parent
        if parent == current:
            break
        current = parent

    raise RepositoryNotFoundError("No Git repository found from the discovery path.")


def resolve_discovery_start(
    *,
    configured_path: str | None,
    discovery_root: str | None,
    cwd: Path,
) -> Path:
    """Resolve the approved discovery starting point."""
    if configured_path:
        return Path(configured_path).expanduser()
    if discovery_root:
        return Path(discovery_root).expanduser()
    return cwd


def load_repository_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Extract repository settings from effective configuration."""
    repository = config.get("repository", {})
    if not isinstance(repository, dict):
        return {}
    return repository


def _is_accessible(path: Path) -> bool:
    try:
        return path.exists() and os_access(path)
    except OSError:
        return False


def os_access(path: Path) -> bool:
    """Return whether the path is readable and executable."""
    return os.access(path, os.R_OK | os.X_OK)
