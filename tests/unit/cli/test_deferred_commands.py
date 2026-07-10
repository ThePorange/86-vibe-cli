"""Deferred command tests."""

from __future__ import annotations

from vibe.cli.execution import unavailable_command
from vibe.cli.exit_codes import ExitCode


def test_unavailable_command_result() -> None:
    """Deferred commands return runtime failure with actionable messaging."""
    result = unavailable_command(
        command_name="repository status",
        required_service="Repository Service",
        governing_iwp="IWP-009",
    )
    assert result.success is False
    assert result.exit_code == ExitCode.RUNTIME_FAILURE
    assert "repository status" in (result.message or "")
    assert "Repository Service" in (result.message or "")
    assert "IWP-009" in (result.message or "")
