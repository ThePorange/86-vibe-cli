"""CLI package."""

from vibe.cli.application import CLIApplication
from vibe.cli.context import CLIContext
from vibe.cli.errors import (
    CLICommandError,
    CLIError,
    CLIInitializationError,
    CLIInternalError,
    CLIOutputError,
    CLIServiceUnavailableError,
    CLIUnsupportedOperationError,
)
from vibe.cli.exit_codes import ExitCode
from vibe.cli.output.renderer import OutputRenderer
from vibe.cli.requirements import CommandRequirements

__all__ = [
    "CLIApplication",
    "CLICommandError",
    "CLIContext",
    "CLIError",
    "CLIInitializationError",
    "CLIInternalError",
    "CLIOutputError",
    "CLIServiceUnavailableError",
    "CLIUnsupportedOperationError",
    "CommandRequirements",
    "ExitCode",
    "OutputRenderer",
]
