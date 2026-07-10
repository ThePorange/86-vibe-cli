"""Prompt command groups."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.exit_codes import ExitCode


def _create_prompts_group() -> typer.Typer:
    prompt_app = typer.Typer(help="Manage prompt templates.")

    @prompt_app.callback(invoke_without_command=True)
    def prompt_group(ctx: typer.Context) -> None:
        """Prompt command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @prompt_app.command("list")
    def prompt_list(ctx: typer.Context) -> None:
        """List prompt templates."""
        run_deferred_command(
            ctx,
            command_name="prompts list",
            required_service="Prompt Management Service",
            governing_iwp="IWP-010",
        )

    @prompt_app.command("show")
    def prompt_show(ctx: typer.Context) -> None:
        """Show a prompt template."""
        run_deferred_command(
            ctx,
            command_name="prompts show",
            required_service="Prompt Management Service",
            governing_iwp="IWP-010",
        )

    @prompt_app.command("validate")
    def prompt_validate(ctx: typer.Context) -> None:
        """Validate prompt templates."""
        run_deferred_command(
            ctx,
            command_name="prompts validate",
            required_service="Prompt Management Service",
            governing_iwp="IWP-010",
        )

    @prompt_app.command("render")
    def prompt_render(ctx: typer.Context) -> None:
        """Render a prompt template."""
        run_deferred_command(
            ctx,
            command_name="prompts render",
            required_service="Prompt Management Service",
            governing_iwp="IWP-010",
        )

    return prompt_app


def register_prompt_commands(app: typer.Typer) -> None:
    """Register prompt command groups and aliases."""
    app.add_typer(_create_prompts_group(), name="prompts")
    app.add_typer(_create_prompts_group(), name="prompt")
