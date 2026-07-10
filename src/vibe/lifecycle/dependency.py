"""Dependency graph validation and shutdown ordering."""

from __future__ import annotations

from collections.abc import Mapping

from vibe.lifecycle.exceptions import DependencyCycleError, DependencyValidationError
from vibe.lifecycle.metadata import LifecycleServiceMetadata


def validate_service_identifier(service_id: str) -> str:
    """Validate a service identifier format."""
    if not isinstance(service_id, str):
        raise DependencyValidationError("Service identifier must be a string.")
    if not service_id or service_id.strip() != service_id or not service_id.strip():
        raise DependencyValidationError("Service identifier must be a non-empty string.")
    return service_id


def validate_dependency_metadata(metadata: LifecycleServiceMetadata) -> None:
    """Validate dependency metadata for a managed service."""
    service_id = validate_service_identifier(metadata.service_id)
    required = metadata.required_dependencies
    optional = metadata.optional_dependencies

    if service_id in required or service_id in optional:
        raise DependencyValidationError("A service cannot depend on itself.")

    if len(required) != len(set(required)):
        raise DependencyValidationError("Required dependencies contain duplicates.")
    if len(optional) != len(set(optional)):
        raise DependencyValidationError("Optional dependencies contain duplicates.")

    overlap = set(required).intersection(optional)
    if overlap:
        raise DependencyValidationError(
            "Dependencies cannot appear in both required and optional lists."
        )

    for dependency_id in (*required, *optional):
        validate_service_identifier(dependency_id)


def detect_cycle(
    service_id: str,
    required_dependencies: tuple[str, ...],
    known_services: Mapping[str, tuple[str, ...]],
) -> None:
    """Detect dependency cycles among known managed services.

    Args:
        service_id:
            Service being registered.
        required_dependencies:
            Required dependencies for the service.
        known_services:
            Mapping of known service identifiers to required dependencies.

    Raises:
        DependencyCycleError:
            When a cycle would be introduced.
    """
    graph = dict(known_services)
    graph[service_id] = required_dependencies

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            cycle_start = path.index(node)
            cycle = " -> ".join([*path[cycle_start:], node])
            raise DependencyCycleError(f"Dependency cycle detected: {cycle}.")
        if node in visited:
            return
        visiting.add(node)
        path.append(node)
        for dependency in graph.get(node, ()):
            if dependency in graph:
                visit(dependency, path)
        path.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        if node not in visited:
            visit(node, [])


def shutdown_order(
    service_ids: tuple[str, ...],
    required_dependencies: Mapping[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """Return service identifiers in reverse dependency order."""
    in_degree = {service_id: 0 for service_id in service_ids}
    dependents: dict[str, list[str]] = {service_id: [] for service_id in service_ids}

    for service_id in service_ids:
        for dependency in required_dependencies.get(service_id, ()):
            if dependency not in in_degree:
                continue
            dependents[dependency].append(service_id)
            in_degree[service_id] += 1

    queue = sorted(service_id for service_id in service_ids if in_degree[service_id] == 0)
    startup_order: list[str] = []

    while queue:
        current = queue.pop(0)
        startup_order.append(current)
        for dependent in sorted(dependents[current]):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
        queue.sort()

    remaining = [
        service_id for service_id in sorted(service_ids) if service_id not in startup_order
    ]
    startup_order.extend(remaining)
    return tuple(reversed(startup_order))
