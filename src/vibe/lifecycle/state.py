"""Lifecycle and platform state definitions."""

from __future__ import annotations

import enum

from vibe.lifecycle.exceptions import LifecycleTransitionError


class ServiceLifecycleState(enum.Enum):
    """Authoritative managed-service lifecycle states."""

    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class PlatformState(enum.Enum):
    """Derived platform operational states."""

    READY = "ready"
    INITIALIZING = "initializing"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


_LEGAL_TRANSITIONS: dict[ServiceLifecycleState, set[ServiceLifecycleState]] = {
    ServiceLifecycleState.REGISTERED: {
        ServiceLifecycleState.INITIALIZING,
        ServiceLifecycleState.READY,
        ServiceLifecycleState.FAILED,
    },
    ServiceLifecycleState.INITIALIZING: {
        ServiceLifecycleState.READY,
        ServiceLifecycleState.DEGRADED,
        ServiceLifecycleState.FAILED,
        ServiceLifecycleState.STOPPING,
    },
    ServiceLifecycleState.READY: {
        ServiceLifecycleState.DEGRADED,
        ServiceLifecycleState.STOPPING,
        ServiceLifecycleState.FAILED,
    },
    ServiceLifecycleState.DEGRADED: {
        ServiceLifecycleState.READY,
        ServiceLifecycleState.STOPPING,
        ServiceLifecycleState.FAILED,
    },
    ServiceLifecycleState.STOPPING: {
        ServiceLifecycleState.STOPPED,
        ServiceLifecycleState.FAILED,
    },
    ServiceLifecycleState.FAILED: {
        ServiceLifecycleState.STOPPING,
        ServiceLifecycleState.STOPPED,
    },
    ServiceLifecycleState.STOPPED: set(),
}


def validate_transition(
    current: ServiceLifecycleState,
    target: ServiceLifecycleState,
) -> None:
    """Validate a lifecycle state transition.

    Args:
        current:
            Current lifecycle state.
        target:
            Requested lifecycle state.

    Raises:
        LifecycleTransitionError:
            When the transition is not permitted.
    """
    allowed = _LEGAL_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise LifecycleTransitionError(
            f"Invalid lifecycle transition from {current.value} to {target.value}."
        )
