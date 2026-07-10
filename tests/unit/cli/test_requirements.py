"""Command requirements tests."""

from __future__ import annotations

from vibe.cli.requirements import (
    CONFIG_SHOW,
    FRAMEWORK_COMMAND,
    FRAMEWORK_SERVICES,
    NO_BOOTSTRAP,
)


def test_framework_command_requires_bootstrap() -> None:
    """Framework commands require bootstrap and core services."""
    assert FRAMEWORK_COMMAND.bootstrap_required is True
    assert FRAMEWORK_COMMAND.required_services == FRAMEWORK_SERVICES


def test_version_requirements_skip_bootstrap() -> None:
    """Version metadata commands do not require bootstrap."""
    assert NO_BOOTSTRAP.bootstrap_required is False
    assert NO_BOOTSTRAP.supports_json is True


def test_config_show_supports_json() -> None:
    """Configuration show declares JSON support."""
    assert CONFIG_SHOW.supports_json is True
