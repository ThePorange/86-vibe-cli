"""Repository Service orchestration and public API."""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any

from vibe.configuration.service import ConfigurationService
from vibe.logging.service import LoggingService
from vibe.repository.artifacts import ArtifactStore
from vibe.repository.cache import RepositoryCache
from vibe.repository.classification import classify_repository
from vibe.repository.discovery import (
    discover_git_root,
    load_repository_settings,
    resolve_discovery_start,
)
from vibe.repository.documents import discover_architecture_documents
from vibe.repository.errors import (
    InvalidRepositoryError,
    RepositoryFailureError,
    RepositoryNotFoundError,
    RepositoryNotInitializedError,
    WriteFailureError,
)
from vibe.repository.git import GitInspector
from vibe.repository.models import (
    InitializationState,
    ListOptions,
    RepositoryCapability,
    RepositoryHealth,
    RepositoryMetadata,
    RepositoryStatus,
    RepositoryType,
    ValidationResult,
    ValidationStatus,
    WriteResult,
)
from vibe.repository.paths import PathPolicy
from vibe.repository.validation import validate_repository_structure
from vibe.version import PLATFORM_VERSION

_VERSION_PATTERN = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.M)


class RepositoryService:
    """Authoritative repository access for the 86-vibe platform."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        logging_service: LoggingService,
        *,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the repository service.

        Args:
            configuration_service:
                Configuration service supplying repository settings.
            logging_service:
                Logging service for repository diagnostics.
            project_root:
                Optional project root used for discovery defaults.
        """
        self._configuration_service = configuration_service
        self._logging_service = logging_service
        self._project_root = project_root or Path.cwd()
        self._lock = threading.RLock()
        self._initialized = False
        self._shutdown = False
        self._root: Path | None = None
        self._path_policy: PathPolicy | None = None
        self._artifacts: ArtifactStore | None = None
        self._git: GitInspector | None = None
        self._repository_type = RepositoryType.UNKNOWN
        self._classification_reason: str | None = None
        self._read_only = False
        self._include_hidden = False
        self._include_ignored = False
        self._cache = RepositoryCache()
        self._last_refresh_success = False
        self._last_discovery_success = False
        self._logger = None

    @property
    def is_initialized(self) -> bool:
        """Return whether the repository service has been initialized."""
        with self._lock:
            return self._initialized and not self._shutdown

    def initialize(self) -> None:
        """Discover, validate, and prepare the active repository."""
        with self._lock:
            if self._shutdown:
                raise RepositoryNotInitializedError("Repository service is shut down.")
            if self._initialized and self._root is not None:
                return

            self._logger = self._logging_service.get_logger("repository")
            self._logger.info("Repository service initialization started")
            settings = self._load_settings()
            self._apply_settings(settings)
            start = resolve_discovery_start(
                configured_path=settings.get("path"),
                discovery_root=settings.get("discovery_root"),
                cwd=self._project_root,
            )
            try:
                self._activate_repository(start, settings)
            except (RepositoryNotFoundError, InvalidRepositoryError) as exc:
                self._last_discovery_success = False
                self._logger.error(
                    "Repository initialization failed",
                    error_type=type(exc).__name__,
                )
                raise
            except Exception as exc:
                self._last_discovery_success = False
                self._logger.error(
                    "Repository initialization failed",
                    error_type=type(exc).__name__,
                )
                raise RepositoryFailureError("Repository initialization failed.") from exc

            self._initialized = True
            self._last_discovery_success = True
            self._logger.info(
                "Repository service initialization completed",
                repository_type=self._repository_type.value,
            )

    def open(self, repository: str | Path) -> RepositoryMetadata:
        """Open an explicit repository location."""
        with self._lock:
            self._require_operational()
            previous_root = self._root
            settings = self._load_settings()
            self._apply_settings(settings)
            try:
                start = Path(repository).expanduser()
                self._activate_repository(start, settings)
            except Exception:
                if previous_root is not None:
                    self._restore_repository(previous_root, settings)
                raise
            return self.metadata()

    def status(self) -> RepositoryStatus:
        """Return normalized repository status."""
        with self._lock:
            self._require_operational()
            validation = self._get_validation()
            metadata = self._build_metadata(InitializationState.READY)
            health = self.health()
            return RepositoryStatus(
                initialized=self._initialized,
                available=self._root is not None,
                synchronized=metadata.git_cleanliness.value == "clean",
                read_only=self._read_only,
                validation_status=validation.status,
                git_cleanliness=metadata.git_cleanliness,
                health=health.state,
                warnings=tuple(issue.message for issue in validation.warnings),
                repository_identifier=metadata.identifier,
                repository_type=metadata.repository_type,
            )

    def exists(self, path: str) -> bool:
        """Return whether an artifact exists."""
        with self._lock:
            self._require_operational()
            return self._artifacts.exists(path)  # type: ignore[union-attr]

    def read(self, path: str) -> str:
        """Read a repository artifact."""
        with self._lock:
            self._require_operational()
            return self._artifacts.read(path)  # type: ignore[union-attr]

    def write(self, path: str, content: str) -> WriteResult:
        """Write a repository artifact."""
        with self._lock:
            self._require_operational()
            result = self._artifacts.write(path, content)  # type: ignore[union-attr]
            self._cache.invalidate_documents()
            self._cache.set_metadata(self._build_metadata(InitializationState.READY))
            self._logger.info("Artifact write completed", path=result.path)
            return result

    def list(
        self,
        path: str = ".",
        *,
        options: ListOptions | None = None,
    ) -> tuple[str, ...]:
        """List repository entries."""
        with self._lock:
            self._require_operational()
            return self._artifacts.list(path, options=options)  # type: ignore[union-attr]

    def metadata(self) -> RepositoryMetadata:
        """Return normalized repository metadata."""
        with self._lock:
            self._require_operational()
            cached = self._cache.get_metadata()
            if cached is not None:
                return cached
            metadata = self._build_metadata(InitializationState.READY)
            self._cache.set_metadata(metadata)
            return metadata

    def refresh(self) -> RepositoryMetadata:
        """Refresh repository and Git state."""
        with self._lock:
            self._require_operational()
            self._logger.info("Repository refresh started")
            try:
                settings = self._load_settings()
                self._activate_repository(self._root, settings)  # type: ignore[arg-type]
                self._last_refresh_success = True
                self._logger.info("Repository refresh completed")
                return self.metadata()
            except Exception as exc:
                self._last_refresh_success = False
                self._logger.error("Repository refresh failed", error_type=type(exc).__name__)
                raise

    def health(self) -> RepositoryHealth:
        """Return repository service health."""
        with self._lock:
            if self._shutdown:
                return RepositoryHealth(
                    state="shutdown",
                    healthy=False,
                    message="Repository service is shut down.",
                )
            if not self._initialized or self._root is None:
                return RepositoryHealth(
                    state="not_initialized",
                    healthy=False,
                    message="Repository service is not initialized.",
                )
            validation = self._get_validation()
            healthy = (
                self._last_discovery_success
                and validation.status in {ValidationStatus.VALID, ValidationStatus.WARNING}
            )
            return RepositoryHealth(
                state="healthy" if healthy else "degraded",
                healthy=healthy,
                message=None if healthy else "Repository validation reported issues.",
                details={
                    "repository_root_accessible": self._root.exists(),
                    "metadata_available": self._cache.get_metadata() is not None,
                    "last_refresh_success": self._last_refresh_success,
                    "last_discovery_success": self._last_discovery_success,
                    "read_only": self._read_only,
                },
            )

    def validate(self) -> ValidationResult:
        """Return repository structural validation results."""
        with self._lock:
            self._require_operational()
            return self._get_validation()

    def documents(self) -> tuple:
        """Return discovered architecture documents."""
        with self._lock:
            self._require_operational()
            cached = self._cache.get_documents()
            if cached is not None:
                return cached
            documents = discover_architecture_documents(self._root)  # type: ignore[arg-type]
            self._cache.set_documents(documents)
            return documents

    def shutdown(self) -> None:
        """Release repository resources and clear caches."""
        with self._lock:
            if self._shutdown:
                return
            if self._logger is not None:
                self._logger.info("Repository service shutdown started")
            self._cache.clear()
            self._root = None
            self._path_policy = None
            self._artifacts = None
            self._git = None
            self._initialized = False
            self._shutdown = True
            if self._logger is not None:
                self._logger.info("Repository service shutdown completed")

    def _require_operational(self) -> None:
        if self._shutdown:
            raise RepositoryNotInitializedError("Repository service is shut down.")
        if not self._initialized or self._root is None or self._artifacts is None:
            raise RepositoryNotInitializedError("Repository service is not initialized.")

    def _load_settings(self) -> dict[str, Any]:
        if not self._configuration_service.is_initialized:
            return {}
        try:
            return load_repository_settings(self._configuration_service.get_section("repository"))
        except Exception:
            return load_repository_settings({})

    def _apply_settings(self, settings: dict[str, Any]) -> None:
        self._read_only = bool(settings.get("read_only", False))
        self._include_hidden = bool(settings.get("include_hidden", False))
        self._include_ignored = bool(settings.get("include_ignored", False))

    def _activate_repository(self, start: Path, settings: dict[str, Any]) -> None:
        root = discover_git_root(start)
        repository_type, reason = classify_repository(root, settings)
        git = GitInspector(root)
        validation = validate_repository_structure(
            root,
            repository_type,
            has_git=git.has_git(),
        )
        if validation.status == ValidationStatus.INVALID:
            raise InvalidRepositoryError("Repository structure validation failed.")

        self._root = root
        self._repository_type = repository_type
        self._classification_reason = reason
        self._path_policy = PathPolicy(root)
        self._git = git
        self._artifacts = ArtifactStore(
            self._path_policy,
            read_only=self._read_only,
            include_hidden=self._include_hidden,
            include_ignored=self._include_ignored,
        )
        self._cache.invalidate_all()
        self._cache.set_validation(validation)
        self._cache.set_metadata(self._build_metadata(InitializationState.READY))
        self._cache.set_documents(discover_architecture_documents(root))
        self._logger.info(
            "Repository activated",
            repository_type=repository_type.value,
            validation_status=validation.status.value,
        )

    def _restore_repository(self, root: Path, settings: dict[str, Any]) -> None:
        self._activate_repository(root, settings)

    def _get_validation(self) -> ValidationResult:
        cached = self._cache.get_validation()
        if cached is not None:
            return cached
        validation = validate_repository_structure(
            self._root,  # type: ignore[arg-type]
            self._repository_type,
            has_git=self._git.has_git() if self._git else False,  # type: ignore[union-attr]
        )
        self._cache.set_validation(validation)
        return validation

    def _build_metadata(self, initialization_state: InitializationState) -> RepositoryMetadata:
        root = self._root
        git = self._git
        assert root is not None and git is not None
        capabilities = {
            RepositoryCapability.METADATA,
            RepositoryCapability.GIT_INSPECTION,
            RepositoryCapability.ARTIFACT_READ,
            RepositoryCapability.RECURSIVE_LISTING,
            RepositoryCapability.ARCHITECTURE_DISCOVERY,
        }
        if not self._read_only:
            capabilities.add(RepositoryCapability.ARTIFACT_WRITE)

        return RepositoryMetadata(
            identifier=root.name,
            name=root.name,
            root=root,
            repository_type=self._repository_type,
            current_branch=git.current_branch(),
            default_branch=git.default_branch(),
            git_cleanliness=git.cleanliness(),
            latest_commit=git.latest_commit(),
            current_tag=git.current_tag(),
            repository_version=self._repository_version(root),
            platform_version=PLATFORM_VERSION,
            capabilities=frozenset(capabilities),
            read_only=self._read_only,
            initialization_state=initialization_state,
            classification_reason=self._classification_reason,
        )

    def _repository_version(self, root: Path) -> str | None:
        pyproject = root / "pyproject.toml"
        if pyproject.is_file():
            try:
                text = pyproject.read_text(encoding="utf-8")
            except OSError:
                return None
            match = _VERSION_PATTERN.search(text)
            if match:
                return match.group(1)
        version_module = root / "src" / "vibe" / "version.py"
        if version_module.is_file():
            try:
                text = version_module.read_text(encoding="utf-8")
            except OSError:
                return None
            match = re.search(r'PLATFORM_VERSION\s*=\s*["\']([^"\']+)["\']', text)
            if match:
                return match.group(1)
        return None
