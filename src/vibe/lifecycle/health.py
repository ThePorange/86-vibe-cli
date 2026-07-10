"""Service health state definitions and summaries."""

from __future__ import annotations

import enum
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vibe.lifecycle.state import ServiceLifecycleState

if TYPE_CHECKING:
    from vibe.lifecycle.models import ManagedServiceRecord


class ServiceHealthState(enum.Enum):
    """Recorded health states for managed services."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PlatformHealthSummary:
    """Immutable summary of managed service health."""

    healthy: int
    degraded: int
    failed: int
    unknown: int


def health_for_lifecycle_state(state: ServiceLifecycleState) -> ServiceHealthState:
    """Derive a default health state from a lifecycle state."""
    if state == ServiceLifecycleState.READY:
        return ServiceHealthState.HEALTHY
    if state == ServiceLifecycleState.DEGRADED:
        return ServiceHealthState.DEGRADED
    if state == ServiceLifecycleState.FAILED:
        return ServiceHealthState.FAILED
    return ServiceHealthState.UNKNOWN


def build_health_summary(records: Iterable[ManagedServiceRecord]) -> PlatformHealthSummary:
    """Compute an immutable platform health summary."""
    healthy = 0
    degraded = 0
    failed = 0
    unknown = 0

    for record in records:
        if record.health == ServiceHealthState.HEALTHY:
            healthy += 1
        elif record.health == ServiceHealthState.DEGRADED:
            degraded += 1
        elif record.health == ServiceHealthState.FAILED:
            failed += 1
        else:
            unknown += 1

    return PlatformHealthSummary(
        healthy=healthy,
        degraded=degraded,
        failed=failed,
        unknown=unknown,
    )
