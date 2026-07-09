"""Loader unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe.configuration.exceptions import ConfigurationLoadError
from vibe.configuration.loader import load_defaults, load_project_configuration, load_yaml_file


def test_load_defaults_contains_platform_and_logging() -> None:
    """Built-in defaults include required platform metadata."""
    defaults = load_defaults()
    assert defaults["platform"]["name"] == "86-vibe"
    assert defaults["logging"]["level"] == "INFO"


def test_load_project_configuration_optional_missing(tmp_path: Path) -> None:
    """Missing optional project configuration returns an empty mapping."""
    loaded = load_project_configuration(tmp_path, required=False)
    assert loaded == {}


def test_load_project_configuration_required_missing(tmp_path: Path) -> None:
    """Missing required project configuration raises a load error."""
    with pytest.raises(ConfigurationLoadError):
        load_project_configuration(tmp_path, required=True)


def test_load_yaml_file_invalid_syntax(tmp_path: Path) -> None:
    """Invalid YAML raises a configuration load error."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("platform: [", encoding="utf-8")
    with pytest.raises(ConfigurationLoadError):
        load_yaml_file(config_path)


def test_load_project_configuration_reads_file(tmp_path: Path) -> None:
    """Project configuration is loaded from .86vibe/config.yaml."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "platform:\n  name: project-name\n",
        encoding="utf-8",
    )
    loaded = load_project_configuration(tmp_path)
    assert loaded["platform"]["name"] == "project-name"
