"""Merger unit tests."""

from __future__ import annotations

from vibe.configuration.merger import apply_dotted_overrides, merge_configurations


def test_merge_configurations_applies_precedence() -> None:
    """Later sources override earlier sources without mutating originals."""
    defaults = {"platform": {"name": "default"}, "logging": {"level": "INFO"}}
    project = {"platform": {"name": "project"}}
    env = {"logging": {"level": "DEBUG"}}
    merged = merge_configurations(defaults, project, env)
    assert merged["platform"]["name"] == "project"
    assert merged["logging"]["level"] == "DEBUG"
    assert defaults["platform"]["name"] == "default"


def test_apply_dotted_overrides_sets_nested_values() -> None:
    """Runtime dotted overrides replace nested configuration values."""
    config = {"logging": {"level": "INFO"}}
    updated = apply_dotted_overrides(config, {"logging.level": "TRACE"})
    assert updated["logging"]["level"] == "TRACE"
    assert config["logging"]["level"] == "INFO"
