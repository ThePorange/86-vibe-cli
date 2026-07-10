"""Service Registry integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe.bootstrap.service import BootstrapService
from vibe.registry import (
    SERVICE_NAME_BOOTSTRAP,
    SERVICE_NAME_CONFIGURATION,
    SERVICE_NAME_LIFECYCLE_MANAGER,
    SERVICE_NAME_LOGGING,
    SERVICE_NAME_REPOSITORY,
    SERVICE_NAME_SERVICE_REGISTRY,
)
from vibe.registry.exceptions import DuplicateServiceRegistrationError
from vibe.registry.service import ServiceRegistry


def test_bootstrap_registers_platform_services(tmp_path: Path) -> None:
    """Bootstrap registers all implemented platform services."""
    service = BootstrapService(project_root=tmp_path)
    result = service.initialize()

    registry = result.service_registry
    assert registry.count == 6
    assert registry.get(SERVICE_NAME_CONFIGURATION) is service.configuration_service
    assert registry.get(SERVICE_NAME_LOGGING) is service.logging_service
    assert registry.get(SERVICE_NAME_REPOSITORY) is service.repository_service
    assert registry.get(SERVICE_NAME_BOOTSTRAP) is service
    assert registry.get(SERVICE_NAME_SERVICE_REGISTRY) is registry
    service.shutdown()


def test_registry_enumeration_after_bootstrap(tmp_path: Path) -> None:
    """Bootstrap exposes deterministic registry enumeration."""
    service = BootstrapService(project_root=tmp_path)
    result = service.initialize()

    names = tuple(descriptor.name for descriptor in result.service_registry.list_services())
    assert names == (
        SERVICE_NAME_BOOTSTRAP,
        SERVICE_NAME_CONFIGURATION,
        SERVICE_NAME_LIFECYCLE_MANAGER,
        SERVICE_NAME_LOGGING,
        SERVICE_NAME_REPOSITORY,
        SERVICE_NAME_SERVICE_REGISTRY,
    )
    service.shutdown()


def test_duplicate_registration_fails_after_bootstrap(tmp_path: Path) -> None:
    """Duplicate registration is rejected once bootstrap completes."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()

    with pytest.raises(DuplicateServiceRegistrationError):
        service.service_registry.register(
            SERVICE_NAME_LOGGING,
            service.logging_service,
        )
    service.shutdown()


def test_registry_available_through_bootstrap_accessor(tmp_path: Path) -> None:
    """Bootstrap exposes the registry after startup."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()

    assert service.service_registry.contains(SERVICE_NAME_CONFIGURATION) is True
    assert service.service_registry.get_optional(SERVICE_NAME_LOGGING) is service.logging_service
    service.shutdown()


def test_registry_state_after_shutdown(tmp_path: Path) -> None:
    """Registry entries remain after bootstrap shutdown in this work package."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()
    registry = service.service_registry
    service.shutdown()

    assert registry.count == 6
    assert registry.contains(SERVICE_NAME_BOOTSTRAP) is True


def test_injected_registry_is_registered(tmp_path: Path) -> None:
    """Bootstrap registers an injected registry instance."""
    registry = ServiceRegistry()
    service = BootstrapService(project_root=tmp_path, service_registry=registry)
    service.initialize()

    assert service.service_registry is registry
    assert registry.get(SERVICE_NAME_SERVICE_REGISTRY) is registry
    service.shutdown()
