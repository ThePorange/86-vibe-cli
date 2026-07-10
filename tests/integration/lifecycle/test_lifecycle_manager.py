"""Service Lifecycle Manager integration tests."""

from __future__ import annotations

from pathlib import Path

from vibe.bootstrap.service import BootstrapService
from vibe.lifecycle.state import PlatformState, ServiceLifecycleState
from vibe.registry import (
    SERVICE_NAME_BOOTSTRAP,
    SERVICE_NAME_CONFIGURATION,
    SERVICE_NAME_LIFECYCLE_MANAGER,
    SERVICE_NAME_LOGGING,
    SERVICE_NAME_REPOSITORY,
    SERVICE_NAME_SERVICE_REGISTRY,
)


def test_bootstrap_initializes_lifecycle_manager(tmp_path: Path) -> None:
    """Bootstrap constructs and initializes the lifecycle manager."""
    service = BootstrapService(project_root=tmp_path)
    result = service.initialize()

    assert result.lifecycle_manager.is_initialized is True
    assert service.lifecycle_manager is result.lifecycle_manager
    service.shutdown()


def test_lifecycle_manager_registers_platform_services(tmp_path: Path) -> None:
    """Lifecycle manager tracks all implemented platform services."""
    service = BootstrapService(project_root=tmp_path)
    result = service.initialize()
    manager = result.lifecycle_manager

    service_ids = tuple(record.metadata.service_id for record in manager.list_services())
    assert service_ids == (
        SERVICE_NAME_BOOTSTRAP,
        SERVICE_NAME_CONFIGURATION,
        SERVICE_NAME_LIFECYCLE_MANAGER,
        SERVICE_NAME_LOGGING,
        SERVICE_NAME_REPOSITORY,
        SERVICE_NAME_SERVICE_REGISTRY,
    )
    states = {record.metadata.service_id: record.state for record in manager.list_services()}
    for service_id in (
        SERVICE_NAME_BOOTSTRAP,
        SERVICE_NAME_CONFIGURATION,
        SERVICE_NAME_LIFECYCLE_MANAGER,
        SERVICE_NAME_LOGGING,
        SERVICE_NAME_SERVICE_REGISTRY,
    ):
        assert states[service_id] == ServiceLifecycleState.READY
    assert states[SERVICE_NAME_REPOSITORY] in {
        ServiceLifecycleState.READY,
        ServiceLifecycleState.FAILED,
    }
    service.shutdown()


def test_registry_contains_lifecycle_manager(tmp_path: Path) -> None:
    """Lifecycle manager is registered in the service registry."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()

    assert service.service_registry.contains(SERVICE_NAME_LIFECYCLE_MANAGER) is True
    assert service.service_registry.get(SERVICE_NAME_LIFECYCLE_MANAGER) is service.lifecycle_manager
    service.shutdown()


def test_platform_status_ready_after_bootstrap(cli_repo: Path) -> None:
    """Platform lifecycle status is READY after bootstrap with a valid repository."""
    service = BootstrapService(project_root=cli_repo)
    service.initialize()

    status = service.lifecycle_manager.status()
    assert status.state == PlatformState.READY
    assert status.service_count == 6
    assert status.ready_services == 6
    service.shutdown()


def test_orderly_shutdown_via_lifecycle_manager(tmp_path: Path) -> None:
    """Bootstrap shutdown delegates to lifecycle-aware coordination."""
    service = BootstrapService(project_root=tmp_path)
    service.initialize()
    configuration = service.configuration_service
    logging = service.logging_service
    lifecycle_manager = service.lifecycle_manager
    service.shutdown()

    assert configuration.is_initialized is False
    assert logging.is_initialized is False
    assert lifecycle_manager.status().state == PlatformState.STOPPED
