"""Backward-compatible CLI entry module."""

from vibe.cli.application import CLIApplication
from vibe.cli.main import main

__all__ = ["CLIApplication", "main"]


def __getattr__(name: str) -> object:
    if name == "app":
        return CLIApplication().create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
