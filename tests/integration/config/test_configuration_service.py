"""Configuration Service integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from vibe.configuration.exceptions import (
    ConfigurationLoadError,
    ConfigurationReloadError,
    ConfigurationValidationError,
)
from vibe.configuration.service import ConfigurationService


@pytest.fixture
def clean_vibe_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove VIBE_ environment variables before each test."""
    for key in list(os.environ):
        if key.startswith("VIBE_"):
            monkeypatch.delenv(key, raising=False)


def test_repository_integration_discovers_project_configuration(
    tmp_path: Path,
    clean_vibe_env: None,
) -> None:
    """Configuration file is discovered and loaded from the repository layout."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "\n".join(
            [
                "platform:",
                "  name: integration-platform",
                "repository:",
                "  type: example",
                "  authoritative: false",
                "logging:",
                "  level: WARNING",
            ]
        ),
        encoding="utf-8",
    )
    service = ConfigurationService(project_root=tmp_path)
    service.initialize()
    service.load()
    service.reload()
    service.shutdown()
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    assert service.get("platform.name") == "integration-platform"
    assert service.get("repository.type") == "example"


def test_effective_configuration_reflects_all_sources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    clean_vibe_env: None,
) -> None:
    """Exported effective configuration reflects defaults, project, env, and overrides."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "logging:\n  level: INFO\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("VIBE_AI_PROVIDER", "openai")
    service = ConfigurationService(
        project_root=tmp_path,
        overrides={"logging.level": "DEBUG"},
    )
    service.load()
    exported = service.export(mask_secrets=False)
    assert exported["platform"]["name"] == "86-vibe"
    assert exported["logging"]["level"] == "DEBUG"
    assert exported["ai"]["provider"] == "openai"


def test_integration_invalid_yaml_fails(tmp_path: Path, clean_vibe_env: None) -> None:
    """Invalid YAML prevents service initialization."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("platform: [", encoding="utf-8")
    service = ConfigurationService(project_root=tmp_path)
    with pytest.raises(ConfigurationLoadError):
        service.load()


def test_integration_malformed_values_fail(tmp_path: Path, clean_vibe_env: None) -> None:
    """Malformed values are rejected during load."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "governance:\n  architecture_lock: not-a-bool\n",
        encoding="utf-8",
    )
    service = ConfigurationService(project_root=tmp_path)
    with pytest.raises(ConfigurationValidationError):
        service.load()


def test_integration_reload_failure_keeps_previous_configuration(
    tmp_path: Path,
    clean_vibe_env: None,
) -> None:
    """Reload failures leave the previous configuration active."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    config_path = config_dir / "config.yaml"
    config_path.write_text("platform:\n  name: before-reload\n", encoding="utf-8")
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    config_path.write_text("logging:\n  level: VERBOSE\n", encoding="utf-8")
    with pytest.raises(ConfigurationReloadError):
        service.reload()
    assert service.get("platform.name") == "before-reload"
