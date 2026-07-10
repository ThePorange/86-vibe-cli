"""Validation command."""

from __future__ import annotations

import typer

from vibe.cli.commands.deferred import run_deferred_command


def register_validation_commands(app: typer.Typer) -> None:
    """Register validation commands."""

    @app.command("validate")
    def validate_command(ctx: typer.Context) -> None:
        """Validate platform artifacts and configuration."""
        run_deferred_command(
            ctx,
            command_name="validate",
            required_service="Validation Framework",
            governing_iwp="IWP-008",
        )
