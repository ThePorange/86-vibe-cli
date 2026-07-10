"""Centralized command execution and readiness validation."""

from __future__ import annotations

import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vibe.cli.context import CLIContext
from vibe.cli.errors import (
    CLIError,
    CLIErrorResult,
    CLIServiceUnavailableError,
    CLIUnsupportedOperationError,
    map_exception,
)
from vibe.cli.exit_codes import ExitCode
from vibe.cli.output.renderer import OutputRenderer
from vibe.cli.requirements import CommandRequirements
from vibe.lifecycle.health import ServiceHealthState
from vibe.lifecycle.state import ServiceLifecycleState
from vibe.registry.service import ServiceRegistry

if TYPE_CHECKING:
    from vibe.bootstrap.service import BootstrapService
    from vibe.lifecycle.manager import ServiceLifecycleManager


@dataclass(frozen=True)
class CommandResult:
    """Stable command execution result."""

    success: bool
    exit_code: ExitCode
    message: str | None = None
    data: object | None = None


def unavailable_command(
    *,
    command_name: str,
    required_service: str,
    governing_iwp: str,
) -> CommandResult:
    """Return a deterministic deferred-command result."""
    message = (
        f"Command unavailable: {command_name}\n"
        f"Required service: {required_service}\n"
        f"Planned implementation: {governing_iwp}\n"
        "No changes were made."
    )
    return CommandResult(
        success=False,
        exit_code=ExitCode.RUNTIME_FAILURE,
        message=message,
    )


def validate_service_readiness(
    registry: ServiceRegistry,
    lifecycle: ServiceLifecycleManager,
    required_services: tuple[str, ...],
    *,
    allow_degraded: bool = False,
) -> None:
    """Validate that required services are registered and ready."""
    for service_id in required_services:
        if not registry.contains(service_id):
            raise CLIServiceUnavailableError(
                f"Required service is not registered: {service_id}"
            )

        record = lifecycle.get_service(service_id)
        if record.state == ServiceLifecycleState.READY:
            if record.health == ServiceHealthState.FAILED:
                raise CLIServiceUnavailableError(
                    f"Required service is not healthy: {service_id}"
                )
            continue

        if allow_degraded and record.state == ServiceLifecycleState.DEGRADED:
            continue

        if record.state in {
            ServiceLifecycleState.FAILED,
            ServiceLifecycleState.STOPPED,
            ServiceLifecycleState.STOPPING,
        }:
            raise CLIServiceUnavailableError(
                f"Required service is unavailable ({record.state.value}): {service_id}"
            )

        raise CLIServiceUnavailableError(
            f"Required service is not ready ({record.state.value}): {service_id}"
        )


def build_cli_context(
    bootstrap: BootstrapService,
    output: OutputRenderer,
    *,
    diagnostic: bool,
    machine_readable: bool,
    correlation_id: str,
) -> CLIContext:
    """Construct an invocation-scoped CLI context."""
    bootstrap.logging_service.set_correlation_id(correlation_id)
    return CLIContext(
        bootstrap=bootstrap,
        configuration=bootstrap.configuration_service,
        logging=bootstrap.logging_service,
        registry=bootstrap.service_registry,
        lifecycle=bootstrap.lifecycle_manager,
        output=output,
        diagnostic=diagnostic,
        machine_readable=machine_readable,
        correlation_id=correlation_id,
    )


def render_result(output: OutputRenderer, result: CommandResult) -> None:
    """Render a command result through the output abstraction."""
    if result.data is not None and result.success and output.machine_readable:
        output.json(result.data)
        return

    output.render_command_result(
        success=result.success,
        message=result.message,
        data=result.data,
        exit_code=result.exit_code,
    )


def render_error_result(
    output: OutputRenderer,
    error_result: CLIErrorResult,
    *,
    diagnostic: bool,
    exc: BaseException | None = None,
) -> None:
    """Render a mapped CLI error."""
    detail = error_result.detail
    if diagnostic and exc is not None and not isinstance(exc, CLIError):
        detail = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
    output.render_error(
        category=error_result.category,
        message=error_result.message,
        correlation_id=error_result.correlation_id,
        detail=detail,
    )


def execute_operational_command(
    bootstrap: BootstrapService,
    output: OutputRenderer,
    requirements: CommandRequirements,
    handler: Callable[[CLIContext], CommandResult],
    *,
    diagnostic: bool,
    command_name: str,
) -> int:
    """Execute an operational command with bootstrap and shutdown."""
    correlation_id = str(uuid.uuid4())
    primary_exit_code: ExitCode | None = None
    logger = None

    try:
        if requirements.bootstrap_required:
            if not bootstrap.is_ready():
                bootstrap.initialize()
            logger = bootstrap.logging_service.get_logger("cli")
            logger.info("CLI invocation started", command=command_name)
            logger.info("Bootstrap completed")

        context = build_cli_context(
            bootstrap,
            output,
            diagnostic=diagnostic,
            machine_readable=output.machine_readable,
            correlation_id=correlation_id,
        )
        validate_service_readiness(
            context.registry,
            context.lifecycle,
            requirements.required_services,
            allow_degraded=requirements.allow_degraded,
        )
        if logger is not None:
            logger.info("Command execution started", command=command_name)
        result = handler(context)
        render_result(output, result)
        primary_exit_code = result.exit_code
        if logger is not None:
            logger.info(
                "Command execution completed",
                command=command_name,
                exit_code=int(result.exit_code),
            )
        return int(result.exit_code)
    except CLIUnsupportedOperationError as exc:
        error_result = map_exception(exc, correlation_id=correlation_id)
        render_error_result(output, error_result, diagnostic=diagnostic, exc=exc)
        primary_exit_code = error_result.exit_code
        if logger is not None:
            logger.error("Command unavailable", command=command_name)
        return int(error_result.exit_code)
    except Exception as exc:
        error_result = map_exception(exc, correlation_id=correlation_id)
        render_error_result(output, error_result, diagnostic=diagnostic, exc=exc)
        primary_exit_code = error_result.exit_code
        if logger is not None:
            logger.error(
                "Command failed",
                command=command_name,
                error_type=type(exc).__name__,
            )
        return int(error_result.exit_code)
    finally:
        if requirements.bootstrap_required and bootstrap.is_ready():
            try:
                if logger is not None:
                    logger.info("Bootstrap shutdown initiated")
                bootstrap.shutdown()
                if logger is not None:
                    logger.info("Bootstrap shutdown completed")
            except Exception as shutdown_exc:
                shutdown_result = map_exception(shutdown_exc, correlation_id=correlation_id)
                if primary_exit_code is None or primary_exit_code == ExitCode.SUCCESS:
                    render_error_result(
                        output,
                        shutdown_result,
                        diagnostic=diagnostic,
                        exc=shutdown_exc,
                    )
                if logger is not None:
                    logger.error("Bootstrap shutdown failed")
            finally:
                try:
                    bootstrap.logging_service.clear_correlation_id()
                except Exception:
                    pass
