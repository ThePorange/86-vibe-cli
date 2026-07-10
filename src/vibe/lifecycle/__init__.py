"""Service Lifecycle Manager package."""

from vibe.lifecycle.events import LifecycleEvent, LifecycleEventType
from vibe.lifecycle.exceptions import (
    DependencyCycleError,
    DependencyValidationError,
    LifecycleManagerError,
    LifecycleRegistrationError,
    LifecycleShutdownError,
    LifecycleTransitionError,
)
from vibe.lifecycle.health import PlatformHealthSummary, ServiceHealthState
from vibe.lifecycle.manager import ServiceLifecycleManager
from vibe.lifecycle.metadata import LifecycleServiceMetadata
from vibe.lifecycle.models import ManagedServiceRecord, PlatformLifecycleStatus
from vibe.lifecycle.state import PlatformState, ServiceLifecycleState

__all__ = [
    "DependencyCycleError",
    "DependencyValidationError",
    "LifecycleEvent",
    "LifecycleEventType",
    "LifecycleManagerError",
    "LifecycleRegistrationError",
    "LifecycleServiceMetadata",
    "LifecycleShutdownError",
    "LifecycleTransitionError",
    "ManagedServiceRecord",
    "PlatformHealthSummary",
    "PlatformLifecycleStatus",
    "PlatformState",
    "ServiceHealthState",
    "ServiceLifecycleManager",
    "ServiceLifecycleState",
]
