"""Core CLI commands."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.context import CLIContext
from vibe.cli.execution import CommandResult, execute_operational_command
from vibe.cli.exit_codes import ExitCode
from vibe.cli.invocation import get_invocation_state
from vibe.cli.requirements import DOCTOR_COMMAND
from vibe.cli.version import get_version_info
from vibe.lifecycle.state import ServiceLifecycleState
from vibe.registry import SERVICE_NAME_REPOSITORY


def register_core_commands(app: typer.Typer) -> None:
    """Register top-level core commands."""

    @app.command("version")
    def version_command(ctx: typer.Context) -> None:
        """Display platform version information."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)
        info = get_version_info()
        if output.machine_readable:
            output.json(info.as_dict())
        else:
            output.info(info.render_text())
        raise typer.Exit(code=int(ExitCode.SUCCESS))

    @app.command("init")
    def init_command(ctx: typer.Context) -> None:
        """Initialize 86-vibe metadata in a repository."""
        run_deferred_command(
            ctx,
            command_name="init",
            required_service="Bootstrap Service",
            governing_iwp="IWP-004",
        )

    @app.command("doctor")
    def doctor_command(ctx: typer.Context) -> None:
        """Validate local environment readiness."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)
        exit_code = execute_operational_command(
            state.application.bootstrap_service,
            output,
            DOCTOR_COMMAND,
            _doctor_handler,
            diagnostic=state.diagnostic,
            command_name="doctor",
        )
        raise typer.Exit(code=exit_code)

    @app.command("build")
    def build_command(ctx: typer.Context) -> None:
        """Build or package platform artifacts."""
        run_deferred_command(
            ctx,
            command_name="build",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )


def _doctor_handler(context: CLIContext) -> CommandResult:
    checks: list[dict[str, object]] = []
    healthy = True

    for service_id in (
        "configuration",
        "logging",
        "service_registry",
        "lifecycle_manager",
        SERVICE_NAME_REPOSITORY,
    ):
        registered = context.registry.contains(service_id)
        lifecycle_state = "unregistered"
        lifecycle_health = "unknown"
        if registered:
            record = context.lifecycle.get_service(service_id)
            lifecycle_state = record.state.value
            lifecycle_health = record.health.value
            if record.state not in {
                ServiceLifecycleState.READY,
                ServiceLifecycleState.DEGRADED,
            }:
                healthy = False
        else:
            healthy = False
        checks.append(
            {
                "name": f"service:{service_id}",
                "registered": registered,
                "lifecycle_state": lifecycle_state,
                "health": lifecycle_health,
            }
        )

    repository_details: dict[str, object] = {"available": False}
    if context.registry.contains(SERVICE_NAME_REPOSITORY):
        repository = context.registry.get(SERVICE_NAME_REPOSITORY)
        repository_details["available"] = repository.is_initialized
        if repository.is_initialized:
            health = repository.health()
            status = repository.status()
            validation = repository.validate()
            repository_details.update(
                {
                    "health": health.as_dict(),
                    "status": status.as_dict(),
                    "validation_status": validation.status.value,
                    "repository_type": validation.repository_type.value,
                    "git_inspection": status.git_cleanliness.value,
                }
            )
            if validation.status.value == "invalid":
                healthy = False
        else:
            healthy = False

    payload = {
        "healthy": healthy,
        "checks": checks,
        "repository": repository_details,
    }
    if context.machine_readable:
        return CommandResult(
            success=healthy,
            exit_code=ExitCode.SUCCESS if healthy else ExitCode.VALIDATION_FAILURE,
            data=payload,
        )

    lines = ["86-vibe doctor"]
    for check in checks:
        state = "ok" if check["registered"] else "missing"
        lines.append(
            f"- {check['name']}: {state} "
            f"(lifecycle={check['lifecycle_state']}, health={check['health']})"
        )
    if repository_details.get("available"):
        lines.append(
            f"- repository validation: {repository_details.get('validation_status', 'unknown')}"
        )
    else:
        lines.append("- repository: unavailable")
        healthy = False

    return CommandResult(
        success=healthy,
        exit_code=ExitCode.SUCCESS if healthy else ExitCode.VALIDATION_FAILURE,
        message="\n".join(lines),
        data=payload,
    )
