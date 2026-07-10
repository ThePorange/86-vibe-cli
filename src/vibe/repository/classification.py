"""Repository type classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vibe.repository.models import RepositoryType

_CONFIG_TYPE_MAP = {
    "platform": RepositoryType.PLATFORM,
    "application": RepositoryType.CLI,
    "library": RepositoryType.CLI,
    "example": RepositoryType.EXAMPLE,
    "cli": RepositoryType.CLI,
    "extension": RepositoryType.EXTENSION,
    "plugin": RepositoryType.PLUGIN,
}


def classify_repository(
    root: Path,
    repository_settings: dict[str, Any] | None = None,
) -> tuple[RepositoryType, str]:
    """Classify a repository using deterministic evidence.

    Args:
        root:
            Canonical repository root.
        repository_settings:
            Optional repository configuration section.

    Returns:
        Repository type and classification reason.
    """
    settings = repository_settings or {}
    configured_type = settings.get("type")
    if isinstance(configured_type, str):
        mapped = _CONFIG_TYPE_MAP.get(configured_type.lower())
        if mapped is not None:
            return mapped, f"Configured repository type: {configured_type}"

    if _looks_like_platform(root):
        return RepositoryType.PLATFORM, "Detected platform repository markers"
    if _looks_like_cli(root):
        return RepositoryType.CLI, "Detected CLI repository markers"
    if _looks_like_example(root):
        return RepositoryType.EXAMPLE, "Detected example repository markers"
    if _looks_like_extension(root):
        return RepositoryType.EXTENSION, "Detected extension repository markers"
    if _looks_like_plugin(root):
        return RepositoryType.PLUGIN, "Detected plugin repository markers"
    return RepositoryType.UNKNOWN, "Repository type could not be determined"


def _looks_like_platform(root: Path) -> bool:
    return (
        (root / "architecture").is_dir()
        and (root / "standards").is_dir()
        and (root / "governance").is_dir()
        and not (root / "src" / "vibe" / "cli").is_dir()
    )


def _looks_like_cli(root: Path) -> bool:
    return (root / "src" / "vibe" / "cli").is_dir() and (root / "pyproject.toml").is_file()


def _looks_like_example(root: Path) -> bool:
    return (
        (root / "architecture").is_dir()
        and (root / "prompts").is_dir()
        and (root / "examples").is_dir()
    ) or (
        (root / "architecture").is_dir()
        and (root / "prompts").is_dir()
        and (root / "data").is_dir()
    )


def _looks_like_extension(root: Path) -> bool:
    return (root / "src").is_dir() and (root / "extension.toml").is_file()


def _looks_like_plugin(root: Path) -> bool:
    return (root / "src").is_dir() and (root / "plugin.toml").is_file()
