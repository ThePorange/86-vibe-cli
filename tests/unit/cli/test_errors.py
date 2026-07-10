"""CLI error mapping tests."""

from __future__ import annotations

import typer

from vibe.bootstrap.exceptions import BootstrapInitializationError
from vibe.cli.errors import CLIErrorCategory, CLIInternalError, map_exception
from vibe.cli.exit_codes import ExitCode
from vibe.configuration.exceptions import ConfigurationLoadError
from vibe.lifecycle.exceptions import LifecycleRegistrationError
from vibe.registry.exceptions import ServiceNotFoundError


def test_maps_configuration_errors() -> None:
    """Configuration failures map to configuration exit code."""
    result = map_exception(ConfigurationLoadError("missing file"))
    assert result.category == CLIErrorCategory.CONFIG_ERROR
    assert result.exit_code == ExitCode.CONFIGURATION_ERROR


def test_maps_bootstrap_initialization_errors() -> None:
    """Bootstrap initialization failures map to configuration exit code."""
    result = map_exception(BootstrapInitializationError("startup failed"))
    assert result.category == CLIErrorCategory.CONFIG_ERROR
    assert result.exit_code == ExitCode.CONFIGURATION_ERROR


def test_maps_registry_errors() -> None:
    """Registry failures map to runtime failure."""
    result = map_exception(ServiceNotFoundError("missing"))
    assert result.category == CLIErrorCategory.RUNTIME_ERROR
    assert result.exit_code == ExitCode.RUNTIME_FAILURE


def test_maps_lifecycle_errors() -> None:
    """Lifecycle failures map to runtime failure."""
    result = map_exception(LifecycleRegistrationError("missing"))
    assert result.category == CLIErrorCategory.RUNTIME_ERROR
    assert result.exit_code == ExitCode.RUNTIME_FAILURE


def test_maps_keyboard_interrupt() -> None:
    """User cancellation maps to exit code 130."""
    result = map_exception(KeyboardInterrupt())
    assert result.category == CLIErrorCategory.USER_CANCELLED
    assert result.exit_code == ExitCode.USER_CANCELLED


def test_maps_unknown_exceptions() -> None:
    """Unknown exceptions map to internal platform error."""
    result = map_exception(RuntimeError("unexpected"))
    assert result.category == CLIErrorCategory.INTERNAL_ERROR
    assert result.exit_code == ExitCode.INTERNAL_PLATFORM_ERROR


def test_maps_cli_errors() -> None:
    """CLI errors preserve their category and exit code."""
    result = map_exception(
        CLIInternalError("internal", correlation_id="abc-123"),
    )
    assert result.category == CLIErrorCategory.INTERNAL_ERROR
    assert result.exit_code == ExitCode.INTERNAL_PLATFORM_ERROR
    assert result.correlation_id == "abc-123"


def test_maps_bad_parameter() -> None:
    """Invalid arguments map to exit code 2."""
    result = map_exception(typer.BadParameter("bad value"))
    assert result.category == CLIErrorCategory.VALIDATION_ERROR
    assert result.exit_code == ExitCode.INVALID_ARGUMENTS
