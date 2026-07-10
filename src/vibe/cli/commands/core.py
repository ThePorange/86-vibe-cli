"""Core CLI commands."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.exit_codes import ExitCode
from vibe.cli.invocation import get_invocation_state
from vibe.cli.version import get_version_info


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
        run_deferred_command(
            ctx,
            command_name="doctor",
            required_service="Health Monitoring Service",
            governing_iwp="IWP-013",
        )

    @app.command("build")
    def build_command(ctx: typer.Context) -> None:
        """Build or package platform artifacts."""
        run_deferred_command(
            ctx,
            command_name="build",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )
