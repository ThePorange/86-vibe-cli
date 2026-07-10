"""Repository metadata cache."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Generic, TypeVar

from vibe.repository.models import (
    ArchitectureDocument,
    RepositoryMetadata,
    ValidationResult,
)

T = TypeVar("T")


@dataclass
class _CacheEntry(Generic[T]):
    """Internal cache entry."""

    value: T


class RepositoryCache:
    """Thread-safe internal repository cache."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metadata: RepositoryMetadata | None = None
        self._validation: ValidationResult | None = None
        self._documents: tuple[ArchitectureDocument, ...] | None = None

    def get_metadata(self) -> RepositoryMetadata | None:
        """Return cached metadata."""
        with self._lock:
            return self._metadata

    def set_metadata(self, metadata: RepositoryMetadata) -> None:
        """Store metadata snapshot."""
        with self._lock:
            self._metadata = metadata

    def get_validation(self) -> ValidationResult | None:
        """Return cached validation result."""
        with self._lock:
            return self._validation

    def set_validation(self, validation: ValidationResult) -> None:
        """Store validation result."""
        with self._lock:
            self._validation = validation

    def get_documents(self) -> tuple[ArchitectureDocument, ...] | None:
        """Return cached architecture documents."""
        with self._lock:
            return self._documents

    def set_documents(self, documents: tuple[ArchitectureDocument, ...]) -> None:
        """Store architecture document inventory."""
        with self._lock:
            self._documents = documents

    def invalidate_all(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._metadata = None
            self._validation = None
            self._documents = None

    def invalidate_documents(self) -> None:
        """Clear architecture document cache."""
        with self._lock:
            self._documents = None

    def clear(self) -> None:
        """Clear all cache entries on shutdown."""
        self.invalidate_all()
