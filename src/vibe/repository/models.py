"""Immutable repository service models."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


class RepositoryType(enum.Enum):
    """Approved repository classifications."""

    PLATFORM = "platform"
    CLI = "cli"
    EXAMPLE = "example"
    EXTENSION = "extension"
    PLUGIN = "plugin"
    UNKNOWN = "unknown"


class ValidationStatus(enum.Enum):
    """Repository structural validation status."""

    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class GitCleanliness(enum.Enum):
    """Normalized Git working-tree cleanliness."""

    CLEAN = "clean"
    MODIFIED = "modified"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class RepositoryCapability(enum.Enum):
    """Operations supported by the active repository."""

    METADATA = "metadata"
    GIT_INSPECTION = "git_inspection"
    ARTIFACT_READ = "artifact_read"
    ARTIFACT_WRITE = "artifact_write"
    RECURSIVE_LISTING = "recursive_listing"
    ARCHITECTURE_DISCOVERY = "architecture_discovery"


class InitializationState(enum.Enum):
    """Repository service initialization state."""

    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass(frozen=True)
class BranchInfo:
    """Normalized branch information."""

    name: str | None
    detached: bool = False


@dataclass(frozen=True)
class LatestCommit:
    """Normalized latest commit metadata."""

    full_hash: str
    short_hash: str
    author: str | None = None
    timestamp: datetime | None = None
    subject: str | None = None


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue."""

    code: str
    message: str
    severity: ValidationStatus


@dataclass(frozen=True)
class ValidationCheck:
    """A single validation check result."""

    name: str
    passed: bool
    message: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    """Normalized repository validation result."""

    status: ValidationStatus
    repository_type: RepositoryType
    checks: tuple[ValidationCheck, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    failures: tuple[ValidationIssue, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "status": self.status.value,
            "repository_type": self.repository_type.value,
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "message": check.message,
                }
                for check in self.checks
            ],
            "warnings": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in self.warnings
            ],
            "failures": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in self.failures
            ],
        }


@dataclass(frozen=True)
class RepositoryMetadata:
    """Normalized immutable repository metadata."""

    identifier: str
    name: str
    root: Path
    repository_type: RepositoryType
    current_branch: BranchInfo | None
    default_branch: str | None
    git_cleanliness: GitCleanliness
    latest_commit: LatestCommit | None
    current_tag: str | None
    repository_version: str | None
    platform_version: str | None
    capabilities: frozenset[RepositoryCapability]
    read_only: bool
    initialization_state: InitializationState
    classification_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "identifier": self.identifier,
            "name": self.name,
            "root": str(self.root),
            "repository_type": self.repository_type.value,
            "current_branch": (
                {
                    "name": self.current_branch.name,
                    "detached": self.current_branch.detached,
                }
                if self.current_branch is not None
                else None
            ),
            "default_branch": self.default_branch,
            "git_cleanliness": self.git_cleanliness.value,
            "latest_commit": (
                {
                    "full_hash": self.latest_commit.full_hash,
                    "short_hash": self.latest_commit.short_hash,
                    "author": self.latest_commit.author,
                    "timestamp": (
                        self.latest_commit.timestamp.isoformat()
                        if self.latest_commit.timestamp is not None
                        else None
                    ),
                    "subject": self.latest_commit.subject,
                }
                if self.latest_commit is not None
                else None
            ),
            "current_tag": self.current_tag,
            "repository_version": self.repository_version,
            "platform_version": self.platform_version,
            "capabilities": sorted(capability.value for capability in self.capabilities),
            "read_only": self.read_only,
            "initialization_state": self.initialization_state.value,
            "classification_reason": self.classification_reason,
        }


@dataclass(frozen=True)
class RepositoryStatus:
    """Normalized repository status."""

    initialized: bool
    available: bool
    synchronized: bool
    read_only: bool
    validation_status: ValidationStatus
    git_cleanliness: GitCleanliness
    health: str
    warnings: tuple[str, ...] = ()
    repository_identifier: str | None = None
    repository_type: RepositoryType | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "initialized": self.initialized,
            "available": self.available,
            "synchronized": self.synchronized,
            "read_only": self.read_only,
            "validation_status": self.validation_status.value,
            "git_cleanliness": self.git_cleanliness.value,
            "health": self.health,
            "warnings": list(self.warnings),
            "repository_identifier": self.repository_identifier,
            "repository_type": (
                self.repository_type.value if self.repository_type is not None else None
            ),
        }


@dataclass(frozen=True)
class WriteResult:
    """Normalized artifact write result."""

    path: str
    bytes_written: int
    created: bool


@dataclass(frozen=True)
class ArchitectureDocument:
    """Discovered architecture document metadata."""

    document_id: str | None
    title: str | None
    package: str | None
    status: str | None
    path: str
    complete: bool = True

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "package": self.package,
            "status": self.status,
            "path": self.path,
            "complete": self.complete,
        }


@dataclass(frozen=True)
class RepositoryHealth:
    """Repository service health result."""

    state: str
    healthy: bool
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "state": self.state,
            "healthy": self.healthy,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class ListOptions:
    """Options for directory listing."""

    include_hidden: bool = False
    include_ignored: bool = False
    recursive: bool = False
    extension: str | None = None


@dataclass(frozen=True)
class ResolvedPath:
    """Internal resolved repository path."""

    relative: str
    absolute: Path
