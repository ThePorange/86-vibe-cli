"""Invocation-scoped CLI context."""

from __future__ import annotations

from dataclasses import dataclass

from vibe.bootstrap.service import BootstrapService
from vibe.cli.output.renderer import OutputRenderer
from vibe.configuration.service import ConfigurationService
from vibe.lifecycle.manager import ServiceLifecycleManager
from vibe.logging.service import LoggingService
from vibe.registry.service import ServiceRegistry


@dataclass
class CLIContext:
    """Invocation-scoped access to approved platform services."""

    bootstrap: BootstrapService
    configuration: ConfigurationService
    logging: LoggingService
    registry: ServiceRegistry
    lifecycle: ServiceLifecycleManager
    output: OutputRenderer
    diagnostic: bool = False
    machine_readable: bool = False
    correlation_id: str | None = None
