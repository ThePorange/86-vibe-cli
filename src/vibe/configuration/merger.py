"""Configuration merge and precedence resolution."""

from __future__ import annotations

from typing import Any


def merge_configurations(*sources: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge configuration sources in precedence order.

    Later sources override earlier sources without mutating the originals.
    """
    merged: dict[str, Any] = {}
    for source in sources:
        merged = _deep_merge(merged, _deep_copy(source))
    return merged


def apply_dotted_overrides(
    config: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Apply dotted-key overrides onto a configuration mapping."""
    result = _deep_copy(config)
    for key, value in overrides.items():
        if "." in key:
            _set_dotted_value(result, key, value)
        else:
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = _deep_merge(result[key], _deep_copy(value))
            else:
                result[key] = _deep_copy(value)
    return result


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_copy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = _deep_copy(value)
    return merged


def _set_dotted_value(config: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    current: dict[str, Any] = config
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[parts[-1]] = _deep_copy(value)


def _deep_copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _deep_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    return value
