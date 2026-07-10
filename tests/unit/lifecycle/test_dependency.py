"""Dependency graph unit tests."""

from __future__ import annotations

import pytest

from vibe.lifecycle.dependency import detect_cycle, shutdown_order, validate_dependency_metadata
from vibe.lifecycle.exceptions import DependencyCycleError, DependencyValidationError
from vibe.lifecycle.metadata import LifecycleServiceMetadata


def test_shutdown_order_is_reverse_dependency_order() -> None:
    """Shutdown order stops dependents before dependencies."""
    dependencies = {
        "configuration": (),
        "logging": ("configuration",),
        "bootstrap": ("configuration", "logging"),
        "lifecycle_manager": ("configuration", "logging", "bootstrap", "service_registry"),
        "service_registry": (),
    }
    order = shutdown_order(tuple(sorted(dependencies)), dependencies)
    assert order.index("lifecycle_manager") < order.index("bootstrap")
    assert order.index("bootstrap") < order.index("logging")
    assert order.index("logging") < order.index("configuration")


def test_detect_cycle_rejects_cycles() -> None:
    """Dependency cycles are rejected deterministically."""
    known = {
        "service_a": ("service_b",),
        "service_b": ("service_c",),
    }
    with pytest.raises(DependencyCycleError):
        detect_cycle("service_c", ("service_a",), known)


def test_validate_dependency_metadata_rejects_self_dependency() -> None:
    """Services cannot depend on themselves."""
    metadata = LifecycleServiceMetadata(
        service_id="service_a",
        name="Service A",
        version="0.1.0",
        required_dependencies=("service_a",),
    )
    with pytest.raises(DependencyValidationError):
        validate_dependency_metadata(metadata)
