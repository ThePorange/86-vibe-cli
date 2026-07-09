"""Bootstrap state machine unit tests."""

from __future__ import annotations

import pytest

from vibe.bootstrap.exceptions import BootstrapStateError
from vibe.bootstrap.state import BootstrapState, transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (BootstrapState.NOT_STARTED, BootstrapState.INITIALISING),
        (BootstrapState.INITIALISING, BootstrapState.RUNNING),
        (BootstrapState.INITIALISING, BootstrapState.FAILED),
        (BootstrapState.RUNNING, BootstrapState.SHUTTING_DOWN),
        (BootstrapState.SHUTTING_DOWN, BootstrapState.STOPPED),
        (BootstrapState.SHUTTING_DOWN, BootstrapState.FAILED),
        (BootstrapState.FAILED, BootstrapState.SHUTTING_DOWN),
        (BootstrapState.FAILED, BootstrapState.STOPPED),
    ],
)
def test_valid_transitions(current: BootstrapState, target: BootstrapState) -> None:
    """Approved bootstrap transitions succeed."""
    assert transition(current, target) == target


def test_invalid_transition_raises() -> None:
    """Invalid bootstrap transitions raise state errors."""
    with pytest.raises(BootstrapStateError):
        transition(BootstrapState.NOT_STARTED, BootstrapState.RUNNING)
    with pytest.raises(BootstrapStateError):
        transition(BootstrapState.STOPPED, BootstrapState.INITIALISING)
