"""Lifecycle health unit tests."""

from __future__ import annotations

from datetime import UTC, datetime

from vibe.lifecycle.health import ServiceHealthState, build_health_summary
from vibe.lifecycle.metadata import LifecycleServiceMetadata
from vibe.lifecycle.models import ManagedServiceRecord
from vibe.lifecycle.state import ServiceLifecycleState


def _record(state: ServiceLifecycleState, health: ServiceHealthState) -> ManagedServiceRecord:
    metadata = LifecycleServiceMetadata(
        service_id="example",
        name="Example",
        version="0.1.0",
    )
    now = datetime.now(UTC)
    return ManagedServiceRecord(
        metadata=metadata,
        state=state,
        health=health,
        registered_at=now,
        updated_at=now,
    )


def test_health_summary_counts_states() -> None:
    """Health summary aggregates managed service health."""
    summary = build_health_summary(
        (
            _record(ServiceLifecycleState.READY, ServiceHealthState.HEALTHY),
            _record(ServiceLifecycleState.DEGRADED, ServiceHealthState.DEGRADED),
            _record(ServiceLifecycleState.FAILED, ServiceHealthState.FAILED),
            _record(ServiceLifecycleState.REGISTERED, ServiceHealthState.UNKNOWN),
        )
    )
    assert summary.healthy == 1
    assert summary.degraded == 1
    assert summary.failed == 1
    assert summary.unknown == 1
