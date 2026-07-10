"""Service Registry package."""

from vibe.registry.descriptor import ServiceDescriptor
from vibe.registry.exceptions import (
    DuplicateServiceRegistrationError,
    InvalidServiceRegistrationError,
    ServiceNotFoundError,
    ServiceRegistryError,
)
from vibe.registry.metadata import ServiceMetadata
from vibe.registry.names import (
    SERVICE_NAME_BOOTSTRAP,
    SERVICE_NAME_CONFIGURATION,
    SERVICE_NAME_LIFECYCLE_MANAGER,
    SERVICE_NAME_LOGGING,
    SERVICE_NAME_REPOSITORY,
    SERVICE_NAME_SERVICE_REGISTRY,
)
from vibe.registry.service import ServiceRegistry

__all__ = [
    "SERVICE_NAME_BOOTSTRAP",
    "SERVICE_NAME_CONFIGURATION",
    "SERVICE_NAME_LIFECYCLE_MANAGER",
    "SERVICE_NAME_LOGGING",
    "SERVICE_NAME_REPOSITORY",
    "SERVICE_NAME_SERVICE_REGISTRY",
    "DuplicateServiceRegistrationError",
    "InvalidServiceRegistrationError",
    "ServiceDescriptor",
    "ServiceMetadata",
    "ServiceNotFoundError",
    "ServiceRegistry",
    "ServiceRegistryError",
]
