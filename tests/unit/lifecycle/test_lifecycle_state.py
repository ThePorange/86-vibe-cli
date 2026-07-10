"""Lifecycle state transition unit tests."""

from __future__ import annotations

import pytest

from vibe.lifecycle.exceptions import LifecycleTransitionError
from vibe.lifecycle.state import ServiceLifecycleState, validate_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ServiceLifecycleState.REGISTERED, ServiceLifecycleState.INITIALIZING),
        (ServiceLifecycleState.REGISTERED, ServiceLifecycleState.READY),
        (ServiceLifecycleState.REGISTERED, ServiceLifecycleState.FAILED),
        (ServiceLifecycleState.INITIALIZING, ServiceLifecycleState.READY),
        (ServiceLifecycleState.INITIALIZING, ServiceLifecycleState.DEGRADED),
        (ServiceLifecycleState.INITIALIZING, ServiceLifecycleState.FAILED),
        (ServiceLifecycleState.INITIALIZING, ServiceLifecycleState.STOPPING),
        (ServiceLifecycleState.READY, ServiceLifecycleState.DEGRADED),
        (ServiceLifecycleState.READY, ServiceLifecycleState.STOPPING),
        (ServiceLifecycleState.READY, ServiceLifecycleState.FAILED),
        (ServiceLifecycleState.DEGRADED, ServiceLifecycleState.READY),
        (ServiceLifecycleState.DEGRADED, ServiceLifecycleState.STOPPING),
        (ServiceLifecycleState.DEGRADED, ServiceLifecycleState.FAILED),
        (ServiceLifecycleState.STOPPING, ServiceLifecycleState.STOPPED),
        (ServiceLifecycleState.STOPPING, ServiceLifecycleState.FAILED),
        (ServiceLifecycleState.FAILED, ServiceLifecycleState.STOPPING),
        (ServiceLifecycleState.FAILED, ServiceLifecycleState.STOPPED),
    ],
)
def test_legal_transitions(
    current: ServiceLifecycleState,
    target: ServiceLifecycleState,
) -> None:
    """All approved lifecycle transitions are accepted."""
    validate_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ServiceLifecycleState.STOPPED, ServiceLifecycleState.READY),
        (ServiceLifecycleState.STOPPED, ServiceLifecycleState.INITIALIZING),
        (ServiceLifecycleState.REGISTERED, ServiceLifecycleState.STOPPING),
        (ServiceLifecycleState.READY, ServiceLifecycleState.INITIALIZING),
    ],
)
def test_illegal_transitions(
    current: ServiceLifecycleState,
    target: ServiceLifecycleState,
) -> None:
    """Illegal lifecycle transitions are rejected."""
    with pytest.raises(LifecycleTransitionError):
        validate_transition(current, target)
