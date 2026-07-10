"""Lifecycle public data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from vibe.lifecycle.health import ServiceHealthState
from vibe.lifecycle.metadata import LifecycleServiceMetadata
from vibe.lifecycle.state import PlatformState, ServiceLifecycleState


@dataclass(frozen=True)
class ManagedServiceRecord:
    """Immutable snapshot of a managed service lifecycle record."""

    metadata: LifecycleServiceMetadata
    state: ServiceLifecycleState
    health: ServiceHealthState
    registered_at: datetime
    updated_at: datetime
    message: str | None = None


@dataclass(frozen=True)
class PlatformLifecycleStatus:
    """Immutable summary of platform lifecycle state."""

    state: PlatformState
    service_count: int
    ready_services: int
    degraded_services: int
    failed_services: int
    stopping_services: int
