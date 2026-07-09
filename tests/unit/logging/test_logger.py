"""PlatformLogger unit tests."""

from __future__ import annotations

from pathlib import Path

from vibe.configuration.service import ConfigurationService
from vibe.logging.handlers import ERROR_LOG_FILE, PLATFORM_LOG_FILE, log_directory
from vibe.logging.service import LoggingService


def _build_service(tmp_path: Path) -> tuple[LoggingService, object]:
    configuration = ConfigurationService(project_root=tmp_path)
    configuration.load()
    service = LoggingService(configuration, project_root=tmp_path)
    service.initialize()
    return service, service.get_logger("cli")


def test_logger_supports_all_platform_levels(tmp_path: Path) -> None:
    """PlatformLogger exposes all required severity methods."""
    service, logger = _build_service(tmp_path)
    logger.trace("trace event")
    logger.debug("debug event")
    logger.info("info event")
    logger.warning("warning event")
    logger.error("error event")
    logger.critical("critical event")
    service.flush()

    platform_log = (log_directory(tmp_path) / PLATFORM_LOG_FILE).read_text(encoding="utf-8")
    assert "info event" in platform_log
    assert "error event" in platform_log
    service.shutdown()


def test_logger_redacts_secret_fields(tmp_path: Path) -> None:
    """Structured secret fields are redacted before formatting."""
    service, logger = _build_service(tmp_path)
    message = logger.format_message("auth", {"api_key": "secret-value"})
    assert "secret-value" not in message
    assert "********" in message
    service.shutdown()


def test_exception_logger_captures_exception_context(tmp_path: Path) -> None:
    """Exception logging captures active exception information."""
    service, logger = _build_service(tmp_path)
    error_log = log_directory(tmp_path) / ERROR_LOG_FILE
    try:
        raise ValueError("failure")
    except ValueError:
        logger.exception("operation failed", component="cli")
    service.flush()
    contents = error_log.read_text(encoding="utf-8")
    assert "operation failed" in contents
    assert "ValueError" in contents
    service.shutdown()
