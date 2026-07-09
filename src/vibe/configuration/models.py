"""Immutable configuration models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlatformConfig:
    """Platform metadata configuration."""

    name: str


@dataclass(frozen=True)
class RepositoryConfig:
    """Repository metadata configuration."""

    type: str
    authoritative: bool


@dataclass(frozen=True)
class AiConfig:
    """AI provider configuration."""

    provider: str
    default_model: str | None = None


@dataclass(frozen=True)
class McpConfig:
    """Model Context Protocol configuration."""

    enabled: bool


@dataclass(frozen=True)
class LoggingConfig:
    """Logging output configuration."""

    level: str
    console: bool
    file: bool
    debug: bool


@dataclass(frozen=True)
class GovernanceConfig:
    """Architecture governance configuration."""

    require_human_approval: bool
    architecture_lock: bool


@dataclass(frozen=True)
class EffectiveConfiguration:
    """Immutable validated runtime configuration."""

    data: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of the configuration mapping."""
        return _deep_copy_dict(self.data)


def build_effective_configuration(config: Mapping[str, Any]) -> EffectiveConfiguration:
    """Build an immutable effective configuration snapshot."""
    return EffectiveConfiguration(data=_deep_copy_dict(config))


def _deep_copy_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            copied[key] = _deep_copy_dict(item)
        elif isinstance(item, list):
            copied[key] = [_deep_copy_value(element) for element in item]
        else:
            copied[key] = item
    return copied


def _deep_copy_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _deep_copy_dict(value)
    if isinstance(value, list):
        return [_deep_copy_value(element) for element in value]
    return value
