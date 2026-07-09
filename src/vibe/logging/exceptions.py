"""Logging-specific exception hierarchy."""

from __future__ import annotations


class LoggingServiceError(Exception):
    """Base exception for logging service failures."""


class LoggerInitializationError(LoggingServiceError):
    """Raised when logging service initialization fails."""


class LoggerConfigurationError(LoggingServiceError):
    """Raised when logging configuration is invalid."""


class LoggerShutdownError(LoggingServiceError):
    """Raised when logging service shutdown fails."""
