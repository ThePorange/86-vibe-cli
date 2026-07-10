"""CLI output rendering abstraction."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from typing import TextIO

from rich.console import Console
from rich.table import Table

from vibe.cli.errors import CLIErrorCategory, CLIOutputError
from vibe.cli.exit_codes import ExitCode
from vibe.cli.output.serializers import dumps_json


class OutputRenderer:
    """Centralized terminal and JSON output rendering."""

    def __init__(
        self,
        *,
        mode: str = "text",
        diagnostic: bool = False,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self._mode = mode
        self._diagnostic = diagnostic
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr
        color_enabled = mode == "text" and not os.environ.get("NO_COLOR")
        self._console = Console(
            file=self._stdout,
            color_system="auto" if color_enabled else None,
            highlight=False,
        )
        self._error_console = Console(
            file=self._stderr,
            color_system="auto" if color_enabled else None,
            highlight=False,
        )

    @property
    def mode(self) -> str:
        """Return the active output mode."""
        return self._mode

    @property
    def machine_readable(self) -> bool:
        """Return whether JSON output mode is active."""
        return self._mode == "json"

    def info(self, message: str) -> None:
        """Render an informational message."""
        if self.machine_readable:
            return
        self._console.print(message)

    def success(self, message: str) -> None:
        """Render a success message."""
        if self.machine_readable:
            return
        self._console.print(message, style="green")

    def warning(self, message: str) -> None:
        """Render a warning message."""
        if self.machine_readable:
            return
        self._error_console.print(message, style="yellow")

    def error(self, message: str) -> None:
        """Render an error message."""
        if self.machine_readable:
            return
        self._error_console.print(message, style="red")

    def table(
        self,
        columns: Sequence[str],
        rows: Sequence[Sequence[object]],
    ) -> None:
        """Render a tabular result."""
        if self.machine_readable:
            self.json({"columns": list(columns), "rows": [list(row) for row in rows]})
            return

        table = Table(show_header=True, header_style="bold")
        for column in columns:
            table.add_column(str(column))
        for row in rows:
            table.add_row(*(str(cell) for cell in row))
        self._console.print(table)

    def json(self, value: object) -> None:
        """Render a JSON value to standard output."""
        try:
            payload = dumps_json(value)
        except CLIOutputError:
            raise
        except Exception as exc:
            raise CLIOutputError(f"Failed to serialize JSON output: {exc}") from exc
        self._stdout.write(payload)

    def render_error(
        self,
        *,
        category: CLIErrorCategory,
        message: str,
        correlation_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        """Render a user-facing error."""
        if self.machine_readable:
            payload: dict[str, object] = {
                "error": {
                    "category": category.value,
                    "message": message,
                },
                "success": False,
            }
            if correlation_id:
                payload["correlation_id"] = correlation_id
            self._stderr.write(dumps_json(payload))
            return

        lines = [f"{category.value.replace('_', ' ').title()}: {message}"]
        if correlation_id:
            lines.append(f"Correlation ID: {correlation_id}")
        if detail and self._diagnostic:
            lines.append(detail)
        self._error_console.print("\n".join(lines), style="red")

    def render_command_result(
        self,
        *,
        success: bool,
        message: str | None = None,
        data: object | None = None,
        exit_code: ExitCode = ExitCode.SUCCESS,
    ) -> None:
        """Render a command result."""
        if self.machine_readable:
            payload: dict[str, object] = {"success": success, "exit_code": int(exit_code)}
            if message is not None:
                payload["message"] = message
            if data is not None:
                payload["data"] = data
            self.json(payload)
            return

        if message:
            if success:
                self.success(message)
            else:
                self.error(message)
        if data is not None and not self.machine_readable:
            self.info(str(data))
