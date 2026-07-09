"""Environment override unit tests."""

from __future__ import annotations

import os

import pytest

from vibe.configuration.environment import discover_env_overrides, parse_env_value


@pytest.fixture
def clean_vibe_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove VIBE_ environment variables before each test."""
    for key in list(os.environ):
        if key.startswith("VIBE_"):
            monkeypatch.delenv(key, raising=False)


def test_discover_env_overrides_maps_nested_keys(
    monkeypatch: pytest.MonkeyPatch,
    clean_vibe_env: None,
) -> None:
    """Supported environment variables map to dotted configuration keys."""
    monkeypatch.setenv("VIBE_PLATFORM_NAME", "custom-platform")
    monkeypatch.setenv("VIBE_LOGGING_LEVEL", "DEBUG")
    overrides = discover_env_overrides()
    assert overrides["platform"]["name"] == "custom-platform"
    assert overrides["logging"]["level"] == "DEBUG"


def test_discover_env_overrides_ignores_unsupported_variables(
    monkeypatch: pytest.MonkeyPatch,
    clean_vibe_env: None,
) -> None:
    """Unsupported environment variables are ignored."""
    monkeypatch.setenv("OTHER_LOGGING_LEVEL", "DEBUG")
    overrides = discover_env_overrides()
    assert overrides == {}


def test_parse_env_value_converts_supported_types() -> None:
    """Environment values are parsed into supported configuration types."""
    assert parse_env_value("true") is True
    assert parse_env_value("false") is False
    assert parse_env_value("42") == 42
    assert parse_env_value("3.14") == 3.14
    assert parse_env_value("openrouter") == "openrouter"
