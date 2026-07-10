"""Repository test helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def init_git_repo(path: Path, *, commit: bool = True) -> None:
    """Initialize a local Git repository for tests."""
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
    )
    if commit:
        marker = path / "README.md"
        marker.write_text("# test\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(path), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(path), "commit", "-m", "initial"],
            check=True,
            capture_output=True,
        )


def create_cli_repository(path: Path) -> Path:
    """Create a minimal CLI-shaped repository."""
    init_git_repo(path)
    (path / "src" / "vibe" / "cli").mkdir(parents=True)
    (path / "tests").mkdir()
    (path / "docs").mkdir()
    (path / "pyproject.toml").write_text(
        'version = "0.1.0"\n[project]\nname = "vibe-cli"\n',
        encoding="utf-8",
    )
    (path / "README.md").write_text("# cli\n", encoding="utf-8")
    return path


def create_platform_repository(path: Path) -> Path:
    """Create a minimal platform-shaped repository."""
    init_git_repo(path)
    for directory in ("architecture", "docs", "tests", "standards", "governance"):
        (path / directory).mkdir(parents=True)
    (path / "README.md").write_text("# platform\n", encoding="utf-8")
    (path / "architecture" / "sample.md").write_text(
        "# Sample\n\n| Document ID | DOC-001 |\n| Document Name | Sample |\n"
        "| Package | AP-002 |\n| Status | Draft |\n",
        encoding="utf-8",
    )
    return path


def create_example_repository(path: Path) -> Path:
    """Create a minimal example-shaped repository."""
    init_git_repo(path)
    for directory in ("architecture", "docs", "src", "tests", "prompts", "examples", "data"):
        (path / directory).mkdir(parents=True)
    (path / "README.md").write_text("# example\n", encoding="utf-8")
    return path
