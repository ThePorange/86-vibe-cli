"""AI command group."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.exit_codes import ExitCode


def _create_ai_group() -> typer.Typer:
    ai_app = typer.Typer(help="AI workflow integration.")

    @ai_app.callback(invoke_without_command=True)
    def ai_group(ctx: typer.Context) -> None:
        """AI command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @ai_app.command("providers")
    def ai_providers(ctx: typer.Context) -> None:
        """List configured AI providers."""
        run_deferred_command(
            ctx,
            command_name="ai providers",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )

    @ai_app.command("models")
    def ai_models(ctx: typer.Context) -> None:
        """List available AI models."""
        run_deferred_command(
            ctx,
            command_name="ai models",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )

    @ai_app.command("plan")
    def ai_plan(ctx: typer.Context) -> None:
        """Plan an AI-assisted implementation."""
        run_deferred_command(
            ctx,
            command_name="ai plan",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )

    @ai_app.command("implement")
    def ai_implement(ctx: typer.Context) -> None:
        """Execute an AI-assisted implementation."""
        run_deferred_command(
            ctx,
            command_name="ai implement",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )

    return ai_app


def register_ai_commands(app: typer.Typer) -> None:
    """Register AI commands and aliases."""
    app.add_typer(_create_ai_group(), name="ai")

    @app.command("providers")
    def providers_alias(ctx: typer.Context) -> None:
        """List configured AI providers (alias for ai providers)."""
        run_deferred_command(
            ctx,
            command_name="providers",
            required_service="AI Provider Layer",
            governing_iwp="IWP-011",
        )
