"""ServiceDescriptor unit tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vibe.registry.descriptor import ServiceDescriptor
from vibe.registry.metadata import ServiceMetadata


def test_service_descriptor_is_immutable() -> None:
    """Service descriptors cannot be modified after creation."""
    metadata = ServiceMetadata(name="logging", service_type="LoggingService")
    descriptor = ServiceDescriptor(
        name="logging",
        service_type="LoggingService",
        metadata=metadata,
        registered_at=datetime.now(UTC),
    )

    with pytest.raises(AttributeError):
        descriptor.name = "other"  # type: ignore[misc]


def test_service_descriptor_uses_utc_timestamp() -> None:
    """Registered timestamps are timezone-aware UTC values."""
    metadata = ServiceMetadata(name="logging", service_type="LoggingService")
    registered_at = datetime.now(UTC)
    descriptor = ServiceDescriptor(
        name="logging",
        service_type="LoggingService",
        metadata=metadata,
        registered_at=registered_at,
    )
    assert descriptor.registered_at.tzinfo is UTC


def test_service_descriptor_links_metadata() -> None:
    """Descriptors retain the associated metadata object."""
    metadata = ServiceMetadata(
        name="configuration",
        service_type="ConfigurationService",
        package="vibe.configuration",
    )
    descriptor = ServiceDescriptor(
        name="configuration",
        service_type="ConfigurationService",
        metadata=metadata,
        registered_at=datetime.now(UTC),
    )
    assert descriptor.metadata is metadata
    assert descriptor.service_type == "ConfigurationService"
