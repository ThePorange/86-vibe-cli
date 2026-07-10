"""Repository Service exception hierarchy."""

from __future__ import annotations


class RepositoryError(Exception):
    """Base exception for repository service failures."""


class RepositoryNotFoundError(RepositoryError):
    """Raised when no valid repository can be discovered."""


class InvalidRepositoryError(RepositoryError):
    """Raised when repository structure or metadata is invalid."""


class ArtifactNotFoundError(RepositoryError):
    """Raised when a requested artifact does not exist."""


class RepositoryAccessDeniedError(RepositoryError):
    """Raised when filesystem permissions prohibit the operation."""


class ReadFailureError(RepositoryError):
    """Raised when an artifact exists but cannot be read."""


class WriteFailureError(RepositoryError):
    """Raised when an artifact cannot be persisted."""


class RepositoryFailureError(RepositoryError):
    """Raised for internal repository operation failures."""


class InvalidRepositoryPathError(RepositoryError):
    """Raised when a path is malformed or escapes the repository boundary."""


class RepositoryNotInitializedError(RepositoryError):
    """Raised when an operation requires an initialized active repository."""
