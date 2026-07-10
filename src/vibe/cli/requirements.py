"""Command dependency declarations."""

from __future__ import annotations

from dataclasses import dataclass

from vibe.registry import (
    SERVICE_NAME_CONFIGURATION,
    SERVICE_NAME_LIFECYCLE_MANAGER,
    SERVICE_NAME_LOGGING,
    SERVICE_NAME_SERVICE_REGISTRY,
)

FRAMEWORK_SERVICES: tuple[str, ...] = (
    SERVICE_NAME_CONFIGURATION,
    SERVICE_NAME_LOGGING,
    SERVICE_NAME_SERVICE_REGISTRY,
    SERVICE_NAME_LIFECYCLE_MANAGER,
)


@dataclass(frozen=True)
class CommandRequirements:
    """Declarative requirements for a CLI command."""

    required_services: tuple[str, ...] = ()
    bootstrap_required: bool = True
    supports_json: bool = False
    destructive: bool = False
    allow_degraded: bool = False


NO_BOOTSTRAP = CommandRequirements(
    required_services=(),
    bootstrap_required=False,
    supports_json=True,
)

FRAMEWORK_COMMAND = CommandRequirements(
    required_services=FRAMEWORK_SERVICES,
    bootstrap_required=True,
    supports_json=False,
)

CONFIG_SHOW = CommandRequirements(
    required_services=FRAMEWORK_SERVICES,
    bootstrap_required=True,
    supports_json=True,
)

CONFIG_VALIDATE = CommandRequirements(
    required_services=FRAMEWORK_SERVICES,
    bootstrap_required=True,
    supports_json=True,
)
