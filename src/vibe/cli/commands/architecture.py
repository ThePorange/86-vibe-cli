"""Architecture command group."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.exit_codes import ExitCode


def _create_arch_group() -> typer.Typer:
    arch_app = typer.Typer(help="Manage architecture documentation workflows.")

    @arch_app.callback(invoke_without_command=True)
    def arch_group(ctx: typer.Context) -> None:
        """Architecture command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @arch_app.command("list")
    def arch_list(ctx: typer.Context) -> None:
        """List architecture documents."""
        run_deferred_command(
            ctx,
            command_name="arch list",
            required_service="Repository Service",
            governing_iwp="IWP-009",
        )

    @arch_app.command("validate")
    def arch_validate(ctx: typer.Context) -> None:
        """Validate architecture documents."""
        run_deferred_command(
            ctx,
            command_name="arch validate",
            required_service="Validation Framework",
            governing_iwp="IWP-008",
        )

    @arch_app.command("status")
    def arch_status(ctx: typer.Context) -> None:
        """Report architecture status."""
        run_deferred_command(
            ctx,
            command_name="arch status",
            required_service="Repository Service",
            governing_iwp="IWP-009",
        )

    @arch_app.command("baseline")
    def arch_baseline(ctx: typer.Context) -> None:
        """Manage architecture baselines (requires human approval)."""
        run_deferred_command(
            ctx,
            command_name="arch baseline",
            required_service="Repository Service",
            governing_iwp="IWP-009",
        )

    return arch_app


def register_architecture_commands(app: typer.Typer) -> None:
    """Register architecture commands."""
    app.add_typer(_create_arch_group(), name="arch")
