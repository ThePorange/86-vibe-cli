"""Service Lifecycle Manager unit tests."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from vibe.configuration.service import ConfigurationService
from vibe.lifecycle.exceptions import (
    DependencyCycleError,
    LifecycleRegistrationError,
    LifecycleTransitionError,
)
from vibe.lifecycle.manager import ServiceLifecycleManager
from vibe.lifecycle.metadata import LifecycleServiceMetadata
from vibe.lifecycle.state import PlatformState, ServiceLifecycleState
from vibe.logging.service import LoggingService
from vibe.registry.service import ServiceRegistry


@dataclass
class _FakeBootstrap:
    configuration_service: ConfigurationService
    logging_service: LoggingService


@dataclass
class _ShutdownTracker:
    shutdown_calls: list[str] = field(default_factory=list)

    def shutdown(self) -> None:
        self.shutdown_calls.append("shutdown")


def _manager(tmp_path: Path) -> tuple[ServiceLifecycleManager, ServiceRegistry, _ShutdownTracker]:
    configuration = ConfigurationService(project_root=tmp_path)
    configuration.initialize()
    configuration.load()
    logging = LoggingService(configuration, project_root=tmp_path)
    logging.initialize()
    registry = ServiceRegistry()
    bootstrap = _FakeBootstrap(configuration, logging)
    manager = ServiceLifecycleManager(
        configuration_service=configuration,
        logging_service=logging,
        bootstrap_service=bootstrap,  # type: ignore[arg-type]
        service_registry=registry,
    )
    tracker = _ShutdownTracker()
    return manager, registry, tracker


def test_initialize_and_register_service(tmp_path: Path) -> None:
    """Lifecycle manager registers managed services."""
    manager, registry, tracker = _manager(tmp_path)
    manager.initialize()
    registry.register("example", tracker)

    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="example",
            name="Example",
            version="0.1.0",
        ),
    )

    record = manager.get_service("example")
    assert record.state == ServiceLifecycleState.REGISTERED
    assert manager.list_services()[0].metadata.service_id == "example"


def test_duplicate_registration_raises(tmp_path: Path) -> None:
    """Duplicate managed service identifiers are rejected."""
    manager, registry, tracker = _manager(tmp_path)
    manager.initialize()
    registry.register("example", tracker)
    metadata = LifecycleServiceMetadata(
        service_id="example",
        name="Example",
        version="0.1.0",
    )
    manager.register(tracker, metadata)
    with pytest.raises(LifecycleRegistrationError):
        manager.register(tracker, metadata)


def test_ready_transition_requires_dependencies(tmp_path: Path) -> None:
    """READY transitions require ready dependencies."""
    manager, registry, tracker = _manager(tmp_path)
    manager.initialize()
    registry.register("dependency", tracker)
    registry.register("example", tracker)
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="dependency",
            name="Dependency",
            version="0.1.0",
        ),
    )
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="example",
            name="Example",
            version="0.1.0",
            required_dependencies=("dependency",),
        ),
    )
    manager.transition("dependency", ServiceLifecycleState.READY)
    manager.transition("example", ServiceLifecycleState.READY)
    assert manager.get_service("example").state == ServiceLifecycleState.READY


def test_ready_transition_fails_for_unready_dependency(tmp_path: Path) -> None:
    """READY transitions fail when dependencies are not ready."""
    manager, registry, tracker = _manager(tmp_path)
    manager.initialize()
    registry.register("dependency", tracker)
    registry.register("example", tracker)
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="dependency",
            name="Dependency",
            version="0.1.0",
        ),
    )
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="example",
            name="Example",
            version="0.1.0",
            required_dependencies=("dependency",),
        ),
    )
    with pytest.raises(LifecycleTransitionError):
        manager.transition("example", ServiceLifecycleState.READY)


def test_cycle_detection_rejects_invalid_graph(tmp_path: Path) -> None:
    """Dependency cycles are rejected during registration."""
    manager, registry, tracker = _manager(tmp_path)
    manager.initialize()
    registry.register("service_a", tracker)
    registry.register("service_b", tracker)
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="service_a",
            name="Service A",
            version="0.1.0",
            required_dependencies=("service_b",),
        ),
    )
    with pytest.raises(DependencyCycleError):
        manager.register(
            tracker,
            LifecycleServiceMetadata(
                service_id="service_b",
                name="Service B",
                version="0.1.0",
                required_dependencies=("service_a",),
            ),
        )


def test_platform_status_reflects_managed_services(tmp_path: Path) -> None:
    """Platform status is derived from managed service states."""
    manager, registry, tracker = _manager(tmp_path)
    manager.initialize()
    registry.register("example", tracker)
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="example",
            name="Example",
            version="0.1.0",
        ),
    )
    manager.transition("example", ServiceLifecycleState.READY)
    status = manager.status()
    assert status.state == PlatformState.READY
    assert status.ready_services == 1


def test_shutdown_invokes_service_shutdown_in_dependency_order(tmp_path: Path) -> None:
    """Shutdown coordinates service shutdown in reverse dependency order."""
    manager, registry, dependency = _manager(tmp_path)
    dependent = _ShutdownTracker()
    manager.initialize()
    registry.register("dependency", dependency)
    registry.register("dependent", dependent)
    manager.register(
        dependency,
        LifecycleServiceMetadata(
            service_id="dependency",
            name="Dependency",
            version="0.1.0",
        ),
    )
    manager.register(
        dependent,
        LifecycleServiceMetadata(
            service_id="dependent",
            name="Dependent",
            version="0.1.0",
            required_dependencies=("dependency",),
        ),
    )
    manager.transition("dependency", ServiceLifecycleState.READY)
    manager.transition("dependent", ServiceLifecycleState.READY)
    manager.shutdown()

    assert dependent.shutdown_calls == ["shutdown"]
    assert manager.get_service("dependent").state == ServiceLifecycleState.STOPPED
    assert manager.get_service("dependency").state == ServiceLifecycleState.STOPPED


def test_lifecycle_events_are_published_to_subscribers(tmp_path: Path) -> None:
    """Lifecycle transitions publish events to subscribers."""
    manager, registry, tracker = _manager(tmp_path)
    events: list[str] = []
    manager.initialize()
    manager.subscribe(lambda event: events.append(event.event_type.value))
    registry.register("example", tracker)
    manager.register(
        tracker,
        LifecycleServiceMetadata(
            service_id="example",
            name="Example",
            version="0.1.0",
        ),
    )
    manager.transition("example", ServiceLifecycleState.READY)
    assert "service_ready" in events


def test_concurrent_registrations_remain_consistent(tmp_path: Path) -> None:
    """Concurrent registrations preserve lifecycle integrity."""
    manager, registry, _tracker = _manager(tmp_path)
    manager.initialize()
    errors: list[Exception] = []

    def register_service(index: int) -> None:
        tracker = _ShutdownTracker()
        try:
            registry.register(f"service-{index}", tracker)
            manager.register(
                tracker,
                LifecycleServiceMetadata(
                    service_id=f"service-{index}",
                    name=f"Service {index}",
                    version="0.1.0",
                ),
            )
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=register_service, args=(index,)) for index in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert manager.status().service_count == 10
