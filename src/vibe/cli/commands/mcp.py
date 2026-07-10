"""MCP command group."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.exit_codes import ExitCode


def register_mcp_commands(app: typer.Typer) -> None:
    """Register MCP commands."""
    mcp_app = typer.Typer(help="MCP configuration and diagnostics.")
    app.add_typer(mcp_app, name="mcp")

    @mcp_app.callback(invoke_without_command=True)
    def mcp_group(ctx: typer.Context) -> None:
        """MCP command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @mcp_app.command("list")
    def mcp_list(ctx: typer.Context) -> None:
        """List configured MCP servers."""
        run_deferred_command(
            ctx,
            command_name="mcp list",
            required_service="MCP Client Service",
            governing_iwp="IWP-012",
        )

    @mcp_app.command("validate")
    def mcp_validate(ctx: typer.Context) -> None:
        """Validate MCP configuration."""
        run_deferred_command(
            ctx,
            command_name="mcp validate",
            required_service="MCP Client Service",
            governing_iwp="IWP-012",
        )

    @mcp_app.command("doctor")
    def mcp_doctor(ctx: typer.Context) -> None:
        """Diagnose MCP connectivity."""
        run_deferred_command(
            ctx,
            command_name="mcp doctor",
            required_service="MCP Client Service",
            governing_iwp="IWP-012",
        )
