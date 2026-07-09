"""Bootstrap-specific exception hierarchy."""

from __future__ import annotations


class BootstrapError(Exception):
    """Base exception for bootstrap failures."""


class BootstrapInitializationError(BootstrapError):
    """Raised when platform startup fails."""


class BootstrapShutdownError(BootstrapError):
    """Raised when platform shutdown fails."""


class BootstrapStateError(BootstrapError):
    """Raised when an invalid bootstrap state transition occurs."""
