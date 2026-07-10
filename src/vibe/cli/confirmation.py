"""Safe confirmation helper for future destructive commands."""

from __future__ import annotations

import sys

import typer


def confirm_action(
    message: str,
    *,
    default: bool = False,
    machine_readable: bool = False,
) -> bool:
    """Prompt for explicit user confirmation.

    Args:
        message:
            Confirmation prompt shown to the user.
        default:
            Default answer when the user presses enter.
        machine_readable:
            When ``True``, non-interactive execution is assumed.

    Returns:
        ``True`` when the user confirms the action.

    Raises:
        typer.Exit:
            When confirmation is rejected or unavailable.
    """
    if machine_readable or not sys.stdin.isatty():
        typer.echo("Confirmation is required but non-interactive execution was detected.", err=True)
        raise typer.Exit(code=130)

    confirmed = typer.confirm(message, default=default)
    if not confirmed:
        raise typer.Exit(code=130)
    return True
