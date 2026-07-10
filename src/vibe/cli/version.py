"""CLI version metadata retrieval."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from vibe.version import ARCHITECTURE_BASELINE, BUILD_IDENTIFIER, PLATFORM_NAME, PLATFORM_VERSION


@dataclass(frozen=True)
class VersionInfo:
    """Immutable version metadata for CLI output."""

    cli_version: str
    platform: str
    architecture_version: str
    python_version: str
    build: str

    def as_dict(self) -> dict[str, str]:
        """Return a deterministic mapping for JSON output."""
        return {
            "architecture_version": self.architecture_version,
            "build": self.build,
            "cli_version": self.cli_version,
            "platform": self.platform,
            "python_version": self.python_version,
        }

    def render_text(self) -> str:
        """Return human-readable version output."""
        return (
            f"86-vibe CLI: {self.cli_version}\n"
            f"Platform: {self.platform}\n"
            f"Architecture: {self.architecture_version}\n"
            f"Python: {self.python_version}\n"
            f"Build: {self.build}"
        )


def _resolve_cli_version() -> str:
    try:
        return version("vibe-cli")
    except PackageNotFoundError:
        return PLATFORM_VERSION


def _resolve_build_identifier() -> str:
    if BUILD_IDENTIFIER in {"", "dev"}:
        return "development"
    return BUILD_IDENTIFIER


def get_version_info() -> VersionInfo:
    """Return deterministic version metadata."""
    return VersionInfo(
        cli_version=_resolve_cli_version(),
        platform=PLATFORM_NAME,
        architecture_version=ARCHITECTURE_BASELINE,
        python_version=sys.version.split()[0],
        build=_resolve_build_identifier(),
    )
