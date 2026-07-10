"""Bootstrap result models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from vibe.bootstrap.state import BootstrapState
from vibe.configuration.service import ConfigurationService
from vibe.logging.service import LoggingService
from vibe.registry.service import ServiceRegistry


@dataclass(frozen=True)
class BootstrapResult:
    """Immutable result of a successful platform bootstrap."""

    state: BootstrapState
    started_at: datetime
    configuration_service: ConfigurationService
    logging_service: LoggingService
    service_registry: ServiceRegistry
