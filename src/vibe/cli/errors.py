"""CLI exception hierarchy and error mapping."""

from __future__ import annotations

import enum
from dataclasses import dataclass

import typer

from vibe.bootstrap.exceptions import (
    BootstrapError,
    BootstrapInitializationError,
    BootstrapShutdownError,
    BootstrapStateError,
)
from vibe.cli.exit_codes import ExitCode
from vibe.configuration.exceptions import (
    ConfigurationError,
    ConfigurationLoadError,
    ConfigurationValidationError,
)
from vibe.lifecycle.exceptions import (
    DependencyValidationError,
    LifecycleManagerError,
    LifecycleRegistrationError,
    LifecycleTransitionError,
)
from vibe.logging.exceptions import LoggingServiceError
from vibe.registry.exceptions import ServiceNotFoundError, ServiceRegistryError
from vibe.repository.errors import (
    ArtifactNotFoundError,
    InvalidRepositoryError,
    InvalidRepositoryPathError,
    ReadFailureError,
    RepositoryAccessDeniedError,
    RepositoryError,
    RepositoryFailureError,
    RepositoryNotFoundError,
    RepositoryNotInitializedError,
    WriteFailureError,
)


class CLIErrorCategory(enum.Enum):
    """Stable user-facing error categories."""

    CONFIG_ERROR = "CONFIG_ERROR"
    REPO_ERROR = "REPO_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    MCP_ERROR = "MCP_ERROR"
    USER_CANCELLED = "USER_CANCELLED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CLIError(Exception):
    """Base exception for CLI framework errors."""

    def __init__(
        self,
        message: str,
        *,
        category: CLIErrorCategory = CLIErrorCategory.RUNTIME_ERROR,
        exit_code: ExitCode = ExitCode.RUNTIME_FAILURE,
        detail: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.exit_code = exit_code
        self.detail = detail
        self.correlation_id = correlation_id


class CLIInitializationError(CLIError):
    """Raised when CLI platform initialization fails."""

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(
            message,
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            **kwargs,  # type: ignore[arg-type]
        )


class CLICommandError(CLIError):
    """Raised when a command fails with a known CLI error."""

    def __init__(
        self,
        message: str,
        *,
        category: CLIErrorCategory = CLIErrorCategory.RUNTIME_ERROR,
        exit_code: ExitCode = ExitCode.RUNTIME_FAILURE,
        **kwargs: object,
    ) -> None:
        super().__init__(message, category=category, exit_code=exit_code, **kwargs)  # type: ignore[arg-type]


class CLIOutputError(CLIError):
    """Raised when output rendering or serialization fails."""

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(
            message,
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            **kwargs,  # type: ignore[arg-type]
        )


class CLIServiceUnavailableError(CLIError):
    """Raised when a required platform service is unavailable."""

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(
            message,
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            **kwargs,  # type: ignore[arg-type]
        )


class CLIUnsupportedOperationError(CLIError):
    """Raised when a command is not available in the current baseline."""

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(
            message,
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            **kwargs,  # type: ignore[arg-type]
        )


class CLIInternalError(CLIError):
    """Raised for unexpected internal platform failures."""

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(
            message,
            category=CLIErrorCategory.INTERNAL_ERROR,
            exit_code=ExitCode.INTERNAL_PLATFORM_ERROR,
            **kwargs,  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class CLIErrorResult:
    """Deterministic mapped CLI failure."""

    category: CLIErrorCategory
    exit_code: ExitCode
    message: str
    detail: str | None = None
    correlation_id: str | None = None


def map_exception(
    exc: BaseException,
    *,
    correlation_id: str | None = None,
) -> CLIErrorResult:
    """Map a raised exception to a stable CLI error result."""
    if isinstance(exc, CLIError):
        return CLIErrorResult(
            category=exc.category,
            exit_code=exc.exit_code,
            message=str(exc),
            detail=exc.detail,
            correlation_id=exc.correlation_id or correlation_id,
        )

    if isinstance(exc, typer.Exit):
        code = int(exc.exit_code) if exc.exit_code is not None else ExitCode.GENERAL_ERROR
        if code == ExitCode.USER_CANCELLED:
            category = CLIErrorCategory.USER_CANCELLED
        elif code == ExitCode.INVALID_ARGUMENTS:
            category = CLIErrorCategory.VALIDATION_ERROR
        else:
            category = CLIErrorCategory.RUNTIME_ERROR
        return CLIErrorResult(
            category=category,
            exit_code=ExitCode(code),
            message="Command exited with an error.",
            correlation_id=correlation_id,
        )

    if isinstance(exc, (typer.BadParameter, typer.Abort)):
        return CLIErrorResult(
            category=CLIErrorCategory.VALIDATION_ERROR,
            exit_code=ExitCode.INVALID_ARGUMENTS,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, KeyboardInterrupt):
        return CLIErrorResult(
            category=CLIErrorCategory.USER_CANCELLED,
            exit_code=ExitCode.USER_CANCELLED,
            message="Operation cancelled by user.",
            correlation_id=correlation_id,
        )

    if isinstance(exc, (ConfigurationError, ConfigurationLoadError, ConfigurationValidationError)):
        return CLIErrorResult(
            category=CLIErrorCategory.CONFIG_ERROR,
            exit_code=ExitCode.CONFIGURATION_ERROR,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, BootstrapInitializationError):
        return CLIErrorResult(
            category=CLIErrorCategory.CONFIG_ERROR,
            exit_code=ExitCode.CONFIGURATION_ERROR,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, (BootstrapError, BootstrapStateError, BootstrapShutdownError)):
        return CLIErrorResult(
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, (ServiceRegistryError, ServiceNotFoundError)):
        return CLIErrorResult(
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(
        exc,
        (
            LifecycleManagerError,
            LifecycleRegistrationError,
            LifecycleTransitionError,
            DependencyValidationError,
        ),
    ):
        return CLIErrorResult(
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, LoggingServiceError):
        return CLIErrorResult(
            category=CLIErrorCategory.RUNTIME_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, (RepositoryNotFoundError, InvalidRepositoryError)):
        return CLIErrorResult(
            category=CLIErrorCategory.REPO_ERROR,
            exit_code=ExitCode.VALIDATION_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(
        exc,
        (
            ArtifactNotFoundError,
            InvalidRepositoryPathError,
            RepositoryNotInitializedError,
        ),
    ):
        return CLIErrorResult(
            category=CLIErrorCategory.REPO_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, (RepositoryAccessDeniedError, ReadFailureError, WriteFailureError)):
        return CLIErrorResult(
            category=CLIErrorCategory.REPO_ERROR,
            exit_code=ExitCode.RUNTIME_FAILURE,
            message=str(exc),
            correlation_id=correlation_id,
        )

    if isinstance(exc, (RepositoryFailureError, RepositoryError)):
        return CLIErrorResult(
            category=CLIErrorCategory.REPO_ERROR,
            exit_code=ExitCode.INTERNAL_PLATFORM_ERROR,
            message=str(exc),
            correlation_id=correlation_id,
        )

    return CLIErrorResult(
        category=CLIErrorCategory.INTERNAL_ERROR,
        exit_code=ExitCode.INTERNAL_PLATFORM_ERROR,
        message="An internal platform error occurred.",
        detail=f"{type(exc).__name__}: {exc}",
        correlation_id=correlation_id,
    )
