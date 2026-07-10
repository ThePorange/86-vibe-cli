"""Exit code contract tests."""

from __future__ import annotations

from vibe.cli.exit_codes import ExitCode


def test_exit_code_values() -> None:
    """Verify canonical exit code values."""
    assert ExitCode.SUCCESS == 0
    assert ExitCode.GENERAL_ERROR == 1
    assert ExitCode.INVALID_ARGUMENTS == 2
    assert ExitCode.CONFIGURATION_ERROR == 3
    assert ExitCode.VALIDATION_FAILURE == 4
    assert ExitCode.RUNTIME_FAILURE == 5
    assert ExitCode.EXTERNAL_SERVICE_FAILURE == 6
    assert ExitCode.INTERNAL_PLATFORM_ERROR == 7
    assert ExitCode.USER_CANCELLED == 130
