"""Service Registry orchestration and public API."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from vibe.registry.descriptor import ServiceDescriptor
from vibe.registry.exceptions import (
    DuplicateServiceRegistrationError,
    InvalidServiceRegistrationError,
    ServiceNotFoundError,
)
from vibe.registry.metadata import ServiceMetadata

if TYPE_CHECKING:
    from vibe.logging.logger import PlatformLogger


class ServiceRegistry:
    """Central registry for platform service instances."""

    def __init__(self, *, logger: PlatformLogger | None = None) -> None:
        """Initialize the service registry.

        Args:
            logger:
                Optional platform logger for registry diagnostics.
        """
        self._logger = logger
        self._services: dict[str, object] = {}
        self._metadata: dict[str, ServiceMetadata] = {}
        self._descriptors: dict[str, ServiceDescriptor] = {}
        self._lock = threading.RLock()

    def set_logger(self, logger: PlatformLogger) -> None:
        """Attach a platform logger for registry diagnostics.

        Args:
            logger:
                Platform logger used for registry events.
        """
        with self._lock:
            self._logger = logger

    def register(
        self,
        name: str,
        service: object,
        metadata: ServiceMetadata | None = None,
    ) -> None:
        """Register a platform service instance.

        Args:
            name:
                Stable service identifier.
            service:
                Initialized service instance.
            metadata:
                Optional immutable service metadata.

        Raises:
            InvalidServiceRegistrationError:
                When the registration request is invalid.
            DuplicateServiceRegistrationError:
                When the service name is already registered.
        """
        validated_name = self._validate_name(name)
        self._validate_service_instance(service)
        resolved_metadata = self._resolve_metadata(validated_name, service, metadata)

        with self._lock:
            if validated_name in self._services:
                self._log_duplicate_registration(validated_name)
                raise DuplicateServiceRegistrationError(
                    f"Service '{validated_name}' is already registered."
                )

            registered_at = datetime.now(UTC)
            descriptor = ServiceDescriptor(
                name=validated_name,
                service_type=resolved_metadata.service_type,
                metadata=resolved_metadata,
                registered_at=registered_at,
            )
            self._services[validated_name] = service
            self._metadata[validated_name] = resolved_metadata
            self._descriptors[validated_name] = descriptor
            self._log_registration(validated_name)

    def unregister(self, name: str) -> None:
        """Remove a registered service by name.

        Args:
            name:
                Stable service identifier.

        Raises:
            InvalidServiceRegistrationError:
                When the service name is invalid.
            ServiceNotFoundError:
                When the service is not registered.
        """
        validated_name = self._validate_name(name)

        with self._lock:
            if validated_name not in self._services:
                raise ServiceNotFoundError(f"Service '{validated_name}' is not registered.")

            del self._services[validated_name]
            del self._metadata[validated_name]
            del self._descriptors[validated_name]
            self._log_unregistration(validated_name)

    def get(self, name: str) -> object:
        """Return a registered service instance.

        Args:
            name:
                Stable service identifier.

        Returns:
            The registered service instance.

        Raises:
            InvalidServiceRegistrationError:
                When the service name is invalid.
            ServiceNotFoundError:
                When the service is not registered.
        """
        validated_name = self._validate_name(name)

        with self._lock:
            service = self._services.get(validated_name)
            if service is None:
                self._log_lookup_failure(validated_name)
                raise ServiceNotFoundError(f"Service '{validated_name}' is not registered.")
            return service

    def get_optional(self, name: str) -> object | None:
        """Return a registered service instance when present.

        Args:
            name:
                Stable service identifier.

        Returns:
            The registered service instance, or ``None`` when absent.

        Raises:
            InvalidServiceRegistrationError:
                When the service name is invalid.
        """
        validated_name = self._validate_name(name)

        with self._lock:
            return self._services.get(validated_name)

    def contains(self, name: str) -> bool:
        """Return whether a service is registered.

        Args:
            name:
                Stable service identifier.

        Returns:
            ``True`` when the service is registered.

        Raises:
            InvalidServiceRegistrationError:
                When the service name is invalid.
        """
        validated_name = self._validate_name(name)

        with self._lock:
            return validated_name in self._services

    def list_services(self) -> tuple[ServiceDescriptor, ...]:
        """Return immutable descriptors for all registered services.

        Returns:
            Registered service descriptors sorted alphabetically by name.
        """
        with self._lock:
            return tuple(self._descriptors[name] for name in sorted(self._descriptors))

    def clear(self) -> None:
        """Remove all registered services.

        Intended for unit and integration test isolation.
        """
        with self._lock:
            self._services.clear()
            self._metadata.clear()
            self._descriptors.clear()
            self._log_clear()

    @property
    def count(self) -> int:
        """Return the number of registered services."""
        with self._lock:
            return len(self._services)

    def _validate_name(self, name: str) -> str:
        if not isinstance(name, str):
            raise InvalidServiceRegistrationError("Service name must be a string.")
        if not name or name.strip() != name or not name.strip():
            raise InvalidServiceRegistrationError("Service name must be a non-empty string.")
        return name

    def _validate_service_instance(self, service: object) -> None:
        if service is None:
            raise InvalidServiceRegistrationError("Service instance must not be None.")

    def _resolve_metadata(
        self,
        name: str,
        service: object,
        metadata: ServiceMetadata | None,
    ) -> ServiceMetadata:
        if metadata is None:
            return ServiceMetadata(name=name, service_type=type(service).__name__)

        if not isinstance(metadata, ServiceMetadata):
            raise InvalidServiceRegistrationError("Metadata must be a ServiceMetadata instance.")

        if metadata.name != name:
            raise InvalidServiceRegistrationError("Metadata name must match the registration name.")

        return metadata

    def _log_registration(self, name: str) -> None:
        if self._logger is not None:
            self._logger.info("Service registered", service_name=name)

    def _log_duplicate_registration(self, name: str) -> None:
        if self._logger is not None:
            self._logger.warning("Duplicate service registration rejected", service_name=name)

    def _log_unregistration(self, name: str) -> None:
        if self._logger is not None:
            self._logger.info("Service unregistered", service_name=name)

    def _log_lookup_failure(self, name: str) -> None:
        if self._logger is not None:
            self._logger.debug("Service lookup failed", service_name=name)

    def _log_clear(self) -> None:
        if self._logger is not None:
            self._logger.info("Service registry cleared")
