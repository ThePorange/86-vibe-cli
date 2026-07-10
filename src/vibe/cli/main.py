"""Installed CLI entry point."""

from __future__ import annotations

from typing import NoReturn

from vibe.cli.application import CLIApplication


def main() -> NoReturn:
    """Console script entry point for the 86vibe command."""
    application = CLIApplication()
    exit_code = application.run()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
