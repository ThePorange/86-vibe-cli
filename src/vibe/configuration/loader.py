"""Configuration loading from defaults and project files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from vibe.configuration.exceptions import ConfigurationLoadError

CONFIG_DIR_NAME = ".86vibe"
CONFIG_FILE_NAME = "config.yaml"


def project_config_path(project_root: Path) -> Path:
    """Return the project configuration file path."""
    return project_root / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def load_defaults() -> dict[str, Any]:
    """Return built-in platform default configuration."""
    return {
        "platform": {"name": "86-vibe"},
        "repository": {"type": "platform", "authoritative": True},
        "ai": {"provider": "openrouter", "default_model": "anthropic/claude-opus-4"},
        "mcp": {"enabled": True},
        "logging": {
            "level": "INFO",
            "console": True,
            "file": True,
            "debug": False,
            "rotation": True,
        },
        "governance": {
            "require_human_approval": True,
            "architecture_lock": True,
        },
    }


def load_project_configuration(
    project_root: Path,
    *,
    required: bool = False,
) -> dict[str, Any]:
    """Load project configuration from ``.86vibe/config.yaml``.

    Args:
        project_root:
            Repository root used for configuration discovery.
        required:
            When ``True``, a missing project configuration file raises an error.

    Returns:
        Parsed project configuration, or an empty mapping when optional and missing.

    Raises:
        ConfigurationLoadError:
            When the configuration file is required but missing or unreadable.
    """
    config_path = project_config_path(project_root)
    if not config_path.exists():
        if required:
            raise ConfigurationLoadError(
                f"Required project configuration file is missing: "
                f"{CONFIG_DIR_NAME}/{CONFIG_FILE_NAME}"
            )
        return {}

    try:
        return load_yaml_file(config_path)
    except ConfigurationLoadError:
        raise
    except OSError as exc:
        raise ConfigurationLoadError(
            f"Unable to read project configuration file: {CONFIG_DIR_NAME}/{CONFIG_FILE_NAME}"
        ) from exc


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Parse a YAML configuration file.

    Args:
        path:
            Path to the YAML configuration file.

    Returns:
        Parsed configuration mapping.

    Raises:
        ConfigurationLoadError:
            When YAML syntax is invalid or the root value is not a mapping.
    """
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationLoadError(f"Unable to read configuration file: {path.name}") from exc

    try:
        parsed = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ConfigurationLoadError(f"Invalid YAML in configuration file: {path.name}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ConfigurationLoadError(f"Configuration file root must be a mapping: {path.name}")
    return parsed
