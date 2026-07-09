"""Configuration Service unit tests."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from vibe.configuration.exceptions import (
    ConfigurationKeyError,
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


def test_service_initializes_with_defaults(tmp_path: Path, clean_vibe_env: None) -> None:
    """Service initializes successfully using default configuration."""
    service = ConfigurationService(project_root=tmp_path)
    service.initialize()
    service.load()
    assert service.validate() is True
    assert service.get("platform.name") == "86-vibe"


def test_service_initializes_with_project_configuration(
    tmp_path: Path,
    clean_vibe_env: None,
) -> None:
    """Service loads project configuration over defaults."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "platform:\n  name: project-platform\n",
        encoding="utf-8",
    )
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    assert service.get("platform.name") == "project-platform"


def test_service_initializes_with_runtime_overrides(tmp_path: Path, clean_vibe_env: None) -> None:
    """Runtime overrides have the highest precedence."""
    service = ConfigurationService(
        project_root=tmp_path,
        overrides={"logging.level": "DEBUG"},
    )
    service.load()
    assert service.get("logging.level") == "DEBUG"


def test_initialize_is_idempotent(tmp_path: Path, clean_vibe_env: None) -> None:
    """Initialization can be called repeatedly."""
    service = ConfigurationService(project_root=tmp_path)
    service.initialize()
    service.initialize()
    assert service.is_initialized is True


def test_load_fails_on_invalid_configuration(tmp_path: Path, clean_vibe_env: None) -> None:
    """Invalid configuration fails deterministically during load."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "logging:\n  level: VERBOSE\n",
        encoding="utf-8",
    )
    service = ConfigurationService(project_root=tmp_path)
    with pytest.raises(ConfigurationValidationError):
        service.load()


def test_required_project_configuration_missing(tmp_path: Path, clean_vibe_env: None) -> None:
    """Missing required project configuration raises a load error."""
    service = ConfigurationService(project_root=tmp_path, require_project_config=True)
    with pytest.raises(ConfigurationLoadError):
        service.load()


def test_environment_overrides_supersede_project_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    clean_vibe_env: None,
) -> None:
    """Environment variables override project configuration."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "logging:\n  level: INFO\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("VIBE_LOGGING_LEVEL", "WARNING")
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    assert service.get("logging.level") == "WARNING"


def test_export_is_read_only_snapshot(tmp_path: Path, clean_vibe_env: None) -> None:
    """Exported configuration does not mutate runtime configuration."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    exported = service.export(mask_secrets=False)
    exported["platform"]["name"] = "changed"
    assert service.get("platform.name") == "86-vibe"


def test_export_contains_runtime_overrides(tmp_path: Path, clean_vibe_env: None) -> None:
    """Exported configuration includes runtime overrides."""
    service = ConfigurationService(
        project_root=tmp_path,
        overrides={"logging.level": "ERROR"},
    )
    service.load()
    exported = service.export(mask_secrets=False)
    assert exported["logging"]["level"] == "ERROR"


def test_export_masks_secret_fields(tmp_path: Path, clean_vibe_env: None) -> None:
    """Sensitive values are masked in exported configuration."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "ai:\n  api_key: secret-value\n",
        encoding="utf-8",
    )
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    exported = service.export()
    assert exported["ai"]["api_key"] == "********"


def test_get_section_returns_section(tmp_path: Path, clean_vibe_env: None) -> None:
    """Section access returns a structured mapping."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    logging_section = service.get_section("logging")
    assert logging_section["level"] == "INFO"


def test_get_section_missing_raises(tmp_path: Path, clean_vibe_env: None) -> None:
    """Missing section access raises a configuration key error."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    with pytest.raises(ConfigurationKeyError):
        service.get_section("missing")


def test_exists_and_contains_are_equivalent(tmp_path: Path, clean_vibe_env: None) -> None:
    """Exists is an alias for contains."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    assert service.exists("logging.level") is True
    assert service.contains("logging.level") is True


def test_get_missing_key_returns_default(tmp_path: Path, clean_vibe_env: None) -> None:
    """Missing optional keys return caller-provided defaults."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    assert service.get("missing.key", "fallback") == "fallback"


def test_get_missing_key_without_default_raises(tmp_path: Path, clean_vibe_env: None) -> None:
    """Missing keys without defaults raise a configuration key error."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    with pytest.raises(ConfigurationKeyError):
        service.get("missing.key")


def test_successful_reload_replaces_configuration(tmp_path: Path, clean_vibe_env: None) -> None:
    """Reload replaces runtime configuration after successful validation."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    config_path = config_dir / "config.yaml"
    config_path.write_text("platform:\n  name: first\n", encoding="utf-8")
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    config_path.write_text("platform:\n  name: second\n", encoding="utf-8")
    service.reload()
    assert service.get("platform.name") == "second"


def test_failed_reload_preserves_previous_configuration(
    tmp_path: Path,
    clean_vibe_env: None,
) -> None:
    """Failed reload keeps the previous active configuration."""
    config_dir = tmp_path / ".86vibe"
    config_dir.mkdir()
    config_path = config_dir / "config.yaml"
    config_path.write_text("platform:\n  name: stable\n", encoding="utf-8")
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    config_path.write_text("logging:\n  level: VERBOSE\n", encoding="utf-8")
    with pytest.raises(ConfigurationReloadError):
        service.reload()
    assert service.get("platform.name") == "stable"


def test_concurrent_reads_remain_consistent(tmp_path: Path, clean_vibe_env: None) -> None:
    """Concurrent readers observe consistent configuration values."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    errors: list[str] = []
    barrier = threading.Barrier(8)

    def reader() -> None:
        barrier.wait()
        for _ in range(100):
            value = service.get("platform.name")
            if value != "86-vibe":
                errors.append(f"unexpected value: {value}")

    threads = [threading.Thread(target=reader) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []


def test_shutdown_resets_state(tmp_path: Path, clean_vibe_env: None) -> None:
    """Shutdown releases runtime configuration."""
    service = ConfigurationService(project_root=tmp_path)
    service.load()
    service.shutdown()
    assert service.is_initialized is False
    assert service.export() == {}
