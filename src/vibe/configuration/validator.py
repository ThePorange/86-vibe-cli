"""Configuration schema validation."""

from __future__ import annotations

from typing import Any

from vibe.configuration.exceptions import ConfigurationValidationError

LOGGING_LEVELS = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
REPOSITORY_TYPES = {"platform", "application", "library", "example"}
KNOWN_SECTIONS = {
    "platform",
    "repository",
    "ai",
    "mcp",
    "logging",
    "governance",
    "experimental",
}


def validate_configuration(config: dict[str, Any]) -> None:
    """Validate required values, supported types, and known section constraints.

    Args:
        config:
            Effective configuration mapping to validate.

    Raises:
        ConfigurationValidationError:
            When validation fails.
    """
    _validate_required_key(config, "platform", "platform")
    platform = _require_mapping(config, "platform")
    _validate_string(platform, "name", required=True)

    if "repository" in config:
        repository = _require_mapping(config, "repository")
        if "type" in repository:
            _validate_enum(repository, "type", REPOSITORY_TYPES)
        if "authoritative" in repository:
            _validate_bool(repository, "authoritative")

    if "ai" in config:
        ai = _require_mapping(config, "ai")
        if "provider" in ai:
            _validate_string(ai, "provider")
        if "default_model" in ai:
            _validate_string(ai, "default_model")

    if "mcp" in config:
        mcp = _require_mapping(config, "mcp")
        if "enabled" in mcp:
            _validate_bool(mcp, "enabled")

    if "logging" in config:
        logging_config = _require_mapping(config, "logging")
        if "level" in logging_config:
            _validate_logging_level(logging_config, "level")
        for key in ("console", "file", "debug"):
            if key in logging_config:
                _validate_bool(logging_config, key)

    if "governance" in config:
        governance = _require_mapping(config, "governance")
        for key in ("require_human_approval", "architecture_lock"):
            if key in governance:
                _validate_bool(governance, key)

    if "experimental" in config:
        _require_mapping(config, "experimental")

    for section_name, section_value in config.items():
        if section_name in KNOWN_SECTIONS:
            continue
        if (
            not isinstance(section_value, (dict, list, str, int, float, bool))
            and section_value is not None
        ):
            raise ConfigurationValidationError(
                f"Unsupported value type for configuration section '{section_name}'"
            )


def _validate_required_key(config: dict[str, Any], key: str, label: str) -> None:
    if key not in config:
        raise ConfigurationValidationError(f"Missing required configuration section: {label}")


def _require_mapping(config: dict[str, Any], section: str) -> dict[str, Any]:
    value = config.get(section)
    if not isinstance(value, dict):
        raise ConfigurationValidationError(f"Configuration section '{section}' must be a mapping")
    return value


def _validate_string(mapping: dict[str, Any], key: str, *, required: bool = False) -> None:
    if key not in mapping:
        if required:
            raise ConfigurationValidationError(f"Missing required configuration key: {key}")
        return
    if not isinstance(mapping[key], str) or not mapping[key].strip():
        raise ConfigurationValidationError(f"Configuration key '{key}' must be a non-empty string")


def _validate_bool(mapping: dict[str, Any], key: str) -> None:
    if not isinstance(mapping[key], bool):
        raise ConfigurationValidationError(f"Configuration key '{key}' must be a boolean")


def _validate_enum(mapping: dict[str, Any], key: str, allowed: set[str]) -> None:
    value = mapping[key]
    if not isinstance(value, str) or value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ConfigurationValidationError(
            f"Configuration key '{key}' must be one of: {allowed_values}"
        )


def _validate_logging_level(mapping: dict[str, Any], key: str) -> None:
    value = mapping[key]
    if not isinstance(value, str) or value.upper() not in LOGGING_LEVELS:
        allowed_values = ", ".join(sorted(LOGGING_LEVELS))
        raise ConfigurationValidationError(
            f"Configuration key '{key}' must be one of: {allowed_values}"
        )
