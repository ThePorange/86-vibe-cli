"""Immutable lifecycle metadata models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LifecycleServiceMetadata:
    """Immutable metadata for a managed platform service."""

    service_id: str
    name: str
    version: str
    required_dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    mandatory: bool = True
