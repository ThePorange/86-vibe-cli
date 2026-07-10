"""ServiceMetadata unit tests."""

from __future__ import annotations

import pytest

from vibe.registry.metadata import ServiceMetadata


def test_service_metadata_is_immutable() -> None:
    """Service metadata cannot be modified after creation."""
    metadata = ServiceMetadata(
        name="logging",
        service_type="LoggingService",
        package="vibe.logging",
        version="0.1.0",
        description="Platform logging",
        dependencies=("configuration",),
        optional=False,
    )

    with pytest.raises(AttributeError):
        metadata.name = "other"  # type: ignore[misc]


def test_service_metadata_stores_dependencies() -> None:
    """Dependency lists are preserved as immutable tuples."""
    metadata = ServiceMetadata(
        name="bootstrap",
        service_type="BootstrapService",
        dependencies=("configuration", "logging"),
    )
    assert metadata.dependencies == ("configuration", "logging")


def test_service_metadata_optional_flag() -> None:
    """Optional services are flagged in metadata."""
    metadata = ServiceMetadata(
        name="optional_service",
        service_type="OptionalService",
        optional=True,
    )
    assert metadata.optional is True
