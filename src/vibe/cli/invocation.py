"""Invocation state shared between Typer callbacks and commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import typer

if TYPE_CHECKING:
    from vibe.cli.application import CLIApplication


@dataclass
class InvocationState:
    """Per-invocation CLI state stored in Typer context."""

    application: CLIApplication
    diagnostic: bool = False
    output_mode: str = "text"


def get_invocation_state(ctx: Any) -> InvocationState:
    """Return invocation state from a Typer context."""
    if not hasattr(ctx, "obj") or not hasattr(ctx, "parent"):
        raise typer.Exit(code=1)

    current: Any = ctx
    while current is not None:
        if isinstance(current.obj, InvocationState):
            return current.obj
        current = current.parent

    raise typer.Exit(code=1)
