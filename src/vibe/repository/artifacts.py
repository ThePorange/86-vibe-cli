"""Repository artifact access."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from vibe.repository.errors import (
    ArtifactNotFoundError,
    InvalidRepositoryPathError,
    ReadFailureError,
    RepositoryAccessDeniedError,
    WriteFailureError,
)
from vibe.repository.git import GitInspector
from vibe.repository.models import ListOptions, ResolvedPath, WriteResult
from vibe.repository.paths import PathPolicy

_TEXT_ENCODING = "utf-8"
_HIDDEN_PREFIX = "."


class ArtifactStore:
    """Governed artifact existence, read, write, and list operations."""

    def __init__(
        self,
        path_policy: PathPolicy,
        *,
        read_only: bool = False,
        include_hidden: bool = False,
        include_ignored: bool = False,
    ) -> None:
        self._path_policy = path_policy
        self._read_only = read_only
        self._include_hidden = include_hidden
        self._include_ignored = include_ignored
        self._git = GitInspector(path_policy.root)

    @property
    def read_only(self) -> bool:
        """Return whether writes are permitted."""
        return self._read_only

    def exists(self, path: str) -> bool:
        """Return whether an artifact exists."""
        resolved = self._path_policy.resolve(path)
        return resolved.absolute.is_file()

    def read(self, path: str) -> str:
        """Read a text artifact."""
        resolved = self._path_policy.resolve(path)
        if resolved.absolute.is_dir():
            raise ReadFailureError("Cannot read a directory as an artifact.")
        if not resolved.absolute.is_file():
            raise ArtifactNotFoundError(f"Artifact not found: {resolved.relative}")
        try:
            return resolved.absolute.read_text(encoding=_TEXT_ENCODING)
        except PermissionError as exc:
            raise RepositoryAccessDeniedError("Read access denied.") from exc
        except OSError as exc:
            raise ReadFailureError("Failed to read artifact.") from exc

    def write(self, path: str, content: str) -> WriteResult:
        """Persist a text artifact using atomic replacement."""
        if self._read_only:
            raise WriteFailureError("Repository is read-only.")
        raw = Path(os.path.normpath(str(path)))
        candidate = self._path_policy.root / raw
        if candidate.is_symlink():
            raise WriteFailureError("Cannot write through a symlink.")
        for parent in candidate.parents:
            if parent == self._path_policy.root or not str(parent).startswith(str(self._path_policy.root)):
                break
            if parent.is_symlink():
                raise WriteFailureError("Cannot write through a symlink.")

        resolved = self._path_policy.resolve(path)
        if resolved.absolute.exists() and resolved.absolute.is_dir():
            raise WriteFailureError("Cannot write over a directory.")
        if resolved.absolute.is_symlink():
            raise WriteFailureError("Cannot write through a symlink.")

        parent = resolved.absolute.parent
        created = not resolved.absolute.exists()
        try:
            parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(resolved.absolute, content)
        except PermissionError as exc:
            raise RepositoryAccessDeniedError("Write access denied.") from exc
        except OSError as exc:
            raise WriteFailureError("Failed to write artifact.") from exc

        encoded = content.encode(_TEXT_ENCODING)
        return WriteResult(
            path=resolved.relative,
            bytes_written=len(encoded),
            created=created,
        )

    def list(self, path: str = ".", *, options: ListOptions | None = None) -> tuple[str, ...]:
        """List repository-relative entries deterministically."""
        resolved = self._path_policy.resolve(path, allow_git=False)
        if not resolved.absolute.is_dir():
            raise ArtifactNotFoundError(f"Directory not found: {resolved.relative}")

        opts = options or ListOptions(
            include_hidden=self._include_hidden,
            include_ignored=self._include_ignored,
        )
        entries: list[str] = []
        if opts.recursive:
            for child in sorted(resolved.absolute.rglob("*")):
                if not child.is_file():
                    continue
                relative = child.relative_to(self._path_policy.root).as_posix()
                if not self._include_entry(relative, opts):
                    continue
                if opts.extension and not relative.endswith(opts.extension):
                    continue
                entries.append(relative)
        else:
            for child in sorted(resolved.absolute.iterdir(), key=lambda item: item.name.lower()):
                relative = child.relative_to(self._path_policy.root).as_posix()
                if not self._include_entry(relative, opts):
                    continue
                if child.is_file() and opts.extension and not relative.endswith(opts.extension):
                    continue
                entries.append(relative)

        return tuple(sorted(entries))

    def _include_entry(self, relative: str, options: ListOptions) -> bool:
        if _GIT_SEGMENT_in_path(relative):
            return False
        name = Path(relative).name
        if not options.include_hidden and name.startswith(_HIDDEN_PREFIX):
            return False
        if not options.include_ignored and self._is_ignored(relative):
            return False
        return True

    def _is_ignored(self, relative: str) -> bool:
        if not self._git.has_git():
            return False
        try:
            completed = subprocess_run_check_ignore(self._path_policy.root, relative)
        except OSError:
            return False
        return completed

    def _atomic_write(self, target: Path, content: str) -> None:
        parent = target.parent
        fd, temp_name = tempfile.mkstemp(prefix=".86vibe-write-", dir=parent)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding=_TEXT_ENCODING) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, target)
        except Exception:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise


def _GIT_SEGMENT_in_path(relative: str) -> bool:
    return ".git" in Path(relative).parts


def subprocess_run_check_ignore(root: Path, relative: str) -> bool:
    """Return whether Git considers a path ignored."""
    import subprocess

    completed = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", relative],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.returncode == 0
