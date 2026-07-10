"""Service Registry unit tests."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC

import pytest

from vibe.registry.exceptions import (
    DuplicateServiceRegistrationError,
    InvalidServiceRegistrationError,
    ServiceNotFoundError,
)
from vibe.registry.metadata import ServiceMetadata
from vibe.registry.service import ServiceRegistry


@dataclass
class _FakeLogger:
    messages: list[tuple[str, dict[str, object]]] = field(default_factory=list)

    def info(self, message: str, **fields: object) -> None:
        self.messages.append((message, fields))

    def warning(self, message: str, **fields: object) -> None:
        self.messages.append((message, fields))

    def debug(self, message: str, **fields: object) -> None:
        self.messages.append((message, fields))


class _ExampleService:
    """Simple service instance for registry tests."""


def test_valid_registration() -> None:
    """Valid registrations are available for lookup."""
    registry = ServiceRegistry()
    service = _ExampleService()
    metadata = ServiceMetadata(name="example", service_type="_ExampleService")

    registry.register("example", service, metadata)

    assert registry.contains("example") is True
    assert registry.get("example") is service
    assert registry.count == 1


def test_duplicate_registration_raises() -> None:
    """Duplicate service names are rejected."""
    registry = ServiceRegistry()
    registry.register("example", _ExampleService())

    with pytest.raises(DuplicateServiceRegistrationError):
        registry.register("example", _ExampleService())


def test_invalid_service_name_raises() -> None:
    """Empty and whitespace service names are rejected."""
    registry = ServiceRegistry()

    with pytest.raises(InvalidServiceRegistrationError):
        registry.register("", _ExampleService())
    with pytest.raises(InvalidServiceRegistrationError):
        registry.register("   ", _ExampleService())
    with pytest.raises(InvalidServiceRegistrationError):
        registry.register(" leading", _ExampleService())


def test_missing_service_instance_raises() -> None:
    """None service instances are rejected."""
    registry = ServiceRegistry()

    with pytest.raises(InvalidServiceRegistrationError):
        registry.register("example", None)  # type: ignore[arg-type]


def test_invalid_metadata_type_raises() -> None:
    """Metadata must be a ServiceMetadata instance when supplied."""
    registry = ServiceRegistry()

    with pytest.raises(InvalidServiceRegistrationError):
        registry.register("example", _ExampleService(), metadata="invalid")  # type: ignore[arg-type]


def test_metadata_name_mismatch_raises() -> None:
    """Metadata name must match the registration name."""
    registry = ServiceRegistry()
    metadata = ServiceMetadata(name="other", service_type="_ExampleService")

    with pytest.raises(InvalidServiceRegistrationError):
        registry.register("example", _ExampleService(), metadata)


def test_get_raises_for_missing_service() -> None:
    """Lookup by name raises when the service is absent."""
    registry = ServiceRegistry()

    with pytest.raises(ServiceNotFoundError):
        registry.get("missing")


def test_get_optional_returns_none_for_missing_service() -> None:
    """Optional lookup returns None for absent services."""
    registry = ServiceRegistry()
    assert registry.get_optional("missing") is None


def test_lookup_after_unregister() -> None:
    """Unregistered services are no longer available."""
    registry = ServiceRegistry()
    registry.register("example", _ExampleService())
    registry.unregister("example")

    assert registry.contains("example") is False
    assert registry.get_optional("example") is None
    with pytest.raises(ServiceNotFoundError):
        registry.get("example")


def test_unregister_missing_service_raises() -> None:
    """Unregistering an absent service raises ServiceNotFoundError."""
    registry = ServiceRegistry()

    with pytest.raises(ServiceNotFoundError):
        registry.unregister("missing")


def test_list_services_is_sorted_alphabetically() -> None:
    """Service enumeration is deterministic and alphabetical."""
    registry = ServiceRegistry()
    registry.register("logging", _ExampleService())
    registry.register("bootstrap", _ExampleService())
    registry.register("configuration", _ExampleService())

    names = tuple(descriptor.name for descriptor in registry.list_services())
    assert names == ("bootstrap", "configuration", "logging")


def test_descriptor_correctness() -> None:
    """Descriptors expose metadata and UTC registration timestamps."""
    registry = ServiceRegistry()
    metadata = ServiceMetadata(
        name="logging",
        service_type="LoggingService",
        package="vibe.logging",
        description="Platform logging",
    )
    registry.register("logging", _ExampleService(), metadata)

    descriptor = registry.list_services()[0]
    assert descriptor.name == "logging"
    assert descriptor.service_type == "LoggingService"
    assert descriptor.metadata is metadata
    assert descriptor.registered_at.tzinfo is UTC


def test_auto_generated_metadata() -> None:
    """Missing metadata is derived from the service instance."""
    registry = ServiceRegistry()
    service = _ExampleService()
    registry.register("example", service)

    descriptor = registry.list_services()[0]
    assert descriptor.metadata.name == "example"
    assert descriptor.metadata.service_type == "_ExampleService"


def test_clear_removes_all_state() -> None:
    """Clearing removes instances, metadata, and descriptors."""
    registry = ServiceRegistry()
    registry.register("one", _ExampleService())
    registry.register("two", _ExampleService())
    registry.clear()

    assert registry.count == 0
    assert registry.list_services() == ()


def test_registry_logs_registration_events() -> None:
    """Registry logs registration, duplicate, unregister, and clear events."""
    logger = _FakeLogger()
    registry = ServiceRegistry(logger=logger)  # type: ignore[arg-type]
    registry.register("example", _ExampleService())

    with pytest.raises(DuplicateServiceRegistrationError):
        registry.register("example", _ExampleService())

    registry.unregister("example")
    registry.register("other", _ExampleService())
    registry.clear()

    messages = [message for message, _fields in logger.messages]
    assert "Service registered" in messages
    assert "Duplicate service registration rejected" in messages
    assert "Service unregistered" in messages
    assert "Service registry cleared" in messages


def test_get_logs_lookup_failure() -> None:
    """Failed lookups are logged when a logger is attached."""
    logger = _FakeLogger()
    registry = ServiceRegistry(logger=logger)  # type: ignore[arg-type]

    with pytest.raises(ServiceNotFoundError):
        registry.get("missing")

    messages = [message for message, _fields in logger.messages]
    assert "Service lookup failed" in messages


def test_concurrent_registrations_preserve_integrity() -> None:
    """Concurrent registrations on unique names preserve registry integrity."""
    registry = ServiceRegistry()
    errors: list[Exception] = []

    def register_service(index: int) -> None:
        try:
            registry.register(f"service-{index}", _ExampleService())
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=register_service, args=(index,)) for index in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert registry.count == 20


def test_concurrent_duplicate_registration_is_rejected() -> None:
    """Concurrent duplicate registrations leave a single entry."""
    registry = ServiceRegistry()
    barrier = threading.Barrier(2)
    results: list[Exception | None] = []

    def attempt_registration() -> None:
        try:
            barrier.wait(timeout=1)
            registry.register("shared", _ExampleService())
            results.append(None)
        except Exception as exc:
            results.append(exc)

    threads = [threading.Thread(target=attempt_registration) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert registry.count == 1
    assert sum(isinstance(result, DuplicateServiceRegistrationError) for result in results) == 1


def test_concurrent_lookups_are_consistent() -> None:
    """Concurrent lookups return the same registered instance."""
    registry = ServiceRegistry()
    service = _ExampleService()
    registry.register("example", service)
    observed: list[object] = []

    def lookup_service() -> None:
        observed.append(registry.get("example"))

    threads = [threading.Thread(target=lookup_service) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert all(item is service for item in observed)


def test_concurrent_unregister_and_lookup() -> None:
    """Concurrent unregister and lookup do not corrupt registry state."""
    registry = ServiceRegistry()
    registry.register("example", _ExampleService())
    errors: list[Exception] = []

    def unregister_service() -> None:
        try:
            registry.unregister("example")
        except Exception as exc:
            errors.append(exc)

    def lookup_service() -> None:
        try:
            registry.get_optional("example")
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=unregister_service),
        *[threading.Thread(target=lookup_service) for _ in range(5)],
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert registry.count in {0, 1}
    assert all(not isinstance(error, DuplicateServiceRegistrationError) for error in errors)


def test_concurrent_clear_preserves_integrity() -> None:
    """Concurrent clear operations leave the registry empty."""
    registry = ServiceRegistry()
    for index in range(10):
        registry.register(f"service-{index}", _ExampleService())

    def clear_registry() -> None:
        registry.clear()

    threads = [threading.Thread(target=clear_registry) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert registry.count == 0
    assert registry.list_services() == ()
