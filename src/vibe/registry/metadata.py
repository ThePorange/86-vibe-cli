"""Immutable service metadata models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceMetadata:
    """Immutable metadata describing a registered platform service."""

    name: str
    service_type: str
    package: str | None = None
    version: str | None = None
    description: str | None = None
    dependencies: tuple[str, ...] = ()
    optional: bool = False
