"""Bootstrap state machine definitions and transition validation."""

from __future__ import annotations

import enum

from vibe.bootstrap.exceptions import BootstrapStateError


class BootstrapState(enum.Enum):
    """Deterministic bootstrap lifecycle states."""

    NOT_STARTED = "not_started"
    INITIALISING = "initialising"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    FAILED = "failed"


_VALID_TRANSITIONS: dict[BootstrapState, set[BootstrapState]] = {
    BootstrapState.NOT_STARTED: {BootstrapState.INITIALISING},
    BootstrapState.INITIALISING: {BootstrapState.RUNNING, BootstrapState.FAILED},
    BootstrapState.RUNNING: {BootstrapState.SHUTTING_DOWN},
    BootstrapState.SHUTTING_DOWN: {BootstrapState.STOPPED, BootstrapState.FAILED},
    BootstrapState.FAILED: {BootstrapState.SHUTTING_DOWN, BootstrapState.STOPPED},
    BootstrapState.STOPPED: set(),
}


def transition(current: BootstrapState, target: BootstrapState) -> BootstrapState:
    """Validate and return the target bootstrap state.

    Args:
        current:
            Current bootstrap state.
        target:
            Requested bootstrap state.

    Returns:
        The validated target state.

    Raises:
        BootstrapStateError:
            When the transition is not permitted.
    """
    allowed = _VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise BootstrapStateError(
            f"Invalid bootstrap state transition from {current.value} to {target.value}"
        )
    return target
