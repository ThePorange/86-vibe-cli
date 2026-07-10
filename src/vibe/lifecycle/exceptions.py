"""Service Lifecycle Manager exception hierarchy."""

from __future__ import annotations


class LifecycleManagerError(Exception):
    """Base exception for lifecycle manager failures."""


class LifecycleRegistrationError(LifecycleManagerError):
    """Raised when service registration or lookup fails."""


class LifecycleTransitionError(LifecycleManagerError):
    """Raised when a lifecycle state transition is invalid."""


class DependencyValidationError(LifecycleManagerError):
    """Raised when dependency metadata is invalid."""


class DependencyCycleError(DependencyValidationError):
    """Raised when a dependency cycle is detected."""


class LifecycleShutdownError(LifecycleManagerError):
    """Raised when coordinated shutdown fails."""
