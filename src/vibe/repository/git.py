"""Read-only Git inspection."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from vibe.repository.errors import RepositoryFailureError
from vibe.repository.models import BranchInfo, GitCleanliness, LatestCommit


class GitInspector:
    """Encapsulated read-only Git inspection."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root

    def has_git(self) -> bool:
        """Return whether a Git repository is present."""
        return (self._root / ".git").exists()

    def current_branch(self) -> BranchInfo | None:
        """Return normalized current branch information."""
        if not self.has_git():
            return None
        try:
            output = self._run("rev-parse", "--abbrev-ref", "HEAD")
        except RepositoryFailureError:
            return None
        if output == "HEAD":
            return BranchInfo(name=None, detached=True)
        return BranchInfo(name=output, detached=False)

    def default_branch(self) -> str | None:
        """Return the default branch when deterministically available."""
        if not self.has_git():
            return None
        for candidate in ("origin/HEAD", "HEAD"):
            try:
                symbolic = self._run("symbolic-ref", "--short", candidate)
            except RepositoryFailureError:
                continue
            if symbolic.startswith("origin/"):
                return symbolic.removeprefix("origin/")
            if symbolic and symbolic != "HEAD":
                return symbolic
        return None

    def cleanliness(self) -> GitCleanliness:
        """Return normalized working-tree cleanliness."""
        if not self.has_git():
            return GitCleanliness.UNAVAILABLE
        try:
            output = self._run("status", "--porcelain")
        except RepositoryFailureError:
            return GitCleanliness.UNKNOWN
        return GitCleanliness.CLEAN if not output else GitCleanliness.MODIFIED

    def latest_commit(self) -> LatestCommit | None:
        """Return normalized latest commit metadata."""
        if not self.has_git():
            return None
        try:
            full_hash = self._run("rev-parse", "HEAD")
            short_hash = self._run("rev-parse", "--short", "HEAD")
            subject = self._run("log", "-1", "--pretty=%s")
            author = self._run("log", "-1", "--pretty=%an")
            timestamp_raw = self._run("log", "-1", "--pretty=%cI")
        except RepositoryFailureError:
            return None
        timestamp = None
        if timestamp_raw:
            try:
                timestamp = datetime.fromisoformat(timestamp_raw).astimezone(UTC)
            except ValueError:
                timestamp = None
        return LatestCommit(
            full_hash=full_hash,
            short_hash=short_hash,
            author=author or None,
            timestamp=timestamp,
            subject=subject or None,
        )

    def current_tag(self) -> str | None:
        """Return the exact tag for HEAD when available."""
        if not self.has_git():
            return None
        try:
            output = self._run("describe", "--tags", "--exact-match")
        except RepositoryFailureError:
            return None
        return output or None

    def _run(self, *args: str) -> str:
        command = ["git", "-C", str(self._root), *args]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RepositoryFailureError("Git inspection failed.") from exc

        if completed.returncode != 0:
            raise RepositoryFailureError("Git inspection failed.")
        return completed.stdout.strip()
