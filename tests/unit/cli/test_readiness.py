"""Service readiness validation tests."""

from __future__ import annotations

import pytest

from vibe.cli.errors import CLIServiceUnavailableError
from vibe.cli.execution import validate_service_readiness
from vibe.lifecycle.health import ServiceHealthState
from vibe.lifecycle.manager import ServiceLifecycleManager
from vibe.lifecycle.metadata import LifecycleServiceMetadata
from vibe.lifecycle.state import ServiceLifecycleState
from vibe.registry.service import ServiceRegistry
from vibe.version import PLATFORM_VERSION


def _register_service(
    registry: ServiceRegistry,
    lifecycle: ServiceLifecycleManager,
    service_id: str,
    *,
    state: ServiceLifecycleState,
    health: ServiceHealthState | None = None,
) -> None:
    service = object()
    registry.register(service_id, service)
    lifecycle.register(
        service,
        LifecycleServiceMetadata(
            service_id=service_id,
            name=service_id,
            version=PLATFORM_VERSION,
        ),
    )
    lifecycle.transition(service_id, state)
    if health is not None:
        entry = lifecycle._entries[service_id]  # noqa: SLF001
        entry.health = health


def test_ready_service_passes() -> None:
    """Ready services satisfy readiness validation."""
    registry = ServiceRegistry()
    lifecycle = ServiceLifecycleManager(
        configuration_service=object(),  # type: ignore[arg-type]
        logging_service=object(),  # type: ignore[arg-type]
        bootstrap_service=object(),  # type: ignore[arg-type]
        service_registry=registry,
    )
    lifecycle._initialized = True  # noqa: SLF001
    _register_service(registry, lifecycle, "configuration", state=ServiceLifecycleState.READY)
    validate_service_readiness(registry, lifecycle, ("configuration",))


def test_missing_service_fails() -> None:
    """Missing registry entries fail readiness validation."""
    registry = ServiceRegistry()
    lifecycle = ServiceLifecycleManager(
        configuration_service=object(),  # type: ignore[arg-type]
        logging_service=object(),  # type: ignore[arg-type]
        bootstrap_service=object(),  # type: ignore[arg-type]
        service_registry=registry,
    )
    lifecycle._initialized = True  # noqa: SLF001
    with pytest.raises(CLIServiceUnavailableError):
        validate_service_readiness(registry, lifecycle, ("configuration",))


def test_failed_service_fails() -> None:
    """Failed lifecycle states fail readiness validation."""
    registry = ServiceRegistry()
    lifecycle = ServiceLifecycleManager(
        configuration_service=object(),  # type: ignore[arg-type]
        logging_service=object(),  # type: ignore[arg-type]
        bootstrap_service=object(),  # type: ignore[arg-type]
        service_registry=registry,
    )
    lifecycle._initialized = True  # noqa: SLF001
    _register_service(registry, lifecycle, "configuration", state=ServiceLifecycleState.FAILED)
    with pytest.raises(CLIServiceUnavailableError):
        validate_service_readiness(registry, lifecycle, ("configuration",))


def test_health_failed_service_fails() -> None:
    """Health-failed ready services fail readiness validation."""
    registry = ServiceRegistry()
    lifecycle = ServiceLifecycleManager(
        configuration_service=object(),  # type: ignore[arg-type]
        logging_service=object(),  # type: ignore[arg-type]
        bootstrap_service=object(),  # type: ignore[arg-type]
        service_registry=registry,
    )
    lifecycle._initialized = True  # noqa: SLF001
    _register_service(
        registry,
        lifecycle,
        "configuration",
        state=ServiceLifecycleState.READY,
        health=ServiceHealthState.FAILED,
    )
    with pytest.raises(CLIServiceUnavailableError):
        validate_service_readiness(registry, lifecycle, ("configuration",))
