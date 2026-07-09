"""Validator unit tests."""

from __future__ import annotations

import pytest

from vibe.configuration.exceptions import ConfigurationValidationError
from vibe.configuration.loader import load_defaults
from vibe.configuration.validator import validate_configuration


def test_validate_configuration_accepts_defaults() -> None:
    """Default configuration passes validation."""
    validate_configuration(load_defaults())


def test_validate_configuration_rejects_missing_platform() -> None:
    """Missing required platform section is rejected."""
    with pytest.raises(ConfigurationValidationError):
        validate_configuration({})


def test_validate_configuration_rejects_invalid_logging_level() -> None:
    """Invalid logging level enumerations are rejected."""
    config = load_defaults()
    config["logging"]["level"] = "VERBOSE"
    with pytest.raises(ConfigurationValidationError):
        validate_configuration(config)


def test_validate_configuration_rejects_invalid_repository_type() -> None:
    """Invalid repository type enumerations are rejected."""
    config = load_defaults()
    config["repository"]["type"] = "invalid"
    with pytest.raises(ConfigurationValidationError):
        validate_configuration(config)


def test_validate_configuration_allows_unknown_sections() -> None:
    """Unknown future sections do not break validation."""
    config = load_defaults()
    config["future_feature"] = {"enabled": True}
    validate_configuration(config)
