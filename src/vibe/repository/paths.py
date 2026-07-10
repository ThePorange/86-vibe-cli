"""Repository path policy and boundary enforcement."""

from __future__ import annotations

import os
from pathlib import Path

from vibe.repository.errors import InvalidRepositoryPathError
from vibe.repository.models import ResolvedPath

_GIT_SEGMENT = ".git"
_NULL_BYTE = "\x00"


class PathPolicy:
    """Centralized repository path resolution and containment."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root.resolve()

    @property
    def root(self) -> Path:
        """Return the canonical repository root."""
        return self._root

    def resolve(self, path: str | Path, *, allow_git: bool = False) -> ResolvedPath:
        """Resolve and validate a repository-relative path."""
        raw = str(path).strip()
        if not raw:
            raise InvalidRepositoryPathError("Repository path must not be empty.")
        if _NULL_BYTE in raw:
            raise InvalidRepositoryPathError("Repository path contains invalid characters.")

        candidate = Path(raw)
        if candidate.is_absolute():
            raise InvalidRepositoryPathError("Absolute repository paths are not permitted.")

        normalized = Path(os.path.normpath(raw))
        if normalized.parts and normalized.parts[0] == "..":
            raise InvalidRepositoryPathError("Repository path escapes the repository root.")
        if ".." in normalized.parts:
            raise InvalidRepositoryPathError("Repository path escapes the repository root.")

        absolute = self._resolve_within_root(normalized)
        if not self._is_within_root(absolute):
            raise InvalidRepositoryPathError("Repository path escapes the repository root.")

        if not allow_git and self._is_git_internal(absolute):
            raise InvalidRepositoryPathError("Access to .git internals is not permitted.")

        relative = absolute.relative_to(self._root).as_posix()
        return ResolvedPath(relative=relative, absolute=absolute)

    def _resolve_within_root(self, normalized: Path) -> Path:
        current = self._root
        for part in normalized.parts:
            if part in {".", ""}:
                continue
            if part == "..":
                raise InvalidRepositoryPathError("Repository path escapes the repository root.")
            candidate = current / part
            if candidate.is_symlink():
                resolved_link = candidate.resolve()
                if not self._is_within_root(resolved_link):
                    raise InvalidRepositoryPathError("Repository path escapes the repository root.")
                current = resolved_link
            else:
                current = candidate
        return current

    def _is_within_root(self, absolute: Path) -> bool:
        try:
            absolute.resolve().relative_to(self._root)
            return True
        except ValueError:
            return False

    def _is_git_internal(self, absolute: Path) -> bool:
        try:
            relative = absolute.relative_to(self._root)
        except ValueError:
            return True
        return _GIT_SEGMENT in relative.parts
