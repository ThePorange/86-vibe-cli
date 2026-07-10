"""Repository command groups."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.exit_codes import ExitCode


def _create_repository_group() -> typer.Typer:
    repo_app = typer.Typer(help="Repository utilities.")

    @repo_app.callback(invoke_without_command=True)
    def repo_group(ctx: typer.Context) -> None:
        """Repository command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @repo_app.command("status")
    def repo_status(ctx: typer.Context) -> None:
        """Report repository status."""
        run_deferred_command(
            ctx,
            command_name="repository status",
            required_service="Repository Service",
            governing_iwp="IWP-009",
        )

    @repo_app.command("validate")
    def repo_validate(ctx: typer.Context) -> None:
        """Validate repository structure."""
        run_deferred_command(
            ctx,
            command_name="repository validate",
            required_service="Repository Service",
            governing_iwp="IWP-009",
        )

    @repo_app.command("docs")
    def repo_docs(ctx: typer.Context) -> None:
        """Manage repository documentation."""
        run_deferred_command(
            ctx,
            command_name="repository docs",
            required_service="Repository Service",
            governing_iwp="IWP-009",
        )

    return repo_app


def register_repository_commands(app: typer.Typer) -> None:
    """Register repository command groups and aliases."""
    app.add_typer(_create_repository_group(), name="repository")
    app.add_typer(_create_repository_group(), name="repo")
