"""Confirmation helper tests."""

from __future__ import annotations

import pytest
import typer

from vibe.cli.confirmation import confirm_action


def test_non_interactive_confirmation_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-interactive execution does not silently approve."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(typer.Exit) as exc_info:
        confirm_action("Delete everything?")
    assert exc_info.value.exit_code == 130


def test_json_mode_confirmation_rejects() -> None:
    """JSON mode does not prompt interactively."""
    with pytest.raises(typer.Exit) as exc_info:
        confirm_action("Delete everything?", machine_readable=True)
    assert exc_info.value.exit_code == 130
