"""Shared deferred command helpers."""

from __future__ import annotations

import typer

from vibe.cli.context import CLIContext
from vibe.cli.execution import CommandResult, execute_operational_command, unavailable_command
from vibe.cli.invocation import get_invocation_state
from vibe.cli.requirements import FRAMEWORK_COMMAND


def run_deferred_command(
    ctx: typer.Context,
    *,
    command_name: str,
    required_service: str,
    governing_iwp: str,
) -> None:
    """Execute a deferred command shell with bootstrap logging."""
    state = get_invocation_state(ctx)
    output = state.application.create_output_renderer(state)

    def handler(cli_context: CLIContext) -> CommandResult:
        logger = cli_context.logging.get_logger("cli")
        logger.info("Deferred command invoked", command=command_name)
        logger.warning("Command unavailable in current baseline", command=command_name)
        return unavailable_command(
            command_name=command_name,
            required_service=required_service,
            governing_iwp=governing_iwp,
        )

    exit_code = execute_operational_command(
        state.application.bootstrap_service,
        output,
        FRAMEWORK_COMMAND,
        handler,
        diagnostic=state.diagnostic,
        command_name=command_name,
    )
    raise typer.Exit(code=exit_code)
