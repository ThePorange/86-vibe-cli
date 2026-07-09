"""86-vibe command-line interface application."""

from __future__ import annotations

import sys
from typing import NoReturn

import typer
from rich.console import Console

from vibe.bootstrap.service import BootstrapService
from vibe.version import (
    ARCHITECTURE_BASELINE,
    BUILD_IDENTIFIER,
    PLATFORM_NAME,
    PLATFORM_VERSION,
)

console = Console()
app = typer.Typer(
    name="86vibe",
    help="86-vibe platform command-line interface.",
    no_args_is_help=True,
    add_completion=False,
)

config_app = typer.Typer(help="Manage CLI configuration.")
arch_app = typer.Typer(help="Manage architecture documentation workflows.")
prompt_app = typer.Typer(help="Manage prompt templates.")
ai_app = typer.Typer(help="AI workflow integration.")
mcp_app = typer.Typer(help="MCP configuration and diagnostics.")
repo_app = typer.Typer(help="Repository utilities.")

app.add_typer(config_app, name="config")
app.add_typer(arch_app, name="arch")
app.add_typer(prompt_app, name="prompt")
app.add_typer(ai_app, name="ai")
app.add_typer(mcp_app, name="mcp")
app.add_typer(repo_app, name="repo")


def _not_implemented(command_name: str) -> None:
    """Raise a placeholder error for unimplemented commands."""
    console.print(f"{command_name} is not yet implemented.")
    raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Initialize platform services before command execution."""
    if ctx.invoked_subcommand is None:
        return
    # Bootstrap is performed lazily by CLIApplication for implemented commands.


class CLIApplication:
    """Primary CLI application coordinating command execution."""

    def __init__(self, bootstrap_service: BootstrapService | None = None) -> None:
        """Initialize the CLI application.

        Args:
            bootstrap_service:
                Optional bootstrap service used during startup.
        """
        self._bootstrap_service = bootstrap_service or BootstrapService()

    def bootstrap(self) -> BootstrapService:
        """Initialize required platform services.

        Returns:
            The bootstrapped service manager.
        """
        self._bootstrap_service.bootstrap()
        return self._bootstrap_service

    def run(self, args: list[str] | None = None) -> int:
        """Execute the CLI application.

        Args:
            args:
                Optional command-line arguments. Defaults to ``sys.argv``.

        Returns:
            Process exit code.
        """
        try:
            app(args=args or sys.argv[1:], standalone_mode=False)
            return 0
        except typer.Exit as exc:
            return int(exc.exit_code)
        except Exception:
            return 1


_cli_application = CLIApplication()


def _ensure_bootstrapped() -> BootstrapService:
    """Bootstrap platform services when a command requires them."""
    if not _cli_application._bootstrap_service.is_ready():
        return _cli_application.bootstrap()
    return _cli_application._bootstrap_service


@app.command("version")
def version_command() -> None:
    """Display platform version information."""
    bootstrap = _ensure_bootstrapped()
    logger = bootstrap.logging_service.get_logger("cli")
    logger.info("version command executed")
    console.print(f"Platform: {PLATFORM_NAME}")
    console.print(f"Platform version: {PLATFORM_VERSION}")
    console.print(f"Architecture baseline: {ARCHITECTURE_BASELINE}")
    console.print(f"Python version: {sys.version.split()[0]}")
    console.print(f"Build identifier: {BUILD_IDENTIFIER}")


@app.command("help")
def help_command(ctx: typer.Context) -> None:
    """Display CLI help information."""
    root = ctx
    while root.parent is not None:
        root = root.parent
    console.print(root.get_help())


@app.command("init")
def init_command() -> None:
    """Initialize 86-vibe metadata in a repository."""
    _not_implemented("init")


@app.command("doctor")
def doctor_command() -> None:
    """Validate local environment readiness."""
    _not_implemented("doctor")


@config_app.callback(invoke_without_command=True)
def config_group(ctx: typer.Context) -> None:
    """Configuration command group."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


@config_app.command("show")
def config_show() -> None:
    """Display configuration values."""
    _not_implemented("config show")


@config_app.command("validate")
def config_validate() -> None:
    """Validate configuration."""
    _not_implemented("config validate")


@arch_app.callback(invoke_without_command=True)
def arch_group(ctx: typer.Context) -> None:
    """Architecture command group."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


@arch_app.command("list")
def arch_list() -> None:
    """List architecture documents."""
    _not_implemented("arch list")


@prompt_app.callback(invoke_without_command=True)
def prompt_group(ctx: typer.Context) -> None:
    """Prompt command group."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


@prompt_app.command("list")
def prompt_list() -> None:
    """List prompt templates."""
    _not_implemented("prompt list")


@ai_app.callback(invoke_without_command=True)
def ai_group(ctx: typer.Context) -> None:
    """AI command group."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


@ai_app.command("providers")
def ai_providers() -> None:
    """List configured AI providers."""
    _not_implemented("ai providers")


@mcp_app.callback(invoke_without_command=True)
def mcp_group(ctx: typer.Context) -> None:
    """MCP command group."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


@mcp_app.command("list")
def mcp_list() -> None:
    """List configured MCP servers."""
    _not_implemented("mcp list")


@repo_app.callback(invoke_without_command=True)
def repo_group(ctx: typer.Context) -> None:
    """Repository command group."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(code=0)


@repo_app.command("status")
def repo_status() -> None:
    """Report repository status."""
    _not_implemented("repo status")


def main() -> NoReturn:
    """Console script entry point for the 86vibe command."""
    raise SystemExit(_cli_application.run())


if __name__ == "__main__":
    main()
