"""Configuration command group."""

from __future__ import annotations

import json

import typer

from vibe.cli.commands.deferred import run_deferred_command
from vibe.cli.context import CLIContext
from vibe.cli.execution import CommandResult, execute_operational_command
from vibe.cli.exit_codes import ExitCode
from vibe.cli.invocation import get_invocation_state
from vibe.cli.requirements import CONFIG_SHOW, CONFIG_VALIDATE


def register_config_commands(app: typer.Typer) -> None:
    """Register configuration commands."""
    config_app = typer.Typer(help="Manage CLI configuration.")
    app.add_typer(config_app, name="config")

    @config_app.callback(invoke_without_command=True)
    def config_group(ctx: typer.Context) -> None:
        """Configuration command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @config_app.command("show")
    def config_show(ctx: typer.Context) -> None:
        """Display configuration values."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)

        def handler(cli_context: CLIContext) -> CommandResult:
            logger = cli_context.logging.get_logger("cli.config.show")
            logger.info("Configuration show requested")
            exported = cli_context.configuration.export(mask_secrets=True)
            if output.machine_readable:
                return CommandResult(
                    success=True,
                    exit_code=ExitCode.SUCCESS,
                    data=exported,
                )
            cli_context.output.info(json.dumps(exported, indent=2, sort_keys=True))
            return CommandResult(success=True, exit_code=ExitCode.SUCCESS)

        exit_code = execute_operational_command(
            state.application.bootstrap_service,
            output,
            CONFIG_SHOW,
            handler,
            diagnostic=state.diagnostic,
            command_name="config show",
        )
        raise typer.Exit(code=exit_code)

    @config_app.command("validate")
    def config_validate(ctx: typer.Context) -> None:
        """Validate configuration."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)

        def handler(cli_context: CLIContext) -> CommandResult:
            logger = cli_context.logging.get_logger("cli.config.validate")
            logger.info("Configuration validation requested")
            valid = cli_context.configuration.validate()
            if output.machine_readable:
                return CommandResult(
                    success=valid,
                    exit_code=ExitCode.SUCCESS if valid else ExitCode.VALIDATION_FAILURE,
                    data={"valid": valid},
                    message=None if valid else "Configuration validation failed.",
                )
            message = (
                "Configuration is valid."
                if valid
                else "Configuration validation failed."
            )
            return CommandResult(
                success=valid,
                exit_code=ExitCode.SUCCESS if valid else ExitCode.VALIDATION_FAILURE,
                message=message,
            )

        exit_code = execute_operational_command(
            state.application.bootstrap_service,
            output,
            CONFIG_VALIDATE,
            handler,
            diagnostic=state.diagnostic,
            command_name="config validate",
        )
        raise typer.Exit(code=exit_code)

    @config_app.command("set")
    def config_set(ctx: typer.Context) -> None:
        """Set a configuration value."""
        run_deferred_command(
            ctx,
            command_name="config set",
            required_service="Configuration Service",
            governing_iwp="IWP-002",
        )

    @config_app.command("unset")
    def config_unset(ctx: typer.Context) -> None:
        """Unset a configuration value."""
        run_deferred_command(
            ctx,
            command_name="config unset",
            required_service="Configuration Service",
            governing_iwp="IWP-002",
        )
