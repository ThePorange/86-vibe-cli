"""Immutable service descriptor models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from vibe.registry.metadata import ServiceMetadata


@dataclass(frozen=True)
class ServiceDescriptor:
    """Immutable descriptor for an entry in the service registry."""

    name: str
    service_type: str
    metadata: ServiceMetadata
    registered_at: datetime
