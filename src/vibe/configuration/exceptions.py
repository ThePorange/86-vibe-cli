"""Configuration-specific exception hierarchy."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Base exception for configuration failures."""


class ConfigurationLoadError(ConfigurationError):
    """Raised when configuration cannot be loaded from a source."""


class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration fails validation."""


class ConfigurationKeyError(ConfigurationError):
    """Raised when a required configuration key is missing."""


class ConfigurationReloadError(ConfigurationError):
    """Raised when configuration reload fails."""
