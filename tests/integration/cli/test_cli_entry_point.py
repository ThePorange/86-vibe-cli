"""CLI entry point tests."""

from __future__ import annotations

from importlib import import_module


def test_entry_point_imports() -> None:
    """Configured entry point imports successfully."""
    module = import_module("vibe.cli.main")
    assert callable(module.main)
