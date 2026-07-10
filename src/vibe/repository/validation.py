"""Repository structure validation."""

from __future__ import annotations

from pathlib import Path

from vibe.repository.models import (
    RepositoryType,
    ValidationCheck,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
)

_TYPE_REQUIRED_DIRECTORIES: dict[RepositoryType, tuple[str, ...]] = {
    RepositoryType.PLATFORM: ("architecture", "docs", "tests"),
    RepositoryType.CLI: ("src", "tests", "docs"),
    RepositoryType.EXAMPLE: ("architecture", "docs", "src", "tests", "prompts"),
    RepositoryType.EXTENSION: ("src",),
    RepositoryType.PLUGIN: ("src",),
    RepositoryType.UNKNOWN: (),
}

_TYPE_REQUIRED_FILES: dict[RepositoryType, tuple[str, ...]] = {
    RepositoryType.PLATFORM: ("README.md",),
    RepositoryType.CLI: ("pyproject.toml", "README.md"),
    RepositoryType.EXAMPLE: ("README.md",),
    RepositoryType.EXTENSION: (),
    RepositoryType.PLUGIN: (),
    RepositoryType.UNKNOWN: (),
}


def validate_repository_structure(
    root: Path,
    repository_type: RepositoryType,
    *,
    has_git: bool,
) -> ValidationResult:
    """Validate repository structure for the given classification."""
    checks: list[ValidationCheck] = []
    warnings: list[ValidationIssue] = []
    failures: list[ValidationIssue] = []

    if has_git:
        checks.append(ValidationCheck(name="git_repository", passed=True))
    else:
        failures.append(
            ValidationIssue(
                code="missing_git",
                message="Git repository is required.",
                severity=ValidationStatus.INVALID,
            )
        )
        checks.append(ValidationCheck(name="git_repository", passed=False))

    for directory in _TYPE_REQUIRED_DIRECTORIES.get(repository_type, ()):
        target = root / directory
        passed = target.is_dir()
        checks.append(
            ValidationCheck(
                name=f"directory:{directory}",
                passed=passed,
                message=None if passed else f"Required directory missing: {directory}",
            )
        )
        if not passed:
            failures.append(
                ValidationIssue(
                    code=f"missing_directory_{directory}",
                    message=f"Required directory missing: {directory}",
                    severity=ValidationStatus.INVALID,
                )
            )

    for file_name in _TYPE_REQUIRED_FILES.get(repository_type, ()):
        target = root / file_name
        passed = target.is_file()
        checks.append(
            ValidationCheck(
                name=f"file:{file_name}",
                passed=passed,
                message=None if passed else f"Required file missing: {file_name}",
            )
        )
        if not passed:
            failures.append(
                ValidationIssue(
                    code=f"missing_file_{file_name}",
                    message=f"Required file missing: {file_name}",
                    severity=ValidationStatus.INVALID,
                )
            )

    config_path = root / ".86vibe" / "config.yaml"
    if config_path.is_file():
        checks.append(ValidationCheck(name="platform_configuration", passed=True))
    elif repository_type in {RepositoryType.CLI, RepositoryType.EXAMPLE}:
        warnings.append(
            ValidationIssue(
                code="missing_platform_configuration",
                message="Platform configuration file is not present.",
                severity=ValidationStatus.WARNING,
            )
        )
        checks.append(
            ValidationCheck(
                name="platform_configuration",
                passed=False,
                message="Platform configuration file is not present.",
            )
        )

    if repository_type == RepositoryType.UNKNOWN:
        warnings.append(
            ValidationIssue(
                code="unknown_repository_type",
                message="Repository type is unknown.",
                severity=ValidationStatus.WARNING,
            )
        )

    if failures:
        status = ValidationStatus.INVALID
    elif warnings:
        status = ValidationStatus.WARNING
    else:
        status = ValidationStatus.VALID

    checks.sort(key=lambda item: item.name)
    warnings.sort(key=lambda item: item.code)
    failures.sort(key=lambda item: item.code)

    return ValidationResult(
        status=status,
        repository_type=repository_type,
        checks=tuple(checks),
        warnings=tuple(warnings),
        failures=tuple(failures),
    )
