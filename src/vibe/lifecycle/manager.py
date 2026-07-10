"""Service Lifecycle Manager orchestration and public API."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from vibe.configuration.exceptions import ConfigurationKeyError
from vibe.lifecycle.dependency import (
    detect_cycle,
    shutdown_order,
    validate_dependency_metadata,
    validate_service_identifier,
)
from vibe.lifecycle.events import (
    LifecycleEvent,
    LifecycleEventDispatcher,
    LifecycleEventHandler,
    LifecycleEventType,
)
from vibe.lifecycle.exceptions import (
    LifecycleRegistrationError,
    LifecycleShutdownError,
    LifecycleTransitionError,
)
from vibe.lifecycle.health import (
    PlatformHealthSummary,
    ServiceHealthState,
    build_health_summary,
    health_for_lifecycle_state,
)
from vibe.lifecycle.metadata import LifecycleServiceMetadata
from vibe.lifecycle.models import ManagedServiceRecord, PlatformLifecycleStatus
from vibe.lifecycle.state import PlatformState, ServiceLifecycleState, validate_transition

if TYPE_CHECKING:
    from vibe.bootstrap.service import BootstrapService
    from vibe.configuration.service import ConfigurationService
    from vibe.logging.logger import PlatformLogger
    from vibe.logging.service import LoggingService
    from vibe.registry.service import ServiceRegistry

_NON_SHUTDOWN_SERVICE_IDS = frozenset({"bootstrap", "lifecycle_manager"})


@dataclass
class _ManagedServiceEntry:
    """Mutable internal lifecycle record."""

    metadata: LifecycleServiceMetadata
    service: object
    state: ServiceLifecycleState
    health: ServiceHealthState
    registered_at: datetime
    updated_at: datetime
    message: str | None = None


class ServiceLifecycleManager:
    """Authoritative lifecycle management for platform services."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        logging_service: LoggingService,
        bootstrap_service: BootstrapService,
        service_registry: ServiceRegistry,
        *,
        logger: PlatformLogger | None = None,
    ) -> None:
        """Initialize the lifecycle manager.

        Args:
            configuration_service:
                Configuration service supplying lifecycle settings.
            logging_service:
                Logging service for lifecycle diagnostics.
            bootstrap_service:
                Bootstrap service that owns platform startup.
            service_registry:
                Authoritative runtime service catalog.
            logger:
                Optional platform logger for lifecycle diagnostics.
        """
        self._configuration_service = configuration_service
        self._logging_service = logging_service
        self._bootstrap_service = bootstrap_service
        self._service_registry = service_registry
        self._logger = logger
        self._entries: dict[str, _ManagedServiceEntry] = {}
        self._dispatcher = LifecycleEventDispatcher(logger=logger)
        self._lock = threading.RLock()
        self._initialized = False
        self._shutdown_in_progress = False
        self._accepting_registrations = True
        self._validate_dependencies = True

    @property
    def is_initialized(self) -> bool:
        """Return whether the lifecycle manager has been initialized."""
        with self._lock:
            return self._initialized

    def initialize(self) -> None:
        """Initialize lifecycle management using platform configuration."""
        with self._lock:
            if self._initialized:
                return

            try:
                section = self._configuration_service.get_section("lifecycle")
            except ConfigurationKeyError:
                section = {}
            self._validate_dependencies = bool(section.get("validate_dependencies", True))
            if self._logger is None:
                self._logger = self._logging_service.get_logger("lifecycle")
                self._dispatcher = LifecycleEventDispatcher(logger=self._logger)

            self._initialized = True
            self._log_info("Lifecycle manager initialized")
            self._publish_system_event(
                LifecycleEventType.LIFECYCLE_MANAGER_INITIALIZED,
                service_id="lifecycle_manager",
                previous_state=None,
                current_state=ServiceLifecycleState.READY,
            )

    def register(
        self,
        service: object,
        metadata: LifecycleServiceMetadata,
    ) -> None:
        """Register a managed platform service.

        Args:
            service:
                Initialized service instance.
            metadata:
                Immutable lifecycle metadata.

        Raises:
            LifecycleRegistrationError:
                When registration is not permitted.
            DependencyValidationError:
                When dependency metadata is invalid.
            DependencyCycleError:
                When dependency metadata introduces a cycle.
        """
        self._require_initialized()
        self._require_accepting_registrations()

        if service is None:
            raise LifecycleRegistrationError("Service instance must not be None.")
        if not isinstance(metadata, LifecycleServiceMetadata):
            raise LifecycleRegistrationError(
                "Metadata must be a LifecycleServiceMetadata instance."
            )

        validate_dependency_metadata(metadata)

        with self._lock:
            if metadata.service_id in self._entries:
                raise LifecycleRegistrationError(
                    f"Service '{metadata.service_id}' is already registered."
                )

            known_dependencies = {
                service_id: entry.metadata.required_dependencies
                for service_id, entry in self._entries.items()
            }
            if self._validate_dependencies:
                detect_cycle(
                    metadata.service_id,
                    metadata.required_dependencies,
                    known_dependencies,
                )

            now = datetime.now(UTC)
            entry = _ManagedServiceEntry(
                metadata=metadata,
                service=service,
                state=ServiceLifecycleState.REGISTERED,
                health=ServiceHealthState.UNKNOWN,
                registered_at=now,
                updated_at=now,
            )
            self._entries[metadata.service_id] = entry
            self._log_info("Service registered", service_id=metadata.service_id)
            self._publish_event(
                LifecycleEventType.SERVICE_REGISTERED,
                metadata.service_id,
                None,
                ServiceLifecycleState.REGISTERED,
            )

    def unregister(self, service_id: str) -> None:
        """Remove a managed service registration.

        Args:
            service_id:
                Managed service identifier.

        Raises:
            LifecycleRegistrationError:
                When the service is not registered.
        """
        self._require_initialized()
        validated_id = validate_service_identifier(service_id)

        with self._lock:
            entry = self._entries.pop(validated_id, None)
            if entry is None:
                raise LifecycleRegistrationError(f"Service '{validated_id}' is not registered.")

            self._publish_event(
                LifecycleEventType.SERVICE_UNREGISTERED,
                validated_id,
                entry.state,
                entry.state,
            )

    def get_service(self, service_id: str) -> ManagedServiceRecord:
        """Return an immutable managed service record.

        Args:
            service_id:
                Managed service identifier.

        Raises:
            LifecycleRegistrationError:
                When the service is not registered.
        """
        self._require_initialized()
        validated_id = validate_service_identifier(service_id)

        with self._lock:
            entry = self._entries.get(validated_id)
            if entry is None:
                raise LifecycleRegistrationError(f"Service '{validated_id}' is not registered.")
            return self._snapshot(entry)

    def list_services(self) -> tuple[ManagedServiceRecord, ...]:
        """Return immutable managed service records sorted by identifier."""
        self._require_initialized()
        with self._lock:
            return tuple(
                self._snapshot(self._entries[service_id])
                for service_id in sorted(self._entries)
            )

    def transition(
        self,
        service_id: str,
        state: ServiceLifecycleState,
        *,
        message: str | None = None,
    ) -> LifecycleEvent:
        """Transition a managed service to a new lifecycle state.

        Args:
            service_id:
                Managed service identifier.
            state:
                Target lifecycle state.
            message:
                Optional diagnostic message.

        Returns:
            Published lifecycle event for the transition.

        Raises:
            LifecycleTransitionError:
                When the transition is invalid or dependencies are unsatisfied.
            LifecycleRegistrationError:
                When the service is not registered.
        """
        self._require_initialized()
        validated_id = validate_service_identifier(service_id)

        with self._lock:
            entry = self._entries.get(validated_id)
            if entry is None:
                raise LifecycleRegistrationError(f"Service '{validated_id}' is not registered.")

            previous_state = entry.state
            validate_transition(previous_state, state)

            if state == ServiceLifecycleState.READY:
                self._validate_ready_transition(entry)

            entry.state = state
            entry.health = health_for_lifecycle_state(state)
            entry.updated_at = datetime.now(UTC)
            entry.message = message

            event_type = self._dispatcher.event_type_for_state(state)
            if event_type is None:
                event_type = LifecycleEventType.SERVICE_REGISTERED

            event = self._build_event(
                event_type,
                validated_id,
                previous_state,
                state,
                message,
            )
            self._log_info(
                "Service transitioned",
                service_id=validated_id,
                previous_state=previous_state.value,
                current_state=state.value,
            )
            self._dispatcher.publish(event)
            return event

    def status(self) -> PlatformLifecycleStatus:
        """Return the derived platform lifecycle status."""
        self._require_initialized()
        with self._lock:
            records = tuple(self._snapshot(entry) for entry in self._entries.values())
            ready_services = sum(
                1 for record in records if record.state == ServiceLifecycleState.READY
            )
            degraded_services = sum(
                1 for record in records if record.state == ServiceLifecycleState.DEGRADED
            )
            failed_services = sum(
                1 for record in records if record.state == ServiceLifecycleState.FAILED
            )
            stopping_services = sum(
                1 for record in records if record.state == ServiceLifecycleState.STOPPING
            )
            platform_state = self._derive_platform_state(records)
            return PlatformLifecycleStatus(
                state=platform_state,
                service_count=len(records),
                ready_services=ready_services,
                degraded_services=degraded_services,
                failed_services=failed_services,
                stopping_services=stopping_services,
            )

    def health(self) -> PlatformHealthSummary:
        """Return the derived platform health summary."""
        self._require_initialized()
        with self._lock:
            records = tuple(self._snapshot(entry) for entry in self._entries.values())
            return build_health_summary(records)

    def shutdown(self) -> None:
        """Coordinate dependency-aware shutdown of managed services.

        Raises:
            LifecycleShutdownError:
                When one or more shutdown operations fail.
        """
        self._require_initialized()

        with self._lock:
            if self._shutdown_in_progress:
                return
            self._shutdown_in_progress = True
            self._accepting_registrations = False

        self._log_info("Lifecycle shutdown started")
        self._publish_system_event(
            LifecycleEventType.LIFECYCLE_SHUTDOWN_STARTED,
            service_id="lifecycle_manager",
            previous_state=None,
            current_state=ServiceLifecycleState.STOPPING,
        )

        shutdown_errors: list[Exception] = []

        with self._lock:
            service_ids = tuple(sorted(self._entries))
            dependency_map = {
                service_id: entry.metadata.required_dependencies
                for service_id, entry in self._entries.items()
            }

        for service_id in shutdown_order(service_ids, dependency_map):
            if service_id == "lifecycle_manager":
                continue
            try:
                self._shutdown_service(service_id)
            except Exception as exc:
                shutdown_errors.append(exc)
                self._log_error(
                    "Service shutdown failed",
                    service_id=service_id,
                    error_type=type(exc).__name__,
                )

        with self._lock:
            if "lifecycle_manager" in self._entries:
                entry = self._entries["lifecycle_manager"]
                if entry.state != ServiceLifecycleState.STOPPED:
                    self._transition_locked(
                        "lifecycle_manager",
                        ServiceLifecycleState.STOPPING,
                        message="Lifecycle manager shutting down",
                    )
                    self._transition_locked(
                        "lifecycle_manager",
                        ServiceLifecycleState.STOPPED,
                        message="Lifecycle manager stopped",
                    )

        self._log_info("Lifecycle shutdown completed")
        self._publish_system_event(
            LifecycleEventType.LIFECYCLE_SHUTDOWN_COMPLETED,
            service_id="lifecycle_manager",
            previous_state=ServiceLifecycleState.STOPPING,
            current_state=ServiceLifecycleState.STOPPED,
        )

        if shutdown_errors:
            raise LifecycleShutdownError("Lifecycle shutdown failed.") from shutdown_errors[0]

    def subscribe(self, handler: LifecycleEventHandler) -> None:
        """Register a synchronous lifecycle event subscriber."""
        self._dispatcher.subscribe(handler)

    def unsubscribe(self, handler: LifecycleEventHandler) -> None:
        """Remove a lifecycle event subscriber."""
        self._dispatcher.unsubscribe(handler)

    def _shutdown_service(self, service_id: str) -> None:
        with self._lock:
            entry = self._entries.get(service_id)
            if entry is None or entry.state == ServiceLifecycleState.STOPPED:
                return
            service = entry.service

        self.transition(service_id, ServiceLifecycleState.STOPPING, message="Shutdown requested")

        if service_id not in _NON_SHUTDOWN_SERVICE_IDS:
            shutdown = getattr(service, "shutdown", None)
            if callable(shutdown):
                shutdown()

        try:
            self.transition(service_id, ServiceLifecycleState.STOPPED, message="Shutdown complete")
        except LifecycleTransitionError:
            self.transition(
                service_id,
                ServiceLifecycleState.FAILED,
                message="Shutdown failed",
            )
            raise

    def _validate_ready_transition(self, entry: _ManagedServiceEntry) -> None:
        for dependency_id in entry.metadata.required_dependencies:
            dependency = self._entries.get(dependency_id)
            if dependency is None:
                raise LifecycleTransitionError(
                    f"Required dependency '{dependency_id}' is not registered."
                )
            if not self._service_registry.contains(dependency_id):
                raise LifecycleTransitionError(
                    f"Required dependency '{dependency_id}' is not present in the registry."
                )
            if dependency.state in {
                ServiceLifecycleState.FAILED,
                ServiceLifecycleState.STOPPING,
                ServiceLifecycleState.STOPPED,
            }:
                raise LifecycleTransitionError(
                    f"Required dependency '{dependency_id}' is not operational."
                )
            if dependency.state != ServiceLifecycleState.READY:
                raise LifecycleTransitionError(
                    f"Required dependency '{dependency_id}' is not ready."
                )

    def _derive_platform_state(
        self,
        records: tuple[ManagedServiceRecord, ...],
    ) -> PlatformState:
        mandatory = [record for record in records if record.metadata.mandatory]

        if mandatory and all(record.state == ServiceLifecycleState.STOPPED for record in mandatory):
            return PlatformState.STOPPED

        if self._shutdown_in_progress or any(
            record.state == ServiceLifecycleState.STOPPING for record in mandatory
        ):
            return PlatformState.STOPPING

        if any(record.state == ServiceLifecycleState.FAILED for record in mandatory):
            return PlatformState.FAILED

        if any(record.state == ServiceLifecycleState.INITIALIZING for record in mandatory):
            return PlatformState.INITIALIZING

        if any(record.state == ServiceLifecycleState.DEGRADED for record in mandatory):
            return PlatformState.DEGRADED

        if mandatory and all(record.state == ServiceLifecycleState.READY for record in mandatory):
            return PlatformState.READY

        return PlatformState.INITIALIZING

    def _transition_locked(
        self,
        service_id: str,
        state: ServiceLifecycleState,
        *,
        message: str | None = None,
    ) -> None:
        entry = self._entries[service_id]
        previous_state = entry.state
        validate_transition(previous_state, state)
        entry.state = state
        entry.health = health_for_lifecycle_state(state)
        entry.updated_at = datetime.now(UTC)
        entry.message = message
        event_type = self._dispatcher.event_type_for_state(state)
        if event_type is not None:
            self._dispatcher.publish(
                self._build_event(event_type, service_id, previous_state, state, message)
            )

    def _snapshot(self, entry: _ManagedServiceEntry) -> ManagedServiceRecord:
        return ManagedServiceRecord(
            metadata=entry.metadata,
            state=entry.state,
            health=entry.health,
            registered_at=entry.registered_at,
            updated_at=entry.updated_at,
            message=entry.message,
        )

    def _build_event(
        self,
        event_type: LifecycleEventType,
        service_id: str,
        previous_state: ServiceLifecycleState | None,
        current_state: ServiceLifecycleState,
        message: str | None,
    ) -> LifecycleEvent:
        return LifecycleEvent(
            event_type=event_type,
            service_id=service_id,
            previous_state=previous_state,
            current_state=current_state,
            timestamp=datetime.now(UTC),
            message=message,
        )

    def _publish_event(
        self,
        event_type: LifecycleEventType,
        service_id: str,
        previous_state: ServiceLifecycleState | None,
        current_state: ServiceLifecycleState,
        message: str | None = None,
    ) -> None:
        self._dispatcher.publish(
            self._build_event(event_type, service_id, previous_state, current_state, message)
        )

    def _publish_system_event(
        self,
        event_type: LifecycleEventType,
        *,
        service_id: str,
        previous_state: ServiceLifecycleState | None,
        current_state: ServiceLifecycleState,
        message: str | None = None,
    ) -> None:
        self._dispatcher.publish(
            self._build_event(event_type, service_id, previous_state, current_state, message)
        )

    def _require_initialized(self) -> None:
        with self._lock:
            if not self._initialized:
                raise LifecycleRegistrationError(
                    "Lifecycle manager must be initialized before use."
                )

    def _require_accepting_registrations(self) -> None:
        with self._lock:
            if not self._accepting_registrations:
                raise LifecycleRegistrationError(
                    "Lifecycle manager is not accepting new registrations."
                )

    def _log_info(self, message: str, **fields: Any) -> None:
        if self._logger is not None:
            self._logger.info(message, **fields)

    def _log_error(self, message: str, **fields: Any) -> None:
        if self._logger is not None:
            self._logger.error(message, **fields)
