"""Lifecycle event models and subscriber dispatch."""

from __future__ import annotations

import enum
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from vibe.lifecycle.state import ServiceLifecycleState

if TYPE_CHECKING:
    from vibe.logging.logger import PlatformLogger


class LifecycleEventType(enum.Enum):
    """Supported lifecycle event types."""

    SERVICE_REGISTERED = "service_registered"
    SERVICE_INITIALIZING = "service_initializing"
    SERVICE_READY = "service_ready"
    SERVICE_DEGRADED = "service_degraded"
    SERVICE_STOPPING = "service_stopping"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_FAILED = "service_failed"
    SERVICE_UNREGISTERED = "service_unregistered"
    LIFECYCLE_MANAGER_INITIALIZED = "lifecycle_manager_initialized"
    LIFECYCLE_SHUTDOWN_STARTED = "lifecycle_shutdown_started"
    LIFECYCLE_SHUTDOWN_COMPLETED = "lifecycle_shutdown_completed"


_STATE_EVENT_MAP: dict[ServiceLifecycleState, LifecycleEventType] = {
    ServiceLifecycleState.INITIALIZING: LifecycleEventType.SERVICE_INITIALIZING,
    ServiceLifecycleState.READY: LifecycleEventType.SERVICE_READY,
    ServiceLifecycleState.DEGRADED: LifecycleEventType.SERVICE_DEGRADED,
    ServiceLifecycleState.STOPPING: LifecycleEventType.SERVICE_STOPPING,
    ServiceLifecycleState.STOPPED: LifecycleEventType.SERVICE_STOPPED,
    ServiceLifecycleState.FAILED: LifecycleEventType.SERVICE_FAILED,
}


@dataclass(frozen=True)
class LifecycleEvent:
    """Immutable lifecycle event payload."""

    event_type: LifecycleEventType
    service_id: str
    previous_state: ServiceLifecycleState | None
    current_state: ServiceLifecycleState
    timestamp: datetime
    message: str | None = None


LifecycleEventHandler = Callable[[LifecycleEvent], None]


class LifecycleEventDispatcher:
    """Synchronously dispatches lifecycle events to subscribers."""

    def __init__(self, *, logger: PlatformLogger | None = None) -> None:
        self._subscribers: list[LifecycleEventHandler] = []
        self._logger = logger
        self._lock = threading.RLock()

    def subscribe(self, handler: LifecycleEventHandler) -> None:
        """Register a synchronous lifecycle event subscriber."""
        with self._lock:
            if handler not in self._subscribers:
                self._subscribers.append(handler)

    def unsubscribe(self, handler: LifecycleEventHandler) -> None:
        """Remove a lifecycle event subscriber."""
        with self._lock:
            if handler in self._subscribers:
                self._subscribers.remove(handler)

    def publish(self, event: LifecycleEvent) -> None:
        """Publish an event to subscribers in registration order."""
        with self._lock:
            subscribers = tuple(self._subscribers)

        for handler in subscribers:
            try:
                handler(event)
            except Exception as exc:
                if self._logger is not None:
                    self._logger.error(
                        "Lifecycle event subscriber failed",
                        error_type=type(exc).__name__,
                        event_type=event.event_type.value,
                        service_id=event.service_id,
                    )

    def event_type_for_state(self, state: ServiceLifecycleState) -> LifecycleEventType | None:
        """Return the event type associated with a lifecycle state transition."""
        return _STATE_EVENT_MAP.get(state)
