"""Environment variable discovery and override mapping."""

from __future__ import annotations

import os
from typing import Any

ENV_PREFIX = "VIBE_"


def discover_env_overrides(prefix: str = ENV_PREFIX) -> dict[str, Any]:
    """Discover supported environment variable overrides.

    Environment variables with the approved ``VIBE_`` prefix are converted to
    dotted configuration keys. Unsupported variables are ignored.
    """
    overrides: dict[str, Any] = {}
    for env_name, raw_value in os.environ.items():
        if not env_name.startswith(prefix):
            continue
        key = _env_name_to_config_key(env_name, prefix)
        if key is None:
            continue
        _set_nested_value(overrides, key, parse_env_value(raw_value))
    return overrides


def parse_env_value(raw_value: str) -> Any:
    """Parse an environment variable value into a supported configuration type."""
    normalized = raw_value.strip()
    lowered = normalized.lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    if normalized.isdigit() or (normalized.startswith("-") and normalized[1:].isdigit()):
        return int(normalized)
    try:
        if "." in normalized:
            return float(normalized)
    except ValueError:
        pass
    return normalized


def _env_name_to_config_key(env_name: str, prefix: str) -> str | None:
    suffix = env_name[len(prefix) :]
    if not suffix:
        return None
    return ".".join(part.lower() for part in suffix.split("_"))


def _set_nested_value(config: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    current: dict[str, Any] = config
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[parts[-1]] = value
