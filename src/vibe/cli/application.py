"""CLI application lifecycle and command routing."""

from __future__ import annotations

import sys
import threading
import traceback
from collections.abc import Sequence
from pathlib import Path

import typer

from vibe.bootstrap.service import BootstrapService
from vibe.cli.commands import (
    register_ai_commands,
    register_architecture_commands,
    register_config_commands,
    register_core_commands,
    register_mcp_commands,
    register_prompt_commands,
    register_repository_commands,
    register_validation_commands,
)
from vibe.cli.errors import map_exception
from vibe.cli.execution import render_error_result
from vibe.cli.exit_codes import ExitCode
from vibe.cli.invocation import InvocationState
from vibe.cli.output.renderer import OutputRenderer
from vibe.cli.version import get_version_info


class CLIApplication:
    """Primary process-level CLI application."""

    _SUPPORTED_OUTPUT_MODES = frozenset({"text", "json"})

    def __init__(
        self,
        bootstrap_service: BootstrapService | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the CLI application."""
        self._bootstrap_service = bootstrap_service or BootstrapService(
            project_root=project_root
        )
        self._app: typer.Typer | None = None
        self._lock = threading.RLock()
        self._shutdown_called = False

    @property
    def bootstrap_service(self) -> BootstrapService:
        """Return the managed bootstrap service."""
        return self._bootstrap_service

    def create_app(self) -> typer.Typer:
        """Construct and return the Typer application."""
        with self._lock:
            if self._app is not None:
                return self._app

            application = self
            app = typer.Typer(
                name="86vibe",
                help="86-vibe platform command-line interface.",
                no_args_is_help=True,
                add_completion=False,
            )

            def version_option_callback(value: bool) -> None:
                if value:
                    output = application.create_output_renderer(
                        InvocationState(application=application, output_mode="text")
                    )
                    output.info(get_version_info().render_text())
                    raise typer.Exit(code=int(ExitCode.SUCCESS))

            @app.callback()
            def root_callback(
                ctx: typer.Context,
                diagnostic: bool = typer.Option(
                    False,
                    "--diagnostic",
                    help="Enable diagnostic error output.",
                ),
                output: str = typer.Option(
                    "text",
                    "--output",
                    help="Output format: text or json.",
                ),
                show_version: bool = typer.Option(
                    False,
                    "--version",
                    help="Show version information and exit.",
                    is_eager=True,
                    callback=version_option_callback,
                ),
            ) -> None:
                if output not in application._SUPPORTED_OUTPUT_MODES:
                    raise typer.BadParameter(
                        f"Unsupported output mode: {output}. Use text or json."
                    )
                ctx.obj = InvocationState(
                    application=application,
                    diagnostic=diagnostic,
                    output_mode=output,
                )

            register_core_commands(app)
            register_config_commands(app)
            register_architecture_commands(app)
            register_repository_commands(app)
            register_validation_commands(app)
            register_prompt_commands(app)
            register_ai_commands(app)
            register_mcp_commands(app)

            self._app = app
            return app

    def create_output_renderer(self, state: InvocationState) -> OutputRenderer:
        """Create an output renderer for the current invocation."""
        return OutputRenderer(
            mode=state.output_mode,
            diagnostic=state.diagnostic,
        )

    def run(self, args: Sequence[str] | None = None) -> int:
        """Execute the CLI application."""
        argv = list(args) if args is not None else sys.argv[1:]
        app = self.create_app()
        output = OutputRenderer()
        diagnostic = "--diagnostic" in argv
        if "--output" in argv:
            index = argv.index("--output")
            if index + 1 < len(argv):
                output = OutputRenderer(mode=argv[index + 1], diagnostic=diagnostic)

        try:
            app(args=argv, standalone_mode=False, prog_name="86vibe")
            return int(ExitCode.SUCCESS)
        except typer.Exit as exc:
            return int(exc.exit_code) if exc.exit_code is not None else int(ExitCode.GENERAL_ERROR)
        except (KeyboardInterrupt, typer.Abort):
            render_error_result(
                output,
                map_exception(KeyboardInterrupt()),
                diagnostic=diagnostic,
            )
            self._safe_shutdown()
            return int(ExitCode.USER_CANCELLED)
        except typer.BadParameter as exc:
            error_result = map_exception(exc)
            render_error_result(output, error_result, diagnostic=diagnostic, exc=exc)
            return int(error_result.exit_code)
        except Exception as exc:
            error_result = map_exception(exc)
            render_error_result(
                output,
                error_result,
                diagnostic=diagnostic,
                exc=exc,
            )
            if diagnostic:
                traceback.print_exc()
            self._safe_shutdown()
            return int(error_result.exit_code)

    def shutdown(self) -> None:
        """Shut down platform services if running."""
        with self._lock:
            if self._shutdown_called:
                return
            self._shutdown_called = True
            if self._bootstrap_service.is_ready():
                self._bootstrap_service.shutdown()

    def _safe_shutdown(self) -> None:
        try:
            self.shutdown()
        except Exception:
            pass
