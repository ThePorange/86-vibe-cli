"""Service Registry exception hierarchy."""

from __future__ import annotations


class ServiceRegistryError(Exception):
    """Base exception for service registry failures."""


class DuplicateServiceRegistrationError(ServiceRegistryError):
    """Raised when a service name is already registered."""


class ServiceNotFoundError(ServiceRegistryError):
    """Raised when a requested service is not registered."""


class InvalidServiceRegistrationError(ServiceRegistryError):
    """Raised when a registration request is invalid."""
