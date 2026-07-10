"""Repository command groups."""

from __future__ import annotations

import typer

from vibe.cli.context import CLIContext
from vibe.cli.execution import CommandResult, execute_operational_command
from vibe.cli.exit_codes import ExitCode
from vibe.cli.invocation import get_invocation_state
from vibe.cli.requirements import REPOSITORY_DOCS, REPOSITORY_STATUS, REPOSITORY_VALIDATE
from vibe.registry import SERVICE_NAME_REPOSITORY
from vibe.repository.errors import RepositoryNotInitializedError
from vibe.repository.models import ValidationStatus


def _get_repository_service(context: CLIContext):
    return context.registry.get(SERVICE_NAME_REPOSITORY)


def _repo_status_handler(context: CLIContext) -> CommandResult:
    repository = _get_repository_service(context)
    if not repository.is_initialized:
        raise RepositoryNotInitializedError("Repository service is not initialized.")
    status = repository.status()
    metadata = repository.metadata()
    payload = {
        "status": status.as_dict(),
        "metadata": metadata.as_dict(),
    }
    if context.machine_readable:
        return CommandResult(success=True, exit_code=ExitCode.SUCCESS, data=payload)

    lines = [
        f"Repository: {metadata.name}",
        f"Type: {metadata.repository_type.value}",
        f"Root: {metadata.root}",
        f"Branch: {metadata.current_branch.name if metadata.current_branch else 'unavailable'}",
        f"Default branch: {metadata.default_branch or 'unavailable'}",
        f"Git status: {metadata.git_cleanliness.value}",
        f"Version: {metadata.repository_version or 'unavailable'}",
        f"Read-only: {metadata.read_only}",
        f"Validation: {status.validation_status.value}",
        f"Health: {status.health}",
    ]
    for warning in status.warnings:
        lines.append(f"Warning: {warning}")
    return CommandResult(
        success=True,
        exit_code=ExitCode.SUCCESS,
        message="\n".join(lines),
        data=payload,
    )


def _repo_validate_handler(context: CLIContext) -> CommandResult:
    repository = _get_repository_service(context)
    if not repository.is_initialized:
        raise RepositoryNotInitializedError("Repository service is not initialized.")
    result = repository.validate()
    payload = result.as_dict()
    if context.machine_readable:
        exit_code = _validation_exit_code(result.status)
        return CommandResult(
            success=exit_code == ExitCode.SUCCESS,
            exit_code=exit_code,
            data=payload,
        )

    lines = [
        f"Validation status: {result.status.value}",
        f"Repository type: {result.repository_type.value}",
    ]
    for check in result.checks:
        state = "pass" if check.passed else "fail"
        detail = f" - {check.message}" if check.message else ""
        lines.append(f"[{state}] {check.name}{detail}")
    for warning in result.warnings:
        lines.append(f"Warning: {warning.message}")
    for failure in result.failures:
        lines.append(f"Failure: {failure.message}")

    exit_code = _validation_exit_code(result.status)
    return CommandResult(
        success=exit_code == ExitCode.SUCCESS,
        exit_code=exit_code,
        message="\n".join(lines),
        data=payload,
    )


def _repo_docs_handler(context: CLIContext) -> CommandResult:
    repository = _get_repository_service(context)
    if not repository.is_initialized:
        raise RepositoryNotInitializedError("Repository service is not initialized.")
    documents = [document.as_dict() for document in repository.documents()]
    payload = {"documents": documents}
    if context.machine_readable:
        return CommandResult(success=True, exit_code=ExitCode.SUCCESS, data=payload)

    if not documents:
        return CommandResult(
            success=True,
            exit_code=ExitCode.SUCCESS,
            message="No architecture documents discovered.",
            data=payload,
        )

    lines = ["Architecture documents:"]
    for document in documents:
        title = document.get("title") or "unknown title"
        document_id = document.get("document_id") or "unknown id"
        lines.append(f"- {document_id}: {title} ({document['path']})")
    return CommandResult(
        success=True,
        exit_code=ExitCode.SUCCESS,
        message="\n".join(lines),
        data=payload,
    )


def _validation_exit_code(status: ValidationStatus) -> ExitCode:
    if status == ValidationStatus.INVALID:
        return ExitCode.VALIDATION_FAILURE
    return ExitCode.SUCCESS


def _create_repository_group() -> typer.Typer:
    repo_app = typer.Typer(help="Repository utilities.")

    @repo_app.callback(invoke_without_command=True)
    def repo_group(ctx: typer.Context) -> None:
        """Repository command group."""
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(code=int(ExitCode.SUCCESS))

    @repo_app.command("status")
    def repo_status(ctx: typer.Context) -> None:
        """Report repository status."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)
        exit_code = execute_operational_command(
            state.application.bootstrap_service,
            output,
            REPOSITORY_STATUS,
            _repo_status_handler,
            diagnostic=state.diagnostic,
            command_name="repository status",
        )
        raise typer.Exit(code=exit_code)

    @repo_app.command("validate")
    def repo_validate(ctx: typer.Context) -> None:
        """Validate repository structure."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)
        exit_code = execute_operational_command(
            state.application.bootstrap_service,
            output,
            REPOSITORY_VALIDATE,
            _repo_validate_handler,
            diagnostic=state.diagnostic,
            command_name="repository validate",
        )
        raise typer.Exit(code=exit_code)

    @repo_app.command("docs")
    def repo_docs(ctx: typer.Context) -> None:
        """Manage repository documentation."""
        state = get_invocation_state(ctx)
        output = state.application.create_output_renderer(state)
        exit_code = execute_operational_command(
            state.application.bootstrap_service,
            output,
            REPOSITORY_DOCS,
            _repo_docs_handler,
            diagnostic=state.diagnostic,
            command_name="repository docs",
        )
        raise typer.Exit(code=exit_code)

    return repo_app


def register_repository_commands(app: typer.Typer) -> None:
    """Register repository command groups and aliases."""
    app.add_typer(_create_repository_group(), name="repository")
    app.add_typer(_create_repository_group(), name="repo")
